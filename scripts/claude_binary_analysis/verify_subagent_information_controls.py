#!/usr/bin/env python3
"""Verify additional subagent channels from actual requests and side effects."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from run_plugin_experiments import sha256, write_json
from run_subagent_skill_experiments import CHILD_ANSWER, EDIT, MEMORY, OUTPUT, strings
from verify_subagent_skill_controls import has_marker


CASES = {
    "memory-read": "v2",
    "memory-propagate": "v3",
    "file-edit": "v2",
    "file-edit-unread": "v1",
    "file-edit-parent-write": "v1",
    "bash-output": "v1",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    controls = []
    hashes = set()
    for case, version in CASES.items():
        root = args.traces / f"subagent-skill-{case}-{version}"
        command = json.loads((root / "command.json").read_text())
        outcome = json.loads((root / "results.json").read_text())
        assert outcome["returncode"] == 0
        assert sha256(root / "runner.py") == command["runner_sha256"]
        hashes.add(command["binary_sha256"])
        fixture_root = Path(command["fixture_tree"]["root"])
        for file in command["fixture_tree"]["files"]:
            path = fixture_root / file["path"]
            if case.startswith("file-edit") and file["path"] == "architecture-context/README.md":
                # This file was deliberately changed. Verify its original Git
                # blob and final disk state rather than requiring immutability.
                original = subprocess.check_output(["git", "show", f"{command['fixture_repository']['head']}:{file['path']}"], cwd=fixture_root)
                assert hashlib.sha256(original).hexdigest() == file["sha256"]
                assert path.read_text() == f"{EDIT}\n"
            else:
                assert sha256(path) == file["sha256"], path
        captures = [json.loads(p.read_text()) for p in sorted((root / "api-captures").glob("*.json"))]
        primary = [c for c in captures if c["agent"] == "primary"]
        child = [c for c in captures if c["agent"] == "child"]
        assert primary and child and not primary[0]["fixture_marker_excerpts"]
        assert any(c["mock_response"] == [{"type": "text", "text": CHILD_ANSWER}] for c in child)
        for c in captures:
            assert not any(r.get("is_error") for r in c["fixture_tool_results"]), (case, c)
        child_calls = [b for c in child for b in c["mock_response"] if b["type"] == "tool_use"]
        expected = ["Read", "Write"] if case.startswith("file-edit") else ["Bash"] if case == "bash-output" else ["Read"]
        assert [b["name"] for b in child_calls] == expected
        parent_calls = [b for c in primary for b in c["mock_response"] if b["type"] == "tool_use"]
        assert not has_marker(primary, MEMORY)
        assert not has_marker(primary, OUTPUT)
        assert has_marker(primary, EDIT) == (case == "file-edit-parent-write")
        if case.startswith("memory-"):
            assert has_marker(child, MEMORY)
            assert any(b["name"] == "Skill" for b in parent_calls)
            assert not any(b["name"] in ("Read", "Bash", "Write", "Edit") for b in parent_calls)
        if case == "file-edit-parent-write":
            child_write_index = next(c["request_index"] for c in child if any(b.get("name") == "Write" for b in c["mock_response"]))
            assert all(c["request_index"] > child_write_index for c in primary if has_marker([c], EDIT))
            assert all(EDIT not in value for b in parent_calls for _, value in strings(b))
        if case in ("file-edit", "file-edit-parent-write"):
            assert any(b["id"] == "fixture_parent_after_read" for b in parent_calls)
        if case == "bash-output":
            assert any(OUTPUT in value for c in child for r in c["fixture_tool_results"] for _, value in strings(r.get("content")))
        # Preserve only scoped notification fields; the child result itself
        # intentionally contains none of the tested content markers.
        notices = []
        for c in primary:
            for path, value in strings(c["fixture_tool_results"]):
                if "Async agent launched" in value:
                    notices.append({"request_index": c["request_index"], "path": path,
                                    "provides_full_transcript_path": "full subagent JSONL transcript" in value,
                                    "output_file": next(iter(re.findall(r"output_file: (\S+)", value)), None)})
        assert notices
        assert all(n["provides_full_transcript_path"] == (case != "memory-propagate") for n in notices)
        stream = [json.loads(line) for line in (root / "stdout.jsonl").read_text().splitlines() if line.startswith("{")]
        task_notices = [c for c in stream if c.get("subtype") == "task_notification"]
        assert task_notices and task_notices[-1]["status"] == "completed"
        sdk_child = [c for c in stream if c.get("agent_id") and c.get("type") in ("user", "assistant")]
        sdk_has_bash_output = any(OUTPUT in value for c in sdk_child for _, value in strings(c))
        if case == "bash-output":
            assert sdk_has_bash_output
        controls.append({
            "case": case, "passed": True, "run": str(root),
            "runner_sha256": command["runner_sha256"],
            "fixture_tree_sha256": command["fixture_tree"]["tree_sha256"],
            "fixture_git_commit": command["fixture_repository"]["head"],
            "coordinator_flags": command.get("coordinator_flags", {}),
            "primary_tools_used": [b["name"] for b in parent_calls],
            "child_tools_used": expected,
            "primary_receives_memory": has_marker(primary, MEMORY),
            "primary_receives_edit": has_marker(primary, EDIT),
            "primary_receives_bash_output": has_marker(primary, OUTPUT),
            "child_receives_memory": has_marker(child, MEMORY),
            "primary_excerpts": [e for c in primary for e in c["fixture_marker_excerpts"] if EDIT in e["markers"]],
            "launch_notices": notices[:1],
            "completion_status": task_notices[-1]["status"],
            "completion_usage": task_notices[-1].get("usage"),
            "sdk_child_message_count": len(sdk_child),
            "sdk_child_messages_contain_bash_marker": sdk_has_bash_output,
            "api_request_count": len(captures),
        })
    assert len(hashes) == 1
    write_json(args.output, {"schema_version": 1, "binary_sha256": hashes.pop(), "controls": controls})
    print(f"Verified {len(controls)} additional subagent information controls")


if __name__ == "__main__":
    main()
