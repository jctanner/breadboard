#!/usr/bin/env python3
"""Check actual persisted workflow outcomes, not just the CLI exit status."""
import argparse
import json
from pathlib import Path

from run_plugin_experiments import write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    summary = []
    cases = ["plain-return", "pipeline-errors", "parallel-errors", "metadata-error", "determinism-error", "dynamic-import-error", "agent-text", "agent-schema", "missing-structured", "missing-structured-parallel", "resume", "named-valid", "named-invalid", "extension", "disabled", "child"]
    rejection_text = {"metadata-error": "FIRST statement", "determinism-error": "must be deterministic", "dynamic-import-error": "import() is not available", "extension": '"typescript-only" not found'}
    hashes = set()
    for case in cases:
        root = args.traces / f"workflow-{case}-v1"
        run = json.loads((root / "results.json").read_text())
        assert run["returncode"] == 0, (case, run)
        command = json.loads((root / "command.json").read_text())
        assert run["binary_sha256"] == command["binary_sha256"]
        hashes.add(run["binary_sha256"])
        captures = [json.loads(p.read_text()) for p in sorted((root / "api-captures").glob("*.json"))]
        states = [json.loads(p.read_text()) for p in (root / "config/projects").glob("**/workflows/*.json")]
        if case in rejection_text:
            errors = [r for c in captures for r in c["tool_results"] if r.get("is_error")]
            assert errors and any(rejection_text[case] in str(e) for e in errors), (case, errors)
            assert not states, case
            outcome = {"rejected": True, "message_contains": rejection_text[case]}
        elif case == "disabled":
            assert captures and all("Workflow" not in c["tool_names"] for c in captures)
            assert not states
            outcome = {"workflow_tool_offered": False}
        else:
            assert len(states) == 1, (case, states)
            state = states[0]
            value = state.get("result")
            if case == "missing-structured":
                assert state["status"] == "failed" and "without calling StructuredOutput" in state["error"]
                assert run["agent_requests"] == 2  # initial prose and in-conversation nudge
            else:
                assert state["status"] == "completed" and not state.get("error"), (case, state)
            if case == "plain-return":
                assert value == {"ok": True, "args": {"marker": "input-object"}, "node": "undefined", "require": "undefined", "budgetTotal": None}
            elif case == "pipeline-errors":
                assert value["results"] == [3, 5, None]
                assert value["events"].index("B2") < value["events"].index("A1")
                assert "B3" not in value["events"]
            elif case == "parallel-errors":
                assert value == [7, None, 9]
            elif case == "agent-text":
                assert value == {"value": "WORKFLOW_FIXTURE_FINAL_TEXT"}
            elif case == "agent-schema":
                assert value == {"value": {"ok": True, "marker": "structured"}}
            elif case == "missing-structured-parallel":
                assert value == [None] and run["agent_requests"] == 2
            elif case == "child":
                assert value == {"origin": "project"}
            elif case.startswith("named-"):
                assert value == {"origin": "project" if case == "named-valid" else "user"}
            elif case == "resume":
                calls = [sum(c["agent_request"] and c["resume_round"] == i for c in captures) for i in range(4)]
                assert calls == [2, 0, 0, 1], calls
                assert [c["mock_response"][0].get("name") for c in captures].count("Workflow") == 4
                progress = [p for p in state["workflowProgress"] if p["type"] == "workflow_agent"]
                assert any(p.get("label") == "renamed" and p.get("cached") for p in progress)
            outcome = {"status": state["status"], "result": value, "error": state.get("error"), "agent_count": state["agentCount"]}
            if case == "resume":
                outcome["agent_api_calls_by_round"] = calls
        summary.append({"case": case, "passed": True, "run": str(root), "outcome": outcome, "api_requests": run["api_requests"], "agent_requests": run["agent_requests"]})
    assert len(hashes) == 1, hashes
    write_json(args.output, {"schema_version": 1, "binary_sha256": hashes.pop(), "controls": summary})
    print(f"Verified {len(summary)} workflow controls")


if __name__ == "__main__":
    main()
