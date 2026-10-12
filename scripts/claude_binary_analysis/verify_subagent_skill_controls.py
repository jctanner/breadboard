#!/usr/bin/env python3
"""Verify skill isolation behavior using scoped captures and fixture provenance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_plugin_experiments import sha256, write_json
from run_subagent_skill_experiments import BODY, CHILD_ANSWER, DESCRIPTION, NAME


CASES = ["explore-read", "general-read", "workflow-read", "explore-bash", "no-read", "ignored-read", "settings-disabled", "primary-skill", "child-skill", "child-read-skill"]
NEGATIVE = {"explore-bash", "no-read", "ignored-read", "settings-disabled"}


def has_marker(captures: list[dict], marker: str) -> bool:
    return any(marker in e["markers"] for c in captures for e in c["fixture_marker_excerpts"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    controls = []
    hashes = set()
    for case in CASES:
        root = args.traces / f"subagent-skill-{case}-v1"
        run = json.loads((root / "results.json").read_text())
        command = json.loads((root / "command.json").read_text())
        assert run["returncode"] == 0, run
        assert run["binary_sha256"] == command["binary_sha256"]
        hashes.add(run["binary_sha256"])
        for file in command["fixture_tree"]["files"]:
            path = Path(command["fixture_tree"]["root"]) / file["path"]
            assert path.is_file() and sha256(path) == file["sha256"], path
        captures = [json.loads(p.read_text()) for p in sorted((root / "api-captures").glob("*.json"))]
        primary = [c for c in captures if c["agent"] == "primary"]
        child = [c for c in captures if c["agent"] == "child"]
        assert primary and child and not primary[0]["fixture_marker_excerpts"]
        child_calls = [b for c in child for b in c["mock_response"] if b["type"] == "tool_use"]
        expected = [] if case == "no-read" else ["Bash"] if case == "explore-bash" else ["Read", "Skill"] if case == "child-skill" else ["Read"]
        assert [b["name"] for b in child_calls] == expected, (case, child_calls)
        assert any(c["mock_response"] == [{"type": "text", "text": CHILD_ANSWER}] for c in child)
        for c in child:
            for result in c["fixture_tool_results"]:
                assert not result.get("is_error"), (case, result)
        metadata = has_marker(primary[1:], DESCRIPTION)
        assert metadata == (case not in NEGATIVE), (case, primary)
        body = has_marker(primary, BODY)
        assert body == (case == "primary-skill"), (case, primary)
        if case == "primary-skill":
            skill_index = next(c["request_index"] for c in primary if any(b.get("name") == "Skill" for b in c["mock_response"]))
            assert not has_marker([c for c in primary if c["request_index"] <= skill_index], BODY)
            assert has_marker([c for c in primary if c["request_index"] > skill_index], BODY)
            assert any(r.get("tool_use_id") == "fixture_parent_skill" and not r.get("is_error") for c in primary for r in c["fixture_tool_results"])
        if case in ("child-skill", "child-read-skill"):
            assert has_marker(child, BODY), (case, child)
        if case not in ("child-skill", "child-read-skill"):
            assert not has_marker(child, BODY), case
        # No direct file operations by the primary: the only root operations
        # are agent/workflow launch and, in one deliberate control, Skill.
        parent_calls = [b["name"] for c in primary for b in c["mock_response"] if b["type"] == "tool_use"]
        assert not any(name in ("Read", "Bash", "Write", "Edit") for name in parent_calls)
        controls.append({
            "case": case, "passed": True, "run": str(root),
            "primary_initial_markers": [],
            "primary_receives_metadata": metadata,
            "primary_receives_body": body,
            "child_receives_body": has_marker(child, BODY),
            "child_tools_used": expected, "primary_tools_used": parent_calls,
            "first_primary_metadata_request": next((c["request_index"] for c in primary if has_marker([c], DESCRIPTION)), None),
            "metadata_excerpts": [e for c in primary for e in c["fixture_marker_excerpts"] if DESCRIPTION in e["markers"]],
            "fixture_tree_sha256": command["fixture_tree"]["tree_sha256"],
            "fixture_git_commit": command["fixture_repository"]["head"],
            "runner_sha256": command["runner_sha256"],
            "api_request_count": run["api_requests"],
        })
    assert len(hashes) == 1, hashes
    write_json(args.output, {"schema_version": 1, "binary_sha256": hashes.pop(), "markers": {"name": NAME, "description": DESCRIPTION, "body": BODY}, "controls": controls})
    print(f"Verified {len(controls)} subagent skill isolation controls")


if __name__ == "__main__":
    main()
