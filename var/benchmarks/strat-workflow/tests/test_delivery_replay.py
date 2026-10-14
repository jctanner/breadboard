"""Historical evaluations are inputs, never overwritten by a stricter replay."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import replay_delivery_gate as replay
from test_batch import reviewer_bodies


class ReplayTests(unittest.TestCase):
    def fixture(self, root, progress=False):
        api = root / "api-dumps"
        api.mkdir(parents=True)
        (root / "artifacts").mkdir()
        bodies = reviewer_bodies(["RHAISTRAT-1"])
        if progress:
            bodies[1]["messages"][1]["content"][-1]["content"] = (
                'Skill "strategy-architecture-review" completed (forked execution).\n\nResult: '
                "I've launched four research agents. I'll wait before assembling the architecture review.")
        (api / "one.request.json").write_text(json.dumps(bodies[1]))
        (api / "one.response.json").write_text(json.dumps(bodies[0]))
        original_gate = {"ok": True, "detail": {"by_strategy": {
            "RHAISTRAT-1": {role: {"returned": True} for role in replay.REVIEWER_SKILLS.values()}}}}
        evaluation = {"job": "authored-job", "strategies": ["RHAISTRAT-1"], "pass": True,
                      "failed_checks": [], "checks": {"reviewer_outputs_returned": original_gate}}
        (root / "artifacts/eval-result.json").write_text(json.dumps(evaluation))
        return evaluation

    def test_recomputed_failure_preserves_original_pass_and_input_bytes(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "job"
            original = self.fixture(root, progress=True)
            before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*.json")}
            result = replay.replay(root)
            self.assertTrue(result["original_pass"])
            self.assertEqual(result["original_gate"], original["checks"]["reviewer_outputs_returned"])
            self.assertFalse(result["recomputed_gate"]["ok"])
            self.assertEqual([p["role"] for p in result["pairs"] if p["changed"]], ["architecture"])
            self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*.json")})

    def test_missing_launches_cannot_reduce_expected_inventory(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "job"
            evaluation = self.fixture(root)
            evaluation["strategies"].append("RHAISTRAT-2")
            (root / "artifacts/eval-result.json").write_text(json.dumps(evaluation))
            result = replay.replay(root)
            self.assertEqual(len(result["pairs"]), 8)
            self.assertFalse(result["recomputed_gate"]["ok"])

    def test_no_evaluation_requires_independent_expected_keys(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "job"
            self.fixture(root)
            (root / "artifacts/eval-result.json").unlink()
            with self.assertRaisesRegex(ValueError, "expected strategies"):
                replay.replay(root)
            result = replay.replay(root, ["RHAISTRAT-1"])
            self.assertIsNone(result["original_gate"])
            self.assertEqual(result["expectation_source"], "explicit strategies")
            self.assertTrue(result["recomputed_gate"]["ok"])

    def test_cli_output_must_be_new_and_outside_original_capture(self):
        with tempfile.TemporaryDirectory() as scratch:
            capture = Path(scratch) / "capture"
            root = capture / "jobs/job"
            self.fixture(root)
            (capture / "manifest.json").write_text("{}")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(replay.main([str(root), "--output", str(capture / "new.json")]), 2)
            self.assertFalse((capture / "new.json").exists())
            output = Path(scratch) / "recomputed.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(replay.main([str(root), "--output", str(output)]), 0)
            before = output.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(replay.main([str(root), "--output", str(output)]), 2)
            self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
