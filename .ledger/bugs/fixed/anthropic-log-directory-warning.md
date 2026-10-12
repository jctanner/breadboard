# ANTHROPIC_LOG is assigned a directory instead of a log level

## Status

Fixed and deployed on 2026-10-12 after the user requested the cleanup.
The original 2026-10-11 deferral preserved the active S2 benchmark; this fix
applies to newly submitted jobs.

## Summary and cause

Job orchestrators set `ANTHROPIC_LOG` to
`/app/artifacts/apibodies/<job-name>` when API dumping is enabled.
The Anthropic client expects a log level: `off`, `error`, `warn`, `info`
or `debug`. Claude stderr repeatedly warns that the directory is invalid.

Original affected assignments:

- `src/dashboard/k8s_orchestrator.py`, `_build_env_vars`, around line 579.
- `src/dashboard/openshell_orchestrator.py`, around line 182.

## Reproduction and evidence

Submit a Claude script job with default API dumping enabled. Observed in
S2 Opus batch `markov-run-6bcb3c32`, job
`script-strategy-entrypoint-all-claude-opus-4-1011-181949-e387e8`.
Its stderr reports `process.env['ANTHROPIC_LOG']` was set to the API dump
directory, followed by `expected one of ["off","error","warn","info","debug"]`.

At approximately 18:45 UTC, 168 files existed in its API dump directory
and 1177 in its strace directory. The runner continued into review with
no restart. Relay inspection during this checkpoint showed 104 complete
requests, one in progress, and no errors. This warning is not evidence of
an inference failure or missing API capture in this run.

## Expected behavior and proposed fix

Leave `ANTHROPIC_LOG` unset unless selecting a supported log level. Remove
the directory-valued assignment from both orchestrators. Preserve API
capture through `OTEL_LOG_RAW_API_BODIES=file:<directory>`, configured by
`scripts/lib/job_setup.sh` and other runner wrappers.

Verify generated job environments for both execution paths and run a
small capture-enabled check: no invalid-log-level warning, request and
response dumps still written. Do not launch another paid benchmark solely
to validate this cleanup.

## Impact

Low: repeated stderr noise obscures useful diagnostics. API capture was
verified working on the active Kubernetes runner; the OpenShell path has
the same source assignment but was not exercised in this investigation.

## Fix and verification, 2026-10-12

Removed the directory-valued ANTHROPIC_LOG default from both dashboard
orchestrators. Runner wrappers still configure raw captures through
OTEL_LOG_RAW_API_BODIES; intentional extra_env log levels remain supported.

Eighteen existing focused tests pass (scripts/test_job_scripts.py and
tests/test_openshell_orchestrator.py). Direct environment checks cover default,
api_dump=true/false and an explicit debug override for both launchers.

Pinned native Claude2.1.296 against a loopback mock confirms the old directory
setting emits the warning and the corrected unset environment does not.
Both calls exit0 and produce one request body, one response body and index.jsonl.
Private fixture evidence: /tmp/anthropic-log-capture-twmgww1j/.
No paid inference, Jira reset or additional benchmark run.

Deployed using make host-rebuild-dashboard. New ready pod:
pipeline-dashboard-59dd85ccf8-szgxd; image
sha256:575e4b1c7e38cfc19d2fa24333f52bd98c385b72f96a4e4d5f650795a6de9be5.
Rollout succeeds, jobs API healthy and no active jobs. Deployed source hashes
match the local files and all environment checks pass inside the new pod.
No pipeline-agent or Model Relay rebuild required. The live OpenShell sandbox
path was not launched; its deployed environment builder and existing tests pass.
