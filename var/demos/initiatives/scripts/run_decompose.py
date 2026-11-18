#!/usr/bin/env python3
"""S8: decompose signed-off Initiatives into RHAI Epics on the epic-decomposer mirror.

Fixture (before the audit window): restore cc75-baseline, then attach the
synthetic strategies (generated/strategies/, scripts/strategy_fixtures.py) to the
signed-off Initiatives. Then play the stand-in job `decompose-initiatives`
(epic-creator PR #40, rhai-initiative workload, Model Relay) on main, and check
the oracle (expected.yaml epic_creator):
  - RHAISTRAT-75025 (decompose): 2..8 new RHAI Epics with parent = the Initiative,
    sibling links only of type Blocks, and epic-creator-auto-decomposed set;
  - RHAISTRAT-75026 (existing Epic children) and RHAISTRAT-75027 (legacy
    Incorporates link to an Epic): skipped, no new Epics, no label;
  - Jira writes touch only the candidates and the new Epics; results reach
    epic-decomposer-results.
With --rerun (default on) a second pipeline runs the job again and must create
no new Epics. The end state is kept as a snapshot (cc75-after-S8, or
cc75-S8-failed) and Jira is restored to the baseline.
Writes evidence/S8-<timestamp>.json.
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
PROJECT = "redhat/rhel-ai/agentic-ci/epic-decomposer"
DATA_PROJECT = "redhat/rhel-ai/agentic-ci/epic-decomposer-results"
JOB = "decompose-initiatives"
# The job YAML is production's: epic-creator from public GitHub main and results on
# gitlab.com. The mirror overrides both per pipeline (pipeline variables beat job
# variables), as rfe-autofixer's schedule does: epic-creator #40 (pending, mirrored in
# the GitHub emulator as pr-40) and the emulator's results repository.
DECOMPOSE_VARIABLES = [
    {"key": "CLAUDE_REPO", "value": "https://github-emulator.ai-pipeline.svc.cluster.local/fullsend-ai/epic-creator.git"},
    {"key": "CLAUDE_REPO_BRANCH", "value": "pr-40"},
    {"key": "RESULTS_REPO", "value":
     "https://gitlab-emulator.ai-pipeline.svc.cluster.local/redhat/rhel-ai/agentic-ci/epic-decomposer-results.git"},
]
PROCESSED = "epic-creator-auto-decomposed"
READ_ONLY_POSTS = ("/search", "/search/jql", "/search/approximate-count", "/issue/bulkfetch", "/expression/eval")
MARKERS = ("cc75: model via Model Relay", "cc75: Model Relay route; skipping setup-gcp-credentials.py",
           "Jira identity probe OK for the JIRA_USERNAME username", "OK: model via ANTHROPIC_BASE_URL")


class Env:
    def __init__(self):
        ca = os.getenv("BREADBOARD_CA_FILE") or True
        self.gl = requests.Session()
        self.gl.auth = (os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin"))
        self.gl.verify = ca
        self.jira = requests.Session()
        self.jira.auth = (os.getenv("JIRA_ADMIN_USER", "admin"), os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
        self.jira.verify = ca
        self.g, self.j = f"https://gitlab.{DOMAIN}/api/v4", f"https://jira.{DOMAIN}"
        self.pid = quote(PROJECT, safe="")

    def snapshot(self, label):
        snaps = self.jira.get(f"{self.j}/api/admin/snapshots", timeout=30).json()["snapshots"]
        names = sorted(s["name"] if isinstance(s, dict) else s for s in snaps)
        names = [n for n in names if label in n]
        if not names:
            raise SystemExit(f"no {label} snapshot")
        return names[-1]

    def restore(self, name):
        self.jira.post(f"{self.j}/api/admin/snapshots/{name}/restore", timeout=120).raise_for_status()

    def keys(self, jql):
        out, token = [], None
        while True:
            params = {"jql": jql, "maxResults": 100, "fields": "key"}
            if token:
                params["nextPageToken"] = token
            page = self.jira.get(f"{self.j}/rest/api/3/search/jql", params=params, timeout=60).json()
            out += [i["key"] for i in page.get("issues", [])]
            token = page.get("nextPageToken")
            if not token or page.get("isLast", True):
                return out

    def fields(self, key, fields="issuetype,parent,labels,issuelinks,summary"):
        return self.jira.get(f"{self.j}/rest/api/2/issue/{key}", params={"fields": fields}, timeout=30).json()["fields"]

    def seq(self):
        return self.jira.get(f"{self.j}/api/admin/requests", params={"since": 0, "limit": 1}, timeout=30).json()["last_seq"]

    def writes_since(self, seq0):
        entries = self.jira.get(f"{self.j}/api/admin/requests", params={"since": seq0}, timeout=30).json()["requests"]
        seen = [{"method": e.get("method"), "path": e.get("path"), "status": e.get("status")}
                for e in entries if e.get("seq", 0) > seq0]
        return [w for w in seen if not (w["method"] == "GET" or (
            w["method"] == "POST" and str(w["path"]).endswith(READ_ONLY_POSTS)))]

    def data_paths(self):
        pid = quote(DATA_PROJECT, safe="")
        out, page = [], 1
        while True:
            r = self.gl.get(f"{self.g}/projects/{pid}/repository/tree", timeout=60,
                            params={"recursive": "true", "per_page": 100, "page": page})
            if r.status_code == 404:
                return out
            r.raise_for_status()
            batch = r.json()
            out += [x["path"] for x in batch if x.get("type") == "blob"]
            if len(batch) < 100:
                return out
            page += 1

    def run_job(self, timeout):
        r = self.gl.post(f"{self.g}/projects/{self.pid}/pipeline", json={"ref": "main", "variables": DECOMPOSE_VARIABLES}, timeout=60)
        r.raise_for_status()
        pipeline = r.json()["id"]
        t0, played, job = time.time(), False, None
        while time.time() - t0 < timeout:
            jobs = self.gl.get(f"{self.g}/projects/{self.pid}/pipelines/{pipeline}/jobs", timeout=60).json()
            job = next((x for x in jobs if x["name"] == JOB), None)
            if job and job["status"] == "manual" and not played:
                self.gl.post(f"{self.g}/projects/{self.pid}/jobs/{job['id']}/play", timeout=60).raise_for_status()
                played = True
                print(f"  pipeline {pipeline}: played {JOB} ({job['id']})", flush=True)
            if played and job and job["status"] in ("success", "failed", "canceled", "skipped"):
                break
            time.sleep(15)
        trace = self.gl.get(f"{self.g}/projects/{self.pid}/jobs/{job['id']}/trace", timeout=60).text if job else ""
        if job:
            traces = Path.home() / ".cache" / "cc75" / "traces"
            traces.mkdir(parents=True, exist_ok=True)
            (traces / f"S8-job{job['id']}.log").write_text(trace)
        cost = re.findall(r"claude-[a-z0-9.-]+\s+\$\s*([0-9.]+)", trace)  # the OTEL summary table
        return {"pipeline": pipeline, "job": job and job["id"], "status": job and job["status"],
                "markers": {m: (m in trace) for m in MARKERS}, "cost_lines": cost[-3:]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-rerun", action="store_true")
    ap.add_argument("--timeout", type=int, default=5 * 3600)
    args = ap.parse_args()
    e = Env()
    oracle = yaml.safe_load((ROOT / "expected.yaml").read_text())["epic_creator"]["candidates"]
    candidates = sorted(oracle)

    base = e.snapshot("cc75-baseline")
    e.restore(base)
    for key in candidates:
        path = ROOT / "generated" / "strategies" / f"{key}-strategy.md"
        r = e.jira.post(f"{e.j}/rest/api/3/issue/{key}/attachments", timeout=60,
                        headers={"X-Atlassian-Token": "no-check"},
                        files={"file": (path.name, path.read_bytes(), "text/markdown")})
        r.raise_for_status()
    rhai_before = set(e.keys("project = RHAI ORDER BY key ASC"))
    data_before = set(e.data_paths())
    seq0 = e.seq()
    print(f"S8: fixture on {base}: strategies attached to {candidates}; RHAI issues before: {len(rhai_before)}", flush=True)

    first = e.run_job(args.timeout)
    rhai_after = set(e.keys("project = RHAI ORDER BY key ASC"))
    new_issues = sorted(rhai_after - rhai_before)
    new = {k: e.fields(k) for k in new_issues}
    by_parent = {}
    for k, f in new.items():
        by_parent.setdefault((f.get("parent") or {}).get("key"), []).append(k)
    link_types = sorted({l["type"]["name"] for f in new.values() for l in f.get("issuelinks") or []
                         if (l.get("outwardIssue") or l.get("inwardIssue") or {}).get("key") in new})
    labels = {k: e.fields(k, "labels")["labels"] for k in candidates}
    writes = e.writes_since(seq0)
    written = sorted({k for w in writes for k in re.findall(r"[A-Z][A-Z0-9]+-\d+", str(w["path"]))})
    data_new = sorted(set(e.data_paths()) - data_before)

    checks = {"job_success": first["status"] == "success", **{f"trace: {m}": v for m, v in first["markers"].items()}}
    for key, spec in oracle.items():
        made = by_parent.get(key, [])
        if spec["action"] == "decompose":
            checks[f"{key} decomposed into {spec['epic_count_min']}..{spec['epic_count_max']} Epics"] = (
                spec["epic_count_min"] <= len(made) <= spec["epic_count_max"])
            checks[f"{key} new Epics are {spec['target_project']} Epics"] = bool(made) and all(
                k.startswith(spec["target_project"] + "-") and new[k]["issuetype"]["name"] == "Epic" for k in made)
            checks[f"{key} labelled {spec['parent_label']}"] = spec["parent_label"] in labels[key]
        else:
            # Meaningful only when submission ran: a failed submit also creates nothing.
            checks[f"{key} skipped ({spec['reason']}): no new Epics"] = bool(new_issues) and not made
            checks[f"{key} skipped ({spec['reason']}): not labelled"] = PROCESSED not in labels[key]
    checks["sibling links are Blocks only"] = set(link_types) <= {"Blocks"}
    checks["writes only to candidates and new Epics"] = set(written) <= set(candidates) | set(new_issues)
    checks["results pushed"] = bool(data_new)

    rerun = None
    if not args.no_rerun:
        seq1 = e.seq()
        rhai_mid = set(e.keys("project = RHAI ORDER BY key ASC"))
        rerun = e.run_job(args.timeout)
        rerun["new_issues"] = sorted(set(e.keys("project = RHAI ORDER BY key ASC")) - rhai_mid)
        rerun["jira_writes"] = len(e.writes_since(seq1))
        checks["rerun job success"] = rerun["status"] == "success"
        checks["rerun creates no Epics"] = not rerun["new_issues"]

    ok = all(checks.values())
    label = "cc75-after-S8" if ok else "cc75-S8-failed"
    kept = e.jira.post(f"{e.j}/api/admin/snapshots", json={"label": label}, timeout=120).json()["name"]
    e.restore(base)
    summary = {"scenario": "S8", "fixture": {"baseline": base, "strategies_attached": candidates},
               "first": first, "rerun": rerun, "checks": checks,
               "new_epics_by_parent": by_parent, "sibling_link_types": link_types,
               "new_epic_summaries": {k: f.get("summary") for k, f in new.items()},
               "candidate_labels": labels, "written_keys": written,
               "write_paths": sorted({f"{w['method']} {re.sub(r'/[0-9]+$', '/<id>', str(w['path']))}" for w in writes}),
               "data_repo_new_paths": data_new, "kept_as_snapshot": kept, "restored_after": base, "ok": ok,
               "checked_at": datetime.now(timezone.utc).isoformat()}
    out = ROOT / "evidence" / f"S8-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    for name, passed in checks.items():
        print(f"  check {name:<70} {passed}")
    print(f"  new Epics by parent: {by_parent}; links: {link_types}")
    print(f"  ok={ok}; kept {kept}; evidence: {out.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
