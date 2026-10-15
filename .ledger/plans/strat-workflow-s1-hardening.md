# Native Workflow production hardening

Created 2026-10-13 from the completed strategy benchmarks and Claude Code
2.1.296 controls. Fullsend maintainers rejected custom entrypoints, so the
production work now targets S1. The earlier S1/S2 comparison remains historical
evidence; S2 is not a production candidate for this plan.

## Working rules

- Assess the nine original items below in priority order, starting with report
  delivery. Keep repairs separately identifiable and review results before
  moving to the next item. Items 1–8 have focused repairs; item 9 was rejected
  as not a bug.
- Run each test scenario once per tested revision. No three-round campaigns or
  automatic whole-job reruns. A changed repair may receive a new single test;
  retain the failed attempt and explain the change.
- Use `rits/zai-org/glm-5-3` for all iterative live testing, including primary,
  helper and default model aliases, with medium effort. Keep the personal key
  on Model Relay. Capture actual request model IDs; do not infer them from labels.
- Haiku or Opus requires both explicit user approval and a documented reason
  that GLM cannot answer the required question. No fallback to either model.
- Use offline checks and deterministic local API controls where they answer
  the question. Start live validation with the smallest relevant workload.
- Preserve `pr-83`, `eval/pr-83` at `1bd7f17`, and every historical S1/S2 pin.
  Put S1 repairs on `eval/s1-hardening` in the local GitHub emulator, in an
  isolated checkout. Publishing this local test branch supports job execution;
  public upstream publication is separate from this work.
- Archive each live test's available API dumps, strace, model transcripts,
  workflow state/journal, MLflow, logs, relay and other system evidence under
  private `var/run-data`. Verify archives before any reset. Do not wipe or
  overwrite earlier evidence, and record source, binary, model and test settings.
- A test pass applies to its scenario and tested release. It is not a statistical
  reliability claim or proof of strategy-content accuracy.

## Priority and acceptance

| Order | Problem | Required result | Task |
| --- | --- | --- | --- |
| 1 | Reviewer reports lost at the Skill return | All four role assessments reach the receiving agent through the intended boundary; its outer structured result still works | [Delivery, focused repair done](../tasks/done/s1-hardening-01-reviewer-delivery.md) |
| 2 | Reviewers assess the whole batch despite a single target | Each assessment identifies and covers only its assigned strategy | [Scope, focused repair done](../tasks/done/s1-hardening-02-reviewer-scope.md) |
| 3 | Refine receipt disagrees with completed persisted work | Valid target receipts and explicit reconciliation keep readiness consistent with saved progress | [Refine receipts, focused repair done](../tasks/done/s1-hardening-03-refine-receipts.md) |
| 4 | Final review loses findings or dissent | Composition preserves role findings, source attribution and unresolved concerns under an explicit decision policy | [Composition, focused repair done](../tasks/done/s1-hardening-04-review-composition.md) |
| 5 | Delivery checker accepts status/errors as assessments | Acknowledgements, progress and errors fail the gate; valid targeted assessments pass | [Delivery gate, focused repair done](../tasks/done/s1-hardening-05-delivery-gate.md) |
| 6 | CLI, Workflow and business completion disagree | Final outcome checks required results and persistent state, including null/failed branches and notification failures | [Outcome, focused repair done](../tasks/done/s1-hardening-06-outcome.md) |
| 7 | Crash/restart can repeat side effects | Publication and other externally visible writes are idempotent or reconciled before repetition | [Recovery, focused repair done](../tasks/done/s1-hardening-07-recovery.md) |
| 8 | Replay can reuse stale results | Reuse checks relevant input/source identity; changed inputs invalidate or explicitly reject cached work | [Freshness, focused repair done](../tasks/done/s1-hardening-08-freshness.md) |
| 9 | Proposed budget/deadline policy | Rejected as not a bug; existing Fullsend timeout covers either invocation, and additional limits are optional policy | [Limits, rejected](../tasks/done/s1-hardening-09-limits.md) |

Ten-RFE qualification, shared-file isolation and independent content judging
remain separate requirements after these repairs. They are not additional
iterations implicitly authorized by this plan.

## Item 1: reviewer delivery

The reproduced cause is schema-tool inheritance into forked reviewer Skills.
Tool-ending specialists lose their earlier assessment at a text-only return
projection. Merely asking for prose does not remove the inherited tool.

Start with the configuration remedy already verified in controlled tests:
select an explicit reviewer agent with an appropriate tool whitelist that
excludes `StructuredOutput`. Preserve each real review Skill and the receiving
agent's outer schema. Confirm plugin loading and effective tools rather than
assuming the frontmatter was applied. Direct assessment agents or explicit
persisted report contracts remain alternatives if this configuration fails.

Validation sequence, one execution per case/revision:

1. Check the actual four Skills, agent configuration and existing source checks.
2. Run a focused native-binary control for schema isolation and delivered report
   content, using authored fixtures and no provider calls.
3. Run one focused GLM review scenario using the real patched four Skills and
   a schema-bearing Workflow receiver, without regenerating a full pipeline.
   Verify all four Skill result bodies in the receiving request, role/target
   attribution, absence of `StructuredOutput` in specialist tools, and the
   valid outer result. Do not substitute transcript scraping for delivery.
4. Archive, inspect and record results. Address a demonstrated failure on a new
   revision before proceeding; do not silently repeat an unchanged run.

## Item 2: reviewer scope

Require one exact target, resolve its source RFE from frontmatter, and remove
whole-directory fallback. Loaded plugin command hooks constrain reviewer tools
and validate completed report targets. Per-agent assignment binding prevents
concurrent reviews from sharing a mutable current-ticket setting. Shared
architecture remains searchable; the receiver and scorer retain their tools.

Candidate `9ec3db8` passed offline source checks and a native loopback control:
12 roles across three targets, 36 blocked foreign/broad tool calls, 12 blocked
wrong completions, 12 delivered corrected reports, zero provider inference.
The corrected single GLM three-ticket scenario on 107e7af delivers all 12
correctly scoped reports with no foreign input markers; full archive verifies.
Final candidate 4102e7a adds frozen-source input parity, tested through 868
offline checks and a zero-provider native scenario. That path adjustment was
not rerun live. The aborted launcher attempt is preserved separately. [Evidence and adapter limits](../notes/s1-hardening-02-reviewer-scope.md).

## Item 3: refinement readiness

Candidate `30cf850` binds receipts to the assigned strategy and validates
completion marks against the current run and saved artifact. After refinement,
a fresh helper snapshot determines readiness; a StructuredOutput hook checks
the agent's returned snapshot against actual disk state. A bad receipt no
longer excludes verified work, and a plausible receipt cannot promote
unrecorded work. Verified work is not refined again to repair a handoff.

Component suite: 886 passed, seven opt-in live checks skipped. Native fault
controls reject nested/wrong-ticket structured returns and invented readiness,
recover only completed targets, and use zero provider calls. One GLM fixture
scenario recovers an injected nested receipt for one of two completed targets;
independent captures confirm one refinement each. Full private archival
verifies. [Evidence, added checkpoint and qualification limits](../notes/s1-hardening-03-refine-receipts.md).

## Item 4: review composition

User decision: numeric scores remain the sole approval gate; prose reviewer
recommendations remain informational. Candidate `7cfcada` captures actual
delivered Skill reports with caller/child/tool identities and source hashes,
then composes their full text deterministically. Scorer assessment is labeled
separately and specialist verdicts stay pending until their own reports arrive.
Differing recommendations are explicit without changing the numeric gate.
The completed review/provenance is verified before recording review and by
the trusted host validator; handoff retains its sources.

906 component tests pass, including all 81 numeric score vectors. Native
controls verify capture, composition and rejection of false attention flags
with zero provider calls. One GLM two-ticket authored fixture preserves all
8/8 reports through the actual review orchestrator in 6m02s. Full private
archive independently verifies. [Evidence and qualification limits](../notes/s1-hardening-04-review-composition.md).

## Item 5: assessment delivery gate

Breadboard's checker now requires an assigned strategy section, a completed
role judgment and recommendation, and explanatory content in a matched receiving
Skill result. It rejects progress/errors, acknowledgements, incomplete templates
and conflicting histories; skips and exclusive scope are separate fields.
Immutable replay keeps original gate/pass values beside recomputed results.
The two known false positives fail. Completed real GLM delivery/scope cases
remain 4/4 and 12/12, and the completed S2 Opus batch remains 12/12. The completed
S1 Opus batch remains 2/12, matching independent full-reference checks.

62 benchmark tests and nine reference-checker tests pass; six optional Markov
checks remain skipped. Six original captures and the new private replay evidence
verify. Zero inference tokens, no S1 source/numeric-policy change or deployment.
[Contract, replays and qualification limits](../notes/s1-hardening-05-delivery-gate.md).

## Item 6: final outcome

Candidate `4c32d21` validates coverage, saved completion marks, actual artifacts
and numeric review provenance before writing a hashed completion receipt. The
final structured result and trusted host validation must match that record;
invalid/null outcomes fail the Workflow. Native state/journal observation keeps
work, runtime and reporting outcomes separate. Reporting recovery restores
verified output and the same receipt without changing completed progress.

941 component tests pass, seven opt-in live checks skipped. Three zero-provider
native controls verify completion enforcement, missing work despite CLI zero,
and a reporting error after completed work. One 57-second GLM fixture validates
the final boundary, with five API pairs and one validation command. Complete
live/system and control archives independently verify. Numeric policy, historical
refs and Fullsend's entrypoint are unchanged. Native observation requires an
exported state/journal; Fullsend/OpenShell and full production batches remain
separate qualification. [Repair, evidence and limits](../notes/s1-hardening-06-final-outcome.md).

## Item 7: restart recovery

Candidate `80a11ed` adds durable mutation intent separate from the agent journal,
conservative Jira read-back before repetition, clone-marker/link recovery,
deterministic publication of a saved review, and owner-bound cleanup. A repeated
preparation preserves recovery data. Host results use a sealed bundle, one
immutable directory per run and repeatable summary timestamps; post-script
retry leaves the remote commit unchanged.

966 component tests pass, seven opt-in/unavailable-tool checks skipped. Twelve
real HTTP commit-before-death/lost-response controls independently verify;
local concurrent recovery, owned lock recovery and actual post-script retries
pass. Zero provider calls or inference tokens. Complete private controls archive
verifies. Native Workflow replay, Fullsend/OpenShell and cross-host fencing are
separate qualification; Jira labels are not atomic distributed leases.
[Evidence, conservative stops and limits](../notes/s1-hardening-07-recovery.md).

## Item 8: freshness before reuse

Candidate `0e7e752` records a host freshness baseline and phase provenance.
Same-run source, context, input or artifact changes stop reuse and writes while
preserving work and mutation intent. Later-job review-only continuation needs
matching provenance and live read-back; legacy/changed progress requires
refinement. S1's launch hook rejects native journal replay.

990 component tests pass, seven opt-in/unavailable-tool checks skipped. Three
zero-provider native controls verify unchanged completion, source-change refusal
and refusal of replay using a real completed journal. Local HTTP/host controls
cover changed RFEs, staff input and verified later-job continuation. Complete
private evidence verifies; failed fixtures remain recorded. Zero inference,
no deployment or historical result rewrite. Fullsend/full-batch qualification
and cross-host fencing remain separate.
[Contract and evidence](../notes/s1-hardening-08-freshness.md).

## Item 9: rejected as not a bug

On 2026-10-14 the user rejected this item. Fullsend already applies its
per-iteration timeout to the Claude invocation, whether it runs a Workflow or
an ordinary agent. No additional Workflow-specific limit defect was demonstrated.
A new spending cap or run-wide deadline would be an optional application policy.
Interruption tests can qualify the existing completion/recovery work, but are
not required repairs under this item. Native limit observations remain evidence;
no implementation or new test run was performed for item 9.
[Resolution](../tasks/done/s1-hardening-09-limits.md).

## Evidence

- [Maintained benchmark analysis](../../var/benchmarks/strat-workflow/analysis.md)
- [Benchmark plan and run inventory](strat-workflow-eval-plan.md)
- [Reviewer-return bug](../bugs/open/strat-workflow-reviewer-output-loss.md)
- [Schema inheritance and verified remedy](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-specialist-handoff.md)
- [Runtime controls](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-operations.md)

## Status

During the first integrated three-RFE GLM validation, live diagnosis found
a [scorer-path integration bug](../bugs/open/strat-workflow-scorer-path-outside-composition-scope.md)
not covered by the focused fixtures: Workflow scoring writes outside the
repository while composition requires an in-repository input. This is a new
concrete defect after the original repair review, not a reopening of rejected
item 9. The operator left the job unchanged during diagnosis.
[Interim duration analysis](../notes/s1-hardening-three-rfe-glm-live-duration.md).
GLM subsequently passed all batch/completion/report-preservation checks in
2h13m26s, and its final archive independently verified. The authorized conditional
Opus run exposed another concrete integration gap: Anthropic rejects our
[top-level oneOf schemas](../bugs/fixed/strat-workflow-anthropic-top-level-union-schema.md)
before review begins. The job subsequently failed after about 73 minutes and
its final archive independently verified. The primary edited both Workflow
copies and local freshness baselines, then relaunched twice; the third Workflow
completed, but trusted-host validation rejected the changed baseline. The
benchmark also rejected two specialist handoffs. Deterministic Workflow control
flow therefore did not enforce predictable job termination: the surrounding
agent could change its program and continue. [Observed actions and terminal evidence](../bugs/open/s1-primary-edits-source-and-freshness-after-failure.md).
Source/baseline protection and externally enforced stop/relaunch policy remain
follow-up work. No additional paid run has been launched.

The schema compatibility repair is now pushed on `eval/s1-hardening` at
`f3508786a1e2200731b25dfeda7e01ef772d32ce`. Object-only schema roots plus explicit
JavaScript consistency checks replace the top-level unions. Full suite:
1,005 passed, seven skipped; native completion control and actual captured
schema checks pass with zero provider calls. [Repair and evidence](../tasks/done/s1-hardening-anthropic-schema-compatibility.md).
Live Anthropic qualification of this revision remains pending; existing
benchmark pins and archives are unchanged. The source/baseline rewrite bug
and scorer-path/formatting issues remain separate repairs.

For the next Opus run, the user selected an explicit outer Workflow agent cap
of five. The `s1-hardening-opus` configuration now pairs that setting with
`f350878`; actual job environment, run metadata and summary wiring pass all 69
offline benchmark tests. This three-ticket workload may only have three outer
agents ready; specialist Skill scheduling is separate. Configuration is prepared
locally for publication/import before the next authorized run; no new job.
[Configuration and limits](../tasks/done/strat-workflow-next-opus-concurrency.md).

The user subsequently authorized that one Opus run. Published/imported
Breadboard `5ed4a28`; five prior archives independently verified before seeding.
`markov-run-f286ae61` launched at 2026-10-15T02:16:52Z, with model job
`script-run-workflow-all-claude-opus-4-6-1015-021705-c4354c`. Actual Claude process
and checkout verify f350878, Opus, high effort and cap five. Native progress has
entered Read; final result pending. Detached archival/verification is active.
[Launch evidence](../tasks/done/s1-hardening-opus-concurrency5.md).

The job subsequently failed after 23m19s on Anthropic OAuth HTTP 429 account
rate-limit rejections. Creation/refinement/push/scoring completed; all three
reviews and the final result agent failed, leaving no completed review or
agent-result.json. The schema rejection did not recur. One Workflow launch,
no primary Edit/Write calls observed. Relay logs confirm upstream rate errors;
the exact allowance/reset window and concurrency causation are unestablished.
The final archive independently verified at 02:53:34Z: 2,898 files and
5,601,760,759 bytes, complete/final with no archive errors. Native configuration
checks verify cap five, the pinned script and exactly one Workflow. The
controller stops on failed benchmark checks after successful archival. No paid retry.

The user subsequently authorized one overnight Opus batch after their reset,
at 2026-10-15 00:30 America/New_York (04:30 UTC). Markovd schedule #6 freezes
the same f350878/cap-five/three-RFE configuration and Breadboard 5ed4a28, one
iteration. A read-only observer will archive and independently verify the
outcome before applying benchmark gates. No paid retry is permitted.
[Schedule and observer](../tasks/done/markovd-scheduled-opus-run.md).

That scheduled run has now completed: model job 00:30:12–01:06:40 New York,
36m28s, one native Workflow (34m19s), f350878/cap five and stored script matching
the pin. All stage exits are zero, the completion receipt and every input hash
agree, and all three strategies have one recorded review and released locks.
Actual Skill receiving channels, producer transcripts, report provenance and
published reviews independently verify all 12 report bodies, verbatim.

The pinned benchmark remains FAIL on one vocabulary mismatch: RHAISTRAT-3's
architecture report says “Mostly sound” and is rejected by the canonical
judgment regex. Its actual 7,179-character return is present; result_chars=0
is the classifier's rejected-result projection, not transport loss. The other
nine checks pass. No provider errors/429s occurred in 284 captured calls.
Usage is 10.51M tokens, about $17.48 at the report's standard Opus API-equivalent
rates, not an OAuth charge. This establishes one successful business execution
and preserved delivery, without turning the pinned evaluation green or claiming
independent content accuracy. [Audit and archive recovery](../notes/s1-hardening-scheduled-opus-20261015.md).
The overnight archive timed out on 29 GiB of retained dashboard state. Recovery
now independently verifies: 3,599 files / 9.00 GB, complete/final, errors=[],
with a published checksum-backed receipt. Both incomplete captures are retained;
later source intervals are explicit. No model work or reset was repeated.

Item 1's focused repair is complete: candidate `c49b43c` delivers all four real
reviewer reports in one GLM scenario, retains the outer schema, and excludes
StructuredOutput from all observed reviewer requests. Final system/job evidence
and the native control independently verify under private var/run-data.
[Results and remaining integration limits](../notes/s1-hardening-01-reviewer-delivery.md).
Item 2's focused scope repair is complete (12/12 in the GLM case, final
frozen-source parity checked offline/native). Item 3's focused receipt repair
is complete on `30cf850`; item 4's focused composition repair is complete on
`7cfcada` with the user's numeric-only decision policy. Item 5's deterministic
benchmark checker repair is complete with offline real-capture replays;
item 6's focused completion repair is complete on `4c32d21`; item 7's focused
restart repair is complete on `80a11ed`; item 8's focused freshness repair is
complete on `0e7e752`; item 9 is closed as rejected, not implemented. The
original nine-item repair review is closed: eight focused repairs and one
rejected proposal, with no pending repair in this list. Atomic cross-host
ownership/fencing and deployment/full-batch/content qualification remain
separate production work.
The diagnostic's revise/needs_attention=false result is
tracked for items 4/6 and does not change the scope result. User authorized S1 repair work and
single-execution GLM iterative tests; the earlier requests to keep benchmark
implementations unchanged and ask before each exploratory run do not prevent
this newly requested hardening work. Historical branches and findings remain intact.
