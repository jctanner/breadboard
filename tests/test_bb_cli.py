"""Tests for scripts/bb CLI and breadboard-ops skill stub."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BB_BIN = PROJECT_ROOT / "scripts" / "bb"
SKILL_PATH = PROJECT_ROOT / ".claude" / "skills" / "breadboard-ops" / "SKILL.md"


def run_bb(args: list[str], env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    base_env = dict(os.environ)
    if env:
        base_env.update(env)
    return subprocess.run(
        [sys.executable, str(BB_BIN)] + args,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        env=base_env,
    )


class TestFastVersionPath:
    """Fast-path version tests (AXI 10)."""

    @pytest.mark.parametrize("flag", ["-v", "-V", "--version"])
    def test_version_flags(self, flag: str):
        t0 = time.perf_counter()
        proc = run_bb([flag])
        elapsed = time.perf_counter() - t0

        assert proc.returncode == 0
        assert proc.stdout.strip() == "bb 0.1.0"
        assert proc.stderr == ""
        # The fast path should execute in well under 250ms
        assert elapsed < 5.0  # tolerate loaded CI hosts; version must remain a fast path


class TestSkillFrontmatterAndGuide:
    """Skill and operational guide tests (Vega P5)."""

    def test_cli_skill_output(self):
        proc = run_bb(["--skill"])
        assert proc.returncode == 0
        out = proc.stdout

        # Frontmatter checks
        assert out.startswith("---\n")
        assert "name: breadboard-ops\n" in out
        assert "description:" in out

        # 4 Required Sections
        assert "## 1. CLI Subcommands (`scripts/bb`)" in out
        assert "## 2. The 3 Fullsend Patch Layers" in out
        assert "05i-build-fullsend.sh" in out
        assert "0016" in out
        assert "seed-upstream-fullsend.py" in out
        assert "seed-upstream-agents.py" in out

        assert "## 3. Physical Host `rhea` Hardware & Thermal Rules" in out
        assert "90°C" in out
        assert "CARGO_BUILD_JOBS=2" in out
        assert "PODMAN_SUDO=1" in out
        assert "SKIP_SANDBOX_DEV=1" in out

        assert "## 4. OpenShell 0.1.4 Architecture" in out
        assert "distroless" in out.lower() or "supervisor" in out.lower()
        assert "openshell-supervisor-local:k3s" in out
        assert "gcp-credentials" in out
        assert "placeholder" in out

    def test_skill_file_stub(self):
        assert SKILL_PATH.is_file(), f"Missing skill file at {SKILL_PATH}"
        content = SKILL_PATH.read_text(encoding="utf-8")

        assert content.startswith("---\n")
        assert "name: breadboard-ops" in content
        assert "description:" in content
        assert "./scripts/bb --skill" in content
        assert "./scripts/bb" in content


class TestFlagAndSubcommandValidation:
    """Strict validation and structured errors (AXI 6)."""

    def test_unknown_flag_on_subcommand(self):
        proc = run_bb(["runs", "--foo"])
        assert proc.returncode == 2
        assert proc.stderr == ""

        expected_header = "error{code,message,hint}:"
        assert expected_header in proc.stdout
        assert "usage,unknown flag --foo for `runs`,valid flags for `runs`: --repo, --limit, --domain (--help always allowed)" in proc.stdout

    def test_unknown_flag_on_root(self):
        proc = run_bb(["--foo"])
        assert proc.returncode == 2
        assert proc.stderr == ""

        assert "error{code,message,hint}:" in proc.stdout
        assert "usage,unknown flag --foo for `bb`,valid flags for `bb`: --skill, --domain (--help always allowed)" in proc.stdout

    def test_unknown_subcommand(self):
        proc = run_bb(["invalidsubcmd"])
        assert proc.returncode == 2
        assert proc.stderr == ""

        assert "error{code,message,hint}:" in proc.stdout
        assert "usage,unknown subcommand `invalidsubcmd`,valid subcommands: status, runs, logs, tickets, openshell, seed (--help always allowed)" in proc.stdout

    def test_missing_required_args(self):
        # logs requires <run_id>
        proc_logs = run_bb(["logs"])
        assert proc_logs.returncode == 2
        assert "error{code,message,hint}:" in proc_logs.stdout
        assert "missing required argument <run_id> for `logs`" in proc_logs.stdout

        # seed requires target
        proc_seed = run_bb(["seed"])
        assert proc_seed.returncode == 2
        assert "error{code,message,hint}:" in proc_seed.stdout
        assert "missing seed target for `seed`" in proc_seed.stdout

        # seed with invalid target
        proc_seed_bad = run_bb(["seed", "unknown_fixture"])
        assert proc_seed_bad.returncode == 2
        assert "error{code,message,hint}:" in proc_seed_bad.stdout
        assert "unknown seed target `unknown_fixture` for `seed`" in proc_seed_bad.stdout


class TestHelpSubcommands:
    """Concise subcommand help tests (AXI 10)."""

    @pytest.mark.parametrize(
        "subcmd",
        [[], ["status"], ["runs"], ["logs"], ["tickets"], ["openshell"], ["seed"]],
    )
    def test_help_flags(self, subcmd: list[str]):
        for flag in ["--help", "-h"]:
            proc = run_bb(subcmd + [flag])
            assert proc.returncode == 0
            assert "usage: bb" in proc.stdout
            assert proc.stderr == ""


@pytest.mark.skipif(os.getenv("BREADBOARD_LIVE_TESTS") != "1", reason="requires an explicitly selected live stack")
class TestLiveExecution:
    """Live execution checks against active cluster/emulators."""

    def test_home_view(self):
        proc = run_bb([])
        assert proc.returncode == 0
        out = proc.stdout

        assert "bin: " in out
        assert "description: Breadboard K3s cluster, emulator, and Fullsend operations CLI" in out
        assert "cluster{host,domain,max_temp_c,pods_running,pods_total}:" in out
        assert "tickets{total,github,gitlab,jira}:" in out
        assert "runners[" in out
        assert "recent_runs[" in out
        assert "help[4]:" in out

    def test_status_command(self):
        proc = run_bb(["status"])
        assert proc.returncode == 0
        out = proc.stdout

        assert "thermal{host,max_temp_c,status}:" in out
        assert "workloads[" in out
        assert "openshell_profiles[" in out
        assert "openshell_providers[" in out
        assert "openshell_sandboxes:" in out
        assert "sandboxes: 0 active sandboxes in openshell-system" in out
        assert "tickets{total,github,gitlab,jira}:" in out

    def test_runs_command(self):
        proc = run_bb(["runs", "--repo", "all", "--limit", "5"])
        assert proc.returncode == 0
        out = proc.stdout

        assert "count: " in out
        assert "runs[" in out
        assert "fullsend-dev/" in out

    def test_tickets_command(self):
        proc = run_bb(["tickets", "--limit", "10"])
        assert proc.returncode == 0
        out = proc.stdout

        assert "count: " in out
        assert "tickets[" in out

    def test_logs_command(self):
        proc = run_bb(["logs", "50"])
        assert proc.returncode == 0
        out = proc.stdout

        assert "jobs[" in out
        assert "Triage" in out
        assert "log{job,id}:" in out
        assert "Triage,443" in out
        assert "help[1]:" in out
