#!/usr/bin/env python3
"""Bounded operational Workflow probes; fresh config, loopback API, owned processes.

Each phase snapshots the files used for restoration. API failures and process
signals are injected only into fixture-owned execution; no real credentials or
provider requests are used. Results must be checked by an outcome verifier.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import threading
import time

from mock_api_support import respond
from run_plugin_experiments import commit_fixture_repository, sha256, tree_manifest, write_json
from run_subagent_skill_experiments import strings

CASES = ["replay-fresh", "replay-shared", "replay-reverse", "crash-during-agent", "crash-before-result", "crash-after-result", "journal-truncate", "resume-competing", "cancel-task", "signal-term", "print-ceiling", "concurrency-1", "concurrency-2", "nested-concurrency-1", "nested-concurrency-2", "budget", "budget-nested", "retry-429", "retry-500", "retry-broken", "retry-exhaust", "stall-retry", "stall-exhaust"]
SCHEMA = {"type": "object", "properties": {"marker": {"type": "string"}, "context": {"type": "string"}}, "required": ["marker", "context"], "additionalProperties": False}


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def call(id: str, name: str, args: dict) -> dict:
    return {"type": "tool_use", "id": id, "name": name, "input": args}


def user_texts(request: dict) -> list[str]:
    return [b.get("text", "") for m in request.get("messages", []) if m.get("role") == "user" for b in (m["content"] if isinstance(m.get("content"), list) else [text(m.get("content", ""))]) if b.get("type") == "text"]


def result_blocks(request: dict) -> list[dict]:
    return [b for m in request.get("messages", []) for b in (m.get("content", []) if isinstance(m.get("content"), list) else []) if b.get("type") == "tool_result"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass

    def do_POST(self) -> None:
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        s = self.server
        texts, results = user_texts(request), result_blocks(request)
        role = "nested" if any("OPS_NESTED_SKILL" in v for v in texts) else next(("agent-" + key for key in ("A", "B", "C") if any("OPS_AGENT_" + key in v for v in texts)), "controller")
        with s.lock:
            s.count += 1
            index = s.count
            agent = role != "controller"
            if agent:
                s.active += 1
                s.max_active = max(s.max_active, s.active)
        started = time.monotonic()
        blocks, fault = [], None
        try:
            if role == "controller":
                if not s.launched:
                    s.launched = True
                    value = {"script": s.script}
                    if s.resume:
                        value = {"scriptPath": s.resume["script_path"], "resumeFromRunId": s.resume["run_id"], "script": s.script}
                    blocks = [call(f"fixture_workflow_{s.phase}", "Workflow", value)]
                elif s.case == "cancel-task" and not s.cancelled:
                    receipt = next((v for r in results for _, v in strings(r.get("content")) if "Task ID:" in v), "")
                    match = re.search(r"Task ID: ([\w-]+)", receipt)
                    if match:
                        deadline = time.monotonic() + 3
                        while not s.start_file.exists() and time.monotonic() < deadline and not s.stopping.is_set():
                            s.stopping.wait(.02)
                        s.cancelled = True
                        blocks = [call("fixture_stop", "TaskStop", {"task_id": match.group(1)})]
                    else:
                        blocks = [text("OPS_CONTROLLER_DONE")]
                else:
                    blocks = [text("OPS_CONTROLLER_DONE")]
            else:
                key = role[-1] if role.startswith("agent-") else "A"
                seen = {r.get("tool_use_id") for r in results}
                side_effect = s.case.startswith(("crash-", "retry-", "stall-")) or s.case in ("journal-truncate", "resume-competing")
                after_counter = f"fixture_counter_{key}" in seen
                if s.case == "crash-during-agent" and s.phase == 1 and key == "A":
                    s.boundary.set()
                    s.stopping.wait(10)
                if s.case == "crash-before-result" and s.phase == 1 and after_counter:
                    s.boundary.set()
                    s.stopping.wait(10)
                if s.case == "crash-after-result" and s.phase == 1 and key == "B":
                    s.boundary.set()
                    s.stopping.wait(10)
                with s.lock:
                    first_fault = after_counter and not s.faulted
                    if first_fault:
                        s.faulted = True
                if after_counter and s.case in ("retry-429", "retry-500", "retry-broken", "retry-exhaust") and (first_fault or s.case == "retry-exhaust"):
                    fault = s.case
                if after_counter and s.case in ("stall-retry", "stall-exhaust") and (first_fault or s.case == "stall-exhaust"):
                    fault = "delayed-stall"
                    s.stopping.wait(1.2)
                if fault and fault.startswith("retry-"):
                    blocks = []
                elif s.case in ("cancel-task", "signal-term", "print-ceiling") and "fixture_sleep" not in seen:
                    command = f"printf '%s\\n' $$ > {shlex.quote(str(s.start_file))}; sleep 2; printf '%s\\n' LATE_WRITE > {shlex.quote(str(s.late_file))}"
                    blocks = [call("fixture_sleep", "Bash", {"command": command})]
                elif s.case == "budget-nested" and role.startswith("agent-") and "fixture_nested_skill" not in seen:
                    blocks = [call("fixture_nested_skill", "Skill", {"skill": "operations-nested"})]
                elif side_effect and not after_counter:
                    command = f"printf '%s\\n' {key} >> {shlex.quote(str(s.counter))}"
                    blocks = [call(f"fixture_counter_{key}", "Bash", {"command": command})]
                elif s.case in ("replay-fresh", "replay-shared") and "fixture_context" not in seen:
                    blocks = [call("fixture_context", "Read", {"file_path": str(s.context_file)})]
                else:
                    if "concurrency" in s.case or s.case == "replay-reverse":
                        delay = .25 if key == ("A" if s.phase == 1 else "B") else .1
                        s.stopping.wait(delay)
                    context = "CONTEXT_v2" if any("CONTEXT_v2" in v for r in results for _, v in strings(r.get("content"))) else "CONTEXT_v1" if any("CONTEXT_v1" in v for r in results for _, v in strings(r.get("content"))) else "none"
                    value = {"marker": "OPS_RESULT_" + key, "context": context}
                    structured = any(t["name"] == "StructuredOutput" for t in request.get("tools", []))
                    blocks = [call(f"fixture_output_{key}", "StructuredOutput", value)] if structured else [text(json.dumps(value))]
            retained = []
            for path, value in strings(request.get("messages", [])):
                if any(marker in value for marker in ("OPS_AGENT_", "OPS_NESTED", "OPS_INSTRUCTION", "OPS_SKILL", "CONTEXT_v")):
                    retained.append({"path": path, "lines": [line[:1200] for line in value.splitlines() if any(marker in line for marker in ("OPS_AGENT_", "OPS_NESTED", "OPS_INSTRUCTION", "OPS_SKILL", "CONTEXT_v"))]})
            write_json(s.captures / f"{index:03d}.json", {"request_index": index, "role": role, "started_monotonic": started, "responded_monotonic": time.monotonic(), "fault": fault, "message_sha256": __import__('hashlib').sha256(json.dumps(request.get('messages'),sort_keys=True).encode()).hexdigest(), "stream": request.get('stream'), "fixture_excerpts": retained, "fixture_tool_results": [r for r in results if r.get('tool_use_id','').startswith('fixture_')], "mock_response": blocks, "tools": [t['name'] for t in request.get('tools',[])]})
            if fault in ("retry-429", "retry-500", "retry-exhaust"):
                status = 429 if fault == "retry-429" else 500
                payload = json.dumps({"type": "error", "error": {"type": "rate_limit_error" if status == 429 else "api_error", "message": "OPS_INJECTED_FAILURE"}}).encode()
                self.send_response(status)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Content-Type", "application/json")
                self.send_header("Retry-After", "0")
                self.end_headers()
                self.wfile.write(payload)
            elif fault == "retry-broken":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Connection", "close")
                self.end_headers()
                partial = {"type": "message_start", "message": {"id": "msg_ops_broken", "type": "message", "role": "assistant", "model": request.get('model'), "content": [], "stop_reason": None, "usage": {"input_tokens": 10, "output_tokens": 0}}}
                self.wfile.write(f"event: message_start\ndata: {json.dumps(partial)}\n\n".encode())
                self.wfile.flush()
                self.close_connection = True
            else:
                usage = {"input_tokens": 10, "output_tokens": 50000 if s.case in ("budget", "budget-nested") and role != 'controller' and not any(b.get('type') == 'tool_use' and b.get('name') != 'StructuredOutput' for b in blocks) else 10}
                respond(self, request, blocks, index, usage=usage)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            if agent:
                with s.lock:
                    s.active -= 1


def snapshots(config: Path) -> list[dict]:
    results = []
    for p in config.rglob('workflows/*.json'):
        try: value = json.loads(p.read_text())
        except (ValueError, OSError): continue
        if 'status' in value:
            results.append({'path': str(p), 'state': value})
    return results


def parse_lines(path: Path) -> list[dict]:
    records = []
    for line in path.read_text().splitlines():
        if not line.startswith('{'):
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            records.append({'truncated': line})
    return records


def run_phase(args, root: Path, fixtures: Path, config: Path, script: str, phase: int, resume: dict | None = None, *, supervisor_signal: str | None = None) -> dict:
    output = root / 'phases' / str(phase)
    output.mkdir(parents=True, exist_ok=False)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.captures = output / 'api-captures'
    server.captures.mkdir()
    server.case, server.phase, server.resume, server.script = args.case, phase, resume, script
    server.counter, server.context_file = fixtures / 'counter.txt', fixtures / 'context.txt'
    server.start_file, server.late_file = fixtures / 'started.pid', fixtures / 'late.txt'
    server.launched, server.cancelled, server.faulted = False, False, False
    server.count, server.active, server.max_active = 0, 0, 0
    server.lock, server.boundary, server.stopping = threading.Lock(), threading.Event(), threading.Event()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = {'PATH': os.environ.get('PATH','/usr/bin:/bin'), 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'CLAUDE_CONFIG_DIR': str(config), 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1', 'DISABLE_AUTOUPDATER': '1', 'ANTHROPIC_BASE_URL': f'http://127.0.0.1:{server.server_port}', 'ANTHROPIC_API_KEY': 'local-analysis-placeholder-not-a-credential', 'CLAUDE_CODE_MAX_RETRIES': '1', 'CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS': '2' if args.case.endswith('-2') or args.case == 'replay-reverse' else '1'}
    if args.case == 'print-ceiling': env['CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS'] = '100'
    argv = [str(args.binary.resolve()), '--print', '--verbose', '--output-format', 'stream-json', '--debug-file', str(output / 'debug.log'), '--permission-mode', 'bypassPermissions', '--max-turns', '8', f'OPS_CONTROLLER_PHASE_{phase}']
    if resume: argv[1:1] = ['--resume', resume['session_id']]
    if args.case in ('budget','budget-nested'): argv[1:1] = ['--max-budget-usd', '.01']
    write_json(output / 'command.json', {'argv': argv, 'environment_keys': sorted(env), 'controls': {k:v for k,v in env.items() if k in ('CLAUDE_CODE_MAX_RETRIES','CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS','CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS')}, 'phase': phase, 'resume': resume, 'supervisor_signal': supervisor_signal})
    started = time.monotonic()
    signal_sent = None
    with (output / 'stdout.jsonl').open('wb') as out, (output / 'stderr.txt').open('wb') as err:
        proc = subprocess.Popen(argv, cwd=fixtures, env=env, stdout=out, stderr=err, start_new_session=True)
        try:
            if supervisor_signal:
                deadline = time.monotonic() + 15
                while proc.poll() is None and time.monotonic() < deadline:
                    ready = server.start_file.exists() if supervisor_signal == 'SIGTERM' else server.boundary.is_set()
                    if ready:
                        sig = signal.SIGTERM if supervisor_signal == 'SIGTERM' else signal.SIGKILL
                        os.kill(proc.pid, sig)
                        signal_sent = {'name': supervisor_signal, 'pid': proc.pid, 'at_monotonic': time.monotonic()}
                        server.stopping.set()
                        break
                    server.stopping.wait(.02)
            code = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            code = 124
        finally:
            server.stopping.set()
    # Let a fixture shell's scheduled late write become observable after logical
    # cancellation; then clean up only a verified fixture-owned surviving PID.
    if args.case in ('cancel-task','signal-term','print-ceiling'):
        time.sleep(2.3)
        if server.start_file.exists():
            pid_text = server.start_file.read_text().strip()
            if pid_text.isdigit():
                pid = int(pid_text)
                try:
                    cwd = Path(f'/proc/{pid}/cwd').resolve(strict=True)
                    if cwd == fixtures.resolve(): os.kill(pid, signal.SIGKILL)
                except (ProcessLookupError, FileNotFoundError, PermissionError): pass
    server.shutdown()
    thread.join()
    server.server_close()
    stream = parse_lines(output / 'stdout.jsonl')
    init = next((e for e in stream if e.get('subtype') == 'init'), None)
    states = snapshots(config)
    journals = [{'path': str(p), 'sha256': sha256(p), 'entries': parse_lines(p)} for p in config.rglob('journal.jsonl')]
    restore = None
    if init and states:
        state = states[-1]['state']
        restore = {'session_id': init['session_id'], 'run_id': state['workflowRunId'] if 'workflowRunId' in state else state.get('runId'), 'script_path': state.get('scriptPath')}
        if not restore['run_id']:
            restore['run_id'] = Path(states[-1]['path']).stem
        if not restore['script_path']:
            restore['script_path'] = str(next(config.rglob(f"*{restore['run_id']}*.js")))
    shutil.copytree(config, output / 'config-snapshot')
    result = {'returncode': code, 'duration_seconds': time.monotonic() - started, 'api_requests': server.count, 'max_active_agent_requests': server.max_active, 'signal_sent': signal_sent, 'restore': restore, 'workflow_states': states, 'journals': journals, 'counter_lines': server.counter.read_text().splitlines() if server.counter.exists() else [], 'late_write': server.late_file.exists(), 'started_shell': server.start_file.exists(), 'terminal_results': [e for e in stream if e.get('type') == 'result']}
    write_json(output / 'results.json', result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--case', choices=CASES, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixtures, config = root / 'fixtures', root / 'config'
    fixtures.mkdir()
    config.mkdir()
    (fixtures / 'context.txt').write_text('CONTEXT_v1\n')
    (fixtures / 'CLAUDE.md').write_text('OPS_INSTRUCTION_OLD\n')
    write_json(config / 'settings.json', {'enableWorkflows': True})
    if args.case == 'budget-nested':
        skill = fixtures / '.claude/skills/operations-nested/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('---\nname: operations-nested\ndescription: Nested budget fixture\ncontext: fork\n---\n\nOPS_NESTED_SKILL\nReturn the authored fixture result.\n')
    options = {'schema': SCHEMA}
    if args.case.startswith('stall-'): options['stallMs'] = 150
    def agent(key: str) -> str:
        return 'agent(' + json.dumps('OPS_AGENT_' + key) + ',' + json.dumps(options) + ')'
    body = 'return await ' + agent('A') + ';'
    if args.case in ('crash-after-result','journal-truncate','resume-competing'):
        body = 'const a=await ' + agent('A') + ';const b=await ' + agent('B') + ';return {a,b};'
    if args.case in ('cancel-task','signal-term','print-ceiling','budget','replay-reverse') or args.case.startswith('concurrency-'):
        body = 'return await parallel([' + ','.join('()=>'+agent(key) for key in ('A','B','C')) + ']);'
    if args.case.startswith('nested-concurrency-'):
        nested = fixtures / '.claude/workflows/nested.js'
        nested.parent.mkdir(parents=True)
        nested.write_text('export const meta={name:"operations-nested",description:"Shared concurrency fixture"};return await parallel([' + ','.join('()=>'+agent(k) for k in ('B','C')) + ']);')
        body = 'return await parallel([()=>'+agent('A')+',()=>workflow("operations-nested",{})]);'
    script = 'export const meta={name:"operations-fixture",description:"Bounded production control"};' + body
    provenance = commit_fixture_repository(fixtures)
    write_json(root / 'manifest.json', {'case': args.case, 'binary_sha256': sha256(args.binary.resolve()), 'runner_sha256': sha256(Path(__file__)), 'helper_sha256': sha256(Path(__file__).with_name('mock_api_support.py')), 'fixture_repository': provenance, 'fixture_tree': tree_manifest(fixtures), 'script': script, 'supervisor_bound_seconds': 45})
    for name in (Path(__file__).name,'mock_api_support.py'): (root/name).write_bytes(Path(__file__).with_name(name).read_bytes())
    sig = 'SIGKILL' if args.case.startswith('crash-') else 'SIGTERM' if args.case == 'signal-term' else None
    first = run_phase(args,root,fixtures,config,script,1,supervisor_signal=sig)
    phases = [first]
    if args.case.startswith(('replay-','crash-')) or args.case in ('journal-truncate','resume-competing'):
        if first['restore']:
            if args.case == 'replay-shared':
                (fixtures/'context.txt').write_text('CONTEXT_v2\n')
                (fixtures/'CLAUDE.md').write_text('OPS_INSTRUCTION_NEW\n')
                skill = fixtures/'.claude/skills/new-fixture/SKILL.md'
                skill.parent.mkdir(parents=True)
                skill.write_text('---\nname: new-fixture\ndescription: OPS_SKILL_NEW\n---\nNew fixture skill.\n')
            if args.case == 'journal-truncate' and first['journals']:
                p=Path(first['journals'][0]['path'])
                lines=p.read_bytes().splitlines(keepends=True)
                lines[-1]=lines[-1][:max(1,len(lines[-1])//2)]
                p.write_bytes(b''.join(lines))
            if args.case == 'resume-competing':
                script=script.replace('OPS_AGENT_B','OPS_AGENT_C')
                results={}
                def launch(phase): results[phase]=run_phase(args,root,fixtures,config,script,phase,first['restore'])
                threads=[threading.Thread(target=launch,args=(p,)) for p in (2,3)]
                for thread in threads: thread.start()
                for thread in threads: thread.join()
                phases.extend(results[p] for p in (2,3))
            else:
                phases.append(run_phase(args,root,fixtures,config,script,2,first['restore']))
    write_json(root/'results.json',{'case':args.case,'phases':phases})
    print(json.dumps({'case':args.case,'returncodes':[p['returncode'] for p in phases],'requests':[p['api_requests'] for p in phases],'counters':[p['counter_lines'] for p in phases],'statuses':[[s['state']['status'] for s in p['workflow_states']] for p in phases]}))


if __name__ == '__main__': main()
