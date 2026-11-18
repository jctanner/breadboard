#!/usr/bin/env python3
"""S1b: build strat-creator's discovery JQL with its own code, per mirrored ref.

For each strat-creator ref cached by mirror_github.py (refs/cc75/<branch>), this
exports scripts/, config/ and types/ to ~/.cache/cc75/work/strat-creator-<branch>,
calls jira_utils.build_jql_from_config("config/initiative-settings.yaml") from
that tree, runs the resulting JQL against the Jira emulator, and compares the
fixture issues it selects with expected.yaml. A difference is reported per
fixture issue with the pipeline labels that explain it.

The exported code runs in a subprocess with `python3 -I`, so nothing from this
repository or the current directory is importable by it.
Writes evidence/tool-discovery-<timestamp>.json; exits 1 if any ref differs.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
CACHE = Path(os.getenv("CC75_CACHE", Path.home() / ".cache" / "cc75" / "sources"))
WORK = CACHE.parent / "work"
BUILD = ("import sys, os; sys.path.insert(0, 'scripts'); import jira_utils as m; "
         "r = m.build_jql_from_config('config/initiative-settings.yaml'); "
         "print(r if isinstance(r, str) else r[0])")


def export(bare: Path, ref: str, dest: Path) -> None:
    data = subprocess.run(["git", "-C", str(bare), "archive", ref, "scripts", "config", "types"],
                          check=True, capture_output=True).stdout
    if dest.exists():
        subprocess.run(["rm", "-rf", str(dest)], check=True)
    dest.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jira-url", default=os.getenv("JIRA_URL", f"https://jira.{DOMAIN}"))
    args = ap.parse_args()
    exp = yaml.safe_load((ROOT / "expected.yaml").read_text())
    intended = exp["strat_creator"]["jql_selected"]
    labels_of = {v["key"]: v["labels"] for v in exp["initiatives"].values()}
    base = min(int(k.split("-")[1]) for k in exp["fixture_ids"].values())
    bare = CACHE / "fullsend-ai__strat-creator.git"
    refs = subprocess.run(["git", "-C", str(bare), "for-each-ref", "--format=%(refname:short) %(objectname)",
                           "refs/cc75/"], check=True, capture_output=True, text=True).stdout.split("\n")
    s = requests.Session()
    s.auth = (os.getenv("JIRA_ADMIN_USER", "admin"), os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
    s.verify = os.getenv("BREADBOARD_CA_FILE") or True
    results = {}
    for line in filter(None, refs):
        ref, sha = line.split()
        branch = ref.split("/")[-1]
        dest = WORK / f"strat-creator-{branch}"
        export(bare, ref, dest)
        jql = subprocess.run([sys.executable, "-I", "-c", BUILD], cwd=dest, check=True,
                             capture_output=True, text=True).stdout.strip()
        r = s.get(f"{args.jira_url.rstrip('/')}/rest/api/3/search/jql",
                  params={"jql": jql, "maxResults": 100, "fields": "key"}, timeout=60)
        r.raise_for_status()
        got = sorted((i["key"] for i in r.json()["issues"] if int(i["key"].split("-")[1]) >= base),
                     key=lambda k: int(k.split("-")[1]))
        extra = {k: [l for l in labels_of.get(k, []) if "ignore" in l or "creator" in l]
                 for k in got if k not in intended}
        missing = [k for k in intended if k not in got]
        results[branch] = {"commit": sha, "jql": jql, "selected": got,
                           "matches_intended": not extra and not missing,
                           "extra_with_labels": extra, "missing": missing}
        print(f"{branch}@{sha[:8]}: matches={results[branch]['matches_intended']} extra={extra} missing={missing}")
    out = ROOT / "evidence" / f"tool-discovery-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"intended": intended, "refs": results}, indent=2) + "\n")
    return 0 if all(v["matches_intended"] for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
