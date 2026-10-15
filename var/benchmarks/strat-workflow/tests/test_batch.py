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
                                       + ("Skill execution completed" if empty else valid_report(key, check_run.REVIEWER_SKILLS[skill]))})
    response = {"type": "message", "content": uses}
    request = {"messages": [{"role": "assistant", "content": uses}, {"role": "user", "content": results}]}
    return [response, request, request]  # repeated history must not count as reruns


def valid_report(key, role):
    judgment = {"feasibility": "**Feasibility**: feasible",
                "testability": "**Testability**: testable",
                "scope": "**Scope assessment**: right-sized",
                "architecture": "**Architecture assessment**: sound"}[role]
    return f"### {key}: Routing timeouts\n{judgment}. The gateway owns cancellation and timeout handling.\n**Recommendation**: approve"


class OutcomeTests(unittest.TestCase):
    def evaluate(self, issues, count=3):
        with patch.object(check_run, "jira", fake_jira(issues)):
            return check_run.batch_jira_checks(seed(count), count)

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

    def test_full_batch_checks_tenth_ticket_and_all_forty_reports(self):
        issues = jira_fixture(10)
        checks, facts = self.evaluate(issues, count=10)
        self.assertTrue(all(row["ok"] for row in checks.values()))
        self.assertEqual(len(facts["items"]), 10)
        keys = [f"RHAISTRAT-{i}" for i in range(1, 11)]
        bodies = reviewer_bodies(keys)
        returns = check_run.reviewer_returns(bodies, keys)
        self.assertTrue(returns["ok"])
        self.assertEqual(len(returns["detail"]["launches"]), 40)
        # Repeated parent history must not conceal a missing fortieth report.
        bodies[1]["messages"][1]["content"].pop()
        self.assertFalse(check_run.reviewer_returns(bodies, keys)["ok"])
        issues["RHAIRFE-10"]["fields"]["issuelinks"] = []
        del issues["RHAISTRAT-10"]
        checks, _ = self.evaluate(issues, count=10)
        self.assertFalse(checks["batch_complete"]["ok"])
        self.assertFalse(checks["steps_done"]["ok"])

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

    def test_glm_response_spelling_requires_exact_request_and_rejects_other_helpers(self):
        model = check_run.GLM_MODEL
        good = {"request_models": [model], "by_model": {"zai-org/GLM-5.3": {}}}
        self.assertTrue(check_run.model_identity_check(model, good)["ok"])
        self.assertFalse(check_run.model_identity_check(model, good, ["claude-opus-4-6"])["ok"])
        self.assertFalse(check_run.model_identity_check(model, {**good, "request_models": []})["ok"])
        self.assertFalse(check_run.model_identity_check(model, {**good, "request_models": [model, "claude-haiku-5-5"]})["ok"])
        self.assertFalse(check_run.model_identity_check(model, {**good, "by_model": {"unknown": {}}})["ok"])
        self.assertFalse(check_run.model_identity_check(model, {**good, "by_model": {}})["ok"])

    def test_glm_single_rfe_emits_model_gate(self):
        run = {"id":"r1-S1-glm", "tier":"glm-smoke", "test":"S1", "arm":"workflow",
               "variant":"glm", "model":check_run.GLM_MODEL, "repeat":1,
               "scenario":"smoke-one-rfe", "strat_creator_ref":"a"*40,
               "breadboard_ref":"b"*40, "mlflow_experiment":"test", "mode":"single"}
        with patch.object(check_run,"jira",fake_jira(jira_fixture(1))), \
                patch.object(check_run,"dashboard",return_value=(200,{"status":"completed"})), \
                patch.object(check_run,"api_usage",return_value={"request_models":[check_run.GLM_MODEL],"by_model":{"zai-org/GLM-5.3":{}}}), \
                patch("sys.stdout",new_callable=io.StringIO) as output:
            check_run.main([json.dumps(run),"fake-job","RHAIRFE-1","completed"])
        result=json.loads(output.getvalue())
        self.assertTrue(result["checks"]["model_matches"]["ok"])
        self.assertTrue(result["pass"])

    def test_fixtures_and_exact_discovery(self):
        scenario, templates = seed_scenario.load_scenario("batch-three-new-rfes")
        self.assertEqual(len(scenario["rfes"]), 3)
        self.assertEqual(len(templates), 3)
        self.assertTrue(all("h2. Acceptance Criteria" in t["description"] for t in templates.values()))
        self.assertEqual(seed_scenario.discovery_problems(seed()["rfes"], seed()["discovered"]), [])
        self.assertTrue(seed_scenario.discovery_problems(seed()["rfes"], ["RHAIRFE-1", "RHAIRFE-2", "RHAIRFE-9"]))
        self.assertEqual(len(seed_scenario.load_scenario("smoke-one-rfe")[0]["rfes"]), 1)

    def test_ten_distinct_complete_rfes_and_exact_discovery(self):
        scenario, templates = seed_scenario.load_scenario("batch-ten-new-rfes")
        self.assertEqual(scenario["expected_batch_size"], 10)
        self.assertEqual(len(scenario["rfes"]), 10)
        self.assertTrue(all(rfe["eligible"] for rfe in scenario["rfes"]))
        self.assertEqual(len(templates), 10)
        self.assertEqual(len({t["summary"] for t in templates.values()}), 10)
        self.assertEqual(len({t["description"] for t in templates.values()}), 10)
        for template in templates.values():
            for section in ("Problem Statement", "Desired Outcome", "Acceptance Criteria", "User Stories", "Technical Notes"):
                self.assertIn("h2. " + section, template["description"])
        fixture = seed(10)
        self.assertEqual(seed_scenario.discovery_problems(fixture["rfes"], fixture["discovered"]), [])
        self.assertTrue(seed_scenario.discovery_problems(fixture["rfes"], fixture["discovered"][:-1]))

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
                            facts = {"seed_job": {"body": {"job_name": "offline-seed"}},
                                     "captured_seed_request": step["params"]["body"]}
                        elif name == "read_seed_report":
                            facts = {"seed_file": {"body": {"content": json.dumps(seed(count))}}}
                        elif name in ("submit_job", "submit_glm_job"):
                            facts = {"job": {"body": {"job_name": "offline-" + workflow["name"]}},
                                     "captured_request": step["params"]["body"]}
                        elif name == "submit_wiring_check":
                            facts = {"wiring_job": {"body": {"job_name": "offline-wiring"}}}
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
                        if name == "submit_seed":
                            steps.append({"name": "verify_seed_source", "type": "assert", "that": [
                                "captured_seed_request.script.args.3 == run.strat_creator_ref",
                                "captured_seed_request.args.extra_env.STRAT_CREATOR_REPO == run.strat_creator_repo"]})
                        if name in ("submit_job", "submit_glm_job"):
                            steps.append({"name": "verify_request_" + name, "type": "assert", "that": [
                                "captured_request.script.args.0 == rfe_key",
                                "captured_request.args.model == models[variant]",
                                "captured_request.args.extra_env.BATCH_SIZE == run.batch_size",
                                "captured_request.args.extra_env.BATCH_EXPECTED_KEYS == batch_expected_keys"],
                                **({"when": step["when"]} if "when" in step else {})})
                            if name == "submit_glm_job":
                                steps[-1]["that"] += [
                                    "captured_request.args.extra_env.CLAUDE_CODE_SUBAGENT_MODEL == models.glm",
                                    "captured_request.args.extra_env.ANTHROPIC_DEFAULT_HAIKU_MODEL == models.glm",
                                    "captured_request.args.extra_env.CLAUDE_CODE_EFFORT_LEVEL == 'medium'",
                                    "captured_request.args.extra_env.STRAT_EFFORT == 'medium'"]
                            if workflow["name"] == "submit-workflow":
                                steps[-1]["that"].append("captured_request.args.extra_env.STRAT_BG_WAIT_CEILING_MS == workflow_bg_wait_ceiling_ms")
                                steps[-1]["that"].append("captured_request.args.extra_env.STRAT_CREATOR_REF == run.strat_creator_ref")
                                steps[-1]["that"].append("captured_request.args.extra_env.STRAT_CREATOR_REPO == run.strat_creator_repo")
                                steps[-1]["that"].append("captured_request.args.extra_env.CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS == run.workflow_max_concurrent_agents")
                                if overrides.get("tier", "").startswith("s1-hardening-"):
                                    steps[-1]["that"] += [
                                        "captured_request.args.extra_env.CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS == 10",
                                        "captured_request.args.extra_env.STRAT_TIMEOUT_MINUTES == 295",
                                        "captured_request.args.extra_env.STRAT_CAPTURE_NATIVE == '1'"]
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
                        '"expected_keys":"{{ batch_expected_keys }}",'
                        '"strat_creator_repo":"{{ run.strat_creator_repo }}",'
                        '"strat_creator_ref":"{{ run.strat_creator_ref }}",'
                        '"workflow_max_concurrent_agents":"{{ run.workflow_max_concurrent_agents }}"}')
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
                self.assertIn("Single-run tier needs", result.stderr)
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

    def test_glm_one_rfe_one_iteration_each_arm_with_explicit_env(self):
        for arm in ("S1", "S2"):
            settings={"tier":"glm-smoke", "variants":"glm", "only_tests":arm, "repeats":1}
            result,rows=self.simulate(settings,count=1)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(len(rows),1)
            self.assertEqual((rows[0]["test"],rows[0]["variant"],rows[0]["batch_size"]),(arm,"glm",1))
            for invalid in ({"only_tests":"S1,S2"},{"repeats":3},{"variants":"opus"},{"wipe_at_start":True}):
                result,rows=self.simulate({**settings,**invalid},count=1)
                self.assertNotEqual(result.returncode,0)
                self.assertIsNone(rows)

    def test_seed_count_mismatch_stops_before_design(self):
        result, rows = self.simulate({}, count=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failed its check", result.stderr)
        self.assertNotIn('step "submit_job"', result.stderr)
        self.assertIsNone(rows)

    def test_hardened_ten_ticket_tiers_pin_candidate_and_reject_other_designs(self):
        candidate = "6a05210215247b287bb0fb61ed02e423c9de8692"
        repository = "https://github.com/jctanner-fullsend-ai/strat-creator.git"
        for variant in ("glm", "opus"):
            settings = {"tier": "s1-hardening-" + variant, "variants": variant, "repeats": 1}
            result, rows = self.simulate(settings, count=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(rows), 1)
            self.assertEqual((rows[0]["test"], rows[0]["variant"], rows[0]["batch_size"]), ("S1", variant, 10))
            self.assertEqual(rows[0]["selector"], "batch-discover")
            self.assertEqual(rows[0]["expected_keys"], " ".join(f"RHAIRFE-{i}" for i in range(10, 0, -1)))
            self.assertEqual(rows[0]["strat_creator_ref"], candidate)
            self.assertEqual(rows[0]["strat_creator_repo"], repository)
            self.assertEqual(rows[0]["workflow_max_concurrent_agents"], "10")
            for invalid in ({"only_tests": "S2"}, {"only_tests": "S1,S2"},
                            {"repeats": 3}, {"variants": "haiku"}, {"wipe_at_start": True}):
                result, rows = self.simulate({**settings, **invalid}, count=10)
                self.assertNotEqual(result.returncode, 0, result.stderr)
                self.assertIsNone(rows)

    def test_full_batch_rejects_nine_discovered_rfes_before_model_submission(self):
        result, rows = self.simulate({"tier": "s1-hardening-glm", "variants": "glm"}, count=9)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failed its check", result.stderr)
        self.assertNotIn('step "submit_glm_job"', result.stderr)
        self.assertIsNone(rows)

    def test_tier_one_selection_and_defaults_survive(self):
        result, rows = self.simulate({"tier": "smoke", "only_tests": "S1,S2", "repeats": 1}, count=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([row["test"] for row in rows], ["S1", "S2"])
        self.assertTrue(all(row["selector"] == "RHAIRFE-1" and row["batch_size"] == 1 for row in rows))
        self.assertTrue(all(row["strat_creator_repo"].startswith("https://github.local/") for row in rows))
        self.assertEqual(rows[0]["strat_creator_ref"], "1bd7f1718c7ed10f2900691c0e9eaea2b8e48e43")
        self.assertEqual(rows[1]["strat_creator_ref"], "0287b838d2bc59a2569cf2dd971aad7ad2d76dad")
        result, rows = self.simulate({"tier": "smoke", "only_tests": ""}, count=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(rows), 12)
        self.assertEqual({row["test"] for row in rows}, {"S1", "S2", "S3", "S4"})


if __name__ == "__main__":
    unittest.main()
