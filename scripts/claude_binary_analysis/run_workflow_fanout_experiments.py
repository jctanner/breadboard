#!/usr/bin/env python3
"""Result-driven fan-out probe: one agent's structured result feeds a for-loop
of further agent() calls. Loopback API only; no credentials."""
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
from run_plugin_experiments import commit_fixture_repository, sha256, tree_manifest, write_json

ORGSCAN_SCRIPT = "export const meta={name:\"org-architecture-scan\",description:\"Clone org repos and summarize each\"};const CLONE_SCHEMA={\"type\": \"object\", \"properties\": {\"root\": {\"type\": \"string\"}, \"repos\": {\"type\": \"array\", \"items\": {\"type\": \"object\", \"properties\": {\"name\": {\"type\": \"string\"}, \"path\": {\"type\": \"string\"}}, \"required\": [\"name\", \"path\"], \"additionalProperties\": false}}}, \"required\": [\"root\", \"repos\"], \"additionalProperties\": false};const SCAN_SCHEMA={\"type\": \"object\", \"properties\": {\"repo\": {\"type\": \"string\"}, \"summary\": {\"type\": \"string\"}, \"concerns\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}}, \"required\": [\"repo\", \"summary\"], \"additionalProperties\": false};const clone = await agent(\"ORG_CLONE: run fetch-architecture-context.sh and return every checkout folder it created; copy paths verbatim from the tool output\", {schema: CLONE_SCHEMA, label: \"org-clone\"});const repos = (clone && clone.repos) || [];const summaries = await parallel(repos.map(function (repo) { return function () {  return agent(\"ORG_SCAN:\" + repo.name + \" at \" + repo.path + \": read the checkout and produce an architecture summary\", {schema: SCAN_SCHEMA, label: \"scan:\" + repo.name});}; }));return {root: clone && clone.root, scanned: summaries.filter(Boolean).length, failed: summaries.filter(function (s) { return !s; }).length, summaries: summaries};"
LIST_SCHEMA = {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "string"}}}, "required": ["items"], "additionalProperties": False}
ITEM_SCHEMA = {"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"], "additionalProperties": False}
SCRIPT = (
    'export const meta={name:"fanout-fixture",description:"Result-driven fan-out"};'
    'const list = await agent("FANOUT_LIST", ' + json.dumps({"schema": LIST_SCHEMA}) + ');'
    'const results = [];'
    'for (const item of list.items) {'
    '  results.push(await agent("FANOUT_ITEM:" + item, ' + json.dumps({"schema": ITEM_SCHEMA}) + '));'
    '}'
    'return {count: list.items.length, results: results.map(r => r.value)};'
)


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def call(id: str, name: str, args: dict) -> dict:
    return {"type": "tool_use", "id": id, "name": name, "input": args}


def user_texts(request: dict) -> list[str]:
    return [b.get("text", "") for m in request.get("messages", []) if m.get("role") == "user" for b in (m["content"] if isinstance(m.get("content"), list) else [text(m.get("content", ""))]) if b.get("type") == "text"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass

    def do_POST(self) -> None:
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        s = self.server
        with s.lock:
            s.count += 1
            index = s.count
        texts = user_texts(request)
        joined = " ".join(texts)
        if "ORG_CLONE" in joined:
            role = "clone"
        elif "ORG_SCAN:" in joined:
            role = "scan"
        else:
            role = "list" if "FANOUT_LIST" in joined else "item" if "FANOUT_ITEM" in joined else "controller"
        write_json(s.captures / f"{index:03d}.json", {"request_index": index, "role": role, "model": request.get("model")})
        if role == "controller":
            script = ORGSCAN_SCRIPT if s.case == "orgscan" else SCRIPT
            blocks = [] if any(r.get("tool_use_id") == "fixture_workflow_1" for m in request.get("messages", []) for r in (m.get("content") or [] if isinstance(m.get("content"), list) else []) if isinstance(r, dict)) else [call("fixture_workflow_1", "Workflow", {"script": script})]
            if not blocks:
                blocks = [text("CONTROLLER_DONE")]
        elif role == "clone":
            ran_clone = any(r.get("tool_use_id") == "fixture_clone" for m in request.get("messages", []) for r in (m.get("content") or [] if isinstance(m.get("content"), list) else []) if isinstance(r, dict))
            if not ran_clone:
                blocks = [call("fixture_clone", "Bash", {"command": "fetch-architecture-context.sh --org opendatahub-io --dest .context/org"})]
            else:
                blocks = [call("fixture_clone_out", "StructuredOutput", {"root": ".context/org", "repos": [{"name": "odh-dashboard", "path": ".context/org/odh-dashboard"}, {"name": "model-registry", "path": ".context/org/model-registry"}, {"name": "llama-stack-distribution", "path": ".context/org/llama-stack-distribution"}]})]
        elif role == "scan":
            name = next(t.split("ORG_SCAN:")[1].split(" ")[0] for t in texts if "ORG_SCAN:" in t)
            blocks = [call("fixture_scan_" + name, "StructuredOutput", {"repo": name, "summary": "fixture summary of " + name, "concerns": []})]
        elif role == "list":
            blocks = [call("fixture_list", "StructuredOutput", {"items": ["alpha", "beta", "gamma"]})]
        else:
            item = next(t.split("FANOUT_ITEM:")[1].strip() for t in texts if "FANOUT_ITEM:" in t)
            blocks = [call(f"fixture_item_{item}", "StructuredOutput", {"value": "processed-" + item})]
        respond(self, request, blocks, index)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--case", choices=["fanout", "orgscan"], default="fanout")
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixtures, config = root / "fixtures", root / "config"
    fixtures.mkdir()
    config.mkdir()
    (fixtures / "CLAUDE.md").write_text("FANOUT_FIXTURE_CONTEXT\n")
    write_json(config / "settings.json", {"enableWorkflows": True})
    provenance = commit_fixture_repository(fixtures)
    driver = Path(__file__)
    write_json(root / "manifest.json", {"case": args.case, "binary_sha256": sha256(args.binary.resolve()), "driver_sha256": sha256(driver), "fixture_repository": provenance, "fixture_tree": tree_manifest(fixtures), "script": SCRIPT, "bound_seconds": 60})
    (root / driver.name).write_bytes(driver.read_bytes())
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.captures = root / "api-captures"
    server.captures.mkdir()
    server.count, server.lock, server.case = 0, threading.Lock(), args.case
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "CLAUDE_CONFIG_DIR": str(config), "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1", "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{server.server_port}", "ANTHROPIC_API_KEY": "local-analysis-placeholder-not-a-credential"}
    argv = [str(args.binary.resolve()), "--print", "--verbose", "--output-format", "stream-json", "--debug-file", str(root / "debug.log"), "--permission-mode", "bypassPermissions", "--max-turns", "8", "FANOUT_PROMPT"]
    write_json(root / "command.json", {"argv": argv, "case": args.case})
    started = time.monotonic()
    with (root / "stdout.jsonl").open("wb") as out, (root / "stderr.txt").open("wb") as err:
        proc = subprocess.Popen(argv, cwd=fixtures, env=env, stdout=out, stderr=err, start_new_session=True)
        try:
            code = proc.wait(timeout=50)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, 9)
            proc.wait()
            code = 124
    server.shutdown()
    thread.join()
    server.server_close()
    states = []
    for p in config.rglob("workflows/*.json"):
        try:
            v = json.loads(p.read_text())
            if "status" in v:
                states.append(v)
        except (ValueError, OSError):
            pass
    journals = [{"path": str(p), "entries": [json.loads(line) for line in p.read_text().splitlines() if line.startswith("{")]} for p in config.rglob("journal.jsonl")]
    write_json(root / "results.json", {"case": args.case, "returncode": code, "duration_seconds": time.monotonic() - started, "api_requests": server.count, "workflow_states": states, "journals": journals})
    print(json.dumps({"case": args.case, "returncode": code, "requests": server.count, "statuses": [s.get("status") for s in states], "result": states[-1].get("result") if states else None}))


if __name__ == "__main__":
    main()
