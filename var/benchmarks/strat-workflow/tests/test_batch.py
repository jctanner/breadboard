"""Offline checks. Run with .venv/bin/python -m unittest discover -s .../tests.

Set MARKOV_BIN to a current Markov binary to also exercise the real workflow
expressions in an isolated copy. All service steps are replaced by local facts.
"""
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH / "scripts"))
import check_run
import seed_scenario


def jira_fixture(count=3):
    issues = {}
    for index in range(1, count + 1):
        rfe, strat = f"RHAIRFE-{index}", f"RHAISTRAT-{index}"
        issues[rfe] = {"key": rfe, "fields": {"labels": [], "issuelinks": [{"outwardIssue": {"key": strat}}]}}
        issues[strat] = {"key": strat, "fields": {
            "labels": ["strat-creator-auto-created", "strat-creator-auto-refined", "strat-creator-rubric-pass"],
            "description": "Refined strategy", "comment": {"comments": [
                {"body": "[Strat Creator] Strategy Review — Approve (Score: 7/8)\nReview text"}]}}}
    return issues


def fake_jira(issues):
    def get(path):
        if path.startswith("/rest/api/2/search"):
            return {"issues": [{"key": key} for key in issues if key.startswith("RHAISTRAT-")]}
        key = path.split("/issue/")[1].split("?")[0]
        return copy.deepcopy(issues[key])
    return get


def seed(count=3):
    keys = [f"RHAIRFE-{index}" for index in range(1, count + 1)]
    return {"ok": True, "rfes": [{"key": key, "eligible": True} for key in keys],
            "discovered": keys, "discovered_in_order": list(reversed(keys))}


def reviewer_bodies(keys, empty=False):
    uses, results = [], []
    for key in keys:
        for skill in check_run.REVIEWER_SKILLS:
            tool_id = f"{key}-{skill}"
            uses.append({"type": "tool_use", "name": "Skill", "id": tool_id,
                         "input": {"skill": skill, "args": key}})
            results.append({"type": "tool_result", "tool_use_id": tool_id,
                            "content": f'Skill "{skill}" completed (forked execution).\n\nResult: '
                                       + ("Skill execution completed" if empty else f"## Review of {key}\nApprove")})
    response = {"type": "message", "content": uses}
    request = {"messages": [{"role": "assistant", "content": uses}, {"role": "user", "content": results}]}
    return [response, request, request]  # repeated history must not count as reruns


class OutcomeTests(unittest.TestCase):
    def evaluate(self, issues):
        with patch.object(check_run, "jira", fake_jira(issues)):
            return check_run.batch_jira_checks(seed(), 3)

    def test_complete_batch_and_single_compatibility(self):
        checks, facts = self.evaluate(jira_fixture())
        self.assertTrue(all(row["ok"] for row in checks.values()))
        self.assertEqual(len(facts["items"]), 3)
        with patch.object(check_run, "jira", fake_jira(jira_fixture(1))):
            checks, facts = check_run.jira_checks("RHAIRFE-1")
        self.assertTrue(all(row["ok"] for row in checks.values()))
        self.assertEqual(facts["verdict"], "approve")

    def test_deduplicated_strategy_fails(self):
        issues = jira_fixture()
        issues["RHAIRFE-2"]["fields"]["issuelinks"] = issues["RHAIRFE-1"]["fields"]["issuelinks"]
        checks, _ = self.evaluate(issues)
        self.assertFalse(checks["batch_complete"]["ok"])

    def test_missing_strategy_fails(self):
        issues = jira_fixture()
        issues["RHAIRFE-3"]["fields"]["issuelinks"] = []
        del issues["RHAISTRAT-3"]
        checks, _ = self.evaluate(issues)
        self.assertFalse(checks["batch_complete"]["ok"])
        self.assertFalse(checks["steps_done"]["ok"])

    def test_locks_and_review_mismatch_on_later_item(self):
        issues = jira_fixture()
        issues["RHAIRFE-3"]["fields"]["labels"] = [check_run.LOCK_LABEL]
        issues["RHAISTRAT-2"]["fields"]["comment"]["comments"][0]["body"] = (
            "[Strat Creator] Strategy Review — Revise (Score: 5/8)")
        checks, _ = self.evaluate(issues)
        self.assertFalse(checks["locks_released"]["ok"])
        self.assertFalse(checks["records_agree"]["ok"])

    def test_duplicate_reviews_fail(self):
        issues = jira_fixture()
        comments = issues["RHAISTRAT-3"]["fields"]["comment"]["comments"]
        comments.append(comments[0])
        checks, _ = self.evaluate(issues)
        self.assertFalse(checks["one_review"]["ok"])

    def test_returns_are_matched_by_id_not_history_or_ack(self):
        keys = ["RHAISTRAT-1", "RHAISTRAT-2", "RHAISTRAT-3"]
        result = check_run.reviewer_returns(reviewer_bodies(keys), keys)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["detail"]["launches"]), 12)
        self.assertFalse(check_run.reviewer_returns(reviewer_bodies(keys, empty=True), keys)["ok"])
        self.assertFalse(check_run.reviewer_returns(reviewer_bodies(keys[:2]), keys)["ok"])

    def test_failed_job_and_wrong_helper_model_emit_failures(self):
        run = {"id": "r1-S1-haiku", "tier": "tier2-smoke", "test": "S1", "arm": "workflow",
               "variant": "haiku", "model": "claude-haiku-5-5", "repeat": 1,
               "scenario": "batch-three-new-rfes", "strat_creator_ref": "a" * 40,
               "breadboard_ref": "b" * 40, "mlflow_experiment": "test", "mode": "batch", "batch_size": 3}
        bodies = reviewer_bodies([f"RHAISTRAT-{i}" for i in range(1, 4)])
        bodies.append({"model": "claude-opus-4-6", "messages": []})
        with patch.object(check_run, "jira", fake_jira(jira_fixture())), \
                patch.object(check_run, "dashboard", return_value=(200, {"status": "failed"})), \
                patch.object(check_run, "api_usage", return_value={"by_model": {"claude-haiku-5-5": {}}}), \
                patch.object(check_run, "api_bodies", return_value=bodies), \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(check_run.main([json.dumps(run), "fake-job", "batch-discover", "failed", json.dumps(seed())]), 0)
            result = json.loads(output.getvalue())
        self.assertFalse(result["pass"])
        self.assertIn("finished", result["failed_checks"])
        self.assertIn("haiku_only", result["failed_checks"])
        self.assertEqual(len(result["items"]), 3)

    def test_fixtures_and_exact_discovery(self):
        scenario, templates = seed_scenario.load_scenario("batch-three-new-rfes")
        self.assertEqual(len(scenario["rfes"]), 3)
        self.assertEqual(len(templates), 3)
        self.assertTrue(all("h2. Acceptance Criteria" in t["description"] for t in templates.values()))
        self.assertEqual(seed_scenario.discovery_problems(seed()["rfes"], seed()["discovered"]), [])
        self.assertTrue(seed_scenario.discovery_problems(seed()["rfes"], ["RHAIRFE-1", "RHAIRFE-2", "RHAIRFE-9"]))
        self.assertEqual(len(seed_scenario.load_scenario("smoke-one-rfe")[0]["rfes"]), 1)

    def test_opus_batch_model_gate_accepts_opus_and_rejects_haiku_helpers(self):
        run = {"id": "r1-S1-opus", "tier": "tier2-opus", "test": "S1", "arm": "workflow",
               "variant": "opus", "model": "claude-opus-4-6", "repeat": 1,
               "scenario": "batch-three-new-rfes", "strat_creator_ref": "a" * 40,
               "breadboard_ref": "b" * 40, "mlflow_experiment": "test", "mode": "batch", "batch_size": 3}
        for model, expected in (("claude-opus-4-6", True), ("claude-haiku-5-5", False)):
            bodies = reviewer_bodies([f"RHAISTRAT-{i}" for i in range(1, 4)])
            bodies.append({"model": model, "messages": []})
            with self.subTest(model=model), patch.object(check_run, "jira", fake_jira(jira_fixture())), \
                    patch.object(check_run, "dashboard", return_value=(200, {"status": "completed"})), \
                    patch.object(check_run, "api_usage", return_value={"by_model": {"claude-opus-4-6": {}}}), \
                    patch.object(check_run, "api_bodies", return_value=bodies), \
                    patch("sys.stdout", new_callable=io.StringIO) as output:
                check_run.main([json.dumps(run), "fake-job", "batch-discover", "completed", json.dumps(seed())])
                result = json.loads(output.getvalue())
            self.assertEqual(result["checks"]["model_matches"]["ok"], expected)
            self.assertEqual(result["pass"], expected)


@unittest.skipUnless(os.environ.get("MARKOV_BIN"), "set MARKOV_BIN for offline orchestration checks")
class WorkflowTests(unittest.TestCase):
    def simulate(self, overrides, count=3):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "benchmark"
            shutil.copytree(BENCH, root)
            # Replace every service interaction in the copy. No HTTP or K8s
            # executor remains, and no design/model/seed script is executed.
            for path in (root / "workflows").glob("*.yaml"):
                workflow = yaml.safe_load(path.read_text())
                steps = []
                for step in workflow["steps"]:
                    name = step["name"]
                    facts = None
                    if step.get("type") == "dashboard_api":
                        if name in ("list_running_jobs", "list_pending_jobs"):
                            facts = {step["register"]: {"body": []}}
                        elif name == "submit_seed":
                            facts = {"seed_job": {"body": {"job_name": "offline-seed"}}}
                        elif name == "read_seed_report":
                            facts = {"seed_file": {"body": {"content": json.dumps(seed(count))}}}
                        elif name == "submit_job":
                            facts = {"job": {"body": {"job_name": "offline-" + workflow["name"]}},
                                     "captured_request": step["params"]["body"]}
                        else:
                            facts = {"unused_service_step": name}
                    elif step.get("type") == "job_wait":
                        facts = {step.get("register", "seed_wait"): {"status": "completed", "failed": False}}
                    elif name == "check":
                        facts = {"eval": {"stdout": "{{ run | to_json }}"}}
                    elif name.startswith("require_archives_before_"):
                        facts = {"offline_archive_gate": True}
                    elif name == "wipe":
                        facts = {"offline_wipe": True}
                    if facts is not None:
                        steps.append({"name": name, "type": "set_fact", "vars": facts,
                                      **({"when": step["when"]} if "when" in step else {})})
                        if name == "submit_job":
                            steps.append({"name": "verify_request", "type": "assert", "that": [
                                "captured_request.script.args.0 == rfe_key",
                                "captured_request.args.model == models[variant]",
                                "captured_request.args.extra_env.BATCH_SIZE == run.batch_size",
                                "captured_request.args.extra_env.BATCH_EXPECTED_KEYS == batch_expected_keys"]})
                            if workflow["name"] == "submit-workflow":
                                steps[-1]["that"].append("captured_request.args.extra_env.STRAT_BG_WAIT_CEILING_MS == workflow_bg_wait_ceiling_ms")
                    else:
                        steps.append(step)
                # The fake eval used above needs summary fields, and checking
                # real arguments/seed shape happens before this stub.
                if workflow["name"] == "run-test":
                    steps[next(i for i, s in enumerate(steps) if s["name"] == "check")]["vars"]["eval"]["stdout"] = (
                        '{"run":"{{ run.id }}","tier":"{{ tier }}","test":"{{ test.id }}",'
                        '"arm":"{{ test.arm }}","variant":"{{ variant }}","repeat":{{ round }},'
                        '"pass":true,"job":"{{ job_name }}","mode":"{{ run.mode }}",'
                        '"batch_size":{{ run.batch_size }},"selector":"{{ rfe_key }}",'
                        '"expected_keys":"{{ batch_expected_keys }}"}')
                workflow["steps"] = steps
                path.write_text(yaml.safe_dump(workflow, sort_keys=False))
            (root / "step_types" / "dashboard.yaml").unlink()
            (root / "workflows" / "wipe.yaml").unlink()
            variables = {"breadboard_ref": "b" * 40, "tier": "tier2-smoke", "only_tests": "S1",
                         "wipe_at_start": False, "artifacts_dir": str(Path(scratch) / "artifacts"), **overrides}
            command = [os.environ["MARKOV_BIN"], "run", str(root), "--state-store", str(Path(scratch) / "state.db")]
            for key, value in variables.items():
                command += ["--var", f"{key}={str(value).lower() if isinstance(value, bool) else value}"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            reports = list((Path(scratch) / "artifacts" / "benchmarks").glob("**/eval-results.json"))
            return result, json.loads(reports[0].read_text()) if reports else None

    def test_only_one_selected_batch_design(self):
        for test in ("S1", "S2"):
            with self.subTest(test=test):
                result, rows = self.simulate({"only_tests": test})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["test"], test)
                self.assertEqual(rows[0]["selector"], "batch-discover")
                self.assertEqual(rows[0]["batch_size"], 3)
                self.assertEqual(rows[0]["expected_keys"], "RHAIRFE-3 RHAIRFE-2 RHAIRFE-1")

    def test_reject_implicit_sweep_repeats_opus_or_wipe(self):
        for overrides in ({"only_tests": ""}, {"only_tests": "S1,S2"}, {"only_tests": "S3"},
                          {"repeats": 3}, {"repeats": 0}, {"variants": "opus"},
                          {"variants": "haiku,opus"}, {"wipe_at_start": True}):
            with self.subTest(overrides=overrides):
                result, rows = self.simulate(overrides)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Tier 2 needs", result.stderr)
                self.assertNotIn('step "submit_seed"', result.stderr)
                self.assertIsNone(rows)

    def test_opus_batch_is_single_selected_run(self):
        settings = {"tier": "tier2-opus", "variants": "opus", "repeats": 1,
                    "workflow_bg_wait_ceiling_ms": 5400000}
        result, rows = self.simulate(settings)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["test"], rows[0]["variant"], rows[0]["batch_size"]), ("S1", "opus", 3))
        for override in ({"only_tests": "S1,S2"}, {"variants": "haiku"}, {"repeats": 3}):
            result, rows = self.simulate({**settings, **override})
            self.assertNotEqual(result.returncode, 0)
            self.assertIsNone(rows)

    def test_seed_count_mismatch_stops_before_design(self):
        result, rows = self.simulate({}, count=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failed its check", result.stderr)
        self.assertNotIn('step "submit_job"', result.stderr)
        self.assertIsNone(rows)

    def test_tier_one_selection_and_defaults_survive(self):
        result, rows = self.simulate({"tier": "smoke", "only_tests": "S1,S2", "repeats": 1}, count=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([row["test"] for row in rows], ["S1", "S2"])
        self.assertTrue(all(row["selector"] == "RHAIRFE-1" and row["batch_size"] == 1 for row in rows))
        result, rows = self.simulate({"tier": "smoke", "only_tests": ""}, count=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["test"] for row in rows}, {"S1", "S2", "S3", "S4"})


if __name__ == "__main__":
    unittest.main()
