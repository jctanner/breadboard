"""Script-entrypoint jobs: validate a script spec and build its command.

A script job runs the usual job setup (Vertex/relay, MLflow tracing, OTel,
strace, API dumps) and then a script instead of ``claude -p``. The script
comes from a known place only:

- the image: a path under ``var/benchmarks/`` (the pipeline-agent image
  copies Breadboard's ``var/`` to ``/app/var/``); or
- a repository clone at a pinned commit: ``repo`` (https URL on an allowed
  host), ``ref`` (full 40-character commit) and ``path`` inside the clone.
"""

import os
import posixpath
import re
from urllib.parse import urlparse

RUN_SCRIPT = "/app/scripts/run_script.sh"
IMAGE_SCRIPT_PREFIX = "var/benchmarks/"


def get_allowed_script_hosts() -> set[str]:
    domain = os.getenv("BREADBOARD_DOMAIN", "local").strip().strip(".") or "local"
    hosts = {"github.com", "github.local", "gitlab.local"}
    if domain != "local":
        hosts.add(f"github.{domain}")
        hosts.add(f"gitlab.{domain}")
    return hosts


ALLOWED_SCRIPT_HOSTS = get_allowed_script_hosts()
MAX_SCRIPT_ARGS = 32
MAX_SCRIPT_ARG_LEN = 4096

_REF = re.compile(r"^[0-9a-f]{40}$")


def _clean_path(path) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("script.path must be a non-empty string")
    path = path.strip()
    if path.startswith("/") or "\\" in path:
        raise ValueError("script.path must be a relative path")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("script.path must not contain empty, '.' or '..' segments")
    return posixpath.normpath(path)


def normalize_script_spec(spec) -> dict:
    """Validate a script spec from the job API and return its normal form.

    Raises ValueError with a message suitable for an HTTP 400 response.
    """
    if not isinstance(spec, dict):
        raise ValueError("script must be an object")
    unknown = set(spec) - {"path", "args", "repo", "ref"}
    if unknown:
        raise ValueError(f"unknown script fields: {', '.join(sorted(unknown))}")

    path = _clean_path(spec.get("path"))

    args = spec.get("args") or []
    if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
        raise ValueError("script.args must be a list of strings")
    if len(args) > MAX_SCRIPT_ARGS:
        raise ValueError(f"script.args allows at most {MAX_SCRIPT_ARGS} arguments")
    if any(len(a) > MAX_SCRIPT_ARG_LEN for a in args):
        raise ValueError(f"script.args entries must be at most {MAX_SCRIPT_ARG_LEN} characters")

    repo = spec.get("repo")
    ref = spec.get("ref")
    if repo is None and ref is None:
        if not path.startswith(IMAGE_SCRIPT_PREFIX):
            raise ValueError(
                f"an image script must be under {IMAGE_SCRIPT_PREFIX}; "
                "give repo and ref to run a script from a clone"
            )
        return {"source": "image", "path": path, "args": list(args)}

    if not isinstance(repo, str) or not isinstance(ref, str):
        raise ValueError("script.repo and script.ref must be given together")
    parsed = urlparse(repo.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("script.repo must be an https URL")
    allowed_hosts = get_allowed_script_hosts()
    if parsed.hostname not in allowed_hosts:
        raise ValueError(
            f"script.repo host must be one of {', '.join(sorted(allowed_hosts))}"
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("script.repo must not carry credentials, a query or a fragment")
    ref = ref.strip()
    if not _REF.match(ref):
        raise ValueError("script.ref must be a full 40-character commit")
    return {"source": "repo", "repo": repo.strip(), "ref": ref, "path": path, "args": list(args)}


def script_phase(spec: dict) -> str:
    """Phase label for a script job: ``script-<file name without extension>``."""
    name = posixpath.splitext(posixpath.basename(spec["path"]))[0]
    return "script-" + (re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-") or "run")


def script_cmd_args(spec: dict, model: str, issue_key: str = "") -> list:
    """Container command for a normalized script spec."""
    cmd = ["/bin/bash", RUN_SCRIPT, "--path", spec["path"], "--model", model]
    if spec["source"] == "repo":
        cmd.extend(["--repo", spec["repo"], "--ref", spec["ref"]])
    if issue_key:
        cmd.extend(["--issue", issue_key])
    cmd.append("--")
    cmd.extend(spec["args"])
    return cmd
