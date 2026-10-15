"""Mixed-state contracts; optional real emulator preparation, with no inference."""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH / "scripts"))
import mixed_state as mixed
import seed_scenario


def authored_case():
    scenario, _ = seed_scenario.load_scenario("batch-mixed-state")
    rows, before = [], {}

    def issue(labels=None):
        return {"summary": "Subject", "description": "Existing strategy", "priority": {"name": "Major"},
                "status": "New", "labels": sorted(labels or []), "links": [],
                "comments": [{"id": "input", "body": "Preserve"}],
                "attachments": [{"id": "sentinel", "filename": "sentinel.txt"}]}

    counter = 0
    for number, item in enumerate(scenario["rfes"], 1):
        row = {**item, "key": f"RHAIRFE-{number}"}
        before[row["key"]] = issue(item.get("labels"))
        if item.get("strat"):
            counter += 1
            row["strat_key"] = key = f"RHAISTRAT-{counter}"
            before[key] = issue(["strat-creator-auto-created", *item["strat"].get("labels", [])])
            before[row["key"]]["links"] = [{"type": "Cloners", "inwardIssue": key}]
        rows.append(row)
    pool = sorted(r["key"] for r in rows if r["action"] != "untouched")
    selected = pool[:10]
    by_key = {r["key"]: r for r in rows}
    acquired = [k for k in selected if by_key[k]["action"] != "late-skip"]
    points = {k: by_key[k]["action"] for k in acquired}
    seed = {"kind": mixed.KIND, "ok": True, "rfes": rows, "before": before,
            "discovered_in_order": selected, "discovered": sorted(selected),
            "expected_acquired_keys": acquired, "expected_resume_points": points,
            "expected_preparation_skips": [k for k in selected if k not in acquired],
            "deferred_keys": [k for k in pool if k not in selected]}
    prepared = {"freshness": {"contract": "strat-freshness-v1"}, "input_keys": selected,
                "acquired_keys": acquired, "resume_points": points,
                "skipped": [{"key": k} for k in seed["expected_preparation_skips"]],
                "expected_skips": [], "reused_push": {k: {} for k in acquired if points[k] == "review"}}
    progress = {"refine": {}, "push": {"strategies": []}}
    after = copy.deepcopy(before)
    for index, rfe in enumerate(acquired, counter + 1):
        row = by_key[rfe]
        key = row.get("strat_key") or f"RHAISTRAT-{index}"
        if key not in after:
            after[key] = issue(["strat-creator-auto-created"])
            after[rfe]["links"] = [{"type": "Cloners", "inwardIssue": key}]
        after[key]["labels"] = sorted(["strat-creator-auto-created", "strat-creator-auto-refined", "strat-creator-rubric-pass"])
        after[key]["comments"].append({"id": "review", "body": "[Strat Creator] Strategy Review - Approve (Score: 7/8)"})
        after[key]["attachments"].append({"id": "review", "filename": f"{key}-review.md"})
        if row["action"] != "review":
            progress["refine"][key] = "recorded"
            progress["push"]["strategies"].append(key)
    return seed, after, prepared, progress


class MixedTests(unittest.TestCase):
    def test_inventory_and_distinct_work(self):
        scenario, templates = seed_scenario.load_scenario("batch-mixed-state")
        mixed.validate(scenario)
        self.assertEqual(len(scenario["rfes"]), 18)
        self.assertEqual(len(templates), 10)
        self.assertEqual(sum(bool(r.get("strat")) for r in scenario["rfes"]), 11)
        for invalid in ("count", "order", "body", "duplicate"):
            bad = copy.deepcopy(scenario)
            if invalid == "count": bad["expected_initial_issues"] -= 1
            if invalid == "order": bad["rfes"].reverse()
            if invalid == "body": bad["rfes"][0]["strat"]["strategy"] = ""
            if invalid == "duplicate": bad["rfes"][2]["template"] = bad["rfes"][3]["template"]
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                mixed.validate(bad)

    def test_ten_candidates_nine_owned_and_one_deferred(self):
        seed, after, prepared, progress = authored_case()
        result = mixed.assess(seed, after, prepared, progress)
        self.assertTrue(result["ok"], result)
        self.assertEqual((result["candidate_count"], result["acquired_count"]), (10, 9))
        self.assertEqual(result["deferred_keys"], ["RHAIRFE-9"])
        self.assertEqual(len(result["new_strategies"]), 4)

    def test_preparation_mismatch_fails_before_inference(self):
        seed, _, prepared, _ = authored_case()
        for field in ("input_keys", "acquired_keys", "resume_points", "skipped", "reused_push"):
            bad = copy.deepcopy(prepared)
            bad[field] = {} if isinstance(bad[field], dict) else []
            self.assertFalse(all(mixed.preparation_checks(seed, bad).values()), field)

    def test_mutating_any_control_or_deferred_ticket_fails(self):
        seed, after, prepared, progress = authored_case()
        controls = set(seed["before"]) - set(seed["expected_acquired_keys"]) - {
            row["strat_key"] for row in seed["rfes"] if row["key"] in seed["expected_acquired_keys"] and row.get("strat_key")}
        for key in controls:
            changed = copy.deepcopy(after)
            changed[key]["comments"].append({"id": "oops", "body": "Unexpected"})
            self.assertFalse(mixed.assess(seed, changed, prepared, progress)["checks"]["untouched_controls_and_deferred"], key)

    def test_review_only_cannot_rewrite_strategy_or_repeat_push(self):
        seed, after, prepared, progress = authored_case()
        for field in ("description", "push", "refine"):
            changed, marks = copy.deepcopy(after), copy.deepcopy(progress)
            if field == "description": changed["RHAISTRAT-1"][field] += " changed"
            if field == "push": marks["push"]["strategies"].append("RHAISTRAT-1")
            if field == "refine": marks["refine"]["RHAISTRAT-1"] = "recorded"
            self.assertFalse(mixed.assess(seed, changed, prepared, marks)["ok"], field)

    def test_duplicate_review_attachment_clone_or_lost_foreign_owner_fails(self):
        for mutation in ("review", "attachment", "clone", "foreign"):
            seed, after, prepared, progress = authored_case()
            if mutation == "review": after["RHAISTRAT-1"]["comments"].append(after["RHAISTRAT-1"]["comments"][-1])
            if mutation == "attachment": after["RHAISTRAT-1"]["attachments"].append(after["RHAISTRAT-1"]["attachments"][-1])
            if mutation == "clone": after["RHAISTRAT-999"] = copy.deepcopy(after["RHAISTRAT-1"])
            if mutation == "foreign": after["RHAIRFE-18"]["labels"] = []
            self.assertFalse(mixed.assess(seed, after, prepared, progress)["ok"], mutation)

    def test_comment_truncation_is_not_an_immutable_snapshot(self):
        with self.assertRaisesRegex(ValueError, "truncated"):
            mixed.normalize({"fields": {"comment": {"comments": [], "total": 1}}})

    def test_runner_checker_uses_mixed_work_set_and_requires_repeat_report(self):
        import check_run
        seed, after, prepared, progress = authored_case()

        def raw(value):
            return {"fields": {**value, "status": {"name": value["status"]},
                "comment": {"comments": value["comments"]}, "attachment": value["attachments"],
                "issuelinks": [{"type": {"name": link["type"]},
                    **{side: {"key": link[side]} for side in ("inwardIssue", "outwardIssue") if side in link}}
                    for link in value["links"]]}}
        seed["before"] = {key: mixed.normalize(raw(value)) for key, value in seed["before"].items()}
        files = {"run.json": prepared, "strat-progress.json": progress,
                 "mixed-preflight.json": {"ok": True, "checks": {}},
                 "mixed-repeat.json": {"ok": True, "checks": {}, "model_invocations": 0}}

        def jira(path):
            if "/search?" in path:
                return {"issues": [{"key": key} for key in after]}
            return raw(after[path.split("/issue/")[1]])

        def read(path):
            result = files.get(Path(path).name)
            return json.dumps(result) if result is not None else None

        with patch.object(check_run, "jira", jira), patch.object(check_run, "read_file", read):
            checks, facts = check_run.mixed_jira_checks(seed, "job")
            self.assertTrue(all(c["ok"] for c in checks.values()), checks)
            self.assertEqual(len(facts["strategies"]), 9)
            self.assertEqual((facts["batch_size"], facts["acquired_count"]), (10, 9))
            del files["mixed-repeat.json"]
            checks, _ = check_run.mixed_jira_checks(seed, "job")
            self.assertFalse(checks["mixed_repeat"]["ok"])


@unittest.skipUnless(os.environ.get("STRAT_CREATOR_CHECKOUT"), "optional local emulator integration; no model calls")
class LocalEmulatorTests(unittest.TestCase):
    def test_real_seed_prepare_guard_and_repeat(self):
        source = Path(os.environ["STRAT_CREATOR_CHECKOUT"]).resolve()
        spec = importlib.util.spec_from_file_location("mixed_test_jira_fixtures", source / "tests/conftest.py")
        fixtures = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixtures)
        server = fixtures.jira_emu.__wrapped__()
        url = next(server)
        try:
            fixtures.jira.__wrapped__(url)
            with tempfile.TemporaryDirectory(delete=os.environ.get("STRAT_MIXED_KEEP_TEST") != "1") as temporary:
                root = Path(temporary)
                target, out, state = root / "target", root / "seed", root / "state"
                out.mkdir()
                subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(source), str(target)], check=True)
                ref = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
                env = {"JIRA_SERVER": url, "JIRA_USER": "admin", "JIRA_TOKEN": "admin", "JOB_ARTIFACT_DIR": str(out),
                       "STRAT_ARCHITECTURE_CONTEXT_PATH": str(source / "tests/fixtures/workflow-smoke/architecture-context"),
                       "TARGET_REPO_DIR": str(target), "STRAT_STATE_DIR": str(state), "STRAT_CREATOR_REF": ref,
                       "STRAT_CREATOR_REPO": str(source), "STRAT_MODE": "batch", "STRAT_RUN_ID": "mixed-test", "BATCH_SIZE": "10"}
                scenario, templates = seed_scenario.load_scenario("batch-mixed-state")
                args = SimpleNamespace(strat_creator=target, strat_creator_repo=str(source), scenario="batch-mixed-state",
                                       no_reset=False, dry_run=False)
                with patch.dict(os.environ, env), patch.object(seed_scenario, "EMULATOR_HOSTS", {"127.0.0.1"}), \
                        patch("require_archive.check_archives", return_value={"ok": True}):
                    mixed.seed(args, scenario, templates)
                    report = json.loads((out / "seed.json").read_text())
                    os.environ["STRAT_PREVIOUS_PROGRESS"] = report["previous_progress_path"]
                    os.environ["BATCH_EXPECTED_KEYS"] = " ".join(report["discovered_in_order"])
                    log = out / "integration.log"
                    mixed.command(["bash", str(target / ".fullsend/shared/pre-strategy.sh")], target, os.environ.copy(), log)
                    self.assertEqual(mixed.main(["guard", str(out / "seed.json"), str(target), str(state), str(out)]), 0)
                    prepared = json.loads((state / "run.json").read_text())
                    self.assertEqual(len(prepared["reused_push"]), 2)
                    # Reimport the published description as strategy-create
                    # Path A does, then verify actual reuse against its proof.
                    client, api = mixed.connection()
                    with client:
                        for row in report["rfes"][:2]:
                            key = row["strat_key"]
                            task = target / f"artifacts/strat-tasks/{key}.md"
                            task.parent.mkdir(parents=True, exist_ok=True)
                            description = api("GET", f"/rest/api/3/issue/{key}")["fields"]["description"]
                            raw = out / f"{key}-description.json"
                            raw.write_text(json.dumps(description))
                            mixed.command([sys.executable, "-c",
                                ("from pathlib import Path; import sys,json; sys.path.insert(0,'scripts'); "
                                "from jira_utils import adf_to_markdown; "
                                "Path(sys.argv[2]).write_text(adf_to_markdown(json.load(open(sys.argv[1]))))"),
                                str(raw), str(task)], target, os.environ.copy(), log)
                            mixed.command([sys.executable, "scripts/frontmatter.py", "set", str(task),
                                f"strat_id={key}", f"source_rfe={row['key']}", f"jira_key={key}",
                                f"title={row['summary']}", "priority=Major", "status=Refined"], target, os.environ.copy(), log)
                    mixed.command([sys.executable, "scripts/strat_pipeline_state.py", "record-create"],
                                  target, os.environ.copy(), log)
                    mixed.command([sys.executable, "scripts/strat_pipeline_state.py", "read"],
                                  target, os.environ.copy(), log)
                    mixed.command(["bash", str(state / "strat-creator/.fullsend/shared/release-locks.sh"), str(state)],
                                  target, os.environ.copy(), log)
                    # Mark completed tickets as final without inference; this
                    # isolates repeat selection/claim cleanup from content tests.
                    client, api = mixed.connection()
                    with client:
                        rows = {r["key"]: r for r in report["rfes"]}
                        for key in report["expected_acquired_keys"]:
                            strat = rows[key].get("strat_key")
                            if not strat:
                                strat = api("POST", "/rest/api/2/issue", json={"fields": {
                                    "project": {"key": "RHAISTRAT"}, "issuetype": {"name": "Feature"}, "summary": "Completed fixture"}})["key"]
                                api("POST", "/rest/api/2/issueLink", json={"type": {"name": "Cloners"},
                                    "inwardIssue": {"key": strat}, "outwardIssue": {"key": key}})
                            api("PUT", f"/rest/api/2/issue/{strat}", json={"update": {"labels": [{"add": "strat-creator-rubric-pass"}]}})
                    result = mixed.repeat(target, report, out)
                    self.assertTrue(result["ok"], result)
        finally:
            server.close()


if __name__ == "__main__":
    unittest.main()
