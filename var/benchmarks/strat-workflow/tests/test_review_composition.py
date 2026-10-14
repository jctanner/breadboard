"""The final document must be grounded in delivered receipts, not its own claims."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_review_composition import CASES, MODEL, ROLES, verify


def save(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def hashed(text):
    return hashlib.sha256(text.encode()).hexdigest()


def evidence(root):
    artifacts = root / "fixture/artifacts"
    directory = artifacts / "strat-reviews"
    directory.mkdir(parents=True)
    calls, receipts, progress = [], [], {"run_id": "fixture", "review": {}}
    for key, case in CASES.items():
        decision = {field: case[field] for field in ("recommendation", "needs_attention")}
        metadata = {**decision, "scores": {"total": case["score"], **dict.fromkeys(ROLES, case["score"] // 4)},
                    "reviewers": dict(zip(ROLES, case["roles"]))}
        text, reports = "## Review\n", {}
        for role, verdict in zip(ROLES, case["roles"]):
            identity = key + role
            body = f"### {key}: Strategy\n{role.upper()}_{key.split('-')[-1]}: Authored concern.\n**Recommendation**: {verdict}"
            path = directory / f"{key}-review-{role}.md"
            path.write_text(body)
            reports[role] = {"key": key, "role": role, "path": "artifacts/" + str(path.relative_to(artifacts)),
                "tool_use_id": identity, "agent_id": identity, "caller": "caller", "session_id": key,
                "sha256": hashed(body), "recommendation": verdict}
            calls.append({"type": "tool_use", "id": identity, "name": "Skill",
                "input": {"skill": "strategy-" + role + "-review", "args": key}})
            receipts.append({"type": "tool_result", "tool_use_id": identity, "content": body})
            save(root, "config/projects/session/subagents/agent-" + identity + ".jsonl", {
                "type": "assistant", "message": {"content": [{"type": "text", "text": body}]}})
            text += body + "\n"
            if verdict != case["recommendation"]:
                text += f"{role}: {verdict} (numeric: {case['recommendation']})\n"
        text += "separate numeric assessor\n"
        review = directory / f"{key}-review.md"
        review.write_text("---\n" + yaml.safe_dump(metadata) + "---\n" + text)
        inputs = {}
        for name in ("strategy", "rfe", "scorer"):
            path = directory / f"{key}-{name}.md"
            path.write_text("Authored " + name)
            inputs[name] = {"path": "artifacts/" + str(path.relative_to(artifacts)), "sha256": hashed(path.read_text())}
        manifest = {"policy": "numeric-only-v1", "key": key, "caller": "caller", "session_id": key,
            "workflow_run_id": "fixture", "decision": decision, "reports": reports,
            "inputs": {name: inputs[name] for name in ("strategy", "rfe")}, "scorer": inputs["scorer"],
            "review": {"path": f"artifacts/strat-reviews/{key}-review.md", "sha256": hashed(review.read_text())}}
        save(root, "fixture/artifacts/strat-reviews/" + key + "-review-provenance.json", manifest)
        progress["review"][key] = {**decision, "composition_session": key}
        calls.extend([
            {"type": "tool_use", "id": key + "parent", "name": "Skill", "input": {"skill": "strategy-review", "args": key}},
            {"type": "tool_use", "id": key + "compose", "name": "Bash", "input": {"command": "python3 scripts/review_composition.py compose " + key}}])
    save(root, "api-dumps/one.request.json", {"model": MODEL, "messages": [{"role": "user", "content": receipts}]})
    save(root, "api-dumps/one.response.json", {"content": calls})
    save(root, "fixture/tmp/strat-progress.json", progress)
    save(root, "config/projects/workflows/wf_test.json", {"status": "completed", "result": [
        {"key": key, **{field: case[field] for field in ("recommendation", "needs_attention")}} for key, case in CASES.items()]})


class TestCompositionEvidence(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        evidence(self.root)

    def test_complete_delivered_reports_and_numeric_gate_pass(self):
        result = verify(self.root)
        self.assertTrue(result["passed"], result.get("errors"))

    def test_review_on_disk_cannot_hide_missing_delivery(self):
        path = self.root / "api-dumps/one.request.json"
        request = json.loads(path.read_text())
        request["messages"][0]["content"].pop()
        path.write_text(json.dumps(request))
        self.assertFalse(verify(self.root)["passed"])

    def test_changed_final_body_cannot_omit_a_report(self):
        path = self.root / "fixture/artifacts/strat-reviews/STRAT-9501-review.md"
        path.write_text(path.read_text().replace("TESTABILITY_9501: Authored concern.", "Concern removed."))
        self.assertFalse(verify(self.root)["passed"])

    def test_copied_role_cannot_claim_another_invocation(self):
        path = self.root / "fixture/artifacts/strat-reviews/STRAT-9501-review-provenance.json"
        manifest = json.loads(path.read_text())
        manifest["reports"]["scope"]["tool_use_id"] = manifest["reports"]["feasibility"]["tool_use_id"]
        path.write_text(json.dumps(manifest))
        self.assertFalse(verify(self.root)["passed"])

    def test_wrong_flag_does_not_pass_successful_workflow(self):
        path = self.root / "fixture/artifacts/strat-reviews/STRAT-9502-review.md"
        path.write_text(path.read_text().replace("needs_attention: true", "needs_attention: false"))
        self.assertFalse(verify(self.root)["passed"])

    def test_missing_provenance_fails_explicitly(self):
        (self.root / "fixture/artifacts/strat-reviews/STRAT-9502-review-provenance.json").unlink()
        self.assertFalse(verify(self.root)["passed"])


if __name__ == "__main__":
    unittest.main()
