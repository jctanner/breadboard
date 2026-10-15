#!/usr/bin/env python3
"""Phase 1 check for the workflow-engine POC.

Runs the demo pipeline N times with the workflow-engine provider and asserts:

Per run:
  - pi exits 0 and the --mode json stream parses;
  - the stream contains the deterministic conversation: an assistant message
    with stopReason "toolUse" carrying one `workflow` tool call, a
    tool_execution_end for it (isError false), a final assistant message
    with stopReason "stop", agent_end willRetry=false, agent_settled;
  - every assistant message reports zero usage (no parent inference);
  - the run directory's usage.jsonl holds one record per child (fullsend
    contract shape) and the artifact is complete (every item exactly one
    validated result).

Across runs:
  - the normalized event streams are byte-identical (timestamps, durations
    and the session id removed); with scripted children this includes the
    child-derived content.

Usage:
  python3 check.py --ext /path/to/workflow-engine --runs 3 --out ./check-runs
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

PROMPT = "Run the demo pipeline on: alpha, beta, gamma"
EXPECTED_ITEMS = ["alpha", "beta", "gamma"]
DROP_KEYS = {"timestamp", "durationMs"}


def normalize(value):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in DROP_KEYS:
                continue
            if k == "id" and isinstance(v, str) and len(v) == 36 and v.count("-") == 4:
                out[k] = "<uuid>"
            else:
                out[k] = normalize(v)
        return out
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def run_once(pi: str, ext: Path, run_dir: Path, prompt: str, env_extra: dict | None = None) -> dict:
    run_dir.mkdir(parents=True, exist_ok=False)
    home = run_dir / "home"
    home.mkdir()
    session = run_dir / "session"
    argv = [
        pi, "--print", "--mode", "json", "--no-approve", "--no-extensions",
        "--no-prompt-templates", "--no-themes", "--session-dir", str(session),
        "-e", str(ext), "--model", "workflow-engine/v1", "--tools", "workflow",
        prompt,
    ]
    env = dict(os.environ)
    env["HOME"] = str(home)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(argv, cwd=run_dir, env=env, capture_output=True, text=True, timeout=300)
    (run_dir / "stdout.jsonl").write_text(proc.stdout)
    (run_dir / "stderr.txt").write_text(proc.stderr)
    events = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    return {"returncode": proc.returncode, "events": events, "run_dir": run_dir}


def check_run(result: dict, expect_child_model: str | None) -> list[str]:
    errors = []
    run_dir: Path = result["run_dir"]
    events = result["events"]

    if result["returncode"] != 0:
        errors.append(f"exit code {result['returncode']}")
        return errors

    kinds = [e.get("type") for e in events]
    if kinds[:1] != ["session"]:
        errors.append(f"first event is {kinds[:1]}, expected session header")

    # Tool-call turn.
    tool_msgs = [
        e for e in events
        if e.get("type") == "message_end" and e.get("message", {}).get("role") == "assistant"
        and e["message"].get("stopReason") == "toolUse"
    ]
    if len(tool_msgs) != 1:
        errors.append(f"expected exactly one toolUse assistant message, got {len(tool_msgs)}")
    else:
        calls = [b for b in tool_msgs[0]["message"].get("content", []) if b.get("type") == "toolCall"]
        if len(calls) != 1 or calls[0].get("name") != "workflow":
            errors.append(f"expected one workflow toolCall, got {calls}")
        elif calls[0].get("arguments", {}).get("command") != "run-demo":
            errors.append(f"tool call command {calls[0].get('arguments', {}).get('command')!r} != run-demo")
        elif calls[0].get("arguments", {}).get("input", {}).get("items") != EXPECTED_ITEMS:
            errors.append(f"tool call input {calls[0].get('arguments', {}).get('input')} != items {EXPECTED_ITEMS}")

    tool_ends = [e for e in events if e.get("type") == "tool_execution_end" and e.get("toolName") == "workflow"]
    if len(tool_ends) != 1 or tool_ends[0].get("isError"):
        errors.append(f"expected one successful workflow tool_execution_end, got {tool_ends}")

    # Final turn.
    final_msgs = [
        e for e in events
        if e.get("type") == "message_end" and e.get("message", {}).get("role") == "assistant"
        and e["message"].get("stopReason") == "stop"
    ]
    if len(final_msgs) != 1:
        errors.append(f"expected exactly one final stop assistant message, got {len(final_msgs)}")
    else:
        text = "".join(b.get("text", "") for b in final_msgs[0]["message"].get("content", []) if b.get("type") == "text")
        if "workflow complete: 3/3" not in text:
            errors.append(f"final message missing completion summary: {text[:200]!r}")

    if not any(e.get("type") == "agent_end" and e.get("willRetry") is False for e in events):
        errors.append("no agent_end with willRetry=false")
    if not any(e.get("type") == "agent_settled" for e in events):
        errors.append("no agent_settled")

    # Zero parent usage on every assistant message.
    for e in events:
        msg = e.get("message", {})
        if e.get("type") in ("message_end", "message_update") and msg.get("role") == "assistant":
            u = msg.get("usage") or e.get("usage") or {}
            if any(u.get(k) for k in ("input", "output", "cacheRead", "cacheWrite")):
                errors.append(f"non-zero parent usage: {u}")
                break

    # Usage file: one record per child, contract shape.
    usage_file = run_dir / "workflow-runs"
    usage_files = sorted(usage_file.glob("*/usage.jsonl"))
    if len(usage_files) != 1:
        errors.append(f"expected one run usage.jsonl, found {len(usage_files)}")
    else:
        records = [json.loads(l) for l in usage_files[0].read_text().splitlines() if l.strip()]
        if len(records) != len(EXPECTED_ITEMS):
            errors.append(f"usage.jsonl has {len(records)} records, expected {len(EXPECTED_ITEMS)}")
        for i, rec in enumerate(records):
            if rec.get("seq") != i + 1:
                errors.append(f"usage record {i} seq={rec.get('seq')}")
            if "usage" not in rec or "model" not in rec:
                errors.append(f"usage record {i} missing model/usage: {rec}")
            if expect_child_model and rec.get("model") != expect_child_model:
                errors.append(f"usage record {i} model {rec.get('model')!r} != {expect_child_model!r}")

    # Artifact completeness.
    artifacts = sorted(usage_file.glob("*/artifact.json"))
    if len(artifacts) != 1:
        errors.append(f"expected one artifact.json, found {len(artifacts)}")
    else:
        art = json.loads(artifacts[0].read_text())
        if not art.get("complete") or art.get("classified") != len(EXPECTED_ITEMS) or art.get("failed") != 0:
            errors.append(f"artifact not complete: {json.dumps(art)[:300]}")
        if sorted(r.get("item") for r in art.get("results", [])) != sorted(EXPECTED_ITEMS):
            errors.append(f"artifact items mismatch: {art.get('results')}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pi", default="pi")
    parser.add_argument("--ext", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument("--expect-child-model", default="test-child/echo")
    parser.add_argument("--env", action="append", default=[], help="KEY=VALUE exported to the parent pi process")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    env_extra = dict(kv.split("=", 1) for kv in args.env)

    failures = 0
    normalized_streams = []
    for n in range(1, args.runs + 1):
        result = run_once(args.pi, args.ext, args.out / f"run-{n}", args.prompt, env_extra)
        errors = check_run(result, args.expect_child_model)
        # The per-run scratch directory legitimately appears in cwd, system
        # sections, tool-result paths and the final message; mask it so the
        # comparison isolates engine determinism from run location.
        rundir = str(result["run_dir"].resolve())
        normalized = [json.dumps(normalize(e), sort_keys=True).replace(rundir, "<rundir>") for e in result["events"]]
        normalized_streams.append(normalized)
        status = "PASS" if not errors else "FAIL"
        print(f"run {n}: {status} ({len(result['events'])} events, exit {result['returncode']})")
        for err in errors:
            print(f"  - {err}")
        failures += bool(errors)

    if len({json.dumps(s) for s in normalized_streams}) != 1:
        failures += 1
        print("determinism: FAIL — normalized event streams differ across runs")
        for n, s in enumerate(normalized_streams, 1):
            print(f"  run {n}: {len(s)} events, sha256={__import__('hashlib').sha256(json.dumps(s).encode()).hexdigest()[:16]}")
    else:
        print(f"determinism: PASS — {args.runs}/{args.runs} normalized streams identical")

    print("PHASE1-CHECK:", "PASS" if failures == 0 else "FAIL")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
