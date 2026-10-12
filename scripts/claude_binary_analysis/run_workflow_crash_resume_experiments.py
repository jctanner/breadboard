#!/usr/bin/env python3
"""Crash-boundary resume probes; fresh config, loopback API, owned processes.

Completes the crash-recovery control for the operational Workflow probes. The
original runner derived its resume handle only from a terminal workflow state
file, which an external SIGKILL never leaves behind. This driver replicates
each crash boundary in phase 1, then derives the resume handle from the
surviving journal and script files and restarts in a fresh process (phase 2).

No real credentials or provider requests are used. API failure injection is
limited to fixture-owned execution. Results must be checked by an outcome
verifier.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_plugin_experiments import commit_fixture_repository, sha256, tree_manifest, write_json
from run_workflow_operations_experiments import SCHEMA, parse_lines, run_phase

CASES = ["crash-during-agent", "crash-before-result", "crash-after-result"]


def journal_restore(config: Path, root: Path, first: dict) -> dict | None:
    """Derive a resume handle from the journal and script left by phase 1."""
    stream = parse_lines(root / "phases" / "1" / "stdout.jsonl")
    init = next((e for e in stream if e.get("subtype") == "init"), None)
    if not init:
        return None
    session_id = init["session_id"]
    journals = list(config.rglob("journal.jsonl"))
    if len(journals) != 1:
        return None
    run_id = journals[0].parent.name
    scripts = list(config.rglob(f"*{run_id}*.js"))
    if len(scripts) != 1:
        return None
    return {"session_id": session_id, "run_id": run_id, "script_path": str(scripts[0])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--case", choices=CASES, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    fixtures, config = root / "fixtures", root / "config"
    fixtures.mkdir()
    config.mkdir()
    (fixtures / "context.txt").write_text("CONTEXT_v1\n")
    (fixtures / "CLAUDE.md").write_text("OPS_INSTRUCTION_OLD\n")
    write_json(config / "settings.json", {"enableWorkflows": True})
    options = {"schema": SCHEMA}
    body = "return await " + 'agent(' + json.dumps("OPS_AGENT_A") + "," + json.dumps(options) + ")" + ";"
    if args.case == "crash-after-result":
        body = ("const a=await " + 'agent(' + json.dumps("OPS_AGENT_A") + "," + json.dumps(options) + ");"
                "const b=await " + 'agent(' + json.dumps("OPS_AGENT_B") + "," + json.dumps(options) + ");return {a,b};")
    script = 'export const meta={name:"operations-fixture",description:"Bounded production control"};' + body
    provenance = commit_fixture_repository(fixtures)
    driver = Path(__file__)
    operations = driver.with_name("run_workflow_operations_experiments.py")
    helper = driver.with_name("mock_api_support.py")
    write_json(root / "manifest.json", {
        "case": args.case,
        "binary_sha256": sha256(args.binary.resolve()),
        "driver_sha256": sha256(driver),
        "operations_runner_sha256": sha256(operations),
        "helper_sha256": sha256(helper),
        "fixture_repository": provenance,
        "fixture_tree": tree_manifest(fixtures),
        "script": script,
        "supervisor_bound_seconds": 45,
        "resume_source": "journal and script files; phase 1 replicates the original crash boundary",
    })
    for name in (driver.name, operations.name, helper.name):
        (root / name).write_bytes(driver.with_name(name).read_bytes())
    first = run_phase(args, root, fixtures, config, script, 1, supervisor_signal="SIGKILL")
    phases = [first]
    restore = journal_restore(config, root, first)
    if restore:
        phases.append(run_phase(args, root, fixtures, config, script, 2, restore))
    write_json(root / "results.json", {"case": args.case, "phases": phases, "journal_restore": restore})
    print(json.dumps({
        "case": args.case,
        "returncodes": [p["returncode"] for p in phases],
        "requests": [p["api_requests"] for p in phases],
        "counters": [p["counter_lines"] for p in phases],
        "statuses": [[s["state"]["status"] for s in p["workflow_states"]] for p in phases],
        "journal_entries": [[e.get("type") for j in p["journals"] for e in j["entries"]] for p in phases],
        "restore": restore,
    }))


if __name__ == "__main__":
    main()
