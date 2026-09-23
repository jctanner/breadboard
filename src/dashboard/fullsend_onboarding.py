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
from dataclasses import dataclass, field
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


def resolve_credential() -> tuple[str, str]:
    """Return ``(token, kind)`` for the onboarding run.

    The plan asks for a short-lived GitHub App installation token scoped to
    repo and workflow writes, and calls a stored personal token "a
    deliberately scoped local fallback". Minting an installation token needs
    the App's private key to sign a JWT, and nothing in this deployment holds
    one — the seeded App reports ``private_key_returned: false`` and no
    secret carries it. So this returns the fallback and *says which it is*,
    rather than presenting a personal token as though the rule were met. The
    caller surfaces `kind` so the dashboard can show it.
    """
    app_token = os.getenv("FULLSEND_ONBOARD_APP_TOKEN", "").strip()
    if app_token:
        return app_token, "app-installation"
    # GITHUB_EMULATOR_TOKEN before GITHUB_TOKEN: this deployment carries both,
    # and they are credentials for different forges. Reading the wrong one
    # handed the CLI a token the forge refuses, which surfaced as a 401
    # several minutes into a run and looked like a Fullsend bug.
    token = os.getenv("GITHUB_EMULATOR_TOKEN", "").strip()
    if token:
        return token, "emulator-admin-fallback"
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise OnboardingError(
            "No credential available for onboarding. Set FULLSEND_ONBOARD_APP_TOKEN "
            "to a GitHub App installation token, or GITHUB_EMULATOR_TOKEN for the "
            "local fallback."
        )
    return token, "personal-fallback"


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
            f"(HTTP {response.status_code}). Check GITHUB_EMULATOR_TOKEN, or set "
            "FULLSEND_ONBOARD_APP_TOKEN."
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
    token, credential_kind = resolve_credential()
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
                f"Onboarded {repository} using a {credential_kind} credential. "
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
