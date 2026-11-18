#!/usr/bin/env python3
"""Mirror the public Initiative-flow repositories into the GitHub emulator.

Reads source-manifest.json. For each repository it maintains a bare cache
under ~/.cache/cc75/sources (outside the repo and /tmp), fetches the pinned
upstream refs anonymously, creates the emulator org and repository if missing,
pushes each ref to the named emulator branch, and verifies the advertised
commit. Re-running converges. TLS to the emulator is verified against
BREADBOARD_CA_FILE. The emulator admin token is read from GITHUB_API_TOKEN and
never written anywhere; topology-manifest.json records only paths and commits.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = os.getenv("BREADBOARD_DOMAIN", "local").strip(".") or "local"
CACHE = Path(os.getenv("CC75_CACHE", Path.home() / ".cache" / "cc75" / "sources"))


def git(*args: str, cwd: Path | None = None, env_extra: dict | None = None, redact: str = "") -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"}, **(env_extra or {}))
    r = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode:
        msg = (r.stderr or r.stdout).strip()
        raise SystemExit(f"git {args[0]} failed: {msg.replace(redact, '***') if redact else msg}")
    return r.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--github-url", default=os.getenv("GITHUB_URL", f"https://github.{DOMAIN}"))
    ap.add_argument("--manifest", default=ROOT / "source-manifest.json", type=Path)
    args = ap.parse_args()
    token = os.environ.get("GITHUB_API_TOKEN")
    if not token:
        raise SystemExit("GITHUB_API_TOKEN (GitHub emulator admin token) is required")
    ca = os.getenv("BREADBOARD_CA_FILE")
    base = args.github_url.rstrip("/")
    api = requests.Session()
    api.headers["Authorization"] = f"token {token}"
    api.verify = ca or True

    def get(path):
        r = api.get(f"{base}/api/v3/{path}", timeout=60)
        return None if r.status_code == 404 else (r.raise_for_status() or r.json())

    def post(path, body):
        # Bounded retry on the emulator's transient SQLite lock (503 sqlite_locked).
        # Replay-safe: callers check existence first, and a 422 "already exists"
        # after a retried create is accepted.
        for attempt in range(6):
            r = api.post(f"{base}/api/v3/{path}", json=body, timeout=60)
            if r.status_code == 503 and "sqlite_locked" in r.text:
                time.sleep(0.5 * 2 ** attempt)
                continue
            if r.status_code == 422 and attempt and "already" in r.text.lower():
                return {}
            if r.status_code >= 400:
                raise SystemExit(f"POST {path}: HTTP {r.status_code}: {r.text[:300]}")
            return r.json()
        raise SystemExit(f"POST {path}: emulator database stayed locked")

    manifest = json.loads(args.manifest.read_text())
    CACHE.mkdir(parents=True, exist_ok=True)
    tls = ["-c", f"http.sslCAInfo={ca}"] if ca else []
    results = []
    for src in manifest["github"]:
        org, name = src["org"], src["name"]
        bare = CACHE / f"{org}__{name}.git"
        if not bare.exists():
            git("init", "-q", "--bare", str(bare))
        refspecs = [f"+{upstream}:refs/cc75/{branch}" for branch, upstream in src["refs"].items()]
        git("fetch", "-q", "--no-tags", src["upstream"], *refspecs, cwd=bare)
        if get(f"orgs/{quote(org)}") is None:
            post("orgs", {"login": org})
        if get(f"repos/{quote(org)}/{quote(name)}") is None:
            post(f"orgs/{quote(org)}/repos", {"name": name, "private": False, "default_branch": "main"})
        remote = f"{base.replace('://', f'://admin:{quote(token, safe="")}@', 1)}/{org}/{name}.git"
        pushes = [f"+refs/cc75/{b}:refs/heads/{b}" for b in src["refs"]]
        git(*tls, "push", "-q", remote, *pushes, cwd=bare, redact=quote(token, safe=""))
        refs = {}
        advertised = dict(reversed(line.split("\t")) for line in
                          git(*tls, "ls-remote", remote, cwd=bare, redact=quote(token, safe="")).splitlines())
        for branch in src["refs"]:
            want = git("rev-parse", f"refs/cc75/{branch}", cwd=bare)
            got = advertised.get(f"refs/heads/{branch}")
            if got != want:
                raise SystemExit(f"{org}/{name}:{branch} mirror mismatch: {got} != {want}")
            refs[branch] = {"upstream_ref": src["refs"][branch], "commit": want}
        results.append({"path": f"{org}/{name}", "upstream": src["upstream"], "refs": refs})
        print(f"{org}/{name}: " + ", ".join(f"{b}@{r['commit'][:8]}" for b, r in refs.items()))

    out = {"version": 1, "github_url": base,
           "mirrored_at": datetime.now(timezone.utc).isoformat(), "github": results,
           "gitlab_private_pending": manifest.get("gitlab_private", []),
           "notes": ["No credentials are stored in this manifest."]}
    (ROOT / "topology-manifest.json").write_text(json.dumps(out, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
