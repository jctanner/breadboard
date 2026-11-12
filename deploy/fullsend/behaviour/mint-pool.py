#!/usr/bin/env python3
"""Keep the dev mint's allowlists in step with the behaviour-test pool.

Fullsend's own behaviour harness sets each mint's WORKFLOW_HOST_REPOS to
every pool slot (pkg/behaviourtest/drivers/install/mint_groups.go), because
a vendored install runs its reusable workflows from the slot repository.
Breadboard's mint is deployed from deploy/k8s/24-fullsend-mint-dev.yaml, so
this script derives the same entries from deploy/fullsend/behaviour/pool.env
and writes them there:

- FULLSEND_ALLOWED_ORGS gains the pool organisation;
- FULLSEND_WORKFLOW_HOST_REPOS gains <org>/test-repo-01 ... test-repo-NN.

Entries that are not pool entries are kept, in their order. Pool slots beyond
the current size are removed.

Usage: mint-pool.py check   exit 1 if the manifest is out of step
       mint-pool.py write   rewrite the manifest in place
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POOL_ENV = ROOT / "deploy/fullsend/behaviour/pool.env"
MANIFEST = ROOT / "deploy/k8s/24-fullsend-mint-dev.yaml"


def read_pool() -> tuple[str, int]:
    values = {}
    for line in POOL_ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    org = values["BT_POOL_ORG"]
    size = int(values["BT_POOL_SIZE"])
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", org) or not 1 <= size <= 99:
        sys.exit(f"{POOL_ENV}: BT_POOL_ORG={org!r} or BT_POOL_SIZE={size} is not valid")
    return org, size


def env_value_pattern(name: str) -> re.Pattern[str]:
    # "- name: NAME" followed on the next line by "  value: ...".
    return re.compile(
        rf"(^[ \t]*- name: {re.escape(name)}[ \t]*\n[ \t]*value:[ \t]*)(.*)$",
        re.MULTILINE,
    )


def updated(text: str, name: str, desired) -> str:
    pattern = env_value_pattern(name)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        sys.exit(f"{MANIFEST}: expected one {name} entry, found {len(matches)}")
    current = [e.strip() for e in matches[0].group(2).strip().strip('"').split(",") if e.strip()]
    value = ",".join(desired(current))
    return pattern.sub(lambda m: m.group(1) + value, text, count=1)


def desired_manifest(text: str) -> str:
    org, size = read_pool()
    slot = re.compile(rf"{re.escape(org)}/test-repo-\d+", re.IGNORECASE)
    slots = [f"{org}/test-repo-{i:02d}" for i in range(1, size + 1)]

    def orgs(current: list[str]) -> list[str]:
        return current if org.lower() in (c.lower() for c in current) else current + [org]

    def hosts(current: list[str]) -> list[str]:
        return [c for c in current if not slot.fullmatch(c)] + slots

    text = updated(text, "FULLSEND_ALLOWED_ORGS", orgs)
    return updated(text, "FULLSEND_WORKFLOW_HOST_REPOS", hosts)


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("check", "write"):
        sys.exit(__doc__)
    text = MANIFEST.read_text()
    want = desired_manifest(text)
    if sys.argv[1] == "write":
        if want != text:
            MANIFEST.write_text(want)
            print(f"updated {MANIFEST.relative_to(ROOT)} from the pool")
        else:
            print(f"{MANIFEST.relative_to(ROOT)} already matches the pool")
        return
    if want != text:
        sys.exit(
            f"{MANIFEST.relative_to(ROOT)} does not allow the behaviour-test pool; "
            "run `make bt-seed` to update and redeploy the mint"
        )
    print("mint allowlists match the behaviour-test pool")


if __name__ == "__main__":
    main()
