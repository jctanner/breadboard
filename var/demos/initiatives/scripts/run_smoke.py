#!/usr/bin/env python3
"""Run a CC-75 CI smoke project in the GitLab emulator and record evidence.

  run_smoke.py fullsend-gateway

Ensures group `cc75` and project `cc75/<name>` (admin:admin, the emulator's
development default), pushes smoke/<name>/ as the project's main branch,
creates one pipeline for that commit (unless one already exists for it and
--rerun is not given), waits for it, and writes the job trace to
~/.cache/cc75/traces/ plus a summary (status, SMOKE_* lines, timings) to
evidence/smoke-<name>-<timestamp>.json.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
CACHE = Path(os.getenv("CC75_CACHE", Path.home() / ".cache" / "cc75" / "sources")).parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("name")
    ap.add_argument("--gitlab-url", default=os.getenv("GITLAB_URL", f"https://gitlab.{DOMAIN}"))
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--timeout", type=int, default=3600)
    args = ap.parse_args()
    user, password = os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin")
    ca = os.getenv("BREADBOARD_CA_FILE")
    base = args.gitlab_url.rstrip("/")
    api = requests.Session()
    api.auth = (user, password)
    api.verify = ca or True
    v4 = f"{base}/api/v4"

    def call(method, path, **kw):
        for attempt in range(6):
            r = api.request(method, f"{v4}/{path}", timeout=60, **kw)
            if r.status_code == 503 and "lock" in r.text.lower():
                time.sleep(0.5 * 2 ** attempt)
                continue
            return r
        return r

    groups = [g for g in call("GET", "groups", params={"search": "cc75"}).json() if g["full_path"] == "cc75"]
    group = groups[0] if groups else call("POST", "groups", json={"name": "cc75", "path": "cc75",
                                                                    "visibility": "private"}).json()
    proj_path = f"cc75/{args.name}"
    r = call("GET", f"projects/{quote(proj_path, safe='')}")
    if r.status_code == 404:
        r = call("POST", "projects", json={"name": args.name, "path": args.name,
                                            "namespace_id": group["id"], "visibility": "private",
                                            "default_branch": "main", "initialize_with_readme": False})
    r.raise_for_status()
    project = r.json()

    src = ROOT / "smoke" / args.name
    work = CACHE / "work" / f"smoke-{args.name}"
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(src, work)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_TERMINAL_PROMPT="0", GIT_AUTHOR_NAME="cc75", GIT_AUTHOR_EMAIL="cc75@example.invalid",
               GIT_COMMITTER_NAME="cc75", GIT_COMMITTER_EMAIL="cc75@example.invalid",
               GIT_AUTHOR_DATE="2026-11-15T00:00:00Z", GIT_COMMITTER_DATE="2026-11-15T00:00:00Z")
    tls = ["-c", f"http.sslCAInfo={ca}"] if ca else []
    remote = base.replace("://", f"://{quote(user)}:{quote(password)}@", 1) + f"/{proj_path}.git"
    for cmd in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", f"cc75 {args.name} smoke"],
                [*tls, "push", "-q", "-f", remote, "main:main"]):
        res = subprocess.run(["git", *cmd], cwd=work, env=env, capture_output=True, text=True)
        if res.returncode:
            raise SystemExit(f"git {cmd[0]}: {(res.stderr or res.stdout).replace(password, '***')}")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=work, capture_output=True, text=True).stdout.strip()

    pid = None
    if not args.rerun:
        existing = call("GET", f"projects/{project['id']}/pipelines", params={"sha": sha}).json()
        pid = existing[0]["id"] if existing else None
    if pid is None:
        r = call("POST", f"projects/{project['id']}/pipeline", json={"ref": "main"})
        if r.status_code >= 400:
            raise SystemExit(f"create pipeline: HTTP {r.status_code}: {r.text[:300]}")
        pid = r.json()["id"]
    print(f"project {proj_path} (id {project['id']}) commit {sha[:8]} pipeline {pid}", flush=True)

    t0, status = time.time(), None
    while time.time() - t0 < args.timeout:
        p = call("GET", f"projects/{project['id']}/pipelines/{pid}").json()
        if p["status"] != status:
            status = p["status"]
            print(f"  {int(time.time() - t0):>5}s pipeline {status}", flush=True)
        if status in ("success", "failed", "canceled", "skipped"):
            break
        time.sleep(15)
    jobs = call("GET", f"projects/{project['id']}/pipelines/{pid}/jobs").json()
    traces = CACHE / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    summary = {"project": proj_path, "commit": sha, "pipeline": pid, "status": status,
               "wall_seconds": int(time.time() - t0), "jobs": []}
    for job in jobs:
        trace = call("GET", f"projects/{project['id']}/jobs/{job['id']}/trace").text
        (traces / f"{args.name}-job{job['id']}.log").write_text(trace)
        # Emulator trace lines look like "<timestamp> 01O <text>"; match on the text.
        texts = [l.split(" ", 2)[2] if len(l.split(" ", 2)) == 3 else l for l in trace.splitlines()]
        marks = [t.strip() for t in texts if t.lstrip().startswith(("SMOKE", "SANDBOX_OK", "PROBE"))]
        summary["jobs"].append({"id": job["id"], "name": job["name"], "status": job["status"],
                                "markers": marks[:40], "trace_tail": trace.splitlines()[-60:]})
    out = ROOT / "evidence" / f"smoke-{args.name}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n")
    for job in summary["jobs"]:
        print(f"job {job['id']} {job['name']}: {job['status']}")
        print("\n".join("  " + m for m in job["markers"]))
    print(f"evidence: {out.relative_to(ROOT)}; full trace under {traces}")
    return 0 if status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
