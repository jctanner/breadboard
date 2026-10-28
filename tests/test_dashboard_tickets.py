"""The ticket browser and service list when an emulator is not deployed."""

import os
import unittest
from unittest import mock

from src.dashboard import webapp
from src.dashboard.ticket_data import TicketAggregator

# RFC 6761 reserves .invalid, so these names never resolve, as a deleted
# cluster Service's name does not.
MISSING = "https://gitlab-emulator.invalid/api/v4"
# Nothing listens on port 1: the host resolves but the service is down.
DOWN = "https://127.0.0.1:1/api/v4"


def sources(**env):
    defaults = {
        "BREADBOARD_JIRA_URL": "https://jira-emulator.invalid",
        "GITHUB_API_URL": "https://github-emulator.invalid/api/v3",
        "GITLAB_API_URL": MISSING,
        "BREADBOARD_TICKET_TIMEOUT": "2",
    }
    return mock.patch.dict(os.environ, {**defaults, **env})


class NotDeployedTests(unittest.TestCase):
    def test_sources_that_are_not_deployed_are_skipped_without_errors(self):
        with sources():
            result = TicketAggregator().collect()
        self.assertEqual(result.errors, [])
        self.assertEqual(result.not_deployed, ["jira", "github", "gitlab"])

    def test_a_deployed_source_that_fails_is_still_an_error(self):
        with sources(GITLAB_API_URL=DOWN):
            result = TicketAggregator().collect()
        self.assertEqual([error["source"] for error in result.errors], ["gitlab"])
        self.assertNotIn("gitlab", result.not_deployed)

    def test_service_list_marks_a_missing_service_not_deployed(self):
        with sources():
            missing = webapp._check_service({"check_url": f"{MISSING}/version"})
        with sources(GITLAB_API_URL=DOWN):
            down = webapp._check_service({"check_url": f"{DOWN}/version"})
        self.assertEqual(missing["status"], "not deployed")
        self.assertEqual(down["status"], "down")


if __name__ == "__main__":
    unittest.main()
