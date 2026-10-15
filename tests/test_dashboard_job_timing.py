"""Regression coverage for Kubernetes Jobs without a completion_time."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from kubernetes import client

from src.dashboard import webapp
from src.dashboard.k8s_orchestrator import PipelineOrchestrator


START = datetime(2026, 10, 15, 2, 17, 5, tzinfo=timezone.utc)
END = START + timedelta(minutes=23, seconds=22)


def job_fixture(**status):
    return client.V1Job(
        metadata=client.V1ObjectMeta(
            name="failed-job", labels={}, annotations={}, creation_timestamp=START,
        ),
        status=client.V1JobStatus(start_time=START, **status),
    )


def condition(kind="Failed", status="True", at=END):
    return client.V1JobCondition(type=kind, status=status, last_transition_time=at)


class JobTimingTests(unittest.TestCase):
    def setUp(self):
        self.orchestrator = PipelineOrchestrator.__new__(PipelineOrchestrator)

    def test_failed_duration_does_not_change_as_clock_advances(self):
        job = job_fixture(failed=1, conditions=[condition()])
        with mock.patch("src.dashboard.k8s_orchestrator.datetime") as clock:
            for hours in (1, 24):
                clock.now.return_value = END + timedelta(hours=hours)
                self.assertEqual(self.orchestrator._get_job_duration(job), 1402.0)
            clock.now.assert_not_called()

    def test_successful_job_uses_completion_time(self):
        job = job_fixture(succeeded=1, completion_time=END)
        self.assertEqual(self.orchestrator._get_job_duration(job), 1402.0)

    def test_complete_condition_can_supply_missing_completion_time(self):
        job = job_fixture(conditions=[condition("Complete")])
        self.assertEqual(self.orchestrator._get_job_status(job), "completed")
        self.assertEqual(self.orchestrator._get_job_duration(job), 1402.0)

    def test_running_job_duration_advances(self):
        job = job_fixture(active=1, conditions=[condition(status="False")])
        with mock.patch("src.dashboard.k8s_orchestrator.datetime") as clock:
            clock.now.return_value = START + timedelta(seconds=10)
            self.assertEqual(self.orchestrator._get_job_duration(job), 10.0)
            clock.now.return_value = START + timedelta(seconds=40)
            self.assertEqual(self.orchestrator._get_job_duration(job), 40.0)

    def test_failed_attempt_does_not_stop_timer_for_active_retry(self):
        job = job_fixture(active=1, failed=1)
        self.assertEqual(self.orchestrator._get_job_status(job), "running")
        with mock.patch("src.dashboard.k8s_orchestrator.datetime") as clock:
            clock.now.return_value = START + timedelta(seconds=40)
            self.assertEqual(self.orchestrator._get_job_duration(job), 40.0)

    def test_terminal_condition_takes_precedence_over_stale_counters(self):
        job = job_fixture(active=1, conditions=[condition()])
        self.assertEqual(self.orchestrator._get_job_status(job), "failed")
        self.assertEqual(self.orchestrator._get_job_duration(job), 1402.0)

    def test_terminal_job_with_unknown_end_time_has_unknown_duration(self):
        for status in ({"failed": 1}, {"succeeded": 1}, {"conditions": [condition(at=None)]}):
            with self.subTest(status=status):
                self.assertIsNone(self.orchestrator._get_job_duration(job_fixture(**status)))

    def test_unstarted_job_has_no_duration(self):
        job = job_fixture()
        job.status.start_time = None
        self.assertIsNone(self.orchestrator._get_job_duration(job))

    def test_zero_duration_is_valid(self):
        job = job_fixture(failed=1, conditions=[condition(at=START)])
        self.assertEqual(self.orchestrator._get_job_duration(job), 0.0)

    def test_list_and_detail_apis_use_failure_timestamp(self):
        job = job_fixture(failed=1, conditions=[condition()])
        self.orchestrator.namespace = "test-only"
        self.orchestrator.batch_v1 = mock.Mock()
        self.orchestrator.batch_v1.list_namespaced_job.return_value.items = [job]
        self.orchestrator.batch_v1.read_namespaced_job.return_value = job
        with (
            mock.patch.object(webapp, "K8S_AVAILABLE", True),
            mock.patch.object(webapp, "EXECUTION_AVAILABLE", True),
            mock.patch.object(webapp, "OPEN_SHELL_AVAILABLE", False),
            mock.patch.object(webapp, "get_orchestrator", return_value=self.orchestrator),
            mock.patch("src.dashboard.k8s_orchestrator.datetime") as clock,
        ):
            browser = webapp.create_app().test_client()
            for hours in (1, 24):
                clock.now.return_value = END + timedelta(hours=hours)
                for path in ("/api/jobs", "/api/evals"):
                    with self.subTest(path=path, hours=hours):
                        response = browser.get(path)
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.json[0]["duration"], 1402.0)
                        self.assertEqual(response.json[0]["status"], "failed")
                detail = browser.get("/api/jobs/failed-job")
                self.assertEqual(detail.status_code, 200)
                self.assertEqual(detail.json["completed"], END.isoformat())


if __name__ == "__main__":
    unittest.main()
