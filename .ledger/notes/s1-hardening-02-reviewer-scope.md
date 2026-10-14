# S1 repair 2: assigned-ticket reviewer scope

2026-10-13 local date; live job started 2026-10-14 UTC.
[Plan](../plans/strat-workflow-s1-hardening.md).

Completed: final local candidate 4102e7a. One corrected GLM case on 107e7af
passed 12/12 scoped report deliveries; final frozen-source parity passed
native/offline controls without another paid run. Archives verify. The
verdict/attention contradiction remains separately tracked for items 4/6.

## Candidate and contract

Local emulator `opendatahub-io/strat-creator`, branch `eval/s1-hardening`,
commit `9ec3db8a470d91f46efe5aea762d3da7644786f0`. Historical pins are intact.

All four reviewer Skills require exactly one strategy key and have no directory
fallback. They resolve the assigned strategy's exact path, its `source_rfe`,
and its own prior review. A local file for another ticket does not switch modes.
The receiving review Skill must stop on a scope error before composition or
publication; it must not rewrite an invalid assessment into a valid one.

Both the interactive strat-creator plugin and Fullsend's strat-pipeline plugin
bundle command hooks and the same Python helper. PreToolUse permits only the
assigned strategy, its source RFE, its prior review and shared architecture
context. It blocks root/batch-directory searches, foreign ticket reads, path
traversal and symlink redirects. SubagentStop checks one assigned-key heading
and rejects other strategy/unrelated RFE keys. Explicit REVIEW_SCOPE_ERROR is
a failed result the caller must handle. The outer receiver and scorer are not
restricted. Item 1's Read/Grep/Glob whitelist and prose delivery are preserved.

The per-agent binding uses the initial expanded Skill prompt and hook agent ID,
not a shared current-ticket variable. It depends on Claude 2.1.296's native
transcript layout. Hooks must remain enabled and the plugin must remain loaded;
standalone Skill files alone provide instructions without this enforcement.
This application boundary does not replace OpenShell or provide an accuracy
judgment. Assignment lookup uses transcripts; assessment delivery does not
recover report bodies from transcripts.

## Offline controls

The component suite passed 867 tests with 7 opt-in tests skipped. The 32 scope
checks include local/CI resolution, concurrent agent identity, wrong tickets,
missing source/identity, broad searches, traversal, symlinks and report target.
Final import sorting passed lint and the scope subset; the architecture-skip
text change passed the 40 integrity checks. No live component smoke was enabled.

One final corrected native scenario against the pinned Claude Code 2.1.296
binary made zero provider calls. Twelve real forked reviewer Skills, four per
three authored tickets, received the original outer status schema. The stub
intentionally attempted three forbidden operations per reviewer and one
wrong-ticket completion, followed by valid inputs and a corrected report.
Result: 36 forbidden tools blocked, 12 wrong completions blocked, 12 targeted
reports delivered; independent capture verification passed. Forty-five local
API request/response pairs, 36 reviewer requests, 96 audited hook events.

Earlier local attempts are preserved under ignored tmp/s1-hardening-02:
- v1 could not open a sandbox socket and never launched Claude.
- v2 rejected the control's missing Workflow metadata before any reviewer ran.
- v3 revealed asynchronous transcript flush: permissions stayed closed, but
  some valid first reads were blocked as well. The helper now waits up to two
  seconds for that agent's initial assignment, then blocks if still unavailable.
- v4 verifies the corrected helper. No unchanged paid scenario was repeated.

Native control working capture: `tmp/s1-hardening-02/native-scope-v4`.
Fixture/binary/helper hashes and requests are retained. Final source differs
from that control only by import ordering, the documented architecture-skip
heading and passive documentation/test additions; live validation uses the
exact final commit above.

## Single GLM scenario

Job `script-run-all-glm-5-3-1014-003034-cdbe05`, created/started
2026-10-14T00:30:34Z. Experiment `strat-workflow-hardening/02-reviewer-scope/glm`.
One execution on the exact candidate commit, strace/API capture enabled,
medium effort and exact `rits/zai-org/glm-5-3` for primary/helpers/all aliases.
No premium model or automatic whole-job retry.

Three distinct authored proposals share the same strategy/RFE directories:
serving timeout handling (9101), dataset retention/deletion (9102), and pipeline
credential rotation (9103). Each receiver calls the real four roles once with
its own key. This isolates scope and delivery; it does not regenerate, score,
compose or publish a full strategy batch. No Jira data is reset or written.

Acceptance uses actual delivered Skill bodies, distinct per-agent native
assignments, effective tools, successful assigned-file reads, hook completion
receipts and foreign-content markers in API messages. Successful CLI/Workflow
status alone is insufficient. Full available system/job evidence is being
collected into private `var/run-data/strat-workflow-hardening/02-reviewer-scope`.

## First live attempt: launcher failure

The first GLM attempt did not reach the reviewer scenario. Two paths after one
`--plugin-dir` flag made the second path become the user prompt on this binary.
The primary agent inspected the fixture and attempted to invoke its test script,
so the host explicitly stopped the job rather than permitting recursive model
work. This is a diagnostic launcher error, not a scope-control pass or failure.
All observed request model IDs before stopping were exact GLM.

The corrected launcher repeats the flag for each plugin and disallows Bash,
Edit, Write and Agent in this diagnostic scenario. Production S1's tools are
unchanged. Native control v5 now loads the exact named reviewer-scope Workflow
and both plugins, and verifies the actual expanded initial prompt and effective
controller tools. Independent verification again passes: 12 targeted delivered
reports, 36 blocked tools, 12 blocked wrong completions, zero provider calls.

The dashboard stop endpoint deletes the Kubernetes job and pods. The archive
collector now accepts an explicit cancellation record and verifies actual job
and pod absence, retaining available system evidence and recording the missing
pod resources/logs as a limitation. Two new offline archive checks pass. No
reset occurred and no failed attempt is overwritten. A corrected source revision
and new single execution will be recorded separately.

## Status

Focused scope validation and final archival are complete. Fullsend sandbox execution,
interactive namespaced-plugin qualification, ten-ticket production batches and
independent content accuracy remain separate.

## Cancelled-attempt archive

Final retained-evidence capture independently verifies with complete=true,
final=true and no source/checksum errors; receipt published:

`var/run-data/strat-workflow-hardening/02-reviewer-scope/script-run-all-glm-5-3-1014-003034-cdbe05/20261014T003618612436Z/`

462 files, including 30 API capture files and 369 strace files. The manifest
explicitly records deleted pod resources/logs as unavailable; complete here
means available retained sources/checksums, not recovery of deleted evidence.
The original stop response and source identity remain in the cancellation
record. The first attempt supplies no evidence that live reviewers stayed in
scope. A CLI exit file alone from the recursive invocation is not accepted.

## Corrected live revision

Commit `107e7afdcc2fc4f1739581d8422f558fa261d1a6` changes only the diagnostic
launcher: repeated plugin flags, disallowed shell/edit/Agent tools and correct
config-directory archival. The full component suite again passed 867 tests
with 7 opt-in tests skipped before local publication. The scope implementation
remains the one in 9ec3db8. Native v5 verifies this named Workflow/launcher.

One new revision execution: `script-run-all-glm-5-3-1014-004354-220e59`,
created 2026-10-14T00:43:54Z, same authored inputs and strict GLM aliases.
Final archive collector waited for terminal status and completed; final results follow.

Native controls and launch/cancellation provenance are privately checksummed and verified at
`var/run-data/strat-workflow-hardening/02-reviewer-scope/native-control/20261014T004715255178Z` (865 files).

## Final live result

The corrected GLM job completed at **2026-10-14T00:57:37Z**, **13 minutes
43 seconds** after creation. CLI exit zero, native Workflow completed. Binary
2.1.296 SHA-256 matches the pinned native controls:
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`.

Independent scope/delivery verification passes with no errors: all **12/12**
real Skill reports, one launch per role/target, identify only their assigned
strategy and mapped RFE. No other ticket's authored content marker appears in
any reviewer API input. All 67 reviewer requests offer exactly Read/Grep/Glob.
The 12 distinct reviewer identities have verified assigned-file reads and
completion hook receipts. Total: 77 request/response pairs, exact hosted GLM
throughout, 101 audited hook events and 19 blocked actions.

| Ticket | Feasibility | Testability | Scope | Architecture |
| --- | ---: | ---: | ---: | ---: |
| RHAISTRAT-9101 | 6,179 | 6,076 | 4,157 | 3,574 |
| RHAISTRAT-9102 | 4,926 | 7,313 | 4,766 | 4,519 |
| RHAISTRAT-9103 | 7,368 | 5,183 | 4,168 | 4,033 |

Cells count report characters actually delivered in receiving requests, not
transcript-only prose. Live denials are assigned-ticket probes in alternate
locations and invalid/broad Glob patterns. They must not be reported as 19
foreign-ticket reads. The native fault control supplies the deliberate
foreign-read/batch-search and wrong-completion tests.

The final **available system/job archive** independently verifies, with final
and complete true, no source/checksum errors and receipt published:

`var/run-data/strat-workflow-hardening/02-reviewer-scope/script-run-all-glm-5-3-1014-004354-220e59/20261014T005748817207Z/`

16 sources, 783 files, 1,281,060,068 bytes; 155 browsable API files and 466
strace files, exact candidate source, native transcripts/journal/state, audit
files, job/pod/events/logs, MLflow/Jira/Observatory snapshots, readable Jira
export and relay telemetry. Shared-service snapshots cover the collection
interval rather than an atomic whole-system instant. No Jira reset or write.

Reported provider usage: 120,220 input, 505,856 cache-read input, zero
cache-creation and 90,906 output tokens; **716,982** across those categories.
GLM billing/category semantics are unverified; no Claude-price estimate is used.
The aborted launcher attempt is separate and is not included in these totals.

## Production source layout qualification

The real strategy-create Skill writes frozen RFE descriptions in CI
`artifacts/strat-originals`, and fresh Fullsend jobs need not have rfe-tasks.
Final candidate **4102e7ae143e8438189b746c9dc69eec3ad5db33** therefore prefers the
assigned frozen source and falls back to the same RFE key in rfe-tasks for CI
compatibility. Local mode continues to use strat-originals. Other RFEs remain
inaccessible. The final full suite passed **868 tests**, with 7 opt-in skips.

One zero-provider native v6 scenario loads the actual named Workflow, final
four Skills/helper and Fullsend plugin with three frozen sources and **no
rfe-tasks directory**. It passes the same 36 tool denials, 12 wrong-completion
denials and 12 corrected deliveries; independent capture verification passes.
No further paid run is used for this deterministic input-path adjustment.
The live GLM evidence is explicitly for **107e7af and the rfe-tasks layout**;
4102e7a's frozen-source layout is verified offline/native, not retested live.

## Separate outcome issue

All three diagnostic receivers returned recommendation=revise while
needs_attention=false. That passes the shape-only VERDICT schema but contradicts
the diagnostic decision instruction. Scope passes; final business consistency
does not. The verifier reports these contradictions separately. This job does
not score, compose or publish, so no production Jira-label claim follows.
[Tracked for items 4/6](../bugs/fixed/strat-workflow-verdict-attention-disagree.md).

## Final status

Item 2's focused repair is complete on local eval/s1-hardening at 4102e7a;
historical refs remain unchanged. Fullsend sandbox execution, namespaced
interactive-plugin use, the full pipeline/ten-ticket batch, content accuracy
and statistical reliability remain separate qualifications. Both live attempts
and local controls are retained; there was one paid execution per tested
revision, no automatic rerun, and no Haiku or Opus inference. Next: item 3.

Final v6 control, exact 4102e7a source and the live verification report have a
new independently checksummed private capture:
`var/run-data/strat-workflow-hardening/02-reviewer-scope/verification/20261014T011617761483Z` (236 files).
The control helper and all four Skill files match the final candidate byte for byte.
Previously finalized job archives were not modified.
