#!/usr/bin/env python3
"""S10: Feature regression - the existing single-RFE strategy path on the new pins.

Production's `workflow-single-rfe` (strat-pipeline main, strat-creator #124 plus the
emulator patches, Model Relay) on one RFE, with the project defaults: an RFE run is
live (STRAT_DRY_RUN=0, FULLSEND_PUBLISH=1); the Initiative tripwire does not apply.

Fixture (before the audit window): restore cc75-baseline, then create one synthetic
RHAIRFE Feature Request that strat-creator's single-RFE intake accepts (release
label strat-creator-3.7, quality label rfe-creator-autofix-rubric-pass, status New,
no existing clone). The fixture's own RFEs are 53-character stubs kept only as link
sources.

Checks: the jobs succeed; a new RHAISTRAT Feature is cloned from the RFE with a
gate label and the strategy-creator provenance; no `initiative-*` label on the
Feature or the RFE; Jira writes touch only the RFE and the new Feature (no
Initiative); results land under RHAISTRAT/ in strat-pipeline-data, nothing new
under initiative-strategy/. The end state is kept as a snapshot and Jira is
restored to the baseline. Writes evidence/S10-<timestamp>.json.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
PROJECT = "redhat/rhel-ai/agentic-ci/strat-pipeline"
DATA_PROJECT = "redhat/rhel-ai/agentic-ci/strat-pipeline-data"
JOB = "workflow-single-rfe"
GATES = ("strat-creator-rubric-pass", "strat-creator-needs-attention")
READ_ONLY_POSTS = ("/search", "/search/jql", "/search/approximate-count", "/issue/bulkfetch", "/expression/eval")
EMULATOR_SOURCE = {
    "STRAT_CREATOR_REPO": "https://github-emulator.ai-pipeline.svc.cluster.local/fullsend-ai/strat-creator.git",
    "STRAT_CREATOR_BRANCH": "cc75-emulator",
}
RFE = {
    "summary": "[SYNTH] Per-namespace request quotas for shared model-serving endpoints",
    "description": """h2. Problem

Teams that share one model-serving endpoint have no way to stop a single namespace from
consuming the endpoint's whole request capacity. During load spikes one workload starves the
others, and operators can only react by scaling the endpoint for everyone.

h2. Who benefits

Platform operators who run shared serving endpoints, and the application teams whose latency
budgets suffer when a neighbour floods the endpoint.

h2. Requested capability

* An operator can set a request-rate quota per namespace on a shared serving endpoint.
* Requests over the quota receive HTTP 429 with a Retry-After header; requests within quota are
  unaffected.
* Quota usage per namespace is exported as metrics and visible on the existing dashboard.
* Quotas can be changed without restarting the endpoint.

h2. Acceptance criteria

* With two namespaces sharing an endpoint and a quota on one of them, saturating traffic from
  that namespace does not raise the other namespace's p95 latency by more than 10 percent.
* Changing a quota takes effect within one minute.
* The 429 responses and quota usage appear in the platform metrics.

h2. Out of scope

Per-user quotas, billing, and quotas on training workloads.""",
    "labels": ["cc75-synthetic", "cc75-s10", "strat-creator-3.7", "rfe-creator-autofix-rubric-pass"],
}


class Env:
    def __init__(self):
        ca = os.getenv("BREADBOARD_CA_FILE") or True
        self.gl, self.jira = requests.Session(), requests.Session()
        self.gl.auth = (os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin"))
        self.jira.auth = (os.getenv("JIRA_ADMIN_USER", "admin"), os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
        self.gl.verify = self.jira.verify = ca
        self.g, self.j = f"https://gitlab.{DOMAIN}/api/v4", f"https://jira.{DOMAIN}"

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

    def fields(self, key):
        return self.jira.get(f"{self.j}/rest/api/2/issue/{key}", timeout=30, params={
            "fields": "issuetype,labels,issuelinks,summary,attachment,status"}).json()["fields"]

    def data_paths(self, prefix):
        pid = quote(DATA_PROJECT, safe="")
        out, page = [], 1
        while True:
            r = self.gl.get(f"{self.g}/projects/{pid}/repository/tree", timeout=60,
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
    e = Env()
    pid = quote(PROJECT, safe="")
    base = e.snapshot("cc75-baseline")
    e.restore(base)
    r = e.jira.post(f"{e.j}/rest/api/2/issue", timeout=60, json={"fields": {
        "project": {"key": "RHAIRFE"}, "issuetype": {"name": "Feature Request"},
        "summary": RFE["summary"], "description": RFE["description"], "labels": RFE["labels"],
        "priority": {"name": "Major"}}})
    r.raise_for_status()
    rfe = r.json()["key"]
    strat_before = set(e.keys("project = RHAISTRAT ORDER BY key ASC"))
    initiatives = set(e.keys("project = RHAISTRAT AND issuetype = Initiative ORDER BY key ASC"))
    data_before = {p: set(e.data_paths(p)) for p in ("RHAISTRAT", "initiative-strategy")}
    seq0 = e.jira.get(f"{e.j}/api/admin/requests", params={"since": 0, "limit": 1}, timeout=30).json()["last_seq"]
    variables = dict(STRAT_EXECUTOR="fullsend", RFE_KEY=rfe, **EMULATOR_SOURCE)
    r = e.gl.post(f"{e.g}/projects/{pid}/pipeline", timeout=60, json={
        "ref": "main", "variables": [{"key": k, "value": v} for k, v in variables.items()]})
    r.raise_for_status()
    pipeline = r.json()["id"]
    print(f"S10: fixture RFE {rfe} on {base}; pipeline {pipeline} variables={variables}", flush=True)

    t0, played, jobs = time.time(), False, []
    while time.time() - t0 < 3 * 3600:
        jobs = e.gl.get(f"{e.g}/projects/{pid}/pipelines/{pipeline}/jobs", timeout=60).json()
        job = next((x for x in jobs if x["name"] == JOB), None)
        if job and job["status"] == "manual" and not played:
            e.gl.post(f"{e.g}/projects/{pid}/jobs/{job['id']}/play", timeout=60).raise_for_status()
            played = True
            print(f"  played {JOB} ({job['id']})", flush=True)
        if played and job and job["status"] in ("success", "failed", "canceled"):
            break
        time.sleep(15)
    statuses = {x["name"]: x["status"] for x in jobs}
    job = next((x for x in jobs if x["name"] == JOB), None)
    trace = e.gl.get(f"{e.g}/projects/{pid}/jobs/{job['id']}/trace", timeout=60).text if job else ""
    traces = Path.home() / ".cache" / "cc75" / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    if job:
        (traces / f"S10-job{job['id']}.log").write_text(trace)

    entries = e.jira.get(f"{e.j}/api/admin/requests", params={"since": seq0}, timeout=30).json()["requests"]
    seen = [{"method": x.get("method"), "path": x.get("path")} for x in entries if x.get("seq", 0) > seq0]
    writes = [w for w in seen if not (w["method"] == "GET" or (
        w["method"] == "POST" and str(w["path"]).endswith(READ_ONLY_POSTS)))]
    written = sorted({k for w in writes for k in re.findall(r"[A-Z][A-Z0-9]+-\d+", str(w["path"]))})
    new_strats = sorted(set(e.keys("project = RHAISTRAT ORDER BY key ASC")) - strat_before)
    features = {k: e.fields(k) for k in new_strats}
    rfe_fields = e.fields(rfe)
    clone_links = {k: [(l["type"]["name"], (l.get("outwardIssue") or l.get("inwardIssue") or {}).get("key"))
                       for l in f.get("issuelinks") or []] for k, f in features.items()}
    data_new = {p: sorted(set(e.data_paths(p)) - data_before[p]) for p in data_before}
    feature = new_strats[0] if len(new_strats) == 1 else None
    f_labels = features[feature]["labels"] if feature else []
    checks = {
        "job success": statuses.get(JOB) == "success",
        "python-tests success": statuses.get("python-tests") == "success",
        "exactly one new RHAISTRAT issue": len(new_strats) == 1,
        "it is a Feature": bool(feature) and features[feature]["issuetype"]["name"] == "Feature",
        "cloned from the RFE": bool(feature) and any(rfe == other for _, other in clone_links[feature]),
        "Feature has a gate label": any(g in f_labels for g in GATES),
        "Feature has no initiative-* label": not any(l.startswith("initiative-") for l in f_labels),
        "RFE has no initiative-* label": not any(l.startswith("initiative-") for l in rfe_fields["labels"]),
        "writes only to the RFE and the new Feature": set(written) <= {rfe, *new_strats},
        "no Initiative written": not (set(written) & initiatives),
        "results under RHAISTRAT/": bool(data_new["RHAISTRAT"]),
        "nothing new under initiative-strategy/": not data_new["initiative-strategy"],
    }
    cost = re.findall(r"Cost: \$([0-9.]+)", trace)
    ok = all(checks.values())
    kept = e.jira.post(f"{e.j}/api/admin/snapshots", json={"label": "cc75-after-S10" if ok else "cc75-S10-failed"},
                       timeout=120).json()["name"]
    e.restore(base)
    summary = {"scenario": "S10", "pipeline": pipeline, "variables": variables, "jobs": statuses, "rfe": rfe,
               "new_rhaistrat": new_strats, "feature_labels": f_labels, "rfe_labels": rfe_fields["labels"],
               "clone_links": clone_links, "written_keys": written,
               "write_paths": sorted({f"{w['method']} {w['path']}" for w in writes}),
               "data_repo_new_paths": data_new, "cost_lines": cost[-2:], "checks": checks, "ok": ok,
               "kept_as_snapshot": kept, "restored_after": base,
               "checked_at": datetime.now(timezone.utc).isoformat()}
    out = ROOT / "evidence" / f"S10-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    for name, passed in checks.items():
        print(f"  check {name:<45} {passed}")
    print(f"  jobs: {statuses}; cost: {cost[-1:]}")
    print(f"  ok={ok}; kept {kept}; evidence: {out.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
