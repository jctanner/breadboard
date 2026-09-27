#!/usr/bin/env python3
"""Turn triage's auto-promotion off on the conformance target.

Fullsend's triage harness sets ``TRIAGE_AUTO_CODE: "on"``: an issue triaged
into a low-risk category (bug, documentation, performance) is labelled
``ready-to-code``, and that label starts the code agent. Conformance issues
are documentation gaps, so every green conformance triage fired a code stage
nobody asked for, which then had to be cancelled by hand.

This is configuration, not a substitution. Fullsend ADR 0080 places the knob
in the harness ``env.runner`` layer and names the per-repository override
path: a ``.fullsend/triage.yaml`` composed with ``base:`` on the upstream
harness, referenced from ``config.yaml``'s ``agents`` list. That is what this
writes, pinned to the mirror's current commit and the harness's content hash
as the CLI requires, so a reset restores it and a mirror update re-pins it.

Idempotent: it rewrites only what differs.
"""

from __future__ import annotations

import base64
import hashlib
import ssl
import sys
import urllib.request
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emulator import BASE_URL, ORG, REPO, api_request  # noqa: E402

AGENTS_REPO = "fullsend-ai/agents"
HARNESS_PATH = ".fullsend/triage.yaml"
CONFIG_PATH = ".fullsend/config.yaml"


def _get_file(path: str) -> tuple[str | None, str | None]:
    status, payload = api_request("GET", f"/repos/{ORG}/{REPO}/contents/{path}")
    if status == 404:
        return None, None
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"{ORG}/{REPO}:{path}: HTTP {status}")
    return base64.b64decode(payload["content"]).decode(), payload["sha"]


def _put_file(path: str, content: str, message: str, sha: str | None) -> None:
    body = {"message": message, "content": base64.b64encode(content.encode()).decode(), "branch": "main"}
    if sha:
        body["sha"] = sha
    status, response = api_request("PUT", f"/repos/{ORG}/{REPO}/contents/{path}", body)
    if status not in (200, 201):
        raise RuntimeError(f"write {path} failed: HTTP {status}: {response}")


def _mirror_pin() -> tuple[str, str]:
    """The mirror's main commit and the sha256 of harness/triage.yaml there."""
    status, commit = api_request("GET", f"/repos/{AGENTS_REPO}/commits/main")
    if status != 200 or not isinstance(commit, dict):
        raise RuntimeError(f"cannot read {AGENTS_REPO} main: HTTP {status}")
    sha = commit["sha"]
    url = f"{BASE_URL}/{AGENTS_REPO}/raw/{sha}/harness/triage.yaml"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(url, context=ctx) as resp:
        raw = resp.read()
    return sha, hashlib.sha256(raw).hexdigest()


def main() -> None:
    sha, digest = _mirror_pin()
    harness = (
        "# Conformance target: triage classifies and labels, and never promotes to\n"
        "# ready-to-code on its own. Fullsend ADR 0080 puts this knob in the harness\n"
        "# env.runner layer and names this file, composed on the upstream harness,\n"
        "# as the per-repository override. Written by\n"
        "# deploy/fullsend/seed/seed-triage-auto-code-off.py; the pin follows the\n"
        "# agents mirror's main.\n"
        f"base: {BASE_URL}/{AGENTS_REPO}/raw/{sha}/harness/triage.yaml#sha256={digest}\n"
        "env:\n"
        "  runner:\n"
        '    TRIAGE_AUTO_CODE: "off"\n'
    )
    current, hsha = _get_file(HARNESS_PATH)
    if current != harness:
        _put_file(HARNESS_PATH, harness, "Conformance: triage does not auto-promote to ready-to-code", hsha)
        print(f"wrote {HARNESS_PATH} (base pinned to {sha[:12]})")
    else:
        print(f"{HARNESS_PATH} already current")

    raw, csha = _get_file(CONFIG_PATH)
    if raw is None:
        raise RuntimeError(f"{CONFIG_PATH} not found; install the per-repo scaffold first")
    config = yaml.safe_load(raw) or {}
    agents = list(config.get("agents") or [])
    entry = {"name": "triage", "source": "triage.yaml"}
    existing = next((a for a in agents if isinstance(a, dict) and a.get("name") == "triage"), None)
    if existing == entry:
        print(f"{CONFIG_PATH} already references {HARNESS_PATH}")
        return
    if existing is not None:
        existing.clear()
        existing.update(entry)
    else:
        agents.append(entry)
    config["agents"] = agents
    updated = yaml.safe_dump(config, sort_keys=False, default_flow_style=False)
    _put_file(CONFIG_PATH, updated, "Conformance: reference the triage harness override", csha)
    print(f"referenced {HARNESS_PATH} from {CONFIG_PATH}")


if __name__ == "__main__":
    main()
