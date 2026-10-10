"""Shared helpers for the Markov runner side of the benchmark.

The Markov runner image has python3 and PyYAML but no third-party HTTP
client, so this uses urllib only. Scripts that import it run on the runner
(script_exec), never in job pods.

Settings come from the environment, set by the workflow's step params:
DASHBOARD_BASE, JIRA_BASE, JIRA_USER, JIRA_TOKEN.
"""
import base64
import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request

# The Jira emulator's certificate is signed by the cluster's internal CA,
# which the runner image doesn't carry (the jira_api step type uses
# tls_insecure for the same reason).
_INSECURE = ssl.create_default_context()
_INSECURE.check_hostname = False
_INSECURE.verify_mode = ssl.CERT_NONE


def _request(url: str, method: str = "GET", body=None, headers=None, timeout: int = 120):
    data = None
    headers = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    context = _INSECURE if url.startswith("https://") else None
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


def dashboard(path: str, method: str = "GET", body=None, raw: bool = False):
    """Call the dashboard API. Returns parsed JSON (or text with raw=True)."""
    base = os.environ.get("DASHBOARD_BASE", "http://pipeline-dashboard.ai-pipeline.svc.cluster.local:5000")
    status, payload = _request(base.rstrip("/") + path, method, body)
    if raw:
        return status, payload.decode("utf-8", "replace")
    try:
        return status, json.loads(payload or b"null")
    except json.JSONDecodeError:
        return status, {"error": payload.decode("utf-8", "replace")[:500]}


def jira(path: str):
    base = os.environ.get("JIRA_BASE", "https://jira-emulator.ai-pipeline.svc.cluster.local")
    token = base64.b64encode(
        f"{os.environ.get('JIRA_USER', 'admin')}:{os.environ.get('JIRA_TOKEN', 'admin')}".encode()).decode()
    status, payload = _request(base.rstrip("/") + path, headers={
        "Authorization": f"Basic {token}", "Accept": "application/json"})
    if status != 200:
        raise RuntimeError(f"Jira GET {path}: HTTP {status}: {payload[:300]!r}")
    return json.loads(payload)


def read_file(path: str):
    """Read a text file from the dashboard's volumes, or None if missing."""
    status, body = dashboard("/api/files/read?" + urllib.parse.urlencode({"path": path}))
    if status != 200 or body.get("binary"):
        return None
    return body.get("content")


def list_dir(path: str) -> list[dict]:
    status, body = dashboard("/api/files/list?" + urllib.parse.urlencode({"path": path}))
    return body.get("entries", []) if status == 200 else []


def emit(obj) -> None:
    print(json.dumps(obj, sort_keys=True))
