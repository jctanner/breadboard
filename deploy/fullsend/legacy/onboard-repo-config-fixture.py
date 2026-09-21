#!/usr/bin/env python3
"""Enroll one existing GitHub-emulator repository in the config-repo fixture
(formerly "M11"'s `onboard_repo.py`).

This is a named legacy compatibility fixture, not the conformance onboarding
path. It hand-rolls fake per-role GitHub App installations and grants bot
collaborators, which is the deprecated per-organization installation shape
(Fullsend ADR 0044). Breakpoint B7 in
`.ledger/plans/fullsend-integration-conformance-plan.md` requires the real
dashboard onboarding action to invoke the actual `fullsend` CLI
(`fullsend github setup OWNER/REPO`) against the emulator, not this script.
Do not reuse this file for work package 7.

The shim workflow content below is inlined from the former
`m11_seed.py` (deleted by work package 8) since this is now the only
consumer.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seed"))
from emulator import api_request  # noqa: E402


TARGET_WORKFLOW = ".github/workflows/fullsend.yaml"
SHIM_WORKFLOW = r'''---
# This file is managed by Fullsend. Do not edit it directly.
# Development mirror of the production workflow-call shim.
name: fullsend

on:
  issues:
    types: [opened, edited, labeled]
  issue_comment:
    types: [created]
  pull_request_target:
    types: [opened, synchronize, ready_for_review, closed, labeled, unlabeled]
  pull_request_review:
    types: [submitted]

permissions: {}

jobs:
  dispatch:
    concurrency:
      group: >-
        fullsend-dispatch-${{ github.event.issue.number || github.event.pull_request.number }}-${{
          github.event.action == 'labeled' && format('label-{0}', github.event.label.name) || 'dispatch'
        }}
      cancel-in-progress: false
    if: >-
      (github.event_name != 'pull_request_target' && github.event_name != 'pull_request_review') ||
      github.event.pull_request.state == 'open' || github.event.action == 'closed'
    uses: fullsend-ai/fullsend/.github/workflows/reusable-dispatch.yml@main
    secrets: inherit
'''

ROLE_APPS = {
    "triage": (
        "1001",
        {"contents": "read", "issues": "write", "metadata": "read"},
    ),
    "code": (
        "1003",
        {
            "contents": "write",
            "issues": "write",
            "pull_requests": "write",
            "metadata": "read",
        },
    ),
    "review": (
        "1004",
        {
            "contents": "read",
            "issues": "write",
            "pull_requests": "write",
            "metadata": "read",
        },
    ),
    "fix": (
        "1005",
        {
            "contents": "write",
            "issues": "write",
            "pull_requests": "write",
            "metadata": "read",
        },
    ),
}

# The development mint returns bot-owned PATs rather than installation tokens.
# These grants bridge that local-only difference. Production App installations
# provide repository authorization directly and do not need collaborators.
DEVELOPMENT_ROLE_BOTS = (
    "fullsend-code[bot]",
    "fullsend-review[bot]",
    "fullsend-fix[bot]",
)


def protection_body() -> dict:
    """Require Review approval so Code can safely queue GitHub auto-merge."""
    return {
        "required_status_checks": None,
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "required_approving_review_count": 1,
            "require_last_push_approval": False,
        },
        "restrictions": None,
        "required_linear_history": False,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }


def _require(status: int, expected: tuple[int, ...], operation: str, payload):
    if status not in expected:
        raise RuntimeError(f"{operation} failed: HTTP {status}: {payload}")
    return payload


def _account_type(owner: str) -> str:
    status, _ = api_request("GET", f"/orgs/{quote(owner, safe='')}")
    if status == 200:
        return "Organization"
    status, payload = api_request("GET", f"/users/{quote(owner, safe='')}")
    _require(status, (200,), f"resolve account {owner}", payload)
    return "User"


def _ensure_shim(full_name: str) -> bool:
    path = quote(TARGET_WORKFLOW, safe="/")
    status, existing = api_request("GET", f"/repos/{full_name}/contents/{path}")
    sha = None
    if status == 200 and isinstance(existing, dict):
        sha = existing.get("sha")
        encoded = str(existing.get("content", "")).replace("\n", "")
        try:
            current = base64.b64decode(encoded).decode()
        except (ValueError, UnicodeDecodeError):
            current = ""
        if current == SHIM_WORKFLOW:
            return False
    elif status != 404:
        raise RuntimeError(f"inspect Fullsend shim failed: HTTP {status}: {existing}")

    body = {
        "message": "Install managed Fullsend event shim",
        "content": base64.b64encode(SHIM_WORKFLOW.encode()).decode(),
        "branch": "main",
    }
    if sha:
        body["sha"] = sha
    status, payload = api_request("PUT", f"/repos/{full_name}/contents/{path}", body)
    _require(status, (200, 201), "install Fullsend shim", payload)
    return True


def _ensure_installations(full_name: str, owner: str, account_type: str) -> list[str]:
    installed = []
    for role, (app_id, permissions) in ROLE_APPS.items():
        status, payload = api_request(
            "POST",
            f"/admin/apps/{app_id}/installations",
            {
                "account_login": owner,
                "account_type": account_type,
                "repositories": [full_name],
                "permissions": permissions,
            },
        )
        _require(status, (200, 201), f"install {role} App", payload)
        repositories = set(payload.get("repositories", [])) if isinstance(payload, dict) else set()
        if full_name not in repositories:
            raise RuntimeError(
                f"{role} App already has an installation for {owner}, but it does "
                f"not include {full_name}; update that selected-repository installation"
            )
        installed.append(role)
    return installed


def _ensure_bot_access(full_name: str) -> list[str]:
    granted = []
    for login in DEVELOPMENT_ROLE_BOTS:
        status, payload = api_request(
            "PUT",
            f"/repos/{full_name}/collaborators/{quote(login, safe='')}",
            {"permission": "push"},
        )
        _require(status, (201, 204), f"grant {login} repository access", payload)
        granted.append(login)
    return granted


def onboard(full_name: str) -> dict:
    if full_name.count("/") != 1:
        raise RuntimeError("repository must be OWNER/REPO")
    owner, _repo = full_name.split("/", 1)
    status, payload = api_request("GET", f"/repos/{full_name}")
    _require(status, (200,), f"find repository {full_name}", payload)

    account_type = _account_type(owner)
    shim_changed = _ensure_shim(full_name)
    installations = _ensure_installations(full_name, owner, account_type)
    bots = _ensure_bot_access(full_name)
    status, protection = api_request(
        "PUT", f"/repos/{full_name}/branches/main/protection", protection_body()
    )
    _require(status, (200,), "configure main branch protection", protection)

    return {
        "status": "onboarded",
        "repository": full_name,
        "shim_changed": shim_changed,
        "apps": installations,
        "development_role_bots": bots,
        "required_approving_review_count": 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="existing emulator repository as OWNER/REPO")
    args = parser.parse_args()
    print(json.dumps(onboard(args.repository), indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        raise SystemExit(f"Fullsend onboarding failed: {exc}") from exc
