#!/usr/bin/env python3
"""Refuse a reset/wipe until earlier terminal benchmark jobs have host archives."""
from datetime import datetime
import json
import sys

from benchlib import dashboard, read_file

RECEIPTS = "/app/logs/strat-workflow-archive-receipts"
DESIGN_PREFIXES = ("script-run-workflow-", "script-strategy-entrypoint-")
DEFAULT_SINCE = "2026-10-11T13:47:49+00:00"


def check_archives(since):
    cutoff = datetime.fromisoformat(since.replace("Z", "+00:00"))
    status, jobs = dashboard("/api/jobs")
    if status != 200 or not isinstance(jobs, list):
        raise RuntimeError("cannot list pipeline jobs for archival preflight")
    pending, archived = [], []
    for job in jobs:
        name = job["name"]
        hardening = (job.get("mlflow_experiment") or "").startswith("strat-workflow-hardening/")
        if (not name.startswith(DESIGN_PREFIXES) and not hardening) or not job.get("created"):
            continue
        if datetime.fromisoformat(job["created"].replace("Z", "+00:00")) < cutoff:
            continue
        if job["status"] not in ("completed", "failed"):
            pending.append({"job": name, "reason": "job is still active"})
            continue
        raw = read_file(f"{RECEIPTS}/{name}.json")
        try:
            receipt = json.loads(raw) if raw else {}
        except ValueError:
            receipt = {}
        if (receipt.get("job") != name or not receipt.get("verified") or not receipt.get("final")
                or not receipt.get("manifest_sha256") or not receipt.get("archive")):
            pending.append({"job": name, "reason": "no verified final host archive receipt"})
        else:
            archived.append({"job": name, "archive": receipt["archive"]})
    return {"ok": not pending, "required_since": since, "archived": archived, "pending": pending}


def main(argv):
    result = check_archives(argv[0])
    print(json.dumps(result))
    if not result["ok"]:
        print("Archive earlier benchmark runs with archive_run.py before any Jira reset or evidence wipe.", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
