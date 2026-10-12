# Task: Fix invalid ANTHROPIC_LOG in pipeline jobs

## Goal

Remove the repeated invalid-log-level warning from newly launched jobs while
preserving raw API captures and intentional SDK log-level overrides.

## Authorization

2026-10-12: user requests fixing the warning now, superseding its earlier
deferral. Update the Kubernetes and OpenShell launchers, verify locally without
paid inference, and deploy the dashboard through its host rebuild target.

## Acceptance criteria

- [x] Remove directory-valued ANTHROPIC_LOG defaults from both launchers.
- [x] Verify both generated environments and explicit valid level overrides.
- [x] Verify native Claude warning removal and API dumps with a local mock.
- [x] Run focused existing checks and deploy/verify the updated dashboard.
- [x] Move the bug to fixed and record the evidence.

## Status

Done. API dumping remains configured by OTEL_LOG_RAW_API_BODIES in the runner
wrappers. Both orchestrators stop assigning a directory to ANTHROPIC_LOG.

## Evidence

18 tests pass via uv run --no-sync --with pytest python -m pytest -q
scripts/test_job_scripts.py tests/test_openshell_orchestrator.py.
Host and deployed builder checks pass for default/API-dump-on/API-dump-off
environments and explicit ANTHROPIC_LOG=debug.

Native2.1.296 loopback mock: the invalid directory control warns, corrected
unset control does not; both exit0 with request/response dumps and an API index.
Fixture root /tmp/anthropic-log-capture-twmgww1j/; no paid inference.

make host-rebuild-dashboard completed; rollout ready. New pod
pipeline-dashboard-59dd85ccf8-szgxd uses image
sha256:575e4b1c7e38cfc19d2fa24333f52bd98c385b72f96a4e4d5f650795a6de9be5.
Deployed k8s_orchestrator.py SHA256:
511e9077b07469c70a2725dd75f37bfa31e1b3454d609248c3d428428fe154d5.
Deployed openshell_orchestrator.py SHA256:
bb96d863ebe8f0f6751b79b57123be62f4437cd7da0ca5076a2bd3fcea01b64f.
Both match local source; jobs API healthy, active_jobs=0.
No agent/relay rebuild, S1/S2 source edit or benchmark run.
[Fixed bug](../../bugs/fixed/anthropic-log-directory-warning.md).
