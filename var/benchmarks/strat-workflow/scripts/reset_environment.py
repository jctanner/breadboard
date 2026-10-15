#!/usr/bin/env python3
"""Return Breadboard to a clean state for one benchmark test, then seed Jira.

Uses the dashboard's admin API, in this order:

1. refuse to start while any pipeline job is pending or running (a wipe
   would pull files out from under it), unless --force;
2. clear the artifacts volume (/app/artifacts: job logs, strace, API dumps,
   script artifacts) with a cleanup job. The context volume is left alone:
   it holds the pinned architecture snapshot;
3. hard-delete all MLflow experiments, runs and traces;
4. clear Observatory's hallucination data (claims, verdicts, explanations).
   Observatory has no API to clear OTel traces; those stay, tagged by job;
5. reset Jira and seed the scenario with a script job running
   seed_scenario.py from Breadboard at --breadboard-ref.

Run it from outside the job pods (the host, or the Markov runner): step 2
wipes the volume jobs write to.

    reset_environment.py --scenario smoke-one-rfe \\
        --strat-creator-ref <sha> --breadboard-ref <sha> \\
        [--dashboard https://dashboard.local --ca /path/ca.crt]

Prints one JSON summary; exit status 0 only when every step succeeded and the
seed check passed.
"""
import argparse
import json
import os
import sys
import time

import httpx

BREADBOARD_REPO = "https://github.com/jctanner/breadboard"
SEED_SCRIPT = "var/benchmarks/strat-workflow/scripts/seed_scenario.py"
SHA_LEN = 40


def wait_for_job(client: httpx.Client, name: str, timeout: int) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = client.get(f"/api/jobs/{name}").json().get("status")
        if status in ("completed", "failed"):
            return status
        time.sleep(3)
    return "timeout"


def seed_report(logs: str) -> dict | None:
    """The seed script prints one indented JSON object; take the last one."""
    end = logs.rfind("\n}")
    if end < 0:
        return None
    start = logs.rfind("\n{", 0, end)
    if start < 0:
        return None
    try:
        return json.loads(logs[start + 1:end + 2])
    except json.JSONDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--strat-creator-ref", required=True, help="strat-creator commit under test")
    parser.add_argument("--strat-creator-repo", default=os.environ.get("STRAT_CREATOR_REPO") or "https://github.local/opendatahub-io/strat-creator.git",
                        help="source repository for the seed job")
    parser.add_argument("--breadboard-ref", required=True, help="pushed Breadboard commit to run the seed from")
    parser.add_argument("--dashboard", default="https://dashboard.local")
    parser.add_argument("--ca", help="CA bundle for the dashboard's TLS certificate")
    parser.add_argument("--force", action="store_true", help="wipe even while jobs are active")
    parser.add_argument("--keep-mlflow", action="store_true")
    parser.add_argument("--keep-observatory", action="store_true")
    parser.add_argument("--keep-artifacts", action="store_true")
    args = parser.parse_args()
    for name in ("strat_creator_ref", "breadboard_ref"):
        if len(getattr(args, name)) != SHA_LEN:
            raise SystemExit(f"--{name.replace('_', '-')} must be a full 40-character commit")

    client = httpx.Client(base_url=args.dashboard.rstrip("/"), verify=args.ca or True, timeout=120)
    summary = {"scenario": args.scenario, "strat_creator_repo": args.strat_creator_repo,
               "strat_creator_ref": args.strat_creator_ref,
               "breadboard_ref": args.breadboard_ref, "steps": {}}
    ok = True

    def record(step: str, value: dict, success: bool) -> None:
        nonlocal ok
        summary["steps"][step] = {"ok": success, **value}
        ok = ok and success

    active = [j["name"] for j in client.get("/api/jobs").json()
              if j.get("status") in ("pending", "running")]
    if active and not args.force:
        record("preflight", {"active_jobs": active}, False)
        print(json.dumps(summary, indent=2))
        return 1
    record("preflight", {"active_jobs": active}, True)

    # --force overrides the active-job check, not the archive requirement.
    from require_archive import DEFAULT_SINCE, check_archives
    os.environ["DASHBOARD_BASE"] = args.dashboard
    archival = check_archives(os.environ.get("STRAT_ARCHIVE_REQUIRED_SINCE", DEFAULT_SINCE))
    record("archive", archival, archival["ok"])
    if not archival["ok"]:
        print(json.dumps(summary, indent=2))
        return 1

    if not args.keep_artifacts:
        response = client.post("/api/volumes/clear", json={"volumes": ["artifacts"], "mode": "job"}).json()
        if "job_name" in response:
            status = wait_for_job(client, response["job_name"], 300)
            record("artifacts", {"job": response["job_name"], "status": status}, status == "completed")
        else:
            record("artifacts", response, False)

    if not args.keep_mlflow:
        response = client.post("/api/mlflow/hard-clear", json={})
        record("mlflow", response.json(), response.is_success and "error" not in response.json())

    if not args.keep_observatory:
        response = client.post("/api/observatory/clear", json={})
        record("observatory", response.json(), response.is_success and "error" not in response.json())

    if ok:
        submitted = client.post("/api/jobs/submit", json={
            "script": {
                "repo": BREADBOARD_REPO,
                "ref": args.breadboard_ref,
                "path": SEED_SCRIPT,
                "args": ["--scenario", args.scenario, "--strat-creator-ref", args.strat_creator_ref,
                         "--strat-creator-repo", args.strat_creator_repo],
            },
            "args": {"model": "claude-haiku-5-5", "mlflow": False, "otel": False, "api_dump": False},
        }).json()
        if "job_name" not in submitted:
            record("seed", submitted, False)
        else:
            name = submitted["job_name"]
            status = wait_for_job(client, name, 600)
            report = seed_report(client.get(f"/api/jobs/{name}/logs").text) or {}
            record("seed", {"job": name, "status": status,
                            "rfes": [{k: r[k] for k in ("id", "key", "eligible")} for r in report.get("rfes", [])],
                            "discovered": report.get("discovered"), "problems": report.get("problems")},
                   status == "completed" and report.get("ok") is True)

    summary["ok"] = ok
    print(json.dumps(summary, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
