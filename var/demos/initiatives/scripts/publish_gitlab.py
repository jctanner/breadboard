#!/usr/bin/env python3
"""Publish the private agentic-ci sources into the GitLab emulator (CC-75).

Source commits come from bare caches under ~/.cache/cc75/sources/gitlab__<name>.git
(ref refs/cc75/main), filled with glab-authenticated fetches on the operator's
machine. For each code repository this script:
  1. exports the source tree (git archive) without paths listed in EXCLUDE
     (run history is not mirrored);
  2. runs the transformations $CC75_PRIVATE_PATCHES/<name>/NNNN-*.py on that tree
     (default ~/.cache/cc75/private-patches; they quote private source, so they
     are kept outside this public repository);
  3. commits a single snapshot (no upstream history) whose message records the
     source commit and the patches applied, and force-pushes it to the emulator
     project's main branch.
The mirror shows production's eventual state on main only: a repository with an
open upstream MR that main is expected to gain is built from that MR's head
(SOURCE_REF; refs/cc75/mr-<iid> in the cache, fetched read-only with glab).
Each patch declares its kind in a "Kind:" line (pending-mr, upstream-proposal,
emulator-gap, environment, model-relay); the manifest records it, so the
differences from upstream double as a list of proposals.
Data repositories are created empty (with one README commit) so no real
pipeline output enters the demo. Groups/projects are created if missing.
Writes pipeline-manifest.json (source/adapted commits; no credentials).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
CACHE = Path(os.getenv("CC75_CACHE", Path.home() / ".cache" / "cc75" / "sources"))
PRIVATE_PATCHES = Path(os.getenv("CC75_PRIVATE_PATCHES", "~/.cache/cc75/private-patches")).expanduser()
GROUP = "redhat/rhel-ai/agentic-ci"
CODE = ["strat-pipeline", "strat-dashboard", "rfe-autofixer", "epic-decomposer"]
DATA = ["strat-pipeline-data", "rfe-autofixer-results", "epic-decomposer-results", "epic-decomposer-dashboard"]
# Empty repositories that are not results: only their existence matters.
PLACEHOLDER = {"epic-decomposer-dashboard": "the trigger target of epic-decomposer's build-dashboard job, "
                                            "which the emulator checks when it creates a pipeline; not mirrored"}
EXCLUDE = {"strat-pipeline": ["execution-logs"]}
# Open upstream MRs main is expected to gain (2026-11-16).
SOURCE_REF = {"strat-pipeline": "mr-27", "rfe-autofixer": "mr-43"}
KINDS = ("pending-mr", "upstream-proposal", "emulator-gap", "environment", "model-relay")


def patch_kind(path: Path) -> str:
    for line in path.read_text().splitlines()[:40]:
        if line.startswith("Kind:"):
            kind = line.split(":", 1)[1].strip().split()[0]
            if kind not in KINDS:
                raise SystemExit(f"{path}: unknown Kind {kind!r}")
            return kind
    raise SystemExit(f"{path}: no 'Kind:' line in the docstring")
GIT_ENV = dict(GIT_AUTHOR_NAME="cc75", GIT_AUTHOR_EMAIL="cc75@example.invalid",
               GIT_COMMITTER_NAME="cc75", GIT_COMMITTER_EMAIL="cc75@example.invalid",
               GIT_AUTHOR_DATE="2026-11-16T00:00:00Z", GIT_COMMITTER_DATE="2026-11-16T00:00:00Z",
               GIT_TERMINAL_PROMPT="0")


def run(cmd, cwd=None, redact=""):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_ENV)
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode:
        msg = (r.stderr or r.stdout).strip()
        raise SystemExit(f"{cmd[0]} {cmd[1] if len(cmd) > 1 else ''} failed: "
                         f"{msg.replace(redact, '***') if redact else msg}")
    return r.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gitlab-url", default=os.getenv("GITLAB_URL", f"https://gitlab.{DOMAIN}"))
    ap.add_argument("--only", nargs="*", help="limit to these repositories")
    args = ap.parse_args()
    user, password = os.getenv("GITLAB_USER", "admin"), os.getenv("GITLAB_ADMIN_PASSWORD", "admin")
    ca = os.getenv("BREADBOARD_CA_FILE")
    base = args.gitlab_url.rstrip("/")
    api = requests.Session()
    api.auth = (user, password)
    api.verify = ca or True

    def call(method, path, **kw):
        for attempt in range(6):
            r = api.request(method, f"{base}/api/v4/{path}", timeout=60, **kw)
            if r.status_code == 503 and "lock" in r.text.lower():
                time.sleep(0.5 * 2 ** attempt)
                continue
            return r
        return r

    parent = None
    for part in GROUP.split("/"):
        full = f"{parent['full_path']}/{part}" if parent else part
        r = call("GET", f"groups/{quote(full, safe='')}")
        if r.status_code == 404:
            body = {"name": part, "path": part, "visibility": "private"}
            if parent:
                body["parent_id"] = parent["id"]
            r = call("POST", "groups", json=body)
        r.raise_for_status()
        parent = r.json()

    def ensure_project(name):
        r = call("GET", f"projects/{quote(f'{GROUP}/{name}', safe='')}")
        if r.status_code == 404:
            r = call("POST", "projects", json={"name": name, "path": name, "namespace_id": parent["id"],
                                                "visibility": "private", "default_branch": "main"})
        r.raise_for_status()
        return r.json()

    tls = ["-c", f"http.sslCAInfo={ca}"] if ca else []
    remote_base = base.replace("://", f"://{quote(user)}:{quote(password)}@", 1)
    manifest_path = ROOT / "pipeline-manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"version": 1, "projects": {}}
    selected = set(args.only or CODE + DATA)

    for name in CODE + DATA:
        if name not in selected:
            continue
        project = ensure_project(name)
        work = CACHE.parent / "work" / f"publish-{name}"
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        entry = {"project": f"{GROUP}/{name}", "project_id": project["id"]}
        if name in CODE:
            bare = CACHE / f"gitlab__{name}.git"
            ref = f"refs/cc75/{SOURCE_REF.get(name, 'main')}"
            source = run(["git", "-C", str(bare), "rev-parse", ref])
            data = subprocess.run(["git", "-C", str(bare), "archive", ref],
                                  check=True, capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(data)) as tar:
                tar.extractall(work, filter="data")
            for path in EXCLUDE.get(name, []):
                shutil.rmtree(work / path, ignore_errors=True)
            patches = sorted((PRIVATE_PATCHES / name).glob("[0-9][0-9][0-9][0-9]-*.py"))
            for patch in patches:
                subprocess.run([sys.executable, "-I", str(patch), str(work)], check=True)
            message = (f"cc75 snapshot of {GROUP}/{name}@{source} ({ref.rsplit('/', 1)[-1]})\n\n"
                       f"Excluded: {', '.join(EXCLUDE.get(name, [])) or 'none'}\n"
                       f"Patches: {', '.join(p.name for p in patches) or 'none'}\n")
            entry.update(source_commit=source, source_ref=ref.rsplit("/", 1)[-1], excluded=EXCLUDE.get(name, []),
                         patches=[{"path": f"private-patches/{name}/{p.name}", "kind": patch_kind(p)} for p in patches])
        else:
            purpose = PLACEHOLDER.get(name)
            if purpose:
                # A downstream pipeline needs a CI file; one no-op job keeps the trigger green.
                (work / ".gitlab-ci.yml").write_text(
                    "# CC-75 placeholder: trigger target only.\nplaceholder:\n  tags: [aipcc-small-x86_64]\n"
                    "  image: registry.access.redhat.com/ubi9/ubi-minimal:latest\n"
                    "  script:\n    - echo \"CC-75 placeholder: nothing to build\"\n")
            (work / "README.md").write_text(
                f"# {name}\n\nEmpty CC-75 emulator placeholder: {purpose}.\n" if purpose
                else f"# {name}\n\nEmpty CC-75 emulator results repository.\n")
            message = f"cc75: empty {name}\n"
        run(["git", "init", "-q", "-b", "main"], cwd=work)
        run(["git", "add", "-A"], cwd=work)
        run(["git", "commit", "-q", "-m", message], cwd=work)
        adapted = run(["git", "rev-parse", "HEAD"], cwd=work)
        if name in DATA and name not in PLACEHOLDER and project.get("default_branch") and not project.get("empty_repo", True):
            # Never overwrite results a scenario already pushed; data repos are created once.
            entry["adapted_commit"] = "existing (left unchanged)"
        else:
            run(["git", *tls, "push", "-q", "-f", f"{remote_base}/{GROUP}/{name}.git", "main:main"],
                cwd=work, redact=quote(password))
            entry["adapted_commit"] = adapted
        manifest["projects"][name] = entry
        print(f"{GROUP}/{name} (id {project['id']}): {entry.get('source_commit', 'empty')[:8]} -> "
              f"{str(entry['adapted_commit'])[:8]} patches={len(entry.get('patches', []))}")

    manifest["published_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
