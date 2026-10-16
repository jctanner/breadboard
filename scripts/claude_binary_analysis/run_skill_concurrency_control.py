#!/usr/bin/env python3
"""Measure forked Skill overlap using a credential-free loopback response server."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import threading
import time

from mock_api_support import respond
from run_plugin_experiments import commit_fixture_repository, sha256, write_json
from run_workflow_handoff_experiments import direct_texts, text, tool

RECEIVER = "SKILL_CONCURRENCY_RECEIVER"
CONTROLLER = "SKILL_CONCURRENCY_CONTROLLER"
LEAF = "SKILL_CONCURRENCY_LEAF_"
SCHEMA = {"type": "object", "properties": {"done": {"type": "boolean"}},
          "required": ["done"], "additionalProperties": False}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        s = self.server
        if self.path.endswith("/count_tokens"):
            body = json.dumps({"input_tokens": 10}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        texts = direct_texts(req)
        leaves = [i for i in range(4) if any(LEAF + str(i) in t for t in texts)]
        receivers = [i for i in range(4) if any(RECEIVER + "_" + str(i) in t for t in texts)]
        role = ("leaf" if leaves else "receiver"
                if s.route == "cli" or any(RECEIVER in t for t in texts) else "controller")
        results = [b for m in req.get("messages", [])
                   for b in (m["content"] if isinstance(m["content"], list) else [])
                   if b.get("type") == "tool_result"]
        names = [t["name"] for t in req.get("tools", [])]
        started = time.monotonic()
        with s.lock:
            s.count += 1
            index = s.count
            if role == "leaf":
                s.active += 1
                s.max_active = max(s.max_active, s.active)
        if role == "controller":
            if not any(b.get("tool_use_id") == "fixture_workflow" for b in results):
                options = json.dumps({"schema": SCHEMA})
                if s.layout == "same-receiver":
                    body = f"return await agent({json.dumps(RECEIVER)}, {options});"
                else:
                    calls = [f"()=>agent({json.dumps(RECEIVER+'_'+str(i))}, {options})" for i in range(4)]
                    body = "return await parallel([" + ",".join(calls) + "]);"
                script = 'export const meta={name:"skill-concurrency",description:"Local dispatch control"};' + body
                blocks = [tool("fixture_workflow", "Workflow", {"script": script})]
            else:
                blocks = [text("SKILL_CONCURRENCY_CONTROLLER_DONE")]
        elif role == "receiver":
            returned = {b.get("tool_use_id") for b in results}
            targets = receivers if s.layout == "separate-receivers" else range(4)
            pending = [i for i in targets if "fixture_skill_"+str(i) not in returned]
            if pending:
                blocks = [tool("fixture_skill_"+str(i), "Skill", {"skill":"concurrency-leaf-"+str(i)})
                          for i in pending]
            else:
                blocks = ([tool("fixture_receiver_output", "StructuredOutput", {"done":True})]
                          if "StructuredOutput" in names else [text("RECEIVER_DONE")])
        else:
            time.sleep(1.0)
            blocks = [text(LEAF+str(leaves[0])+"_DONE")]
        respond(self, req, blocks, index)
        finished = time.monotonic()
        with s.lock:
            if role == "leaf":
                s.active -= 1
            s.events.append({"index":index, "role":role, "leaves":leaves,
                             "receivers":receivers, "started":started, "finished":finished,
                             "receiver_prompt_seen":any(RECEIVER in t for t in texts),
                             "tool_names":names, "mock_response":blocks,
                             "returned_skill_ids":[b.get("tool_use_id") for b in results
                                                   if b.get("tool_use_id", "").startswith("fixture_skill_")]})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--layout", choices=["same-receiver", "separate-receivers"], required=True)
    parser.add_argument("--route", choices=["workflow", "cli"], default="workflow")
    args = parser.parse_args()
    if args.route == "cli" and args.layout != "same-receiver":
        parser.error("The plain CLI control uses --layout same-receiver")
    binary, output = args.binary.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixtures, config = output/"fixtures", output/"config"
    fixtures.mkdir()
    config.mkdir()
    for i in range(4):
        skill = fixtures/".claude/skills"/f"concurrency-leaf-{i}"/"SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(f"---\nname: concurrency-leaf-{i}\ndescription: Isolated local dispatch fixture\n"
                         f"context: fork\nagent: concurrency-reader\n---\n\n{LEAF}{i}\nReturn a text assessment.\n")
    agent = fixtures/".claude/agents/concurrency-reader.md"
    agent.parent.mkdir(parents=True)
    agent.write_text("---\nname: concurrency-reader\ndescription: Local narrow fixture reader\ntools: Read\n---\nReturn prose only.\n")
    review = fixtures/".claude/skills/concurrency-review/SKILL.md"
    review.parent.mkdir(parents=True)
    review.write_text("---\nname: concurrency-review\ndescription: Local review dispatch fixture\n---\n\n"
                      +RECEIVER+"\nInvoke all four concurrency-leaf skills together.\n")
    commit = commit_fixture_repository(fixtures)
    write_json(config/"settings.json", {"enableWorkflows":args.route == "workflow"})
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.route = args.route
    server.layout, server.count, server.active, server.max_active = args.layout, 0, 0, 0
    server.lock, server.events = threading.Lock(), []
    env = {"PATH":os.environ.get("PATH", "/usr/bin:/bin"), "LANG":"C.UTF-8", "LC_ALL":"C.UTF-8",
           "CLAUDE_CONFIG_DIR":str(config), "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC":"1",
           "DISABLE_AUTOUPDATER":"1", "CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS":"5",
           "ANTHROPIC_BASE_URL":f"http://127.0.0.1:{server.server_port}",
           "ANTHROPIC_API_KEY":"local-concurrency-fixture-not-a-credential"}
    argv = [str(binary), "--print", "--verbose", "--output-format", "stream-json",
            "--debug-file", str(output/"debug.log"), "--permission-mode", "bypassPermissions",
            "--max-turns", "6", "/concurrency-review" if args.route == "cli" else CONTROLLER]
    write_json(output/"command.json", {"argv":argv, "layout":args.layout, "route":args.route,
               "environment_keys":sorted(env),
               "binary_sha256":sha256(binary), "runner_sha256":sha256(Path(__file__)),
               "mock_helper_sha256":sha256(Path(__file__).with_name("mock_api_support.py")),
               "fixture_repository":commit, "real_provider_calls":0})
    source = output/"runner-source"
    source.mkdir()
    for name in [Path(__file__).name, "mock_api_support.py", "run_plugin_experiments.py",
                 "run_workflow_handoff_experiments.py"]:
        (source/name).write_bytes(Path(__file__).with_name(name).read_bytes())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(argv, cwd=fixtures, env=env, capture_output=True, timeout=45)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    (output/"stdout.jsonl").write_bytes(stdout)
    (output/"stderr.txt").write_bytes(stderr)
    write_json(output/"events.json", sorted(server.events, key=lambda r:r["index"]))
    returned = {tool_id for event in server.events for tool_id in event["returned_skill_ids"]}
    leaves = [r for r in server.events if r["role"]=="leaf"]
    expected = 1 if args.layout=="same-receiver" else 4
    passed = (code==0 and len(leaves)==4 and len(returned)==4 and server.max_active==expected)
    prompt_seen = any(r["role"]=="receiver" and r["receiver_prompt_seen"] for r in server.events)
    passed = passed and prompt_seen
    summary = {"passed":passed, "layout":args.layout, "route":args.route,
               "receiver_prompt_seen":prompt_seen, "exit":code, "requests":server.count,
               "leaf_requests":len(leaves), "returned_skills":len(returned),
               "max_concurrent_leaf_requests":server.max_active, "real_provider_calls":0}
    write_json(output/"results.json", summary)
    print(json.dumps(summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
