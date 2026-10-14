#!/usr/bin/env python3
"""Exercise delivered-Skill capture and composition through the native Claude CLI."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import threading

from mock_api_support import respond
from run_plugin_experiments import commit_fixture_repository, sha256, write_json

MODEL = "rits/zai-org/glm-5-3"
ROLES = ("feasibility", "testability", "scope", "architecture")


def text_messages(request):
    return "\n".join(message["content"] if isinstance(message["content"], str) else
                     "\n".join(block.get("text", "") for block in message["content"] if block.get("type") == "text")
                     for message in request["messages"] if message["role"] == "user")


def tool(identity, name, value):
    return {"type": "tool_use", "id": identity, "name": name, "input": value}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        server = self.server
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        prompt = text_messages(request)
        results = {block["tool_use_id"]: block for message in request["messages"]
                   if isinstance(message["content"], list) for block in message["content"]
                   if block.get("type") == "tool_result"}
        assigned = re.search(r"^REVIEW_SCOPE_TARGET: (STRAT-950[12])$", prompt, re.M)
        parent = re.search(r'args "(STRAT-950[12]) --scores-from', prompt)
        if assigned:
            key = assigned[1]
            role = next(role for role in ROLES if f"strategy-{role}-review" in prompt)
            identity = key + "_" + role
            if identity + "_read" not in results:
                blocks = [tool(identity + "_read", "Read", {"file_path": str(server.root / "artifacts/strat-originals" /
                    (key.replace("STRAT", "RHAIRFE") + ".md"))})]
            else:
                blocks = [{"type": "text", "text": server.fixture.report(key, role)}]
            category = "reviewer"
        elif parent:
            key = parent[1]
            stages = [
                ("review_skill", "Skill", {"skill": "strategy-review", "args": key + " --scores-from tmp/composition-scores/" + key +
                    " --architecture-context tests/fixtures/review-composition/context --dry-run"}),
                ("score", "Bash", {"command": f"python3 tests/review-composition/fixture.py prepare-score {key}"}),
                ("begin", "Bash", {"command": f"python3 scripts/review_composition.py begin {key} --scorer-result tmp/composition-scores/{key}/{key}.result.md"}),
            ]
            missing = next((stage for stage in stages if key + "_" + stage[0] not in results), None)
            if missing:
                value = missing[2]
                if missing[0] == "begin" and server.mixed_begin_log:
                    argv = ["python3", "scripts/review_composition.py", "begin", key,
                            "--scorer-result", f"tmp/composition-scores/{key}/{key}.result.md"]
                    code = 'import subprocess; print("Authored shell log before begin", flush=True); subprocess.run(' + repr(argv) + ', check=True)'
                    value = {"command": "python3 -c " + shlex.quote(code)}
                blocks = [tool(key + "_" + missing[0], missing[1], value)]
            elif any(key + "_skill_" + role not in results for role in ROLES):
                blocks = [tool(key + "_skill_" + role, "Skill", {"skill": f"strategy-{role}-review", "args": key})
                          for role in ROLES]
            else:
                commands = [("compose", f"python3 scripts/review_composition.py compose {key}"),
                            ("verify", f"python3 scripts/review_composition.py verify {key}"),
                            ("record", f"python3 scripts/strat_pipeline_state.py record-review {key}")]
                missing = next((stage for stage in commands if key + "_" + stage[0] not in results), None)
                if missing:
                    blocks = [tool(key + "_" + missing[0], "Bash", {"command": missing[1]})]
                else:
                    with server.lock:
                        attempt = server.verdict_attempts.get(key, 0)
                        server.verdict_attempts[key] = attempt + 1
                    verdict = {"key": key, "recommendation": "approve" if key == "STRAT-9501" else "revise",
                               "needs_attention": key == "STRAT-9502"}
                    if attempt == 0:
                        verdict = {"key": key, "recommendation": "revise", "needs_attention": False}
                    blocks = [tool(key + "_output_" + str(attempt), "StructuredOutput", verdict)]
            category = "receiver"
        else:
            with server.lock:
                launched = server.launched
                server.launched = True
            blocks = [{"type": "text", "text": "Composition control complete"}] if launched else [
                tool("workflow", "Workflow", {"name": "review-composition:review-composition"})]
            category = "controller"
        with server.lock:
            server.count += 1
            index = server.count
        write_json(server.capture / f"{index:03d}.request.json", request)
        write_json(server.capture / f"{index:03d}.response.json", {"category": category, "content": blocks})
        respond(self, request, blocks, index)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mixed-begin-log", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chmod(output, 0o700)
    root, config = output / "fixture", output / "config"
    root.mkdir(); config.mkdir()
    for relative in ("scripts", "workflows", ".fullsend/plugins/strat-pipeline", "tests/review-composition",
                     "tests/fixtures/review-composition", ".claude/skills/strategy-review", ".claude/agents"):
        shutil.copytree(args.candidate / relative, root / relative, symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
    setup = subprocess.run(["python3", "tests/review-composition/fixture.py", "setup"], cwd=root, capture_output=True)
    (output / "setup.stdout").write_bytes(setup.stdout)
    (output / "setup.stderr").write_bytes(setup.stderr)
    if setup.returncode:
        raise RuntimeError("Fixture setup failed; see retained setup.stderr")
    spec = importlib.util.spec_from_file_location("authored_composition", root / "tests/review-composition/fixture.py")
    fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
    repository = commit_fixture_repository(root)
    write_json(config / "settings.json", {"enableWorkflows": True, "effortLevel": "medium"})
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.root, server.fixture, server.count, server.launched = root, fixture, 0, False
    server.mixed_begin_log = args.mixed_begin_log
    server.lock, server.verdict_attempts = threading.Lock(), {}
    server.capture = output / "api-dumps"; server.capture.mkdir()
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "CLAUDE_CONFIG_DIR": str(config),
           "DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
           "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential",
           "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
    env.update({name: MODEL for name in ("ANTHROPIC_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL",
               "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_FABLE_MODEL")})
    argv = [str(args.binary.resolve()), "--print", "--verbose", "--output-format", "stream-json", "--model", MODEL,
            "--effort", "medium", "--dangerously-skip-permissions", "--max-turns", "30", "--disallowed-tools", "Edit", "Write", "Agent",
            "--plugin-dir", str(root / ".fullsend/plugins/strat-pipeline"), "--plugin-dir",
            str(root / "tests/fixtures/review-composition/plugin"), "--debug-file", str(output / "debug.log"),
            "/review-composition:review-composition"]
    write_json(output / "command.json", {"argv": argv, "binary_sha256": sha256(args.binary),
               "runner_sha256": sha256(Path(__file__)), "fixture_repository": repository,
               "provider_calls": 0, "inherited_values": ["PATH"], "environment_keys": sorted(env)})
    shutil.copy2(__file__, output / Path(__file__).name)
    shutil.copy2(Path(__file__).with_name("mock_api_support.py"), output / "mock_api_support.py")
    try:
        process = subprocess.run(argv, cwd=root, env=env, capture_output=True, timeout=150)
        code, stdout, stderr = process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    finally:
        server.shutdown(); thread.join(); server.server_close()
    (output / "stdout.jsonl").write_bytes(stdout)
    (output / "stderr.txt").write_bytes(stderr)
    states = [json.loads(p.read_text()) for p in (config / "projects").rglob("workflows/wf_*.json")]
    result = next((state.get("result") for state in states if state.get("status") == "completed"), None)
    checks = []
    for key in fixture.CASES:
        check = subprocess.run(["python3", "scripts/review_composition.py", "verify", key], cwd=root, capture_output=True, text=True)
        checks.append({"key": key, "exit": check.returncode, "stdout": check.stdout, "stderr": check.stderr})
    expected = [{"key": key, "recommendation": "approve" if key == "STRAT-9501" else "revise",
                 "needs_attention": key == "STRAT-9502"} for key in fixture.CASES]
    verification = {"passed": code == 0 and result == expected and all(check["exit"] == 0 for check in checks),
                    "returncode": code, "result": result, "expected": expected, "checks": checks,
                    "verdict_attempts": server.verdict_attempts, "requests": server.count, "provider_calls": 0}
    write_json(output / "verification.json", verification)
    print(json.dumps(verification))
    return 0 if verification["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
