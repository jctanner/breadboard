#!/usr/bin/env python3
"""Drive the CC-75 Initiatives demo on the emulators, one step at a time.

Every step is a real action through the production jobs the scenarios verified
(S3-S10); nothing is simulated, and nothing here resets Jira between steps, so
the demo builds state as the audience watches. Run from this directory on the
stack host with BREADBOARD_DOMAIN and BREADBOARD_CA_FILE set (see README).

  demo.py reset                 restore the newest cc75-baseline snapshot
  demo.py board                 list the Initiatives: key, status, labels, summary
  demo.py show KEY              one issue: labels, attachments, links, children
  demo.py optin KEY             add initiative-autofix-opt-in (the canary boundary)
  demo.py autofix [--limit N]   rfe-autofixer's schedule-only autofix-initiative (model)
  demo.py tripwire              a live Initiative run on strat-pipeline main: refused
  demo.py dry                   dry Initiative batch, BATCH_SIZE=1, on main (model)
  demo.py live KEY              live strategy for one Initiative on main, INITIATIVE_LIVE=on (model)
  demo.py signoff KEY           add strat-creator-human-sign-off (the human gate)
  demo.py decompose             epic-decomposer's decompose-initiatives (model)
  demo.py killswitch            pipeline with INITIATIVE_STRATEGIES unset: RFE batch only
  demo.py results               the data repos' Initiative folders

Steps that start a pipeline print its URL and, with --wait, follow the job to
the end and print its last lines. Model steps go through Model Relay.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from urllib.parse import quote

import requests

DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
CA = os.getenv("BREADBOARD_CA_FILE") or True
G, J = f"https://gitlab.{DOMAIN}", f"https://jira.{DOMAIN}"
GROUP = "redhat/rhel-ai/agentic-ci"
EMULATOR_SOURCE = {
    "STRAT_CREATOR_REPO": "https://github-emulator.ai-pipeline.svc.cluster.local/fullsend-ai/strat-creator.git",
    "STRAT_CREATOR_BRANCH": "cc75-emulator",
}
DRY = {"STRAT_DRY_RUN": "1", "FULLSEND_PUBLISH": "0"}
LIVE = {"STRAT_DRY_RUN": "0", "FULLSEND_PUBLISH": "1"}
AUTOFIX_SCHEDULE = "cc75 S5 initiative autofix (inactive; played by run_autofix.py)"

gl, jira = requests.Session(), requests.Session()
gl.auth = (os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin"))
jira.auth = (os.getenv("JIRA_ADMIN_USER", "admin"), os.getenv("JIRA_ADMIN_PASSWORD", "admin"))
gl.verify = jira.verify = CA
# Ride out a brief gateway outage (the rehearsal hit a ~1 minute 502 from the GitLab
# ingress). A 502/503/504 means the emulator did not handle the request, so even a POST
# is retried; other errors still fail the step.
_retry = requests.adapters.HTTPAdapter(max_retries=requests.adapters.Retry(
    total=8, backoff_factor=2, status_forcelist=(502, 503, 504), allowed_methods=None,
    raise_on_status=False))
for _session in (gl, jira):
    _session.mount("https://", _retry)


def api(path):
    return f"{G}/api/v4/{path}"


def pid(name):
    return quote(f"{GROUP}/{name}", safe="")


def labels(key, add=(), remove=()):
    ops = [{"add": l} for l in add] + [{"remove": l} for l in remove]
    jira.put(f"{J}/rest/api/2/issue/{key}", json={"update": {"labels": ops}}, timeout=30).raise_for_status()
    print(f"{key}: labels now {sorted(issue(key)['labels'])}")


def issue(key, fields="summary,status,labels,attachment,issuelinks,parent,issuetype"):
    return jira.get(f"{J}/rest/api/2/issue/{key}", params={"fields": fields}, timeout=30).json()["fields"]


def search(jql, fields="summary,status,labels"):
    out, token = [], None
    while True:
        params = {"jql": jql, "maxResults": 100, "fields": fields}
        if token:
            params["nextPageToken"] = token
        page = jira.get(f"{J}/rest/api/3/search/jql", params=params, timeout=60).json()
        out += page.get("issues", [])
        token = page.get("nextPageToken")
        if not token or page.get("isLast", True):
            return out


def pipeline(project, ref="main", variables=None, play=None, wait=False):
    r = gl.post(api(f"projects/{pid(project)}/pipeline"), timeout=60, json={
        "ref": ref, "variables": [{"key": k, "value": v} for k, v in (variables or {}).items()]})
    r.raise_for_status()
    pl = r.json()["id"]
    print(f"pipeline {pl}: {G}/{GROUP}/{project}/-/pipelines/{pl}")
    return follow(project, pl, play, wait)


def follow(project, pl, play=None, wait=False):
    played, job = False, None
    for _ in range(4 * 360 if wait else 40):
        jobs = gl.get(api(f"projects/{pid(project)}/pipelines/{pl}/jobs"), timeout=60).json()
        job = next((x for x in jobs if x["name"] == play), None) if play else None
        if job and job["status"] == "manual" and not played:
            gl.post(api(f"projects/{pid(project)}/jobs/{job['id']}/play"), timeout=60).raise_for_status()
            played = True
            print(f"played {play}: {G}/{GROUP}/{project}/-/jobs/{job['id']}")
            if not wait:
                return pl
        lint = [x for x in jobs if x["stage"] in ("validate", "lint")]
        if not play and lint and all(x["status"] in ("success", "failed", "canceled") for x in lint):
            for x in lint:
                print(f"  {x['name']}: {x['status']}")
            return pl
        if job and job["status"] in ("success", "failed", "canceled"):
            trace = gl.get(api(f"projects/{pid(project)}/jobs/{job['id']}/trace"), timeout=60).text.splitlines()
            print(f"{play}: {job['status']}")
            print("\n".join(line[28:220] for line in trace if "💬" in line or "Cost" in line)[-2000:])
            return pl
        time.sleep(15)
    return pl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step")
    ap.add_argument("key", nargs="?")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--limit", default="3")
    a = ap.parse_args()

    if a.step == "reset":
        snaps = jira.get(f"{J}/api/admin/snapshots", timeout=30).json()["snapshots"]
        name = sorted(s["name"] if isinstance(s, dict) else s for s in snaps if "cc75-baseline" in str(s))[-1]
        jira.post(f"{J}/api/admin/snapshots/{name}/restore", timeout=120).raise_for_status()
        print(f"restored {name}")
    elif a.step == "board":
        for i in search("project = RHAISTRAT AND issuetype = Initiative ORDER BY key ASC"):
            f = i["fields"]
            shown = [l for l in f["labels"] if not l.startswith("cc75-")]
            print(f"{i['key']:<16} {f['status']['name']:<15} {f['summary'][8:70]:<62} {' '.join(shown)}")
    elif a.step == "show":
        f = issue(a.key)
        print(f"{a.key} [{f['issuetype']['name']}] {f['summary']}\n  status: {f['status']['name']}")
        print(f"  labels: {' '.join(sorted(f['labels']))}")
        print(f"  attachments: {[x['filename'] for x in f.get('attachment') or []]}")
        for l in f.get("issuelinks") or []:
            other = l.get("outwardIssue") or l.get("inwardIssue")
            print(f"  link: {l['type']['name']} {other['key']}")
        for c in search(f"parent = {a.key} ORDER BY key ASC", fields="summary,issuetype"):
            print(f"  child: {c['key']} [{c['fields']['issuetype']['name']}] {c['fields']['summary'][:80]}")
    elif a.step == "optin":
        labels(a.key, add=["initiative-autofix-opt-in"])
    elif a.step == "signoff":
        labels(a.key, add=["strat-creator-human-sign-off"])
    elif a.step == "autofix":
        p = pid("rfe-autofixer")
        sched = next(s for s in gl.get(api(f"projects/{p}/pipeline_schedules"), timeout=60).json()
                     if s["description"] == AUTOFIX_SCHEDULE)
        from run_autofix import schedule_variables
        gl.put(api(f"projects/{p}/pipeline_schedules/{sched['id']}"), timeout=60,
               json={"variables": schedule_variables(a.limit)}).raise_for_status()
        pl = gl.post(api(f"projects/{p}/pipeline_schedules/{sched['id']}/play"), timeout=60).json()["id"]
        print(f"schedule played, pipeline {pl}: {G}/{GROUP}/rfe-autofixer/-/pipelines/{pl}")
        if a.wait:
            follow("rfe-autofixer", pl, "autofix-initiative", True)
    elif a.step == "tripwire":
        pipeline("strat-pipeline", variables={"INITIATIVE_STRATEGIES": "on", "STRAT_EXECUTOR": "fullsend"},
                 wait=True)
    elif a.step == "dry":
        pipeline("strat-pipeline", variables={"INITIATIVE_STRATEGIES": "on", "STRAT_EXECUTOR": "fullsend",
                                              **DRY, **EMULATOR_SOURCE, "BATCH_SIZE": "1"},
                 play="workflow-batch-initiative", wait=a.wait)
    elif a.step == "live":
        pipeline("strat-pipeline",
                 variables={"STRAT_EXECUTOR": "fullsend", "STRAT_TYPE": "initiative-strategy", "RFE_KEY": a.key,
                            **LIVE, "INITIATIVE_LIVE": "on", **EMULATOR_SOURCE},
                 play="workflow-single-rfe", wait=a.wait)
    elif a.step == "decompose":
        # The job YAML is production's; point it at epic-creator #40 and the emulator's results.
        from run_decompose import DECOMPOSE_VARIABLES
        pipeline("epic-decomposer", play="decompose-initiatives", wait=a.wait,
                 variables={v["key"]: v["value"] for v in DECOMPOSE_VARIABLES})
    elif a.step == "killswitch":
        pipeline("strat-pipeline", variables={"STRAT_EXECUTOR": "fullsend", **DRY}, wait=True)
        jobs = gl.get(api(f"projects/{pid('strat-pipeline')}/pipelines?per_page=1"), timeout=60).json()
        names = [x["name"] for x in gl.get(api(f"projects/{pid('strat-pipeline')}/pipelines/{jobs[0]['id']}/jobs"),
                                           timeout=60).json()]
        print(f"jobs offered: {', '.join(sorted(names))}")
    elif a.step == "results":
        for project, prefix in (("strat-pipeline-data", "initiative-strategy"),
                                ("rfe-autofixer-results", "initiative-rhaistrat"),
                                ("epic-decomposer-results", "")):
            r = gl.get(api(f"projects/{pid(project)}/repository/tree"), timeout=60,
                       params={"path": prefix, "per_page": 100})
            names = [x["name"] for x in r.json()] if r.ok else []
            print(f"{project}/{prefix}: {', '.join(names) or '(empty)'}")
    else:
        ap.error(f"unknown step {a.step}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
