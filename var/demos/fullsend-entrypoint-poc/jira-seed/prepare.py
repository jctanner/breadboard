#!/usr/bin/env python3
"""Reset only local Jira, restore CI credentials, and seed one eligible RFE."""
import argparse
import base64
import importlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[4]
FIXTURE_LABEL = "fullsend-entrypoint-poc-m5"
BOT = "aipcc-agentic-jira-bot"
SECRET = "fullsend-strategy-jira"


def kubectl(*args, body=None):
    result = subprocess.run(["kubectl", "-n", "ai-pipeline", *args],
                            input=body, text=True, capture_output=True, check=True)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset-jira", action="store_true")
    parser.add_argument("--checkout", type=Path, default=ROOT / "checkouts.fullsend_prototype/jctanner.strat-creator")
    args = parser.parse_args()
    server = os.environ.get("JIRA_SERVER", "https://jira.local").rstrip("/")
    if server != "https://jira.local":
        raise SystemExit("This fixture operates only on https://jira.local")
    ca = os.environ["JIRA_CA_FILE"]
    admin = (os.environ["JIRA_ADMIN_USER"], os.environ["JIRA_ADMIN_TOKEN"])
    settings = yaml.safe_load((args.checkout / "config/pipeline-settings.yaml").read_text())
    spec = importlib.util.spec_from_file_location("seed_source", ROOT / "var/demos/strat-pipeline-replication/scripts/seed_single_rfe.py")
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    lock_spec = importlib.util.spec_from_file_location("lock_source", args.checkout / "scripts/lock_issues.py")
    sys.path.insert(0, str(args.checkout / "scripts"))
    lock = importlib.util.module_from_spec(lock_spec)
    lock_spec.loader.exec_module(lock)
    jira = importlib.import_module("jira_utils")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.checkout, text=True).strip()
    client = httpx.Client(base_url=server, verify=ca, timeout=30)

    def api(method, path, body=None, auth=admin, bearer=None):
        headers = {"Authorization": f"Bearer {bearer}"} if bearer else {}
        response = client.request(method, path, json=body, auth=None if bearer else auth, headers=headers)
        if response.is_error:
            raise RuntimeError(f"Jira {method} {path}: HTTP {response.status_code}")
        return response.json() if response.content else None

    # Check connectivity and prerequisites before the destructive, explicit reset.
    identity = api("GET", "/rest/api/3/myself")
    assert identity["name"] == admin[0], "unexpected admin identity"
    for project in ("RHAIRFE", "RHAISTRAT"):
        api("GET", f"/rest/api/3/project/{project}")
    before = api("GET", "/rest/api/3/search?jql=project%20%3D%20RHAIRFE&maxResults=1")["total"]
    if args.reset_jira:
        result = api("POST", "/api/admin/reset")
        assert result["message"] == "Database reset successfully"
    projects = {key: api("GET", f"/rest/api/3/project/{key}") for key in ("RHAIRFE", "RHAISTRAT")}
    assert "Feature Request" in {t["name"] for t in projects["RHAIRFE"]["issueTypes"]}
    assert {"Feature", "Initiative"} <= {t["name"] for t in projects["RHAISTRAT"]["issueTypes"]}
    assert api("GET", "/rest/api/3/myself")["name"] == admin[0]

    # Reuse only a still-valid fixture credential; a reset invalidates old PATs.
    saved = subprocess.run(["kubectl", "-n", "ai-pipeline", "get", "secret", SECRET, "-o", "json"],
                           text=True, capture_output=True)
    credential = None
    if saved.returncode == 0:
        data = json.loads(saved.stdout)["data"]
        candidate = {k: base64.b64decode(v).decode() for k, v in data.items()}
        current = api("GET", "/rest/api/3/myself", bearer=candidate["JIRA_BEARER_TOKEN"])
        if not args.reset_jira and current["name"] == BOT:
            credential = candidate
    if credential is None:
        password = secrets.token_urlsafe(32)
        response = client.get(f"/rest/api/3/user?username={BOT}", auth=admin)
        if response.status_code == 404:
            api("POST", "/rest/api/3/user", {"name": BOT, "password": password,
                "emailAddress": f"{BOT}@redhat.com", "displayName": "AIPCC Agentic Jira Bot"})
        else:
            response.raise_for_status()
            api("PUT", f"/rest/api/3/user/password?username={BOT}", {"password": password})
        token = api("POST", "/rest/pat/latest/tokens", {"name": FIXTURE_LABEL}, auth=(BOT, password))["rawToken"]
        credential = {"JIRA_SERVER": server, "JIRA_USER": BOT, "JIRA_TOKEN": password, "JIRA_BEARER_TOKEN": token}
        resource = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": SECRET, "namespace": "ai-pipeline"},
                    "type": "Opaque", "stringData": credential}
        kubectl("apply", "-f", "-", body=json.dumps(resource))
    assert api("GET", "/rest/api/3/myself", bearer=credential["JIRA_BEARER_TOKEN"])["name"] == BOT
    wrong = api("GET", "/rest/api/3/myself", bearer="invalid-m5-bearer-token")
    assert wrong["name"] != BOT, "invalid bearer resolved to bot identity"
    bot_auth = (BOT, credential["JIRA_TOKEN"])
    assert api("GET", "/rest/api/3/myself", auth=bot_auth)["name"] == BOT

    components = api("GET", "/rest/api/3/project/RHAIRFE/components")
    component = next((c for c in components if c["name"] == "CLI"), None)
    if component is None:
        component = api("POST", "/rest/api/3/component", {"name": "CLI", "project": "RHAIRFE"})
    gate = settings["jql"]
    labels = [FIXTURE_LABEL, gate["required_labels"][0], "rfe-creator-feasibility-pass"]
    if gate.get("quality_labels"):
        labels.append(gate["quality_labels"][0])
    query = httpx.QueryParams({"jql": f'project = RHAIRFE AND labels = "{FIXTURE_LABEL}"', "maxResults": 2})
    found = api("GET", f"/rest/api/3/search?{query}")
    assert found["total"] <= 1, "duplicate fixture issues"
    if found["issues"]:
        key = found["issues"][0]["key"]
        created = False
    else:
        issue = api("POST", "/rest/api/3/issue", {"fields": {
            "project": {"key": "RHAIRFE"}, "issuetype": {"name": "Feature Request"},
            "summary": source.SUMMARY, "description": source.DESCRIPTION,
            "priority": {"name": "Major"}, "components": [{"name": component["name"]}], "labels": labels,
        }}, auth=bot_auth)
        key, created = issue["key"], True
    fields = api("GET", f"/rest/api/3/issue/{key}", auth=bot_auth)["fields"]
    actual = set(fields["labels"])
    assert not actual.intersection(lock.BLOCKING_LABELS | set(settings.get("skip_labels", [])))
    if "CLI" not in {c["name"] for c in fields["components"]}:
        assert not actual.intersection(lock.BLOCKING_LABELS), "refusing to repair a locked fixture"
        api("PUT", f"/rest/api/3/issue/{key}", {"fields": {"components": [{"name": "CLI"}]}}, auth=bot_auth)
        fields = api("GET", f"/rest/api/3/issue/{key}", auth=bot_auth)["fields"]
    assert set(labels) <= actual
    assert actual.intersection(gate["required_labels"])
    assert not gate.get("quality_labels") or actual.intersection(gate["quality_labels"])
    assert fields["status"]["name"] not in gate["excluded_statuses"]
    assert fields["summary"] == source.SUMMARY and fields["description"]
    if isinstance(fields["description"], str):
        assert fields["description"] == source.DESCRIPTION, "seed description changed"
    assert not fields.get("attachment"), "fixture already has attachments"
    assert fields["issuetype"]["name"] == "Feature Request"
    assert fields["priority"]["name"] == "Major"
    assert "CLI" in {c["name"] for c in fields["components"]}
    assert not fields.get("issuelinks"), "fixture already linked to other work"
    jira.ssl_ctx.load_verify_locations(ca)
    strategy_read = jira.get_issue(server, BOT, credential["JIRA_TOKEN"], key, fields=["summary", "labels", "status"])
    assert strategy_read["fields"]["summary"] == source.SUMMARY
    # Query the branch's own discovery JQL and prove this explicit issue is selected.
    query = httpx.QueryParams({"jql": jira.build_jql_from_config(args.checkout / "config/pipeline-settings.yaml")})
    eligible = api("GET", f"/rest/api/3/search?{query}", auth=bot_auth)
    assert key in {i["key"] for i in eligible["issues"]}, "seed missing from configured discovery"
    print(json.dumps({"reset_performed": args.reset_jira, "pre_reset_rfe_count": before,
        "key": key, "created": created, "summary": fields["summary"], "labels": sorted(actual),
        "status": fields["status"]["name"], "eligible": True, "strategy_links": 0,
        "checkout_sha": revision, "credential_secret": f"ai-pipeline/{SECRET}",
        "ci_identity": BOT, "bearer_identity_verified": True, "invalid_bearer_not_bot": True,
        "basic_identity_verified": True, "strategy_python_read_verified": True, "basic_password_validation": "unavailable in permissive mode",
        "required_projects_verified": list(projects)}, indent=2))


if __name__ == "__main__":
    main()
