#!/usr/bin/env python3
"""Run a CC-75 pipeline scenario on the strat-pipeline emulator mirror.

  run_scenario.py S3          tripwire negative: Initiative run without dry flags
  run_scenario.py S3-control  same, with STRAT_DRY_RUN=1 FULLSEND_PUBLISH=0
  run_scenario.py S4          dry Initiative batch with no opted-in Initiatives:
                              the pipeline succeeds with no work and no sandbox
  run_scenario.py S6          dry strategy canary on the baseline, BATCH_SIZE=1:
                              the oracle's first Initiative goes through the real
                              model in the sandbox; nothing is written to Jira
  run_scenario.py S7a         LIVE on the emulators (strat-pipeline main, INITIATIVE_LIVE=on),
                              baseline, BATCH_SIZE=1: the strategy for the oracle's
                              first Initiative is written to the Jira emulator and the
                              run is published to the GitLab emulator's data repo
  run_scenario.py S7b         LIVE, continuing from S7a's end state, BATCH_SIZE=3: the
                              next three Initiatives; the one S7a finished is skipped

Each scenario creates one API pipeline with fixed variables, waits for the
named jobs to settle, checks job status and trace markers, and compares the
Jira emulator's request audit (non-GET /rest/ requests) before and after:
the dry scenarios must write nothing to Jira. Live scenarios (S7*) must write
only to the Initiatives they select, leave each with a strategy attachment, a
review gate label and no lock, and add initiative-strategy/ results to the data
repo; they keep their end state as a snapshot (cc75-after-<scenario>) instead of
restoring the baseline. Writes evidence/<scenario>-*.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
PROJECT = "redhat/rhel-ai/agentic-ci/strat-pipeline"
# Log lines the strat-pipeline jobs print (the refusal and the live-run notice) quote private
# source, so they are read from the private patch folder; without it only job status is checked.
_MARKERS = Path(os.getenv("CC75_PRIVATE_PATCHES", "~/.cache/cc75/private-patches")).expanduser() / "strat-pipeline" / "markers.json"
MARKERS = json.loads(_MARKERS.read_text()) if _MARKERS.exists() else {}
TRIPWIRE, LIVE_NOTICE = MARKERS.get("tripwire"), MARKERS.get("live")
BASE_VARS = {"INITIATIVE_STRATEGIES": "on", "STRAT_EXECUTOR": "fullsend"}
DRY = {"STRAT_DRY_RUN": "1", "FULLSEND_PUBLISH": "0"}
LIVE = {"STRAT_DRY_RUN": "0", "FULLSEND_PUBLISH": "1"}
DATA_PROJECT = "redhat/rhel-ai/agentic-ci/strat-pipeline-data"
GATE_LABELS = ("strat-creator-rubric-pass", "strat-creator-needs-attention")
LOCK_LABEL = "strat-creator-processing"
EMULATOR_SOURCE = {
    "STRAT_CREATOR_REPO": "https://github-emulator.ai-pipeline.svc.cluster.local/fullsend-ai/strat-creator.git",
    "STRAT_CREATOR_BRANCH": "cc75-emulator",
}
OPT_IN = "initiative-autofix-opt-in"
# The audit records every non-GET /rest/ request; these POSTs only read.
READ_ONLY_POSTS = ("/search", "/search/jql", "/search/approximate-count", "/issue/bulkfetch", "/expression/eval")

SCENARIOS = {
    "S3": {
        "variables": dict(BASE_VARS),
        "expect": {"python-tests": ("failed", TRIPWIRE)},
    },
    "S3-control": {
        "variables": dict(BASE_VARS, **DRY),
        "expect": {"python-tests": ("success", None)},
    },
    "S4": {
        "variables": dict(BASE_VARS, **DRY, **EMULATOR_SOURCE, BATCH_SIZE="1"),
        "fixture": "no-opt-in",
        "play": ["workflow-batch-initiative"],
        "expect": {"python-tests": ("success", None), "fullsend-input-check": ("success", None),
                   "workflow-batch-initiative": ("success", None)},
    },
    "S6": {
        "variables": dict(BASE_VARS, **DRY, **EMULATOR_SOURCE, BATCH_SIZE="1"),
        "fixture": "baseline",
        "play": ["workflow-batch-initiative"],
        "expect": {"python-tests": ("success", None), "fullsend-input-check": ("success", None),
                   "workflow-batch-initiative": ("success", None)},
        "markers": {"workflow-batch-initiative": ["RHAISTRAT-75006", "Sandbox created", "Validation passed", "Job succeeded"]},
        "timeout": 6 * 3600,
    },
    "S7a": {
        "variables": dict(BASE_VARS, **LIVE, INITIATIVE_LIVE="on", **EMULATOR_SOURCE, BATCH_SIZE="1"),
        "fixture": "baseline",
        "play": ["workflow-batch-initiative"],
        "expect": {"python-tests": ("success", LIVE_NOTICE),
                   "fullsend-input-check": ("success", None), "workflow-batch-initiative": ("success", None)},
        "markers": {"workflow-batch-initiative": ["RHAISTRAT-75006", "Validation passed", "Job succeeded"]},
        "live": {"processed": ["RHAISTRAT-75006"], "untouched": ["RHAISTRAT-75009", "RHAISTRAT-75010",
                                                                 "RHAISTRAT-75019"]},
        "timeout": 6 * 3600,
    },
    "S7b": {
        "variables": dict(BASE_VARS, **LIVE, INITIATIVE_LIVE="on", **EMULATOR_SOURCE, BATCH_SIZE="3"),
        "fixture": "after-S7a",
        "play": ["workflow-batch-initiative"],
        "expect": {"python-tests": ("success", LIVE_NOTICE),
                   "fullsend-input-check": ("success", None), "workflow-batch-initiative": ("success", None)},
        "markers": {"workflow-batch-initiative": ["RHAISTRAT-75009", "RHAISTRAT-75010", "RHAISTRAT-75019",
                                                  "Validation passed", "Job succeeded"]},
        "live": {"processed": ["RHAISTRAT-75009", "RHAISTRAT-75010", "RHAISTRAT-75019"],
                 "untouched": ["RHAISTRAT-75006"]},
        "timeout": 6 * 3600,
    },
}


def baseline_snapshot(jira, j, label="cc75-baseline"):
    snaps = jira.get(f"{j}/api/admin/snapshots", timeout=30).json()["snapshots"]
    names = sorted(s["name"] if isinstance(s, dict) else s for s in snaps)
    names = [n for n in names if label in n]
    if not names:
        raise SystemExit(f"no {label} snapshot; run seed_initiatives.py (or the scenario that makes it) first")
    return names[-1]


def apply_fixture(jira, j, variant):
    """Restore the baseline, then derive the scenario's variant (before the audit window)."""
    snap = baseline_snapshot(jira, j, f"cc75-{variant}" if variant.startswith("after-") else "cc75-baseline")
    jira.post(f"{j}/api/admin/snapshots/{snap}/restore", timeout=120).raise_for_status()
    if variant == "no-opt-in":
        keys = [i["key"] for i in jira.get(f"{j}/rest/api/3/search/jql", timeout=60, params={
            "jql": f'labels = cc75-synthetic AND labels = "{OPT_IN}"', "maxResults": 100,
            "fields": "key"}).json()["issues"]]
        for key in keys:
            jira.put(f"{j}/rest/api/2/issue/{key}", timeout=30,
                     json={"update": {"labels": [{"remove": OPT_IN}]}}).raise_for_status()
        return {"baseline": snap, "variant": variant, "opt_in_removed": len(keys)}
    return {"baseline": snap, "variant": variant}


def issue_state(jira, j, key):
    f = jira.get(f"{j}/rest/api/2/issue/{key}", timeout=30, params={"fields": "labels,attachment,status"}).json()["fields"]
    return {"labels": sorted(f.get("labels") or []), "status": (f.get("status") or {}).get("name"),
            "attachments": sorted(a["filename"] for a in f.get("attachment") or [])}


def data_repo_paths(gl, g, prefix="initiative-strategy"):
    pid = quote(DATA_PROJECT, safe="")
    paths, page = [], 1
    while True:
        r = gl.get(f"{g}/projects/{pid}/repository/tree", timeout=60,
                   params={"path": prefix, "recursive": "true", "per_page": 100, "page": page})
        if r.status_code == 404:
            return paths
        r.raise_for_status()
        batch = r.json()
        paths += [x["path"] for x in batch if x.get("type") == "blob"]
        if len(batch) < 100:
            return paths
        page += 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scenario", choices=sorted(SCENARIOS))
    ap.add_argument("--timeout", type=int, default=None)
    args = ap.parse_args()
    sc = SCENARIOS[args.scenario]
    args.timeout = args.timeout or sc.get("timeout", 1800)
    ca = os.getenv("BREADBOARD_CA_FILE") or True
    gl = requests.Session()
    gl.auth = (os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin"))
    gl.verify = ca
    jira = requests.Session()
    jira.auth = (os.getenv("JIRA_ADMIN_USER", "admin"), os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
    jira.verify = ca
    g = f"https://gitlab.{DOMAIN}/api/v4"
    j = f"https://jira.{DOMAIN}"
    pid = quote(PROJECT, safe="")

    fixture = apply_fixture(jira, j, sc["fixture"]) if sc.get("fixture") else None
    live = sc.get("live")
    before = {"data_paths": data_repo_paths(gl, g)} if live else None
    seq0 = jira.get(f"{j}/api/admin/requests", params={"since": 0, "limit": 1}, timeout=30).json()["last_seq"]
    r = gl.post(f"{g}/projects/{pid}/pipeline", timeout=60, json={
        "ref": sc.get("ref", "main"), "variables": [{"key": k, "value": v} for k, v in sc["variables"].items()]})
    if r.status_code >= 400:
        raise SystemExit(f"create pipeline: HTTP {r.status_code}: {r.text[:300]}")
    pipeline = r.json()["id"]
    print(f"{args.scenario}: pipeline {pipeline} variables={sc['variables']}", flush=True)

    t0, jobs, played = time.time(), [], set()
    while time.time() - t0 < args.timeout:
        jobs = gl.get(f"{g}/projects/{pid}/pipelines/{pipeline}/jobs", timeout=60).json()
        for job in jobs:
            if job["name"] in sc.get("play", []) and job["status"] == "manual" and job["id"] not in played:
                gl.post(f"{g}/projects/{pid}/jobs/{job['id']}/play", timeout=60).raise_for_status()
                played.add(job["id"])
                print(f"  played {job['name']} ({job['id']})", flush=True)
        watched = [x for x in jobs if x["name"] in sc["expect"]]
        if watched and all(x["status"] in ("success", "failed", "canceled", "skipped") for x in watched):
            break
        time.sleep(10)

    results, ok = {}, True
    for job in jobs:
        trace = gl.get(f"{g}/projects/{pid}/jobs/{job['id']}/trace", timeout=60).text
        entry = {"id": job["id"], "status": job["status"], "stage": job.get("stage")}
        extra = sc.get("markers", {}).get(job["name"], [])
        if extra:
            entry["markers"] = {m: (m in trace) for m in extra}
            ok &= all(entry["markers"].values())
        if job["name"] in sc["expect"]:
            want_status, marker = sc["expect"][job["name"]]
            entry["expected_status"] = want_status
            entry["status_ok"] = job["status"] == want_status
            if marker:
                entry["marker"] = marker
                entry["marker_found"] = marker in trace
            ok &= entry["status_ok"] and entry.get("marker_found", True)
        results[job["name"]] = entry

    audit1 = jira.get(f"{j}/api/admin/requests", params={"since": seq0}, timeout=30).json()
    entries = audit1["requests"]
    requests_seen = [{"method": e.get("method"), "path": e.get("path"), "status": e.get("status"),
                      "user": e.get("user")} for e in entries if e.get("seq", 0) > seq0]
    reads = [r for r in requests_seen if r["method"] == "POST" and str(r["path"]).endswith(READ_ONLY_POSTS)]
    writes = [r for r in requests_seen if r not in reads]
    live_report = None
    if live:
        import re
        allowed = set(live["processed"])
        named = {k for w in writes for k in re.findall(r"[A-Z][A-Z0-9]+-\d+", str(w["path"]))}
        issues = {k: issue_state(jira, j, k) for k in live["processed"] + live["untouched"]}
        checks = {
            "writes_only_to_selected": named <= allowed,
            "every_selected_written": all(any(k in str(w["path"]) for w in writes) for k in allowed),
            "untouched_not_written": not (named & set(live["untouched"])),
        }
        for k in live["processed"]:
            st = issues[k]
            checks[f"{k}_strategy_attachment"] = f"{k}-strategy.md" in st["attachments"]
            checks[f"{k}_gate_label"] = any(lbl in st["labels"] for lbl in GATE_LABELS)
            checks[f"{k}_lock_released"] = LOCK_LABEL not in st["labels"]
        after_paths = data_repo_paths(gl, g)
        new_paths = sorted(set(after_paths) - set(before["data_paths"]))
        checks["results_published"] = bool(new_paths)
        live_report = {"checks": checks, "issues": issues, "write_keys": sorted(named),
                       "write_paths": sorted({f"{w['method']} {w['path']}" for w in writes}),
                       "data_repo_new_paths": new_paths}
        ok &= all(checks.values())
        if fixture and ok:
            # Only a passing run's end state may seed the next scenario (S7b starts from S7a's).
            snap_name = jira.post(f"{j}/api/admin/snapshots", timeout=120,
                                  json={"label": f"cc75-after-{args.scenario}"}).json()["name"]
            fixture["kept_as_snapshot"] = snap_name
    else:
        ok &= not writes
    if fixture and not live:
        snap = baseline_snapshot(jira, j)
        jira.post(f"{j}/api/admin/snapshots/{snap}/restore", timeout=120).raise_for_status()
        fixture["restored_after"] = snap
    summary = {"scenario": args.scenario, "pipeline": pipeline, "variables": sc["variables"],
               "ref": sc.get("ref", "main"),
               "fixture": fixture, "jobs": results, "live": live_report,
               "jira_writes": writes if not live else len(writes), "jira_read_posts": reads, "ok": ok,
               "checked_at": datetime.now(timezone.utc).isoformat()}
    out = ROOT / "evidence" / f"{args.scenario}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n")
    for name, e in results.items():
        print(f"  {name:<28} {e['status']:<8}" + (f" expected={e['expected_status']}" if "expected_status" in e else "")
              + (f" marker_found={e['marker_found']}" if "marker_found" in e else "")
              + (f" markers={e['markers']}" if "markers" in e else ""))
    if live_report:
        for name, passed in live_report["checks"].items():
            print(f"  check {name:<40} {passed}")
        print(f"  data repo: {len(live_report['data_repo_new_paths'])} new path(s) under initiative-strategy/")
    print(f"  jira writes: {len(writes)} (read-only POSTs: {len(reads)}); ok={ok}; evidence: {out.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
