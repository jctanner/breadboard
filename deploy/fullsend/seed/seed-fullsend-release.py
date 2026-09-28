#!/usr/bin/env python3
"""Publish a release of the Fullsend CLI on the emulator's upstream mirror.

Fullsend's install action (``.github/actions/install-fullsend-cli``) decides
how a job gets the CLI: a binary committed in the workspace, a release whose
tag points at the workflow's own commit, or a build from source. The release
is the common path on real GitHub and the only one that completes on this
stack: the dispatch chain's mirror carries no Go source, the runner has no
``make``, and its egress policy would refuse the module proxy anyway.

This seeds the release. It tags the mirror's head with a semver tag (the
action only matches ``vX.Y.Z``), creates the release there, and uploads the
CLI as ``fullsend_<version>_linux_amd64.tar.gz``, the asset name the action
derives from the runner's OS and architecture. The binary is the one
``deploy/scripts/05i-build-fullsend.sh`` compiled for the runner image, so
what a run downloads and what the image ships cannot drift apart.

Run it after ``seed-upstream-fullsend.py``, every time: a mirror commit moves
the head, and a release tag left on the old commit no longer matches
``job.workflow_sha``. A release that already sits at the head with the same
binary is left alone.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import ssl
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

from emulator import API_URL, TOKEN, api_request


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BINARY = ROOT / "deploy" / "fullsend" / "vendor" / "fullsend"
BINARY = Path(os.environ.get("FULLSEND_VENDOR_BINARY", "") or DEFAULT_BINARY)

UPSTREAM_ORG = "fullsend-ai"
UPSTREAM_REPO = "fullsend"
UPSTREAM_BRANCH = "main"
# The action matches ``^v[0-9]+\\.[0-9]+\\.[0-9]+$`` and takes the highest.
TAG = os.environ.get("FULLSEND_RELEASE_TAG", "v0.0.1")
VERSION = TAG.removeprefix("v")
ASSET_NAME = f"fullsend_{VERSION}_linux_amd64.tar.gz"
REPO_PATH = f"/repos/{UPSTREAM_ORG}/{UPSTREAM_REPO}"


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def tarball(path: Path) -> bytes:
    """``fullsend`` at the archive root, executable, as the release build ships it."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        info = archive.gettarinfo(str(path), arcname="fullsend")
        info.mode = 0o755
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        with path.open("rb") as handle:
            archive.addfile(info, handle)
    return buffer.getvalue()


def upload_asset(release_id: int, name: str, content: bytes) -> dict:
    request = urllib.request.Request(
        f"{API_URL}{REPO_PATH}/releases/{release_id}/assets?name={name}",
        data=content,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"token {TOKEN}",
            "Content-Type": "application/gzip",
            "User-Agent": "breadboard-fullsend-seed",
        },
        method="POST",
    )
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(request, context=context) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"asset upload failed: {exc.code} {exc.read().decode(errors='replace')}")


def head_sha() -> str:
    status, payload = api_request("GET", f"{REPO_PATH}/commits/{UPSTREAM_BRANCH}")
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(
            f"could not read {UPSTREAM_ORG}/{UPSTREAM_REPO}@{UPSTREAM_BRANCH}: {status} {payload}; "
            "run seed-upstream-fullsend.py first"
        )
    return payload["sha"]


def tag_sha() -> str | None:
    status, payload = api_request("GET", f"{REPO_PATH}/tags?per_page=100")
    if status != 200 or not isinstance(payload, list):
        return None
    for tag in payload:
        if tag.get("name") == TAG:
            return tag["commit"]["sha"]
    return None


def main() -> None:
    if not BINARY.is_file():
        raise RuntimeError(
            f"no Fullsend binary at {BINARY}. Run deploy/scripts/05i-build-fullsend.sh "
            "first, or point FULLSEND_VENDOR_BINARY at one."
        )
    binary_digest = digest(BINARY)
    marker = f"binary sha256: {binary_digest}"
    head = head_sha()

    status, existing = api_request("GET", f"{REPO_PATH}/releases/tags/{TAG}")
    if status == 200 and isinstance(existing, dict):
        asset_names = [asset.get("name") for asset in existing.get("assets") or []]
        if tag_sha() == head and marker in (existing.get("body") or "") and ASSET_NAME in asset_names:
            print(
                f"release {TAG} already current on {UPSTREAM_ORG}/{UPSTREAM_REPO} "
                f"(commit {head[:8]}, sha256 {binary_digest[:12]})"
            )
            return
        status, _ = api_request("DELETE", f"{REPO_PATH}/releases/{existing['id']}")
        if status != 204:
            raise RuntimeError(f"could not delete stale release {TAG}: {status}")
        print(f"removed stale release {TAG}")

    if tag_sha() is not None:
        # The tag, not only the release, has to sit at the head: the action
        # maps the workflow commit to a tag through the tags API.
        status, _ = api_request("DELETE", f"{REPO_PATH}/git/refs/tags/{TAG}")
        if status not in (204, 404):
            raise RuntimeError(f"could not move tag {TAG}: {status}")

    status, release = api_request(
        "POST",
        f"{REPO_PATH}/releases",
        {
            "tag_name": TAG,
            "target_commitish": head,
            "name": TAG,
            "body": (
                f"Fullsend CLI for the breadboard stack, built by "
                f"deploy/scripts/05i-build-fullsend.sh.\n\n{marker}\n"
            ),
        },
    )
    if status != 201 or not isinstance(release, dict):
        raise RuntimeError(f"could not create release {TAG}: {status} {release}")

    content = tarball(BINARY)
    asset = upload_asset(release["id"], ASSET_NAME, content)
    print(
        f"released {TAG} on {UPSTREAM_ORG}/{UPSTREAM_REPO} at {head[:8]} with "
        f"{ASSET_NAME} ({len(content) // (1024 * 1024)} MiB, asset {asset['id']}, "
        f"sha256 {binary_digest[:12]})"
    )


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        sys.exit(f"Fullsend release seed failed: {exc}")
