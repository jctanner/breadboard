#!/usr/bin/env python3
"""Probe Claude Code auto-mode with a loopback API and no real credentials.

Runs the unmodified pinned binary with auto mode requested (--proactivity
proactive) against a mock Anthropic endpoint. The mock answers the main
conversation with a Bash tool call and answers auto-mode classifier requests
(detected by their stop sequences and prompt markers) with a configured
verdict. Every request body is captured verbatim so the classifier's model,
system prompt, transcript packaging, and request shape can be inspected.
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

CASES = ["allow", "block", "default-mode-control"]


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def call(id: str, name: str, args: dict) -> dict:
    return {"type": "tool_use", "id": id, "name": name, "input": args}


def system_text(request: dict) -> str:
    system = request.get("system")
    if isinstance(system, str):
        return system
    if isinstance(system, list):
        return " ".join(b.get("text", "") for b in system if isinstance(b, dict))
    return ""


def message_text(request: dict) -> str:
    parts = []
    for m in request.get("messages", []):
        content = m.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            parts.extend(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return " ".join(parts)


def result_blocks(request: dict) -> list[dict]:
    return [b for m in request.get("messages", []) for b in (m.get("content") if isinstance(m.get("content"), list) else []) if isinstance(b, dict) and b.get("type") == "tool_result"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass

    def do_POST(self) -> None:
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        s = self.server
        with s.lock:
            s.count += 1
            index = s.count
        stops = request.get("stop_sequences") or []
        system = system_text(request)
        messages = message_text(request)
        is_classifier = bool(stops) or "<settings_deny_rules>" in system or "<transcript>" in messages or "block threshold" in system
        role = "classifier" if is_classifier else "main"
        stage = None
        if is_classifier:
            thinking = request.get("thinking") or {}
            stage = "stage2" if (thinking.get("type") not in (None, "disabled") or (request.get("max_tokens") or 0) > 512) else "stage1"
        started = time.monotonic()
        record = {
            "request_index": index,
            "role": role,
            "classifier_stage": stage,
            "model": request.get("model"),
            "stream": request.get("stream"),
            "max_tokens": request.get("max_tokens"),
            "stop_sequences": stops,
            "thinking": request.get("thinking"),
            "temperature": request.get("temperature"),
            "metadata": request.get("metadata"),
            "betas": self.headers.get("anthropic-beta"),
            "attribution": self.headers.get("x-anthropic-billing-header") or self.headers.get("anthropic-billing-header"),
            "system_sha256": __import__("hashlib").sha256(system.encode()).hexdigest(),
            "system": system,
            "messages": request.get("messages"),
            "tools": [t.get("name") for t in request.get("tools", [])],
            "started_monotonic": started,
        }
        write_json(s.captures / f"{index:03d}.json", record)
        write_json(s.captures / f"{index:03d}-raw.json", request)
        if is_classifier:
            # Prompt contract: <severity>N</severity>, N in 0-100, 50 is the allow/block boundary.
            if s.case == "allow":
                verdict = "<severity>10</severity>"
            elif stage == "stage1":
                verdict = "<severity>72</severity><category>Data Exfiltration</category>"
            else:
                verdict = "<severity>90</severity><category>Data Exfiltration</category><reason>fixture verdict: block</reason>"
            blocks = [text(verdict)]
        else:
            results = result_blocks(request)
            if not results:
                blocks = [call("fixture_bash", "Bash", {"command": f"printf '%s\\n' {s.case} >> {shlex.quote(str(s.effect))}"})]
            else:
                blocks = [text("FIXTURE_MAIN_DONE")]
        respond(self, request, blocks, index)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--case", choices=CASES, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixtures, config = root / "fixtures", root / "config"
    fixtures.mkdir()
    config.mkdir()
    (fixtures / "CLAUDE.md").write_text("FIXTURE_CLAUDE_MD_CONTEXT\n")
    write_json(config / "settings.json", {})
    effect = root / "effect.txt"
    provenance = commit_fixture_repository(fixtures)
    driver = Path(__file__)
    helper = driver.with_name("mock_api_support.py")
    write_json(root / "manifest.json", {
        "case": args.case,
        "binary_sha256": sha256(args.binary.resolve()),
        "driver_sha256": sha256(driver),
        "helper_sha256": sha256(helper),
        "fixture_repository": provenance,
        "fixture_tree": tree_manifest(fixtures),
        "bound_seconds": 90,
    })
    for name in (driver.name, helper.name):
        (root / name).write_bytes(driver.with_name(name).read_bytes())
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.captures = root / "api-captures"
    server.captures.mkdir()
    server.case, server.effect, server.count, server.lock = args.case, effect, 0, threading.Lock()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "CLAUDE_CONFIG_DIR": str(config),
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_AUTOUPDATER": "1",
        "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}",
        "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential",
        "CLAUDE_CODE_AUTO_MODE_MODEL": "claude-haiku-4-5",
    }
    argv = [str(args.binary.resolve()), "--print", "--verbose", "--output-format", "stream-json", "--debug-file", str(root / "debug.log"), "--max-turns", "8"]
    if args.case != "default-mode-control":
        argv += ["--proactivity", "proactive"]
    argv += ["FIXTURE_PROMPT_RUN_THE_COMMAND"]
    write_json(root / "command.json", {"argv": argv, "environment_keys": sorted(env), "case": args.case})
    started = time.monotonic()
    with (root / "stdout.jsonl").open("wb") as out, (root / "stderr.txt").open("wb") as err:
        proc = subprocess.Popen(argv, cwd=fixtures, env=env, stdout=out, stderr=err, start_new_session=True)
        try:
            code = proc.wait(timeout=75)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, 9)
            proc.wait()
            code = 124
    server.shutdown()
    thread.join()
    server.server_close()
    stream = [json.loads(line) for line in (root / "stdout.jsonl").read_text().splitlines() if line.startswith("{")]
    write_json(root / "results.json", {
        "case": args.case,
        "returncode": code,
        "duration_seconds": time.monotonic() - started,
        "api_requests": server.count,
        "effect_written": effect.read_text().splitlines() if effect.exists() else [],
        "terminal_results": [e for e in stream if e.get("type") == "result"],
        "system_events": [e for e in stream if e.get("type") == "system"],
    })
    print(json.dumps({"case": args.case, "returncode": code, "api_requests": server.count, "effect": (effect.read_text().splitlines() if effect.exists() else [])}))


if __name__ == "__main__":
    main()
