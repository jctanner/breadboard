"""Delivery/content checks, without model calls or a technical-accuracy claim."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from review_assessment import classify
import check_run
from test_batch import reviewer_bodies, valid_report

KEY = "RHAISTRAT-1"


def numbered_report(findings):
    return (f"### {KEY}: Gateway cancellation\n**Feasibility**: needs revision\n"
            "**Effort estimate**: optimistic\n**RFE alignment**: delivers\n"
            "**Key concerns**: listed below\n**Prior review status**: unchanged\n\n"
            + findings + "\n**Recommendation**: revise")


class AssessmentTests(unittest.TestCase):
    def test_scope_subject_preserves_canonical_completed_judgments(self):
        for subject in ("The capability is", "Capability is", "The scope is", "Scope is"):
            for verdict in ("right-sized", "too large", "too small", "unbounded"):
                with self.subTest(subject=subject, verdict=verdict):
                    report = valid_report(KEY, "scope").replace("right-sized.", f"{subject} {verdict}.")
                    self.assertTrue(classify(report, KEY, "scope")["assessment_present"])

    def test_scope_subject_does_not_supply_a_missing_explanation(self):
        for verdict in ("right-sized", "too large", "unbounded"):
            report = (f"### {KEY}: Gateway cancellation\n"
                      f"**Scope assessment**: The capability is {verdict}\n"
                      "**Recommendation**: revise")
            with self.subTest(verdict=verdict):
                self.assertFalse(classify(report, KEY, "scope")["assessment_present"])

    def test_scope_subject_does_not_accept_negation_templates_or_search_for_a_verdict(self):
        for judgment in ("The capability is not right-sized", "The capability is pending",
                         "The scope is TODO", "The capability is <right-sized / too large>",
                         "The capability is right-sized or too large", "The scope is too small / unbounded",
                         "The capability might be right-sized", "Architecture is right-sized",
                         "We have not decided whether the capability is right-sized"):
            report = valid_report(KEY, "scope").replace("right-sized.", judgment + ".")
            with self.subTest(judgment=judgment):
                self.assertFalse(classify(report, KEY, "scope")["assessment_present"])

    def test_repeated_scope_judgments_normalize_subject_and_reject_conflicts(self):
        report = valid_report(KEY, "scope").replace("right-sized.", "The capability is right-sized.")
        report += "\n**Scope assessment**: right-sized"
        self.assertTrue(classify(report, KEY, "scope")["assessment_present"])
        for other in ("The scope is too large", "pending", "The capability is not right-sized"):
            with self.subTest(other=other):
                self.assertFalse(classify(report + f"\n**Scope assessment**: {other}", KEY, "scope")["assessment_present"])

    def test_markdown_numbered_findings_use_the_body_not_only_the_title(self):
        for heading in ("#### 1. Cancellation race", "## 2) Cancellation race"):
            with self.subTest(heading=heading):
                report = numbered_report(heading + "\n\nThe gateway must resolve cancellation racing with the final response.")
                self.assertTrue(classify(report, KEY, "feasibility")["assessment_present"])

    def test_numbered_headings_do_not_turn_scaffolding_into_explanations(self):
        for findings in (
                "#### 1. The gateway needs a documented cancellation race outcome",
                "#### 1. Cancellation race\nTODO explain the cancellation and completion behavior here.",
                "#### 1. Cancellation race\nReview is pending while I gather more background.",
                "#### 1. Cancellation race\n> The gateway must resolve cancellation racing with the final response.",
                "#### 1. Cancellation race\n| The gateway must resolve cancellation racing with the final response. |",
                "```markdown\n#### 1. Cancellation race\nThe gateway must resolve cancellation racing with the final response.\n```",
                "#### 1. Cancellation race\n~~~text\nThe gateway must resolve cancellation racing with the final response.\n~~~",
                "#### 1. Cancellation race\nTBD\n#### Unrelated background\nThe gateway already owns cancellation and timeout handling."):
            with self.subTest(findings=findings):
                self.assertFalse(classify(numbered_report(findings), KEY, "feasibility")["assessment_present"])

    def test_numbered_findings_cannot_borrow_another_tickets_explanation(self):
        report = numbered_report("#### 1. Cancellation race\nTBD")
        report += "\n" + valid_report("RHAISTRAT-2", "feasibility")
        self.assertFalse(classify(report, KEY, "feasibility")["assessment_present"])

    def test_explicit_architecture_subject_preserves_completed_judgment(self):
        report = (f"### {KEY}: Gateway cancellation\n"
                  "**Architecture assessment**: Core architecture is sound with two unresolved validation items\n"
                  "**Cross-component risks**: Gateway ownership already defines where cancellation must be implemented.\n"
                  "**Recommendation**: approve")
        self.assertTrue(classify(report, KEY, "architecture")["assessment_present"])
        repeated = report + "\n**Architecture assessment**: sound"
        self.assertTrue(classify(repeated, KEY, "architecture")["assessment_present"])

    def test_architecture_subject_is_not_explanation_or_permission_to_search_for_sound(self):
        for judgment in ("Core architecture is sound", "Core architecture is mostly sound"):
            report = f"### {KEY}: Gateway cancellation\n**Architecture assessment**: {judgment}\n**Recommendation**: approve"
            with self.subTest(judgment=judgment):
                self.assertFalse(classify(report, KEY, "architecture")["assessment_present"])
        for judgment in ("Core architecture is not sound", "Core architecture is pending",
                         "Core architecture is <sound / concerns identified>",
                         "Core architecture is sound or concerns identified",
                         "We have not decided whether the core architecture is sound"):
            report = valid_report(KEY, "architecture").replace("sound.", judgment + ".")
            with self.subTest(judgment=judgment):
                self.assertFalse(classify(report, KEY, "architecture")["assessment_present"])

    def test_numbered_explanations_and_consistent_role_repeats(self):
        for role, label, judgment in (
                ("feasibility", "Feasibility", "feasible"),
                ("architecture", "Architecture assessment", "Mostly sound"),
                ("testability", "Testability", "Partially testable")):
            report = (f"### {KEY}: Timeouts\n**{label}**: {judgment}\n"
                      "1. The gateway already owns cancellation for this route.\n"
                      f"**{label}**: {judgment.upper()}\n**Recommendation**: revise")
            self.assertTrue(classify(report, KEY, role)["assessment_present"])
            for conflict in ("pending", "<TODO>", "untestable", "infeasible", "conflicts with platform"):
                changed = report + f"\n**{label}**: {conflict}"
                self.assertFalse(classify(changed, KEY, role)["assessment_present"])
            for unfinished in ("I will write the assessment after reading the files.",
                               "TODO explain the cancellation and error behavior here.",
                               "Review is pending while I gather more background."):
                changed = report.replace("The gateway already owns cancellation for this route.", unfinished)
                self.assertFalse(classify(changed, KEY, role)["assessment_present"])

    def test_repeated_agreeing_decisions_preserve_completed_assessment(self):
        for role in check_run.REVIEWER_SKILLS.values():
            for verdict in ("approve", "revise", "reject"):
                with self.subTest(role=role, verdict=verdict):
                    report = valid_report(KEY, role).replace("Recommendation**: approve", f"Recommendation**: {verdict}")
                    report += f"\n**Recommendation**: {verdict.upper()}\n**Recommendation**: {verdict}"
                    result = classify(report, KEY, role)
                    self.assertTrue(result["assessment_present"])
                    self.assertEqual(result["recommendation"], verdict)

    def test_conflicting_or_unfinished_companion_decisions_remain_incomplete(self):
        for other in ("revise", "reject", "", "pending", "<approve / revise / reject>", "approve or reject"):
            with self.subTest(other=other):
                report = valid_report(KEY, "feasibility") + f"\n**Recommendation**: {other}"
                self.assertFalse(classify(report, KEY, "feasibility")["assessment_present"])

    def test_repeated_architecture_skip_does_not_claim_an_assessment(self):
        report = (f"### {KEY}: Architecture review skipped\n"
                  "**Architecture assessment**: no architecture context available\n"
                  "**Recommendation**: skipped\n**Recommendation**: skipped")
        result = classify(report, KEY, "architecture")
        self.assertEqual(result["classification"], "skipped")
        self.assertFalse(result["assessment_present"])

    def test_short_completed_reports_for_every_role(self):
        for role in check_run.REVIEWER_SKILLS.values():
            report = valid_report(KEY, role)
            self.assertLess(len(report), 200)
            with self.subTest(role=role):
                result = classify(report, KEY, role)
                self.assertTrue(result["assessment_present"])
                self.assertTrue(result["exclusive_report_target"])

    def test_non_assessments_cannot_pass_as_feasibility(self):
        prefix = f"### {KEY}: Timeouts\n**Feasibility**: feasible\n"
        negatives = {
            "empty": "",
            "ack": "Skill execution completed",
            "observed_progress": "I've launched four research agents in parallel to read component architecture docs and overlays. I'll wait for them to complete before assembling the architecture review.",
            "observed_error": 'API Error: Connection error.\n{"error":"upstream_stream_error"}',
            "heading_only": f"### {KEY}: Timeouts",
            "decision_only": prefix + "**Recommendation**: approve",
            "length_padding": prefix + "\n" + "Review in progress, please wait for completion.\n" * 50 + "**Recommendation**: approve",
            "status_field": prefix + "**Key concerns**: I will wait for all agents before assembling the review.\n**Recommendation**: revise",
            "pending_role": prefix.replace("feasible", "pending") + "**Key concerns**: The gateway owns cancellation and timeout handling.\n**Recommendation**: revise",
            "template": prefix.replace("feasible", "<feasible / infeasible / needs revision>") + "**Key concerns**: <list of concrete concerns about gateway routing behavior>\n**Recommendation**: <approve / revise / reject>",
            "tbd": prefix + "**Key concerns**: TBD, waiting for the gateway investigation to complete.\n**Recommendation**: approve",
            "unsupported_decision": prefix + "**Key concerns**: The gateway owns cancellation and timeout handling.\n**Recommendation**: pending",
            "missing_decision": prefix + "**Key concerns**: The gateway owns cancellation and timeout handling.",
            "duplicate_decision": valid_report(KEY, "feasibility") + "\n**Recommendation**: reject",
            "unfilled_decision_choices": valid_report(KEY, "feasibility").replace("**Recommendation**: approve", "**Recommendation**: approve / revise / reject"),
            "wrong_role": valid_report(KEY, "architecture"),
            "wrong_target": valid_report("RHAISTRAT-2", "feasibility"),
            "source_rfe_only": valid_report("RHAIRFE-1", "feasibility"),
            "scorer_json": '{"key":"RHAISTRAT-1","recommendation":"approve","feasibility":2}',
        }
        for name, report in negatives.items():
            with self.subTest(name=name):
                self.assertFalse(classify(report, KEY, "feasibility")["assessment_present"])

    def test_error_flag_wins_even_with_valid_content(self):
        self.assertEqual(classify(valid_report(KEY, "scope"), KEY, "scope", is_error=True)["classification"], "error")

    def test_legitimate_findings_about_errors_do_not_become_error_returns(self):
        report = (f"### {KEY}: Timeouts\n**Feasibility**: needs revision\n"
                  "**Key concerns**:\n- The gateway emits Connection error when the upstream cancels a delayed stream.\n"
                  "**Recommendation**: revise")
        self.assertTrue(classify(report, KEY, "feasibility")["assessment_present"])

    def test_none_found_requires_explanation(self):
        report = (f"### {KEY}: Timeouts\n**Architecture assessment**: sound\n"
                  "**Cross-component risks**: None identified. The gateway already owns cancellation for this route.\n"
                  "**Recommendation**: approve")
        self.assertTrue(classify(report, KEY, "architecture")["assessment_present"])
        self.assertFalse(classify(report.replace(" The gateway already owns cancellation for this route.", ""), KEY, "architecture")["assessment_present"])

    def test_historical_recommendations_and_colon_inside_bold(self):
        report = (f"### {KEY}: Timeouts\n**Testability: Partially testable**\n"
                  "**Missing edge cases**:\n- Delayed streams need an explicit cancellation race test.\n"
                  "**Recommendation**: Revise criteria. Add that boundary test.")
        self.assertTrue(classify(report, KEY, "testability")["assessment_present"])
        self.assertTrue(classify(report.replace("Partially testable", "Largely testable"), KEY, "testability")["assessment_present"])

    def test_explanation_can_follow_verdict_in_a_findings_section(self):
        report = (f"### {KEY}: Timeouts\n**Scope assessment**: right-sized\n"
                  "**Scope risks**: minor, listed below\n**Recommendation**: approve\n\n"
                  "**Findings**\n1. **Right-sized.** The gateway change delivers one bounded cancellation capability.\n")
        self.assertTrue(classify(report, KEY, "scope")["assessment_present"])

    def test_real_review_can_propose_placeholder_fields_to_be_resolved(self):
        report = (f"### {KEY}: Timeouts\n**Testability**: partially testable\n"
                  "**Missing edge cases**: Delayed streams need an explicit cancellation race test.\n"
                  "**Recommendation**: revise criteria. Define `<status>` and `<schema>` in the API contract.")
        self.assertTrue(classify(report, KEY, "testability")["assessment_present"])

    def test_skip_recorded_without_claiming_assessment(self):
        report = (f"### {KEY}: Architecture review skipped\n"
                  "**Architecture assessment**: no architecture context available\n**Recommendation**: skipped")
        result = classify(report, KEY, "architecture")
        self.assertEqual(result["classification"], "skipped")
        self.assertFalse(result["assessment_present"])

    def test_delivery_and_exclusive_scope_are_distinct(self):
        report = valid_report(KEY, "scope") + "\n" + valid_report("RHAISTRAT-2", "scope")
        result = classify(report, KEY, "scope")
        self.assertTrue(result["assessment_present"])
        self.assertFalse(result["exclusive_report_target"])
        # The requested target needs its own assessment, not the next target's.
        incomplete = f"### {KEY}: Timeouts\nReview pending.\n" + valid_report("RHAISTRAT-2", "scope")
        self.assertFalse(classify(incomplete, KEY, "scope")["assessment_present"])


class ReceivingChannelTests(unittest.TestCase):
    def test_scope_subject_still_requires_valid_assigned_receiving_result(self):
        bodies = reviewer_bodies([KEY])
        report = valid_report(KEY, "scope").replace("right-sized.", "The capability is right-sized but loosely bounded.")
        scope_result = bodies[1]["messages"][1]["content"][2]
        self.assertTrue(scope_result["tool_use_id"].endswith("strategy-scope-review"))
        wrapper = scope_result["content"].split("Result:", 1)[0] + "Result: "
        scope_result["content"] = wrapper + report
        self.assertTrue(check_run.reviewer_returns(bodies, [KEY])["ok"])
        for failure in ("wrong_target", "tool_error", "missing_boundary", "status"):
            changed = copy.deepcopy(bodies)
            result = changed[1]["messages"][1]["content"][2]
            if failure == "wrong_target":
                result["content"] = wrapper + report.replace(KEY, "RHAISTRAT-2")
            elif failure == "tool_error":
                result["is_error"] = True
            elif failure == "missing_boundary":
                result["content"] = report
            else:
                result["content"] = wrapper + "Review is pending while I collect the scope findings."
            with self.subTest(failure=failure):
                self.assertFalse(check_run.reviewer_returns(changed, [KEY])["ok"])

    def test_observed_markdown_formats_pass_only_through_a_matching_receiving_channel(self):
        bodies = reviewer_bodies([KEY])
        results = bodies[1]["messages"][1]["content"]
        reports = {
            "feasibility": numbered_report("#### 1. Cancellation race\nThe gateway must resolve cancellation racing with the final response."),
            "architecture": valid_report(KEY, "architecture").replace("sound.", "Core architecture is sound."),
        }
        for result in results:
            for role, report in reports.items():
                if result["tool_use_id"].endswith(f"strategy-{role}-review"):
                    result["content"] = result["content"].split("Result:", 1)[0] + "Result: " + report
        self.assertTrue(check_run.reviewer_returns(bodies, [KEY])["ok"])
        results[0]["is_error"] = True
        self.assertFalse(check_run.reviewer_returns(bodies, [KEY])["ok"])

    def test_agreeing_repeats_do_not_invalidate_delivered_roles_or_change_launch_counts(self):
        bodies = reviewer_bodies([KEY])
        for result in bodies[1]["messages"][1]["content"]:
            result["content"] += "\n**Recommendation**: approve"
        gate = check_run.reviewer_returns(bodies, [KEY])
        self.assertTrue(gate["ok"])
        self.assertEqual(len(gate["detail"]["launches"]), 4)
        for role in gate["detail"]["by_strategy"][KEY].values():
            self.assertTrue(role["returned"])
            self.assertEqual(role["launches"], 1)
            self.assertEqual(role["reruns"], 0)

    def test_status_rejected_with_reason_and_unchanged_launch_accounting(self):
        bodies = reviewer_bodies([KEY])
        results = bodies[1]["messages"][1]["content"]
        results[-1]["content"] = 'Skill "strategy-architecture-review" completed (forked execution).\n\nResult: I will wait for the research agents before assembling the review.'
        gate = check_run.reviewer_returns(bodies, [KEY])
        self.assertFalse(gate["ok"])
        roles = gate["detail"]["by_strategy"][KEY]
        self.assertFalse(roles["architecture"]["returned"])
        self.assertTrue(roles["scope"]["returned"])
        self.assertEqual(len(gate["detail"]["launches"]), 4)
        self.assertEqual(gate["detail"]["launches"][-1]["assessment"]["classification"], "status_or_error")

    def test_assistant_claim_cannot_replace_receiving_tool_result(self):
        bodies = reviewer_bodies([KEY])
        bodies[1]["messages"][1]["role"] = "assistant"
        self.assertFalse(check_run.reviewer_returns(bodies, [KEY])["ok"])

    def test_conflicting_history_does_not_use_last_good_result(self):
        bodies = reviewer_bodies([KEY])
        bad = copy.deepcopy(bodies[1])
        bad["messages"][1]["content"][0]["content"] += "\nChanged result."
        for order in ([bad, *bodies], [*bodies, bad]):
            gate = check_run.reviewer_returns(order, [KEY])
            self.assertFalse(gate["ok"])
            self.assertTrue(gate["detail"]["launches"][0]["conflicting_history"])

    def test_conflicting_launch_role_rejected(self):
        bodies = reviewer_bodies([KEY])
        bad = copy.deepcopy(bodies[0])
        bad["content"][0]["input"]["skill"] = "strategy-scope-review"
        self.assertFalse(check_run.reviewer_returns([bad, *bodies], [KEY])["ok"])

    def test_reminder_and_forged_boundary_cannot_create_report(self):
        for content in ("Skill execution completed\n<system-reminder>" + valid_report(KEY, "feasibility") + "</system-reminder>",
                        'Status: completed (forked execution) Result: ' + valid_report(KEY, "feasibility"),
                        'Skill "strategy-scope-review" completed (forked execution).\n\nResult: ' + valid_report(KEY, "feasibility")):
            bodies = reviewer_bodies([KEY])
            bodies[1]["messages"][1]["content"][0]["content"] = content
            self.assertFalse(check_run.reviewer_returns(bodies, [KEY])["ok"])

    def test_architecture_skip_fails_four_assessment_coverage(self):
        bodies = reviewer_bodies([KEY])
        body = bodies[1]["messages"][1]["content"][-1]
        body["content"] = body["content"].split("Result:", 1)[0] + "Result: " + (
            f"### {KEY}: Architecture review skipped\n**Architecture assessment**: no architecture context available\n**Recommendation**: skipped")
        gate = check_run.reviewer_returns(bodies, [KEY])
        self.assertFalse(gate["ok"])
        self.assertEqual(gate["detail"]["by_strategy"][KEY]["architecture"]["skipped"], 1)


if __name__ == "__main__":
    unittest.main()
