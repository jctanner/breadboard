# One-ticket S1 smoke through the Fullsend fork and Vertex

User authorized one S1 batch, one ticket, one iteration, `claude-opus-4-6`,
through Markovd, using `jctanner-fullsend-ai/strat-creator` branch
`feat/s1-workflow-hardening` at `6a05210215247b287bb0fb61ed02e423c9de8692`.

Use imported Breadboard source `54934699e61ee86a1e00117925e3ff3a0b79ae7f`.
A run-only tier named `s1-integration-opus` selects the existing one-RFE fixture,
batch mode, batch size one, repeats one and five outer Workflow slots. Preserve
the native 295-minute timeout and capture settings, 17,700,000ms background wait,
18,000s job wait, and all evidence. No wipe and no automatic paid retry.
The built-in relay project defaults to the new `vertex-strat-evals` provider;
this run exercises the real Vertex prediction integration for the first time.

Before launch: offline-render the exact run variables, verify no active jobs or
conflicting schedules, independently verify prior final archives, check imported
source and relay readiness. Record intent before one launch POST. An uncertain
response requires reconciliation, not another POST. Observe read-only and
archive the terminal run, including failures, under
`var/run-data/strat-workflow-hardening/fullsend-vertex-opus-one-rfe-20261015/`.

Status: completed, results audited and final archive independently verified.
One launch POST; no additional paid run authorized.

## Launch and live verification

Markov run: `markov-run-d7043ace`, launched 2026-10-15 at about 17:18 UTC.
Seed job `script-seed-scenario-all-claude-haiku-5-5-1015-171820-7295dc`
completed without inference; its model name is setup metadata. Opus model job
`script-run-workflow-all-claude-opus-4-6-1015-171835-332613` completed successfully.

The exact run-only variables passed offline Markov execution, including the
real seed/execution request templates. Four retained prior model-job archives
were independently reverified before launch. Import source and relay account
readiness match the intended revisions and provider. The configured pipeline
dashboard uses relay project `vertex-shim-local` and its relay ADC secret.

Read-only inspection of actual Claude PID 142 verifies source `6a05210`,
the new public fork URL, batch mode, `BATCH_SIZE=1`, one owned RFE (`RHAIRFE-1`),
cap five, and Opus 4.6 for the primary, subagents and model aliases. Tracked
source diff is empty at startup. The relay records successful HTTP 200
generation requests using `vertex-strat-evals` and `google-service-account`
authentication. This established real Opus prediction access through Vertex
at startup; terminal results follow below.

Observer PID 4112002 polls read-only, collects terminal evidence with a
2,400-second stream timeout, independently verifies the capture and retains
failures. It never retries model work. Launch intent/request, imported source,
archive verification, actual-process settings, initial Vertex telemetry and
live status are saved in the archive root's `launch-context/` directory.

## Run-only variable detail

Nested CLI JSON numeric values become floating-point values, while quoted
numbers remain strings; either form fails the seed count's strict equality
against the integer batch size. The run-only tier omits `batch_size`, invoking
the workflow's native integer default of one, and the offline check verifies
the effective one-ticket batch. Counts/timeouts used as environment strings are
quoted. Saved tier definitions and code remain unchanged.

## Terminal results

The model job completed 17:18:35–17:46:29 UTC, 27m54s. All stage exits are zero;
one native Workflow ran 26m17s and its stored script matches 6a05210. RHAIRFE-1
produced RHAISTRAT-1, approve 7/8. Completion receipt, result and all input hashes
agree. All four actual Skill returns match their producer transcripts and
published reports verbatim, with one assigned-ticket section each. Numeric-only
approval preserves the testability reviewer's separate revise recommendation.

All 108 captured Opus generation responses match relay records by upstream
message ID: vertex-strat-evals, google-service-account, HTTP 200, complete usage,
no errors. Token totals agree exactly: 3,743,001 including cache and output.

The pinned benchmark remains FAIL on reviewer_outputs_returned alone. Its parser
rejects the 11,809-character feasibility report because detailed prose appears
under numbered headings and unrecognized fields. An offline replay adding only
a Findings heading in memory passes. Original evidence is unchanged.
[Analysis](../../notes/s1-fullsend-vertex-opus-smoke-20261015.md) and
[checker defect](../../bugs/fixed/strat-review-gate-numbered-findings-false-negative.md).
Final archive completed at 17:53:01 UTC: 1,612 files, 6,357,233,437 bytes,
complete/final, errors=[]. The observer independently verified every checksum
with no problems and confirmed receipt publication. This includes 1,102 strace
files and 217 API-dump files, plus shared databases/logs/Jira/MLflow/relay/native
evidence. Launch context retains the audit scripts/results and exact relay
message-ID correlation. No model work was retried.
