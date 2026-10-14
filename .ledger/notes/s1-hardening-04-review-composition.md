# S1 repair 4: preserve delivered reports and numeric decision policy

2026-10-14. [Plan](../plans/strat-workflow-s1-hardening.md).

User decision: numeric scores remain the sole approval gate. Prose reviewer
recommendations and unresolved dissent must be retained and attributed, but
do not override the score-derived recommendation or attention flag.

The present Skill asks a model to copy four reports into the final review;
apply_scores also supplies provisional reviewer verdicts from the scorer.
The repair will capture actual delivered specialist results at PostToolUse,
then compose their full text deterministically. Scorer feedback remains a
separately identified input, not a substitute specialist report. Source hashes
and invocation identities will let the verifier join the final sections to
their delivered results. Missing required reports prevent final composition.

Native hook probe: Claude Code 2.1.296, pinned binary SHA-256
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`.
The actual PostToolUse Skill event exposes tool_input.skill/args and
tool_response.success, status=forked, agentId and result. Twelve observed
events contain the delivered report text directly. This avoids recovering
assessment bodies from private child transcripts. The reused scope control
made 45 loopback requests and zero provider calls. The first socket-denied
attempt never launched Claude; both attempts are preserved in ignored tmp.

## Candidate and local validation

Candidate `7cfcadaa51b752792011c106e1a2aa27b7c65529` is committed and published
only to the local `eval/s1-hardening` branch. Historical pins are unchanged.

The capture session is bound to the actual caller through the Bash begin
receipt. Four PostToolUse Skill receipts supply role, target, child agent,
tool call and full returned text. The composer exports those exact texts and
the separate scorer source, writes their hashes into a provenance manifest,
and builds the final review without a model rewriting its sections. Pending
reviewer fields remain pending until their own receipts arrive. Architecture
skip is explicit. Recording completion and trusted host validation check the
composed file and sources; handoff retains the provenance and report files.

Numeric-only policy is unchanged for all 81 score vectors. The final suite
passed 906 tests, seven opt-in live checks skipped. Offline cases reject
missing reports, substituted scorer text, changed inputs/review/report hashes,
wrong target/caller/role, invalid fork receipts and inconsistent attention
flags. Six independent archive-verifier tests cover missing delivery,
changed sections, wrong attribution, wrong flags and missing provenance.

Final native control v4: 37 loopback request/response pairs, zero provider
calls; eight complete reports across two targets, joins verified against both
their actual receiving tool results and child final messages. False
revise/needs_attention=false StructuredOutput attempts are rejected for both
targets. Corrections preserve 8/8 approve/false alongside two specialist
revise recommendations and 4/8 revise/true alongside specialist approvals.
The hook also binds a begin receipt mixed with ordinary shell output.

Earlier local attempts are retained: the first composition fixture omitted
reviewer directories and failed setup before Claude launched; v2 omitted the
generated Workflow's STRAT constant and failed before any reviewer ran (CLI
exit 0 alone was insufficient). V3 passes the plain-output path. These are
diagnostic fixture errors, not discovered Claude bugs or paid model retries.

## Live check

One GLM diagnostic completed: `script-run-all-glm-5-3-1014-134422-aa8a5b`.
It uses the real strategy-review orchestrator with authored score/report
fixtures, two different proposals, exact hosted GLM and medium effort for
all agents. Full generation, scorer inference and strategy-content accuracy
are outside this preservation test. No Jira writes or resets.

Created 13:44:22 UTC, completed 13:50:24 UTC: **6m02s**. CLI exit 0 and native
Workflow completion agree with persisted numeric decisions. Independent
verification passes for **8/8 reports**, one real review orchestrator call
and one composition per target, 62 request/response pairs and exact hosted
GLM throughout. Both targets' source files, scorer output, report hashes,
role recommendations and composition-session IDs agree with the final review
and saved progress. Each producer ID also joins to its child's final response;
each report joins to the tool result actually delivered to the receiver.

| Target | Numeric score | Numeric decision / attention | Preserved role recommendations |
| --- | ---: | --- | --- |
| STRAT-9501, serving timeout | 8/8 | approve / false | feasibility approve, testability revise, scope approve, architecture revise |
| STRAT-9502, dataset retention | 4/8 | revise / true | feasibility approve, testability revise, scope approve, architecture approve |

The first review preserves the architecture/feasibility disagreement about
downstream cancellation ownership and the missing delayed-stream test. The
second preserves the hold/deletion race and partial-failure concerns. These
are authored test findings, not new platform conclusions.

Reported API usage: 161,652 input, 1,196,544 cache-read input, zero cache
creation and 37,504 output tokens: **1,395,700** across those categories.
This includes the real review orchestrator and launch/completion conversation;
it is not a matched full-pipeline cost estimate. Medium effort was configured
in the job, CLI and Workflow; captures have no output_config effort field,
so upstream effort enforcement is not inferred from that field. Claude's
hosted-model dollar cost basis is unknown; no provider billing amount asserted.

## Archival

All native attempts, fixtures, captures and test logs have a verified private
archive with 1,538 file/symlink entries:
`var/run-data/strat-workflow-hardening/04-review-composition/controls/20261014T134941671649Z/`.

The final live archive independently verifies at
`var/run-data/strat-workflow-hardening/04-review-composition/script-run-all-glm-5-3-1014-134422-aa8a5b/20261014T135049930340Z/`.
Final/complete true, zero collection/checksum errors: 16 sources, 821 files,
1,313,848,834 bytes, including 124 API dump files (62 pairs), 508 strace files,
native state/transcripts, role/provenance files, exact candidate source,
Kubernetes resources/logs, Jira/MLflow/Observatory snapshots, shared dashboard
data, architecture context, service logs and relay telemetry. The verified
final archive receipt is published to the dashboard archival guard.

Independent verification, launch records and final verifier sources have a
separate checksummed capture:
`var/run-data/strat-workflow-hardening/04-review-composition/verification/20261014T135917170805Z/`.
Prior finalized archives remain unchanged.

## Qualification limits

This repair preserves the full delivered reports and source attribution. It
does not classify every prose disagreement semantically; all opposing text
is retained, while differing recommendations are listed deterministically.
The architecture skip cannot supply an invented specialist approval. Numeric
gate fields remain the original policy. Report-content quality checking is
item 5; whole-run outcome/replay/side effects remain items 6–9.

The hook adapter depends on Claude Code 2.1.296's Bash and forked Skill
PostToolUse payloads and loaded plugins. Full production content generation,
ten-ticket batches, namespaced interactive use, Fullsend/OpenShell execution
and statistical reliability remain separately unqualified. No additional live
run, premium model or historical-pin change was used.

Item 4's focused repair is complete. [Runtime control findings](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-hardening-controls.md)
are also maintained in the binary analysis documentation. The saved dry-run
summary comments identify dissent in both targets, but their prose remains
model-written; the complete review and source reports are the enforced record.
