#!/usr/bin/env python3
"""Seed the non-admin actors the conformance path needs.

Every run so far was triggered by `admin`, who owns the repository and is
short-circuited to `admin` permission. The authorization gate has therefore
only ever been observed saying yes, which is not evidence that it is a gate.

This creates three distinct, non-admin identities on the target repository so
the gate can be exercised in both directions. Fullsend's dispatch authorizes an
`issues opened` event with `has_repo_permission "$ISSUE_USER_LOGIN" triage`,
which accepts `admin`, `maintain`, `write`/`push`, and `triage`, and rejects
everything else including `pull` and a missing collaborator record
(Fullsend ADR 0054).

| Actor                | Repository permission | Expected routing |
| -------------------- | --------------------- | ---------------- |
| `fullsend-triager`   | `triage`              | allowed          |
| `fullsend-reader`    | `pull`                | denied           |
| `fullsend-outsider`  | none                  | denied           |

Prints the actors and their tokens as JSON so a harness can open issues as
each. Tokens are development credentials for a local emulator only.

Work package 3 of the Fullsend integration conformance plan.
"""

from __future__ import annotations

import json
import sys

from emulator import ORG, REPO, api_request


FULL_NAME = f"{ORG}/{REPO}"

ACTORS = (
    {
        "login": "fullsend-triager",
        "name": "Fullsend Triager",
        "permission": "triage",
        "expected": "allowed",
        "why": "triage is the minimum the issues-opened path accepts",
    },
    {
        "login": "fullsend-reader",
        "name": "Fullsend Reader",
        "permission": "pull",
        "expected": "denied",
        "why": "read access is below the triage threshold",
    },
    {
        "login": "fullsend-outsider",
        "name": "Fullsend Outsider",
        "permission": None,
        "expected": "denied",
        "why": "not a collaborator at all; the permission lookup 404s",
    },
)


def ensure_user(actor: dict) -> None:
    status, payload = api_request("GET", f"/users/{actor['login']}")
    if status == 200:
        return
    status, payload = api_request(
        "POST",
        "/admin/users",
        {
            "login": actor["login"],
            "password": "conformance-dev-only",
            "name": actor["name"],
            "email": f"{actor['login']}@localhost",
        },
    )
    if status not in (201, 422):
        raise RuntimeError(f"create user {actor['login']} failed: HTTP {status}: {payload}")


def issue_token(login: str) -> str:
    status, payload = api_request(
        "POST",
        "/admin/tokens",
        {"login": login, "name": "conformance", "scopes": ["repo"]},
    )
    if status != 201 or not isinstance(payload, dict):
        raise RuntimeError(f"create token for {login} failed: HTTP {status}: {payload}")
    token = payload.get("token") or payload.get("raw") or ""
    if not token:
        raise RuntimeError(f"token response for {login} carried no token: {payload}")
    return token


def set_permission(login: str, permission: str | None) -> None:
    if permission is None:
        # Remove any prior collaborator record so "no access" really means it.
        api_request("DELETE", f"/repos/{FULL_NAME}/collaborators/{login}")
        return
    status, payload = api_request(
        "PUT",
        f"/repos/{FULL_NAME}/collaborators/{login}",
        {"permission": permission},
    )
    if status not in (201, 204):
        raise RuntimeError(
            f"grant {permission} to {login} failed: HTTP {status}: {payload}"
        )


def observed_role(login: str) -> str:
    status, payload = api_request(
        "GET", f"/repos/{FULL_NAME}/collaborators/{login}/permission"
    )
    if status == 404:
        return "none"
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"read permission for {login} failed: HTTP {status}: {payload}")
    return str(payload.get("role_name", "unknown"))


def main() -> None:
    seeded = []
    for actor in ACTORS:
        ensure_user(actor)
        set_permission(actor["login"], actor["permission"])
        seeded.append({
            "login": actor["login"],
            "granted": actor["permission"] or "none",
            "role_name": observed_role(actor["login"]),
            "expected": actor["expected"],
            "why": actor["why"],
            "token": issue_token(actor["login"]),
        })
    print(json.dumps({"repository": FULL_NAME, "actors": seeded}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        sys.exit(f"Conformance actor seed failed: {exc}")
