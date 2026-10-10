import json

import pytest

from src.dashboard.job_scripts import (
    RUN_SCRIPT,
    normalize_script_spec,
    script_cmd_args,
    script_phase,
)

SHA = "0123456789abcdef0123456789abcdef01234567"


def test_image_script_under_benchmarks():
    spec = normalize_script_spec(
        {"path": "var/benchmarks/strat-workflow/scripts/selfcheck.sh", "args": ["--call-model"]}
    )
    assert spec == {
        "source": "image",
        "path": "var/benchmarks/strat-workflow/scripts/selfcheck.sh",
        "args": ["--call-model"],
    }


def test_repo_script_at_pinned_commit():
    spec = normalize_script_spec(
        {
            "repo": "https://github.com/jctanner/breadboard",
            "ref": SHA,
            "path": "var/benchmarks/strat-workflow/scripts/run-workflow.sh",
            "args": ["RHAIRFE-1"],
        }
    )
    assert spec["source"] == "repo"
    assert spec["ref"] == SHA


@pytest.mark.parametrize(
    "spec, message",
    [
        ({"path": "scripts/run_skill.sh"}, "under var/benchmarks/"),
        ({"path": "/etc/passwd"}, "relative"),
        ({"path": "var/benchmarks/../scripts/x.sh"}, "'..'"),
        ({"path": "var/benchmarks/x.sh", "args": "RHAIRFE-1"}, "list of strings"),
        ({"path": "x.sh", "repo": "https://github.com/a/b"}, "together"),
        ({"path": "x.sh", "repo": "http://github.com/a/b", "ref": SHA}, "https"),
        ({"path": "x.sh", "repo": "https://evil.example/a/b", "ref": SHA}, "host"),
        ({"path": "x.sh", "repo": "https://u:p@github.com/a/b", "ref": SHA}, "credentials"),
        ({"path": "x.sh", "repo": "https://github.com/a/b", "ref": "main"}, "40-character"),
        ({"path": "var/benchmarks/x.sh", "command": "rm -rf /"}, "unknown script fields"),
    ],
)
def test_rejected_specs(spec, message):
    with pytest.raises(ValueError, match=message):
        normalize_script_spec(spec)


def test_phase_and_command_for_repo_script():
    spec = normalize_script_spec(
        {
            "repo": "https://github.com/jctanner/breadboard",
            "ref": SHA,
            "path": "var/benchmarks/strat-workflow/scripts/run-workflow.sh",
            "args": ["RHAIRFE-1", "two words"],
        }
    )
    assert script_phase(spec) == "script-run-workflow"
    assert script_cmd_args(spec, "claude-haiku-5-5", "RHAIRFE-1") == [
        "/bin/bash", RUN_SCRIPT,
        "--path", "var/benchmarks/strat-workflow/scripts/run-workflow.sh",
        "--model", "claude-haiku-5-5",
        "--repo", "https://github.com/jctanner/breadboard", "--ref", SHA,
        "--issue", "RHAIRFE-1",
        "--", "RHAIRFE-1", "two words",
    ]


def test_orchestrator_builds_script_job_manifest():
    from src.dashboard.k8s_orchestrator import PipelineOrchestrator

    orch = object.__new__(PipelineOrchestrator)
    orch.namespace = "ai-pipeline"
    orch.model_relay_url = "http://model-relay.ai-pipeline.svc.cluster.local:8080/v1"
    orch.model_relay_project = "vertex-shim-local"
    orch.gcp_credentials_secret = "gcp-credentials-relay"

    spec = normalize_script_spec({"path": "var/benchmarks/strat-workflow/scripts/selfcheck.sh"})
    args = {"script": spec, "mlflow_experiment": "strat-workflow-eval/smoke/selfcheck", "strace": True}
    job = orch._create_job_manifest(script_phase(spec), "", "claude-haiku-5-5", "cli", args)

    container = job.spec.template.spec.containers[0]
    command = (container.command or []) + (container.args or [])
    assert RUN_SCRIPT in command
    assert "--skill" not in command and "--prompt" not in command
    assert job.metadata.labels["runner"] == "script"
    assert job.metadata.labels["phase"] == "script-selfcheck"
    assert json.loads(job.metadata.annotations["script"]) == spec

    env = {e.name: e.value for e in container.env}
    assert env["MLFLOW_EXPERIMENT_NAME"] == "strat-workflow-eval/smoke/selfcheck"
    assert env["ENABLE_STRACE"] == "1"
    assert env["ANTHROPIC_VERTEX_BASE_URL"] == orch.model_relay_url
    assert env["GOOGLE_CLOUD_PROJECT"] == "vertex-shim-local"
