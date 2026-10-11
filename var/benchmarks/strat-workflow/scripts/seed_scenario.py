#!/usr/bin/env python3
"""Reset the Jira emulator and seed one benchmark scenario.

Each scenario in ../data/scenarios/<name>.yaml lists the RFEs to create, by
template (../data/rfe-templates/<name>.yaml) and whether each one should be
eligible for strat-creator's discovery. Eligibility rules come from the
strat-creator commit under test, not from this script:

- labels: one release label from config/pipeline-settings.yaml
  (jql.required_labels) and the first quality label (jql.quality_labels);
- after seeding, that commit's own discovery JQL (scripts/jira_utils.py
  build_jql_from_config) must return exactly the RFEs marked eligible.

Runs anywhere with JIRA_SERVER, JIRA_USER and JIRA_TOKEN for the emulator,
normally as a dashboard script job (the job already has them and trusts the
emulator CA). It refuses any server that isn't the Jira emulator.

    seed_scenario.py --scenario smoke-one-rfe --strat-creator-ref <sha>
    seed_scenario.py --scenario smoke-one-rfe --strat-creator /path/to/checkout

Writes seed.json (scenario, keys, labels, discovery result) to stdout and to
$JOB_ARTIFACT_DIR when set.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

import httpx
import yaml

BENCH = Path(__file__).resolve().parents[1]
EMULATOR_HOSTS = {"jira.local", "jira-emulator.ai-pipeline.svc.cluster.local"}
STRAT_CREATOR_REPO = "https://github.local/opendatahub-io/strat-creator.git"
BENCH_LABEL = "strat-workflow-eval"
RELEASE_LABEL = "strat-creator-3.6"  # matches the rhoai-3.6-ea.2 architecture snapshot
EXTRA_ELIGIBLE_LABELS = ["rfe-creator-feasibility-pass"]


def clone_strat_creator(ref: str, dest: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "fetch", "-q", "--depth", "1", STRAT_CREATOR_REPO, ref], check=True)
    subprocess.run(["git", "-C", str(dest), "-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD"], check=True)
    head = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    if head != ref:
        raise SystemExit(f"strat-creator clone is at {head}, not {ref}")
    return dest


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_scenario(name: str) -> tuple[dict, dict]:
    """Validate all fixture inputs before any reset or issue creation."""
    scenario_file = BENCH / "data" / "scenarios" / f"{name}.yaml"
    if not scenario_file.is_file():
        raise SystemExit(f"unknown scenario: {name} ({scenario_file})")
    scenario = yaml.safe_load(scenario_file.read_text())
    rfes = scenario["rfes"]
    templates = {rfe["template"]: yaml.safe_load(
        (BENCH / "data" / "rfe-templates" / f"{rfe['template']}.yaml").read_text()) for rfe in rfes}
    if not rfes or len({rfe["id"] for rfe in rfes}) != len(rfes):
        raise SystemExit("scenario needs nonempty RFEs with unique IDs")
    for template in templates.values():
        if not template.get("summary") or not template.get("description"):
            raise SystemExit("each RFE template needs a summary and full description")
    if scenario.get("expected_batch_size"):
        count = scenario["expected_batch_size"]
        if len(rfes) != count or not all(rfe.get("eligible") for rfe in rfes):
            raise SystemExit("all-new batch must contain exactly the expected number of eligible RFEs")
        for field in ("summary", "description"):
            if len({templates[rfe["template"]][field] for rfe in rfes}) != count:
                raise SystemExit(f"batch RFEs must have distinct {field} values")
    return scenario, templates


def discovery_problems(created: list[dict], discovered: list[str]) -> list[str]:
    expected = {rfe["key"] for rfe in created if rfe["eligible"]}
    found = set(discovered)
    problems = []
    if expected - found:
        problems.append(f"eligible but not discovered: {sorted(expected - found)}")
    if found - expected:
        problems.append(f"unexpected discovery candidates: {sorted(found - expected)}")
    if len(discovered) != len(found):
        problems.append("discovery returned duplicate keys")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--scenario", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--strat-creator", type=Path, help="existing strat-creator checkout")
    source.add_argument("--strat-creator-ref", help="40-character commit to clone from the GitHub emulator")
    parser.add_argument("--no-reset", action="store_true", help="seed without resetting Jira first")
    parser.add_argument("--dry-run", action="store_true",
                        help="check connectivity and print the planned issues; no reset, no writes")
    args = parser.parse_args()

    scenario, templates = load_scenario(args.scenario)

    server = os.environ["JIRA_SERVER"].rstrip("/")
    if urlparse(server).hostname not in EMULATOR_HOSTS:
        raise SystemExit(f"refusing to seed {server}: not the Jira emulator")
    auth = (os.environ["JIRA_USER"], os.environ["JIRA_TOKEN"])
    verify = os.environ.get("JIRA_CA_FILE") or os.environ.get("REQUESTS_CA_BUNDLE") or True

    with tempfile.TemporaryDirectory() as tmp:
        if args.strat_creator:
            checkout = args.strat_creator.resolve()
            ref = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        else:
            ref = args.strat_creator_ref
            checkout = clone_strat_creator(ref, Path(tmp) / "strat-creator")
        settings = yaml.safe_load((checkout / "config" / "pipeline-settings.yaml").read_text())
        sys.path.insert(0, str(checkout / "scripts"))
        jira_utils = load_module("jira_utils", checkout / "scripts" / "jira_utils.py")
        lock = load_module("lock_issues", checkout / "scripts" / "lock_issues.py")
        discovery_jql = jira_utils.build_jql_from_config(checkout / "config" / "pipeline-settings.yaml")

    gate = settings["jql"]
    if RELEASE_LABEL not in gate.get("required_labels", []):
        raise SystemExit(f"{RELEASE_LABEL} is not a required label at strat-creator {ref}")
    eligible_labels = [RELEASE_LABEL, *gate.get("quality_labels", [])[:1], *EXTRA_ELIGIBLE_LABELS]
    for rfe in scenario["rfes"]:
        blocked = set([*rfe.get("labels", []), *eligible_labels]) & set(lock.BLOCKING_LABELS)
        if rfe.get("eligible") and blocked:
            raise SystemExit(f"{rfe['id']} is marked eligible but carries lock labels {sorted(blocked)}")

    client = httpx.Client(base_url=server, auth=auth, verify=verify, timeout=30)

    def api(method: str, path: str, **kwargs):
        response = client.request(method, path, **kwargs)
        if response.is_error:
            raise SystemExit(f"Jira {method} {path}: HTTP {response.status_code}: {response.text[:300]}")
        return response.json() if response.content else None

    reset = scenario.get("reset", True) and not args.no_reset
    if args.dry_run:
        for project in ("RHAIRFE", "RHAISTRAT"):
            api("GET", f"/rest/api/2/project/{project}")
        planned = []
        for rfe in scenario["rfes"]:
            template = templates[rfe["template"]]
            labels = [BENCH_LABEL, f"swe-{args.scenario}", f"swe-id-{rfe['id']}", *rfe.get("labels", [])]
            if rfe.get("eligible"):
                labels += eligible_labels
            planned.append({"id": rfe["id"], "template": rfe["template"], "summary": template["summary"],
                            "eligible": bool(rfe.get("eligible")), "labels": list(dict.fromkeys(labels))})
        current = api("GET", "/rest/api/2/search", params={"jql": discovery_jql, "maxResults": 0})
        print(json.dumps({"dry_run": True, "scenario": args.scenario, "server": server,
                          "would_reset": reset, "strat_creator_ref": ref,
                          "eligible_labels": eligible_labels, "discovery_jql": discovery_jql,
                          "currently_discovered": current.get("total"), "planned": planned}, indent=2))
        return 0
    # This also protects direct seed-script use outside the Markov workflow.
    from require_archive import DEFAULT_SINCE, check_archives
    archival = check_archives(os.environ.get("STRAT_ARCHIVE_REQUIRED_SINCE", DEFAULT_SINCE))
    if not archival["ok"]:
        raise SystemExit("Earlier benchmark data has no verified final host archive: " + json.dumps(archival["pending"]))
    if reset:
        result = api("POST", "/api/admin/reset")
        if result.get("message") != "Database reset successfully":
            raise SystemExit(f"unexpected reset reply: {result}")
    for project in ("RHAIRFE", "RHAISTRAT"):
        api("GET", f"/rest/api/2/project/{project}")

    created = []
    for rfe in scenario["rfes"]:
        template = templates[rfe["template"]]
        labels = [BENCH_LABEL, f"swe-{args.scenario}", f"swe-id-{rfe['id']}", *rfe.get("labels", [])]
        if rfe.get("eligible"):
            labels += eligible_labels
        labels = list(dict.fromkeys(labels))
        blocked = set(labels) & set(lock.BLOCKING_LABELS)
        if rfe.get("eligible") and blocked:
            raise SystemExit(f"{rfe['id']} is marked eligible but carries lock labels {sorted(blocked)}")
        issue = api("POST", "/rest/api/2/issue", json={"fields": {
            "project": {"key": "RHAIRFE"},
            "issuetype": {"name": "Feature Request"},
            "summary": template["summary"],
            "description": template["description"],
            "priority": {"name": rfe.get("priority", "Major")},
            "labels": labels,
        }})
        key = issue["key"]
        fields = api("GET", f"/rest/api/2/issue/{key}", params={"fields": "summary,labels,status"})["fields"]
        created.append({
            "id": rfe["id"],
            "key": key,
            "template": rfe["template"],
            "summary": fields["summary"],
            "description_sha256": hashlib.sha256(template["description"].encode()).hexdigest(),
            "eligible": bool(rfe.get("eligible")),
            "labels": sorted(fields["labels"]),
            "status": fields["status"]["name"],
            "description_chars": len(template["description"]),
        })

    found = api("GET", "/rest/api/2/search", params={"jql": discovery_jql, "maxResults": 200, "fields": "labels"})
    discovered = [issue["key"] for issue in found["issues"]]
    problems = discovery_problems(created, discovered)
    if found.get("total", len(discovered)) != len(discovered):
        problems.append("discovery was truncated")

    report = {
        "scenario": args.scenario,
        "description": scenario.get("description", ""),
        "server": server,
        "reset": reset,
        "strat_creator_ref": ref,
        "eligible_labels": eligible_labels,
        "discovery_jql": discovery_jql,
        "rfes": created,
        "discovered": sorted(discovered),
        "discovered_in_order": discovered,
        "ok": not problems,
        "problems": problems,
    }
    text = json.dumps(report, indent=2)
    print(text)
    if os.environ.get("JOB_ARTIFACT_DIR"):
        Path(os.environ["JOB_ARTIFACT_DIR"], "seed.json").write_text(text + "\n")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
