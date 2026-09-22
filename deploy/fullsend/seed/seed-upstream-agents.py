#!/usr/bin/env python3
"""Seed the upstream `fullsend-ai/agents` repository into the GitHub emulator.

Fullsend's CLI does not carry its agent definitions. It resolves the agents
repository to a commit and downloads the harness file from that commit, which
means a run with no agent configured needs this repository to exist wherever
the CLI is pointed. Without it the CLI reaches the public internet, is refused,
and reports `no config and agents-repo fallback unavailable`.

Unlike the Fullsend mirror next door, this one is whole. That mirror is a
narrow subset because only a handful of its paths are read; here the CLI picks
a file by agent name and the set of names is not ours to predict, so mirroring
selectively would just move the failure to the first agent nobody anticipated.

Gap G28 of the Fullsend integration conformance plan.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from emulator import TOKEN, api_request, run_git


# deploy/fullsend/seed/seed-upstream-agents.py -> parents[3] is the project root.
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "checkouts" / "fullsend-ai" / "agents"

UPSTREAM_ORG = "fullsend-ai"
UPSTREAM_REPO = "agents"
UPSTREAM_BRANCH = "main"

# Patches applied to the mirrored agent definitions.
#
# This is the third patch list in the project, and the split between them is
# not arbitrary. deploy/scripts/05i-build-fullsend.sh patches Go source before
# the CLI is compiled. seed-upstream-fullsend.py patches files a workflow reads
# at run time. These patch files the *agent harness* reads at run time, which
# live in a different repository, so they could not go in either of the others.
# A patch in the wrong list does nothing and does it silently.
PATCH_DIR = ROOT / "deploy" / "fullsend" / "patches" / "agents"
MIRROR_PATCHES = (
    "0001-accept-a-configured-github-host.patch",
    "0002-pass-the-forge-host-into-the-sandbox.patch",
    # Local substitution, not upstream-bound. See the patch header.
    "0003-local-allow-the-emulator-in-the-github-profile.patch",
    "0004-local-sandbox-image-with-the-internal-ca.patch",
)


def ensure_upstream_org() -> None:
    status, _ = api_request("GET", f"/orgs/{UPSTREAM_ORG}")
    if status == 200:
        return
    if status != 404:
        raise RuntimeError(f"GET organization failed: HTTP {status}")
    status, payload = api_request(
        "POST", "/orgs", {"login": UPSTREAM_ORG, "name": UPSTREAM_ORG}
    )
    if status not in (201, 422):
        raise RuntimeError(f"POST organization failed: HTTP {status}: {payload}")


def ensure_upstream_repo() -> None:
    status, _ = api_request("GET", f"/repos/{UPSTREAM_ORG}/{UPSTREAM_REPO}")
    if status == 200:
        return
    if status != 404:
        raise RuntimeError(f"GET repository failed: HTTP {status}")
    status, payload = api_request(
        "POST",
        f"/orgs/{UPSTREAM_ORG}/repos",
        {
            "name": UPSTREAM_REPO,
            "description": "Mirror of the Fullsend agent definitions",
            "private": False,
        },
    )
    if status not in (201, 422):
        raise RuntimeError(f"POST repository failed: HTTP {status}: {payload}")


def collect_sources() -> list[tuple[Path, str]]:
    """Every tracked file, taken from git rather than the working tree."""
    if not (SOURCE / ".git").exists():
        raise RuntimeError(
            f"Fullsend agents checkout is missing: {SOURCE}. "
            "Clone fullsend-ai/agents into checkouts/fullsend-ai/ first."
        )
    listed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=SOURCE, capture_output=True, check=True,
    ).stdout.decode()
    collected = []
    for relative in filter(None, listed.split("\0")):
        path = SOURCE / relative
        if path.is_file():
            collected.append((path, relative))
    if not collected:
        raise RuntimeError(f"no tracked files found in {SOURCE}")
    return collected


def apply_mirror_patches(directory: Path) -> None:
    """Apply the local patches to the mirrored copy.

    A patch that no longer applies is an error rather than a warning. Mirroring
    unpatched harness scripts silently would put the failure back where it was
    hardest to read: inside an agent's pre-script, several jobs after the thing
    that actually went wrong.
    """
    for name in MIRROR_PATCHES:
        patch = PATCH_DIR / name
        if not patch.is_file():
            raise RuntimeError(f"mirror patch is missing: {patch}")
        result = subprocess.run(
            ["git", "apply", str(patch)],
            cwd=directory, capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"mirror patch {name} does not apply to the current agents "
                f"checkout: {result.stderr.strip()}"
            )
        print(f"applied mirror patch {name}")


def main() -> None:
    ensure_upstream_org()
    ensure_upstream_repo()

    sources = collect_sources()
    revision = run_git(SOURCE, "rev-parse", "HEAD").stdout.strip()
    remote = (
        f"https://x-access-token:{TOKEN}@github.local/"
        f"{UPSTREAM_ORG}/{UPSTREAM_REPO}.git"
    )

    with tempfile.TemporaryDirectory(prefix="fullsend-agents-mirror-") as temp:
        directory = Path(temp)
        run_git(directory, "init", f"--initial-branch={UPSTREAM_BRANCH}")
        run_git(directory, "config", "user.name", "Breadboard Fullsend Seed")
        run_git(directory, "config", "user.email", "breadboard-fullsend-seed@localhost")
        run_git(directory, "remote", "add", "origin", remote)

        for _ in range(10):
            fetched = run_git(directory, "fetch", "origin", UPSTREAM_BRANCH, check=False)
            if fetched.returncode == 0:
                run_git(directory, "reset", "--hard", "FETCH_HEAD")
                break
            time.sleep(2)

        for origin, relative in sources:
            destination = directory / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin, destination)
            destination.chmod(origin.stat().st_mode & 0o777)

        apply_mirror_patches(directory)

        run_git(directory, "add", "-A")
        if run_git(directory, "diff", "--cached", "--quiet", check=False).returncode == 0:
            print(
                f"agents mirror already current at "
                f"{UPSTREAM_ORG}/{UPSTREAM_REPO}@{UPSTREAM_BRANCH} "
                f"({len(sources)} files, source {revision[:8]})"
            )
            return

        run_git(
            directory, "commit", "-m",
            f"Mirror Fullsend agent definitions from {revision[:8]}",
        )
        pushed = None
        for _ in range(10):
            pushed = run_git(directory, "push", "-u", "origin", UPSTREAM_BRANCH, check=False)
            if pushed.returncode == 0:
                break
            time.sleep(2)
        if pushed is None or pushed.returncode != 0:
            raise RuntimeError(pushed.stderr if pushed else "push did not run")

        head = run_git(directory, "rev-parse", "HEAD").stdout.strip()
        print(
            f"mirrored {len(sources)} files to "
            f"{UPSTREAM_ORG}/{UPSTREAM_REPO}@{UPSTREAM_BRANCH} "
            f"(commit {head[:8]}, source {revision[:8]})"
        )


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        sys.exit(f"Agents mirror seed failed: {exc}")
