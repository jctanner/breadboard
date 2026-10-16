"""Exercise the supervisor with local Python processes, never Claude."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH / "scripts"))


class WatchTests(unittest.TestCase):
    def execute(self, status, timeout=10, exit_code=0, previous=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "repository"
            report = root / "failure.json"
            config = root / "config"
            env = {**os.environ, "CLAUDE_CONFIG_DIR": str(config)}
            slug = "".join(c if c.isascii() and c.isalnum() else "-" for c in str(repository))
            state = config / "projects" / slug / "session/workflows/wf_test.json"
            value = {"runId": "wf_test", "workflowName": "strat-pipeline", "status": status}
            if previous:
                state.parent.mkdir(parents=True)
                state.write_text(json.dumps(value))
            code = ("import json,pathlib,sys,time; p=pathlib.Path(sys.argv[1]); p.parent.mkdir(parents=True,exist_ok=True); "
                    "p.write_text(sys.argv[2]); time.sleep(float(sys.argv[3])); "
                    "pathlib.Path(sys.argv[4]).write_text('parent would repair'); sys.exit(int(sys.argv[5]))")
            sleep = 10 if status == "failed" and not previous else (3 if status == "running" else 0.3)
            started = time.monotonic()
            result = subprocess.run([sys.executable, str(BENCH / "scripts/watch_workflow.py"),
                "--repository", str(repository), "--report", str(report), "--timeout", str(timeout),
                "--", sys.executable, "-c", code, str(state), json.dumps(value), str(sleep),
                str(root / "repair"), str(exit_code)], env=env, capture_output=True, text=True, timeout=20, check=False)
            return result, json.loads(report.read_text()) if report.exists() else None, (root / "repair").exists(), time.monotonic() - started

    def test_failed_native_workflow_stops_before_parent_repairs(self):
        result, report, repaired, elapsed = self.execute("failed")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report["reason"], "native_workflow_failed")
        self.assertEqual(report["workflow"]["runId"], "wf_test")
        self.assertFalse(repaired)
        self.assertLess(elapsed, 5)

    def test_completed_workflow_keeps_normal_exit(self):
        result, report, repaired, _ = self.execute("completed")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(report)
        self.assertTrue(repaired)

    def test_cli_failure_is_not_retried(self):
        result, report, _, _ = self.execute("completed", exit_code=7)
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertIsNone(report)

    def test_timeout_stops_without_parent_repair(self):
        result, report, repaired, _ = self.execute("running", timeout=0.6)
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertEqual(report["reason"], "timeout")
        self.assertFalse(repaired)

    def test_previous_failed_journal_does_not_stop_new_process(self):
        result, report, _, _ = self.execute("failed", previous=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(report)
