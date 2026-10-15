#!/usr/bin/env python3
"""Native final-checkpoint control, optionally failing the post-completion turn.

Only a loopback authored API stub is used. No provider credentials/inference.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading

from mock_api_support import respond
from run_plugin_experiments import sha256, write_json

MODEL = "rits/zai-org/glm-5-3"


def tool(identity, name, value):
    return {"type": "tool_use", "id": identity, "name": name, "input": value}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        server = self.server
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        text = "\n".join(message["content"] if isinstance(message["content"], str) else
                         "\n".join(block.get("text", "") for block in message["content"] if block.get("type") == "text")
                         for message in request["messages"] if message["role"] == "user")
        results = {block["tool_use_id"]: block for message in request["messages"]
                   if isinstance(message["content"], list) for block in message["content"]
                   if block.get("type") == "tool_result"}
        if "OUTCOME_CONTROL" in text:
            if "completion_command" not in results:
                blocks = [tool("completion_command", "Bash", {"command": "python3 scripts/strat_pipeline_state.py result"})]
            else:
                value = server.outcome.summary(server.root, server.outcome.verify_completion(server.root, allow_failed=True))
                with server.lock:
                    attempt = server.attempts
                    server.attempts += 1
                # First invent a success hash; actual plugin must deny it.
                if attempt == 0:
                    value = {**value, "receipt_sha256": "f" * 64}
                blocks = [tool("completion_output_" + str(attempt), "StructuredOutput", value)]
            category = "checkpoint"
        else:
            with server.lock:
                launched = server.launched
                server.launched = True
            category = "reporting" if launched else "controller"
            completed = False
            for path in (server.config / "projects").rglob("workflows/wf_*.json"):
                try:
                    value = json.loads(path.read_text())
                    completed |= value.get("status") == "completed" and isinstance(value.get("result"), dict)
                except (OSError, ValueError):
                    pass
            if launched and server.reporting_fault and completed:
                body = {"type": "error", "error": {"type": "invalid_request_error",
                                                    "message": "Authored post-completion reporting fault"}}
                with server.lock:
                    server.count += 1
                    number = server.count
                write_json(server.capture / f"{number:03d}.request.json", request)
                write_json(server.capture / f"{number:03d}.response.json", body)
                payload = json.dumps(body).encode()
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            invocation = {"name": "outcome:outcome"}
            if not launched and server.freshness_fault == "source":
                (server.root / "scripts/freshness-changed.md").write_text("Authored changed source after preparation.\n")
            if launched and completed and server.freshness_fault == "native-replay" and not server.replay_attempted:
                states = [json.loads(p.read_text()) for p in (server.config / "projects").rglob("workflows/wf_*.json")]
                prior = next(value for value in states if value.get("status") == "completed")
                server.replay_attempted = True
                blocks = [tool("workflow_replay", "Workflow", {"name": "outcome:outcome",
                                "resumeFromRunId": prior["runId"]})]
                category = "native-replay"
            else:
                blocks = [{"type": "text", "text": "Completion control finished"}] if launched else [
                    tool("workflow", "Workflow", invocation)]
        with server.lock:
            server.count += 1
            number = server.count
        write_json(server.capture / f"{number:03d}.request.json", request)
        write_json(server.capture / f"{number:03d}.response.json", {"category": category, "content": blocks})
        respond(self, request, blocks, number)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reporting-fault", action="store_true")
    parser.add_argument("--business-fault", action="store_true", help="remove one required report before validation")
    parser.add_argument("--freshness-fault", choices=("source", "native-replay"),
                        help="require the actual pre-launch hook to refuse changed source or native replay")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o700)
    root, config = output / "fixture", output / "config"
    root.mkdir()
    config.mkdir()
    for relative in ("scripts", "workflows", ".fullsend/plugins/strat-pipeline", "tests/outcome", "tests/fixtures/outcome"):
        shutil.copytree(args.candidate / relative, root / relative, symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(args.candidate / "tests/review_composition_support.py", root / "tests/review_composition_support.py")
    setup = subprocess.run(["python3", "tests/outcome/fixture.py", "setup"], cwd=root, capture_output=True)
    (output / "setup.stdout").write_bytes(setup.stdout)
    (output / "setup.stderr").write_bytes(setup.stderr)
    if setup.returncode:
        raise RuntimeError("Fixture setup failed; retained setup.stderr")
    if args.business_fault:
        (root / "artifacts/strat-reviews/STRAT-9602-review-scope.md").unlink()
    spec = importlib.util.spec_from_file_location("outcome_fixture", root / "tests/outcome/fixture.py")
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    import strat_pipeline_outcome as outcome
    write_json(config / "settings.json", {"enableWorkflows": True, "effortLevel": "medium"})
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.root, server.outcome, server.count, server.launched = root, outcome, 0, False
    server.config = config
    server.reporting_fault, server.attempts = args.reporting_fault, 0
    server.freshness_fault = args.freshness_fault
    server.replay_attempted = False
    server.lock = threading.Lock()
    server.capture = output / "api-dumps"
    server.capture.mkdir()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "CLAUDE_CONFIG_DIR": str(config),
           "DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
           "FULLSEND_OUTPUT_DIR": str(root / "output"),
           "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential",
           "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}"}
    env.update({name: MODEL for name in ("ANTHROPIC_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL",
               "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_FABLE_MODEL")})
    argv = [str(args.binary.resolve()), "--print", "--verbose", "--output-format", "stream-json", "--model", MODEL,
            "--effort", "medium", "--dangerously-skip-permissions", "--max-turns", "12", "--disallowed-tools",
            "Edit", "Write", "Agent", "Skill", "--plugin-dir", str(root / ".fullsend/plugins/strat-pipeline"),
            "--plugin-dir", str(root / "tests/fixtures/outcome/plugin"), "/outcome:outcome"]
    write_json(output / "command.json", {"argv": argv, "binary_sha256": sha256(args.binary), "provider_calls": 0,
                                        "reporting_fault": args.reporting_fault, "business_fault": args.business_fault,
                                        "freshness_fault": args.freshness_fault,
                                        "environment_keys": sorted(env)})
    shutil.copyfile(__file__, output / Path(__file__).name)
    try:
        process = subprocess.run(argv, cwd=root, env=env, capture_output=True, timeout=150)
        code, stdout, stderr = process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    (output / "stdout.jsonl").write_bytes(stdout)
    (output / "stderr.txt").write_bytes(stderr)
    shutil.copytree(config / "projects", output / "native-projects")
    if args.freshness_fault:
        requests = [json.loads(path.read_text()) for path in server.capture.glob("*.request.json")]
        responses = [block for request in requests for message in request["messages"]
                     if isinstance(message["content"], list) for block in message["content"]
                     if block.get("type") == "tool_result" and block.get("tool_use_id") ==
                     ("workflow_replay" if args.freshness_fault == "native-replay" else "workflow")]
        refused = any(block.get("is_error") and "S1 freshness check refused launch" in json.dumps(block)
                      for block in responses)
        states = list((output / "native-projects").rglob("workflows/wf_*.json"))
        if args.freshness_fault == "native-replay":
            passed = refused and server.replay_attempted and len(states) == 1 and server.attempts == 2
        else:
            passed = refused and not states and server.attempts == 0 and not (root / "output/agent-result.json").exists()
        verification = {"passed": passed, "freshness_fault": args.freshness_fault, "workflow_states": len(states),
                        "requests": server.count, "provider_calls": 0, "cli_exit": code,
                        "expected": "guard refuses requested launch/replay before executing its agents"}
        write_json(output / "verification.json", verification)
        print(json.dumps(verification))
        return 0 if passed else 1
    if args.business_fault:
        states = list((output / "native-projects").rglob("workflows/wf_*.json"))
        path = next(p for p in states if json.loads(p.read_text()).get("workflowName") == "outcome")
        state = json.loads(path.read_text())
        journal = next((output / "native-projects").rglob(f"subagents/workflows/{state['runId']}/journal.jsonl"))
        observed = outcome.observe(root, path, journal, code, root / "output/agent-result.json")
        write_json(output / "runtime-outcome.json", observed)
        passed = not observed["runtime_verified"] and not observed["business_completed"] and state["status"] == "failed"
        verification = {"passed": passed, "observed": observed, "requests": server.count,
                        "structured_attempts": server.attempts, "provider_calls": 0, "cli_exit": code,
                        "expected": "failed business work must fail the Workflow regardless of CLI exit"}
        write_json(output / "verification.json", verification)
        print(json.dumps(verification))
        return 0 if passed else 1
    observed = fixture.inspect(output, code)
    receipt_before = (root / "tmp/strat-completion.json").read_bytes()
    progress_before = (root / "tmp/strat-progress.json").read_bytes()
    (root / "output/agent-result.json").unlink()
    restored = subprocess.run(["python3", "scripts/strat_pipeline_state.py", "result", "--failed", "workflow"],
                              cwd=root, env=env, capture_output=True, text=True)
    write_json(output / "recovery.json", {"exit_code": restored.returncode, "stdout": restored.stdout,
        "same_receipt": receipt_before == (root / "tmp/strat-completion.json").read_bytes(),
        "same_progress": progress_before == (root / "tmp/strat-progress.json").read_bytes()})
    hooks = [json.loads(line) for line in (root / "tmp/completion-checkpoints/events.jsonl").read_text().splitlines()]
    passed = (observed["runtime_verified"] and observed["retry_work"] is False and server.attempts == 2 and
              any(not event["allowed"] for event in hooks) and any(event["allowed"] for event in hooks) and
              restored.returncode == 0 and receipt_before == (root / "tmp/strat-completion.json").read_bytes() and
              progress_before == (root / "tmp/strat-progress.json").read_bytes() and
              (code != 0 if args.reporting_fault else code == 0))
    verification = {"passed": passed, "observed": observed, "requests": server.count,
                    "structured_attempts": server.attempts, "provider_calls": 0, "cli_exit": code}
    write_json(output / "verification.json", verification)
    print(json.dumps(verification))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
