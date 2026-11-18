#!/usr/bin/env python3
"""Converge the CC-75 Model Relay route and CI model credentials (approved 2026-11-16).

1. Relay project `cc75-initiatives`: upstream profile `rh-vertex-strat-evals`
   (the human's Vertex account), model allowlist [claude-opus-5-5].
2. One Vertex workload key (exchange_only + mock_adc): its raw secret can only
   be exchanged at the relay's in-cluster /v1/token for a short-lived,
   project-bound token. Real upstream credentials stay inside the relay.
3. GitLab File variables on the CC-75 projects:
     CC75_RELAY_WORKLOAD_KEY          the workload key (masked file)
     GOOGLE_APPLICATION_CREDENTIALS   external_account ADC whose token_url is the
                                      relay and whose credential_source is the
                                      key at its sandbox path
   replacing bootstrap_ci.py's inert placeholder.
4. A Vertex-capable relay API key (`cc75-ci-apikey`, claude-opus-5-5 only) as the
   masked CI variable CC75_RELAY_API_KEY. Sandboxed Claude Code cannot acquire
   external_account credentials (smoke/sandbox-relay: the same exchange works
   from Python), so the harness skips Claude's Google auth and sends this key as
   `Authorization: Bearer` (CLAUDE_CODE_SKIP_VERTEX_AUTH + ANTHROPIC_CUSTOM_HEADERS).
5. --smoke: one minimal inference per credential path (exchanged token, and
   API key as bearer; 5-token rawPredict each). Records status and token counts only.
The key is never printed or written to disk outside GitLab; a valid stored key
is reused. Writes evidence/model-route-<timestamp>.json.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
PROJECT = "cc75-initiatives"
PROFILE = "rh-vertex-strat-evals"
MODEL = "claude-opus-5-5"
CLIENT_ID = "cc75-ci-workload"
API_CLIENT_ID = "cc75-ci-apikey"
GROUP = "redhat/rhel-ai/agentic-ci"
CI_PROJECTS = ["strat-pipeline", "rfe-autofixer", "epic-decomposer"]
RELAY = "model-relay.ai-pipeline.svc.cluster.local"
TOKEN_URL = f"http://{RELAY}:8082/v1/token"
SANDBOX_KEY_PATH = "/tmp/.cc75-relay-workload-key"
SCOPE = "https://www.googleapis.com/auth/cloud-platform"
TT = "urn:ietf:params:oauth:token-type:access_token"


def audience(project: str) -> str:
    return ("//iam.googleapis.com/projects/000000000001/locations/global/"
            f"workloadIdentityPools/{project}/providers/vertex-shim")


def adc_json() -> str:
    return json.dumps({"type": "external_account", "audience": audience(PROJECT), "token_url": TOKEN_URL,
                       "subject_token_type": TT,
                       "credential_source": {"file": SANDBOX_KEY_PATH, "format": {"type": "text"}}})


class PortForward:
    """kubectl port-forward to the relay's unpublished ADC (8082) and inference (8080) ports."""

    def __enter__(self):
        with socket.socket() as a, socket.socket() as b:
            a.bind(("127.0.0.1", 0)); b.bind(("127.0.0.1", 0))
            self.adc, self.api = a.getsockname()[1], b.getsockname()[1]
        self.proc = subprocess.Popen(
            ["kubectl", "port-forward", "-n", "ai-pipeline", "svc/model-relay",
             f"{self.adc}:8082", f"{self.api}:8080"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                socket.create_connection(("127.0.0.1", self.api), timeout=0.2).close()
                return self
            except OSError:
                time.sleep(0.2)
        raise SystemExit("port-forward to model-relay did not come up")

    def __exit__(self, *exc):
        self.proc.terminate()
        self.proc.wait(timeout=10)


def exchange(adc_port: int, key: str) -> requests.Response:
    return requests.post(f"http://127.0.0.1:{adc_port}/v1/token", timeout=30, data={
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange", "scope": SCOPE,
        "requested_token_type": TT, "subject_token_type": TT,
        "audience": audience(PROJECT), "subject_token": key})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--extra-project", action="append", default=[],
                    help="additional GitLab project path (e.g. cc75/sandbox-relay) to receive the CI variables")
    args = ap.parse_args()
    ca = os.getenv("BREADBOARD_CA_FILE") or True
    admin = requests.Session()
    admin.headers["authorization"] = f"Bearer {os.getenv('MODEL_RELAY_ADMIN_KEY', 'admin')}"
    admin.verify = ca
    a = f"https://relay.{DOMAIN}/api/private/v1"
    gl = requests.Session()
    gl.auth = (os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin"))
    gl.verify = ca
    g = f"https://gitlab.{DOMAIN}/api/v4"

    def ok(r):
        if r.status_code >= 400:
            raise SystemExit(f"{r.request.method} {r.url.split('?')[0]}: HTTP {r.status_code}: {r.text[:200]}")
        return r.json() if r.content else None

    project_doc = {"project_id": PROJECT, "display_name": "CC-75 Initiatives (synthetic demo)",
                   "enabled": True, "labels": {"cc75": "synthetic-demo"}, "upstream_profile": PROFILE,
                   "model_policy": {"allowed": [MODEL], "blocked": []}}
    r = admin.get(f"{a}/projects/{PROJECT}", timeout=30)
    if r.status_code == 404:
        ok(admin.post(f"{a}/projects", json=project_doc, timeout=30))
        project_action = "created"
    else:
        current = ok(r)
        same = all(current.get(k) == v for k, v in project_doc.items() if k != "model_policy") and \
            (current.get("model_policy") or {}).get("allowed") == [MODEL]
        if not same:
            ok(admin.put(f"{a}/projects/{PROJECT}", json=project_doc, timeout=30))
        project_action = "unchanged" if same else "updated"
    status = ok(admin.get(f"{a}/projects/{PROJECT}/auth/status", timeout=30))

    paths = [f"{GROUP}/{n}" for n in CI_PROJECTS] + args.extra_project
    pids = {p.rsplit("/", 1)[-1] if p.startswith(GROUP) else p:
            ok(gl.get(f"{g}/projects/{quote(p, safe='')}", timeout=30))["id"] for p in paths}

    def get_var(pid, key):
        r = gl.get(f"{g}/projects/{pid}/variables/{key}", timeout=30)
        return None if r.status_code == 404 else ok(r)

    def set_var(pid, key, value, *, masked, description, file=True):
        body = {"value": value, "variable_type": "file" if file else "env_var", "masked": masked, "protected": False,
                "raw": True, "environment_scope": "*", "description": description}
        if get_var(pid, key) is None:
            ok(gl.post(f"{g}/projects/{pid}/variables", json={"key": key, **body}, timeout=30))
        else:
            ok(gl.put(f"{g}/projects/{pid}/variables/{key}", json=body, timeout=30))

    smoke = None
    with PortForward() as pf:
        stored = get_var(pids["strat-pipeline"], "CC75_RELAY_WORKLOAD_KEY")
        key = stored["value"].strip() if stored else None
        key_action = "reused"
        if not key or exchange(pf.adc, key).status_code != 200:
            creds = ok(admin.get(f"{a}/projects/{PROJECT}/credentials", timeout=30))
            items = creds.get("items", creds) if isinstance(creds, dict) else creds
            for c in items or []:
                if c.get("client_id") == CLIENT_ID:
                    ok(admin.delete(f"{a}/projects/{PROJECT}/credentials/{c['key_id']}", timeout=30))
            issued = ok(admin.post(f"{a}/projects/{PROJECT}/credentials", timeout=30, json={
                "client_id": CLIENT_ID, "models": [MODEL], "backends": ["anthropic"],
                "catalog_models": False, "vertex_catalog_models": True, "mock_adc": True,
                "exchange_only": True}))
            key, key_action = issued["api_key"], "issued"
        for name, pid in pids.items():
            set_var(pid, "CC75_RELAY_WORKLOAD_KEY", key + "\n", masked=True,
                    description="CC-75: relay Vertex workload key (exchange-only)")
            set_var(pid, "GOOGLE_APPLICATION_CREDENTIALS", adc_json(), masked=False,
                    description="CC-75: external_account ADC via Model Relay")
        def raw_predict(bearer):
            r = requests.post(
                f"http://127.0.0.1:{pf.api}/v1/projects/{PROJECT}/locations/global/publishers/anthropic/"
                f"models/{MODEL}:rawPredict", timeout=120, headers={"authorization": f"Bearer {bearer}"},
                json={"anthropic_version": "vertex-2023-10-16", "max_tokens": 5,
                      "messages": [{"role": "user", "content": "Reply with the single word OK."}]})
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            return {"status": r.status_code, "model": body.get("model"), "usage": body.get("usage"),
                    "error_message": str((body.get("error") or {}).get("message", ""))[:200]}

        stored_api = get_var(pids["strat-pipeline"], "CC75_RELAY_API_KEY")
        api_key = stored_api["value"].strip() if stored_api else None
        api_action = "reused"
        creds = ok(admin.get(f"{a}/projects/{PROJECT}/credentials", timeout=30))
        listed = [c for c in (creds.get("items", creds) if isinstance(creds, dict) else creds) or []
                  if c.get("client_id") == API_CLIENT_ID]
        # Messages API use (the corsair provider recipe) needs the Messages catalogue grant.
        grants_ok = all(c.get("catalog_models") for c in listed) and listed
        if not api_key or not grants_ok or raw_predict(api_key)["status"] == 401:
            for c in listed:
                ok(admin.delete(f"{a}/projects/{PROJECT}/credentials/{c['key_id']}", timeout=30))
            api_key = ok(admin.post(f"{a}/projects/{PROJECT}/credentials", timeout=30, json={
                "client_id": API_CLIENT_ID, "models": [MODEL], "backends": ["anthropic"],
                "catalog_models": True, "vertex_catalog_models": True, "mock_adc": False,
                "exchange_only": False}))["api_key"]
            api_action = "issued"
        for name, pid in pids.items():
            set_var(pid, "CC75_RELAY_API_KEY", api_key, masked=True, file=False,
                    description="CC-75: relay Vertex API key (claude-opus-5-5 only)")
        # rfe-autofixer takes agentic-ci's API-key route (production's autofix-rfe-anthropic job):
        # the relay key as ANTHROPIC_API_KEY plus the relay base URL and model names, all as
        # project variables, so its YAML needs no relay changes (runner patch 0004 forwards them).
        relay_settings = {
            "ANTHROPIC_BASE_URL": f"https://relay-api.{DOMAIN}", "CLAUDE_MODEL": MODEL,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": MODEL, "ANTHROPIC_DEFAULT_SONNET_MODEL": MODEL,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": MODEL, "ANTHROPIC_SMALL_FAST_MODEL": MODEL,
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            # The relay requires Claude Code 2.1.280+ for this model; claude-sandbox ships 2.1.263.
            "CC75_CLAUDE_CODE_IMAGE": ("ghcr.io/fullsend-ai/fullsend-sandbox@sha256:"
                                       "2fc886b02c280ccf11f317662d182a56cefa6f9299ca9cbd54e780fced743ca7"),
        }
        if "rfe-autofixer" in pids:
            pid = pids["rfe-autofixer"]
            set_var(pid, "ANTHROPIC_API_KEY", api_key, masked=True, file=False,
                    description="CC-75: Model Relay key (claude-opus-5-5 only)")
            for var, value in relay_settings.items():
                set_var(pid, var, value, masked=False, file=False, description="CC-75: Model Relay route")
        direct = requests.post(f"http://127.0.0.1:{pf.api}/v1/messages", timeout=30,
                               headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                               json={"model": MODEL, "max_tokens": 1,
                                     "messages": [{"role": "user", "content": "hi"}]}).status_code
        if args.smoke:
            t = exchange(pf.adc, key)
            ok(t)
            m = requests.post(f"http://127.0.0.1:{pf.api}/v1/messages", timeout=120,
                              headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                              json={"model": MODEL, "max_tokens": 5,
                                    "messages": [{"role": "user", "content": "Reply with the single word OK."}]})
            mb = m.json() if m.headers.get("content-type", "").startswith("application/json") else {}
            smoke = {"exchange_status": t.status_code,
                     "exchanged_token": raw_predict(t.json()["access_token"]),
                     "api_key_bearer": raw_predict(api_key),
                     "messages_api_key": {"status": m.status_code, "model": mb.get("model"),
                                          "usage": mb.get("usage"),
                                          "error_message": str((mb.get("error") or {}).get("message", ""))[:200]}}
            smoke["raw_predict_status"] = smoke["messages_api_key"]["status"]

    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "relay_project": PROJECT,
              "project_action": project_action, "upstream_profile": PROFILE, "allowed_models": [MODEL],
              "auth_status": status, "workload_key": key_action, "api_key_action": api_action, "exchange_only_direct_messages_status": direct,
              "ci_projects": pids, "ci_file_variables": ["CC75_RELAY_WORKLOAD_KEY (masked)",
                                                         "GOOGLE_APPLICATION_CREDENTIALS"],
              "ci_env_variables": ["CC75_RELAY_API_KEY (masked)"],
              "smoke": smoke, "notes": ["No key or token values are recorded."]}
    out = ROOT / "evidence" / f"model-route-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("project_action", "workload_key", "api_key_action",
                                             "exchange_only_direct_messages_status", "smoke")}, indent=1))
    ok_smoke = (not args.smoke) or (smoke and smoke["raw_predict_status"] == 200)
    return 0 if ok_smoke and direct in (401, 403) else 1


if __name__ == "__main__":
    sys.exit(main())
