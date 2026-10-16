#!/usr/bin/env python3
"""Probe unmodified workflow behavior using a fresh config and mock API only.

No caller credentials, headers, system prompts, or tool descriptions are saved.
The mock chooses tool calls deterministically; no real model is contacted.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time

from run_plugin_experiments import commit_fixture_repository, sha256, tree_manifest, write_json


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        server = self.server
        tools = [t["name"] for t in body.get("tools", [])]
        messages = body.get("messages", [])
        results = [
            c for m in messages for c in (m.get("content") if isinstance(m.get("content"), list) else [])
            if c.get("type") == "tool_result"
        ]
        texts = [
            c.get("text", "") for m in messages
            for c in (m.get("content") if isinstance(m.get("content"), list) else [])
            if c.get("type") == "text"
        ]
        # Agent probes deliberately receive a short final text or structured output.
        agent_request = any("WORKFLOW_FIXTURE_AGENT" in t for t in texts)
        structured = "StructuredOutput" in tools and not server.text_only_agents
        notification = next((t for t in reversed(texts) if "<task-notification>" in t and "<status>completed</status>" in t), None)
        resume_input = None
        if not agent_request and server.resume_controls and notification:
            notification_key = notification
            if notification_key not in server.seen_notifications:
                server.seen_notifications.add(notification_key)
                if server.resume_round < 3:
                    launch = next((c.get("content", "") for c in results if "Run ID:" in str(c.get("content", ""))), "")
                    run = re.search(r"Run ID: (wf_[a-z0-9-]+)", str(launch))
                    if run:
                        server.resume_round += 1
                        script = server.input["script"]
                        if server.resume_round >= 2:
                            script = script.replace('label:"first"', 'label:"renamed"')
                        if server.resume_round >= 3:
                            script = script.replace("WORKFLOW_FIXTURE_AGENT second", "WORKFLOW_FIXTURE_AGENT edited-second")
                        resume_input = {**server.input, "script": script, "resumeFromRunId": run.group(1)}
        if agent_request:
            server.agent_requests += 1
            if structured:
                blocks = [{"type": "tool_use", "id": "tool_fixture_structured", "name": "StructuredOutput", "input": {"ok": True, "marker": "structured"}}] if not results else [{"type": "text", "text": "fixture done"}]
            else:
                blocks = [{"type": "text", "text": "WORKFLOW_FIXTURE_FINAL_TEXT"}]
        elif server.blocking_hook_timeout and any(
                c.get("tool_use_id") == "tool_fixture_workflow" and c.get("is_error") for c in results) \
                and not any(c.get("tool_use_id") == "tool_fixture_workflow_retry" for c in results):
            blocks = [{"type": "tool_use", "id": "tool_fixture_workflow_retry", "name": "Workflow", "input": server.input}]
        elif resume_input is not None:
            blocks = [{"type": "tool_use", "id": f"tool_fixture_resume_{server.resume_round}", "name": "Workflow", "input": resume_input}]
        elif server.input is not None and not results:
            blocks = [{"type": "tool_use", "id": "tool_fixture_workflow", "name": "Workflow", "input": server.input}]
        elif results and not any(c.get("tool_use_id") == "tool_fixture_wait" for c in results):
            # TaskOutput waits for background completion before the main loop exits.
            task_id = None
            for result in results:
                match = re.search(r"Task ID: ([a-zA-Z0-9_-]+)", str(result.get("content", "")))
                if match:
                    task_id = match.group(1)
            if task_id and "TaskOutput" in tools:
                blocks = [{"type": "tool_use", "id": "tool_fixture_wait", "name": "TaskOutput", "input": {"task_id": task_id, "block": True, "timeout": 30000}}]
            else:
                blocks = [{"type": "text", "text": "WORKFLOW_FIXTURE_MAIN_DONE"}]
        else:
            blocks = [{"type": "text", "text": "WORKFLOW_FIXTURE_MAIN_DONE"}]
        stop = "tool_use" if any(c["type"] == "tool_use" for c in blocks) else "end_turn"
        with server.lock:
            server.captures += 1
            index = server.captures
        write_json(server.output / f"{index:03d}.json", {
            "tool_names": tools,
            "model": body.get("model"),
            "agent_request": agent_request,
            "resume_round": server.resume_round,
            "completion_notification": notification,
            "tool_results": results,
            "mock_response": blocks,
            "retention_policy": "No headers, system prompts, tool schemas, or unrelated request messages",
        })
        message = {"id": f"msg_fixture_{index}", "type": "message", "role": "assistant", "model": body.get("model", "fixture"), "content": blocks, "stop_reason": stop, "stop_sequence": None, "usage": {"input_tokens": 10, "output_tokens": 10}}
        if body.get("stream"):
            events = [("message_start", {"type": "message_start", "message": {**message, "content": [], "stop_reason": None, "usage": {"input_tokens": 10, "output_tokens": 0}}})]
            for i, block in enumerate(blocks):
                if block["type"] == "tool_use":
                    start = {**block, "input": {}}
                    delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}
                else:
                    start = {"type": "text", "text": ""}
                    delta = {"type": "text_delta", "text": block["text"]}
                events.extend([
                    ("content_block_start", {"type": "content_block_start", "index": i, "content_block": start}),
                    ("content_block_delta", {"type": "content_block_delta", "index": i, "delta": delta}),
                    ("content_block_stop", {"type": "content_block_stop", "index": i}),
                ])
            events.extend([
                ("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": 10}}),
                ("message_stop", {"type": "message_stop"}),
            ])
            encoded = "".join(f"event: {event}\ndata: {json.dumps(value)}\n\n" for event, value in events).encode()
            content_type = "text/event-stream"
        else:
            encoded = json.dumps(message).encode()
            content_type = "application/json"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--case", default="discover")
    parser.add_argument("--input", type=Path, help="JSON Workflow tool input; omitted for discovery")
    parser.add_argument("--settings", type=Path, help="Override isolated settings")
    parser.add_argument("--resume-controls", action="store_true", help="Replay, relabel, then edit the second prompt in the same session")
    parser.add_argument("--text-only-agents", action="store_true", help="Return prose even when StructuredOutput is offered")
    parser.add_argument("--named-fixtures", choices=["valid", "invalid-project"], help="Create competing user/project .js workflows")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--blocking-hook-timeout", action="store_true",
                        help="time out the first Workflow pre-hook and verify it blocks execution")
    args = parser.parse_args()
    binary = args.binary.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixtures = output / "fixtures"
    fixtures.mkdir()
    (fixtures / "README.md").write_text("Credential-free Claude workflow analysis fixture.\n")
    config = output / "config"
    config.mkdir()
    if args.named_fixtures:
        for directory, origin in [(config / "workflows", "user"), (fixtures / ".claude/workflows", "project")]:
            directory.mkdir(parents=True)
            body = 'return ( ;' if origin == "project" and args.named_fixtures == "invalid-project" else f'return {{origin:"{origin}"}};'
            (directory / "different-filename.js").write_text('export const meta={name:"shadowed",description:"Named fixture"};\n' + body)
            (directory / "ignored.ts").write_text('export const meta={name:"typescript-only",description:"Extension fixture"};return 1;')
    provenance = commit_fixture_repository(fixtures)
    settings = json.loads(args.settings.read_text()) if args.settings else {"enableWorkflows": True}
    if args.blocking_hook_timeout:
        import shlex
        probe = output / "timeout-hook.py"
        probe.write_text("import json,sys,time\nfrom pathlib import Path\n"
            f"log=Path({str(output / 'timeout-events.jsonl')!r})\n"
            "first=not log.exists()\n"
            "with log.open('a') as stream: stream.write(json.dumps(json.load(sys.stdin))+'\\n')\n"
            "if first: time.sleep(3)\n")
        settings["hooks"] = {"PreToolUse": [{"matcher": "Workflow", "hooks": [{
            "type": "command", "command": "python3 " + shlex.quote(str(probe)),
            "timeout": 1, "onFailure": "block"}]}]}
    write_json(config / "settings.json", settings)
    api_output = output / "api-captures"
    api_output.mkdir()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.output = api_output
    server.input = json.loads(args.input.read_text()) if args.input else None
    server.captures = 0
    server.agent_requests = 0
    server.lock = threading.Lock()
    server.resume_controls = args.resume_controls
    server.resume_round = 0
    server.seen_notifications = set()
    server.text_only_agents = args.text_only_agents
    server.blocking_hook_timeout = args.blocking_hook_timeout
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
        "NO_COLOR": "1",
    }
    argv = [str(binary), "--print", "--verbose", "--output-format", "stream-json", "--debug-file", str(output / "debug.log"), "--permission-mode", "bypassPermissions", "--max-turns", "8", "Use a workflow to run the supplied local fixture and wait for its completion."]
    if args.blocking_hook_timeout:
        argv[1:1] = ["--model", "rits/zai-org/glm-5-3"]
        env.update({k: "rits/zai-org/glm-5-3" for k in ("ANTHROPIC_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL",
            "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL")})
    write_json(output / "command.json", {"argv": argv, "binary_sha256": sha256(binary), "fixture_repository": provenance, "fixture_tree": tree_manifest(fixtures), "initial_config_tree": tree_manifest(config), "settings": settings, "input": server.input, "controls": {"resume": args.resume_controls, "named_fixtures": args.named_fixtures, "text_only_agents": args.text_only_agents}, "environment_keys": sorted(env), "inherited_values": ["PATH"]})
    started = time.monotonic()
    try:
        completed = subprocess.run(argv, cwd=fixtures, env=env, capture_output=True, timeout=args.timeout)
        code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    (output / "stdout.jsonl").write_bytes(stdout)
    (output / "stderr.txt").write_bytes(stderr)
    result = {"case": args.case, "returncode": code, "duration_seconds": time.monotonic() - started, "api_requests": server.captures, "agent_requests": server.agent_requests, "binary_sha256": sha256(binary)}
    if args.blocking_hook_timeout:
        # The receiving result, rather than a log line alone, must deny the call.
        events = [json.loads(line) for line in stdout.decode().splitlines() if line.startswith("{")]
        denied = [b for event in events if event.get("type") == "user"
                  for b in event.get("message", {}).get("content", [])
                  if isinstance(b, dict) and b.get("tool_use_id") == "tool_fixture_workflow" and b.get("is_error")]
        states = [json.loads(p.read_text()) for p in (config / "projects").rglob("workflows/wf_*.json")]
        denied = [b for b in denied if "hook" in str(b.get("content", "")).lower() and "tim" in str(b.get("content", "")).lower()]
        result["passed"] = bool(denied) and len(states) == 1 and states[0].get("status") == "completed"
        result["denied_timeout_calls"] = len(denied)
        result["workflow_states"] = len(states)
        result["provider_calls"] = 0
    write_json(output / "results.json", result)
    print(json.dumps(result))
    return 1 if code or result.get("passed") is False else 0


if __name__ == "__main__":
    raise SystemExit(main())
