#!/usr/bin/env python3
"""Publish patched emulator branches of public repos to the GitHub emulator.

Reads "patched" from source-manifest.json, e.g.
  {"org": "fullsend-ai", "name": "strat-creator", "base": "pr-124",
   "branch": "cc75-emulator", "patches": "strat-creator"}
For each entry: check out refs/cc75/<base> from the mirror cache (filled by
mirror_github.py) in a temporary worktree, run patches/<patches>/NNNN-*.py on
it, commit once on top of the base (the base history is public and kept),
and push the result to the emulator as <branch>. Records the commits in
topology-manifest.json under "patched". Deterministic author and date.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
CACHE = Path(os.getenv("CC75_CACHE", Path.home() / ".cache" / "cc75" / "sources"))
ENV = dict(GIT_AUTHOR_NAME="cc75", GIT_AUTHOR_EMAIL="cc75@example.invalid", GIT_COMMITTER_NAME="cc75",
           GIT_COMMITTER_EMAIL="cc75@example.invalid", GIT_AUTHOR_DATE="2026-11-16T00:00:00Z",
           GIT_COMMITTER_DATE="2026-11-16T00:00:00Z", GIT_TERMINAL_PROMPT="0")


def git(*args, cwd=None, redact=""):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(ENV)
    r = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode:
        msg = (r.stderr or r.stdout).strip()
        raise SystemExit(f"git {args[0]}: {msg.replace(redact, '***') if redact else msg}")
    return r.stdout.strip()


def main() -> int:
    token = os.environ.get("GITHUB_API_TOKEN")
    if not token:
        raise SystemExit("GITHUB_API_TOKEN (GitHub emulator admin token) is required")
    ca = os.getenv("BREADBOARD_CA_FILE")
    tls = ["-c", f"http.sslCAInfo={ca}"] if ca else []
    base_url = os.getenv("GITHUB_URL", f"https://github.{DOMAIN}").rstrip("/")
    manifest = json.loads((ROOT / "source-manifest.json").read_text())
    topo_path = ROOT / "topology-manifest.json"
    topo = json.loads(topo_path.read_text())
    topo["patched"] = []
    for entry in manifest.get("patched", []):
        org, name = entry["org"], entry["name"]
        bare = CACHE / f"{org}__{name}.git"
        work = CACHE.parent / "work" / f"patched-{name}-{entry['branch']}"
        subprocess.run(["git", "-C", str(bare), "worktree", "remove", "--force", str(work)], capture_output=True)
        shutil.rmtree(work, ignore_errors=True)
        git("-C", str(bare), "worktree", "prune")
        git("-C", str(bare), "worktree", "add", "-q", "--detach", str(work), f"refs/cc75/{entry['base']}")
        base_commit = git("rev-parse", "HEAD", cwd=work)
        patches = sorted((ROOT / "patches" / entry["patches"]).glob("[0-9][0-9][0-9][0-9]-*.py"))
        for patch in patches:
            subprocess.run([sys.executable, "-I", str(patch), str(work)], check=True)
        git("add", "-A", cwd=work)
        git("commit", "-q", "-m", f"cc75: emulator patches on {entry['base']}\n\n"
            + "\n".join(f"- patches/{entry['patches']}/{p.name}" for p in patches), cwd=work)
        commit = git("rev-parse", "HEAD", cwd=work)
        remote = f"{base_url.replace('://', f'://admin:{quote(token, safe="")}@', 1)}/{org}/{name}.git"
        git(*tls, "push", "-q", "-f", remote, f"HEAD:refs/heads/{entry['branch']}", cwd=work,
            redact=quote(token, safe=""))
        git("-C", str(bare), "update-ref", f"refs/cc75/{entry['branch']}", commit)
        git("-C", str(bare), "worktree", "remove", "--force", str(work))
        topo["patched"].append({"path": f"{org}/{name}", "branch": entry["branch"], "base": entry["base"],
                                "base_commit": base_commit, "commit": commit,
                                "patches": [f"patches/{entry['patches']}/{p.name}" for p in patches]})
        print(f"{org}/{name}:{entry['branch']} = {entry['base']}@{base_commit[:8]} + {len(patches)} patch(es) -> {commit[:8]}")
    topo_path.write_text(json.dumps(topo, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
