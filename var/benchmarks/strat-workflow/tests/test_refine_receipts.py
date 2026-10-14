"""Check that archive verification cannot confuse CLI success with recovery."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_refine_receipts import KEYS, MODEL, verify


def save(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def evidence(root):
    calls = []
    for key in KEYS:
        calls.extend([
            {"type": "tool_use", "id": key + "-skill", "name": "Skill",
             "input": {"skill": "strategy-refine", "args": key}},
            {"type": "tool_use", "id": key + "-apply", "name": "Bash",
             "input": {"command": "python3 tests/refine-receipts/fixture.py apply " + key}},
            {"type": "tool_use", "id": key + "-mark", "name": "Bash",
             "input": {"command": "python3 scripts/strat_pipeline_state.py mark refine " + key}},
        ])
        save(root, "api-dumps/" + key + ".request.json", {"model": MODEL,
             "tools": [{"name": "StructuredOutput", "input_schema": {
                 "properties": {"recorded": {"enum": [key, "none"]}}}}]})
        path = root / "artifacts/fixture-strategies" / (key + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nstrat_id: {key}\nsource_rfe: {key.replace('STRAT', 'RHAIRFE')}\n"
                        "status: Refined\nrefine_count: 1\n---\n## Strategy\nAn authored proposal.\n")
    save(root, "api-dumps/response.response.json", {"content": calls})
    save(root, "artifacts/fixture-state/strat-input.json", {"run_id": "test"})
    save(root, "artifacts/fixture-state/strat-progress.json", {
        "run_id": "test", "refine": {key: "2026-10-14T00:00:00Z" for key in KEYS}})
    save(root, "artifacts/fixture-state/refine-checkpoints/events.jsonl", {
        "allowed": True, "result": {"kind": "checkpoint",
                                     "verified": {"refined": KEYS, "rejected": []}}})
    save(root, "artifacts/native-projects/project/workflows/wf_1.json", {
        "status": "completed", "result": {"ready": KEYS, "failed": [], "injected": [{
            "key": KEYS[1], "receipt": {"recorded": json.dumps({"recorded": KEYS[1]}, separators=(",", ":"))}}]}})
    (root / "artifacts/claude-exit.txt").write_text("0\n")


class TestRefineReceiptEvidence(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        evidence(self.root)

    def test_saved_fault_recovery_passes(self):
        result = verify(self.root)
        self.assertTrue(result["passed"], result["errors"])

    def test_cli_success_does_not_hide_missing_completion(self):
        save(self.root, "artifacts/fixture-state/strat-progress.json", {"run_id": "test", "refine": {}})
        self.assertFalse(verify(self.root)["passed"])

    def test_repeated_work_is_not_receipt_recovery(self):
        path = self.root / "api-dumps/response.response.json"
        response = json.loads(path.read_text())
        repeated = dict(response["content"][1], id="repeated-work")
        response["content"].append(repeated)
        path.write_text(json.dumps(response))
        self.assertFalse(verify(self.root)["passed"])

    def test_simply_omitting_the_fault_cannot_pass(self):
        path = self.root / "artifacts/native-projects/project/workflows/wf_1.json"
        state = json.loads(path.read_text())
        state["result"]["injected"] = []
        path.write_text(json.dumps(state))
        self.assertFalse(verify(self.root)["passed"])


if __name__ == "__main__":
    unittest.main()
