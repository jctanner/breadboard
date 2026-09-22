#!/usr/bin/env python3
"""Allow the local forge in the target repository's remote-resource allowlist.

Fullsend refuses to fetch a remote resource whose URL does not match a prefix
in `allowed_remote_resources`. The scaffolded config lists the public raw host,
which is correct on github.com and useless here: the CLI now resolves agent
definitions against this emulator, so the URL it builds starts with the
emulator's own host and the allowlist rejects it.

This adds that prefix and changes nothing else. It is deliberately narrow.
`.fullsend/config.yaml` as a whole is still placed by hand, which is the same
reproducibility gap as G6, and owning the entire file is a larger change than
this one needs to be. Editing one list keeps the local substitution visible
rather than burying it in a file nobody can diff against upstream.
"""

from __future__ import annotations

import base64
import sys

import yaml

from emulator import ORG, REPO, api_request


CONFIG_PATH = ".fullsend/config.yaml"
# The prefix the patched CLI builds: <server>/<owner>/<repo>/raw/
LOCAL_PREFIX = "https://github.local/fullsend-ai/agents/"


def main() -> None:
    status, payload = api_request(
        "GET", f"/repos/{ORG}/{REPO}/contents/{CONFIG_PATH}"
    )
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(
            f"{ORG}/{REPO}:{CONFIG_PATH} not found (HTTP {status}). "
            "Install the per-repo scaffold first."
        )

    raw = base64.b64decode(payload["content"]).decode()
    config = yaml.safe_load(raw) or {}
    allowlist = list(config.get("allowed_remote_resources") or [])

    if any(entry.startswith(LOCAL_PREFIX) for entry in allowlist):
        print(f"allowlist already permits {LOCAL_PREFIX}")
        return

    allowlist.append(LOCAL_PREFIX)
    config["allowed_remote_resources"] = allowlist
    updated = yaml.safe_dump(config, sort_keys=False, default_flow_style=False)

    status, response = api_request(
        "PUT",
        f"/repos/{ORG}/{REPO}/contents/{CONFIG_PATH}",
        {
            "message": "Allow the local forge as a remote resource",
            "content": base64.b64encode(updated.encode()).decode(),
            "branch": "main",
            "sha": payload["sha"],
        },
    )
    if status not in (200, 201):
        raise RuntimeError(f"write {CONFIG_PATH} failed: HTTP {status}: {response}")
    print(f"added {LOCAL_PREFIX} to allowed_remote_resources")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        sys.exit(f"Allowlist seed failed: {exc}")
