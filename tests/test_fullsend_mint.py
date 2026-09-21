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
