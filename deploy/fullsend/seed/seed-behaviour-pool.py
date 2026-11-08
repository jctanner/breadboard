#!/usr/bin/env python3
"""Seed the behaviour-test pool organisation on the GitHub emulator.

Fullsend's behaviour suite (run by deploy/fullsend/behaviour/run.sh with
ENVIRONMENT=external) leases slot repositories test-repo-01 ... test-repo-NN
in one organisation, creating each repository when it takes the slot and
deleting it when it gives the slot back. It also creates the organisation's
e2e-lock repository itself. So the organisation needs only to exist, with
the Fullsend role Apps installed on it for every repository, so that the
mint can issue a role token for any slot the suite creates.

The organisation comes from deploy/fullsend/behaviour/pool.env. The Apps
and their ids are the ones 18-deploy-fullsend-mint-dev.sh creates; their
installation here mirrors the one that script makes on the seed
organisation: repository selection "all", replacing any installation that
named specific repositories. The installation is given the App's own
permissions, read from the public App. Idempotent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emulator import BASE_URL, api_request  # noqa: E402

POOL_ENV = Path(__file__).resolve().parents[1] / "behaviour" / "pool.env"

# Role App ids, as created by deploy/scripts/18-deploy-fullsend-mint-dev.sh.
ROLE_APPS = {
    "triage": "1001", "scribe": "1002", "coder": "1003", "review": "1004",
    "fix": "1005", "fullsend": "1006", "retro": "1007", "prioritize": "1008",
}


def pool_org() -> str:
    for line in POOL_ENV.read_text().splitlines():
        key, _, value = line.strip().partition("=")
        if key == "BT_POOL_ORG" and value:
            return value.strip()
    sys.exit(f"{POOL_ENV}: BT_POOL_ORG is not set")


def admin(method: str, path: str) -> tuple[int, dict | list | None]:
    # The installation listing lives under the emulator's admin UI API,
    # which is outside /api/v3.
    import ssl
    import urllib.error
    import urllib.request

    from emulator import TOKEN

    request = urllib.request.Request(
        f"{BASE_URL}/admin/api{path}", method=method,
        headers={"Authorization": f"token {TOKEN}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, context=ssl._create_unverified_context()) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else None
    except urllib.error.HTTPError as exc:
        return exc.code, None


def ensure_org(org: str) -> None:
    status, _ = api_request("GET", f"/orgs/{org}")
    if status == 200:
        return
    if status != 404:
        sys.exit(f"GET /orgs/{org} failed: HTTP {status}")
    status, payload = api_request("POST", "/orgs", {"login": org, "name": org})
    if status not in (201, 422):
        sys.exit(f"creating organisation {org} failed: HTTP {status}: {payload}")


def ensure_installation(org: str, app_id: str) -> str:
    status, app = admin("GET", f"/apps/{app_id}")
    if status != 200 or not isinstance(app, dict):
        sys.exit(f"could not read App {app_id}: HTTP {status}; run 18-deploy-fullsend-mint-dev.sh first")
    for installation in app.get("installations") or []:
        if installation.get("owner") != org:
            continue
        if not installation.get("repositories"):
            return "present"
        status, _ = admin("DELETE", f"/apps/{app_id}/installations/{installation['id']}")
        if status != 204:
            sys.exit(f"could not replace installation {installation['id']} of App {app_id}: HTTP {status}")
    # The admin record carries no permissions; the public App does.
    status, public = api_request("GET", f"/apps/{app['slug']}")
    permissions = public.get("permissions") if status == 200 and isinstance(public, dict) else None
    if not permissions:
        sys.exit(f"could not read the permissions of App {app['slug']}: HTTP {status}")
    status, payload = api_request("POST", f"/admin/apps/{app_id}/installations", {
        "account_login": org,
        "account_type": "Organization",
        "repositories": [],
        "permissions": permissions,
    })
    if status not in (200, 201):
        sys.exit(f"could not install App {app_id} on {org}: HTTP {status}: {payload}")
    return "installed"


def main() -> None:
    org = pool_org()
    ensure_org(org)
    result = {role: ensure_installation(org, app_id) for role, app_id in ROLE_APPS.items()}
    print(json.dumps({"organisation": org, "role_apps": result}, indent=2))


if __name__ == "__main__":
    main()
