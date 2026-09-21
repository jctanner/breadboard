#!/usr/bin/env python3
"""Commit the prebuilt Fullsend binary into the target repository.

Fullsend's agent action decides how to install the CLI in three steps, in
order: a binary already committed in the workspace, a release matching the
workflow's own commit, or a build from source. The local stack seeds neither of
the first two, so every run fell through to the third and compiled the CLI.
That is the action's last resort, reached here by omission rather than by
anyone choosing it.

This seeds the first. `.fullsend/bin/fullsend` is the path the action checks for
a per-repo install, and it is what `fullsend admin install --vendor` writes.
Finding it there makes the action exit before it makes any network call at all.

Two things worth being explicit about.

The binary is the one `deploy/scripts/05i-build-fullsend.sh` compiled for the
runner image, not a second build that resembles it, so what a run executes and
what the image ships cannot drift apart.

This is a deliberate deviation from what a production install does. Production
downloads a release asset matching the workflow commit; vendoring is Fullsend's
pinned or air-gapped mode. Both are supported, but only the release path is the
common one, and reproducing that locally needs release-asset endpoints the
emulator does not have. See the Fullsend integration conformance plan.

The push uses git rather than the contents API on purpose: the action looks for
a regular file and chmods it later, but committing through a git tree keeps the
executable bit, which the contents API drops.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from emulator import ORG, REPO, TOKEN, run_git


# deploy/fullsend/seed/seed-vendored-binary.py -> parents[3] is the project root.
ROOT = Path(__file__).resolve().parents[3]

# Published by the image build so both consumers use one artifact.
DEFAULT_BINARY = ROOT / "deploy" / "fullsend" / "vendor" / "fullsend"
BINARY = Path(os.environ.get("FULLSEND_VENDOR_BINARY", "") or DEFAULT_BINARY)

# Fullsend's per-repo vendored path, from internal/layers/vendor.go.
VENDORED_PATH = ".fullsend/bin/fullsend"
BRANCH = "main"


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def main() -> None:
    if not BINARY.is_file():
        raise RuntimeError(
            f"no Fullsend binary at {BINARY}. Run "
            "deploy/scripts/05i-build-fullsend.sh first, or point "
            "FULLSEND_VENDOR_BINARY at one."
        )

    source_digest = digest(BINARY)
    remote = (
        f"https://x-access-token:{TOKEN}@github.local/{ORG}/{REPO}.git"
    )

    with tempfile.TemporaryDirectory(prefix="fullsend-vendor-") as temp:
        directory = Path(temp)
        run_git(directory, "init", f"--initial-branch={BRANCH}")
        run_git(directory, "config", "user.name", "Breadboard Fullsend Seed")
        run_git(directory, "config", "user.email", "breadboard-fullsend-seed@localhost")
        run_git(directory, "remote", "add", "origin", remote)

        fetched = None
        for _ in range(10):
            fetched = run_git(directory, "fetch", "origin", BRANCH, check=False)
            if fetched.returncode == 0:
                run_git(directory, "reset", "--hard", "FETCH_HEAD")
                break
            time.sleep(2)
        if fetched is None or fetched.returncode != 0:
            raise RuntimeError(
                f"could not fetch {ORG}/{REPO}@{BRANCH}: "
                f"{fetched.stderr if fetched else 'fetch did not run'}"
            )

        destination = directory / VENDORED_PATH
        if destination.is_file() and digest(destination) == source_digest:
            print(
                f"vendored binary already current at {ORG}/{REPO}:{VENDORED_PATH} "
                f"(sha256 {source_digest[:12]})"
            )
            return

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BINARY, destination)
        destination.chmod(0o755)

        run_git(directory, "add", "--", VENDORED_PATH)
        # Git records the executable bit in the tree, which is what makes this
        # usable on checkout. Assert it rather than trusting the umask.
        staged = subprocess.run(
            ["git", "ls-files", "--stage", "--", VENDORED_PATH],
            cwd=directory, capture_output=True, text=True, check=True,
        ).stdout.split()
        if not staged or staged[0] != "100755":
            raise RuntimeError(
                f"{VENDORED_PATH} staged as mode {staged[0] if staged else 'missing'}, "
                "expected 100755; the checkout would not be executable"
            )

        run_git(
            directory,
            "commit",
            "-m",
            f"Vendor fullsend binary (sha256 {source_digest[:12]})",
        )
        pushed = None
        for _ in range(10):
            pushed = run_git(directory, "push", "origin", BRANCH, check=False)
            if pushed.returncode == 0:
                break
            time.sleep(2)
        if pushed is None or pushed.returncode != 0:
            raise RuntimeError(pushed.stderr if pushed else "push did not run")

        size = BINARY.stat().st_size
        print(
            f"vendored {size // (1024 * 1024)} MiB binary to "
            f"{ORG}/{REPO}:{VENDORED_PATH} (sha256 {source_digest[:12]})"
        )


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        sys.exit(f"Vendored binary seed failed: {exc}")
