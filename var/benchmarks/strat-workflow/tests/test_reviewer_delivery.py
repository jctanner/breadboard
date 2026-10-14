import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_batch import valid_report

path = Path(__file__).resolve().parents[1] / "scripts" / "verify_reviewer_delivery.py"
spec = importlib.util.spec_from_file_location("verify_reviewer_delivery", path)
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class ReviewerDeliveryTests(unittest.TestCase):
    def fixture(self, root):
        api = root / "api-dumps"
        api.mkdir()
        artifacts = root / "artifacts"
        artifacts.mkdir()
        (artifacts / "claude-exit.txt").write_text("0")
        state = artifacts / "native-projects" / "project" / "session" / "workflows"
        state.mkdir(parents=True)
        (state / "wf_fixture.json").write_text(json.dumps({"status": "completed", "result": {"key": delivery.TARGET}}))
        blocks = []
        for index, (role, heading) in enumerate(delivery.ROLES.items()):
            blocks.extend([{"type": "tool_use", "name": "Skill", "id": str(index),
                            "input": {"skill": role, "args": delivery.TARGET}},
                           {"type": "tool_result", "tool_use_id": str(index), "content":
                            valid_report(delivery.TARGET, role.removeprefix("strategy-").removesuffix("-review"))}])
            (api / f"leaf-{index}.request.json").write_text(json.dumps({
                "model": delivery.MODEL, "system": "return its complete assessment",
                "tools": [{"name": tool} for tool in ["Read", "Grep", "Glob"]], "messages": []}))
        receiver = api / "receiver.request.json"
        receiver.write_text(json.dumps({"model": delivery.MODEL, "messages": [{"content": blocks}]}))
        (api / "receiver.response.json").write_text(json.dumps({"content": [
            {"type": "tool_use", "name": "StructuredOutput", "id": "outer",
             "input": {"key": delivery.TARGET, "recommendation": "revise", "needs_attention": True}}]}))
        return receiver

    def test_reports_and_outer_status_pass(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            self.fixture(root)
            self.assertTrue(delivery.verify(root)["passed"])

    def test_successful_workflow_does_not_hide_acknowledgement_only_review(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            receiver = self.fixture(root)
            value = json.loads(receiver.read_text())
            value["messages"][0]["content"][1]["content"] = "Skill execution completed"
            receiver.write_text(json.dumps(value))
            report = delivery.verify(root)
            self.assertFalse(report["passed"])
            self.assertFalse(report["reports"][0]["delivered"])

    def test_schema_tool_and_unapproved_model_fail(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            self.fixture(root)
            leaf = root / "api-dumps" / "leaf-0.request.json"
            value = json.loads(leaf.read_text())
            value["model"] = "unapproved-model"
            value["tools"].append({"name": "StructuredOutput"})
            leaf.write_text(json.dumps(value))
            report = delivery.verify(root)
            self.assertFalse(report["passed"])
            self.assertIn("unexpected request model", report["errors"])
            self.assertIn("reviewer agent tool isolation not established", report["errors"])


if __name__ == "__main__":
    unittest.main()
