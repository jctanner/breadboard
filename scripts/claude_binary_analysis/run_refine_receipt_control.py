#!/usr/bin/env python3
"""Run actual S1 refine/readiness code with forced faults and a loopback API."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading

from mock_api_support import respond
from hook_control_support import observed_settings
from run_plugin_experiments import commit_fixture_repository, sha256, write_json

MODEL = "rits/zai-org/glm-5-3"
KEYS = [f"STRAT-{number}" for number in range(9401, 9405)]


def user_text(request):
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
        prompt = user_text(request)
        results = {block["tool_use_id"] for message in request["messages"] if isinstance(message["content"], list)
                   for block in message["content"] if block.get("type") == "tool_result"}
        key_match = re.search(r'strategy-refine skill with args "(STRAT-[0-9]+)', prompt)
        leaf = re.search(r"fixture.py apply (STRAT-[0-9]+)", prompt)
        if "This fixture tests receipt handling" in prompt and not key_match:
            key = leaf[1]
            if key in KEYS[:2] and key + "_apply" not in results:
                blocks = [tool(key + "_apply", "Bash", {"command": f"python3 tests/refine-receipts/fixture.py apply {key}"})]
            else:
                blocks = [{"type": "text", "text": "Fixture action completed " + key if key in KEYS[:2]
                           else "Fixture stopped without refinement " + key}]
            role = "fixture leaf " + key
        elif "strat_pipeline_state.py refine-status` once" in prompt:
            if "snapshot_read" not in results:
                blocks = [tool("snapshot_read", "Bash", {"command": "python3 scripts/strat_pipeline_state.py refine-status"})]
            else:
                expected = json.loads(subprocess.check_output(["python3", "scripts/strat_pipeline_state.py", "refine-status"], cwd=server.root))
                with server.lock:
                    attempt = server.snapshot_attempts
                    server.snapshot_attempts += 1
                claim = {**expected, "refined": KEYS, "rejected": []} if attempt == 0 else expected
                blocks = [tool("snapshot_output_" + str(attempt), "StructuredOutput", claim)]
            role = "checkpoint"
        elif "strat_pipeline_state.py read` once" in prompt:
            if "initial_read" not in results:
                blocks = [tool("initial_read", "Bash", {"command": "python3 scripts/strat_pipeline_state.py read"})]
            else:
                value = json.loads(subprocess.check_output(["python3", "scripts/strat_pipeline_state.py", "read"], cwd=server.root))
                blocks = [tool("initial_output", "StructuredOutput", value)]
            role = "initial"
        elif key_match:
            key = key_match[1]
            if key + "_skill" not in results:
                blocks = [tool(key + "_skill", "Skill", {"skill": "strategy-refine", "args": key + " --dry-run"})]
            elif key in KEYS[:2] and key + "_mark" not in results:
                blocks = [tool(key + "_mark", "Bash", {"command": f"python3 scripts/strat_pipeline_state.py mark refine {key}"})]
            else:
                with server.lock:
                    attempt = server.receipts.get(key, 0)
                    server.receipts[key] = attempt + 1
                recorded = key
                if key == KEYS[1]:
                    recorded = json.dumps({"recorded": key}) if attempt == 0 else "none"
                if key == KEYS[3]:
                    recorded = KEYS[0] if attempt == 0 else "none"
                blocks = [tool(key + "_output_" + str(attempt), "StructuredOutput", {"recorded": recorded})]
            role = "refine " + key
        else:
            with server.lock:
                launched = server.launched
                server.launched = True
            blocks = [{"type": "text", "text": "Receipt control complete"}] if launched else [
                tool("workflow", "Workflow", {"name": "refine-receipts:refine-receipts", "args": {"receipt_faults": {}}})]
            role = "controller"
        with server.lock:
            server.count += 1
            index = server.count
        write_json(server.capture / f"{index:03d}.request.json", request)
        write_json(server.capture / f"{index:03d}.response.json", {"role": role, "content": blocks})
        respond(self, request, blocks, index)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chmod(output, 0o700)
    root, config = output / "fixture", output / "config"
    root.mkdir(); config.mkdir()
    for path in ["scripts", "workflows", ".fullsend/plugins/strat-pipeline", "tests/refine-receipts", "tests/fixtures/refine-receipts"]:
        shutil.copytree(args.candidate / path, root / path, ignore=shutil.ignore_patterns("__pycache__"))
    skill = root / ".claude/skills/strategy-refine/SKILL.md"
    skill.parent.mkdir(parents=True)
    shutil.copy2(root / "tests/fixtures/refine-receipts/strategy-refine.md", skill)
    subprocess.run(["python3", "tests/refine-receipts/fixture.py", "setup", *KEYS], cwd=root, check=True, capture_output=True)
    fixture_repository = commit_fixture_repository(root)
    write_json(config / "settings.json", observed_settings(output, {"enableWorkflows": True}))
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.root, server.count, server.launched = root, 0, False
    server.lock, server.receipts, server.snapshot_attempts = threading.Lock(), {}, 0
    server.capture = output / "api-dumps"; server.capture.mkdir()
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8",
           "CLAUDE_CONFIG_DIR": str(config), "DISABLE_AUTOUPDATER": "1",
           "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential",
           "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
    env["CLAUDE_BIN"] = str(args.binary.resolve())
    env.update({name: MODEL for name in ["ANTHROPIC_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL",
        "ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_FABLE_MODEL"]})
    argv = [str(args.binary.resolve()), "--print", "--verbose", "--output-format", "stream-json",
        "--model", MODEL, "--effort", "medium", "--dangerously-skip-permissions", "--max-turns", "10",
        "--plugin-dir", str(root / ".fullsend/plugins/strat-pipeline"),
        "--plugin-dir", str(root / "tests/fixtures/refine-receipts/plugin"),
        "--debug-file", str(output / "debug.log"), "/refine-receipts:refine-receipts"]
    write_json(output / "command.json", {"argv": argv, "binary_sha256": sha256(args.binary),
        "runner_sha256": sha256(Path(__file__)), "fixture_repository": fixture_repository,
        "provider_calls": 0, "inherited_environment_values": ["PATH"], "environment_keys": sorted(env)})
    shutil.copy2(__file__, output / Path(__file__).name)
    shutil.copy2(Path(__file__).with_name("mock_api_support.py"), output / "mock_api_support.py")
    shutil.copy2(Path(__file__).with_name("hook_control_support.py"), output / "hook_control_support.py")
    try:
        process = subprocess.run(argv, cwd=root, env=env, capture_output=True, timeout=120)
        code, stdout, stderr = process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    finally:
        server.shutdown(); thread.join(); server.server_close()
    (output / "stdout.jsonl").write_bytes(stdout)
    (output / "stderr.txt").write_bytes(stderr)
    events = [json.loads(line) for line in (root / "tmp/refine-checkpoints/events.jsonl").read_text().splitlines()]
    states = [json.loads(p.read_text()) for p in (config / "projects").rglob("workflows/wf_*.json")]
    result = next((state.get("result") for state in states
                   if state.get("state", state.get("status")) == "completed"), None)
    expected = {"ready": KEYS[:2], "failed": ["refine:" + key for key in KEYS[2:]], "faults": {}, "injected": []}
    progress = json.loads((root / "tmp/strat-progress.json").read_text())
    verification = {"passed": code == 0 and result == expected and set(progress["refine"]) == set(KEYS[:2])
                    and any(not event["allowed"] for event in events),
                    "returncode": code, "result": result, "expected": expected,
                    "saved_refined": sorted(progress["refine"]), "hook_events": len(events),
                    "blocked_readiness_claims": sum(not event["allowed"] for event in events),
                    "requests": server.count, "provider_calls": 0, "receipt_attempts": server.receipts}
    write_json(output / "verification.json", verification)
    print(json.dumps(verification))
    return 0 if verification["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
