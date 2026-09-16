from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import m11_seed  # noqa: E402
import onboard_repo  # noqa: E402


def test_dispatch_uses_the_minimal_site_wide_router_runner():
    assert "runs-on: [self-hosted, linux, fullsend-router]" in m11_seed.DISPATCH_WORKFLOW
    assert "runs-on: [self-hosted, linux, fullsend]" in m11_seed.TRIAGE_AGENT_WORKFLOW


def test_fix_stage_is_routed_for_requested_changes_and_manual_commands():
    assert "review.state == 'CHANGES_REQUESTED'" in m11_seed.SHIM_WORKFLOW
    assert "if [[ \"${review_state}\" == \"CHANGES_REQUESTED\" ]]" in m11_seed.DISPATCH_WORKFLOW
    assert "/fs-fix*) stage=fix" in m11_seed.DISPATCH_WORKFLOW


def test_human_comments_retriage_needs_info_issues():
    assert "github.event.comment.user.type != 'Bot'" in m11_seed.SHIM_WORKFLOW
    assert 'index("needs-info") != null' in m11_seed.DISPATCH_WORKFLOW
    assert '[[ -z "${stage}" && "${needs_info}" == "true" ]]' in m11_seed.DISPATCH_WORKFLOW


def test_fix_workflow_materializes_pinned_sonnet_agent_assets():
    files = m11_seed._config_files()

    assert m11_seed.CONFIG_FIX in files
    assert m11_seed.CONFIG_FIX_AGENT in files
    assert "agents/fix.yaml" in files[".fullsend/config.yaml"]
    assert "fullsend run fix" in files[m11_seed.CONFIG_FIX_AGENT]
    assert "REVIEW_BODY_FILE" in files[m11_seed.CONFIG_FIX_AGENT]
    assert "PRE_AGENT_HEAD" in files[m11_seed.CONFIG_FIX_AGENT]
    assert "model: claude-sonnet-5" in files[".fullsend/agents/fix.yaml"]
    assert "model: opus" not in files[".fullsend/agents/fix.yaml"]
    fix_harness = files[".fullsend/agents/fix.yaml"]
    assert fix_harness.count('GH_HOST: "${GH_HOST}"') == 1
    assert fix_harness.count('GITHUB_API_URL: "${GITHUB_API_URL}"') == 1


def test_fix_agent_checks_out_the_pr_head_before_running():
    workflow = m11_seed.FIX_AGENT_WORKFLOW

    assert 'git -C target-repo fetch origin "pull/${pr_number}/head:${head_ref}"' in workflow
    assert 'git -C target-repo fetch origin "${head_ref}:${head_ref}"' in workflow
    assert 'git -C target-repo checkout "${head_ref}"' in workflow
    assert 'printf \'%s\\n\' "${review_body}" > "${review_body_file}"' in workflow
    assert 'echo "HUMAN_INSTRUCTION=" >> "${GITHUB_ENV}"' in workflow
    assert 'role: fix' in workflow


def test_code_agent_opts_into_local_auto_merge_queue():
    workflow = m11_seed._config_files()[m11_seed.CONFIG_CODE_AGENT]

    assert 'CODE_AUTO_MERGE: "true"' in workflow
    assert "CODE_AUTO_MERGE_METHOD: squash" in workflow


def test_repository_onboarding_requires_review_and_all_delivery_roles():
    protection = onboard_repo.protection_body()

    assert protection["required_status_checks"] is None
    assert protection["required_pull_request_reviews"][
        "required_approving_review_count"
    ] == 1
    assert set(onboard_repo.ROLE_APPS) == {"triage", "code", "review", "fix"}
    assert set(onboard_repo.DEVELOPMENT_ROLE_BOTS) == {
        "fullsend-code[bot]",
        "fullsend-review[bot]",
        "fullsend-fix[bot]",
    }
