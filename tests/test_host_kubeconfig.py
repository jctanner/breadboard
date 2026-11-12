"""User kubeconfig selection must work with the K3s kubectl default."""
import os
from pathlib import Path
import stat
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_install_and_bash_selection_preserves_explicit_context(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("installation is intentionally restricted to an operator user")
    user_dir = tmp_path / "user home"
    user_dir.mkdir()
    source = tmp_path / "server.yaml"
    source.write_text("apiVersion: v1\nkind: Config\n")
    source.chmod(0o640)
    config_dir = user_dir / ".kube"
    config_dir.mkdir()
    (config_dir / "config").write_text("previous operator contexts\n")
    (config_dir / "config").chmod(0o644)
    commands = tmp_path / "commands"
    commands.mkdir()
    sudo = commands / "sudo"
    sudo.write_text('#!/bin/sh\nexec "$@"\n')
    sudo.chmod(0o755)
    env = {**os.environ, "HOME": str(user_dir),
           "PATH": f"{commands}:{os.environ['PATH']}",
           "K3S_KUBECONFIG_SOURCE": str(source)}
    for _ in range(2):
        subprocess.run(["bash", str(ROOT / "deploy/scripts/host-kubeconfig.sh")],
                       env=env, check=True, capture_output=True)
    target = user_dir / ".kube/config"
    assert target.read_bytes() == source.read_bytes()
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert stat.S_IMODE(source.stat().st_mode) == 0o640
    assert stat.S_IMODE(config_dir.stat().st_mode) == 0o700
    backups = list(config_dir.glob("config.backup.*"))
    assert len(backups) == 1
    assert backups[0].read_text() == "previous operator contexts\n"
    assert stat.S_IMODE(backups[0].stat().st_mode) == 0o600
    assert (user_dir / ".bashrc").read_text().count("# Breadboard user kubeconfig") == 1
    command = '. "$HOME/.bashrc"; printf "%s" "$KUBECONFIG"'
    unset_env = dict(env)
    unset_env.pop("KUBECONFIG", None)
    result = subprocess.run(["bash", "--noprofile", "--norc", "-c", command],
                            env=unset_env, check=True, capture_output=True, text=True)
    assert result.stdout == str(target)
    result = subprocess.run(["bash", "--noprofile", "--norc", "-c", command],
                            env={**env, "KUBECONFIG": "/operator/other-context"},
                            check=True, capture_output=True, text=True)
    assert result.stdout == "/operator/other-context"


def test_refuse_root_before_changing_user_files(tmp_path):
    commands = tmp_path / "commands"
    commands.mkdir()
    fake_id = commands / "id"
    fake_id.write_text("#!/bin/sh\necho 0\n")
    fake_id.chmod(0o755)
    result = subprocess.run(["bash", str(ROOT / "deploy/scripts/host-kubeconfig.sh")],
                            env={**os.environ, "HOME": str(tmp_path),
                                 "PATH": f"{commands}:{os.environ['PATH']}"},
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert "operator user" in result.stderr
    assert not (tmp_path / ".kube").exists()
    assert not (tmp_path / ".bashrc").exists()


def test_compare_error_preserves_existing_config(tmp_path):
    if os.geteuid() == 0:
        pytest.skip("installation is intentionally restricted to an operator user")
    config_dir = tmp_path / ".kube"
    config_dir.mkdir()
    target = config_dir / "config"
    target.write_text("operator contexts\n")
    commands = tmp_path / "commands"
    commands.mkdir()
    sudo = commands / "sudo"
    sudo.write_text('#!/bin/sh\nexec "$@"\n')
    sudo.chmod(0o755)
    result = subprocess.run(["bash", str(ROOT / "deploy/scripts/host-kubeconfig.sh")],
                            env={**os.environ, "HOME": str(tmp_path),
                                 "PATH": f"{commands}:{os.environ['PATH']}",
                                 "K3S_KUBECONFIG_SOURCE": str(tmp_path / "absent")},
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert target.read_text() == "operator contexts\n"
    assert not list(config_dir.glob("config.backup.*"))
    assert not (tmp_path / ".bashrc").exists()
