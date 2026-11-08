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

It also seeds the suite's human test actors the way Fullsend's
hack/setup-new-e2e-org.sh does on GitHub. Access comes from organization
roles, which cover slot repositories created later, and not from collaborator
grants, which each delete-and-recreate would drop:

- the write actor is a member holding all_repo_write;
- the triage actor is a member holding all_repo_triage;
- the outsider is kept out of the organization.

Their tokens are written to deploy/fullsend/behaviour/.env.actors (ignored by
git; development credentials for the local emulator only) as
TEST_ACTOR_WRITE_PAT, TEST_ACTOR_TRIAGE_PAT and TEST_ACTOR_OUTSIDER_PAT,
which deploy/fullsend/behaviour/run.sh exports. A token that still
authenticates as its actor is kept, so reseeding does not pile up tokens.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emulator import BASE_URL, api_request  # noqa: E402

POOL_ENV = Path(__file__).resolve().parents[1] / "behaviour" / "pool.env"
ACTORS_ENV = Path(__file__).resolve().parents[1] / "behaviour" / ".env.actors"

# (env var, login, all-repository role or None for the outsider)
ACTORS = (
    ("TEST_ACTOR_WRITE_PAT", "bt-write-actor", "all_repo_write"),
    ("TEST_ACTOR_TRIAGE_PAT", "bt-triage-actor", "all_repo_triage"),
    ("TEST_ACTOR_OUTSIDER_PAT", "bt-outsider", None),
)

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


def read_actor_tokens() -> dict[str, str]:
    tokens = {}
    if ACTORS_ENV.exists():
        for line in ACTORS_ENV.read_text().splitlines():
            key, _, value = line.strip().partition("=")
            if key and value and not key.startswith("#"):
                tokens[key] = value
    return tokens


def token_login(token: str) -> str | None:
    import ssl
    import urllib.error
    import urllib.request

    from emulator import API_URL

    request = urllib.request.Request(f"{API_URL}/user", headers={"Authorization": f"token {token}"})
    try:
        with urllib.request.urlopen(request, context=ssl._create_unverified_context()) as response:
            return json.loads(response.read()).get("login")
    except urllib.error.HTTPError:
        return None


def ensure_user(login: str) -> None:
    status, _ = api_request("GET", f"/users/{login}")
    if status == 200:
        return
    status, payload = api_request("POST", "/admin/users", {
        "login": login, "password": "behaviour-dev-only",
        "name": login, "email": f"{login}@localhost",
    })
    if status not in (201, 422):
        sys.exit(f"creating user {login} failed: HTTP {status}: {payload}")


def ensure_token(login: str, current: str | None) -> tuple[str, str]:
    if current and token_login(current) == login:
        return current, "kept"
    status, payload = api_request("POST", "/admin/tokens", {
        "login": login, "name": "behaviour-tests", "scopes": ["repo", "read:org", "workflow"],
    })
    token = (payload.get("token") or payload.get("raw")) if status == 201 and isinstance(payload, dict) else None
    if not token:
        sys.exit(f"creating a token for {login} failed: HTTP {status}: {payload}")
    return token, "issued"


def role_ids(org: str) -> dict[str, int]:
    status, payload = api_request("GET", f"/orgs/{org}/organization-roles")
    if status != 200 or not isinstance(payload, dict):
        sys.exit(f"listing organization roles of {org} failed: HTTP {status}; "
                 "the emulator needs organization roles (BT-E4)")
    return {role["name"]: role["id"] for role in payload.get("roles", [])}


def ensure_actor_access(org: str, login: str, role: str | None, roles: dict[str, int]) -> str:
    if role is None:
        # The outsider must stay outside: no membership, so no role either.
        status, _ = api_request("DELETE", f"/orgs/{org}/memberships/{login}")
        if status not in (204, 404):
            sys.exit(f"removing {login} from {org} failed: HTTP {status}")
        return "outside"
    status, payload = api_request("PUT", f"/orgs/{org}/memberships/{login}", {"role": "member"})
    if status != 200:
        sys.exit(f"adding {login} to {org} failed: HTTP {status}: {payload}")
    status, payload = api_request("PUT", f"/orgs/{org}/organization-roles/users/{login}/{roles[role]}")
    if status != 204:
        sys.exit(f"assigning {role} to {login} in {org} failed: HTTP {status}: {payload}")
    # Then exactly that role: one left over from an earlier seed (or a hand
    # edit) would give more access than the actor is meant to have and quietly
    # invalidate the scenarios that expect a refusal. The intended role is
    # assigned first, so a failure here never leaves the actor with less.
    for other, role_id in roles.items():
        if other == role:
            continue
        status, _ = api_request("DELETE", f"/orgs/{org}/organization-roles/users/{login}/{role_id}")
        if status != 204:
            sys.exit(f"removing {other} from {login} in {org} failed: HTTP {status}")
    return role


def ensure_actors(org: str) -> dict[str, dict[str, str]]:
    roles = role_ids(org)
    current = read_actor_tokens()
    tokens, result = {}, {}
    for env, login, role in ACTORS:
        ensure_user(login)
        access = ensure_actor_access(org, login, role, roles)
        tokens[env], how = ensure_token(login, current.get(env))
        result[login] = {"access": access, "token": how}
    content = (
        "# Behaviour-test actor tokens for the local GitHub emulator; written by\n"
        "# deploy/fullsend/seed/seed-behaviour-pool.py. Not for any real forge.\n"
        + "".join(f"{env}={tokens[env]}\n" for env, _, _ in ACTORS)
    )
    # Created 0600 from the start, then renamed over the old file, so the
    # tokens are never readable by others, not even briefly.
    import os

    temporary = ACTORS_ENV.with_name(ACTORS_ENV.name + ".tmp")
    temporary.unlink(missing_ok=True)
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        handle.write(content)
    os.replace(temporary, ACTORS_ENV)
    return result


def main() -> None:
    org = pool_org()
    ensure_org(org)
    result = {role: ensure_installation(org, app_id) for role, app_id in ROLE_APPS.items()}
    actors = ensure_actors(org)
    print(json.dumps({"organisation": org, "role_apps": result, "actors": actors}, indent=2))


if __name__ == "__main__":
    main()
