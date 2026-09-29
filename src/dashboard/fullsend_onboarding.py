"""Run Fullsend's own onboarding command for a repository.

Work package 7 of the Fullsend integration conformance plan. The dashboard
button runs `fullsend github setup OWNER/REPO` — the real CLI, from the
runner pod that already has it installed, its CA trust and its route to the
forge — and reports what that command did. It does not re-implement any of
it, which is what keeps the dashboard from drifting away from the CLI and
keeps Fullsend's own pull-request review step in the loop.

Two rules from the plan shape this module.

**Always deliver through a pull request.** `--direct` pushes the scaffold
straight to the default branch, which skips the review a maintainer is
supposed to give generated workflow files. It is not exposed here, and the
argument list is built rather than passed through, so a caller cannot smuggle
it in.

**Never return the credential.** The token is passed to the command through
its environment and the result carries the argument list, exit code and
output — not the environment. `redact()` is applied to the output as well,
because a CLI that echoes its own configuration on failure would otherwise
put the token in a dashboard response.
"""

from __future__ import annotations

import os
import re
import shlex
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import requests

# OWNER/REPO, the shape the CLI's per-repo mode takes. An org-only argument
# puts the CLI into per-org mode, which creates a config repository and is a
# much larger action than this button offers.
_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")

# The branch Fullsend opens its scaffold pull request from.
SCAFFOLD_BRANCH = "fullsend/scaffold-install"


class OnboardingError(RuntimeError):
    """Raised when onboarding cannot be attempted or could not be understood."""


@dataclass
class OnboardingResult:
    """What the run did, in terms the dashboard can render."""

    repository: str
    status: str  # "created" | "already-open" | "failed"
    command: list[str] = field(default_factory=list)
    exit_code: int | None = None
    output: str = ""
    pull_request_url: str | None = None
    # Where a human can actually open it: the CLI's URL is the canonical
    # GitHub shape, which this forge's web UI does not serve.
    pull_request_browse_url: str | None = None
    pull_request_number: int | None = None
    branch: str | None = None
    message: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "status": self.status,
            "command": self.command,
            "exit_code": self.exit_code,
            "output": self.output,
            "pull_request_url": self.pull_request_url,
            "pull_request_browse_url": self.pull_request_browse_url,
            "pull_request_number": self.pull_request_number,
            "branch": self.branch,
            "message": self.message,
        }


def redact(text: str, secrets: list[str]) -> str:
    """Remove known secret values from text before it leaves the backend."""
    for secret in secrets:
        if secret and len(secret) >= 8:
            text = text.replace(secret, "***")
    return text


class OnboardingConfig:
    """Where the command runs and what it is told about this environment."""

    def __init__(self) -> None:
        self.namespace = os.getenv("FULLSEND_ONBOARD_NAMESPACE", "ai-pipeline")
        self.deployment = os.getenv(
            "FULLSEND_ONBOARD_DEPLOYMENT", "github-actions-runner"
        )
        self.api_url = os.getenv(
            "GITHUB_API_URL",
            "https://github-emulator.ai-pipeline.svc.cluster.local/api/v3",
        ).rstrip("/")
        self.server_url = os.getenv("GITHUB_SERVER_URL", "https://github.local").rstrip("/")
        self.mint_url = os.getenv("FULLSEND_MINT_URL", "")
        self.inference_project = os.getenv("FULLSEND_GCP_PROJECT_ID", "")
        self.inference_wif_provider = os.getenv("FULLSEND_GCP_WIF_PROVIDER", "")
        self.runtime = os.getenv("FULLSEND_ONBOARD_RUNTIME", "claude")
        # Passed through to the CLI so the scaffold targets this stack's
        # runners rather than a GitHub-hosted image name.
        self.runner_image = os.getenv("FULLSEND_RUNNER_IMAGE", "")
        # Where a human opens the pull request. The CLI reports the canonical
        # GitHub shape, <host>/<owner>/<repo>/pull/<n>, which this emulator
        # does not serve: its web UI lives under /ui/ and uses "pulls".
        # Linking the CLI's URL gives a 404, so the browse URL is built from a
        # template that can be set per forge — the default is this emulator's
        # shape, and a real GitHub deployment sets the canonical one.
        self.ui_url = os.getenv("GITHUB_UI_URL", "https://github.local").rstrip("/")
        self.pull_url_template = os.getenv(
            "FULLSEND_ONBOARD_PULL_URL_TEMPLATE",
            "{ui}/ui/{owner}/{repo}/pulls/{number}",
        )
        self.timeout = float(os.getenv("FULLSEND_ONBOARD_TIMEOUT", "420"))
        self.verify_tls = os.getenv("FULLSEND_ONBOARD_VERIFY_TLS", "0") == "1"


def _onboarding_app() -> tuple[str, str, str] | None:
    """The onboarding App's id, installation id, and private key, if seeded.

    Read from files in ``FULLSEND_ONBOARD_APP_DIR`` rather than from the
    environment: the directory is a mounted Secret, which the kubelet keeps
    current, so a stack seeded after the dashboard started still finds the
    App without a restart. Absent or incomplete means "no App", not an error.
    """
    directory = os.getenv("FULLSEND_ONBOARD_APP_DIR", "").strip()
    if not directory:
        return None

    def read(name: str) -> str:
        path = Path(directory) / name
        try:
            return path.read_text().strip() if path.is_file() else ""
        except OSError:
            return ""

    app_id, installation_id, key = read("app-id"), read("installation-id"), read("private-key")
    if not (app_id and installation_id and key):
        return None
    return app_id, installation_id, key


def _app_assertion(app_id: str, key: str) -> str:
    import jwt  # PyJWT, with cryptography for RS256

    now = int(time.time())
    return jwt.encode({"iat": now - 60, "exp": now + 540, "iss": app_id}, key, algorithm="RS256")


def _installation_for(config: "OnboardingConfig", assertion: str, owner: str) -> int | None:
    """The onboarding App's installation on ``owner``, or None."""
    try:
        response = requests.get(
            f"{config.api_url}/app/installations",
            headers={"Authorization": f"Bearer {assertion}", "Accept": "application/vnd.github+json"},
            timeout=15,
            verify=config.verify_tls,
        )
    except requests.RequestException as exc:
        raise OnboardingError(f"could not list the onboarding App's installations: {exc}") from exc
    if response.status_code != 200:
        raise OnboardingError(
            f"the forge refused to list the onboarding App's installations (HTTP {response.status_code})"
        )
    for installation in response.json() or []:
        login = ((installation.get("account") or {}).get("login") or "")
        if login.lower() == owner.lower():
            return int(installation["id"])
    return None


def enrol_owner(config: "OnboardingConfig", owner: str) -> list[str]:
    """Install every Fullsend App on ``owner``, the way an organisation's
    administrator installs them on GitHub before the first repository is
    onboarded.

    An owner the Apps are not installed on cannot be onboarded (the
    onboarding App has no installation to mint from) and cannot run agents
    (the mint finds no role App installed there). Both are one act on
    GitHub, install the Apps on the organisation, and the dashboard performs
    it with the emulator's admin API, which is the only place that act
    exists here. Repository selection "all", so later repositories in the
    owner are covered. Returns the slugs that were newly installed.
    """
    token = os.getenv("GITHUB_EMULATOR_TOKEN", "").strip()
    if not token:
        raise OnboardingError(
            f"the Fullsend Apps are not installed on {owner} and no admin credential "
            "is available to install them"
        )
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    try:
        listed = requests.get(
            f"{config.server_url}/admin/api/apps", headers=headers, timeout=15, verify=config.verify_tls,
        )
    except requests.RequestException as exc:
        raise OnboardingError(f"could not list the forge's Apps: {exc}") from exc
    if listed.status_code != 200:
        raise OnboardingError(f"the forge refused the App listing (HTTP {listed.status_code})")
    installed: list[str] = []
    for app in listed.json() or []:
        slug = str(app.get("slug") or "")
        if not (slug.startswith("fullsend") or slug == "breadboard-onboarding"):
            continue
        owners = {str(i.get("owner") or "").lower() for i in (app.get("installations") or [])}
        if owner.lower() in owners:
            continue
        created = requests.post(
            f"{config.api_url}/admin/apps/{app['app_id']}/installations",
            headers=headers,
            json={"account_login": owner, "account_type": "Organization", "repositories": []},
            timeout=15,
            verify=config.verify_tls,
        )
        if created.status_code not in (200, 201):
            raise OnboardingError(
                f"could not install {slug} on {owner} (HTTP {created.status_code}): {created.text[:200]}"
            )
        installed.append(slug)
    return installed


def mint_installation_token(config: "OnboardingConfig", repository: str) -> tuple[str, list[str]]:
    """Exchange the onboarding App's key for a one-hour installation token.

    The plan's rule: a short-lived GitHub App installation token with repo
    and workflow write scope only. The App's private key signs a ten-minute
    JWT naming the App, the forge answers with a ``ghs_`` token scoped to the
    one repository being onboarded and the installation's permissions, and
    the token expires on its own after an hour. The key never leaves this
    process and the token never reaches the browser.

    The installation is the one on the repository's owner, looked up rather
    than assumed: the seeded installation is on the seed organisation, and a
    repository elsewhere minted against it got a token for a repository of
    the wrong owner and then Not Found on its own (2026-09-29,
    experiment/testrepo). An owner with no installation is enrolled first.
    The repository is named in full for the same reason. Returns the token
    and the App slugs newly installed on the way.
    """
    app = _onboarding_app()
    if app is None:
        raise OnboardingError("no onboarding App is seeded")
    app_id, _seeded_installation, key = app
    owner = repository.split("/", 1)[0]
    assertion = _app_assertion(app_id, key)
    enrolled: list[str] = []
    installation_id = _installation_for(config, assertion, owner)
    if installation_id is None:
        enrolled = enrol_owner(config, owner)
        installation_id = _installation_for(config, assertion, owner)
        if installation_id is None:
            raise OnboardingError(f"the onboarding App is still not installed on {owner}")
    try:
        response = requests.post(
            f"{config.api_url}/app/installations/{installation_id}/access_tokens",
            headers={"Authorization": f"Bearer {assertion}", "Accept": "application/vnd.github+json"},
            json={"repositories": [repository]},
            timeout=15,
            verify=config.verify_tls,
        )
    except requests.RequestException as exc:
        raise OnboardingError(f"could not reach the forge to mint an installation token: {exc}") from exc
    if response.status_code != 201:
        raise OnboardingError(
            f"the forge refused to mint an installation token for {repository} "
            f"(HTTP {response.status_code}): {response.text[:200]}"
        )
    token = str(response.json().get("token", "")).strip()
    if not token:
        raise OnboardingError("the forge minted no token")
    return token, enrolled


def resolve_credential(config: "OnboardingConfig | None" = None, repository: str = "") -> tuple[str, str, list[str]]:
    """Return ``(token, kind)`` for the onboarding run.

    The plan asks for a short-lived GitHub App installation token scoped to
    repo and workflow writes, and calls a stored personal token "a
    deliberately scoped local fallback". In order: a token handed in ready
    made, one minted from the seeded onboarding App's key for this
    repository, and only then the fallbacks. A seeded App that fails to mint
    is an error, not a reason to fall back: the fallback is for a stack that
    has no App, and using it silently would hide a broken exchange behind an
    admin credential. The caller surfaces `kind` so the dashboard can show
    which was used.
    """
    app_token = os.getenv("FULLSEND_ONBOARD_APP_TOKEN", "").strip()
    if app_token:
        return app_token, "app-installation", []
    if repository and _onboarding_app() is not None:
        token, enrolled = mint_installation_token(config or OnboardingConfig(), repository)
        return token, "app-installation", enrolled
    # GITHUB_EMULATOR_TOKEN before GITHUB_TOKEN: this deployment carries both,
    # and they are credentials for different forges. Reading the wrong one
    # handed the CLI a token the forge refuses, which surfaced as a 401
    # several minutes into a run and looked like a Fullsend bug.
    token = os.getenv("GITHUB_EMULATOR_TOKEN", "").strip()
    if token:
        return token, "emulator-admin-fallback", []
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise OnboardingError(
            "No credential available for onboarding. Set FULLSEND_ONBOARD_APP_TOKEN "
            "to a GitHub App installation token, or GITHUB_EMULATOR_TOKEN for the "
            "local fallback."
        )
    return token, "personal-fallback", []


def verify_credential(config: "OnboardingConfig", token: str) -> None:
    """Fail fast if the forge will not accept the credential.

    The CLI takes minutes and does its own work before it first authenticates,
    so a credential the forge refuses arrives as an error deep in its output
    about whatever call happened to be first. One cheap call up front turns
    that into a credential problem stated as one.
    """
    try:
        response = requests.get(
            f"{config.api_url}/user",
            headers={"Authorization": f"token {token}"},
            timeout=10,
            verify=config.verify_tls,
        )
    except requests.RequestException as exc:
        raise OnboardingError(
            f"could not reach the forge at {config.api_url}: {exc}"
        ) from exc
    if response.status_code in (401, 403):
        raise OnboardingError(
            f"the forge at {config.api_url} refused the onboarding credential "
            f"(HTTP {response.status_code}). Check the seeded onboarding App, "
            "GITHUB_EMULATOR_TOKEN, or FULLSEND_ONBOARD_APP_TOKEN."
        )


def find_open_scaffold_pr(
    repository: str, config: OnboardingConfig, token: str
) -> dict[str, Any] | None:
    """Return an open scaffold pull request for the repository, if any.

    Repeating the action must not create duplicate state. Fullsend's own
    command is not relied on to decide that: asking the forge is both cheaper
    and answers the question the dashboard is actually asking, which is
    whether a maintainer already has something to review.
    """
    url = f"{config.api_url}/repos/{repository}/pulls"
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"token {token}"},
            params={"state": "open", "per_page": 100},
            timeout=15,
            verify=config.verify_tls,
        )
    except requests.RequestException as exc:
        raise OnboardingError(f"could not reach the forge at {config.api_url}: {exc}") from exc
    if response.status_code == 404:
        raise OnboardingError(f"repository not found: {repository}")
    if response.status_code >= 400:
        raise OnboardingError(
            f"forge refused the pull request listing for {repository}: "
            f"HTTP {response.status_code}"
        )
    for pull in response.json():
        if (pull.get("head") or {}).get("ref") == SCAFFOLD_BRANCH:
            return pull
    return None


def build_command(repository: str, config: OnboardingConfig) -> list[str]:
    """Build the CLI argument list.

    Built rather than accepted from the caller so that --direct cannot be
    introduced from outside this module.
    """
    command = [
        "fullsend", "github", "setup", repository,
        "--skip-app-setup",
        "--runtime", config.runtime,
    ]
    if config.mint_url:
        command += ["--mint-url", config.mint_url]
    if config.inference_project:
        command += ["--inference-project", config.inference_project]
    if config.inference_wif_provider:
        command += ["--inference-wif-provider", config.inference_wif_provider]
    return command


def browse_url(repository: str, number: int | None, config: OnboardingConfig) -> str | None:
    """Build a pull request URL a browser can open on this forge."""
    if not number or "/" not in repository:
        return None
    owner, repo = repository.split("/", 1)
    return config.pull_url_template.format(
        ui=config.ui_url, owner=owner, repo=repo, number=number
    )


def _parse_pull_request(output: str) -> tuple[str | None, int | None]:
    """Pull the PR URL and number out of the CLI's output."""
    match = re.search(r"Created PR #(\d+):\s*(\S+)", output)
    if match:
        return match.group(2), int(match.group(1))
    match = re.search(r"(https?://\S+/pull/(\d+))", output)
    if match:
        return match.group(1), int(match.group(2))
    return None, None


def onboard_repository(
    repository: str,
    *,
    config: OnboardingConfig | None = None,
    runner: Callable[[list[str], dict[str, str], float], tuple[int, str]] | None = None,
) -> OnboardingResult:
    """Run Fullsend's onboarding for one repository.

    ``runner`` executes the argument list in the runner pod and returns
    ``(exit_code, combined_output)``. It is injectable so the operation can be
    tested without a cluster.
    """
    repository = (repository or "").strip()
    if not _REPO_RE.match(repository):
        raise OnboardingError(
            f"expected OWNER/REPO, got {repository!r}. An organisation on its own "
            "puts the CLI into per-org mode, which is a larger action than this."
        )

    config = config or OnboardingConfig()
    token, credential_kind, enrolled = resolve_credential(config, repository)
    enrolment_note = (
        f" Installed the Fullsend Apps on {repository.split('/', 1)[0]} first "
        f"({', '.join(enrolled)}); add that owner to the mint's FULLSEND_ALLOWED_ORGS "
        "before running agents there."
        if enrolled else ""
    )
    verify_credential(config, token)

    existing = find_open_scaffold_pr(repository, config, token)
    if existing is not None:
        return OnboardingResult(
            repository=repository,
            status="already-open",
            pull_request_url=existing.get("html_url"),
            pull_request_browse_url=browse_url(repository, existing.get("number"), config),
            pull_request_number=existing.get("number"),
            branch=SCAFFOLD_BRANCH,
            message=(
                f"{repository} already has an open scaffold pull request. "
                "Merge or close it before onboarding again."
            ),
        )

    command = build_command(repository, config)
    env = {
        "GH_TOKEN": token,
        "GITHUB_API_URL": config.api_url,
        "GITHUB_SERVER_URL": config.server_url,
    }
    if config.runner_image:
        env["FULLSEND_RUNNER_IMAGE"] = config.runner_image

    if runner is None:
        runner = _exec_in_runner_pod
    exit_code, output = runner(command, env, config.timeout)
    output = redact(output, [token])

    pr_url, pr_number = _parse_pull_request(output)
    if exit_code == 0:
        return OnboardingResult(
            repository=repository,
            status="created",
            command=command,
            exit_code=exit_code,
            output=output,
            pull_request_url=pr_url,
            pull_request_browse_url=browse_url(repository, pr_number, config),
            pull_request_number=pr_number,
            branch=SCAFFOLD_BRANCH,
            message=(
                f"Onboarded {repository} using a {credential_kind} credential.{enrolment_note} "
                "Review and merge the scaffold pull request to activate it."
            ),
        )

    return OnboardingResult(
        repository=repository,
        status="failed",
        command=command,
        exit_code=exit_code,
        output=output,
        pull_request_url=pr_url,
        pull_request_browse_url=browse_url(repository, pr_number, config),
        pull_request_number=pr_number,
        branch=SCAFFOLD_BRANCH,
        message=f"fullsend github setup exited {exit_code} for {repository}.",
    )


def _exec_in_runner_pod(
    command: list[str], env: dict[str, str], timeout: float
) -> tuple[int, str]:
    """Run the command in the runner pod and return (exit_code, output).

    The runner pod is where the CLI already lives, with the forge's CA in its
    trust store and a route to it. Running it there rather than in the
    dashboard pod keeps one installation of the binary rather than two that
    can differ.
    """
    from kubernetes import client, config as k8s_config
    from kubernetes.stream import stream as k8s_stream

    try:
        k8s_config.load_incluster_config()
    except Exception:  # noqa: BLE001 - outside a cluster during development
        k8s_config.load_kube_config()

    core = client.CoreV1Api()
    cfg = OnboardingConfig()
    pods = core.list_namespaced_pod(
        namespace=cfg.namespace,
        label_selector=f"app={cfg.deployment}",
        field_selector="status.phase=Running",
    )
    running = [p for p in pods.items if p.status.phase == "Running"]
    if not running:
        raise OnboardingError(
            f"no running pod with label app={cfg.deployment} in {cfg.namespace}"
        )

    exports = " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items())
    script = f"export {exports}; exec {shlex.join(command)} 2>&1"

    resp = k8s_stream(
        core.connect_get_namespaced_pod_exec,
        running[0].metadata.name,
        cfg.namespace,
        command=["sh", "-c", script],
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
        _preload_content=False,
    )
    chunks: list[str] = []
    resp.run_forever(timeout=timeout)
    chunks.append(resp.read_stdout() or "")
    chunks.append(resp.read_stderr() or "")
    # returncode is exposed through the exec channel's status payload.
    status = resp.read_channel(3) if hasattr(resp, "read_channel") else ""
    resp.close()
    output = "".join(chunks)
    exit_code = 0 if '"status":"Success"' in (status or "") else 1
    if exit_code != 0:
        match = re.search(r'"ExitCode":\s*"?(\d+)"?', status or "")
        if match:
            exit_code = int(match.group(1))
    return exit_code, output
