"""Sudo seeders can read operator-owned checkouts without global Git config."""
import importlib.util
import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_seed_git_trusts_only_requested_checkout(tmp_path, monkeypatch):
    env = {"PATH": os.environ["PATH"], "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], env=env, check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@localhost", "-c", "commit.gpgsign=false",
                    "commit", "--allow-empty", "-m", "fixture"],
                   env=env, check=True, capture_output=True)
    suspect_env = {**env, "GIT_TEST_ASSUME_DIFFERENT_OWNER": "1"}
    plain = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                           env=suspect_env, capture_output=True, text=True)
    if plain.returncode == 0:
        pytest.skip("Git does not expose the ownership test hook")
    assert "dubious ownership" in plain.stderr
    for key, value in suspect_env.items():
        monkeypatch.setenv(key, value)
    spec = importlib.util.spec_from_file_location("ownership_seed", ROOT / "deploy/fullsend/seed/emulator.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    head = helper.run_git(repo, "rev-parse", "HEAD").stdout.strip()
    assert len(head) == 40
    hook = repo / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\nexit 7\n")
    hook.chmod(0o755)
    helper.run_git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@localhost",
                   "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", "no hooks")
    assert helper.git_env()["GIT_CONFIG_GLOBAL"] == os.devnull
    assert helper.run_git(repo, "config", "--get", "http.sslVerify").stdout.strip() == "true"
    after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                           env=suspect_env, capture_output=True, text=True)
    assert after.returncode != 0  # No persistent or wildcard trust was installed.


def test_git_environment_drops_redirection_and_config_injection(monkeypatch):
    spec = importlib.util.spec_from_file_location("isolated_seed", ROOT / "deploy/fullsend/seed/emulator.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    bad = {"GIT_DIR": "/other/repo", "GIT_WORK_TREE": "/other/tree",
           "GIT_CONFIG_PARAMETERS": "'safe.directory=*'", "GIT_CONFIG_COUNT": "1",
           "GIT_CONFIG_KEY_0": "http.sslVerify", "GIT_CONFIG_VALUE_0": "false",
           "GIT_SSH_COMMAND": "unwanted", "GIT_ASKPASS": "unwanted",
           "GIT_EXEC_PATH": "/other/bin", "GIT_SSL_NO_VERIFY": "1"}
    for key, value in bad.items():
        monkeypatch.setenv(key, value)
    env = helper.git_env()
    assert not set(bad).intersection(env)
    assert env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
