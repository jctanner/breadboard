import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_reviewer_scope import inspect, MODEL, ROLES, TARGETS, outcome_issues
from test_batch import valid_report


def scenario():
    requests, content, audits, transcripts = [], [], {}, {}
    for key, canary in TARGETS.items():
        for role, heading in ROLES.items():
            identity = key + "_" + role
            prompt = f"Base directory for this skill: /repo/.claude/skills/{role}\nREVIEW_SCOPE_TARGET: {key}\n"
            transcripts[identity] = prompt
            content.extend([
                {"type": "tool_use", "name": "Skill", "id": identity, "input": {"skill": role, "args": key}},
                {"type": "tool_result", "tool_use_id": identity, "content":
                 valid_report(key, role.removeprefix("strategy-").removesuffix("-review"))}])
            requests.append({"model": MODEL, "tools": [{"name": name} for name in ["Read", "Grep", "Glob"]],
                             "messages": [{"role": "user", "content": prompt + canary}]})
            audits[identity] = [
                {"allowed": True, "event": "PreToolUse", "key": key, "tool": "Read",
                 "input": {"file_path": f"/repo/artifacts/strat-tasks/{key}.md"}},
                {"allowed": True, "event": "PreToolUse", "key": key, "tool": "Read",
                 "input": {"file_path": f"/repo/artifacts/rfe-tasks/{key.replace('STRAT', 'RFE')}.md"}},
                {"allowed": True, "event": "SubagentStop", "key": key}]
    return requests, [{"content": content}], audits, transcripts


class TestReviewerScopeEvidence(unittest.TestCase):
    def test_business_flag_contradiction_is_reported_separately(self):
        issues = outcome_issues([{"key": "RHAISTRAT-9101", "recommendation": "revise", "needs_attention": False},
                                 {"key": "RHAISTRAT-9102", "recommendation": "revise", "needs_attention": True}])
        self.assertEqual([issue["key"] for issue in issues], ["RHAISTRAT-9101"])

    def test_complete_targeted_reports_with_hooks_pass(self):
        result = inspect(*scenario())
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(len(result["reports"]), 12)

    def test_successful_report_does_not_hide_foreign_input(self):
        values = list(scenario())
        values[0][0]["messages"].append({"role": "user", "content": [{"type": "tool_result",
            "tool_use_id": "foreign_read", "content": "RETENTION_SCOPE_CANARY"}]})
        self.assertFalse(inspect(*values)["passed"])

    def test_missing_effective_hook_cannot_pass(self):
        values = list(scenario())
        values[2].clear()
        self.assertFalse(inspect(*values)["passed"])

    def test_wrong_ticket_cannot_satisfy_a_role(self):
        values = copy.deepcopy(scenario())
        values[1][0]["content"][1]["content"] = values[1][0]["content"][1]["content"].replace("RHAISTRAT-9101", "RHAISTRAT-9102")
        self.assertFalse(inspect(*values)["passed"])


if __name__ == "__main__":
    unittest.main()
