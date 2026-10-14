#!/usr/bin/env python3
"""Vary outer schemas and forked Skill result forms against a local mock API."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import threading

from mock_api_support import respond
from run_plugin_experiments import commit_fixture_repository, sha256, tree_manifest, write_json
from run_subagent_skill_experiments import strings

RECEIVER = "HANDOFF_RECEIVER_PROMPT"
SPECIALIST = "HANDOFF_SPECIALIST_PROMPT"
ASSESSMENT = "HANDOFF_ASSESSMENT_MARKER"
DISSENT = "HANDOFF_DISSENT_REVISE_MARKER"
TARGET = "HANDOFF_TARGET_STRATEGY_A"
SCHEMA = {"type": "object", "properties": {k: {"type": "string"} for k in ("assessment", "dissent", "target")}, "required": ["assessment", "dissent", "target"], "additionalProperties": False}
MARKERS = [RECEIVER, SPECIALIST, ASSESSMENT, DISSENT, TARGET]


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def tool(id: str, name: str, value: dict) -> dict:
    return {"type": "tool_use", "id": id, "name": name, "input": value}


def direct_texts(request: dict) -> list[str]:
    return [b.get("text", "") for m in request.get("messages", []) if m["role"] == "user" for b in (m["content"] if isinstance(m["content"], list) else [text(m["content"])]) if b.get("type") == "text"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass

    def do_POST(self) -> None:
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        s = self.server
        texts = direct_texts(req)
        role = "specialist" if any(SPECIALIST in t for t in texts) else "receiver" if s.route == "cli" or any(RECEIVER in t for t in texts) else "controller"
        results = [b for m in req.get("messages", []) for b in (m["content"] if isinstance(m["content"], list) else []) if b.get("type") == "tool_result"]
        names = [t["name"] for t in req.get("tools", [])]
        has_output = "StructuredOutput" in names
        if role == "controller":
            if not s.launched:
                s.launched = True
                script = 'export const meta={name:"handoff-fixture",description:"Probe nested Skill results"};return await agent(' + json.dumps(RECEIVER) + ', ' + json.dumps({"schema": SCHEMA} if s.schema else {}) + ');'
                blocks = [tool("fixture_workflow", "Workflow", {"script": script})]
            else:
                blocks = [text("HANDOFF_CONTROLLER_DONE")]
        elif role == "receiver" and s.completion == "fork" and not any(b.get("tool_use_id") == "fixture_skill" for b in results):
            blocks = [tool("fixture_skill", "Skill", {"skill": "handoff-fixture", "args": TARGET})]
        elif role == "receiver" and s.completion == "fork":
            delivered = {marker: any(marker in value for b in results if b.get("tool_use_id") == "fixture_skill" for _, value in strings(b.get("content"))) for marker in (ASSESSMENT, DISSENT, TARGET)}
            value = {"assessment": "RECEIVER_ASSESSMENT_DELIVERED=" + str(delivered[ASSESSMENT]), "dissent": "RECEIVER_DISSENT_DELIVERED=" + str(delivered[DISSENT]), "target": TARGET}
            blocks = [tool("fixture_receiver_output", "StructuredOutput", value)] if s.schema and has_output else [text(json.dumps(value))]
        else:
            assessment = f"{ASSESSMENT}: boundary finding; {DISSENT}: revise; {TARGET}"
            value = {"assessment": ASSESSMENT, "dissent": DISSENT, "target": TARGET}
            if s.mode == "prose" or not has_output:
                blocks = [text(assessment)]
            elif s.mode == "earlier-prose" and not any(b.get("tool_use_id") == "fixture_neutral_read" for b in results):
                blocks = [text(assessment), tool("fixture_neutral_read", "Read", {"file_path": str(s.neutral)})]
            elif any(b.get("tool_use_id") == "fixture_leaf_output" for b in results):
                blocks = [text("HANDOFF_POST_OUTPUT_ACK")]
            else:
                blocks = ([text(assessment)] if s.mode == "mixed" else []) + [tool("fixture_leaf_output", "StructuredOutput", value)]
        with s.lock:
            s.count += 1
            index = s.count
        markers = [{"path": p, "markers": [m for m in MARKERS if m in v], "lines": [line[:1500] for line in v.splitlines() if any(m in line for m in MARKERS)]} for p, v in strings(req.get("messages", [])) if any(m in v for m in MARKERS)]
        instruction_sources = {"system": req.get("system", []), "user_text": texts, "structured_tool_description": next((t.get("description", "") for t in req.get("tools", []) if t["name"] == "StructuredOutput"), "")}
        instructions = [{"path": p, "lines": [line[:1000] for line in v.splitlines() if "StructuredOutput" in line or "MUST call" in line]} for p, v in strings(instruction_sources) if "StructuredOutput" in v or "MUST call" in v]
        write_json(s.captures / f"{index:03d}.json", {"request_index": index, "role": role, "tools": names, "structured_schema": next((t.get("input_schema") for t in req.get("tools", []) if t["name"] == "StructuredOutput"), None), "structured_instruction_excerpts": instructions, "marker_excerpts": markers, "fixture_tool_results": [b for b in results if b.get("tool_use_id", "").startswith("fixture_")], "mock_response": blocks})
        respond(self, req, blocks, index)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--route", choices=["cli", "workflow"], required=True)
    parser.add_argument("--schema", action="store_true")
    parser.add_argument("--completion", choices=["direct", "fork"], required=True)
    parser.add_argument("--mode", choices=["prose", "structured", "mixed", "earlier-prose"], required=True)
    parser.add_argument("--leaf-tools", choices=["inherit", "reader"], default="inherit")
    parser.add_argument("--leaf-agent-file", type=Path, help="copy a real reviewer agent definition into the fixture")
    parser.add_argument("--model", help="pin the primary, helpers and aliases, including mock requests")
    args = parser.parse_args()
    binary, output = args.binary.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixtures, config = output / "fixtures", output / "config"
    fixtures.mkdir(); config.mkdir()
    skill = fixtures / ".claude/skills/handoff-fixture/SKILL.md"
    skill.parent.mkdir(parents=True)
    agent = args.leaf_agent_file.stem if args.leaf_agent_file else 'handoff-reader' if args.leaf_tools == 'reader' else 'general-purpose'
    skill.write_text(f"---\nname: handoff-fixture\ndescription: Authored specialist handoff fixture\ncontext: fork\nagent: {agent}\n---\n\n{SPECIALIST}\nAssess only target $ARGUMENTS. Return an assessment and explicit dissent.\n")
    if args.leaf_agent_file:
        definition = fixtures / '.claude/agents' / (agent + '.md')
        definition.parent.mkdir(parents=True)
        definition.write_bytes(args.leaf_agent_file.read_bytes())
    elif args.leaf_tools == 'reader':
        definition = fixtures / '.claude/agents/handoff-reader.md'
        definition.parent.mkdir(parents=True)
        definition.write_text('---\nname: handoff-reader\ndescription: Narrow fixture specialist\ntools: Read\n---\nReturn the authored specialist assessment as text.\n')
    neutral = fixtures / "neutral.txt"
    neutral.write_text("Neutral fixture content.\n")
    commit = commit_fixture_repository(fixtures)
    write_json(config / "settings.json", {"enableWorkflows": True})
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.route, server.schema, server.completion, server.mode = args.route, args.schema, args.completion, args.mode
    server.neutral, server.launched, server.count = neutral, False, 0
    server.captures = output / "api-captures"; server.captures.mkdir()
    server.lock = threading.Lock()
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "CLAUDE_CONFIG_DIR": str(config), "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1", "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}", "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential"}
    argv = [str(binary), "--print", "--verbose", "--output-format", "stream-json", "--debug-file", str(output / "debug.log"), "--permission-mode", "bypassPermissions", "--max-turns", "6", RECEIVER if args.route == "cli" else "HANDOFF_CONTROLLER_PROMPT"]
    if args.model:
        argv[1:1] = ["--model", args.model]
        env.update({key: args.model for key in ("ANTHROPIC_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL",
            "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL",
            "ANTHROPIC_DEFAULT_FABLE_MODEL")})
    if args.schema and args.route == "cli": argv[1:1] = ["--json-schema", json.dumps(SCHEMA)]
    write_json(output / "command.json", {"argv": argv, "route": args.route, "schema": args.schema, "completion": args.completion, "mode": args.mode, "leaf_tools": args.leaf_tools, "binary_sha256": sha256(binary), "runner_sha256": sha256(Path(__file__)), "helper_sha256": sha256(Path(__file__).with_name("mock_api_support.py")), "fixture_repository": commit, "fixture_tree": tree_manifest(fixtures), "environment_keys": sorted(env), "inherited_values": ["PATH"]})
    for name in (Path(__file__).name, "mock_api_support.py"): (output / name).write_bytes(Path(__file__).with_name(name).read_bytes())
    try:
        result = subprocess.run(argv, cwd=fixtures, env=env, capture_output=True, timeout=35)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error: code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    finally: server.shutdown(); thread.join(); server.server_close()
    (output / "stdout.jsonl").write_bytes(stdout); (output / "stderr.txt").write_bytes(stderr)
    captures = [json.loads(p.read_text()) for p in sorted(server.captures.glob("*.json"))]
    write_json(output / "results.json", {"returncode": code, "api_requests": server.count, "roles": [c["role"] for c in captures]})
    print(json.dumps({"route": args.route, "schema": args.schema, "completion": args.completion, "mode": args.mode, "returncode": code, "api_requests": server.count}))
    return int(code == 124)


if __name__ == "__main__": raise SystemExit(main())
