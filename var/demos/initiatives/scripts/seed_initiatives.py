#!/usr/bin/env python3
"""Seed the CC-75 synthetic Initiative fixture into a breadboard Jira emulator.

Steps (idempotent; a second run converges without creating duplicates):
  1. Project-config import: Outcome type, Release Pending status, the
     "CC75 Initiative Workflow", Incorporates/Depend link types, synthetic
     custom fields, Outcome on RHAISTRAT, and an RHAI engineering project with the
     fixture's synthetic components (epic-creator #40 reads RHAI's components and
     stops when there are none).
     Existing statuses are re-sent with their live category and description,
     because the emulator's upsert overwrites both.
  2. Issue import of generated/issues.json (explicit synthetic keys).
  3. Read-back verification of every issue: type, status, labels, parent and
     link order. The emulator silently drops unknown parents, so this matters.
  4. A jira-emulator snapshot labelled cc75-baseline (skip with --no-snapshot).

Writes a non-secret summary to evidence/seed-<timestamp>.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
WORKFLOW = "CC75 Initiative Workflow"
WORKFLOW_STATUSES = ["New", "Backlog", "Refinement", "To Do", "In Progress", "Review",
                     "Release Pending", "Closed"]
NEW_STATUSES = {"Release Pending": ("indeterminate", "Synthetic CC-75 status: awaiting release.")}
CATEGORY_KEYS = {"new", "indeterminate", "done"}


class Jira:
    def __init__(self, url: str, user: str, password: str, ca):
        self.url = url.rstrip("/")
        self.s = requests.Session()
        self.s.auth = (user, password)
        self.s.verify = ca

    def get(self, path, **params):
        r = self.s.get(self.url + path, params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    def upload(self, path, name, payload: bytes):
        r = self.s.post(self.url + path, files={"file": (name, payload, "application/json")}, timeout=300)
        if r.status_code >= 400:
            raise SystemExit(f"{path}: HTTP {r.status_code}: {r.text[:500]}")
        return r.json()

    def post(self, path, body):
        r = self.s.post(self.url + path, json=body, timeout=120)
        r.raise_for_status()
        return r.json()


def config_payloads(jira: Jira) -> list[tuple[str, dict]]:
    live = {s["name"]: s for s in jira.get("/rest/api/2/status")}
    statuses = []
    for name in WORKFLOW_STATUSES:
        if name in live:
            cat = (live[name].get("statusCategory") or {}).get("key", "indeterminate")
            if cat not in CATEGORY_KEYS:
                cat = "indeterminate"
            statuses.append({"status_id": name, "name": name, "status_category": cat,
                             "description": live[name].get("description")})
        else:
            cat, desc = NEW_STATUSES[name]
            statuses.append({"status_id": name, "name": name, "status_category": cat, "description": desc})
    rhaistrat_types = [t["name"] for t in jira.get("/rest/api/2/project/RHAISTRAT").get("issueTypes", [])]
    rhaistrat = {
        "version": "1.0",
        "statuses": statuses,
        "issue_types": [{"name": "Outcome", "subtask": False,
                         "description": "Synthetic CC-75 parent of Initiatives and Features."}],
        "link_types": [
            {"name": "Incorporates", "inward_description": "is incorporated by",
             "outward_description": "incorporates"},
            {"name": "Depend", "inward_description": "is depended on by",
             "outward_description": "depends on"},
        ],
        "custom_fields": [
            {"field_id": "customfield_10855", "name": "Target Version", "field_type": "string"},
            {"field_id": "customfield_75001", "name": "RICE Score (synthetic)", "field_type": "number"},
            {"field_id": "customfield_75002", "name": "RICE Effort (synthetic)", "field_type": "number"},
        ],
        "workflows": [{"workflow_id": "cc75", "name": WORKFLOW,
                       "statuses": [{"status_id": n, "sequence": i} for i, n in enumerate(WORKFLOW_STATUSES)]}],
        "project": {"key": "RHAISTRAT",
                    "issue_types": sorted(set(rhaistrat_types) | {"Outcome", "Initiative", "Feature"}),
                    "workflows": [{"workflow_id": "cc75", "issue_type": "Initiative"},
                                  {"workflow_id": "cc75", "issue_type": "Outcome"}]},
    }
    rhai = {"version": "1.0",
            "project": {"key": "RHAI", "name": "RHAI (synthetic engineering)",
                        "description": "Synthetic CC-75 engineering project for Initiative child Epics.",
                        "issue_types": ["Epic", "Story", "Task", "Sub-task"]}}
    return [("rhaistrat-initiatives.json", rhaistrat), ("rhai-project.json", rhai)]


def verify(jira: Jira, issues: list[dict]) -> list[str]:
    problems = []
    for rec in issues:
        want = rec["fields"]
        got = jira.get(f"/rest/api/2/issue/{rec['key']}",
                       fields="issuetype,status,labels,parent,issuelinks,summary")["fields"]
        if got["issuetype"]["name"] != want["issuetype"]["name"]:
            problems.append(f"{rec['key']}: type {got['issuetype']['name']}")
        if got["status"]["name"] != want["status"]["name"]:
            problems.append(f"{rec['key']}: status {got['status']['name']}")
        if sorted(got.get("labels") or []) != sorted(want["labels"]):
            problems.append(f"{rec['key']}: labels differ")
        want_parent = (want.get("parent") or {}).get("key")
        got_parent = (got.get("parent") or {}).get("key")
        if want_parent != got_parent:
            problems.append(f"{rec['key']}: parent {got_parent!r}, expected {want_parent!r}")
        want_links = [(l["type"]["name"], l["outwardIssue"]["key"]) for l in want.get("issuelinks", [])]
        got_links = [(l["type"]["name"], l["outwardIssue"]["key"])
                     for l in got.get("issuelinks") or [] if "outwardIssue" in l]
        if got_links != want_links:
            problems.append(f"{rec['key']}: outward links {got_links}, expected {want_links}")
    return problems


def count_fixture(jira: Jira) -> int:
    n, token = 0, None
    while True:
        params = {"jql": "labels = cc75-synthetic ORDER BY key ASC", "maxResults": 100, "fields": "key"}
        if token:
            params["nextPageToken"] = token
        page = jira.get("/rest/api/3/search/jql", **params)
        n += len(page.get("issues", []))
        token = page.get("nextPageToken")
        if not token or page.get("isLast", True):
            return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jira-url", default=os.getenv("JIRA_URL", f"https://jira.{DOMAIN}"))
    ap.add_argument("--user", default=os.getenv("JIRA_ADMIN_USER", "admin"))
    ap.add_argument("--password", default=os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
    ap.add_argument("--issues", default=ROOT / "generated" / "issues.json", type=Path)
    ap.add_argument("--no-snapshot", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()
    ca = os.getenv("BREADBOARD_CA_FILE") or True
    jira = Jira(args.jira_url, args.user, args.password, ca)
    issues = json.loads(args.issues.read_text())["issues"]
    summary = {"jira_url": args.jira_url, "issues_in_fixture": len(issues),
               "started": datetime.now(timezone.utc).isoformat()}

    if not args.verify_only:
        for name, payload in config_payloads(jira):
            res = jira.upload("/api/admin/import/project-config", name, json.dumps(payload).encode())
            if res.get("errors"):
                raise SystemExit(f"{name}: config import errors: {res['errors']}")
            summary[f"config:{name}"] = {k: v for k, v in res.items() if k != "errors"}
        res = jira.upload("/api/admin/import/file", "issues.json", args.issues.read_bytes())
        if res.get("errors"):
            raise SystemExit(f"issue import errors: {res['errors'][:10]}")
        summary["import"] = {k: res.get(k) for k in ("imported", "updated", "projects_created", "users_created")}
        wanted = sorted({c["name"] for i in issues for c in i["fields"].get("components") or []})
        have = {c["name"] for c in jira.get("/rest/api/2/project/RHAI/components")}
        for name in wanted:
            if name not in have:
                jira.post("/rest/api/2/component", {"name": name, "project": "RHAI",
                                                    "description": "Synthetic CC-75 component"})
        summary["rhai_components"] = {"wanted": wanted, "created": sorted(set(wanted) - have)}

    problems = verify(jira, issues)
    summary["verify_problems"] = problems
    summary["fixture_issue_count"] = count_fixture(jira)
    ok = not problems and summary["fixture_issue_count"] == len(issues)
    if ok and not args.verify_only and not args.no_snapshot:
        summary["snapshot"] = jira.post("/api/admin/snapshots", {"label": "cc75-baseline"})["name"]
    summary["ok"] = ok
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    out = evidence / f"seed-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in summary if k != "verify_problems"}, indent=1))
    for p in problems[:20]:
        print("PROBLEM", p, file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
