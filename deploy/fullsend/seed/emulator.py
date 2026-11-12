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
import shutil
import os
import ssl
import re
import time
import tempfile
import subprocess
from urllib.parse import urlsplit, urlunsplit, quote
from pathlib import Path


DOMAIN = os.environ.get("BREADBOARD_DOMAIN", "local")
BASE_URL = os.environ.get("GITHUB_EMULATOR_URL", f"https://github.{DOMAIN}").rstrip("/")
API_URL = f"{BASE_URL}/api/v3"
TOKEN = os.environ.get("GITHUB_EMULATOR_TOKEN", "ghp_admin_default_token")
# The conformance target by default. A seeder that is also the right tool
# for another repository - the allowlist one, for a repository onboarded
# through the dashboard - takes the target from the environment.
ORG = os.environ.get("FULLSEND_SEED_ORG", "fullsend-dev")
REPO = os.environ.get("FULLSEND_SEED_REPO", "triage-target")


def ssl_context() -> ssl.SSLContext:
    """Use verified HTTPS, preferring an explicitly selected public CA."""
    return ssl.create_default_context(cafile=os.getenv("BREADBOARD_CA_FILE") or None)


def git_remote(owner: str, repo: str) -> str:
    parsed = urlsplit(BASE_URL)
    if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RuntimeError("GITHUB_EMULATOR_URL must be an HTTP(S) base URL without credentials, query, or fragment")
    auth = f"x-access-token:{quote(TOKEN, safe='')}@{parsed.netloc}"
    return urlunsplit((parsed.scheme, auth, f"{parsed.path.rstrip('/')}/{owner}/{repo}.git", "", ""))


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
    context = ssl_context()
    # Only retry the emulator's explicit lock response on replay-safe operations.
    # Organization/repository names are unique; their callers accept duplicate 422s.
    replay_safe = method.upper() in {"GET", "HEAD", "PUT", "DELETE"} or (
        method.upper() == "POST" and (path == "/orgs" or re.fullmatch(r"/orgs/[^/]+/repos", path))
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                payload = response.read()
                return response.status, json.loads(payload) if payload else None
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            try:
                decoded = json.loads(payload) if payload else None
            except (json.JSONDecodeError, UnicodeDecodeError):
                decoded = payload.decode(errors="replace")
            exc.close()
            errors = decoded.get("errors") if isinstance(decoded, dict) else None
            locked = isinstance(errors, list) and any(
                isinstance(error, dict) and error.get("code") == "sqlite_locked"
                for error in errors
            ) and "cannot be replayed safely" not in str(decoded.get("message", ""))
            if exc.code == 503 and locked and replay_safe and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            return exc.code, decoded


def ensure_org() -> None:
    status, _ = api_request("GET", f"/orgs/{ORG}")
    if status == 200:
        return
    if status != 404:
        raise RuntimeError(f"GET organization failed: HTTP {status}")
    status, payload = api_request("POST", "/orgs", {"login": ORG, "name": ORG})
    if status == 422:
        found, _ = api_request("GET", f"/orgs/{ORG}")
        if found != 200:
            raise RuntimeError(f"Organization conflict was not confirmed: HTTP {found}")
    elif status != 201:
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
    if status == 422:
        found, existing = api_request("GET", f"/repos/{ORG}/{REPO}")
        if found != 200 or not isinstance(existing, dict) or not existing.get("default_branch"):
            raise RuntimeError(f"Repository conflict was not confirmed with a default branch: HTTP {found}")
    elif status != 201:
        raise RuntimeError(f"POST repository failed: HTTP {status}: {payload}")


def git_env() -> dict[str, str]:
    env = os.environ.copy()
    # Git has many environment controls; retain only its stricter ownership
    # test hook, never inherited config, transport, tracing or execution overrides.
    for key in list(env):
        if (key.startswith("GIT_") and key != "GIT_TEST_ASSUME_DIFFERENT_OWNER") or key == "SSH_ASKPASS":
            env.pop(key, None)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    if os.getenv("BREADBOARD_CA_FILE"):
        env["GIT_SSL_CAINFO"] = os.environ["BREADBOARD_CA_FILE"]
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run_git(directory: Path, *args: str, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    # Old Git versions require safe.directory in global rather than -c scope.
    # Build an isolated, short-lived config containing only this controlled repo.
    with tempfile.TemporaryDirectory(prefix="breadboard-seed-git-") as temporary:
        config = Path(temporary) / "config"
        env = git_env()
        subprocess.run(
            ["git", "config", "--file", str(config), "--add", "safe.directory", str(directory.resolve())],
            cwd=temporary, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        config.chmod(0o600)
        env["GIT_CONFIG_GLOBAL"] = str(config)
        return subprocess.run(
            ["git", "-c", "core.hooksPath=" + os.devnull, "-c", "core.fsmonitor=false",
             "-c", "credential.helper=", "-c", "protocol.ext.allow=never",
             "-c", "http.sslVerify=true", *args], cwd=directory, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check, input=input_text,
        )


def seed_source_path(root: Path, relative: str, *, allow_final_symlink: bool = False) -> Path:
    """Reject ancestor symlinks/escapes; optionally preserve a final link."""
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise RuntimeError("Mirror source path must stay inside its checkout")
    base = root.resolve()
    current = base
    for index, part in enumerate(relative_path.parts):
        current = current / part
        if current.is_symlink():
            if allow_final_symlink and index == len(relative_path.parts) - 1:
                return current  # The caller may readlink, never read its target.
            raise RuntimeError(f"Mirror source symlink is not allowed: {relative}")
    if not current.resolve().is_relative_to(base):
        raise RuntimeError("Mirror source escapes its checkout")
    return current


def copy_mirror_source(root: Path, relative: str, destination: Path) -> None:
    """Copy regular bytes or symlink text, never a symlink target's bytes."""
    origin = seed_source_path(root, relative, allow_final_symlink=True)
    if origin.is_symlink():
        destination.symlink_to(os.readlink(origin))
    else:
        shutil.copyfile(origin, destination)
        destination.chmod(origin.stat().st_mode & 0o777)


def clear_mirror_worktree(directory: Path) -> None:
    """Remove fetched content without following mirror-controlled symlinks."""
    for entry in directory.iterdir():
        if entry.name == ".git":
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()



FULLSEND_SHIM = """---
# This file is managed by Fullsend. Do not edit it directly.
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
    with:
      event_action: ${{ github.event.action }}
      mint_url: https://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080
      runner_image: fullsend
    secrets: inherit
"""
