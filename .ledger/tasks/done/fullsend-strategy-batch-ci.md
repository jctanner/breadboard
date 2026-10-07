# M8: Add batch strategy CI and simplify the normal pipeline

## Goal

Run multiple eligible RFEs through Fullsend from the local GitLab
`strat-pipeline` workflow, using `claude-opus-4-6`. Keep the normal pipeline
focused on strategy work and move milestone diagnostics to opt-in validation.

Use the user-approved names:

- **`batch-discover`**: discover eligible RFEs from Jira using the existing
  pipeline settings; replaces the native name `batch-jql`.
- **`batch-selected`**: process a curated list of RFEs; replaces the native
  name `batch-config` when that variant is implemented.

M8's initial implementation scope remains `batch-discover`. Naming the
selected-list variant does not add it to this milestone.

## Starting points

- Native behavior: `checkouts.tmp/gitlab_rhel_agentic_ci/strat-pipeline/.gitlab-ci.yml`,
  job `batch-jql`, and strat-creator's `scripts/list-rfe-ids.py` and
  `scripts/lock_issues.py`.
- Strat-creator: existing `feat/fullsend-strategy-entrypoint` branch, starting
  at `68614f656df6598e1429cac125d634802c07e0f1`. Read component instructions.
- Breadboard source: `var/demos/fullsend-entrypoint-poc/strategy-ci/` and
  `runner-validation/`; publish `.gitlab-ci.yml` to the existing local GitLab
  `feat/fullsend-strategy-poc` branch. Preserve native `main` for comparison.
- Keep the maintained single runner, job-owned gateway, shared images,
  enabled hooks, Vertex credentials, exact model pin, and artifact redaction.

## Implementation

1. **Add the batch entrypoint and `batch-discover` CI job.** Reuse native JQL discovery,
   processed-work filtering, `BATCH_SIZE` and `BATCH_OFFSET`. Preserve
   `resource_group: strat-batch` and schedule eligibility; add an explicit
   manual invocation for acceptance without enabling a recurring schedule.
   Make batch and single-RFE selection unambiguous. Retain `single-rfe`.
   Use `batch-discover` consistently in CI dependencies, publisher commands,
   tests, and documentation. Keep historical/native references under their
   original names; do not publish a duplicate `batch-jql` alias job.
2. **Preserve batch execution order.** Inside one job-owned sandbox, discover
   candidates, lock the available subset, create strategies for those RFEs,
   refine each new strategy, push refinements to Jira, review each strategy,
   and publish the batch results. Use native `pipeline-settings` reporting.
   Generalize the single-entrypoint assumptions without processing old
   artifacts from the results checkout. Pass owned-lock context to Claude.
3. **Handle limits and failures.** Align CI, Fullsend, and sandbox deadlines
   with the native batch job's five-hour budget. Empty discovery or no acquired
   locks is a successful no-work result without model calls. Process only
   acquired locks; cleanup releases only this job's recorded locks. Preserve
   nonzero failures and partial-work diagnostics, redaction, and teardown.
   Do not automatically replay a partially completed batch.
4. **Simplify the published pipeline.** Remove `lifecycle-check`, `model-smoke`,
   and `sandbox-connectivity` from the normal `.gitlab-ci.yml`. Retain their
   useful checks in a separate opt-in validation configuration/branch, reusing
   the existing runner-validation fixture where practical. Keep necessary
   lightweight preflight checks within real jobs. Remove obsolete stages,
   rules, variables, publisher switches/files, and job dependencies; update
   diagnostic commands so they still work without appearing in normal runs.
5. **Publish results correctly.** Make dashboard dependencies/rules support
   either batch or single-RFE success without requiring a missing job. Keep
   results commits, per-issue reviews, reports, and Org Pulse publication.
   Account for the documented eager-dashboard emulator bug: verify a fresh
   dashboard build after publication, not merely the early bridge status.

## Acceptance criteria

- [x] Focused tests cover multiple RFEs, size/offset, processed/blocked keys,
  partial lock acquisition, empty batches, phase failure, lock cleanup, and
  exclusion of prior-run artifacts. All Claude phases retain the 4.6 pin.
- [x] Validate the actual published CI job graph for batch, single-RFE, and
  opt-in diagnostics. No missing-job dependencies or diagnostic jobs in the
  normal pipeline. Preserve the existing EXIT redaction guard on failures.
- [x] Run component-required tests and syntax/configuration checks, plus
  `git diff --check`. Commit/push fork changes, update all dependent source
  pins, and publish the POC CI branch; record source SHAs.
- [x] Seed at least two fresh, distinguishable eligible RFEs using existing
  fixtures without resetting Jira or altering RHAIRFE-1/RHAISTRAT-1. Record
  discovered candidates before launch and bound the live batch to these
  inputs. Verify the historical processed RFE remains excluded.
- [x] Run one real batch through the maintained runner. For both RFEs verify
  linked strategies, create/refine/review output, actual Opus 4.6 metadata,
  released locks, results commits, per-issue Org Pulse data, refreshed dashboard,
  retained sanitized artifacts, and gateway/container/network cleanup.
  Record pipeline/job IDs and issue/result references. Preserve genuine
  revise/needs-attention outcomes instead of requiring an artificial pass.
- [x] Verify no-work behavior and controlled failure cleanup without spending
  additional model calls. Run a focused single-RFE regression after shared
  code changes; do not replay the processed M6 seed to test it.
- [x] Document normal batch invocation, limits, diagnostic invocation, and
  partial-failure recovery. Leave no recurring schedule or test job running.

## Remaining boundaries

The [nested DNS bug](../../bugs/open/nested-podman-aardvark-dns-startup-intermittent.md)
remains separate; M8 is batch delivery, not a DNS investigation milestone.
If it interrupts validation, retain diagnostics and check partial Jira effects
before any rerun. A failed batch is not acceptance evidence. This task does
not add `reprocess-strat` or claim to fix the emulator scheduler/cancel bugs.

## Status

Complete — 2026-10-06. Source pushed, normal/diagnostic CI published and
validated, two fresh RFEs processed on actual Opus 4.6. Results, per-feature
Org Pulse reads (after standard Jira sync recovery), fresh dashboard and
cleanup passed. The separate Org Pulse stale-key issue remains open.

## Implementation progress — 2026-10-06

- Shared entrypoint supports batch-discover; native discovery/filtering precedes
  size/offset. Optional exact candidate bound aborts before locks if input changes.
- Acquired subset only: create together, refine all new files, push, review all,
  pipeline-settings publication. Clear prior root working outputs; historical
  RHAISTRAT runs remain intact. Recorded owned locks alone are released; nonzero
  failures retain owned-key and partial-work diagnostics. No replay is added.
- Exact 4.6/forced child pin, effort high, hooks, Vertex credentials and images
  retained. CI batch 5h; Fullsend 295 minutes reserves five minutes for cleanup;
  sandbox startup budget 18000 seconds. Single-RFE behavior remains supported.
- Normal CI selects build + single-rfe or batch-discover + matching dashboard
  bridge. Separate needs avoid missing jobs. No batch-jql alias or batch-selected
  implementation. Diagnostics move to runner-validation, including opt-in live
  batch-controls (size-zero no-work and phase exit 37 with real owned-lock cleanup,
  without inference or results publication).
- Focused graph tests: 2 passed. Component unit tests: 520 passed; final full
  suite running before commit/push. Fixtures parse as Python/YAML/Bash.
- Fresh fixtures: RHAIRFE-2 (diagnose JSON support report export), RHAIRFE-3
  (bounded per-check deadlines), adapted from the existing replication fixture.
  Native filtered discovery returns exactly these two; historical RHAIRFE-1
  is excluded. Seed verifies RHAIRFE-1/RHAISTRAT-1 unchanged. Live acceptance
  will use BATCH_SIZE=2, BATCH_OFFSET=0, exact expected-key bound.

Runtime acceptance remains pending; no strategy batch has been started yet.

### First publication and live control finding

Initial fork df3d4cc4d602276b0a4439e6fa8ce3c767bf6667 was pushed after
520 unit / 784 full passed, 1 skipped. Normal CI published at
0771b59a37822178c1a4c3967ebb7641842df92f; validation at
6dc73f18f559857d49af130c7bc8aa9772cfdc85.

Actual single graph 2049: build 3984, manual single-rfe 3985, matching bridge
3986. No diagnostic jobs; canceled without playing strategy. The emulator
includes bridges in both jobs and bridges responses, accounted for in the
check. Opt-in model-smoke graph 2051: build 3988 + smoke 3989 only, canceled
before inference. The eager bridge created its known early dashboard pipeline;
this is not claimed as post-publication acceptance.

Control pipeline 2048/job 3983 failed before sandbox execution: batch harness
sandbox_timeout_seconds=18000 was invalid (supported 30–600). This setting is
startup readiness, not agent execution lifetime. Restored the existing 300-second
startup timeout; five-hour CI and 295-minute agent deadline remain. Fullsend
run.go uses SandboxTimeoutSeconds for readyTimeout, TimeoutMinutes for the
entrypoint execution context and deadline written into the sandbox. No Jira
lock or model call happened. Required suites are rerunning before pushing the
correction. Runtime acceptance remains open.

Correction pushed at efcf94667940301f30920b272c9b2b7f47be9e2b after
520 unit / 784 full passed, 1 skipped. Startup remains 300 seconds; execution
295 minutes. Failed preflight archive 3983 had zero credential matches across
13 entries. CI fixtures now consume the corrected pin; controls are retrying
before any real batch call.

Corrected CI publication: normal fa8b966a58f5dd251a613b15b3deb4da1e5edf1b,
validation 6f2b2251eeecd20ce46033fe1f4e22b4a66830e5, both source efcf946.
Control 2052/build 3990 passed, batch-controls 3991 running. Normal bounded
batch 2053 contains build 3992 (passed), batch-discover 3993 (manual/unplayed),
and matching bridge 3994 only. No diagnostic or single-RFE job is included.
The early bridge is the known emulator behavior and is not final dashboard proof.

### Live controls passed; batch launched

Control **2052/3991** passed: M8_EMPTY_BATCH_PASS and injected phase exit 37
with M8_FAILURE_37_UNLOCKED_NO_JIRA_STRATEGY_PASS. Fullsend metrics show zero
turns/tokens/tool calls. No strategy links or attachments were created, and
RHAIRFE-2's lock was released. Artifact scan: zero credential matches across
26 entries. Cleanup exit 0; no containers or job network remained.

Bounded real batch **2053/3993** is now running from corrected source efcf946
through the maintained runner. Only RHAIRFE-2/RHAIRFE-3 may be discovered.
Historical Jira body hashes and results main baseline were captured before
strategy work; initial results main 05b2a813232d2b3446f30ff17fba6520d7c9215d.
Runtime outcome and final publication/cleanup are still pending.

Live progress: native JQL returned 3 RFEs, excluded the historical processed
RFE, acquired both fresh locks. Created RHAISTRAT-2/RHAISTRAT-3 and pushed
both refinements to Jira. Historical issue hashes still match baseline.
Claude emits an Opus-5/unavailable/4.8 warning, so actual live transcript
metadata was inspected directly: 133 assistant records all report
claude-opus-4-6; no 4.8 response was observed. This warning is not treated as
provider inference evidence. Reviews and final archive verification remain
pending; final scan must include all parent/subagent transcripts.

## Final acceptance — 2026-10-06

### Sources and checks

- Strat-creator: **efcf94667940301f30920b272c9b2b7f47be9e2b** on
  feat/fullsend-strategy-entrypoint, committed and pushed. Initial batch
  implementation df3d4cc; supported startup timeout correction efcf946.
- Fullsend unchanged: **8f628aec6d113181914e2a2307fce17488e2c4b4**.
- Published normal CI: **fa8b966a58f5dd251a613b15b3deb4da1e5edf1b**.
- Published validation: **6f2b2251eeecd20ce46033fe1f4e22b4a66830e5**.
- Final component checks: **520 unit; 784 full passed, 1 skipped**.
  Focused CI graph tests: 2 passed. Python/YAML/Bash syntax and diff checks
  passed. Single-RFE success/no-work/failure regressions passed; no processed
  single-RFE was replayed. Native main remains 14d81319af44973d592e4197b14b680684f35813.

### Real batch and actual model

**Pipeline 2053 passed: build 3992, batch-discover 3993.** Job-owned run
fs-bat-8e342cef7ee1 in pod runner-emulator--project-7-concurrent-0-flw5ady1.
One maintained registration ID 1 remains; no temporary runner was created.
The emulator job API reports generic description gitlab-runner; assignment
trace/pod evidence and the sole maintained registration identify the path.

Native discovery returned 3 RFEs and excluded processed RHAIRFE-1 before
slicing. BATCH_SIZE=2, BATCH_OFFSET=0, expected keys RHAIRFE-2 RHAIRFE-3.
Both acquired locks; one sandbox ran create, two refinements, deterministic
Jira push, two reviews and pipeline-settings publication. The run archive
contains only the two new strategy/review files, corresponding RFE originals
and refinement snapshots; refine_count=1 on each. Old RHAISTRAT-1 was not
refined/reviewed or copied into the new run. Final native discovery excludes
all three processed RFEs and returns no eligible keys.

Archived **17 parent/subagent transcripts, 355 assistant records**, all actual
message.model values **claude-opus-4-6**, with nonzero response usage. No 4.8
response exists in that set, despite the generic Claude Opus-5/4.8 warning.
Vertex credentials, effort high, images and enabled hooks were retained.
Multi-call entrypoint stream_format=none intentionally does not claim aggregate
Fullsend token metrics; transcript response metadata proves actual inference.

| Source RFE | Created strategy | Review | Jira attachment |
| --- | --- | --- | --- |
| RHAIRFE-2 (JSON report export) | RHAISTRAT-2 | approve, 8/8 | RHAISTRAT-2-review.md, ID 2 |
| RHAIRFE-3 (per-check deadlines) | RHAISTRAT-3 | approve, 8/8 | RHAISTRAT-3-review.md, ID 3 |

Both strategies have auto-created, auto-refined and rubric-pass labels; both
RFE processing locks are released. These are the actual model review outcomes,
not forced pass criteria or human sign-off. Historical Jira issue body hashes
for RHAIRFE-1/RHAISTRAT-1 remain unchanged; historical M6 stays 4.8 and
revise/5-of-8/needs-attention. No Jira reset occurred.

### Publication and recovery finding

Run **20261006-223446**, config pipeline-settings, non-dry-run.
Results commit **73af1d2f841966e7acdc7105f1c3b42bcc4fdad6**; summary commit
**54945d1ae4f87a2640310b79e567ea2b0827708e**. Both summary rows match source
RFE and approve/8-of-8; M6 summary row/run remains unchanged.

Org Pulse reported 2 created, 790 unchanged and 16 validation errors in
historical rows. The two new review records were stored, but stale flags left
by the earlier Jira reset hid them from its index. This was a real readback
gap, not list pagination. Invoked the existing admin refresh/handler API with
handlerId=releases:jira-sync to reconcile live Jira keys, without model replay
or manual data-file edits. Per-feature GETs now return each key/sourceRfe,
runId **20261006-223446**, approve, needsAttention=false and total score 8.
[Underlying ingest/refresh bug remains open](../../bugs/open/org-pulse-ingest-recreated-jira-keys-stay-stale.md);
runtime recovery is verified, not represented as a durable product fix.

Eager bridge 3994 ran before publication, as documented previously. Fresh
dashboard **2055/pages 3996** passed afterward: HTML and public/summary.json
contain both strategies; public/runs/20261006-223446.json exists. A transient
GitLab 502 interrupted one observer request; retry collected the successful
job and archive. No job replay was needed.

### Safety, cleanup and handoff

Archive credential scan: **zero hits across 63 entries**, including managed
credentials and Google refresh token/client secret. Gateway cleanup exit 0,
no Podman containers and no job network remain. Outputs, reviews, reports,
telemetry, transcripts and gateway logs are retained as sanitized GitLab
artifacts; runtime copies/proofs remain under /tmp, excluded from source.
Fullsend reported its normal output sanitization and eight audit entries;
this does not claim immutable hooks or complete runtime trace accounting.

Control 2052/3991 demonstrated size-zero no-work and exit-37 owned-lock
cleanup with **zero turns/tokens**, no new strategy and clean retained artifacts.
Single graph 2049 canceled its unplayed strategy; diagnostic graph 2051
canceled its smoke before inference. All test jobs are terminal, one runner
is active and unpaused, and pipeline_schedules is empty. No recurring schedule
was enabled. The nested DNS bug remains separate and open; this successful
batch does not establish a causal DNS fix.

Normal batch, limits, diagnostic selectors and partial-failure recovery are
documented in the strategy CI/runner-validation READMEs and fork invocation
document. Use fresh RFEs for future runs; do not replay these processed seeds.
M8 is complete. batch-selected and reprocess-strat remain outside this scope.
