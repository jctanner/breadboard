#!/usr/bin/env python3
"""Network-fault probes for workflow agent calls; loopback API, no credentials.

Single-agent workflow whose conversation hits a persistent injected fault
after a counter side effect. Cases cover the fault classes not exercised by
the operations controls: persistent rate limits, connection resets with no
HTTP response, spend-limit 429s, and 529 overload. Captures per-request
timings so retry backoff is measurable. No real credentials or provider
requests are used.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shlex
import subprocess
import threading
import time

from mock_api_support import respond
from run_plugin_experiments import commit_fixture_repository, sha256, tree_manifest, write_json
from run_workflow_operations_experiments import SCHEMA, parse_lines, snapshots

CASES = ["rate-limit-exhaust", "conn-reset", "spend-limit-429", "overloaded-529", "notify-fault"]


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def call(id: str, name: str, args: dict) -> dict:
    return {"type": "tool_use", "id": id, "name": name, "input": args}


def result_blocks(request: dict) -> list[dict]:
    return [b for m in request.get("messages", []) for b in (m.get("content") if isinstance(m.get("content"), list) else []) if isinstance(b, dict) and b.get("type") == "tool_result"]


def user_texts(request: dict) -> list[str]:
    return [b.get("text", "") for m in request.get("messages", []) if m.get("role") == "user" for b in (m["content"] if isinstance(m.get("content"), list) else [text(m.get("content", ""))]) if b.get("type") == "text"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass

    def do_POST(self) -> None:
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        s = self.server
        with s.lock:
            s.count += 1
            index = s.count
        texts = user_texts(request)
        role = "nested" if any("OPS_NESTED_SKILL" in v for v in texts) else next(("agent-" + key for key in ("A", "B", "C") if any("OPS_AGENT_" + key in v for v in texts)), "controller")
        seen = {r.get("tool_use_id") for r in result_blocks(request)}
        after_counter = "fixture_counter_A" in seen
        started = time.monotonic()
        fault = (after_counter and s.case != "notify-fault") or (s.case == "notify-fault" and getattr(s, "agent_done", False) and role == "controller" and s.launched)
        write_json(s.captures / f"{index:03d}.json", {"request_index": index, "role": role, "started_monotonic": started, "responded_monotonic": time.monotonic(), "fault": fault, "after_counter": after_counter, "model": request.get("model"), "stream": request.get("stream")})
        blocks: list[dict] = []
        if role == "controller":
            if not s.launched:
                s.launched = True
                blocks = [call("fixture_workflow_1", "Workflow", {"script": s.script})]
            else:
                blocks = [text("OPS_CONTROLLER_DONE")]
        else:
            if not after_counter:
                blocks = [call("fixture_counter_A", "Bash", {"command": f"printf '%s\\n' A >> {shlex.quote(str(s.counter))}"})]
            else:
                # The agent's final structured response completes the workflow.
                s.agent_done = True
                value = {"marker": "OPS_RESULT_A", "context": "none"}
                structured = any(t["name"] == "StructuredOutput" for t in request.get("tools", []))
                blocks = [call("fixture_output_A", "StructuredOutput", value)] if structured else [text(json.dumps(value))]
        if fault:
            s.faults += 1
            if s.case == "rate-limit-exhaust" or s.case == "notify-fault":
                payload = json.dumps({"type": "error", "error": {"type": "rate_limit_error", "message": "OPS_INJECTED_RATE_LIMIT"}}).encode()
                self.send_response(429)
                self.send_header("Retry-After", "0")
            elif s.case == "conn-reset":
                # Accept the request, then kill the connection with no HTTP response.
                self.connection.close()
                return
            elif s.case == "spend-limit-429":
                payload = json.dumps({"type": "error", "error": {"type": "rate_limit_error", "message": "Your organization's service spend limit has been reached: service_spend_limit_reached"}}).encode()
                self.send_response(429)
            else:  # overloaded-529
                payload = json.dumps({"type": "error", "error": {"type": "overloaded_error", "message": "OPS_INJECTED_OVERLOADED"}}).encode()
                self.send_response(529)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)
            return
        respond(self, request, blocks, index)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--max-retries", type=int, default=2)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixtures, config = root / "fixtures", root / "config"
    fixtures.mkdir()
    config.mkdir()
    (fixtures / "CLAUDE.md").write_text("OPS_INSTRUCTION_OLD\n")
    write_json(config / "settings.json", {"enableWorkflows": True})
    options = {"schema": SCHEMA}
    script = 'export const meta={name:"operations-fixture",description:"Bounded production control"};return await agent(' + json.dumps("OPS_AGENT_A") + "," + json.dumps(options) + ");"
    provenance = commit_fixture_repository(fixtures)
    driver = Path(__file__)
    write_json(root / "manifest.json", {"case": args.case, "binary_sha256": sha256(args.binary.resolve()), "driver_sha256": sha256(driver), "helper_sha256": sha256(driver.with_name("mock_api_support.py")), "fixture_repository": provenance, "fixture_tree": tree_manifest(fixtures), "script": script, "max_retries": args.max_retries, "bound_seconds": 120})
    for name in (driver.name, "mock_api_support.py"):
        (root / name).write_bytes(driver.with_name(name).read_bytes())
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.captures = root / "api-captures"
    server.captures.mkdir()
    server.case, server.script, server.counter = args.case, script, fixtures / "counter.txt"
    server.launched, server.count, server.faults, server.lock, server.agent_done = False, 0, 0, threading.Lock(), False
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "CLAUDE_CONFIG_DIR": str(config), "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1", "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}", "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential", "CLAUDE_CODE_MAX_RETRIES": str(args.max_retries)}
    argv = [str(args.binary.resolve()), "--print", "--verbose", "--output-format", "stream-json", "--debug-file", str(root / "debug.log"), "--permission-mode", "bypassPermissions", "--max-turns", "8", "OPS_CONTROLLER_PHASE_1"]
    write_json(root / "command.json", {"argv": argv, "environment_keys": sorted(env), "case": args.case})
    started = time.monotonic()
    with (root / "stdout.jsonl").open("wb") as out, (root / "stderr.txt").open("wb") as err:
        proc = subprocess.Popen(argv, cwd=fixtures, env=env, stdout=out, stderr=err, start_new_session=True)
        try:
            code = proc.wait(timeout=100)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, 9)
            proc.wait()
            code = 124
    server.shutdown()
    thread.join()
    server.server_close()
    stream = parse_lines(root / "stdout.jsonl")
    result = {"case": args.case, "returncode": code, "duration_seconds": time.monotonic() - started, "api_requests": server.count, "faults_injected": server.faults, "counter_lines": server.counter.read_text().splitlines() if server.counter.exists() else [], "workflow_states": snapshots(config), "journals": [{"path": str(p), "entries": parse_lines(p)} for p in config.rglob("journal.jsonl")], "terminal_results": [e for e in stream if e.get("type") == "result"]}
    write_json(root / "results.json", result)
    print(json.dumps({"case": args.case, "returncode": code, "requests": server.count, "faults": server.faults, "counter": result["counter_lines"], "statuses": [s["state"]["status"] for s in result["workflow_states"]]}))


if __name__ == "__main__":
    main()
