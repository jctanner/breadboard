# Final completion hook times out after a fully processed ten-ticket batch

## Observed failure

Run `markov-run-0e40b64c`, candidate `2a4b7c9`, benchmark `2963585`, Claude
Code 2.1.296, Opus 4.6, ten distinct RFEs and Workflow concurrency ten.
The model job ends FAIL in 37m21s; native Workflow fails after 35m38s.

All ten strategies were created, refined, pushed, scored and reviewed. All
forty role assessments returned, with one launch each and no reviewer rerun.
The final helper wrote a valid completion receipt and result. The trusted host
validator subsequently returned 0; Jira readback and every business check pass.
All ten claims were released. This does not make native completion successful.

The final `write result` agent returns the correct receipt to StructuredOutput
five times. Each `strat_completion_guard.py` PreToolUse call is killed at
approximately ten seconds under `onFailure: block`. The native retry cap then
fails the Workflow, and the failure monitor stops the primary agent. The job
and benchmark correctly retain FAIL, with only `finished` failing evaluation.

## Evidence

Private archive:
`var/run-data/strat-workflow-hardening/pr85-distinct-ten-vertex-opus-20261016/markov-run-0e40b64c/20261017T023730830883Z/`.

Model job: `script-run-workflow-all-claude-opus-4-6-1017-015939-25d06a`.
Native run: `wf_9ef8792d-33a`; final agent: `ae53d585b7e01602d`.
Its transcript records the helper result at 02:33:54 UTC and blocked
StructuredOutput returns at 02:34:07, 02:34:20, 02:34:39, 02:35:13 and
02:35:48 UTC. The receipt identity/hash remain the same. Native error,
`workflow-failure-stop.json`, `run-summary.json`, `eval-result.json` and
`workflow/validation.txt` agree on the split outcome.

Archive complete/final, 10,951 manifest entries / 16,586,566,882 regular-file
bytes, no capture errors. Independent checksum verification passes and final
receipts are published. Raw API captures, syscall traces and native state are
retained. No new inference or retry was used to diagnose this.

## Code path and next investigation

The hook calls `strat_pipeline_outcome.guard()` and
`verify_completion(..., live=False)`. The latter calls `verify_progress()`,
then `business_errors()` calls it again. Each of ten `verify_review()` calls
also starts with a full `strat_freshness.verify()`. Source/context hashing is
therefore repeated within a single completion verification. This is a concrete
batch-scaling concern; exact runtime attribution still needs a matched,
model-free replay with all ten tickets and original tracing enabled.

Profile that fixture and remove redundant verification within one invocation
while preserving full source/context checks, every report/hash/provenance
check, blocking rejection and the timeout policy. Do not reuse a verification
across invocations or weaken the guard merely because saved business work is
complete. Cover the full batch and tampered-input negatives before another
paid run.

The previously fixed refinement checkpoint completed on its first attempt in
this batch. This is a different hook and code path.

[Run result](../../tasks/done/strat-creator-pr85-distinct-ten-opus.md).

## Repair verified and published, 2026-10-17

Signed-off `6ed858b2294a29457153a90f187a801022c21e8b` is pushed to PR 85's
existing feature branch. Full input/progress freshness is verified once per
completion call, followed by private business/review validation. Public
standalone entrypoints retain their own checks. All per-ticket artifact hashes,
attribution, provenance and numeric policy are still checked; no cross-call
cache, public skip flag, timeout change or blocking-policy relaxation.

Matched ten-ticket replay with 453 source files, 1,846 architecture files,
113 receipt inputs, preserved symlinks, original absolute path/image/resources
and tracing: 20.423s before, 2.465s fixed. The old hook reproduces SIGTERM at
ten seconds; the fix passes in 2.601s. Full freshness scans decrease 12 to one;
traced file opens decrease 32,116 to 3,186. Single mechanical measurements,
not a reliability estimate or a new end-to-end model run.

Nine new regressions cover the full batch, same-size/same-mtime changes and
rehashing an outer receipt after altering the last ticket. All 140 focused
checks pass; required unit/full suites each pass 1,089 tests, with five/six
existing optional skips. Eight final full-size traced tampering cases block
within 0.45–2.60s. The main and bundled review helpers agree. Ruff, descriptor
validation, staged allowlist and redacted credential scan pass.

Evidence is collected in `completion-hook-profile-20261017/` under the private
hardening run-data root. Preliminary bundle-copy/test-umask failures are retained
and excluded from final candidate measurements. Both profiling pods are removed.
Final profiling archive independently verifies 10,093 entries / 852,391,176
bytes with no problems. The original run archive also re-verifies unchanged;
its historical FAIL is retained. No profiling pod remains.
[Repair task](../../tasks/done/strat-completion-hook-performance.md).

## Real ten-ticket qualification, 2026-10-18 UTC

The one authorized retest, markov-run-0b098f6e on 6ed858b, completes natively:
all ten strategies and forty role reports published, CLI/host/post/release exit
0. The final guard's traced Python process exits 0 after 2.525709 seconds on
its first receipt, under the unchanged ten-second timeout. Its StructuredOutput
round trip is 2.572s. The write-result agent takes 20.998s overall; that includes
model turns and its separate result helper, not twenty seconds in the guard.

The benchmark's remaining FAIL is two already tracked external assessment-format
false negatives, with all forty reports independently matched across producer,
parent return, saved provenance and final composition. It is separate from
native completion. Archive independently verifies 11,033 files / 17.09 GB;
receipts published. One passing integration observation is not a reliability
estimate. No second model run was submitted.
[Retest analysis](../../notes/s1-completion-fixed-opus-ten-rfe-20261018.md).
