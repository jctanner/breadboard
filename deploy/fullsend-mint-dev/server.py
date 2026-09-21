#!/usr/bin/env python3
"""Development-only Fullsend token mint for the breadboard emulators.

This is not a GitHub App implementation: it returns pre-created, bot-owned
emulator personal access tokens selected by role rather than installation
tokens. What it *is* now is a real OIDC verifier.

It used to accept one opaque shared string that both the runner pod and this
service held in their environment. That made the mint's repository and role
checks decorative: any process anywhere in the cluster that could read the
secret could ask for any role on any repository, and nothing in the request
tied the caller to a workflow run. The emulator now issues a signed Actions
OIDC token whose claims describe the run that asked for it, so this service
verifies the signature against the emulator's JWKS and authorizes against the
claims:

- the signature must verify against a key the emulator publishes;
- ``iss`` must be the configured issuer and ``aud`` the configured audience;
- ``exp``/``nbf`` must be current; and
- every repository named in ``repos`` must be the repository the token was
  issued for.

That last check is the one that matters: a run in one repository can no longer
mint a credential for another.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import threading
import time
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import jwt
from jwt import PyJWKClient


ROLE_PERMISSIONS = {
    "triage": {"contents": "read", "issues": "write", "metadata": "read"},
    "scribe": {"contents": "read", "issues": "write", "metadata": "read"},
    "coder": {"contents": "write", "issues": "write", "pull_requests": "write", "metadata": "read"},
    "review": {"contents": "read", "issues": "write", "pull_requests": "write", "metadata": "read"},
    "fix": {"contents": "write", "issues": "write", "pull_requests": "write", "metadata": "read"},
    "fullsend": {"contents": "write", "issues": "write", "pull_requests": "write", "metadata": "read"},
}
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REPO_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

AUDIENCE = os.environ.get("FULLSEND_OIDC_AUDIENCE", "fullsend-mint")


class ClaimsRejected(Exception):
    """The presented OIDC token is not one this mint will act on."""


class _JwksCache:
    """Fetch and cache the emulator's signing keys.

    The emulator generates its key pair at startup, so a reset changes the
    key. Cache briefly and refetch on an unknown ``kid`` rather than pinning,
    which would make the mint outlive the issuer it trusts.
    """

    def __init__(self, url: str, ttl_seconds: int = 300):
        self._url = url
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._client: PyJWKClient | None = None
        self._fetched_at = 0.0

    def signing_key(self, token: str):
        for attempt in (0, 1):
            client = self._client_for(force=attempt == 1)
            try:
                return client.get_signing_key_from_jwt(token)
            except Exception:
                if attempt == 1:
                    raise
        raise ClaimsRejected("no signing key available")

    def _client_for(self, force: bool) -> PyJWKClient:
        with self._lock:
            stale = (time.monotonic() - self._fetched_at) > self._ttl
            if force or stale or self._client is None:
                self._client = PyJWKClient(self._url, cache_keys=False)
                self._fetched_at = time.monotonic()
            return self._client


def _config() -> tuple[dict[str, str], str, str]:
    try:
        tokens = json.loads(os.environ.get("FULLSEND_ROLE_TOKENS", "{}"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("FULLSEND_ROLE_TOKENS is not valid JSON") from exc
    if not isinstance(tokens, dict):
        raise RuntimeError("FULLSEND_ROLE_TOKENS must be a JSON object")
    issuer = os.environ.get("FULLSEND_OIDC_ISSUER", "").rstrip("/")
    jwks_url = os.environ.get("FULLSEND_OIDC_JWKS_URL", "")
    if not issuer or not jwks_url:
        raise RuntimeError(
            "FULLSEND_OIDC_ISSUER and FULLSEND_OIDC_JWKS_URL must both be set; "
            "the mint verifies real OIDC tokens and cannot fall back to a "
            "shared secret"
        )
    return {str(k): str(v) for k, v in tokens.items()}, issuer, jwks_url


def _verify(token: str, issuer: str, jwks: _JwksCache) -> dict:
    try:
        key = jwks.signing_key(token)
    except Exception as exc:  # network, malformed token, unknown kid
        raise ClaimsRejected(f"signing key lookup failed: {exc}") from exc
    try:
        return jwt.decode(
            token,
            key.key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub", "aud", "iss"]},
        )
    except jwt.InvalidTokenError as exc:
        raise ClaimsRejected(str(exc)) from exc


def _authorize_repos(claims: dict, granted_repos: list[str]) -> None:
    """Refuse any repository the presented token was not issued for."""
    subject_repo = str(claims.get("repository") or "")
    if not subject_repo:
        raise ClaimsRejected("token carries no repository claim")
    outside = sorted({repo for repo in granted_repos if repo != subject_repo})
    if outside:
        raise ClaimsRejected(
            f"token was issued for {subject_repo} and cannot mint for "
            + ", ".join(outside)
        )


class Handler(BaseHTTPRequestHandler):
    server_version = "fullsend-mint-dev/2"

    def log_message(self, _format: str, *_args: object) -> None:
        # Never log Authorization headers or token response bodies.
        return

    def _send(self, status: int, body: dict) -> None:
        payload = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok", "mode": "development-only"})
            return
        if self.path == "/v1/status":
            self._send(HTTPStatus.OK, {
                "status": "ok",
                "mode": "development-only",
                "roles": sorted(ROLE_PERMISSIONS),
                "oidc": {"issuer": self.server.issuer, "audience": AUDIENCE},
            })
            return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/token":
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        tokens, issuer, _ = _config()
        scheme, _, presented = self.headers.get("Authorization", "").partition(" ")
        if scheme.lower() != "bearer" or not presented:
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "OIDC token required"})
            return

        try:
            claims = _verify(presented, issuer, self.server.jwks)
        except ClaimsRejected as exc:
            self._send(HTTPStatus.UNAUTHORIZED, {"error": f"OIDC token rejected: {exc}"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "request body must be JSON"})
            return

        role = str(body.get("role", ""))
        repos = body.get("repos", [])
        if role not in ROLE_PERMISSIONS:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "unknown role"})
            return
        if not isinstance(repos, list) or not repos or not all(
            isinstance(repo, str) and (REPO_RE.fullmatch(repo) or REPO_NAME_RE.fullmatch(repo))
            for repo in repos
        ):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "repos must contain repository names or owner/name values"})
            return
        default_owner = os.environ.get("FULLSEND_DEV_DEFAULT_OWNER", "fullsend-dev")
        granted_repos = [repo if "/" in repo else f"{default_owner}/{repo}" for repo in repos]

        try:
            _authorize_repos(claims, granted_repos)
        except ClaimsRejected as exc:
            self._send(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        token = tokens.get(role) or tokens.get("fullsend")
        if not token:
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": f"no emulator token configured for role {role}"})
            return

        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        self._send(HTTPStatus.OK, {
            "token": token,
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "granted_repos": granted_repos,
            "granted_permissions": ROLE_PERMISSIONS[role],
            "repository_selection": "selected",
            "subject": claims.get("sub", ""),
            "run_id": claims.get("run_id", ""),
            "development_only": True,
        })


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    # Fail during startup rather than serving a mint that cannot verify.
    _tokens, issuer, jwks_url = _config()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.issuer = issuer
    server.jwks = _JwksCache(jwks_url)

    # Serve TLS when a certificate is mounted. Fullsend refuses a non-HTTPS
    # mint URL at install time, and an OIDC assertion should not cross the
    # cluster in the clear on its way to being exchanged for a credential.
    cert = os.environ.get("FULLSEND_MINT_TLS_CERT", "")
    key = os.environ.get("FULLSEND_MINT_TLS_KEY", "")
    if cert and key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)

    server.serve_forever()


if __name__ == "__main__":
    main()
