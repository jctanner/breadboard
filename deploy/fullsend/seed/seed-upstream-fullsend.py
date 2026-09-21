#!/usr/bin/env python3
"""Seed the upstream `fullsend-ai/fullsend` repository into the GitHub emulator.

The per-repo shim a target repository carries calls

    uses: fullsend-ai/fullsend/.github/workflows/reusable-dispatch.yml@main

The emulator resolves a cross-repo reusable workflow by looking the owner/repo
up in its database and reading the file out of that repository's git tree at
the requested ref. Without the repository present the call resolves to a
placeholder job with no steps, which never leaves the queue.

This mirrors the subset of the Fullsend source that the dispatch chain reads:
the reusable workflows themselves, the composite actions and scripts they call,
the root `action.yml` agent entry point, and the per-repo scaffold the
"checkout upstream defaults" step expects. It is a mirror of a local checkout,
not a network fetch, and it does not pretend to be the whole repository.

Gap A1 of the Fullsend integration conformance plan.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from emulator import TOKEN, api_request, run_git


# deploy/fullsend/seed/seed-upstream-fullsend.py -> parents[3] is the project root.
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "checkouts" / "fullsend-ai" / "fullsend"

UPSTREAM_ORG = "fullsend-ai"
UPSTREAM_REPO = "fullsend"
UPSTREAM_BRANCH = "main"

# Paths the dispatch chain reads. Kept deliberately narrow so the mirror stays
# reviewable and fast; widen it when a later wave needs more.
MIRRORED_PATHS = (
    ".github/workflows",
    ".github/actions",
    ".github/scripts",
    "internal/scaffold/fullsend-repo",
    "action.yml",
)

# Patches applied to the mirrored files.
#
# These are separate from the patch list in
# deploy/scripts/05i-build-fullsend.sh, and the split is not arbitrary: that
# list patches Go source before the Fullsend binary is compiled, while these
# change files a workflow reads at run time out of this mirror. A patch belongs
# in exactly one of the two, depending on whether it survives compilation.
#
# Each is written to be sent upstream unchanged. Keeping them here rather than
# in the checkout keeps the checkout clean and keeps the deviation reviewable.
PATCH_DIR = ROOT / "deploy" / "fullsend" / "patches"
MIRROR_PATCHES = (
    "0003-honor-github-api-and-server-url.patch",
    "0004-skip-local-sandbox-host-setup.patch",
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
            "description": "Mirror of the Fullsend reusable workflows and actions",
            "private": False,
        },
    )
    if status not in (201, 422):
        raise RuntimeError(f"POST repository failed: HTTP {status}: {payload}")


def collect_sources() -> list[tuple[Path, str]]:
    """Return (absolute source, repo-relative destination) pairs to mirror."""
    if not (SOURCE / ".git").exists():
        raise RuntimeError(
            f"Fullsend checkout is missing: {SOURCE}. "
            "Clone fullsend-ai into checkouts/ first."
        )
    collected: list[tuple[Path, str]] = []
    for relative in MIRRORED_PATHS:
        origin = SOURCE / relative
        if origin.is_file():
            collected.append((origin, relative))
        elif origin.is_dir():
            for path in sorted(origin.rglob("*")):
                if path.is_file():
                    collected.append((path, str(path.relative_to(SOURCE))))
        else:
            raise RuntimeError(f"required Fullsend path is missing: {origin}")
    return collected


def apply_mirror_patches(directory: Path) -> None:
    """Apply the local patches to the mirrored copy.

    A patch that no longer applies is an error rather than a warning. Silently
    mirroring unpatched files would leave the emulator serving a workflow that
    reaches for github.com, and the resulting failure appears several jobs
    later as an unexplained 401.
    """
    for name in MIRROR_PATCHES:
        patch = PATCH_DIR / name
        if not patch.is_file():
            raise RuntimeError(f"mirror patch is missing: {patch}")
        result = subprocess.run(
            ["git", "apply", str(patch)],
            cwd=directory,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"mirror patch {name} does not apply to the current Fullsend "
                f"checkout: {result.stderr.strip()}\n"
                "Rebase, replace, or drop it - see work package 1 in "
                ".ledger/plans/fullsend-integration-conformance-plan.md."
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

    with tempfile.TemporaryDirectory(prefix="fullsend-upstream-mirror-") as temp:
        directory = Path(temp)
        run_git(directory, "init", f"--initial-branch={UPSTREAM_BRANCH}")
        run_git(directory, "config", "user.name", "Breadboard Fullsend Seed")
        run_git(directory, "config", "user.email", "breadboard-fullsend-seed@localhost")
        run_git(directory, "remote", "add", "origin", remote)

        fetched = None
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
                f"upstream mirror already current at "
                f"{UPSTREAM_ORG}/{UPSTREAM_REPO}@{UPSTREAM_BRANCH} "
                f"({len(sources)} files, source {revision[:8]})"
            )
            return

        run_git(
            directory,
            "commit",
            "-m",
            f"Mirror Fullsend dispatch chain from {revision[:8]}",
        )
        pushed = None
        for _ in range(10):
            pushed = run_git(
                directory, "push", "-u", "origin", UPSTREAM_BRANCH, check=False
            )
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
        sys.exit(f"Fullsend upstream seed failed: {exc}")
