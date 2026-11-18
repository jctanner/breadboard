#!/usr/bin/env python3
"""S9: kill switch and rollback on the CC-75 emulator mirror. No model calls.

1. Kill switch. Create a strat-pipeline pipeline (ref main, STRAT_EXECUTOR=fullsend,
   dry flags) with INITIATIVE_STRATEGIES unset, as a schedule does once the switch
   is turned off, and the same with it on. Wait for python-tests, then compare the
   job lists: off offers the RFE batch (workflow-batch-jql) and no Initiative job;
   on offers workflow-batch-initiative and suppresses the RFE batch. Nothing is
   played; both pipelines are cancelled afterwards.
2. Rollback. Fingerprint every fixture issue (type, status, labels, parent, links,
   summary, description hash, attachment names, comment count):
     restore cc75-baseline -> A; restore a changed state taken from the same
     baseline (default: the demo check's cc75-demo-75028-decomposed: a live
     strategy, a sign-off and 11 new Epics) -> B; restore cc75-baseline -> C.
   Pass when C == A exactly, B differs from A, and seed_initiatives.verify()
   finds no difference from the catalogue.
The Jira emulator is left at the baseline. Writes evidence/S9-<timestamp>.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import seed_initiatives  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
PROJECT = "redhat/rhel-ai/agentic-ci/strat-pipeline"
CHANGED_SNAPSHOT = os.getenv("CC75_S9_CHANGED_SNAPSHOT", "cc75-demo-75028-decomposed")
VARS = {"STRAT_EXECUTOR": "fullsend", "STRAT_DRY_RUN": "1", "FULLSEND_PUBLISH": "0"}


def kill_switch(gl, g):
    pid = quote(PROJECT, safe="")
    out = {}
    for name, extra in (("off", {}), ("on", {"INITIATIVE_STRATEGIES": "on"})):
        variables = dict(VARS, **extra)
        r = gl.post(f"{g}/projects/{pid}/pipeline", timeout=60, json={
            "ref": "main", "variables": [{"key": k, "value": v} for k, v in variables.items()]})
        r.raise_for_status()
        pipeline = r.json()["id"]
        jobs = []
        for _ in range(90):
            jobs = gl.get(f"{g}/projects/{pid}/pipelines/{pipeline}/jobs", timeout=60).json()
            tests = [j for j in jobs if j["name"] == "python-tests"]
            if tests and tests[0]["status"] in ("success", "failed", "canceled"):
                break
            time.sleep(10)
        gl.post(f"{g}/projects/{pid}/pipelines/{pipeline}/cancel", timeout=60)
        out[name] = {"pipeline": pipeline, "variables": variables,
                     "jobs": {j["name"]: j["status"] for j in jobs}}
    off, on = out["off"]["jobs"], out["on"]["jobs"]
    out["checks"] = {
        "off_python_tests_success": off.get("python-tests") == "success",
        "off_offers_rfe_batch": "workflow-batch-jql" in off,
        "off_has_no_initiative_job": "workflow-batch-initiative" not in off,
        "on_python_tests_success": on.get("python-tests") == "success",
        "on_offers_initiative_job": "workflow-batch-initiative" in on,
        "on_suppresses_rfe_batch": "workflow-batch-jql" not in on,
    }
    return out


def snapshot(jira, j, label):
    snaps = jira.get(f"{j}/api/admin/snapshots", timeout=30).json()["snapshots"]
    names = sorted(s["name"] if isinstance(s, dict) else s for s in snaps)
    names = [n for n in names if label in n]
    if not names:
        raise SystemExit(f"no {label} snapshot")
    return names[-1]


def restore(jira, j, name):
    jira.post(f"{j}/api/admin/snapshots/{name}/restore", timeout=120).raise_for_status()


def fingerprint(jira, j, keys):
    fp = {}
    for key in keys:
        r = jira.get(f"{j}/rest/api/2/issue/{key}", timeout=30, params={
            "fields": "issuetype,status,labels,parent,issuelinks,summary,description,attachment,comment"})
        if r.status_code == 404:
            fp[key] = None
            continue
        f = r.json()["fields"]
        fp[key] = {
            "type": f["issuetype"]["name"], "status": f["status"]["name"], "labels": sorted(f.get("labels") or []),
            "parent": (f.get("parent") or {}).get("key"),
            "links": sorted(f"{l['type']['name']}>{l['outwardIssue']['key']}" for l in f.get("issuelinks") or []
                            if "outwardIssue" in l),
            "summary": f.get("summary"),
            "description_sha256": hashlib.sha256(json.dumps(f.get("description"), sort_keys=True).encode()).hexdigest(),
            "attachments": sorted(a["filename"] for a in f.get("attachment") or []),
            "comments": (f.get("comment") or {}).get("total", 0),
        }
    return fp


def main() -> int:
    ca = os.getenv("BREADBOARD_CA_FILE") or True
    gl = requests.Session()
    gl.auth = (os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin"))
    gl.verify = ca
    jira = requests.Session()
    jira.auth = (os.getenv("JIRA_ADMIN_USER", "admin"), os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
    jira.verify = ca
    g, j = f"https://gitlab.{DOMAIN}/api/v4", f"https://jira.{DOMAIN}"

    ks = kill_switch(gl, g)
    issues = json.loads((ROOT / "generated" / "issues.json").read_text())["issues"]
    keys = [i["key"] for i in issues]
    base, after = snapshot(jira, j, "cc75-baseline"), snapshot(jira, j, CHANGED_SNAPSHOT)
    restore(jira, j, base)
    a = fingerprint(jira, j, keys)
    restore(jira, j, after)
    b = fingerprint(jira, j, keys)
    restore(jira, j, base)
    c = fingerprint(jira, j, keys)
    changed = sorted(k for k in keys if a[k] != b[k])
    problems = seed_initiatives.verify(seed_initiatives.Jira(j, jira.auth[0], jira.auth[1], ca), issues)
    rollback = {"baseline": base, "changed_state": after, "issues": len(keys), "changed_in_that_state": changed,
                "restore_differences": sorted(k for k in keys if a[k] != c[k]), "catalogue_problems": problems,
                "checks": {"restore_is_exact": a == c, "changed_state_differs": bool(changed),
                           "matches_catalogue": not problems,
                           "baseline_has_no_attachments": not any(a[k] and a[k]["attachments"] for k in keys)}}
    ok = all(ks["checks"].values()) and all(rollback["checks"].values())
    summary = {"scenario": "S9", "kill_switch": ks, "rollback": rollback, "ok": ok,
               "checked_at": datetime.now(timezone.utc).isoformat()}
    out = ROOT / "evidence" / f"S9-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    for section in (ks, rollback):
        for name, passed in section["checks"].items():
            print(f"  check {name:<40} {passed}")
    print(f"  changed in {after}: {changed}; ok={ok}; evidence: {out.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
