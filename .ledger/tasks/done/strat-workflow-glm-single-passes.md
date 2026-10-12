# Task: One GLM single-RFE iteration each of S1 and S2

## Authorization and scope

User authorized 2026-10-11: one GLM run of S1 and one GLM run of S2,
each one RFE and one iteration. Run S1 first, archive and analyze it, then
run S2 separately. Include one tiny job wiring check before S1. No automatic
benchmark retries, sweeps or batch expansion. Preserve S1/S2 pins and real skills.

Use existing Vertex relay project `vertex-shim-local`, routing hosted model
`rits/zai-org/glm-5-3` to `enmaas-personal`. Keep the private EnMaaS key on
the relay. Pin helper and default model aliases explicitly in job env and
use medium effort. Other models must not silently consume Anthropic quota.

## Acceptance criteria

- [x] Add isolated `glm-smoke` tier with one design/repeat/RFE per invocation.
- [x] Validate model identity against exact requests and the verified GLM
      response spelling without relaxing Claude checks.
- [x] Offline checks; commit/push only required harness changes; sync/import.
- [x] Run one S1 pass after wiring check; archive all run/system evidence.
- [x] Analyze S1 before the separately submitted S2 pass.
- [x] Run one S2 pass; archive and analyze, including failures.
- [x] Record outcomes in the benchmark plan, without claiming quality parity
      or GLM invoice pricing from Claude client fallback metadata.

## Status

Completed. Both one-iteration GLM passes are finished, archived and analyzed;
see terminal evidence below. Existing unrelated local changes are preserved.

## Offline preparation

Markov validate passed; all 26 offline tests passed with real workflow expressions,
including GLM single-arm/repeat guards, explicit helper/effort settings, provider
response aliases and rejected Claude helper calls. Existing tier 1/2 tests pass.
Shell syntax and Python compile checks passed. Service preflight found no active
pipeline jobs or Markov runs. The deployed dashboard already targets the built-in
Vertex relay project. No agent/dashboard/relay rebuild is needed for these
harness-only changes; imported/pushed scripts supply the GLM-specific settings.

## S1 launch

Published/imported Breadboard `7f4362ec65a56cbf8c58da1cda76acb775a9b055`.
One POST created `markov-run-23df27ac` at 2026-10-11 22:48:05.783 UTC.
GLM wiring job `script-selfcheck-all-glm-5-3-1011-224808-df9d56` passed,
including one real model call, alias pins and instrumentation. Seed job
`script-seed-scenario-all-claude-haiku-5-5-1011-224838-1bff87` passed; its
Haiku label is setup metadata, not an inference call. S1 workload
`script-run-workflow-all-glm-5-3-1011-224849-152aa2` started on one RFE,
real pinned workflow/skills, GLM, medium effort, no artifact wipe. Headless
wait ceiling is 90 minutes to avoid a premature background-task cutoff.

Detached collector PID 2888932 waits up to 8100 seconds, then archives and
verifies all available sources and publishes receipts. Launch/source context
is under `var/run-data/strat-workflow/markov-run-23df27ac/launch-context/`.
At 23:13 UTC S1 is at specialist review; no repeat or S2 run launched.

## S1 live finding

At about 37 minutes all four specialist reviewers completed, but their Skill
results contain only completion acknowledgements (100/100/94/101 characters),
not assessments. Nine StructuredOutput calls appear in the captured histories.
This reproduces the known S1 return-loss mechanism on GLM. Model requests remain
GLM-only and API captures show no errors. Final verdict/outcome remains pending;
a smoke pass alone will not establish reviewer handoff correctness.

## S1 terminal outcome

Job completion: 2026-10-11 23:29:15 UTC, exit 0, 2426 seconds (40.4 min).
The single-RFE smoke checks, including exact GLM request identity, all pass.
RHAISTRAT-1 refined/pushed, one matching APPROVE 6/8 review, all locks released.
180 request/response pairs; 740791 uncached input, 7258112 cache-read input,
zero reported cache writes, 179890 output tokens. These are provider-reported
usage categories, not GLM billing estimates or proof of zero hidden reasoning.
All requests use hosted GLM ID; all responses report `zai-org/GLM-5.3`; no API
errors or missing/unreadable responses. Final archive is collecting; S2 waits.

## S1 archive and analysis complete

Final capture independently verifies, complete=true/final=true/errors=[];
receipts published. `var/run-data/strat-workflow/markov-run-23df27ac/20261011T232950539833Z/`:
21 sources, 1931 files, 1304175093 bytes; S1 has 361 browsable API files and
1197 strace files. Two MLflow traces in experiment 9 are OK. Relay capture
contains 198 records, all exact hosted GLM on `enmaas-personal`, no errors.

Four reviewer Skill results are acknowledgement-only; 11 total StructuredOutput
calls. The existing batch reviewer-return detector fails when applied manually
(single-RFE smoke intentionally retains its original gates). This reproduces
S1's known defect on GLM; the smoke pass is compatibility, not handoff correctness.
All 180 provider message IDs use `chatcmpl-...`, yielding zero exact relay joins
because the relay only records `msg_...`. Deferred observability bug recorded;
reconcile current capture by isolated job/time scope, not message-ID joins.

S1 analysis done before submitting S2. No benchmark retry or design edit.

## S2 launch

After S1's verified final archive and analysis, one POST created
`markov-run-428f237a` at 2026-10-11 23:37:40.618 UTC. Seed
`script-seed-scenario-all-claude-haiku-5-5-1011-233743-87e588` passed;
S2 job `script-strategy-entrypoint-all-glm-5-3-1011-233753-27ed46`
created at 23:37:53 UTC on RHAIRFE-1 with unchanged pin
`0287b838d2bc59a2569cf2dd971aad7ad2d76dad`, GLM helper aliases and medium
request effort, repeats=1, no wipe. S1 wiring check is not repeated.
Detached collector PID 2929136 waits/archives/verifies this run; launch context
is under `var/run-data/strat-workflow/markov-run-428f237a/launch-context/`.

## S2 live reliability findings

At about 27 minutes the job remains running. Relay records include
`16e8d603-1e7d-44ee-8774-6e21a87a9fc7`: HTTP 200 stream starts
2026-10-11 23:55:12.463 UTC, ends failed `incomplete_upstream_stream`
after 48381 ms. Request `06e2b7fa-ed2f-4eb9-bbf6-3ef0eaa7edad` starts
23:58:29.875, first event at 4071 ms, becomes cancelled after 323979 ms.
A further request starts 2026-10-12 00:04:37.336. These are not HTTP 429s
or the old 120-second deadline, nor observed 600-second timeouts. API captures
contain no top-level `type:error` bodies so far; this does not mean relay
streams are all complete. Await final reconciliation before declaring clean
transport or attributing why the client cancelled.

A feasibility reviewer reads prior review files under shared
`artifacts/RHAISTRAT/2026*/`, noting one is for a pre-refinement version.
Prior artifacts retained by wipe=false and reused Jira keys may affect reviewer
context. This is evidence of earlier-review access, not proof the final review
is wrong. Preserve paths/content in the final archive; no mid-run cleanup or
reference-design modification.

## S2 client fallback confirmed

Captured non-streaming request
`929c9558-d65b-412b-a509-22bd209e965b.request.json` has identical messages
and all other fields to streaming request
`42606e7c-77da-4ea7-84d0-3c479a3dcf9b.request.json`; only `stream` differs.
Index records a successful tool_use response at 2026-10-12 00:04:37.094 UTC,
model echoed as exact hosted ID, 3584 output tokens. Thus the job performs a
same-model non-streaming fallback, rather than switching upstreams/models.
This is part of the existing client's behavior inside the one benchmark attempt.
At about 44.7 minutes all specialists have finished and the review parent is
assembling its final response; final job result/archive still pending.

## S2 terminal outcome

Job completes at 2026-10-12 00:23:59 UTC, exit 0, 2766 seconds (46.1 min).
All single-RFE smoke/model checks pass, one refined/pushed RHAISTRAT-1,
one matching APPROVE 6/8 review, all locks released. Four reviewer results are
substantive (12439/7859/5488/11399 characters); no StructuredOutput calls.

143 captured requests / 141 responses (140 stream model spellings plus one
non-stream hosted spelling), all exact GLM requests. Provider-reported usage:
790961 uncached input, 7814144 cache-read input, zero cache writes, 206070
output. Response-only API errors/unreadable counts are zero, but do not cover
abandoned/incomplete streams; final relay reconciliation is pending. Native
non-stream fallback is inside this one attempt. Final archive is collecting.

## Completed validation and final archive

S2 final capture independently verifies; receipts published, final=true,
complete=true, errors=[]:
`var/run-data/strat-workflow/markov-run-428f237a/20261012T002415035434Z/`.
20 sources, 1700 files, 1310235963 bytes; 285 API files and 1190 strace files.
Two MLflow traces in experiment 10 are OK. Manual reviewer-return gate passes;
all four returned substantive text (12439/7859/5488/11399 chars), zero
StructuredOutput calls. This tests delivery, not verbatim publication fidelity.

S2 relay: 162 records, all exact GLM on enmaas-personal: 142 streaming
attempts (140 complete, one failed incomplete stream, one cancelled), one
complete non-streaming generation, 19 complete token-count requests. The counts
reconcile with 143 request dumps / 141 successful response dumps. Zero HTTP 429s
and no timeout_error or upstream_stream_error classifications. Exact upstream message-ID joins
remain 0/141 because of the separately recorded ID-format limitation.

Both separately authorized single-RFE iterations are complete and archived.
S1: 40.4 min / 180 responses / APPROVE 6/8; S2: 46.1 min / 141 responses /
APPROVE 6/8. No extra benchmark iteration, design changes, or private upstream
key passed to a job. Model/env wiring is feasible. S1 reviewer loss persists;
S2 transport is not uniformly clean despite successful client recovery. n=1
per design, retained earlier-artifact access and the S2 fallback prevent claims
of quality/runtime equivalence or inherent design performance. No GLM pricing
or actual compute budget inferred from native Claude fallback metadata.

Plan updated; deferred investigations:
`model-relay-enmaas-message-id-not-recorded.md`,
`enmaas-strategy-stream-incomplete.md`. Existing unrelated local changes remain
preserved. Harness implementation was pushed as `7f4362e`; outcome notes remain
local ledger changes. No further run or provider change is required for this task.
