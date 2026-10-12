#!/usr/bin/env python3
"""Capture authored skill substitution fixtures using a credential-free API stub."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import subprocess
import threading

from run_plugin_experiments import commit_fixture_repository, sha256, tree_manifest, write_json
from run_subagent_skill_experiments import strings


BEGIN = "VARIABLE_FIXTURE_BEGIN"
END = "VARIABLE_FIXTURE_END"
CASES = ["local-args", "local-empty", "local-fallback", "local-escapes", "local-argument-variables", "local-shell", "plugin-args", "plugin-config", "plugin-shell"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass

    def do_POST(self) -> None:
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        server = self.server
        with server.lock:
            server.count += 1
            index = server.count
        invoked = any(c.get("type") == "tool_result" and c.get("tool_use_id") == "fixture_skill" for m in request.get("messages", []) for c in m.get("content", []) if isinstance(c, dict))
        if not server.launched:
            server.launched = True
            blocks = [{"type": "tool_use", "id": "fixture_skill", "name": "Skill", "input": {"skill": server.skill_name, "args": server.arguments}}]
        else:
            blocks = [{"type": "text", "text": "VARIABLE_FIXTURE_DONE"}]
        fixture_texts = []
        errors = []
        for path, value in strings(request.get("messages", [])):
            if BEGIN in value:
                begin = value.index(BEGIN)
                end = value.find(END, begin)
                if end >= 0:
                    excerpt = value[begin:end + len(END)]
                    suffix = value[end + len(END):]
                    footer = re.match(r"\s*\nARGUMENTS: ([^\n]*)", suffix)
                    if footer:
                        excerpt += "\n\nARGUMENTS: " + footer.group(1)
                    fixture_texts.append({"path": path, "text": excerpt})
        for message in request.get("messages", []):
            for block in message.get("content", []):
                if isinstance(block, dict) and block.get("tool_use_id") == "fixture_skill" and block.get("is_error"):
                    errors.append(block)
        write_json(server.captures / f"{index:03d}.json", {"request_index": index, "fixture_texts": fixture_texts, "fixture_errors": errors, "invoked_skill_result_present": invoked, "mock_response": blocks, "tool_names": [t["name"] for t in request.get("tools", [])]})
        stop = "tool_use" if blocks[0]["type"] == "tool_use" else "end_turn"
        result = {"id": f"msg_variables_{index}", "type": "message", "role": "assistant", "model": request.get("model", "fixture"), "content": blocks, "stop_reason": stop, "stop_sequence": None, "usage": {"input_tokens": 10, "output_tokens": 10}}
        if request.get("stream"):
            events = [("message_start", {"type": "message_start", "message": {**result, "content": [], "stop_reason": None, "usage": {"input_tokens": 10, "output_tokens": 0}}})]
            for i, block in enumerate(blocks):
                start = {**block, "input": {}} if block["type"] == "tool_use" else {"type": "text", "text": ""}
                delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])} if block["type"] == "tool_use" else {"type": "text_delta", "text": block["text"]}
                events.extend([( "content_block_start", {"type": "content_block_start", "index": i, "content_block": start}), ("content_block_delta", {"type": "content_block_delta", "index": i, "delta": delta}), ("content_block_stop", {"type": "content_block_stop", "index": i})])
            events.extend([("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": 10}}), ("message_stop", {"type": "message_stop"})])
            encoded = "".join(f"event: {event}\ndata: {json.dumps(value)}\n\n" for event, value in events).encode()
            content_type = "text/event-stream"
        else:
            encoded, content_type = json.dumps(result).encode(), "application/json"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--case", choices=CASES, required=True)
    args = parser.parse_args()
    output, binary = args.output.resolve(), args.binary.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixtures, config = output / "fixtures", output / "config"
    fixtures.mkdir()
    config.mkdir()
    plugin = args.case.startswith("plugin-")
    plugin_root = fixtures / "plugin"
    skill_dir = plugin_root / "skills/variables" if plugin else fixtures / ".claude/skills/variables"
    skill_dir.mkdir(parents=True)
    manifest = {"name": "variable-fixture", "version": "1.0.0", "description": "Authored substitution fixture"}
    if plugin:
        write_json(plugin_root / ".claude-plugin/plugin.json", manifest)
    arguments = 'alpha "two words" third'
    lines = [BEGIN, "skill=${CLAUDE_SKILL_DIR}", "project=${CLAUDE_PROJECT_DIR}", "session=${CLAUDE_SESSION_ID}", "effort=${CLAUDE_EFFORT}", "plugin=${CLAUDE_PLUGIN_ROOT}", "data=${CLAUDE_PLUGIN_DATA}", "all=$ARGUMENTS", "zero=$0", "one=$1", "index=$ARGUMENTS[1]", "missing=$ARGUMENTS[9]|$9", "named=$target|$mode", "unsupported=${SKILL_DIR}|$SKILL_DIR|$CLAUDE_SKILL_DIR|${ARGUMENTS}|${HOME}|${VARIABLE_FIXTURE_ENV}"]
    if args.case == "local-empty":
        arguments = ""
    if args.case == "local-argument-variables":
        arguments = "${CLAUDE_SESSION_ID}"
    if args.case == "local-fallback":
        lines = [BEGIN, "skill=${CLAUDE_SKILL_DIR}", "no argument placeholders", END]
    elif args.case == "local-escapes":
        lines = [BEGIN, r"escaped=\$ARGUMENTS|\$0|\$target", "missing=$ARGUMENTS[9]|$9", "named=$mode", END]
        arguments = "alpha"
    elif args.case.endswith("shell"):
        arguments = ""
        # Output deliberately contains a supported placeholder: it must stay
        # literal because shell preprocessing follows the substitution passes.
        (skill_dir / "show.sh").write_text("#!/bin/sh\nprintf '%s\\n' 'VARIABLE_FIXTURE_SHELL_OUTPUT=${CLAUDE_SKILL_DIR}'\npwd\n")
        lines = [BEGIN, 'inline:', '!`sh "${CLAUDE_SKILL_DIR}/show.sh"`', END]
    elif args.case == "plugin-config":
        arguments = ""
        manifest["userConfig"] = {"color": {"type": "string", "title": "Color", "description": "Fixture color", "default": "DEFAULT_NOT_STORED"}, "secret": {"type": "string", "title": "Secret", "description": "Fake marker only", "sensitive": True}, "unset": {"type": "string", "title": "Unset", "description": "Unset control"}}
        write_json(plugin_root / ".claude-plugin/plugin.json", manifest)
        manifest["userConfig"]["onlydefault"] = {"type": "string", "title": "Default", "description": "Default without stored value", "default": "DEFAULT_ONLY_MARKER"}
        write_json(plugin_root / ".claude-plugin/plugin.json", manifest)
        lines = [BEGIN, "option=${user_config.color}", "sensitive=${user_config.secret}", "unset=${user_config.unset}", "undeclared=${user_config.unknown}", "defaultonly=${user_config.onlydefault}", END]
    else:
        lines.append(END)
    skill_body = "\n".join(lines) + "\n"
    (skill_dir / "SKILL.md").write_text("---\nname: variables\ndescription: Variable substitution fixture\narguments: [target, mode]\neffort: low\nallowed-tools: 'Bash(sh ${CLAUDE_SKILL_DIR}/*)'\n---\n\n" + skill_body)
    provenance = commit_fixture_repository(fixtures)
    fixture_tree = tree_manifest(fixtures)
    settings = {"pluginConfigs": {"variable-fixture@inline": {"options": {"color": "CONFIGURED_COLOR_MARKER", "secret": "FAKE_NONCREDENTIAL_MARKER"}}}} if args.case == "plugin-config" else {}
    write_json(config / "settings.json", settings)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.captures = output / "api-captures"
    server.captures.mkdir()
    server.skill_name = "variable-fixture:variables" if plugin else "variables"
    server.arguments, server.launched, server.count = arguments, False, 0
    server.lock = threading.Lock()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "CLAUDE_CONFIG_DIR": str(config), "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1", "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}", "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential", "VARIABLE_FIXTURE_ENV": "ENV_VALUE_SHOULD_NOT_EXPAND"}
    argv = [str(binary), "--print", "--verbose", "--output-format", "stream-json", "--debug-file", str(output / "debug.log"), "--permission-mode", "bypassPermissions", "--max-turns", "4", "Invoke the authored variable fixture skill, then finish."]
    if plugin:
        argv[1:1] = ["--plugin-dir", str(plugin_root)]
    write_json(output / "command.json", {"case": args.case, "argv": argv, "arguments": arguments, "skill_dir": str(skill_dir), "plugin_root": str(plugin_root) if plugin else None, "project_dir": str(fixtures), "config_dir": str(config), "binary_sha256": sha256(binary), "runner_sha256": sha256(Path(__file__)), "fixture_repository": provenance, "fixture_tree": fixture_tree, "settings": settings, "environment_keys": sorted(env), "inherited_values": ["PATH"]})
    (output / "runner.py").write_bytes(Path(__file__).read_bytes())
    try:
        result = subprocess.run(argv, cwd=fixtures, env=env, capture_output=True, timeout=30)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    (output / "stdout.jsonl").write_bytes(stdout)
    (output / "stderr.txt").write_bytes(stderr)
    captures = [json.loads(p.read_text()) for p in sorted(server.captures.glob("*.json"))]
    summary = {"case": args.case, "returncode": code, "api_requests": server.count, "fixture_errors": [e for c in captures for e in c["fixture_errors"]], "fixture_texts": [e for c in captures for e in c["fixture_texts"]]}
    write_json(output / "results.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "fixture_texts"}))
    return int(bool(code or summary["fixture_errors"] or not summary["fixture_texts"]))


if __name__ == "__main__":
    raise SystemExit(main())
