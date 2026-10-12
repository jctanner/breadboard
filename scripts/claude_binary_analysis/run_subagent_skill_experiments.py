#!/usr/bin/env python3
"""Probe skill discovery and other subagent channels using only a mock API.

Cases vary child Read/Bash/Skill/Write and selected primary operations. Every
child returns a fixed answer without the tested information. Retain only
fixture markers and relevant tool results, never full API system prompts.
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

from run_plugin_experiments import commit_fixture_repository, sha256, tree_manifest, write_json

NAME = "isolation-fixture"
DESCRIPTION = "SKILL_ISOLATION_METADATA_MARKER"
BODY = "SKILL_ISOLATION_BODY_MARKER"
CHILD_PROMPT = "SKILL_ISOLATION_CHILD_PROMPT"
CHILD_ANSWER = "CHILD_FIXED_ANSWER_WITHOUT_SKILL_DETAILS"
MEMORY = "SUBAGENT_NESTED_MEMORY_MARKER"
EDIT = "SUBAGENT_FILE_EDIT_MARKER"
OUTPUT = "SUBAGENT_BASH_OUTPUT_MARKER"
MARKERS = (NAME, DESCRIPTION, BODY, MEMORY, EDIT, OUTPUT)


def strings(value: object, path: str = "") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        return [s for i, v in enumerate(value) for s in strings(v, f"{path}[{i}]" )]
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in strings(v, f"{path}.{k}")]
    return []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        server = self.server
        tools = body.get("tools", [])
        tool_names = [t["name"] for t in tools]
        messages = body.get("messages", [])
        direct_user_text = [c.get("text", "") for m in messages if m.get("role") == "user" for c in (m.get("content") if isinstance(m.get("content"), list) else [{"type": "text", "text": m.get("content", "")}]) if c.get("type") == "text"]
        child = any(CHILD_PROMPT in t for t in direct_user_text)
        results = [c for m in messages for c in (m.get("content") if isinstance(m.get("content"), list) else []) if c.get("type") == "tool_result"]
        response_tools = []
        if child:
            if server.case == "no-read" or any(c.get("tool_use_id") == "fixture_child_read" for c in results):
                if server.case in ("file-edit", "file-edit-unread", "file-edit-parent-write") and not any(c.get("tool_use_id") == "fixture_child_write" for c in results):
                    blocks = [{"type": "tool_use", "id": "fixture_child_write", "name": "Write", "input": {"file_path": str(server.target), "content": f"{EDIT}\n"}}]
                elif server.case == "child-skill" and not any(c.get("tool_use_id") == "fixture_child_skill" for c in results):
                    blocks = [{"type": "tool_use", "id": "fixture_child_skill", "name": "Skill", "input": {"skill": NAME}}]
                else:
                    blocks = [{"type": "text", "text": CHILD_ANSWER}]
            else:
                name = "Bash" if server.case in ("explore-bash", "bash-output") else "Read"
                args = {"command": f"printf '%s\\n' {shlex.quote(OUTPUT)}" if server.case == "bash-output" else f"cat {shlex.quote(str(server.target))}"} if name == "Bash" else {"file_path": str(server.target)}
                blocks = [{"type": "tool_use", "id": "fixture_child_read", "name": name, "input": args}]
        elif server.case in ("file-edit", "file-edit-parent-write") and not any(c.get("tool_use_id") == "fixture_parent_read" for c in results):
            blocks = [{"type": "tool_use", "id": "fixture_parent_read", "name": "Read", "input": {"file_path": str(server.target)}}]
        elif server.case == "file-edit-parent-write" and not any(c.get("tool_use_id") == "fixture_parent_write" for c in results):
            blocks = [{"type": "tool_use", "id": "fixture_parent_write", "name": "Write", "input": {"file_path": str(server.target), "content": "Primary-authored baseline content.\n"}}]
        elif not server.launched:
            server.launched = True
            prompt = f"{CHILD_PROMPT}: explore the checkout by reading {server.target}; then return only a fixed answer."
            if server.case == "workflow-read":
                script = 'export const meta={name:"isolation-workflow",description:"Explore nested checkout fixture"};return await agent(' + json.dumps(prompt) + ');'
                blocks = [{"type": "tool_use", "id": "fixture_parent_agent", "name": "Workflow", "input": {"script": script}}]
            else:
                agent = next(t for t in tools if t["name"] in ("Agent", "Task"))
                fields = agent["input_schema"]["properties"]
                agent_type_field = "subagent_type" if "subagent_type" in fields else "subagentType"
                args = {"prompt": prompt, "description": "Explore nested checkout fixture", agent_type_field: "worker" if server.case == "memory-propagate" else "general-purpose" if server.case in ("general-read", "file-edit", "file-edit-unread", "file-edit-parent-write") else "Explore"}
                blocks = [{"type": "tool_use", "id": "fixture_parent_agent", "name": agent["name"], "input": args}]
                response_tools = sorted(fields)
        elif server.case in ("file-edit", "file-edit-unread", "file-edit-parent-write") and not server.post_completion_read and any(CHILD_ANSWER in value for _, value in strings(messages)):
            server.post_completion_read = True
            blocks = [{"type": "tool_use", "id": "fixture_parent_after_read", "name": "Read", "input": {"file_path": str(server.after_target)}}]
        elif server.case in ("memory-read", "memory-propagate") and not server.invoked_skill and any(CHILD_ANSWER in value for _, value in strings(messages)):
            server.invoked_skill = True
            blocks = [{"type": "tool_use", "id": "fixture_parent_skill", "name": "Skill", "input": {"skill": NAME}}]
        elif server.case == "primary-skill" and not server.invoked_skill and any(DESCRIPTION in value for _, value in strings(messages)):
            server.invoked_skill = True
            blocks = [{"type": "tool_use", "id": "fixture_parent_skill", "name": "Skill", "input": {"skill": NAME}}]
        else:
            blocks = [{"type": "text", "text": "PRIMARY_FIXED_ANSWER"}]

        excerpts = []
        for path, value in strings({"system": body.get("system", []), "messages": messages, "tools": tools}):
            markers = [m for m in MARKERS if m in value]
            if not markers:
                continue
            # Save only complete fixture-bearing lines, not neighboring prompts.
            lines = [line[:1000] for line in value.splitlines() if any(m in line for m in MARKERS)]
            excerpts.append({"path": path, "markers": markers, "lines": lines[:15]})
        with server.lock:
            server.captures += 1
            index = server.captures
        fixture_results = [r for r in results if r.get("tool_use_id", "").startswith("fixture_")]
        record = {
            "request_index": index,
            "agent": "child" if child else "primary",
            "tool_names": tool_names,
            "agent_input_fields": response_tools,
            "fixture_marker_excerpts": excerpts,
            "fixture_tool_results": fixture_results,
            "mock_response": blocks,
            "retention_policy": "Only fixture-bearing lines, fixture tool results, tool names and field names; no headers/full system prompts/tool descriptions",
        }
        write_json(server.output / f"{index:03d}.json", record)
        stop = "tool_use" if blocks[0]["type"] == "tool_use" else "end_turn"
        message = {"id": f"msg_isolation_{index}", "type": "message", "role": "assistant", "model": body.get("model", "fixture"), "content": blocks, "stop_reason": stop, "stop_sequence": None, "usage": {"input_tokens": 10, "output_tokens": 10}}
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
            kind = "text/event-stream"
        else:
            encoded = json.dumps(message).encode()
            kind = "application/json"
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--case", choices=["explore-read", "general-read", "workflow-read", "explore-bash", "no-read", "ignored-read", "settings-disabled", "primary-skill", "child-skill", "child-read-skill", "memory-read", "memory-propagate", "file-edit", "file-edit-unread", "file-edit-parent-write", "bash-output"], default="explore-read")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    binary, output = args.binary.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixtures = output / "fixtures"
    checkout = fixtures / "architecture-context"
    skill = checkout / ".claude/skills" / NAME / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(f"---\nname: {NAME}\ndescription: {DESCRIPTION}\n---\n\n{BODY}\nReturn only fixture data.\n")
    target = checkout / "README.md"
    target.write_text("An ordinary nested checkout document. No skill details appear here.\n")
    after_target = fixtures / "AFTER.txt"
    after_target.write_text("An unrelated file used to advance the primary after child completion.\n")
    if args.case in ("memory-read", "memory-propagate"):
        (checkout / "CLAUDE.md").write_text(f"{MEMORY}\nNested fixture instructions.\n")
    if args.case == "child-read-skill":
        target = skill
    if args.case == "ignored-read":
        (fixtures / ".gitignore").write_text("architecture-context/\n")
    provenance = commit_fixture_repository(fixtures)
    # The ignored checkout is deliberately absent from Git; tree_manifest covers it.
    fixture_tree = tree_manifest(fixtures)
    config = output / "config"
    config.mkdir()
    write_json(config / "settings.json", {"enableWorkflows": True})
    api_output = output / "api-captures"
    api_output.mkdir()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.output, server.target, server.case = api_output, target, args.case
    server.after_target, server.post_completion_read = after_target, False
    server.captures, server.launched, server.invoked_skill = 0, False, False
    server.lock = threading.Lock()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "CLAUDE_CONFIG_DIR": str(config), "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1", "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}", "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential", "NO_COLOR": "1"}
    if args.case == "memory-propagate":
        env.update({"CLAUDE_CODE_COORDINATOR_MODE": "1", "CLAUDE_CODE_COORDINATOR_PROPAGATE_NESTED_MEMORY": "1"})
    argv = [str(binary), "--print", "--verbose", "--output-format", "stream-json", "--debug-file", str(output / "debug.log"), "--permission-mode", "bypassPermissions", "--max-turns", "6", "Use an Explore subagent to inspect the nested checkout; return its fixed answer."]
    if args.case == "settings-disabled":
        argv[1:1] = ["--setting-sources", "user"]
    write_json(output / "command.json", {"argv": argv, "case": args.case, "binary_sha256": sha256(binary), "runner_sha256": sha256(Path(__file__)), "fixture_repository": provenance, "fixture_tree": fixture_tree, "environment_keys": sorted(env), "inherited_values": ["PATH"], "coordinator_flags": {k: v for k, v in env.items() if k.startswith("CLAUDE_CODE_COORDINATOR")}, "markers": {"name": NAME, "description": DESCRIPTION, "body": BODY, "memory": MEMORY, "edit": EDIT, "output": OUTPUT}, "child_answer": CHILD_ANSWER})
    (output / "runner.py").write_bytes(Path(__file__).read_bytes())
    started = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=fixtures, env=env, capture_output=True, timeout=args.timeout)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    (output / "stdout.jsonl").write_bytes(stdout)
    (output / "stderr.txt").write_bytes(stderr)
    captures = [json.loads(f.read_text()) for f in sorted(api_output.glob("*.json"))]
    primary = [c for c in captures if c["agent"] == "primary"]
    summary = {"case": args.case, "returncode": code, "duration_seconds": time.monotonic() - started, "api_requests": server.captures, "binary_sha256": sha256(binary), "initial_primary_excerpts": primary[0]["fixture_marker_excerpts"] if primary else [], "later_primary_excerpts": [e for c in primary[1:] for e in c["fixture_marker_excerpts"]], "child_request_count": sum(c["agent"] == "child" for c in captures)}
    write_json(output / "results.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if "excerpts" not in k}))
    return 1 if code else 0


if __name__ == "__main__":
    raise SystemExit(main())
