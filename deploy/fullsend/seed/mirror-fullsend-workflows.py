#!/usr/bin/env python3
"""Mirror the composite actions the Fullsend workflows call.

These three actions are used by the conformance path itself: reusable-dispatch
calls prepare-workspace, mint-token and install-fullsend-cli. They are
mirrored from the local checkout rather than fetched from the network.

This script used to also write an "M8 role and event" fixture workflow into
the target repository. It no longer does, and it removes that file if it finds
one. The fixture echoed a string into a log nothing read, while firing on
`issues: [opened, labeled]` and `issue_comment: [created]` - so every agent
comment and every label the agent applied triggered it again. One conformance
run produced six of them. Worse, it appeared ahead of the real run in the runs
list on the same event, which is why selecting a run by event alone picks the
wrong one.

What it could have covered is covered better elsewhere: reusable-dispatch uses
a matrix itself, and array `runs-on`, matrix expansion and event triggers all
have emulator unit tests in tests/actions/. See decision 1 in
`.ledger/plans/fullsend-integration-conformance-plan.md`, amended 2026-09-22.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import time

from emulator import ORG, REPO, TOKEN, run_git


# deploy/fullsend/seed/mirror-fullsend-workflows.py -> parents[3] is the project root.
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "checkouts" / "fullsend-ai" / "fullsend"
FILES = (
    ".github/actions/mint-token/action.yml",
    ".github/actions/prepare-workspace/action.yml",
    ".github/actions/install-fullsend-cli/action.yml",
)
RETIRED_WORKFLOW = ".github/workflows/m8-role-events.yml"


def main() -> None:
    remote = f"https://x-access-token:{TOKEN}@github.local/{ORG}/{REPO}.git"
    with tempfile.TemporaryDirectory(prefix="fullsend-seed-mirror-") as temp:
        directory = Path(temp)
        run_git(directory, "init", "--initial-branch=main")
        run_git(directory, "config", "user.name", "Breadboard Fullsend Seed")
        run_git(directory, "config", "user.email", "breadboard-fullsend-seed@localhost")
        run_git(directory, "remote", "add", "origin", remote)
        fetched = None
        for _ in range(10):
            fetched = run_git(directory, "fetch", "origin", "main", check=False)
            if fetched.returncode == 0:
                run_git(directory, "reset", "--hard", "FETCH_HEAD")
                break
            time.sleep(2)
        if fetched is None or fetched.returncode != 0:
            raise RuntimeError(fetched.stderr if fetched else "fetch did not run")
        mirrored = []
        for relative in FILES:
            source = SOURCE / relative
            if not source.is_file():
                raise RuntimeError(f"required local Fullsend fixture is missing: {source}")
            destination = directory / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
            mirrored.append(relative)
        run_git(directory, "add", *mirrored)
        # Converge rather than merely stop writing it: a repository seeded
        # before this change still carries the fixture, and it keeps firing.
        retired = directory / RETIRED_WORKFLOW
        if retired.is_file():
            retired.unlink()
            run_git(directory, "rm", "--cached", "--quiet", RETIRED_WORKFLOW)
            mirrored.append(f"-{RETIRED_WORKFLOW}")
        if run_git(directory, "diff", "--cached", "--quiet", check=False).returncode != 0:
            run_git(directory, "commit", "-m", "Mirror Fullsend composite actions")
            pushed = None
            for _ in range(10):
                pushed = run_git(directory, "push", "-u", "origin", "main", check=False)
                if pushed.returncode == 0:
                    break
                time.sleep(2)
            if pushed is None or pushed.returncode != 0:
                raise RuntimeError(pushed.stderr if pushed else "push did not run")
        print({"status": "mirrored", "commit": run_git(directory, "rev-parse", "HEAD").stdout.strip(), "files": mirrored})


if __name__ == "__main__":
    main()
