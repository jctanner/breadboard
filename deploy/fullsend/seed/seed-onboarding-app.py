#!/usr/bin/env python3
"""Seed the GitHub App the dashboard onboards repositories with.

The conformance plan's rule for onboarding is a short-lived App installation
token with repository and workflow write scope, never a stored personal
token. The seeded "Fullsend Triage" App carries `contents: read` and cannot
write a scaffold, so this seeds a second App for the dashboard's own use:

- installed on the seed organisation with repository selection "all", so a
  repository that does not exist yet when this runs can still be onboarded;
- with the permissions a scaffold needs and no more: contents, workflows,
  variables, secrets, and pull requests to write, metadata to read;
- its private key written to a Kubernetes Secret the dashboard mounts, so
  the dashboard signs a ten-minute JWT per operation and exchanges it for a
  one-hour token scoped to the one repository. The key never sits in the
  dashboard's environment and no token outlives the run.

Idempotent: an existing App and installation are reused, and the Secret is
applied every time so a regenerated key replaces the old one.
"""

from __future__ import annotations

import json
import os
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request

from emulator import BASE_URL, ORG, TOKEN, api_request, ensure_org


APP_ID = "1100"
APP_SLUG = "breadboard-onboarding"
APP_NAME = "Breadboard Onboarding"
PERMISSIONS = {
    "contents": "write",
    "workflows": "write",
    "actions_variables": "write",
    "secrets": "write",
    "pull_requests": "write",
    "metadata": "read",
}
NAMESPACE = os.environ.get("FULLSEND_ONBOARD_APP_NAMESPACE", "ai-pipeline")
SECRET = os.environ.get("FULLSEND_ONBOARD_APP_SECRET", "fullsend-onboarding-app")


def private_key() -> str:
    """The App's key from the emulator's admin API (site admin only)."""
    request = urllib.request.Request(
        f"{BASE_URL}/admin/api/apps/{APP_ID}/private-key",
        headers={"Authorization": f"token {TOKEN}", "User-Agent": "breadboard-fullsend-seed"},
    )
    try:
        with urllib.request.urlopen(request, context=ssl._create_unverified_context()) as response:
            return str(json.loads(response.read())["private_key"])
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"could not read the App's private key: HTTP {exc.code}")


def write_secret(app_id: str, installation_id: int, key: str) -> str:
    if not shutil.which("kubectl"):
        return "kubectl not found; Secret not written"
    manifest = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": SECRET, "namespace": NAMESPACE,
                     "labels": {"breadboard.dev/role": "fullsend"}},
        "type": "Opaque",
        "stringData": {"app-id": app_id, "installation-id": str(installation_id), "private-key": key},
    }
    result = subprocess.run(
        ["kubectl", "apply", "-f", "-"], input=json.dumps(manifest), capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"kubectl apply failed: {result.stderr.strip()}")
    return result.stdout.strip()


def main() -> None:
    ensure_org()
    status, app = api_request("POST", "/admin/apps", {
        "app_id": APP_ID, "name": APP_NAME, "slug": APP_SLUG, "permissions": PERMISSIONS,
    })
    if status == 409:
        status, app = api_request("GET", f"/admin/apps/{APP_ID}")
    if status not in (200, 201) or not isinstance(app, dict):
        raise RuntimeError(f"onboarding App bootstrap failed: HTTP {status}: {app}")

    status, installation = api_request("POST", f"/admin/apps/{APP_ID}/installations", {
        "account_login": ORG, "account_type": "Organization",
        "repositories": [], "permissions": PERMISSIONS,
    })
    if status not in (200, 201) or not isinstance(installation, dict):
        raise RuntimeError(f"onboarding App installation failed: HTTP {status}: {installation}")

    key = str(app.get("private_key") or "") or private_key()
    written = write_secret(APP_ID, installation["id"], key)
    print(json.dumps({
        "status": "seeded", "app_id": APP_ID, "app_slug": APP_SLUG, "bot": f"{APP_SLUG}[bot]",
        "installation_id": installation["id"], "organization": ORG,
        "repository_selection": "all", "secret": f"{NAMESPACE}/{SECRET}", "kubectl": written,
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        sys.exit(f"Onboarding App seed failed: {exc}")
