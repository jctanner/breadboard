#!/usr/bin/env python3
"""End the headless invocation when its native Workflow fails. No model calls."""
import argparse
import json
import os
import signal
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path


def project_path(repository):
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    slug = "".join(c if c.isascii() and c.isalnum() else "-" for c in str(repository.resolve()))
    return config / "projects" / slug


def failed_workflow(project, previous):
    for path in project.glob("*/workflows/*.json"):
        if path in previous:
            continue
        try:
            state = json.loads(path.read_text())
        except (OSError, ValueError):
            continue  # Native state may be between writes.
        name = state.get("workflowName", "").split(":")[-1]
        if name == "strat-pipeline" and state.get("status") in {"failed", "killed", "cancelled", "canceled"}:
            return {k: state.get(k) for k in ("runId", "workflowName", "status", "error", "timestamp")}
    return None


def stop(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        return process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        return process.wait(timeout=10)


def run(repository, report, timeout, command):
    if timeout <= 0 or not command:
        raise ValueError("positive timeout and command required")
    project = project_path(repository)
    previous = set(project.glob("*/workflows/*.json"))
    process = subprocess.Popen(command, start_new_session=True)
    deadline = time.monotonic() + timeout

    def interrupted(signum, _frame):
        stop(process)
        raise SystemExit(128 + signum)

    old = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        while True:
            failure = failed_workflow(project, previous)
            expired = time.monotonic() >= deadline
            if failure or expired:
                result = {"reason": "native_workflow_failed" if failure else "timeout",
                          "observed_at": datetime.now(UTC).isoformat(),
                          "workflow": failure, "primary_pid": process.pid}
                # Preserve the reason before signalling; the shell still owns
                # validation, lock release and native/artifact capture.
                report.parent.mkdir(parents=True, exist_ok=True)
                report.write_text(json.dumps(result, indent=2) + "\n")
                result["process_exit"] = stop(process)
                report.write_text(json.dumps(result, indent=2) + "\n")
                return 1 if failure else 124
            code = process.poll()
            if code is not None:
                return code if code >= 0 else 128 - code
            time.sleep(0.2)
    finally:
        if process.poll() is None:
            stop(process)
        for sig, handler in old.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    return run(args.repository, args.report, args.timeout, command)


if __name__ == "__main__":
    raise SystemExit(main())
