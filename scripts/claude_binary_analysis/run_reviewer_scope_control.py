#!/usr/bin/env python3
"""Exercise real S1 review scope hooks against a credential-free loopback API."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading

from mock_api_support import respond
from run_plugin_experiments import commit_fixture_repository, sha256, tree_manifest, write_json

MODEL = "rits/zai-org/glm-5-3"
ROLES = ["feasibility", "testability", "scope", "architecture"]
HEADINGS = ["Feasibility", "Testability", "Scope assessment", "Architecture assessment"]
SCHEMA = {"type": "object", "properties": {"key": {"type": "string"},
          "recommendation": {"type": "string", "enum": ["approve", "revise", "reject"]},
          "needs_attention": {"type": "boolean"}},
          "required": ["key", "recommendation", "needs_attention"]}


def user_text(request):
    return "\n".join(m["content"] if isinstance(m["content"], str) else
                     "\n".join(b.get("text", "") for b in m["content"] if b.get("type") == "text")
                     for m in request["messages"] if m["role"] == "user")


def tool(identity, name, value):
    return {"type": "tool_use", "id": identity, "name": name, "input": value}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        s = self.server
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt = user_text(request)
        assignment = re.search(r"^REVIEW_SCOPE_TARGET: (RHAISTRAT-[0-9]+)$", prompt, re.M)
        results = {b["tool_use_id"]: b for m in request["messages"] if isinstance(m["content"], list)
                   for b in m["content"] if b.get("type") == "tool_result"}
        if assignment:
            key = assignment[1]
            role = next(role for role in ROLES if f"strategy-{role}-review" in prompt)
            identity = key + "_" + role
            if identity + "_own" not in results:
                peer = "RHAISTRAT-9102" if key != "RHAISTRAT-9102" else "RHAISTRAT-9101"
                blocks = [
                    tool(identity + "_foreign", "Read", {"file_path": str(s.fixture / f"artifacts/strat-tasks/{peer}.md")}),
                    tool(identity + "_batchgrep", "Grep", {"path": str(s.fixture / "artifacts/strat-tasks"), "pattern": "CANARY"}),
                    tool(identity + "_batchglob", "Glob", {"path": str(s.fixture / "artifacts/strat-tasks"), "pattern": "*.md"}),
                    tool(identity + "_own", "Read", {"file_path": str(s.fixture / f"artifacts/strat-tasks/{key}.md")}),
                    tool(identity + "_rfe", "Read", {"file_path": str(s.fixture / f"artifacts/{s.rfe_dir}/{key.replace('STRAT', 'RFE')}.md")}),
                    tool(identity + "_architecture", "Glob", {"path": str(s.fixture / ".context/architecture-context"), "pattern": "**/*.md"}),
                ]
            else:
                # Try returning another ticket once; the completion hook must block it.
                with s.lock:
                    attempts = s.endings.get(identity, 0)
                    s.endings[identity] = attempts + 1
                target = "RHAISTRAT-9999" if attempts == 0 else key
                blocks = [{"type": "text", "text": f"### {target}: Authored feature\n"
                           f"**{HEADINGS[ROLES.index(role)]}**: concerns identified\n"
                           "Finding: acceptance criteria need a measurable failure test.\n"
                           "**Recommendation**: revise"}]
            category = "reviewer"
        elif "Your assigned strategy is" in prompt:
            key = re.search(r"Your assigned strategy is (RHAISTRAT-[0-9]+)", prompt)[1]
            if not any(key + "_skill_" + role in results for role in ROLES):
                blocks = [tool(key + "_skill_" + role, "Skill", {
                    "skill": f"strategy-{role}-review", "args": key}) for role in ROLES]
            else:
                blocks = [tool(key + "_output", "StructuredOutput", {
                    "key": key, "recommendation": "revise", "needs_attention": True})]
            category = "receiver"
        else:
            with s.lock:
                launched = s.launched
                s.launched = True
            blocks = [{"type": "text", "text": "Scope control complete"}] if launched else [tool("workflow", "Workflow", {"name": "reviewer-scope:reviewer-scope"})]
            category = "controller"
        with s.lock:
            s.count += 1
            index = s.count
        write_json(s.captures / f"{index:03d}.request.json", request)
        write_json(s.captures / f"{index:03d}.response.json", {"content": blocks, "category": category})
        respond(self, request, blocks, index)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--frozen-rfe", action="store_true", help="use Fullsend's frozen strat-originals layout without rfe-tasks")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chmod(output, 0o700)
    fixture, config = output / "fixture", output / "config"
    fixture.mkdir(); config.mkdir()
    for role in ROLES:
        source = args.candidate / f".claude/skills/strategy-{role}-review/SKILL.md"
        path = fixture / source.relative_to(args.candidate)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, path)
    path = fixture / ".claude/agents/strat-reviewer.md"
    path.parent.mkdir(parents=True)
    shutil.copy2(args.candidate / path.relative_to(fixture), path)
    plugin = fixture / "plugin"
    shutil.copytree(args.candidate / ".fullsend/plugins/strat-pipeline", plugin)
    authored = args.candidate / "tests/fixtures/reviewer-scope"
    shutil.copytree(authored / "plugin", fixture / "scenario-plugin")
    for folder in ("strat-tasks", "rfe-tasks"):
        destination = "strat-originals" if folder == "rfe-tasks" and args.frozen_rfe else folder
        shutil.copytree(authored / folder, fixture / "artifacts" / destination)
    architecture = fixture / ".context/architecture-context/architecture/fixture"
    architecture.mkdir(parents=True)
    shutil.copy2(authored / "platform.md", architecture / "PLATFORM.md")
    (architecture.parents[1] / "LATEST_VERSION").write_text("fixture\n")
    write_json(config / "settings.json", {"enableWorkflows": True})
    source = commit_fixture_repository(fixture)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.fixture, server.count, server.launched = fixture, 0, False
    server.rfe_dir = "strat-originals" if args.frozen_rfe else "rfe-tasks"
    server.lock, server.endings = threading.Lock(), {}
    server.captures = output / "api-dumps"; server.captures.mkdir()
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8",
           "CLAUDE_CONFIG_DIR": str(config), "DISABLE_AUTOUPDATER": "1",
           "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
           "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}",
           "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential"}
    env["CLAUDE_BIN"] = str(args.binary.resolve())
    env.update({name: MODEL for name in ("ANTHROPIC_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL",
               "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
               "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_FABLE_MODEL")})
    argv = [str(args.binary.resolve()), "--print", "--verbose", "--output-format", "stream-json",
            "--model", MODEL, "--effort", "medium", "--dangerously-skip-permissions",
            "--disallowed-tools", "Bash", "Edit", "Write", "Agent",
            "--plugin-dir", str(plugin), "--plugin-dir", str(fixture / "scenario-plugin"),
            "--debug-file", str(output / "debug.log"),
            "--max-turns", "10", "/reviewer-scope:reviewer-scope"]
    write_json(output / "command.json", {"argv": argv, "binary_sha256": sha256(args.binary),
               "runner_sha256": sha256(Path(__file__)), "fixture_repository": source,
               "fixture_tree": tree_manifest(fixture), "environment_keys": sorted(env),
               "source_rfe_layout": server.rfe_dir,
               "inherited_values": ["PATH"], "provider_calls": 0})
    shutil.copy2(__file__, output / Path(__file__).name)
    shutil.copy2(Path(__file__).with_name("mock_api_support.py"), output / "mock_api_support.py")
    try:
        run = subprocess.run(argv, cwd=fixture, env=env, capture_output=True, timeout=120)
        code, stdout, stderr = run.returncode, run.stdout, run.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    finally:
        server.shutdown(); thread.join(); server.server_close()
    (output / "stdout.jsonl").write_bytes(stdout)
    (output / "stderr.txt").write_bytes(stderr)
    events = [json.loads(line) for path in (fixture / "tmp/review-scope").glob("*.jsonl")
              for line in path.read_text().splitlines()]
    requests = [json.loads(path.read_text()) for path in server.captures.glob("*.request.json")]
    receipts = [b for request in requests for message in request["messages"]
                if isinstance(message["content"], list) for b in message["content"]
                if b.get("type") == "tool_result" and "_skill_" in b["tool_use_id"]]
    unique = {b["tool_use_id"]: b for b in receipts}
    denied = [e for e in events if not e["allowed"]]
    stop_denied = [e for e in denied if e["event"] == "SubagentStop"]
    foreign_leaks = []
    for request in requests:
        prompt = user_text(request)
        target = re.search(r"^REVIEW_SCOPE_TARGET: RHAISTRAT-(910[123])$", prompt, re.M)
        if target:
            expected = {"9101": "TIMEOUT", "9102": "RETENTION", "9103": "ROTATION"}[target[1]]
            foreign_leaks.extend(marker for marker in ["TIMEOUT", "RETENTION", "ROTATION"]
                                 if marker != expected and marker + "_SCOPE_CANARY" in json.dumps(request["messages"]))
    result = {"returncode": code, "api_requests": server.count, "provider_calls": 0,
              "reviewer_agents": len(list((fixture / "tmp/review-scope").glob("*.jsonl"))),
              "denied_tools": len([e for e in denied if e["event"] == "PreToolUse"]),
              "denied_completions": len(stop_denied), "delivered_reports": len(unique),
              "reports_valid": all(re.search(r"### " + re.escape(identity.split('_skill_')[0]) + ":", json.dumps(value))
                                   for identity, value in unique.items()),
              "foreign_input_leaks": foreign_leaks,
              "passed": code == 0 and len(unique) == 12 and len(stop_denied) == 12
              and len([e for e in denied if e["event"] == "PreToolUse"]) == 36 and not foreign_leaks}
    result["passed"] = result["passed"] and result["reports_valid"]
    write_json(output / "results.json", result)
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
