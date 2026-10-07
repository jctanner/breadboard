# Batch test after CI progress fix

## Goal

Run two fresh RFEs through batch-discover with the updated stdout forwarding,
Claude rendering, credential masking, and exact Vertex Opus 4.6 pin.

## Acceptance

- [x] Two fresh exact-bound RFEs; historical six issues unchanged
- [x] Normal CI uses strat-creator 7244097 and Fullsend bdedebeaf
- [x] Batch completes; live trace contains Claude response text
- [x] Results and review outcomes recorded; owned locks released
- [x] Actual transcript models remain claude-opus-4-6
- [x] Trace/artifact credentials scan clean; gateway/container cleanup verified

## Context

User authorized batch test following logging fix. Existing native discovery
returned no candidates. Reuse M8 fixture with unique marker
fullsend-entrypoint-poc-ci-progress-20261007, without resetting Jira or replaying
processed RFEs. Historical hash baseline: /tmp/ci-progress-batch-historical.json.
Previous optional connectivity probe was canceled during slow GitHub fetch.

## Started

Fresh RFEs RHAIRFE-4 and RHAIRFE-5 match native discovery exactly at size 2 /
offset 0. Existing processed RFEs excluded. Invocation:
`publish.py --batch-discover --batch-size 2 --batch-offset 0 --expected-keys 'RHAIRFE-4 RHAIRFE-5'`.
Pipeline 2057 created on POC commit 7301e4d5f8d28b3fa4fd48168750804a4a893728.
Build 3999 passed; played batch-discover 4000. The dashboard bridge 4001
completed eagerly before batch work (known emulator behavior); a fresh dashboard
build after publication is still required for acceptance.

## First attempt

4000 failed before inference/locks/writes during results-repository clone:
HTTP/2 INTERNAL_ERROR / bad pack header, exit 128. Historical six hashes
unchanged, fresh issues unlocked and unlinked, results main unchanged. Sandbox
removed; no transcripts. Bounded job-only retry uses successful build 3999.
See bugs/open/fullsend-results-clone-http2-stream-error.md.
Retry passed results clone; live CI trace contains Claude assistant text and tool
summaries. Created RHAISTRAT-4 from RHAIRFE-4 and RHAISTRAT-5 from RHAIRFE-5.
Create phase still running; do not replay these RFEs now that Jira effects exist.
Live model check: first 67 assistant records all claude-opus-4-6. RHAISTRAT-4
refined_count=1 and strategy pushed to Jira. The optional architecture-context
fetch reported HTTP 403; it proceeded without that context. Record this evidence
limit rather than claiming successful architecture-context retrieval.
Both refinements completed; native push reports 2/2 strategies sent to Jira.
Review phase started for RHAISTRAT-4. Live model count 103, all Opus 4.6.

## Review evidence gap

RHAISTRAT-4 architecture prose check was skipped without context. The schema
rejects skipped, so the agent set reviewers.architecture=approve based on scorer
2/2 (02:03:54 UTC). Overall approve/8/8 is the published outcome, not proof of
completed architecture-context review. Filed
bugs/open/strategy-review-skipped-architecture-recorded-as-approve.md.

## Final result

Complete: pipeline 2057 / batch job 4000 succeeded on its bounded retry.
Build 3999 duration 8m57s; successful batch attempt 33m48s (29 minutes model
phases, remaining startup/scan/cleanup). CI timeout remains five hours.
Fullsend run fs-bat-ac1383df189e; published run 20261007-021455.

RHAIRFE-4 -> RHAISTRAT-4: numeric approve 8/8.
RHAIRFE-5 -> RHAISTRAT-5: numeric approve 6/8; prose feasibility/testability/
scope request revisions. Per native skill contract, prose does not change the
numeric recommendation or gate. Both review attachments and rubric-pass labels
present, no fabricated human sign-off, both owned locks released. Missing
architecture context / skipped-as-approve remains an open review-evidence bug.

All 367 assistant model records in 17 transcripts are claude-opus-4-6 with
nonzero usage. Source 7244097, Fullsend bdedebeaf, hooks enabled. Trace 3,588,180
bytes, retained stdout 38,667 bytes. All 31 long plain stdout lines appear intact
in trace after stripping ANSI colors; longest stdout line 535 bytes. No runner
log-limit warning. Zero credential matches in trace and all 63 archive entries.
Cleanup exit 0, no remaining containers or job network, test runner pod removed.
Historical six issue hashes unchanged.

Results run commit f90572652600e98d11291fbaba6e60ab29cdfa70; summaries
42551cbb6d9d8cc059a867d64a77aa4311264833. Org Pulse direct per-feature reads
verify source RFEs, run ID and scores after standard releases:jira-sync recovery
(the existing stale-key bug remains open). Fresh dashboard 2059/pages4003 passed
on retry and contains both keys in HTML/summary plus the run JSON. Its first
clone failure overlapped the GitLab restart; retry succeeded after rollout.
Transient API 502 responses during final checks cleared on bounded retry.

User-reported pending/stale warning was a UI/diagnostic defect: lifetime >30m
was treated as stale despite fresh trace updates. Fixed to use job/trace
inactivity and correct non-pending wording. Two diagnostic tests passed; rebuilt
GitLab after batch completion, live job shows success and working authenticated
trace/artifact downloads (anonymous 404). See fixed stale-warning bug.

Proof metadata saved under /tmp/ci-progress-batch-{artifact,log,publication,
dashboard}-proof.json; no credential values were logged. No repeated strategy
run, Jira reset, recurring schedule, or leftover test execution.
