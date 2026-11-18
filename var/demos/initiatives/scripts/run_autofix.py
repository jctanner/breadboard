#!/usr/bin/env python3
"""S5: Initiative autofix canary on the rfe-autofixer emulator mirror.

Runs production's schedule-only `autofix-initiative` job the way production
enables it: an (inactive) pipeline schedule on main with
AUTOFIX_SCHEDULE=initiative, played once. The mirror (its private adaptations)
routes the model through Model Relay (project variables); the schedule carries
the run size (AUTOFIX_LIMIT/AUTOFIX_BATCH_SIZE, default 3) and the emulator
endpoints. A watchdog cancels the job if the agent's prompt shows any other limit.

Starts from the cc75-baseline snapshot. Checks:
  - the job succeeds; the trace shows the relay route, the limit, and the
    identity probe (the permissions probe is skipped: emulator gap);
  - Jira writes touch only opted-in Initiatives (expected.yaml), at most LIMIT;
  - each written Initiative ends with an autofix outcome label (rubric-pass and
    needs-attention may coexist) and keeps its summary;
  - results reach rfe-autofixer-results under the type's subtree.
A passing run's end state is kept as snapshot cc75-after-S5; Jira is then
restored to the baseline. Writes evidence/S5-<timestamp>.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
PROJECT = "redhat/rhel-ai/agentic-ci/rfe-autofixer"
DATA_PROJECT = "redhat/rhel-ai/agentic-ci/rfe-autofixer-results"
SUBDIR = "initiative-rhaistrat"
JOB = "autofix-initiative"
OUTCOMES = ("initiative-autofix-rubric-pass", "initiative-needs-attention")
READ_ONLY_POSTS = ("/search", "/search/jql", "/search/approximate-count", "/issue/bulkfetch", "/expression/eval")
SCHEDULE_DESCRIPTION = "cc75 S5 initiative autofix (inactive; played by run_autofix.py)"
DOMAIN_GITHUB = "https://github-emulator.ai-pipeline.svc.cluster.local"
DOMAIN_GITLAB = "https://gitlab-emulator.ai-pipeline.svc.cluster.local"


def schedule_variables(limit: str) -> list[dict]:
    """The schedule's variables, as production configures an Initiative schedule, plus the
    emulator endpoints (pipeline variables override the job's YAML values)."""
    values = {"AUTOFIX_SCHEDULE": "initiative", "AUTOFIX_LIMIT": limit, "AUTOFIX_BATCH_SIZE": limit,
              "JIRA_SERVER": f"https://jira.{os.getenv('BREADBOARD_DOMAIN', 'local').strip('.') or 'local'}",
              "CLAUDE_REPO": f"{DOMAIN_GITHUB}/fullsend-ai/rfe-creator.git",
              "RESULTS_REPO": f"{DOMAIN_GITLAB}/redhat/rhel-ai/agentic-ci/rfe-autofixer-results.git",
              "CLAUDE_CODE_SUBAGENT_MODEL": "claude-opus-5-5"}
    return [{"key": k, "value": v} for k, v in values.items()]


def snapshot(jira, j, label):
    snaps = jira.get(f"{j}/api/admin/snapshots", timeout=30).json()["snapshots"]
    names = sorted(s["name"] if isinstance(s, dict) else s for s in snaps)
    names = [n for n in names if label in n]
    if not names:
        raise SystemExit(f"no {label} snapshot")
    return names[-1]


def issue(jira, j, key):
    f = jira.get(f"{j}/rest/api/2/issue/{key}", timeout=30,
                 params={"fields": "summary,labels,comment,attachment,status"}).json()["fields"]
    comments = (f.get("comment") or {}).get("comments") or []
    return {"summary": f.get("summary"), "labels": sorted(f.get("labels") or []),
            "status": (f.get("status") or {}).get("name"),
            "comments": len(comments),
            "initiative_creator_comments": sum("[Initiative Creator]" in json.dumps(c.get("body")) for c in comments)}


def tree(gl, g, prefix):
    pid = quote(DATA_PROJECT, safe="")
    out, page = [], 1
    while True:
        r = gl.get(f"{g}/projects/{pid}/repository/tree", timeout=60,
                   params={"path": prefix, "recursive": "true", "per_page": 100, "page": page})
        if r.status_code == 404:
            return out
        r.raise_for_status()
        batch = r.json()
        out += [x["path"] for x in batch if x.get("type") == "blob"]
        if len(batch) < 100:
            return out
        page += 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=5 * 3600)
    args = ap.parse_args()
    ca = os.getenv("BREADBOARD_CA_FILE") or True
    gl = requests.Session()
    gl.auth = (os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin"))
    gl.verify = ca
    jira = requests.Session()
    jira.auth = (os.getenv("JIRA_ADMIN_USER", "admin"), os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
    jira.verify = ca
    g, j = f"https://gitlab.{DOMAIN}/api/v4", f"https://jira.{DOMAIN}"
    pid = quote(PROJECT, safe="")
    opted_in = yaml.safe_load((ROOT / "expected.yaml").read_text())["rfe_autofixer"]["opted_in"]

    base = snapshot(jira, j, "cc75-baseline")
    jira.post(f"{j}/api/admin/snapshots/{base}/restore", timeout=120).raise_for_status()
    before = {k: issue(jira, j, k) for k in opted_in}
    data_before = set(tree(gl, g, SUBDIR))

    variables = schedule_variables(str(args.limit))
    schedules = gl.get(f"{g}/projects/{pid}/pipeline_schedules", timeout=60).json()
    mine = [s for s in schedules if s.get("description") == SCHEDULE_DESCRIPTION]
    body = {"description": SCHEDULE_DESCRIPTION, "ref": "main", "cron": "0 3 1 1 *", "active": False,
            "variables": variables}
    if mine:
        sid = mine[0]["id"]
        gl.put(f"{g}/projects/{pid}/pipeline_schedules/{sid}", json=body, timeout=60).raise_for_status()
    else:
        r = gl.post(f"{g}/projects/{pid}/pipeline_schedules", json=body, timeout=60)
        r.raise_for_status()
        sid = r.json()["id"]

    seq0 = jira.get(f"{j}/api/admin/requests", params={"since": 0, "limit": 1}, timeout=30).json()["last_seq"]
    r = gl.post(f"{g}/projects/{pid}/pipeline_schedules/{sid}/play", timeout=60)
    r.raise_for_status()
    pipeline = r.json()["id"]
    print(f"S5: schedule {sid} played -> pipeline {pipeline}; limit {args.limit}", flush=True)

    t0, jobs, job, watchdog = time.time(), [], None, None
    want_limit = f"--limit {args.limit} --batch-size {args.limit}"
    while time.time() - t0 < args.timeout:
        jobs = gl.get(f"{g}/projects/{pid}/pipelines/{pipeline}/jobs", timeout=60).json()
        job = next((x for x in jobs if x["name"] == JOB), None)
        if job and job["status"] == "running" and watchdog is None:
            trace = gl.get(f"{g}/projects/{pid}/jobs/{job['id']}/trace", timeout=60).text
            if "-p /rfe-auto-fix" in trace:
                watchdog = want_limit in trace
                if not watchdog:
                    gl.post(f"{g}/projects/{pid}/jobs/{job['id']}/cancel", timeout=60)
                    print("  watchdog: unexpected autofix limit; job cancelled", flush=True)
        if jobs and all(x["status"] in ("success", "failed", "canceled", "skipped", "manual") for x in jobs):
            break
        time.sleep(15)

    trace = gl.get(f"{g}/projects/{pid}/jobs/{job['id']}/trace", timeout=60).text if job else ""
    traces_dir = Path.home() / ".cache" / "cc75" / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    if job:
        (traces_dir / f"S5-job{job['id']}.log").write_text(trace)
    markers = {m: (m in trace) for m in ("Model: claude-opus-5-5", "cc75: sandbox image", want_limit,
                                         "Jira identity probe OK for the JIRA_USERNAME username",
                                         "Jira permissions probe skipped")}
    entries = jira.get(f"{j}/api/admin/requests", params={"since": seq0}, timeout=30).json()["requests"]
    seen = [{"method": e.get("method"), "path": e.get("path"), "status": e.get("status")}
            for e in entries if e.get("seq", 0) > seq0]
    writes = [w for w in seen if not (w["method"] == "GET" or (w["method"] == "POST" and str(w["path"]).endswith(READ_ONLY_POSTS)))]
    written = sorted({k for w in writes for k in re.findall(r"[A-Z][A-Z0-9]+-\d+", str(w["path"]))})
    after = {k: issue(jira, j, k) for k in opted_in}
    new_paths = sorted(set(tree(gl, g, SUBDIR)) - data_before)
    checks = {
        "job_success": bool(job) and job["status"] == "success",
        "watchdog_limit_ok": watchdog is True,
        **{f"trace: {m}": v for m, v in markers.items()},
        "writes_only_opted_in": set(written) <= set(opted_in),
        "written_within_limit": 1 <= len(written) <= args.limit,
        "results_pushed": bool(new_paths),
    }
    for k in written:
        if k in after:
            # rubric-pass and needs-attention may coexist: rfe-creator asks a human to look at an
            # Initiative that passed (strat-creator config/initiative-settings.yaml says so).
            outcome = [lbl for lbl in OUTCOMES if lbl in after[k]["labels"]]
            checks[f"{k}_has_outcome_label"] = bool(outcome)
            checks[f"{k}_summary_unchanged"] = after[k]["summary"] == before[k]["summary"]
    ok = all(checks.values())
    summary = {"scenario": "S5", "pipeline": pipeline, "schedule": sid, "job": job and job["id"],
               "jobs": {x["name"]: x["status"] for x in jobs}, "checks": checks, "written_keys": written,
               "label_changes": {k: {"before": before[k]["labels"], "after": after[k]["labels"]}
                                 for k in opted_in if before[k]["labels"] != after[k]["labels"]},
               "comments_added": {k: after[k]["comments"] - before[k]["comments"] for k in written if k in after},
               "initiative_creator_comments": {k: after[k]["initiative_creator_comments"] for k in written if k in after},
               "write_paths": sorted({f"{w['method']} {w['path']}" for w in writes}),
               "data_repo_new_paths": new_paths, "ok": ok, "checked_at": datetime.now(timezone.utc).isoformat()}
    if ok:
        summary["kept_as_snapshot"] = jira.post(f"{j}/api/admin/snapshots", timeout=120,
                                                json={"label": "cc75-after-S5"}).json()["name"]
    jira.post(f"{j}/api/admin/snapshots/{base}/restore", timeout=120).raise_for_status()
    summary["restored_after"] = base
    out = ROOT / "evidence" / f"S5-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    for name, passed in checks.items():
        print(f"  check {name:<52} {passed}")
    print(f"  jobs: {summary['jobs']}")
    print(f"  written: {written}; data repo: {len(new_paths)} new path(s); ok={ok}; evidence: {out.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
