#!/usr/bin/env python3
"""Check persisted outcomes of the operational Workflow probes.

Verifies the twenty-three original operations cases plus the three
crash-resume completions against their recorded journals, counters,
workflow states, API captures and terminal results. CLI exit status alone
is not sufficient verification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_plugin_experiments import write_json
from run_workflow_operations_experiments import parse_lines

PINNED_BINARY_SHA256 = "24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de"
RESUME_CASES = {"crash-during-agent", "crash-before-result", "crash-after-result"}
NETWORK_CASES = {"rate-limit-exhaust", "conn-reset", "spend-limit-429", "overloaded-529"}
NOTIFY_CASE = "notify-fault"


def journal_types(phase: dict) -> list:
    return [e.get("type") for j in phase["journals"] for e in j["entries"]]


def journal_entries(phase: dict) -> list:
    return [e for j in phase["journals"] for e in j["entries"]]


def captures(root: Path, phase: int) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((root / "phases" / str(phase) / "api-captures").glob("*.json"))]


def stdout_events(root: Path, phase: int) -> list[dict]:
    return parse_lines(root / "phases" / str(phase) / "stdout.jsonl")


def statuses(phase: dict) -> list:
    return [s["state"]["status"] for s in phase["workflow_states"]]


def result_event(phase: dict) -> dict:
    events = phase["terminal_results"]
    assert events, "no terminal result event"
    return events[-1]


def check_base(case: str, root: Path, phase_count: int) -> list[dict]:
    run = json.loads((root / "results.json").read_text())
    assert run["case"] == case, (case, run["case"])
    phases = run["phases"]
    assert len(phases) == phase_count, (case, len(phases))
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["binary_sha256"] == PINNED_BINARY_SHA256, (case, manifest["binary_sha256"])
    if case in RESUME_CASES:
        assert manifest.get("driver_sha256"), case
        assert run.get("journal_restore"), (case, "no journal-derived resume handle")
    return phases


def outcome(case: str, root: Path, phases: list[dict]) -> dict:
    p1 = phases[0]
    if case == "replay-fresh":
        assert p1["returncode"] == 0 and statuses(p1) == ["completed"], case
        assert journal_types(p1) == ["launched", "started", "result"], case
        p2 = phases[1]
        assert p2["returncode"] == 0 and p2["max_active_agent_requests"] == 0, case
        assert journal_types(p2) == journal_types(p1), case
        return {"replayed_agent_requests": 0, "cached_result_reused": True}
    if case == "replay-shared":
        assert p1["returncode"] == 0 and statuses(p1) == ["completed"], case
        p2 = phases[1]
        assert p2["returncode"] == 0 and p2["max_active_agent_requests"] == 0, case
        assert journal_types(p2) == journal_types(p1), case
        results = [e.get("result") for e in journal_entries(p2) if e.get("type") == "result"]
        assert results == [{"marker": "OPS_RESULT_A", "context": "CONTEXT_v1"}], (case, results)
        assert (root / "fixtures" / "context.txt").read_text().strip() == "CONTEXT_v2", case
        assert (root / "fixtures" / "CLAUDE.md").read_text().strip() == "OPS_INSTRUCTION_NEW", case
        assert (root / "fixtures" / ".claude" / "skills" / "new-fixture" / "SKILL.md").exists(), case
        return {"changed_shared_state_detected": False, "stale_context_returned": "CONTEXT_v1", "replayed_agent_requests": 0}
    if case == "replay-reverse":
        assert p1["returncode"] == 0 and statuses(p1) == ["completed"], case
        assert p1["max_active_agent_requests"] == 2, case
        assert journal_types(p1) == ["launched", "started", "started", "result", "started", "result", "result"], case
        p2 = phases[1]
        assert p2["returncode"] == 0 and p2["max_active_agent_requests"] == 0, case
        assert journal_types(p2) == journal_types(p1), case
        return {"journal_order_diverges_from_response_order": True, "concurrent_completions_replayed": True, "replayed_agent_requests": 0}
    if case == "crash-during-agent":
        assert p1["returncode"] == -9 and p1["signal_sent"]["name"] == "SIGKILL", case
        assert journal_types(p1) == ["launched", "started"] and p1["counter_lines"] == [], case
        p2 = phases[1]
        assert p2["returncode"] == 0 and statuses(p2) == ["completed"], case
        assert journal_types(p2) == ["launched", "started", "started", "result"], case
        started = [e["agentId"] for e in journal_entries(p2) if e.get("type") == "started"]
        assert len(set(started)) == 2, (case, started)
        assert p2["counter_lines"] == ["A"], case
        return {"crash_boundary": "during first agent request", "resumed": True, "side_effect_executions": 1}
    if case == "crash-before-result":
        assert p1["returncode"] == -9 and p1["signal_sent"]["name"] == "SIGKILL", case
        assert journal_types(p1) == ["launched", "started"] and p1["counter_lines"] == ["A"], case
        p2 = phases[1]
        assert p2["returncode"] == 0 and statuses(p2) == ["completed"], case
        assert journal_types(p2) == ["launched", "started", "started", "result"], case
        assert p2["counter_lines"] == ["A", "A"], case
        return {"crash_boundary": "after side effect, before result journaling", "resumed": True, "side_effect_executions": 2, "side_effect_duplicated": True}
    if case == "crash-after-result":
        assert p1["returncode"] == -9 and p1["signal_sent"]["name"] == "SIGKILL", case
        assert journal_types(p1) == ["launched", "started", "result", "started"], case
        assert p1["counter_lines"] == ["A"], case
        p2 = phases[1]
        assert p2["returncode"] == 0 and statuses(p2) == ["completed"], case
        assert journal_types(p2) == ["launched", "started", "result", "started", "started", "result"], case
        assert p2["counter_lines"] == ["A", "B"], case
        return {"crash_boundary": "after first result journaling, second agent started", "resumed": True, "journaled_result_reused": True, "first_agent_side_effect_executions": 1}
    if case == "journal-truncate":
        assert p1["returncode"] == 0 and statuses(p1) == ["completed"], case
        assert p1["counter_lines"] == ["A", "B"], case
        p2 = phases[1]
        assert p2["returncode"] == 0 and statuses(p2) == ["completed"], case
        assert p2["counter_lines"] == ["A", "B", "B"], case
        entries = journal_entries(p2)
        truncated = [e for e in entries if "type" not in e]
        assert len(truncated) == 1 and truncated[0].get("truncated"), (case, truncated)
        assert journal_types(p2)[-1] == "result", case
        return {"truncated_entry_reexecuted": "B", "side_effect_duplicated": True, "final_status": "completed"}
    if case == "resume-competing":
        assert p1["returncode"] == 0 and statuses(p1) == ["completed"], case
        assert p1["counter_lines"] == ["A", "B"], case
        for p in phases[1:]:
            assert p["returncode"] == 0 and p["max_active_agent_requests"] == 0, case
            assert journal_types(p) == journal_types(p1), case
            assert p["counter_lines"] == ["A", "B"], case
        return {"concurrent_resumptions": 2, "reexecuted_agents": 0, "journal_corrupted": False}
    if case == "cancel-task":
        assert p1["returncode"] == 0 and statuses(p1) == ["killed"], case
        assert p1["late_write"] is False and p1["started_shell"] is True, case
        stops = [r for c in captures(root, 1) for r in c["fixture_tool_results"] if r.get("tool_use_id") == "fixture_stop"]
        assert stops and "Successfully stopped task" in stops[0]["content"], (case, stops)
        return {"task_stop_acknowledged": True, "late_write_after_cancel": False, "status": "killed"}
    if case == "signal-term":
        assert p1["returncode"] == 143 and p1["signal_sent"]["name"] == "SIGTERM", case
        assert p1["workflow_states"] == [] and p1["late_write"] is False, case
        assert journal_types(p1) == ["launched", "started"], case
        return {"exit_code": 143, "workflow_state_persisted": False, "late_write_after_term": False}
    if case == "print-ceiling":
        assert p1["returncode"] == 0 and statuses(p1) == ["killed"], case
        assert p1["late_write"] is False, case
        command = json.loads((root / "phases" / "1" / "command.json").read_text())
        assert command["controls"].get("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS") == "100", case
        updates = [e for e in stdout_events(root, 1) if e.get("subtype") == "task_updated"]
        assert updates and updates[-1]["patch"]["status"] == "killed", (case, updates)
        return {"ceiling_exceeded": True, "workflow_killed": True, "late_write_after_kill": False, "cli_exit": 0}
    if case in ("concurrency-1", "nested-concurrency-1"):
        assert p1["returncode"] == 0 and statuses(p1) == ["completed"], case
        assert p1["max_active_agent_requests"] == 1, case
        assert journal_types(p1) == ["launched", "started", "result", "started", "result", "started", "result"], case
        return {"max_concurrent_agent_requests": 1, "serialized": True}
    if case in ("concurrency-2", "nested-concurrency-2"):
        assert p1["returncode"] == 0 and statuses(p1) == ["completed"], case
        assert p1["max_active_agent_requests"] == 2, case
        assert journal_types(p1) == ["launched", "started", "started", "result", "started", "result", "result"], case
        return {"max_concurrent_agent_requests": 2, "cap_shared_with_nested_workflow": case.startswith("nested-")}
    if case == "budget":
        assert p1["returncode"] == 1, case
        assert result_event(p1)["subtype"] == "error_max_budget_usd", case
        assert statuses(p1) == ["killed"], case
        assert journal_types(p1) == ["launched", "started", "result", "started"], case
        command = json.loads((root / "phases" / "1" / "command.json").read_text())
        assert "--max-budget-usd" in command["argv"], case
        return {"cli_exit": 1, "terminal": "error_max_budget_usd", "status": "killed", "gate_fired_at": "next agent launch"}
    if case == "budget-nested":
        assert p1["returncode"] == 1, case
        assert statuses(p1) == ["completed"], case
        assert journal_types(p1) == ["launched", "started", "result"], case
        subtypes = [e.get("subtype") for e in p1["terminal_results"]]
        assert subtypes == ["success", "error_max_budget_usd"], (case, subtypes)
        assert p1["terminal_results"][-1]["total_cost_usd"] >= 2.0, case
        return {"cli_exit": 1, "workflow_status": "completed", "nested_skill_usage_counted": True, "terminal_subtypes": subtypes}
    if case in ("retry-429", "retry-500", "retry-broken"):
        assert p1["returncode"] == 0 and statuses(p1) == ["completed"], case
        assert p1["counter_lines"] == ["A"], case
        faults = [c["fault"] for c in captures(root, 1) if c["fault"]]
        assert faults == [case], (case, faults)
        assert journal_types(p1) == ["launched", "started", "result"], case
        return {"injected_fault": case, "retried": True, "side_effect_executions": 1}
    if case == "retry-exhaust":
        assert p1["returncode"] == 1, case
        state = p1["workflow_states"][0]["state"]
        assert state["status"] == "completed" and state.get("result") is None, (case, state)
        assert journal_types(p1) == ["launched", "started", "failed"], case
        assert p1["counter_lines"] == ["A", "A"], case
        assert result_event(p1)["is_error"] is True, case
        return {"agent_retry_exhausted": True, "workflow_result": None, "side_effect_executions": 2, "cli_exit": 1}
    if case == "stall-retry":
        assert p1["returncode"] == 0 and statuses(p1) == ["completed"], case
        assert journal_types(p1) == ["launched", "started", "started", "result"], case
        started = [e["agentId"] for e in journal_entries(p1) if e.get("type") == "started"]
        assert len(set(started)) == 2, (case, started)
        assert p1["counter_lines"] == ["A", "A"], case
        assert p1["max_active_agent_requests"] >= 2, case
        return {"stall_detected": True, "recovery": "fresh agent conversation", "side_effect_executions": 2}
    if case == "stall-exhaust":
        assert p1["returncode"] == 0, case
        assert statuses(p1) == ["failed"], case
        types = journal_types(p1)
        assert types == ["launched"] + ["started"] * 6 + ["failed"], (case, types)
        assert p1["counter_lines"] == ["A"] * 6, case
        return {"stall_recovery_iterations": 5, "side_effect_executions": 6, "status": "failed"}
    if case in NETWORK_CASES:
        return check_network_fault(root, case)
    if case == NOTIFY_CASE:
        return check_notify_fault(root)
    raise AssertionError(f"unhandled case {case}")


def check_notify_fault(root: Path) -> dict:
    """Workflow completes; the notification-delivery turn then fails terminally."""
    run = json.loads((root / "results.json").read_text())
    assert run["returncode"] == 1, run["returncode"]
    assert run["counter_lines"] == ["A"], run["counter_lines"]
    assert journal_types(run) == ["launched", "started", "result"], journal_types(run)
    state = run["workflow_states"][0]["state"]
    assert state["status"] == "completed" and state.get("result") == {"marker": "OPS_RESULT_A", "context": "none"}, state
    caps = [json.loads(p.read_text()) for p in sorted((root / "api-captures").glob("*.json"))]
    roles = [(c["role"], bool(c["fault"])) for c in caps]
    assert roles == [("controller", False), ("agent-A", False), ("controller", False), ("agent-A", False), ("controller", True), ("controller", True), ("controller", True)], roles
    agent_final = caps[3]["started_monotonic"]
    assert all(c["started_monotonic"] > agent_final for c in caps[4:])
    finals = run["terminal_results"]
    assert finals[-1]["is_error"] is True and "API Error" in str(finals[-1].get("result")), finals[-1]
    return {"workflow_status": "completed", "result_persisted": True, "notification_turn_retries": 2, "cli_outcome": "API error, exit 1 despite completed workflow"}


def check_network_fault(root: Path, case: str) -> dict:
    run = json.loads((root / "results.json").read_text())
    assert run["returncode"] == 1, (case, run["returncode"])
    assert statuses(run) == ["completed"], (case, statuses(run))
    state = run["workflow_states"][0]["state"]
    assert state["status"] == "completed" and state.get("result") is None, (case, state)
    types = journal_types(run)
    assert types == ["launched", "started", "failed"], (case, types)
    assert run["counter_lines"] == ["A", "A"], (case, run["counter_lines"])
    assert result_event(run)["is_error"] is True, case
    caps = [json.loads(p.read_text()) for p in sorted((root / "api-captures").glob("*.json"))]
    assert caps, case
    faulted = [c for c in caps if c.get("fault")]
    clean_after = [c for c in caps if not c.get("fault") and c["started_monotonic"] > faulted[0]["started_monotonic"]]
    if case == "spend-limit-429":
        assert len(faulted) == 2 and len(caps) == 6, (case, len(faulted), len(caps))
        gap = faulted[1]["started_monotonic"] - clean_after[0]["started_monotonic"]
        assert gap < 1.0, (case, gap)
        return {"request_retries": 0, "conversation_restarts": 1, "side_effect_executions": 2, "non_retryable": True}
    assert len(faulted) == 6 and len(caps) == 10, (case, len(faulted), len(caps))
    gaps = [faulted[i + 1]["started_monotonic"] - faulted[i]["started_monotonic"] for i in range(2)]
    assert all(0.2 < g < 5.0 for g in gaps) and gaps[1] > gaps[0] * 1.5, (case, gaps)
    return {"request_retries_per_conversation": 2, "conversation_restarts": 1, "side_effect_executions": 2, "measured_backoff_gaps_s": [round(g, 2) for g in gaps]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    cases = ["replay-fresh", "replay-shared", "replay-reverse", "crash-during-agent", "crash-before-result", "crash-after-result", "journal-truncate", "resume-competing", "cancel-task", "signal-term", "print-ceiling", "concurrency-1", "concurrency-2", "nested-concurrency-1", "nested-concurrency-2", "budget", "budget-nested", "retry-429", "retry-500", "retry-broken", "retry-exhaust", "stall-retry", "stall-exhaust"]
    summary = []
    for case in cases:
        suffix = "-resume-v1" if case in RESUME_CASES else "-v1"
        root = args.traces / f"workflow-operations-{case}{suffix}"
        phase_count = 3 if case == "resume-competing" else 2 if case in RESUME_CASES or case.startswith("replay-") or case == "journal-truncate" else 1
        phases = check_base(case, root, phase_count)
        result = outcome(case, root, phases)
        summary.append({"case": case, "passed": True, "run": str(root), "outcome": result, "api_requests": [p["api_requests"] for p in phases], "agent_max_concurrency": [p["max_active_agent_requests"] for p in phases]})
    for case in sorted(NETWORK_CASES) + [NOTIFY_CASE]:
        if case == NOTIFY_CASE:
            root = args.traces / "workflow-network-notify-fault-v2"
        else:
            root = args.traces / f"workflow-network-{case}-v1"
        manifest = json.loads((root / "manifest.json").read_text())
        assert manifest["binary_sha256"] == PINNED_BINARY_SHA256, (case, manifest["binary_sha256"])
        run = json.loads((root / "results.json").read_text())
        result = check_notify_fault(root) if case == NOTIFY_CASE else check_network_fault(root, case)
        summary.append({"case": case, "passed": True, "run": str(root), "outcome": result, "api_requests": [run["api_requests"]], "agent_max_concurrency": [1]})
    write_json(args.output, {"schema_version": 1, "binary_sha256": PINNED_BINARY_SHA256, "controls": summary})
    print(f"Verified {len(summary)} workflow operations controls")


if __name__ == "__main__":
    main()
