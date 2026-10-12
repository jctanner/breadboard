#!/usr/bin/env python3
"""Verify handoff markers at child, Skill-result and receiving-model boundaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_plugin_experiments import sha256, write_json
from run_subagent_skill_experiments import strings
from run_workflow_handoff_experiments import ASSESSMENT, DISSENT, SCHEMA, TARGET


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    controls = []
    for route in ("cli", "workflow"):
        for schema in (False, True):
            for completion in ("direct", "fork"):
                for mode in (("prose", "structured", "mixed", "earlier-prose") if schema else ("prose",)):
                    key = f"{route}-{'schema' if schema else 'text'}-{completion}-{mode}"
                    version = "v2" if key in {"workflow-schema-fork-structured", "workflow-schema-fork-prose", "cli-schema-fork-structured"} else "v1"
                    root = args.traces / f"handoff-{key}-{version}"
                    command = json.loads((root / "command.json").read_text())
                    run = json.loads((root / "results.json").read_text())
                    assert run["returncode"] == 0
                    assert sha256(root / "run_workflow_handoff_experiments.py") == command["runner_sha256"]
                    assert sha256(root / "mock_api_support.py") == command["helper_sha256"]
                    for file in command["fixture_tree"]["files"]:
                        assert sha256(Path(command["fixture_tree"]["root"]) / file["path"]) == file["sha256"]
                    cs = [json.loads(p.read_text()) for p in sorted((root / "api-captures").glob("*.json"))]
                    receivers = [c for c in cs if c["role"] == "receiver"]
                    specialists = [c for c in cs if c["role"] == "specialist"]
                    assert receivers
                    assert all((c["structured_schema"] == SCHEMA) == schema for c in receivers)
                    delivery = None
                    if completion == "fork":
                        assert specialists
                        assert all((c["structured_schema"] == SCHEMA) == schema for c in specialists)
                        assert any(TARGET in v for c in specialists for e in c["marker_excerpts"] for v in e["lines"])
                        result = next(r for c in receivers for r in c["fixture_tool_results"] if r["tool_use_id"] == "fixture_skill")
                        assert not result.get("is_error")
                        returned = "\n".join(v for _, v in strings(result["content"]))
                        delivery = {m: m in returned for m in (ASSESSMENT, DISSENT, TARGET)}
                        expected = mode == "prose"
                        assert all(present == expected for present in delivery.values()), (key, returned)
                        assert ("Skill execution completed" in returned) == (not expected)
                        assert any(ASSESSMENT in v for c in specialists for _, v in strings(c["mock_response"]))
                        assert any(DISSENT in v for c in specialists for _, v in strings(c["mock_response"]))
                    else:
                        assert not specialists
                    stream = [json.loads(l) for l in (root / "stdout.jsonl").read_text().splitlines() if l.startswith("{")]
                    finals = [c for c in stream if c.get("type") == "result"]
                    assert finals
                    outcome = {"cli_subtype": finals[-1]["subtype"], "structured_output": finals[-1].get("structured_output")}
                    if route == "workflow":
                        states = []
                        for f in (root / "config").rglob("workflows/*.json"):
                            state = json.loads(f.read_text())
                            if "status" in state: states.append(state)
                        assert len(states) == 1
                        state = states[0]
                        expected_failed = schema and completion == "direct" and mode == "prose"
                        assert state["status"] == ("failed" if expected_failed else "completed")
                        if expected_failed: assert "without calling StructuredOutput" in state["error"]
                        outcome = {"status": state["status"], "result": state.get("result"), "error": state.get("error")}
                    elif schema and completion == "direct" and mode == "prose":
                        # CLI success is not evidence of schema output: this
                        # negative fixture is success without structured_output.
                        assert outcome["structured_output"] is None
                    elif schema:
                        assert isinstance(outcome["structured_output"], dict)
                    controls.append({"case": key, "passed": True, "run": str(root), "runner_sha256": command["runner_sha256"], "fixture_tree_sha256": command["fixture_tree"]["tree_sha256"], "api_requests": len(cs), "specialist_schema_inherited": bool(specialists and specialists[0]["structured_schema"]), "markers_delivered_in_skill_result_and_receiving_request": delivery, "specialist_structured_instructions": specialists[0]["structured_instruction_excerpts"] if specialists else [], "outcome": outcome})
    assert len(controls) == 20
    root = args.traces / 'handoff-workflow-schema-fork-reader-v1'
    command = json.loads((root / 'command.json').read_text())
    assert sha256(root / 'run_workflow_handoff_experiments.py') == command['runner_sha256']
    for file in command['fixture_tree']['files']:
        assert sha256(Path(command['fixture_tree']['root']) / file['path']) == file['sha256']
    cs = [json.loads(p.read_text()) for p in sorted((root / 'api-captures').glob('*.json'))]
    leaf = next(c for c in cs if c['role'] == 'specialist')
    assert leaf['tools'] == ['Read'] and leaf['structured_schema'] is None
    returned = next(r for c in cs if c['role'] == 'receiver' for r in c['fixture_tool_results'] if r['tool_use_id'] == 'fixture_skill')
    assert all(marker in json.dumps(returned['content']) for marker in (ASSESSMENT, DISSENT, TARGET))
    assert all(c['structured_schema'] == SCHEMA for c in cs if c['role'] == 'receiver')
    states = [json.loads(p.read_text()) for p in (root / 'config').rglob('workflows/*.json')]
    state = next(s for s in states if 'status' in s)
    assert state['status'] == 'completed' and state['result']['assessment'].endswith('True')
    controls.append({'case': 'workflow-schema-fork-reader', 'passed': True, 'run': str(root), 'runner_sha256': command['runner_sha256'], 'child_tools': leaf['tools'], 'outer_schema_preserved': True, 'markers_delivered': True, 'outcome': {'status': state['status'], 'result': state['result']}})
    write_json(args.output, {"schema_version": 1, "controls": controls})
    print("Verified 20 handoff matrix cases and the narrowed-agent workaround")


if __name__ == "__main__": main()
