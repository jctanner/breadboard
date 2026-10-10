#!/usr/bin/env python3
"""Submit and wait for dashboard jobs from the Markov runner.

    dashboard_job.py preflight
        Fail if any pipeline job is pending or running: a reset or a new
        test would pull Jira or files out from under it.
    dashboard_job.py submit-run '<run json>' <RFE key>
        Submit one test run (a run from plan_runs.py) as a script job.
    dashboard_job.py submit-seed <scenario> <strat-creator ref> <breadboard repo> <breadboard ref>
        Reset Jira and seed a scenario with seed_scenario.py, as a script job.
    dashboard_job.py wait <job name> --timeout=<seconds> [--must-complete]
        Wait for a job. Prints its status. Exits 0 when it finished either
        way, so a failed test is recorded rather than stopping the tier. A
        job still running at the timeout is stopped and reported as
        "timeout". With --must-complete (housekeeping jobs) anything but
        completed exits 1.
    dashboard_job.py seed-report <job name>
        Read the seed job's report from its log. Exits 1 unless the seed
        check passed; prints the seeded RFE keys, eligible ones first.

Each prints one JSON line.
"""
import json
import sys

from benchlib import dashboard, emit, wait_for_job

SEED_SCRIPT = "var/benchmarks/strat-workflow/scripts/seed_scenario.py"


def last_json_object(logs: str):
    """seed_scenario.py prints one indented JSON object; take the last one."""
    end = logs.rfind("\n}")
    start = logs.rfind("\n{", 0, end) if end >= 0 else -1
    if start < 0:
        return None
    try:
        return json.loads(logs[start + 1:end + 2])
    except json.JSONDecodeError:
        return None


def submit(body: dict) -> int:
    status, response = dashboard("/api/jobs/submit", "POST", body)
    if status >= 300 or "job_name" not in response:
        emit({"ok": False, "http_status": status, "response": response, "request": body})
        return 1
    emit({"ok": True, "job_name": response["job_name"], "request": body})
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    command, rest = argv[0], argv[1:]

    if command == "preflight":
        status, jobs = dashboard("/api/jobs")
        if status != 200:
            emit({"ok": False, "http_status": status, "response": jobs})
            return 1
        active = [j["name"] for j in jobs if j.get("status") in ("pending", "running")]
        emit({"ok": not active, "active_jobs": active})
        return 1 if active else 0

    if command == "submit-run":
        run, rfe_key = json.loads(rest[0]), rest[1]
        return submit({
            "script": {**run["script"], "args": [rfe_key]},
            "args": {
                "model": run["model"],
                "mlflow_experiment": run["mlflow_experiment"],
                "extra_env": run["extra_env"],
                "strace": True,
            },
        })

    if command == "submit-seed":
        scenario, strat_ref, repo, ref = rest
        return submit({
            "script": {
                "repo": repo,
                "ref": ref,
                "path": SEED_SCRIPT,
                "args": ["--scenario", scenario, "--strat-creator-ref", strat_ref],
            },
            "args": {"model": "claude-haiku-5-5", "mlflow": False, "otel": False, "api_dump": False},
        })

    if command == "wait":
        name = rest[0]
        timeout = int(next(a.split("=", 1)[1] for a in rest if a.startswith("--timeout=")))
        job = wait_for_job(name, timeout)
        result = {k: job.get(k) for k in ("name", "status", "created", "completed")}
        result["job_name"] = name
        if job["status"] == "timeout":
            stop_status, _ = dashboard(f"/api/jobs/{name}/stop", "POST", {})
            result["stopped"] = stop_status == 200
        emit(result)
        if "--must-complete" in rest and job["status"] != "completed":
            return 1
        return 0

    if command == "seed-report":
        status, logs = dashboard(f"/api/jobs/{rest[0]}/logs", raw=True)
        report = last_json_object(logs) if status == 200 else None
        if not report:
            emit({"ok": False, "error": "no seed report in the job log", "http_status": status})
            return 1
        rfes = sorted(report.get("rfes", []), key=lambda r: not r.get("eligible"))
        emit({"ok": report.get("ok") is True,
              "rfe_key": rfes[0]["key"] if rfes else "",
              "rfes": [{k: r.get(k) for k in ("id", "key", "eligible")} for r in rfes],
              "discovered": report.get("discovered"), "problems": report.get("problems")})
        return 0 if report.get("ok") is True and rfes else 1

    print(f"unknown command {command!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
