#!/usr/bin/env python3
"""Development-only Fullsend token mint for the breadboard emulators.

It verifies a real Actions OIDC assertion and answers with a real GitHub App
installation token: each role is a GitHub App on the emulator, the mint holds
the Apps' private keys, and every exchange signs a short JWT as the role's App
and asks the forge for a one-hour installation token scoped to the calling
repository and the role's permission level. Nothing long-lived is handed out.

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
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import jwt
from jwt import PyJWKClient


# Each role's full ("write") permission set. The "read" level, the default
# when a request names none, is the same set with every write downgraded to
# read, as Fullsend ADR 0073 defines it.
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
LEVELS = ("read", "write")

AUDIENCE = os.environ.get("FULLSEND_OIDC_AUDIENCE", "fullsend-mint")


class ClaimsRejected(Exception):
    """The presented OIDC token is not one this mint will act on."""


class MintFailed(Exception):
    """The forge would not issue the installation token."""


def permissions_for(role: str, level: str) -> dict[str, str]:
    """The permission set a role gets at a level (ADR 0073)."""
    full = ROLE_PERMISSIONS[role]
    if level == "write":
        return dict(full)
    return {name: ("read" if value == "write" else value) for name, value in full.items()}


def parse_level(value: object) -> str:
    """An omitted or empty level is read; anything but read or write is refused."""
    level = str(value or "").strip().lower() or "read"
    if level not in LEVELS:
        raise ValueError(f"unknown level {level!r}; expected one of {', '.join(LEVELS)}")
    return level


def load_role_apps(path: str) -> dict[str, dict[str, str]]:
    """The role Apps: ``{role: {"app_id": ..., "private_key": ...}}`` from a mounted file."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise RuntimeError("role apps file must be a JSON object keyed by role")
    apps: dict[str, dict[str, str]] = {}
    for role, entry in data.items():
        if role not in ROLE_PERMISSIONS:
            raise RuntimeError(f"role apps file names unknown role {role!r}")
        if not isinstance(entry, dict) or not entry.get("app_id") or not entry.get("private_key"):
            raise RuntimeError(f"role apps entry for {role!r} needs app_id and private_key")
        apps[role] = {"app_id": str(entry["app_id"]), "private_key": str(entry["private_key"])}
    return apps


def app_assertion(app: dict[str, str]) -> str:
    """A ten-minute JWT naming the role's App, as GitHub requires."""
    now = int(time.time())
    return jwt.encode({"iat": now - 60, "exp": now + 540, "iss": app["app_id"]}, app["private_key"], algorithm="RS256")


def _forge_request(method: str, url: str, bearer: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": f"Bearer {bearer}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "fullsend-mint-dev",
        },
    )
    # The default context honours SSL_CERT_FILE, which names the internal CA.
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, context=context, timeout=15) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else None
    except urllib.error.HTTPError as exc:
        payload = exc.read()
        try:
            return exc.code, json.loads(payload) if payload else None
        except json.JSONDecodeError:
            return exc.code, payload.decode(errors="replace")
    except (urllib.error.URLError, OSError) as exc:
        raise MintFailed(f"forge unreachable: {exc}") from exc


def installation_for_owner(installations: object, owner: str) -> dict | None:
    """The App's installation on the requesting owner, if any."""
    if not isinstance(installations, list):
        return None
    for installation in installations:
        account = installation.get("account") if isinstance(installation, dict) else None
        login = (account or {}).get("login", "")
        if login.lower() == owner.lower():
            return installation
    return None


def mint_installation_token(
    forge_api: str, role: str, app: dict[str, str], owner: str, repos: list[str], level: str,
) -> dict:
    """Exchange the role App's assertion for an installation token on the owner."""
    assertion = app_assertion(app)
    status, installations = _forge_request("GET", f"{forge_api}/app/installations", assertion)
    if status != 200:
        raise MintFailed(f"could not list installations for the {role} App: HTTP {status}")
    installation = installation_for_owner(installations, owner)
    if installation is None:
        raise MintFailed(f"the {role} App is not installed on {owner}")
    permissions = permissions_for(role, level)
    status, minted = _forge_request(
        "POST", f"{forge_api}/app/installations/{installation['id']}/access_tokens", assertion,
        {"repositories": [repo.split("/", 1)[-1] for repo in repos], "permissions": permissions},
    )
    if status != 201 or not isinstance(minted, dict) or not minted.get("token"):
        raise MintFailed(f"the forge refused an installation token for {role} on {owner}: HTTP {status} {minted}")
    return {
        "token": str(minted["token"]),
        "expires_at": str(minted.get("expires_at", "")),
        "permissions": minted.get("permissions") or permissions,
        "repository_selection": minted.get("repository_selection", "selected"),
    }


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


def _config() -> tuple[dict[str, dict[str, str]], str, str, str]:
    """Role Apps, issuer, JWKS URL, and the forge API the Apps are on."""
    issuer = os.environ.get("FULLSEND_OIDC_ISSUER", "").rstrip("/")
    jwks_url = os.environ.get("FULLSEND_OIDC_JWKS_URL", "")
    if not issuer or not jwks_url:
        raise RuntimeError(
            "FULLSEND_OIDC_ISSUER and FULLSEND_OIDC_JWKS_URL must both be set; "
            "the mint verifies real OIDC tokens and cannot fall back to a "
            "shared secret"
        )
    role_apps_file = os.environ.get("FULLSEND_ROLE_APPS_FILE", "")
    if not role_apps_file:
        raise RuntimeError(
            "FULLSEND_ROLE_APPS_FILE must name the role Apps file; the mint "
            "issues installation tokens and holds no static role credentials"
        )
    forge_api = os.environ.get("FULLSEND_FORGE_API_URL", "").rstrip("/") or f"{issuer}/api/v3"
    return load_role_apps(role_apps_file), issuer, jwks_url, forge_api


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
                "roles": sorted(self.server.role_apps),
                "levels": list(LEVELS),
                "credential": "app-installation",
                "oidc": {"issuer": self.server.issuer, "audience": AUDIENCE},
            })
            return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/token":
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        role_apps, issuer, forge_api = self.server.role_apps, self.server.issuer, self.server.forge_api
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
        try:
            level = parse_level(body.get("level"))
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        if not isinstance(repos, list) or not repos or not all(
            isinstance(repo, str) and (REPO_RE.fullmatch(repo) or REPO_NAME_RE.fullmatch(repo))
            for repo in repos
        ):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "repos must contain repository names or owner/name values"})
            return
        # A bare name is resolved against the owner the token was issued
        # for, which is what an installation-scoped mint does: the caller's
        # own organization. A fixed default owner only ever fitted a stack
        # with one organization; the first repository onboarded under a
        # second one (phase2/fresh-target) had its request rewritten to
        # fullsend-dev/fresh-target and was refused as cross-repository.
        default_owner = str(claims.get("repository_owner") or "") or os.environ.get(
            "FULLSEND_DEV_DEFAULT_OWNER", "fullsend-dev"
        )
        granted_repos = [repo if "/" in repo else f"{default_owner}/{repo}" for repo in repos]

        try:
            _authorize_repos(claims, granted_repos)
        except ClaimsRejected as exc:
            self._send(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return

        app = role_apps.get(role)
        if app is None:
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": f"no App configured for role {role}"})
            return
        try:
            minted = mint_installation_token(forge_api, role, app, default_owner, granted_repos, level)
        except MintFailed as exc:
            self._send(HTTPStatus.BAD_GATEWAY, {"error": str(exc)})
            return

        self._send(HTTPStatus.OK, {
            "token": minted["token"],
            "expires_at": minted["expires_at"],
            "granted_repos": granted_repos,
            "granted_permissions": minted["permissions"],
            "repository_selection": minted["repository_selection"],
            "level": level,
            "subject": claims.get("sub", ""),
            "run_id": claims.get("run_id", ""),
            "development_only": True,
        })


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    # Fail during startup rather than serving a mint that cannot verify or mint.
    role_apps, issuer, jwks_url, forge_api = _config()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.issuer = issuer
    server.forge_api = forge_api
    server.role_apps = role_apps
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
