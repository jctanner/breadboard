"""The dashboard's onboarding operation runs the real CLI and reports it.

Work package 7. The rules these cover come from the plan: always deliver
through a pull request, never return the credential, and repeating the action
must not create duplicate state.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "src/dashboard/fullsend_onboarding.py"
SPEC = importlib.util.spec_from_file_location("fullsend_onboarding", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
# Registered before exec: a dataclass resolves its field types through
# sys.modules[cls.__module__], which is None for a spec-loaded module.
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

# Captured before the autouse fixture replaces it with a no-op, so a test
# that wants the real preflight can put it back.
REAL_VERIFY_CREDENTIAL = MODULE.verify_credential

TOKEN = "ghs_atokenlongenoughtoredact"
CREATED = (
    "→ Setting up per-repo fullsend for acme/widget\n"
    "  ✓ Created PR #7: https://github.local/acme/widget/pull/7\n"
    "  ✓ Set 3 repository variables\n"
    "  ✓ Set 2 repository secrets\n"
)


@pytest.fixture(autouse=True)
def _credential(monkeypatch):
    monkeypatch.setenv("GITHUB_EMULATOR_TOKEN", TOKEN)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("FULLSEND_ONBOARD_APP_TOKEN", raising=False)
    monkeypatch.delenv("FULLSEND_ONBOARD_APP_DIR", raising=False)
    monkeypatch.setattr(MODULE, "find_open_scaffold_pr", lambda *a, **k: None)
    monkeypatch.setattr(MODULE, "verify_credential", lambda *a, **k: None)


def _run(output=CREATED, exit_code=0, capture=None):
    def runner(command, env, timeout):
        if capture is not None:
            capture["command"] = command
            capture["env"] = env
        return exit_code, output
    return runner


def test_a_successful_run_reports_the_pull_request():
    result = MODULE.onboard_repository("acme/widget", runner=_run())
    assert result.status == "created"
    assert result.pull_request_number == 7
    assert result.pull_request_url.endswith("/pull/7")
    assert result.branch == MODULE.SCAFFOLD_BRANCH


def test_the_credential_never_appears_in_the_result():
    # A CLI that echoes its configuration on failure would otherwise put the
    # token straight into a dashboard response.
    leaky = f"error: request failed with GH_TOKEN={TOKEN}\n"
    result = MODULE.onboard_repository("acme/widget", runner=_run(leaky, 1))
    payload = str(result.as_dict())
    assert TOKEN not in payload
    assert "***" in result.output


def test_direct_commit_mode_is_not_reachable():
    capture: dict = {}
    MODULE.onboard_repository("acme/widget", runner=_run(capture=capture))
    assert "--direct" not in capture["command"], (
        "--direct skips the review a maintainer is supposed to give the "
        "generated workflow files"
    )


def test_the_command_is_the_real_cli():
    capture: dict = {}
    MODULE.onboard_repository("acme/widget", runner=_run(capture=capture))
    assert capture["command"][:4] == ["fullsend", "github", "setup", "acme/widget"]


def test_an_existing_open_pr_is_not_duplicated(monkeypatch):
    monkeypatch.setattr(
        MODULE, "find_open_scaffold_pr",
        lambda *a, **k: {"html_url": "https://github.local/acme/widget/pull/3", "number": 3},
    )
    def must_not_run(*a, **k):  # noqa: ANN002, ANN003
        raise AssertionError("the CLI must not run when a scaffold PR is already open")
    result = MODULE.onboard_repository("acme/widget", runner=must_not_run)
    assert result.status == "already-open"
    assert result.pull_request_number == 3


def test_a_failing_run_is_reported_not_swallowed():
    result = MODULE.onboard_repository("acme/widget", runner=_run("boom\n", 2))
    assert result.status == "failed"
    assert result.exit_code == 2
    assert "boom" in result.output


@pytest.mark.parametrize("bad", ["acme", "", "acme/widget/extra", "acme widget"])
def test_only_owner_repo_is_accepted(bad):
    # An org on its own puts the CLI into per-org mode, which creates a config
    # repository — a much larger action than this button offers.
    with pytest.raises(MODULE.OnboardingError):
        MODULE.onboard_repository(bad, runner=_run())


def test_a_missing_credential_is_refused_clearly(monkeypatch):
    monkeypatch.delenv("GITHUB_EMULATOR_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(MODULE.OnboardingError) as exc:
        MODULE.onboard_repository("acme/widget", runner=_run())
    assert "FULLSEND_ONBOARD_APP_TOKEN" in str(exc.value)


def test_the_fallback_credential_is_named_in_the_message():
    # The plan wants a short-lived App installation token; a stored token is
    # a fallback and must not be presented as though the rule were met.
    result = MODULE.onboard_repository("acme/widget", runner=_run())
    assert "emulator-admin-fallback" in result.message


def test_the_emulator_token_is_preferred_over_github_token(monkeypatch):
    # The deployment carries both, for different forges. Reading the wrong one
    # handed the CLI a token the forge refuses, and the failure surfaced
    # minutes later as a confusing CLI error.
    monkeypatch.setenv("GITHUB_TOKEN", "ghe_wrongforgecredential")
    monkeypatch.setenv("GITHUB_EMULATOR_TOKEN", TOKEN)
    token, kind = MODULE.resolve_credential()
    assert token == TOKEN
    assert kind == "emulator-admin-fallback"


def test_a_credential_the_forge_refuses_fails_before_the_cli_runs(monkeypatch):
    # The CLI takes minutes and authenticates partway through, so a refused
    # credential must be caught up front rather than deep in its output.
    class Refused:
        status_code = 401
    monkeypatch.setattr(MODULE, "verify_credential", REAL_VERIFY_CREDENTIAL)
    monkeypatch.setattr(MODULE.requests, "get", lambda *a, **k: Refused())
    def must_not_run(*a, **k):  # noqa: ANN002, ANN003
        raise AssertionError("the CLI must not run with a credential the forge refuses")
    with pytest.raises(MODULE.OnboardingError) as exc:
        MODULE.onboard_repository("acme/widget", runner=must_not_run)
    assert "refused the onboarding credential" in str(exc.value)


def test_the_pull_request_link_is_one_a_browser_can_open(monkeypatch):
    # The CLI reports <host>/<owner>/<repo>/pull/N, the canonical GitHub
    # shape. This emulator serves its web UI at /ui/<owner>/<repo>/pulls/N and
    # returns 404 for the other, so linking the CLI's URL gives a dead link.
    monkeypatch.setenv("GITHUB_UI_URL", "https://github.local")
    monkeypatch.delenv("FULLSEND_ONBOARD_PULL_URL_TEMPLATE", raising=False)
    result = MODULE.onboard_repository("acme/widget", runner=_run())
    assert result.pull_request_browse_url == "https://github.local/ui/acme/widget/pulls/7"
    # The CLI's own URL is kept: it is what the command said.
    assert result.pull_request_url.endswith("/pull/7")


def test_the_browse_url_shape_is_configurable(monkeypatch):
    # A real GitHub deployment serves the canonical shape; the template is how
    # that is expressed rather than hardcoding one forge's layout.
    monkeypatch.setenv("GITHUB_UI_URL", "https://github.com")
    monkeypatch.setenv(
        "FULLSEND_ONBOARD_PULL_URL_TEMPLATE", "{ui}/{owner}/{repo}/pull/{number}"
    )
    result = MODULE.onboard_repository("acme/widget", runner=_run())
    assert result.pull_request_browse_url == "https://github.com/acme/widget/pull/7"


def test_the_runner_image_is_passed_through(monkeypatch):
    # This stack's runners are labelled `fullsend`, not a GitHub-hosted image
    # name. Without it the scaffold renders workflows nothing picks up, and
    # the jobs sit queued with nothing reporting why.
    monkeypatch.setenv("FULLSEND_RUNNER_IMAGE", "fullsend")
    capture: dict = {}
    MODULE.onboard_repository("acme/widget", runner=_run(capture=capture))
    assert capture["env"].get("FULLSEND_RUNNER_IMAGE") == "fullsend"


def test_no_runner_image_means_the_cli_default(monkeypatch):
    monkeypatch.delenv("FULLSEND_RUNNER_IMAGE", raising=False)
    capture: dict = {}
    MODULE.onboard_repository("acme/widget", runner=_run(capture=capture))
    assert "FULLSEND_RUNNER_IMAGE" not in capture["env"]


# --- the App installation token ------------------------------------------------
#
# The plan's rule is a short-lived App installation token. The seeded
# onboarding App's key is mounted as files; a ten-minute JWT signed with it is
# exchanged at the forge for a one-hour token scoped to the one repository.

def _seed_app(tmp_path, monkeypatch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()
    ).decode()
    (tmp_path / "app-id").write_text("2001\n")
    (tmp_path / "installation-id").write_text("7\n")
    (tmp_path / "private-key").write_text(pem)
    monkeypatch.setenv("FULLSEND_ONBOARD_APP_DIR", str(tmp_path))
    return key.public_key()


class _Response:
    def __init__(self, status_code, payload, text=""):
        self.status_code, self._payload, self.text = status_code, payload, text

    def json(self):
        return self._payload


def test_a_seeded_app_mints_a_token_for_the_one_repository(tmp_path, monkeypatch):
    import jwt

    public_key = _seed_app(tmp_path, monkeypatch)
    calls = {}

    def fake_post(url, headers=None, json=None, timeout=None, verify=None):
        calls.update(url=url, headers=headers, json=json)
        return _Response(201, {"token": "ghs_mintedforthisrun", "expires_at": "later"})

    monkeypatch.setattr(MODULE.requests, "post", fake_post)
    capture = {}
    result = MODULE.onboard_repository("acme/widget", runner=_run(capture=capture))
    assert result.status == "created"
    assert "app-installation" in result.message
    assert capture["env"]["GH_TOKEN"] == "ghs_mintedforthisrun"
    assert calls["url"].endswith("/app/installations/7/access_tokens")
    assert calls["json"] == {"repositories": ["widget"]}
    assertion = calls["headers"]["Authorization"].split(" ", 1)[1]
    claims = jwt.decode(assertion, public_key, algorithms=["RS256"])
    assert claims["iss"] == "2001"
    assert claims["exp"] - claims["iat"] == 600
    assert "ghs_mintedforthisrun" not in result.output


def test_a_seeded_app_that_cannot_mint_is_an_error_not_a_fallback(tmp_path, monkeypatch):
    _seed_app(tmp_path, monkeypatch)
    monkeypatch.setattr(
        MODULE.requests, "post",
        lambda *a, **k: _Response(422, {}, text="requested repository is not installed"),
    )
    with pytest.raises(MODULE.OnboardingError) as refused:
        MODULE.onboard_repository("acme/widget", runner=_run())
    assert "not installed" in str(refused.value)
    assert "emulator-admin-fallback" not in str(refused.value)


def test_an_incomplete_app_directory_means_no_app(tmp_path, monkeypatch):
    (tmp_path / "app-id").write_text("2001")
    monkeypatch.setenv("FULLSEND_ONBOARD_APP_DIR", str(tmp_path))
    token, kind = MODULE.resolve_credential(None, "acme/widget")
    assert kind == "emulator-admin-fallback"
    assert token == TOKEN


def test_a_ready_made_app_token_still_wins(tmp_path, monkeypatch):
    _seed_app(tmp_path, monkeypatch)
    monkeypatch.setenv("FULLSEND_ONBOARD_APP_TOKEN", "ghs_handedin")
    monkeypatch.setattr(MODULE.requests, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no mint")))
    assert MODULE.resolve_credential(None, "acme/widget") == ("ghs_handedin", "app-installation")
