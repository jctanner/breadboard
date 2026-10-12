# R1: Matched-concurrency retest

Pre-registered 2026-10-12. Status: prepared proposal; no paid launch authorized.
This is a named configuration variant, not a replacement for the original runs.

## Question

How do wall time, token categories, equivalent cost and specialist delivery
compare when both designs run one top-level strategy task at a time?
The existing 51.2/88.7-minute pair used different schedules and cannot answer it.

## Design

Prefer a sequential Native Workflow variant over adding a new parallel bash
implementation. Keep S1 source 1bd7f17 and S2 source 0287b83, their real skills,
the batch-three-new-rfes fixture and Opus 4.6. Preserve the original observations.

Use two fresh runs, one per design, on the same pinned runner/Claude binary,
relay image/build, architecture snapshot and benchmark harness. Reusing the old
Scripted Pipeline measurement would retain version/time/environment confounds.
Record exact source hashes, image IDs, model/effort/permission settings and fixture
description hashes before launch. Verify they are unchanged before the second run.

The Native Workflow uses the existing run-workflow.sh script job with:

```json
{
  "CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS": "1",
  "STRAT_BG_WAIT_CEILING_MS": "7200000",
  "BATCH_SIZE": "3",
  "BATCH_EXPECTED_KEYS": "RHAIRFE-1 RHAIRFE-2 RHAIRFE-3"
}
```

Supply the existing STRAT_CREATOR_REF and architecture path as normal. The first
setting is the tested runtime agent cap, not a change to strategy code. Pass it
through the script-job extra_env payload and confirm it appears in the actual
Workflow process environment. Do not describe concurrency as matched until API
intervals show that top-level strategy tasks do not overlap. Nested specialist
concurrency is separately recorded; this setting does not prove those forks serial.

Run the original sequential Scripted Pipeline through its reference entrypoint
with the same source/model/fixture settings. This tests matched top-level agent
concurrency, not identical review implementation or identical generated content.

## Before any paid run

- Obtain explicit authorization for the first individual pass. Preserve the
  existing user policy: one run, archive/analyze, then separately authorize the
  other design. This file and its JSON do not authorize submission or reset.
- Verify no competing workload consumes the account allowance and schedule after
  its reset. Authentication readiness is not a measurement of remaining quota.
- Verify all prior final archive receipts before any Jira reset. Use
  wipe_at_start=false and fresh workspaces/per-run output locations. Paths alone
  do not enforce isolation: record any accessible historical artifacts and flag
  observed cross-run reads. Clear only selected starting state after preservation.
- Produce reviewable, credential-free job payloads with pushed full source SHAs;
  pass secrets through existing service mechanisms, never through this plan.
- Retain the one-run selection guard. No automatic second run or failed-run retry.

## Measurements and stopping rules

Use job wall time, actual top-level API intervals, expected-item completeness,
all four specialist returns per strategy, scope and dissent, returned/posted
records and lock cleanup. Use check_specialist_delivery.py with a hashed expected
report manifest against receiving API tool results; inspect final incorporation
separately. A process exit, valid status schema or acknowledgement is insufficient.

Sum uncached input, five-minute/one-hour cache creation, cache reads and output
by generation ID; thinking is already inside output. Separately report count
requests, ancillary calls, failures and time spent waiting for quota. Cost
remains API list-price equivalent for the managed account, not an invoice.

Proposed operational ceiling: 120 minutes per pass plus bounded collection time.
Before launch, set and verify both job cancellation and the Workflow background
wait ceiling. Record partial spend, native state and any aborted run rather than
silently replacing it with a success. Do not change a ceiling after seeing results.

Planning estimate: the old pair used 25.16M reported tokens and $45.83 equivalent.
That is an estimate for two new runs, not a hard spending limit; sequential cache
expiration, generated content and retries can change it. Obtain the user's
spending ceiling with launch authorization and stop through the external runner.

## Analysis fixed before launch

Report all results, including failed checks. Add a separate matched-concurrency
table to the readable report; retain the original schedule comparison. Calculate
Scripted minus Native differences in time, each token category and cost. Do not
attribute the existing $2.73 gap to caching without measured category differences
and matched configurations. One new pair scopes a scheduling comparison; it does
not estimate general failure rates, content accuracy or safe parallel execution.

Isolation/cache reuse is a separate follow-up: vary shared versus per-strategy
review sessions with identical reference inputs and blinded grading. Both benchmark
designs already have per-strategy review conversations. Do not import older
production shared-session costs as though they described these runs. No quality
campaign, mixed-state batch or ten-pair pilot belongs to R1.
