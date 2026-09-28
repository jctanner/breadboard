"""Verification and authorization in the development Fullsend mint.

The mint used to compare one shared string that both the runner pod and the
mint held in their environment. Anything in the cluster that could read that
string could request any role on any repository, so the mint's role and
repository checks proved nothing about the caller. It now verifies a signed
Actions OIDC token and authorizes against its claims. These tests pin the
properties that make that worth doing.
"""

import importlib.util
import time
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa


SERVER_PATH = Path(__file__).parents[1] / "deploy" / "fullsend-mint-dev" / "server.py"
_SPEC = importlib.util.spec_from_file_location("fullsend_mint_dev", SERVER_PATH)
assert _SPEC and _SPEC.loader
mint = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mint)


ISSUER = "https://github.local"
AUDIENCE = "fullsend-mint"
REPOSITORY = "fullsend-dev/triage-target"


@pytest.fixture(scope="module")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def other_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _StubJwks:
    """Stand in for the emulator's published keys."""

    def __init__(self, public_key):
        self._public_key = public_key

    def signing_key(self, _token):
        return type("Key", (), {"key": self._public_key})()


def _token(key, **overrides):
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": f"repo:{REPOSITORY}:ref:refs/heads/main",
        "repository": REPOSITORY,
        "repository_owner": REPOSITORY.split("/")[0],
        "run_id": "1234",
        "iat": now,
        "nbf": now - 5,
        "exp": now + 300,
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


def _verify(token, key):
    return mint._verify(token, ISSUER, _StubJwks(key.public_key()))


def test_a_valid_token_verifies(signing_key):
    claims = _verify(_token(signing_key), signing_key)
    assert claims["repository"] == REPOSITORY
    assert claims["run_id"] == "1234"


def test_a_token_signed_by_another_key_is_rejected(signing_key, other_key):
    with pytest.raises(mint.ClaimsRejected):
        _verify(_token(other_key), signing_key)


def test_an_expired_token_is_rejected(signing_key):
    past = int(time.time()) - 600
    with pytest.raises(mint.ClaimsRejected):
        _verify(_token(signing_key, iat=past, nbf=past, exp=past + 60), signing_key)


def test_a_token_for_another_audience_is_rejected(signing_key):
    with pytest.raises(mint.ClaimsRejected):
        _verify(_token(signing_key, aud="some-other-service"), signing_key)


def test_a_token_from_another_issuer_is_rejected(signing_key):
    with pytest.raises(mint.ClaimsRejected):
        _verify(_token(signing_key, iss="https://evil.local"), signing_key)


def test_an_unsigned_token_is_rejected(signing_key):
    unsigned = jwt.encode({"iss": ISSUER, "aud": AUDIENCE}, None, algorithm="none")
    with pytest.raises(mint.ClaimsRejected):
        _verify(unsigned, signing_key)


def test_a_run_may_mint_for_its_own_repository():
    mint._authorize_repos({"repository": REPOSITORY}, [REPOSITORY])


def test_a_run_may_not_mint_for_another_repository():
    """The check that makes the whole exchange worth verifying."""
    with pytest.raises(mint.ClaimsRejected) as excinfo:
        mint._authorize_repos({"repository": REPOSITORY}, ["fullsend-dev/secrets"])
    assert "fullsend-dev/secrets" in str(excinfo.value)


def test_a_mixed_request_is_refused_entirely():
    with pytest.raises(mint.ClaimsRejected):
        mint._authorize_repos(
            {"repository": REPOSITORY}, [REPOSITORY, "fullsend-dev/secrets"]
        )


def test_a_token_without_a_repository_claim_is_refused():
    with pytest.raises(mint.ClaimsRejected):
        mint._authorize_repos({}, [REPOSITORY])


def test_config_refuses_to_start_without_issuer_settings(monkeypatch):
    """No silent fall back to the shared secret it replaced."""
    monkeypatch.setenv("FULLSEND_ROLE_TOKENS", "{}")
    monkeypatch.delenv("FULLSEND_OIDC_ISSUER", raising=False)
    monkeypatch.delenv("FULLSEND_OIDC_JWKS_URL", raising=False)
    with pytest.raises(RuntimeError):
        mint._config()


# --- installation tokens -------------------------------------------------------
#
# The mint used to answer with a static per-role personal access token, the
# compatibility profile's deviation 7a. It now signs a JWT as the role's App
# and asks the forge for a one-hour installation token scoped to the calling
# repository and the requested level.

def test_the_read_level_downgrades_every_write():
    """Upstream's canonical table: coder, write and read levels."""
    assert mint.permissions_for("coder", "write") == {
        "contents": "write", "packages": "read", "pull_requests": "write", "issues": "write",
        "checks": "read", "metadata": "read",
    }
    assert mint.permissions_for("coder", "read") == {
        "contents": "read", "packages": "read", "pull_requests": "read", "issues": "read",
        "checks": "read", "metadata": "read",
    }
    assert set(mint.ROLE_PERMISSIONS) == {"triage", "scribe", "coder", "review", "fix", "retro", "prioritize", "fullsend"}


def test_an_omitted_or_empty_level_is_read_and_an_unknown_one_is_refused():
    assert mint.parse_level(None) == "read"
    assert mint.parse_level("") == "read"
    assert mint.parse_level(" Write ") == "write"
    with pytest.raises(ValueError):
        mint.parse_level("admin")


def test_the_installation_on_the_requesting_owner_is_chosen():
    installations = [
        {"id": 3, "account": {"login": "someone-else"}},
        {"id": 8, "account": {"login": "Fullsend-Dev"}},
    ]
    assert mint.installation_for_owner(installations, "fullsend-dev")["id"] == 8
    assert mint.installation_for_owner(installations, "nobody") is None
    assert mint.installation_for_owner("not a list", "fullsend-dev") is None


def _role_app(signing_key):
    from cryptography.hazmat.primitives import serialization
    pem = signing_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()
    ).decode()
    return {"app_id": "1001", "private_key": pem}


def test_minting_signs_as_the_app_and_scopes_the_token(monkeypatch, signing_key):
    app = _role_app(signing_key)
    calls = []

    def fake_forge(method, url, bearer, body=None):
        calls.append((method, url, bearer, body))
        if url.endswith("/app/installations"):
            return 200, [{"id": 8, "account": {"login": "fullsend-dev"}}]
        return 201, {"token": "ghs_minted", "expires_at": "2026-09-28T12:00:00Z",
                     "permissions": body["permissions"], "repository_selection": "selected"}

    monkeypatch.setattr(mint, "_forge_request", fake_forge)
    minted = mint.mint_installation_token(
        "https://github.local/api/v3", "triage", app, "fullsend-dev", ["fullsend-dev/triage-target"], "write",
    )
    assert minted["token"] == "ghs_minted"
    assert minted["permissions"] == {"contents": "read", "issues": "write", "metadata": "read"}
    (list_call, mint_call) = calls
    assert list_call[1] == "https://github.local/api/v3/app/installations"
    assert mint_call[1] == "https://github.local/api/v3/app/installations/8/access_tokens"
    assert mint_call[3]["repositories"] == ["triage-target"]
    claims = jwt.decode(mint_call[2], signing_key.public_key(), algorithms=["RS256"])
    assert claims["iss"] == "1001"
    assert claims["exp"] - claims["iat"] == 600


def test_an_app_not_installed_on_the_owner_cannot_mint(monkeypatch, signing_key):
    monkeypatch.setattr(mint, "_forge_request", lambda *a, **k: (200, [{"id": 1, "account": {"login": "other-org"}}]))
    with pytest.raises(mint.MintFailed) as refused:
        mint.mint_installation_token("https://f/api/v3", "triage", _role_app(signing_key), "fullsend-dev", ["x"], "read")
    assert "not installed on fullsend-dev" in str(refused.value)


def test_a_forge_refusal_is_reported_not_papered_over(monkeypatch, signing_key):
    def fake_forge(method, url, bearer, body=None):
        if url.endswith("/app/installations"):
            return 200, [{"id": 8, "account": {"login": "fullsend-dev"}}]
        return 422, {"detail": "requested repository is not installed"}

    monkeypatch.setattr(mint, "_forge_request", fake_forge)
    with pytest.raises(mint.MintFailed) as refused:
        mint.mint_installation_token("https://f/api/v3", "triage", _role_app(signing_key), "fullsend-dev", ["x"], "read")
    assert "HTTP 422" in str(refused.value)


def test_role_apps_file_is_validated(tmp_path):
    path = tmp_path / "role-apps.json"
    path.write_text('{"triage": {"app_id": "1001", "private_key": "k"}}')
    assert mint.load_role_apps(str(path)) == {"triage": {"app_id": "1001", "private_key": "k"}}
    path.write_text('{"janitor": {"app_id": "1", "private_key": "k"}}')
    with pytest.raises(RuntimeError):
        mint.load_role_apps(str(path))
    path.write_text('{"triage": {"app_id": "1001"}}')
    with pytest.raises(RuntimeError):
        mint.load_role_apps(str(path))


def test_config_requires_the_role_apps_file(monkeypatch):
    monkeypatch.setenv("FULLSEND_OIDC_ISSUER", ISSUER)
    monkeypatch.setenv("FULLSEND_OIDC_JWKS_URL", f"{ISSUER}/.well-known/jwks.json")
    monkeypatch.delenv("FULLSEND_ROLE_APPS_FILE", raising=False)
    with pytest.raises(RuntimeError):
        mint._config()


# --- workflow provenance -----------------------------------------------------------
#
# Which workflow may ask for a role. Fullsend's mint keys this on the
# job_workflow_ref claim: the job must have been defined by an allowed
# workflow file hosted by fullsend-ai/fullsend or a configured host repo.

UPSTREAM = "fullsend-ai/fullsend/.github/workflows/reusable-dispatch.yml@refs/heads/main"


def test_an_upstream_reusable_workflow_is_always_an_allowed_host():
    mint.validate_workflow_ref(UPSTREAM, [], ["reusable-dispatch.yml"])
    mint.validate_workflow_ref(UPSTREAM.upper(), [], ["reusable-dispatch.yml"])  # case-insensitive


def test_a_workflow_in_the_calling_repository_needs_the_repository_registered():
    ref = "fullsend-dev/triage-target/.github/workflows/fullsend-trust-check.yaml@refs/heads/main"
    with pytest.raises(mint.ClaimsRejected, match="allowed workflow host"):
        mint.validate_workflow_ref(ref, [], ["*"])
    mint.validate_workflow_ref(ref, ["fullsend-dev/triage-target"], ["fullsend-trust-check.yaml"])


def test_the_basename_must_be_allowed_and_star_allows_any():
    with pytest.raises(mint.ClaimsRejected, match="not in allowed list"):
        mint.validate_workflow_ref(UPSTREAM, [], ["reusable-triage.yml"])
    mint.validate_workflow_ref(UPSTREAM, [], ["*"])


def test_an_empty_allowed_list_denies_everything_as_upstream_does():
    with pytest.raises(mint.ClaimsRejected):
        mint.validate_workflow_ref(UPSTREAM, [], [])


def test_a_ref_outside_the_workflows_directory_or_missing_is_refused():
    with pytest.raises(mint.ClaimsRejected, match="workflow file"):
        mint.validate_workflow_ref("fullsend-ai/fullsend/action.yml@main", [], ["*"])
    with pytest.raises(mint.ClaimsRejected, match="missing"):
        mint.validate_workflow_ref("", [], ["*"])


def test_provenance_is_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("FULLSEND_WORKFLOW_HOST_REPOS", "fullsend-dev/triage-target, other/repo")
    monkeypatch.setenv("FULLSEND_ALLOWED_WORKFLOW_FILES", "reusable-dispatch.yml,fullsend-trust-check.yaml")
    assert mint._provenance() == (
        ["fullsend-dev/triage-target", "other/repo"],
        ["reusable-dispatch.yml", "fullsend-trust-check.yaml"],
    )
    monkeypatch.delenv("FULLSEND_WORKFLOW_HOST_REPOS")
    monkeypatch.delenv("FULLSEND_ALLOWED_WORKFLOW_FILES")
    assert mint._provenance() == ([], [])
