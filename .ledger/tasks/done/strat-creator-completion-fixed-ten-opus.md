# Ten-ticket Opus retest after final completion-hook optimization

User authorization, 2026-10-17: rerun the ten-ticket batch. One S1 iteration
with Opus 4.6, high effort and concurrency ten. No automatic paid retry/resume.

Use published PR 85 head `6ed858b2294a29457153a90f187a801022c21e8b`, fork
`jctanner-fullsend-ai/strat-creator`, branch `feat/s1-workflow-hardening`.
The new tier `s1-pr85-completion-fixed-opus` recreates the same ten distinct
RFEs from `batch-ten-distinct-v2`. Jira is reset after archive checks, so old
RFEs/strategies cannot mix with the new fixture. Reuse across these comparison
runs is deliberate; each batch itself contains ten independent requests.
Preserve previous tier pins, verdicts and archives.

- [x] Confirm repaired source is published and prior terminal archive is verified.
- [x] Confirm no active jobs or conflicting schedules.
- [x] Validate/publish the source pin and verify Markovd import.
- [x] Independently verify prior archives and read-only fixture/provider checks.
- [x] Submit once through markovd-cli; verify actual acquired RFEs, source,
      Opus primary/helpers, cap ten and provider requests.
- [x] Archive terminal evidence, verify checksums and record actual outcome.

[Model-free repair evidence](../done/strat-completion-hook-performance.md).
This is Kubernetes/Markov/Breadboard integration, not a Fullsend/OpenShell
deployment or independent judging of strategy content.

## Preparation

Benchmark source `f9802385f3d2d3d9f044cc6f9b03257af6c09bf2` is published;
all 80 imported Markovd files match. Only four benchmark files were committed;
unrelated pending ledger/CLI work remains outside that commit. The staged
allowlist, redacted credential scan, directory validation and 99 offline tests
(one optional skip) pass. Exact-payload rendering confirms ten expected keys,
Opus, source 6ed858b, cap ten, native capture and stop-on-failure.

Submission did not occur before the earlier preparation was interrupted:
neither a launch intent nor launch response existed, and Markovd's latest run
remained markov-run-0e40b64c. On the user's status check, temporary launch files
were absent. The controller was reconstructed from the saved prior campaign,
with the new source/tier and direct `checkouts/markovd/bin/markovd-cli` path.
Offline checks were repeated with `checkouts/markovd/bin/markov` and pass.
No replacement model run was submitted during this reconciliation.

Campaign root:
`var/run-data/strat-workflow-hardening/pr85-completion-fixed-vertex-opus-ten-rfe-20261017/`.
Restored controller, exact request, offline proof, imported source, fixture
checks and archive receipts are persisted under `launch-context/` before
submission. Preflight passes: retained prior model-job archives and all 10,093
completion-fix evidence entries verify, ten eligible distinct requests are
planned, and the intended Vertex service-account profile is ready.

## Submitted

One run submitted through `checkouts/markovd/bin/markovd-cli`:
[markov-run-0b098f6e](https://markovd.local/runs/markov-run-0b098f6e).
Detached archive observer PID 291155 is attached. Exact request, intent,
CLI invocation and response are persisted; do not resubmit this campaign.
Run started 2026-10-18 01:56:31 UTC (2026-10-17 21:56:31 America/New_York).
Model job: `script-run-workflow-all-claude-opus-4-6-1018-015649-777f2f`.

Direct process inspection confirms clean 6ed858b source, batch mode, batch size
and cap ten, stop-on-native-failure, and exactly RHAIRFE-1 through RHAIRFE-10
acquired. Primary, subagent and Haiku/Sonnet/Opus aliases all use Opus 4.6.
The pipeline image digest matches the prior qualified 2.1.296 smoke. Completed
HTTP 200 calls use `vertex-strat-evals` and Google service-account auth.

Seed metadata and live Jira readback confirm ten distinct full descriptions
matching the published fixtures exactly, with no old tickets mixed in. The
launch context retains seed/source/process/image/telemetry evidence and the
startup verification summary. No other model run, retry or resume was submitted.

## Result and verification

Native Workflow and model job completed, CLI/validation/post/release each exit 0.
All ten distinct RFEs completed, with ten published reviews and all forty role
reports delivered and preserved. All 36 Workflow agents completed on their first
attempt. Final completion guard passes first try: 2.525709 seconds traced, exit 0,
under the unchanged ten-second cutoff. Workflow 36m41s; model job 38m26s;
Markov orchestration 39m01s.

The historical benchmark remains FAIL only for `reviewer_outputs_returned`:
38 accepted, two complete assessments rejected for the already tracked numbered-
findings and qualified-architecture wording defects. Independent read-only API/
native/provenance/final-review joins establish all forty complete handoffs.
In-memory formatting-only probes make both rejected reports pass; originals,
source pins and historical verdicts remain unchanged. No cross-ticket scope
violation was found by prompt/report/path checks. Final numeric decisions all
approve: four 8/8, two 7/8, four 6/8. This is not independent content judging.

Usage: 854 Opus requests/responses, 33,214,640 accounted tokens, no recorded API
errors or rate limits. CLI-recorded API list-price equivalent $55.27. Thinking
is already included in output. The primary's ~1.2M-token summary is incomplete
for job accounting.

Final archive `20261018T023540533633Z` is complete/final, with 11,033 files /
17,094,202,740 bytes, no collection errors and published receipts. Independent
`archive_run.py --verify` passes. Reproducible audit script and JSON are saved
under the campaign's separate `analysis/`; it exits 0 with no delivery,
provenance, incorporation or scope problems. `git diff --check` passes.
No automatic paid rerun/resume or source/checker repair during analysis.
[Detailed analysis](../../notes/s1-completion-fixed-opus-ten-rfe-20261018.md).
