#!/usr/bin/env python3
"""Converge CI credentials and project variables for the CC-75 emulator mirrors.

Creates (or keeps, if still valid) emulator-only credentials and stores them
as masked GitLab project variables. Raw values are never printed or written:
  - Jira bot `cc75-strat-bot` (synthetic identity) and a PAT -> JIRA_API_TOKEN;
  - a GitLab PAT for result pushes -> RESULTS_PUSH_TOKEN.
Visible variables point jobs at in-cluster emulators and the runner's CA:
  JIRA_SERVER, the bot username (USERNAME_VARIABLE), EXTRA_CA_FILE, STRAT_CREATOR_RAW_BASE, GCP_PROJECT_ID,
  and for live runs STRAT_RESULTS_GIT_BASE and RESULTS_REPO (GitLab emulator).
GOOGLE_APPLICATION_CREDENTIALS is a File variable. Until the model route is
approved it holds an inert placeholder, which is enough for runs that select
no work (Fullsend skips the sandbox); bootstrap_model.py replaces it later.
Writes credentials-manifest.json (names and checks only).
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
GROUP = "redhat/rhel-ai/agentic-ci"
PROJECTS = ["strat-pipeline", "rfe-autofixer", "epic-decomposer"]
BOT = {"name": "cc75-strat-bot", "emailAddress": "cc75-strat-bot@example.invalid",
       "displayName": "CC75 Strategy Bot (synthetic)"}
JIRA_TOKEN_NAME = "cc75-ci"
GITLAB_TOKEN_NAME = "cc75-results-push"
IN_CLUSTER = {
    # The emulator's canonical URL (its BASE_URL), as production uses its site URL: Jira
    # returns attachment URLs on it. Cluster DNS rewrites it to the TLS ingress.
    "JIRA_SERVER": f"https://jira.{DOMAIN}",
    "STRAT_CREATOR_RAW_BASE": "https://github-emulator.ai-pipeline.svc.cluster.local/fullsend-ai/strat-creator/raw",
    "EXTRA_CA_FILE": "/etc/gitlab-runner/certs/ca.crt",
    # Live runs (S7, cc75-live branch only) publish here instead of gitlab.com.
    "STRAT_RESULTS_GIT_BASE": "https://gitlab-emulator.ai-pipeline.svc.cluster.local",
    "RESULTS_REPO": "redhat/rhel-ai/agentic-ci/strat-pipeline-data",
}
# The mirror shows the eventual state: every project carries the bot username as
# JIRA_USERNAME only.
USERNAME_VARIABLE = {"strat-pipeline": "JIRA_USERNAME", "rfe-autofixer": "JIRA_USERNAME",
                     "epic-decomposer": "JIRA_USERNAME"}
# The emulator CA, as GitLab File variables holding the host's public roots plus the
# emulator CA, so every step of every job (the Jira identity probe first) trusts the
# emulators without YAML changes. CC75_SANDBOX_CA feeds the per-job sandbox images.
CA_FILE_VARIABLES = ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "GIT_SSL_CAINFO",
                     "NODE_EXTRA_CA_CERTS", "CC75_SANDBOX_CA")
SYSTEM_BUNDLES = ("/etc/pki/tls/certs/ca-bundle.crt", "/etc/ssl/certs/ca-certificates.crt")
# Per-project settings that production would carry as project or group variables.
PROJECT_SETTINGS = {
    # Emulator gap: the Jira emulator has no permissions endpoint for the job's probe.
    "rfe-autofixer": {"CC75_SKIP_PERMISSIONS_PROBE": "1",
                      # A sandbox image that w530's older CPU can run.
                      "CLAUDE_CONTAINER_IMAGE": "quay.io/aipcc/agentic-ci/claude-sandbox:0.3.46"},
}
PLACEHOLDER_ADC = json.dumps({"type": "cc75-placeholder",
                              "note": "Inert placeholder; no model access. Replaced by bootstrap_model.py."})


def main() -> int:
    ca = os.getenv("BREADBOARD_CA_FILE") or True
    jira_url = os.getenv("JIRA_URL", f"https://jira.{DOMAIN}")
    gl_url = os.getenv("GITLAB_URL", f"https://gitlab.{DOMAIN}") + "/api/v4"
    jira = requests.Session()
    jira.auth = (os.getenv("JIRA_ADMIN_USER", "admin"), os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
    jira.verify = ca
    gl = requests.Session()
    gl.auth = (os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin"))
    gl.verify = ca

    def ok(r):
        if r.status_code >= 400:
            raise SystemExit(f"{r.request.method} {r.url.split('?')[0]}: HTTP {r.status_code}: {r.text[:200]}")
        return r.json() if r.content else None

    def bot_valid(token):
        r = requests.get(f"{jira_url}/rest/api/2/myself", auth=(BOT["name"], token), verify=ca, timeout=30)
        return r.status_code == 200 and r.json().get("name", r.json().get("key")) == BOT["name"]

    def gitlab_valid(token):
        r = requests.get(f"{gl_url}/user", headers={"PRIVATE-TOKEN": token}, verify=ca, timeout=30)
        return r.status_code == 200

    def get_var(pid, key):
        r = gl.get(f"{gl_url}/projects/{pid}/variables/{key}", timeout=30)
        return None if r.status_code == 404 else ok(r)

    def delete_var(pid, key):
        if get_var(pid, key) is not None:
            ok(gl.delete(f"{gl_url}/projects/{pid}/variables/{key}", timeout=30))

    def set_var(pid, key, value, *, masked=False, file=False, description=""):
        body = {"value": value, "variable_type": "file" if file else "env_var", "masked": masked,
                "protected": False, "raw": True, "environment_scope": "*", "description": description}
        if get_var(pid, key) is None:
            ok(gl.post(f"{gl_url}/projects/{pid}/variables", json={"key": key, **body}, timeout=30))
        else:
            ok(gl.put(f"{gl_url}/projects/{pid}/variables/{key}", json=body, timeout=30))

    pids = {}
    for name in PROJECTS:
        pids[name] = ok(gl.get(f"{gl_url}/projects/{quote(f'{GROUP}/{name}', safe='')}", timeout=30))["id"]
    main_pid = pids["strat-pipeline"]

    # Jira bot + PAT (reuse the stored one while it still authenticates).
    existing = get_var(main_pid, "JIRA_API_TOKEN")
    jira_token = existing["value"] if existing and bot_valid(existing["value"]) else None
    jira_rotated = jira_token is None
    if jira_rotated:
        password = secrets.token_urlsafe(24)
        r = jira.get(f"{jira_url}/rest/api/2/user", params={"username": BOT["name"]}, timeout=30)
        if r.status_code == 404:
            ok(jira.post(f"{jira_url}/rest/api/2/user", json={**BOT, "name": BOT["name"], "password": password},
                         timeout=30))
        else:
            ok(jira.put(f"{jira_url}/rest/api/2/user/password", params={"username": BOT["name"]},
                        json={"password": password}, timeout=30))
        bot = requests.Session()
        bot.auth = (BOT["name"], password)
        bot.verify = ca
        for t in ok(bot.get(f"{jira_url}/rest/pat/latest/tokens", timeout=30)) or []:
            if t.get("name") == JIRA_TOKEN_NAME:
                ok(bot.delete(f"{jira_url}/rest/pat/latest/tokens/{t['id']}", timeout=30))
        jira_token = ok(bot.post(f"{jira_url}/rest/pat/latest/tokens", json={"name": JIRA_TOKEN_NAME},
                                 timeout=30))["rawToken"]
        if not bot_valid(jira_token):
            raise SystemExit("new Jira PAT does not authenticate with Basic JIRA_USER:JIRA_TOKEN")

    existing = get_var(main_pid, "RESULTS_PUSH_TOKEN")
    gl_token = existing["value"] if existing and gitlab_valid(existing["value"]) else None
    gl_rotated = gl_token is None
    if gl_rotated:
        gl_token = ok(gl.post(f"{gl_url}/admin/tokens", json={
            "login": "admin", "name": GITLAB_TOKEN_NAME,
            "scopes": ["api", "read_repository", "write_repository"]}, timeout=30))["token"]

    project_id = os.getenv("CC75_RELAY_PROJECT", "cc75-initiatives")
    emulator_ca = Path(ca).read_text() if isinstance(ca, str) else ""
    system = next((Path(b) for b in SYSTEM_BUNDLES if Path(b).is_file()), None)
    if not emulator_ca or system is None:
        raise SystemExit("BREADBOARD_CA_FILE and a system CA bundle are required for the CA File variables")
    ca_bundle = system.read_text().rstrip("\n") + "\n" + emulator_ca
    for name, pid in pids.items():
        set_var(pid, "JIRA_SERVER", IN_CLUSTER["JIRA_SERVER"], description="CC-75: Jira emulator (canonical URL)")
        username_var = USERNAME_VARIABLE[name]
        set_var(pid, username_var, BOT["name"], description="CC-75: synthetic Jira bot")
        delete_var(pid, "JIRA_USERNAME" if username_var == "JIRA_USER" else "JIRA_USER")
        set_var(pid, "JIRA_API_TOKEN", jira_token, masked=True, description="CC-75: emulator Jira PAT")
        set_var(pid, "RESULTS_PUSH_TOKEN", gl_token, masked=True, description="CC-75: emulator GitLab PAT")
        set_var(pid, "EXTRA_CA_FILE", IN_CLUSTER["EXTRA_CA_FILE"], description="CC-75: runner-mounted emulator CA")
        for var in CA_FILE_VARIABLES:
            set_var(pid, var, ca_bundle, file=True, description="CC-75: public roots plus the emulator CA")
        for var, value in PROJECT_SETTINGS.get(name, {}).items():
            set_var(pid, var, value, description="CC-75: emulator project setting")
        set_var(pid, "STRAT_CREATOR_RAW_BASE", IN_CLUSTER["STRAT_CREATOR_RAW_BASE"],
                description="CC-75: GitHub emulator raw endpoint for strat-creator")
        set_var(pid, "STRAT_RESULTS_GIT_BASE", IN_CLUSTER["STRAT_RESULTS_GIT_BASE"],
                description="CC-75: results remote is the in-cluster GitLab emulator")
        # strat-pipeline-data is strat-pipeline's results repository. rfe-autofixer and
        # epic-decomposer name theirs in the job YAML and the mirror overrides it per
        # schedule or pipeline (run_autofix.py, run_decompose.py), so they carry none.
        if name == "strat-pipeline":
            set_var(pid, "RESULTS_REPO", IN_CLUSTER["RESULTS_REPO"], description="CC-75: emulator results repository")
        else:
            delete_var(pid, "RESULTS_REPO")
        set_var(pid, "GCP_PROJECT_ID", project_id, description="CC-75: Model Relay project id")
        current = get_var(pid, "GOOGLE_APPLICATION_CREDENTIALS")
        if current is None or "cc75-placeholder" in current.get("value", ""):
            set_var(pid, "GOOGLE_APPLICATION_CREDENTIALS", PLACEHOLDER_ADC, file=True,
                    description="CC-75: placeholder until the model route is configured")

    report = {"version": 1, "checked_at": datetime.now(timezone.utc).isoformat(),
              "jira_bot": BOT["name"], "jira_token_rotated": jira_rotated, "jira_basic_auth_check": True,
              "gitlab_token_rotated": gl_rotated, "projects": pids,
              "username_variable": USERNAME_VARIABLE, "ca_file_variables": list(CA_FILE_VARIABLES),
              "project_settings": PROJECT_SETTINGS,
              "variables_visible": ["JIRA_SERVER", "EXTRA_CA_FILE", "STRAT_CREATOR_RAW_BASE",
                                    "STRAT_RESULTS_GIT_BASE", "RESULTS_REPO", "GCP_PROJECT_ID"],
              "variables_masked": ["JIRA_API_TOKEN", "RESULTS_PUSH_TOKEN"],
              "variables_file": ["GOOGLE_APPLICATION_CREDENTIALS"],
              "notes": ["Raw credentials are not written to this report."]}
    (ROOT / "credentials-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("jira_token_rotated", "gitlab_token_rotated", "projects")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
