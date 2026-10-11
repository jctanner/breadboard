#!/usr/bin/env python3
"""Read-only export helpers, streamed over kubectl exec by archive_run.py."""
from datetime import datetime, timezone
import base64
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import ssl


def http(url, body=None, headers=None):
    request = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **(headers or {})})
    context = ssl._create_unverified_context() if url.startswith("https:") else None
    with urllib.request.urlopen(request, context=context, timeout=60) as response:
        return json.load(response)


def job_names(value):
    names = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "job_name" and isinstance(item, str) and item.startswith("script-"):
                names.add(item)
            elif key == "output_json" and isinstance(item, str):
                try:
                    names.update(job_names(json.loads(item)))
                except ValueError:
                    pass
            else:
                names.update(job_names(item))
    elif isinstance(value, list):
        for item in value:
            names.update(job_names(item))
    return names


def info(run_id):
    base = "http://markovd.ai-pipeline.svc.cluster.local:8080/api/v1"
    token = http(base + "/auth/login", {"username": "admin", "password": "admin"})["token"]
    headers = {"Authorization": "Bearer " + token}
    run = http(base + "/runs/" + run_id, headers=headers)
    jobs = sorted(job_names(run))
    dashboard = "http://pipeline-dashboard.ai-pipeline.svc.cluster.local:5000"
    return {"run": run, "workflow": http(base + "/workflows/" + run["workflow_name"], headers=headers),
            "jobs": {name: http(dashboard + "/api/jobs/" + name) for name in jobs}}


def jira_export():
    base = os.environ.get("JIRA_SERVER", "https://jira-emulator.ai-pipeline.svc.cluster.local").rstrip("/")
    auth = base64.b64encode(f"{os.environ.get('JIRA_USER','admin')}:{os.environ.get('JIRA_TOKEN','admin')}".encode()).decode()
    headers = {"Authorization": "Basic " + auth}
    issues, start = [], 0
    while True:
        query = urllib.parse.urlencode({"jql": "ORDER BY key ASC", "startAt": start, "maxResults": 100,
                                        "fields": "*all", "expand": "changelog,renderedFields,names,schema"})
        page = http(base + "/rest/api/2/search?" + query, headers=headers)
        batch = page["issues"]
        issues.extend(batch)
        start += len(batch)
        if start >= page["total"]:
            break
        if not batch:
            raise RuntimeError("Jira pagination stopped early")
    return {"captured_at": datetime.now(timezone.utc).isoformat(), "total": len(issues), "issues": issues}


def stream_paths(paths, database=None):
    """Online SQLite backup plus raw stored files; never follow symlinks."""
    with tempfile.TemporaryDirectory(prefix="strat-archive-") as scratch:
        db_copy = None
        if database:
            path = Path(database)
            if not path.is_file():
                raise RuntimeError(f"missing database: {database}")
            db_copy = Path(scratch) / "database.sqlite"
            with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(db_copy) as target:
                source.backup(target, pages=256)
                assert target.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        inventory = {"captured_at": datetime.now(timezone.utc).isoformat(), "paths": {}, "symlinks_skipped": []}
        with tarfile.open(fileobj=sys.stdout.buffer, mode="w|gz", dereference=False) as archive:
            if db_copy:
                archive.add(db_copy, arcname="database.sqlite")
            for name in paths:
                path = Path(name)
                inventory["paths"][name] = path.exists()
                if not path.exists():
                    continue
                candidates = [path, *path.rglob("*")] if path.is_dir() else [path]
                for candidate in candidates:
                    if candidate.is_symlink():
                        inventory["symlinks_skipped"].append(str(candidate))
                        continue
                    if database and str(candidate) in (database, database + "-wal", database + "-shm"):
                        continue
                    archive.add(candidate, arcname=str(candidate).lstrip("/"), recursive=False)
            data = json.dumps(inventory, indent=2).encode()
            member = tarfile.TarInfo("capture-inventory.json")
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))


def main(argv):
    mode = argv[0]
    if mode == "info":
        print(json.dumps(info(argv[1])))
    elif mode == "jira":
        print(json.dumps(jira_export()))
    elif mode == "files":
        stream_paths(json.loads(argv[1]))
    elif mode == "database":
        stream_paths(json.loads(argv[2]), database=argv[1])
    else:
        raise ValueError(f"unknown export mode: {mode}")


if __name__ == "__main__":
    main(sys.argv[1:])
