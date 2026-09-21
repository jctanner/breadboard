#!/usr/bin/env python3
"""Shared GitHub-emulator helpers for the Fullsend conformance seed scripts.

Trimmed from the former demo folder's `m1_seed.py` (removed by work package 8
of the Fullsend integration conformance plan). This module
keeps only the helpers that `seed-github-app.py`, `mirror-fullsend-workflows.py`,
and `onboard-repo.py` actually import: the emulator API client, the org/repo
bootstrap helpers, and the local git helper used to push fixture content
through the emulator's Git transport.
"""

from __future__ import annotations

import json
import os
import ssl
import subprocess
from pathlib import Path


BASE_URL = os.environ.get("GITHUB_EMULATOR_URL", "https://github.local").rstrip("/")
API_URL = f"{BASE_URL}/api/v3"
TOKEN = os.environ.get("GITHUB_EMULATOR_TOKEN", "ghp_admin_default_token")
ORG = "fullsend-dev"
REPO = "triage-target"


def api_request(method: str, path: str, body: dict | None = None) -> tuple[int, dict | list | None]:
    import urllib.error
    import urllib.request

    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {TOKEN}",
        "User-Agent": "breadboard-fullsend-seed",
    }
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        f"{API_URL}{path}", data=data, headers=headers, method=method,
    )
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(request, context=context) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else None
    except urllib.error.HTTPError as exc:
        payload = exc.read()
        try:
            decoded = json.loads(payload) if payload else None
        except json.JSONDecodeError:
            decoded = payload.decode(errors="replace")
        return exc.code, decoded


def ensure_org() -> None:
    status, _ = api_request("GET", f"/orgs/{ORG}")
    if status == 200:
        return
    if status != 404:
        raise RuntimeError(f"GET organization failed: HTTP {status}")
    status, payload = api_request("POST", "/orgs", {"login": ORG, "name": ORG})
    if status not in (201, 422):
        raise RuntimeError(f"POST organization failed: HTTP {status}: {payload}")


def ensure_repo() -> None:
    status, _ = api_request("GET", f"/repos/{ORG}/{REPO}")
    if status == 200:
        return
    if status != 404:
        raise RuntimeError(f"GET repository failed: HTTP {status}")
    status, payload = api_request(
        "POST", f"/orgs/{ORG}/repos",
        {"name": REPO, "description": "Minimal Fullsend development target", "private": False},
    )
    if status not in (201, 422):
        raise RuntimeError(f"POST repository failed: HTTP {status}: {payload}")


def git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_SSL_NO_VERIFY"] = "true"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run_git(directory: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=directory, env=git_env(), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check,
    )
