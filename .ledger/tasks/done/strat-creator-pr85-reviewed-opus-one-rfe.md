# PR 85: one-ticket Opus integration test after review fixes

Authorized 2026-10-16: one real S1 batch with one RFE and
`claude-opus-4-6`, one iteration. No automatic paid retry.

Candidate: `jctanner-fullsend-ai/strat-creator`, branch
`feat/s1-workflow-hardening`, commit
`18cdf46716a291439e766d9341eb8e0a03702d52` (PR 85).
Benchmark source: Breadboard `440d864797c4dd7e6e31ec639acb751c6ed2308b`,
including the repaired independent report checker. Historical tier pins stay
unchanged; a run-only tier selects `smoke-one-rfe`, batch mode, concurrency 10,
native capture, and stop-on-workflow-failure.

The deployed pipeline image reports Claude Code 2.1.296 without inference;
image digest: `sha256:2a7c01426967e6a7e1566525057a81b0060026969cb6f2f8430a7e1abfd6115e`.
An offline execution of the exact request passes: one S1 job, one discovered
RFE, Opus, correct source/fork, concurrency and failure-monitor settings.
No provider calls were made by those checks.

Before the Jira fixture reset, verify prior final archive receipts and idle
services. Preserve existing telemetry. Verify actual job source/model/provider
after launch. A detached observer collects terminal evidence, including API
dumps, strace, native state, logs, Jira, MLflow and service snapshots, and
independently verifies the final archive and published receipts.

Archive campaign:
`var/run-data/strat-workflow-hardening/pr85-reviewed-vertex-opus-one-rfe-20261016/`.

This tests the Kubernetes/Markov/Breadboard integration; it does not validate
Fullsend's runner or OpenShell deployment. Completion and content quality are
separate claims. The existing mechanical checks do not replace content judging.

- [x] Pin the repaired candidate and benchmark source.
- [x] Verify exact request offline and deployed Claude version without inference.
- [x] Verify prior archives, sync/import and provider readiness.
- [x] Launch exactly one batch and verify the real job configuration.
- [x] Collect and verify terminal evidence; record the independent verdict.

## Launch

Submitted once at 2026-10-16 22:54 UTC (18:54 America/New_York):
[markov-run-64a6b4f4](https://markovd.local/runs/markov-run-64a6b4f4).
The separate archive observer is PID 1752357; its controller, request,
preflight, imported source, checks and status live in the campaign's
`launch-context/`. It never launches replacement model work.

Both previous model-job archives independently passed checksums before this
run's Jira reset. All 69 imported benchmark files match the pushed source.
Relay readiness confirms `vertex-shim-local` routes through
`vertex-strat-evals` using its configured Google service account.

Model job: `script-run-workflow-all-claude-opus-4-6-1016-225441-c61df7`.
Its actual primary process has the expected source commit and fork, batch mode,
one acquired RFE (`RHAIRFE-1`), concurrency 10 and stop-on-failure enabled.
The primary model, subagent model and default Haiku/Sonnet/Opus aliases all
resolve to `claude-opus-4-6`. The running pod has the same image digest as the
Claude version probe; the initial source diff is empty. Initial relay telemetry
shows completed HTTP 200 Opus requests through `vertex-strat-evals` with Google
service-account authentication. These were startup checks; the terminal result
is recorded below.

The seed job's Haiku name is non-inference metadata: fixture setup does not call
a model. The one inference job is the Opus job above.

## Result: failed smoke, complete evidence

Model job: 18:54:41–19:10:27 America/New_York, 15m46s. Native Workflow:
14m59s, failed. Markov finishes recording the evaluation as `completed`; its
underlying model job failed and the independent evaluation has `pass: false`.

Creation (about 2m01s) and refinement (7m43s) succeeded. The fourth step,
`verify refinement progress`, spent 4m55s attempting to return its valid helper
JSON. The StructuredOutput PreToolUse hook `refine_checkpoint_guard.py`
timed out at ten seconds on each of five attempts. Claude's structured-output
retry cap failed the Workflow before push, scoring or any reviewer launch.
This exposes a real guard runtime defect, rather than a report-format failure.
[Bug and evidence](../../bugs/fixed/strat-refine-checkpoint-hook-timeout.md).

Pre-script and release exit 0; Claude and host validation exit 1. The post-script
was not run. One linked strategy exists and has recorded refinement, but there
is no final review, numeric verdict or business completion receipt. All Jira
claims were released. All observed inference was Opus: 81 captured requests,
2,678,455 accounted tokens including cache reads/writes and output, with no
recorded API errors or rate limits. This is execution evidence, not content
quality judging.

Archive final/complete, no source errors, 1,228 manifest files. Independent
verification succeeded and final receipts were published at 23:23 UTC.
It includes API captures, syscall traces, native Workflow state/transcripts,
job logs/artifacts, Jira exports and service/telemetry snapshots. Final capture:
`markov-run-64a6b4f4/20261016T231100432769Z/` within the campaign root.
No retry, resume, Jira reset or additional model run was launched.
