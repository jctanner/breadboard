"""Emulator-backed test for the dashboard onboarding button.

Work package 7's last checklist item. The unit tests in
``test_fullsend_onboarding.py`` inject a fake runner, so everything they prove
stops at the boundary: ``_exec_in_runner_pod`` — the part that actually shells
into the runner pod and invokes the CLI — has no coverage there, and every
claim about it so far rests on manual runs.

So this exercises the deployed endpoint rather than importing the module. It
goes through the dashboard's own HTTP route, in its own pod, with its own
credentials and RBAC, against a real repository on the emulator. That is the
only arrangement in which the exec path, the credential handoff, the pull
request parse and the redaction are all real at once.

It is skipped when the stack is not up, rather than failed: a unit test run on
a laptop should not go red because there is no cluster.

Run it with the stack running:

    uv run --with pytest --with requests pytest tests/test_fullsend_onboarding_live.py -v
"""

from __future__ import annotations

import os
import time
import uuid

import pytest

requests = pytest.importorskip("requests")
requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

DASHBOARD = os.getenv("BREADBOARD_DASHBOARD_URL", "https://dashboard.local").rstrip("/")
FORGE_API = os.getenv(
    "BREADBOARD_FORGE_API", "https://github.local/api/v3"
).rstrip("/")
FORGE_TOKEN = os.getenv("GITHUB_EMULATOR_TOKEN", "ghp_admin_default_token")
ORG = os.getenv("BREADBOARD_ONBOARD_TEST_ORG", "fullsend-dev")
AUTH = {"Authorization": f"token {FORGE_TOKEN}"}
TIMEOUT = float(os.getenv("BREADBOARD_ONBOARD_TEST_TIMEOUT", "420"))


def _reachable(url: str, **kwargs) -> bool:
    try:
        requests.get(url, timeout=5, verify=False, **kwargs)
        return True
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not (_reachable(f"{DASHBOARD}/healthz") and _reachable(f"{FORGE_API}/user", headers=AUTH)),
    reason="needs the running stack: the dashboard and the GitHub emulator",
)


@pytest.fixture
def scratch_repo():
    """A repository that exists only for this test, removed afterwards.

    Named uniquely per run: onboarding is deliberately not idempotent in the
    sense of re-running the CLI, so a leftover repository from a previous run
    would make the first assertion here test the repeat path instead.
    """
    name = f"onboard-test-{uuid.uuid4().hex[:8]}"
    full = f"{ORG}/{name}"
    created = requests.post(
        f"{FORGE_API}/orgs/{ORG}/repos",
        headers={**AUTH, "Content-Type": "application/json"},
        json={"name": name, "private": False, "auto_init": True},
        timeout=30,
        verify=False,
    )
    assert created.status_code == 201, f"could not create {full}: {created.text[:200]}"
    time.sleep(1)
    try:
        yield full
    finally:
        requests.delete(f"{FORGE_API}/repos/{full}", headers=AUTH, timeout=30, verify=False)


def _onboard(repository: str) -> dict:
    response = requests.post(
        f"{DASHBOARD}/api/fullsend/onboard",
        headers={"Content-Type": "application/json"},
        json={"repository": repository},
        timeout=TIMEOUT,
        verify=False,
    )
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.text[:400]}"
    return response.json()


def _pulls(repository: str) -> list[dict]:
    response = requests.get(
        f"{FORGE_API}/repos/{repository}/pulls",
        headers=AUTH, params={"state": "all"}, timeout=30, verify=False,
    )
    response.raise_for_status()
    return response.json()


def test_onboarding_creates_a_reviewable_pull_request(scratch_repo):
    """The whole path: HTTP, exec into the runner, real CLI, PR on the forge."""
    result = _onboard(scratch_repo)
    assert result["status"] == "created", result.get("output", "")[-600:]
    assert result["exit_code"] == 0

    pulls = _pulls(scratch_repo)
    assert len(pulls) == 1, "expected exactly one scaffold pull request"
    pull = pulls[0]
    assert pull["state"] == "open", "the scaffold must be reviewable, not merged"
    assert pull["head"]["ref"] == "fullsend/scaffold-install"
    assert pull["number"] == result["pull_request_number"]


def test_the_scaffold_carries_the_shim_workflow(scratch_repo):
    """What lands is Fullsend's real scaffold, not something resembling it."""
    _onboard(scratch_repo)
    listing = requests.get(
        f"{FORGE_API}/repos/{scratch_repo}/contents/.github/workflows",
        headers=AUTH, params={"ref": "fullsend/scaffold-install"}, timeout=30, verify=False,
    )
    assert listing.status_code == 200, listing.text[:200]
    names = {item["name"] for item in listing.json()}
    assert "fullsend.yaml" in names, f"the shim workflow is missing; found {names}"


def test_variables_and_secrets_are_configured(scratch_repo):
    """Secrets are sealed on the way in; their presence is what is observable."""
    _onboard(scratch_repo)
    variables = requests.get(
        f"{FORGE_API}/repos/{scratch_repo}/actions/variables",
        headers=AUTH, timeout=30, verify=False,
    ).json()
    names = {v["name"] for v in variables.get("variables", [])}
    assert "FULLSEND_MINT_URL" in names
    assert "FULLSEND_PER_REPO_INSTALL" in names

    secrets = requests.get(
        f"{FORGE_API}/repos/{scratch_repo}/actions/secrets",
        headers=AUTH, timeout=30, verify=False,
    ).json()
    assert secrets.get("total_count", 0) >= 1, "sealed-box upload produced no secrets"


def test_repeating_does_not_duplicate(scratch_repo):
    """Repeating is allowed and must not create a second pull request."""
    first = _onboard(scratch_repo)
    assert first["status"] == "created"

    second = _onboard(scratch_repo)
    assert second["status"] == "already-open"
    assert second["pull_request_number"] == first["pull_request_number"]
    assert not second["command"], "the CLI must not run when a scaffold PR is open"
    assert len(_pulls(scratch_repo)) == 1


def test_the_link_returned_can_actually_be_opened(scratch_repo):
    """The CLI reports a URL this forge does not serve; the browse URL is the
    one a reviewer clicks. Linking the wrong one produced a 404."""
    result = _onboard(scratch_repo)
    browse = result.get("pull_request_browse_url")
    assert browse, "no browse URL was returned"
    page = requests.get(browse, headers=AUTH, timeout=30, verify=False)
    assert page.status_code == 200, f"{browse} returned {page.status_code}"


def test_no_credential_reaches_the_response(scratch_repo):
    """The token is passed through the command's environment and must not come
    back in any field, including the captured CLI output."""
    result = _onboard(scratch_repo)
    body = str(result)
    assert FORGE_TOKEN not in body
    for prefix in ("ghp_", "ghs_", "ghe_"):
        # A token-shaped string of real length would mean something leaked
        # even if it is not the one this test knows about.
        assert not any(
            len(chunk) > 20 for chunk in body.split(prefix)[1:]
            if chunk[:20].replace("_", "").isalnum()
        ), f"something token-shaped ({prefix}...) is in the response"


def test_a_repository_that_does_not_exist_is_refused():
    """A refusal the caller can act on, not a five-minute CLI failure."""
    response = requests.post(
        f"{DASHBOARD}/api/fullsend/onboard",
        headers={"Content-Type": "application/json"},
        json={"repository": f"{ORG}/definitely-not-a-real-repo-{uuid.uuid4().hex[:6]}"},
        timeout=60,
        verify=False,
    )
    assert response.status_code == 400
    assert "not found" in response.json().get("error", "").lower()


def test_an_organisation_name_alone_is_refused():
    """Per-org mode creates a config repository, which this button does not do."""
    response = requests.post(
        f"{DASHBOARD}/api/fullsend/onboard",
        headers={"Content-Type": "application/json"},
        json={"repository": ORG},
        timeout=30,
        verify=False,
    )
    assert response.status_code == 400
    assert "OWNER/REPO" in response.json().get("error", "")
