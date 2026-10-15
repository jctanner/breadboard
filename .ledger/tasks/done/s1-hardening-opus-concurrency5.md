# One Opus three-RFE batch with five Workflow agent slots

Status: done. The authorized run failed on upstream HTTP 429; evidence is
complete, final and independently verified. No automatic retry.

Authorized by the user after the schema repair and concurrency configuration:
launch one S1 batch through markovd using claude-opus-4-6, high effort,
component f3508786a1e2200731b25dfeda7e01ef772d32ce and
CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS=5. No extra iteration or model probe.

## Checks

- [x] Schema-fixed component is pushed; 1,005 component tests and a native
  zero-provider completion control pass.
- [x] All 69 benchmark tests verify the prepared source/concurrency job wiring.
- [x] Publish the exact benchmark source and sync/import it in markovd.
- [x] Verify previous final archives before the seed resets Jira.
- [x] Launch once and verify the actual model job's source, model and cap.
- [x] Archive and independently verify all terminal evidence, even on failure.
- [x] Analyze completion, delivery, preserved reports, source integrity and
  observed scheduling; no automatic paid retry.

## Configuration

Tier s1-hardening-opus, only_tests=S1, variants=opus, repeats=1,
wipe_at_start=false. Existing distinct three-RFE scenario. Native timeout
295 minutes, background wait 17,700,000 ms, job wait 18,000 seconds.

The cap permits up to five outer Workflow agents; three tickets may only supply
three ready agents. Forked Skill scheduling is separate. Both source and
concurrency change from the failed Opus run, preventing attribution of timing
differences to concurrency alone. Source/baseline rewrite protection, scorer
path and specialist format/delivery issues remain open; no new fixes are being
silently added to this run.

Evidence root: var/run-data/strat-workflow-hardening/opus-concurrency5/.
The launch intent must be recorded before the sole POST. An uncertain response
requires reconciliation, never a blind second POST. Terminal collection and
verification precede any later reset.

[Prepared configuration](../done/strat-workflow-next-opus-concurrency.md).
[Hardening plan](../../plans/strat-workflow-s1-hardening.md).

## Launch evidence

Published Breadboard `5ed4a28494bcbb0d3fed31cbe985bca16fc49cc0` and synced/imported
that exact revision in project 1. Scoped credential/path checks passed; unrelated
Org Pulse/binary-analysis changes and the session log were left uncommitted.
Five retained model-job archives independently verified, including both jobs
from the completed GLM/Opus campaign, before the new Jira seed.

One POST at 2026-10-15T02:16:52Z launched `markov-run-f286ae61`.
Seed `script-seed-scenario-all-claude-haiku-5-5-1015-021654-9a7b45` completed;
its model label is setup metadata, with no inference. Model job
`script-run-workflow-all-claude-opus-4-6-1015-021705-c4354c` started at 02:17:05Z.
Read-only inspection of actual Claude PID 149 confirms Opus primary/subagent/
Haiku-alias model settings, cap `5`, background wait 17,700,000 ms and checked-out
source f350878. Its command line specifies high effort. Native progress has
entered Read; completion and final qualification remain pending.

Detached controller PID 3178553 polls read-only, archives the terminal result,
independently verifies its manifest, checks configuration/native source identity
and runs the completion/report-preservation gates. Failures stop without paid
reruns. Native source/launch changes are analyzed, not silently accepted as a
qualification of the pin. Controller, launch intent, imported source and status
are saved under the evidence root's launch-context directory.

## Interim check, about 16 minutes into the model job

Read-only inspection around 02:33 UTC: all three strategies created, refined
and pushed. The three refinement agents started at the same native timestamp
and overlapped, verifying more than two outer agents in this run. Scoring and
review now overlap; two review agents have started. The first review's native
transcript contains Skill and Bash calls with no reported tool errors, so its
request has passed the previous immediate schema rejection. Final result-schema
and business validation remain untested until completion.

One Workflow launch, no primary Edit/Write calls and an empty tracked source
diff at inspection. Job remains running; no intervention or additional inference
was launched by this status check.

## Terminal failure: upstream account rate limit

The model container exited 1 at 2026-10-15T02:40:24Z, 23m19s after job
creation. Native Workflow `wf_06d4a5cf-be3` failed after 1,350,680 ms. All
three strategies were created, refined, pushed and scored. Each review then
failed with `Request rejected (429)` and `This request would exceed your
account's rate limit. Please try again later.` The final result agent also
received HTTP 429 in 420 ms. No review was recorded complete and no
agent-result.json was written. Host validation failed and lock release passed.

Relay logs corroborate HTTP 429 `rate_limit_error` from the Anthropic backend
with `claude-oauth` authentication and upstream request IDs. This establishes
an upstream rejection; the inspected messages do not identify a five-hour
window, reset time or whether increased concurrency caused the limit. No
top-level union schema rejection recurred. One Workflow launch and no primary
Edit/Write calls are observed in the terminal stream.

Benchmark checks fail finished, steps_done, one_review, records_agree and
reviewer_outputs_returned. Markov orchestration completed while reporting that
failed design result. The detached controller began terminal collection at
02:40:53Z; final manifest/independent verification remain pending at this
inspection. No additional paid attempt has been launched. This interrupted
runtime is not evidence of a completed batch's duration.

## Final archive verified

Collection completed at 2026-10-15T02:53:26Z and independent verification
passed at 02:53:34Z, approximately 12m41s after collection began. Manifest:
complete=true, final=true, errors=[]. All 2,898 files and 5,601,760,759 bytes
verify. Inventory includes 450 API-dump files, 2,002 strace files and 64 native
project files, plus logs, Jira, MLflow, Observatory and relay/system snapshots.

Final immutable capture:
`var/run-data/strat-workflow-hardening/opus-concurrency5/markov-run-f286ae61/20261015T024053615666Z/`.
The collector published the verified final receipt. Independent configuration
checks confirm f350878, cap five, exactly one native Workflow and a native
script matching the pinned source. The controller then stopped on the five
expected failed benchmark checks; archival succeeded even though the benchmark
failed. No additional inference or paid run was launched.
