from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    "delivery", Path(__file__).resolve().parents[1] / "check_specialist_delivery.py")
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.entry = {"strategy": "RHAISTRAT-1", "role": "scope", "tool_use_id": "call-1",
                      "required_fragments": ["SPECIFIC_FINDING", "DISSENT_REVISE"]}
        self.manifest = {"schema_version": 1, "expected": [self.entry]}
        self.observation = {"strategy": "RHAISTRAT-1", "role": "scope", "tool_use_id": "call-1",
                            "content": "SPECIFIC_FINDING. DISSENT_REVISE."}

    def tearDown(self):
        self.temp.cleanup()

    def check(self, observations):
        return delivery.check_delivery(self.manifest, observations, self.root)

    def test_complete_report_and_deduplicated_history(self):
        result = self.check([self.observation, self.observation])
        self.assertTrue(result["ok"])
        self.assertEqual(result["delivered"], 1)

    def test_status_and_long_progress_are_not_reports(self):
        for content in ("Skill execution completed", "Now I will compose the review. " * 100):
            self.assertFalse(self.check([{**self.observation, "content": content}])["ok"])

    def test_missing_dissent_and_error_fail(self):
        self.assertFalse(self.check([{**self.observation, "content": "SPECIFIC_FINDING"}])["ok"])
        self.assertFalse(self.check([{**self.observation, "is_error": True}])["ok"])

    def test_wrong_launch_target_and_missing_role_fail(self):
        self.assertFalse(self.check([{**self.observation, "strategy": "RHAISTRAT-2"}])["ok"])
        self.assertFalse(self.check([])["ok"])

    def test_conflicting_results_and_unexpected_calls_fail(self):
        self.assertFalse(self.check([self.observation, {**self.observation, "content": "Different"}])["ok"])
        self.assertFalse(self.check([self.observation, {**self.observation, "tool_use_id": "unexpected"}])["ok"])

    def test_metadata_reminders_do_not_satisfy_assertions(self):
        result = self.check([{**self.observation, "content":
                             "Skill execution completed<system-reminder>SPECIFIC_FINDING DISSENT_REVISE</system-reminder>"}])
        self.assertFalse(result["ok"])

    def test_duplicate_expected_pairs_and_empty_assertions_rejected(self):
        self.manifest["expected"].append({**self.entry, "tool_use_id": "call-2"})
        with self.assertRaises(ValueError):
            self.check([])
        self.manifest["expected"] = [{**self.entry, "required_fragments": [""]}]
        with self.assertRaises(ValueError):
            self.check([])

    def test_hashed_complete_reference_and_tampering(self):
        report = self.root / "report.txt"
        report.write_text("Specific finding with preserved dissent.\n")
        entry = {k: v for k, v in self.entry.items() if k != "required_fragments"}
        entry["expected_report"] = {"file": "report.txt", "sha256": hashlib.sha256(report.read_bytes()).hexdigest()}
        self.manifest["expected"] = [entry]
        content = "Skill wrapper\nSPECIFIC FINDING WITH PRESERVED DISSENT.\nfooter"
        self.assertTrue(self.check([{**self.observation, "content": content}])["ok"])
        self.assertFalse(self.check([{**self.observation, "content": "Specific finding."}])["ok"])
        report.write_text("Changed report")
        with self.assertRaises(ValueError):
            self.check([self.observation])

    def test_paired_api_adapter_ignores_assistant_text_and_other_tool_ids(self):
        response = {"content": [{"type": "tool_use", "name": "Skill", "id": "call-1",
                                  "input": {"skill": "strategy-scope-review", "args": "RHAISTRAT-1"}}]}
        request = {"messages": [{"role": "assistant", "content": [{"type": "text", "text": self.observation["content"]}]},
                                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "unrelated",
                                                               "content": self.observation["content"]}]}]}
        (self.root / "response.json").write_text(json.dumps(response))
        (self.root / "request.json").write_text(json.dumps(request))
        (self.root / "index.jsonl").write_text(json.dumps({"request_file": "request.json", "response_file": "response.json"}) + "\n")
        self.assertFalse(self.check(delivery.read_api_channels(self.root, self.manifest))["ok"])
        request["messages"][1]["content"].append({"type": "tool_result", "tool_use_id": "call-1",
                                                 "content": self.observation["content"]})
        (self.root / "request.json").write_text(json.dumps(request))
        self.assertTrue(self.check(delivery.read_api_channels(self.root, self.manifest))["ok"])


if __name__ == "__main__":
    unittest.main()
