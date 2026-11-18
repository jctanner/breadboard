#!/usr/bin/env python3
"""S1: check Initiative discovery queries against the expected.yaml oracle.

Runs, against the Jira emulator:
  - strat-creator's initiative-strategy discovery JQL (exact string);
  - the rfe-autofixer opt-in query (provisional, plan Q4);
  - epic-creator's skip query `parent = KEY AND issuetype = Epic` per candidate,
    plus its legacy outward Incorporates check.
Only fixture issues are compared (keys in the synthetic block); pre-existing
demo issues are reported separately if a query selects them.
Writes evidence/discovery-<timestamp>.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"


def search(s: requests.Session, url: str, jql: str) -> list[str]:
    keys, token = [], None
    while True:
        params = {"jql": jql, "maxResults": 100, "fields": "key"}
        if token:
            params["nextPageToken"] = token
        r = s.get(f"{url}/rest/api/3/search/jql", params=params, timeout=60)
        r.raise_for_status()
        page = r.json()
        keys += [i["key"] for i in page.get("issues", [])]
        token = page.get("nextPageToken")
        if not token or page.get("isLast", True):
            return keys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jira-url", default=os.getenv("JIRA_URL", f"https://jira.{DOMAIN}"))
    ap.add_argument("--expected", default=ROOT / "expected.yaml", type=Path)
    ap.add_argument("--autofix-project", default="RHAISTRAT")
    args = ap.parse_args()
    exp = yaml.safe_load(args.expected.read_text())
    base = min(int(v.split("-")[1]) for v in exp["fixture_ids"].values())
    s = requests.Session()
    s.auth = (os.getenv("JIRA_ADMIN_USER", "admin"), os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
    s.verify = os.getenv("BREADBOARD_CA_FILE") or True
    url = args.jira_url.rstrip("/")

    def fixture(keys):
        return [k for k in keys if int(k.split("-")[1]) >= base]

    def other(keys):
        return [k for k in keys if int(k.split("-")[1]) < base]

    results = {}
    sc = exp["strat_creator"]
    got = search(s, url, sc["discovery_jql"])
    results["strat_creator_jql"] = {"expected": sc["jql_selected"], "got": fixture(got),
                                    "non_fixture_selected": other(got)}
    optin_jql = (f"project = {args.autofix_project} AND issuetype = Initiative "
                 "AND labels = 'initiative-autofix-opt-in' ORDER BY key ASC")
    got = search(s, url, optin_jql)
    results["rfe_autofixer_optin"] = {"jql": optin_jql, "expected": exp["rfe_autofixer"]["opted_in"],
                                      "got": fixture(got), "non_fixture_selected": other(got)}
    decomp = {}
    for key, want in exp["epic_creator"]["candidates"].items():
        children = search(s, url, f"parent = {key} AND issuetype = Epic")
        r = s.get(f"{url}/rest/api/2/issue/{key}", params={"fields": "issuelinks"}, timeout=60)
        r.raise_for_status()
        legacy = [l["outwardIssue"]["key"] for l in r.json()["fields"].get("issuelinks") or []
                  if l["type"]["name"] == "Incorporates" and "outwardIssue" in l]
        action = "skip" if children or legacy else "decompose"
        decomp[key] = {"expected": want["action"], "got": action,
                       "epic_children": children, "legacy_incorporates": legacy}
    results["epic_creator_skip"] = decomp
    # Cross-project parent rollup: every fixture Initiative's Epic children must be found.
    rollup = {}
    for fid, item in exp["initiatives"].items():
        got = sorted(search(s, url, f"parent = {item['key']} AND issuetype = Epic"))
        rollup[item["key"]] = {"expected": sorted(item["epic_children"]), "got": got}
    results["epic_child_rollup"] = rollup

    failures = []
    for name in ("strat_creator_jql", "rfe_autofixer_optin"):
        if results[name]["expected"] != results[name]["got"]:
            failures.append(name)
    failures += [f"epic_creator_skip:{k}" for k, v in decomp.items() if v["expected"] != v["got"]]
    failures += [f"rollup:{k}" for k, v in rollup.items() if v["expected"] != v["got"]]
    results["failures"] = failures
    results["ok"] = not failures
    results["checked_at"] = datetime.now(timezone.utc).isoformat()
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    out = evidence / f"discovery-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({"ok": results["ok"], "failures": failures,
                      "strat_jql": results["strat_creator_jql"]["got"],
                      "strat_non_fixture": results["strat_creator_jql"]["non_fixture_selected"],
                      "optin_non_fixture": results["rfe_autofixer_optin"]["non_fixture_selected"],
                      "decomp": {k: v["got"] for k, v in decomp.items()},
                      "evidence": str(out.relative_to(ROOT))}, indent=1))
    return 0 if results["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
