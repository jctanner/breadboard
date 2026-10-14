# Task: pi provider workflow-engine POC — Phase 2 fullsend integration

## Goal

Run the workflow-engine plugin through `fullsend run --runtime pi` in a real
OpenShell sandbox and verify R1–R6 per
[pi-provider-workflow-engine-poc](../../plans/pi-provider-workflow-engine-poc.md).

## Acceptance criteria

- [x] Local OpenShell gateway running with the podman driver; fullsend CLI
      built from the checkout; sandbox image built with PI_VERSION=1.1.0.
- [x] POC harness (config.yaml, harness/poc.yaml, agents/poc.md, plugin
      tree, policy) under var/demos/workflow-engine-poc/phase2.
- [x] R1 model pass-through: `workflow-engine/v1` reaches pi untouched.
- [x] R2 plugin path: tree uploaded, format detected, hash preflight and
      guards pass, extension loads in-sandbox.
- [x] R3 (observed scope): renderer progress and TOKENS events live; no
      stall in a 2.6 s run. Watchdog (>10 m slow phase) not exercised —
      see the Phase 0 caveat (FULLSEND_STALL_TIMEOUT not in any tree).
- [x] R4 metrics: parent usage 0; children folded into per_model_usage
      (test-child/echo 3 requests + workflow-engine/v1 1 request; sums to
      totals).
- [x] R5 completion: exit 0, result stop, transcripts/metrics extracted.
- [x] R6 hooks: PreToolUse allowlist hook blocks the code-issued workflow
      call; finding recorded in security/findings.jsonl.
- [x] Phase 1 check re-validated on the updated extension (3/3 PASS).
- [ ] R7 (stretch): retry/validation-loop re-entry — not attempted.

## Status

Done (R1–R6; R7 not attempted). Run logs: /tmp/fullsend-run{6,7,8,9}.log;
run artifacts under /tmp/fullsend/fs-poc-*. Key findings recorded in the
plan and the POC README.
