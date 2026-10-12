#!/usr/bin/env python3
"""Check actual skill expansion requests against fixture paths and values."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from run_plugin_experiments import sha256, write_json


CASES = {"local-args": "v1", "local-empty": "v1", "local-fallback": "v2", "local-escapes": "v1", "local-argument-variables": "v1", "local-shell": "v2", "plugin-args": "v1", "plugin-config": "v2", "plugin-shell": "v2"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("traces", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    controls = []
    binary_hashes = set()
    for case, version in CASES.items():
        root = args.traces / f"skill-variables-{case}-{version}"
        command = json.loads((root / "command.json").read_text())
        result = json.loads((root / "results.json").read_text())
        assert result["returncode"] == 0 and not result["fixture_errors"]
        assert sha256(root / "runner.py") == command["runner_sha256"]
        binary_hashes.add(command["binary_sha256"])
        for file in command["fixture_tree"]["files"]:
            path = Path(command["fixture_tree"]["root"]) / file["path"]
            assert sha256(path) == file["sha256"], path
        captures = [json.loads(p.read_text()) for p in sorted((root / "api-captures").glob("*.json"))]
        assert not captures[0]["fixture_texts"] and len(captures) >= 2
        assert captures[0]["mock_response"][0]["name"] == "Skill"
        assert any(c["invoked_skill_result_present"] for c in captures[1:])
        assert all(not c["fixture_errors"] for c in captures)
        texts = [e["text"] for c in captures[1:] for e in c["fixture_texts"]]
        assert len(texts) == 1
        text = texts[0]
        rows = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
        if case in ("local-args", "local-empty", "local-argument-variables", "plugin-args"):
            assert rows["skill"] == command["skill_dir"]
            assert rows["project"] == command["project_dir"]
            stream = [json.loads(line) for line in (root / "stdout.jsonl").read_text().splitlines() if line.startswith("{")]
            session_id = next(c["session_id"] for c in stream if c.get("subtype") == "init")
            assert rows["session"] == session_id and re.fullmatch(r"[0-9a-f-]{36}", session_id)
            assert rows["effort"] == "low"
            assert rows["missing"] == "$ARGUMENTS[9]|$9"
            assert rows["unsupported"] == "${SKILL_DIR}|$SKILL_DIR|$CLAUDE_SKILL_DIR|${ARGUMENTS}|${HOME}|${VARIABLE_FIXTURE_ENV}"
            if case == "local-empty":
                assert rows["all"] == "" and rows["zero"] == "$0" and rows["one"] == "$1"
                assert rows["index"] == "$ARGUMENTS[1]" and rows["named"] == "|"
            elif case == "local-argument-variables":
                assert rows["all"] == session_id and rows["zero"] == session_id
                assert rows["named"] == session_id + "|"
            else:
                assert rows["all"] == command["arguments"] and rows["zero"] == "alpha"
                assert rows["one"] == rows["index"] == "two words"
                assert rows["named"] == "alpha|two words"
            if case.startswith("plugin-"):
                assert rows["plugin"] == command["plugin_root"]
                expected_data = Path(command["config_dir"]) / "plugins/data/variable-fixture-inline"
                assert rows["data"] == str(expected_data) and expected_data.is_dir()
            else:
                assert rows["plugin"] == "${CLAUDE_PLUGIN_ROOT}" and rows["data"] == "${CLAUDE_PLUGIN_DATA}"
        elif case == "local-fallback":
            assert rows["skill"] == command["skill_dir"]
            assert text.endswith("\n\nARGUMENTS: " + command["arguments"])
        elif case == "local-escapes":
            assert rows == {"escaped": "$ARGUMENTS|$0|$target", "missing": "$ARGUMENTS[9]|$9", "named": ""}
            assert "\nARGUMENTS: " not in text
        elif case == "plugin-config":
            assert rows == {"option": "CONFIGURED_COLOR_MARKER", "sensitive": "[sensitive option 'secret' not available in skill content]", "unset": "${user_config.unset}", "undeclared": "${user_config.unknown}", "defaultonly": "${user_config.onlydefault}"}
            assert "FAKE_NONCREDENTIAL_MARKER" not in text
        elif case.endswith("shell"):
            assert "!`" not in text
            assert rows["VARIABLE_FIXTURE_SHELL_OUTPUT"] == "${CLAUDE_SKILL_DIR}"
            assert "\n" + command["project_dir"] + "\n" in text
        controls.append({"case": case, "passed": True, "run": str(root), "runner_sha256": command["runner_sha256"], "fixture_tree_sha256": command["fixture_tree"]["tree_sha256"], "fixture_git_commit": command["fixture_repository"]["head"], "arguments": command["arguments"], "expanded_fixture": text, "api_request_count": len(captures)})
    assert len(binary_hashes) == 1
    write_json(args.output, {"schema_version": 1, "binary_sha256": binary_hashes.pop(), "controls": controls})
    print(f"Verified {len(controls)} skill variable expansion controls")


if __name__ == "__main__":
    main()
