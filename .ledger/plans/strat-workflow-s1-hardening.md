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
a [scorer-path integration bug](../bugs/fixed/strat-workflow-scorer-path-outside-composition-scope.md)
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

## Fullsend fork and real Vertex integration smoke, 2026-10-15

The single authorized Opus ticket on Fullsend fork pin 6a05210 completed in
27m54s, with one native Workflow taking 26m17s. RHAIRFE-1 produced RHAISTRAT-1,
approve 7/8, with all pipeline stages and completion receipt checks passing.
The stored Workflow script matches the pin; the primary launched it once and
only read the final result afterward. All four specialist reports reached their
parent, match their producing transcripts and provenance hashes, and appear
verbatim in the composed review, with one assigned-ticket section each.

All 108 actual generation responses match real Vertex relay records by message
ID, with google-service-account authentication, HTTP 200, complete usage and
no errors. Usage is 3,743,001 tokens including cache; thinking is already counted
inside output. The eight token-count operations in the same window also succeed.
This validates the fork/provider integration in one smoke, without claiming
full-batch reliability or independent content accuracy. The numeric-only gate
correctly retains a testability revise recommendation while approving 7/8.

The pinned benchmark remains FAIL on one
[new parser false negative](../bugs/fixed/strat-review-gate-numbered-findings-false-negative.md).
Its feasibility classifier ignores detailed numbered findings attached to
unrecognized fields, despite an 11,809-character delivered report. An offline
replay adding only a Findings heading in memory passes; the original evidence
is unchanged. Report-format validation and actual transport delivery need
separate diagnostics, since result_chars=0 after rejection again conceals a
nonempty return. No further paid run or code repair was performed.
The final archive independently verifies 1,612 files / 6.36 GB, complete/final
with no archive errors and its receipt published, including API dumps and strace.
[Run analysis and archival status](../notes/s1-fullsend-vertex-opus-smoke-20261015.md).

Follow-up timing diagnosis: one ticket used about 64% fewer tokens than the
overnight three-ticket run but only 24% less job time (27m54s versus 36m28s).
The earlier run overlapped ticket refinement/scoring/review, so reducing ticket
count does not divide the dependency chain by three. One-ticket refinement
still took 6m29s and scoring/review 15m42s. Within its review, all four Skill
calls came from one model response but executed serially over 8m49s; the longest
individual reviewer took 2m50s. This also occurs per ticket in the older run.
[Observed serialization](../bugs/open/strat-reviewer-skills-serialized.md) is a
separate performance follow-up. Its cause is now confirmed: Skill inherits
isConcurrencySafe=false and the Claude dispatcher serializes unsafe tools.
Two credential-free native controls at cap five show one active child request
for four Skills from one caller and four active requests when each Skill has
its own Workflow caller. No pipeline repair or paid retest has been performed.
The [binary report](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-skill-concurrency.md)
retains the exact byte ranges/hashes, runner and control outcomes.
The outer cap was already five. No broad Vertex slowdown or paid retry was
observed; this pair changes fixtures, provider and source and cannot isolate
their causal effects.

The same reviewer serialization is confirmed in the pre-Workflow invocation
path. A plain claude -p slash-command control, with Workflows disabled, returns
all four Skills but reaches concurrency one; no real provider calls are made.
Archived S2 Opus calls show matching ordered child response ranges for all three
tickets, with launch/first/last response hashes checked against provenance.
This restriction belongs to Claude's Skill dispatcher and is shared by both
designs. It is not a new regression caused by the Workflow integration.

### Reviewer concurrency deferred by the user

On 2026-10-15 the user put this optimization on the backburner. The ideal
single-ticket saving is approximately six minutes, not a measured speedup.
A full ten-ticket fan-out would need 40 simultaneous reviewer workers, plus
any overlapping scoring/coordination. The proposed change would also require
multi-caller session binding, actual-report receipt/hash validation, explicit
handling of parallel()'s null failures, and preservation of completed reports
for recovery. A clean scheduling expression does not remove that supporting
work. Keep the existing dispatch and retained binary/control evidence.
No concurrency implementation or additional qualification runs are planned
until the user revisits the [deferred finding](../bugs/open/strat-reviewer-skills-serialized.md).

### Ten-ticket batch and cap ten prepared

The user subsequently requested ten tickets and Claude concurrency ten without
reopening reviewer dispatch. Both current S1 hardening tiers now select the
ten-RFE scenario, explicit Workflow cap ten and one iteration. The Fullsend fork
pin remains 6a05210. The scenario combines seven independent existing RFE
templates with three new requests covering training checkpoint recovery,
connection credential rotation and portable evaluation report export. Complete
coverage requires ten strategies and forty role reports; the four Skills within
each ticket still execute serially. Historical one-/three-ticket tests remain.

Published source 0359a9a394e3f27beee084031958fd91fa932da6 and synced Markovd
project 1 / workflow 744. All 64 imported files match exactly. All 75 offline
benchmark tests, Markov validation and read-only ten-RFE seed validation pass.
This prepares the next run; no model job, reset or issue creation was performed.
GLM remains the iterative model and Opus requires separate approval.
[Configuration, fixtures and launch variables](../tasks/done/strat-workflow-ten-ticket-config.md).

The user authorized launch of the prepared batch. One POST started GLM run
markov-run-d72c2f57 at 2026-10-15T19:10:43Z, with ten RFEs, cap ten and one
iteration on 0359a9a / 6a05210. Exact offline launch rendering, all imported files,
five retained prior archives, idle/schedule checks and GLM relay readiness pass.
Seeding/discovery passed and the model job is running. A detached observer will
archive and independently verify terminal evidence, including failures. No
automatic paid retry or Opus continuation. [GLM run task](../tasks/done/s1-ten-ticket-glm-c10.md).
Startup inspection now verifies the actual clean source checkout, ten acquired
RFEs, batch size/cap ten, medium effort and exact GLM pins for primary/helpers
and aliases. Successful GLM generation requests use enmaas-personal. Completion
and final archive remain pending.

The user then identified that GLM was not the intended model and explicitly
selected “Stop GLM, archive, then run Opus.” Dashboard stop deleted the GLM
job/pod at 19:20:32 UTC and the Markov runner at 19:20:41 UTC. The stale Markovd
run was reconciled to cancelled. This is an interrupted wrong-model run, not
a model failure. Shared storage retains the workflow stream/stderr, 95 API
dump files and 678 syscall trace files; native pod-local transcripts/worktree
and pod logs were lost before the exit capture. Recovery archival records that
limitation, captures all retained system evidence and verifies it before reset.
One ten-ticket Opus run with cap ten is authorized next. Exact offline launch
passes with source 0359a9a / candidate 6a05210. No automatic retries.
[Opus task](../tasks/done/s1-ten-ticket-opus-c10.md).

The cancelled GLM recovery archive independently verifies 894 files totaling
6,123,261,163 bytes, with no capture-source errors and a final receipt published.
Its manifest explicitly records the deleted native/pod-local evidence. Final
capture: fullsend-glm-ten-rfe-c10-20261015/markov-run-d72c2f57/20261015T192802999222Z.

One Opus run, markov-run-fbc62d49, launched at 2026-10-15T19:38:50Z after all
archive, source, idle/schedule and Vertex checks passed. Model job
script-run-workflow-all-claude-opus-4-6-1015-193904-1a3da4 verifies clean
6a05210 source, all ten acquired RFEs, batch size/cap ten, high effort and Opus
for primary/helpers and model aliases. The first nine streaming calls are
claude-opus-4-6, HTTP 200 through vertex-strat-evals. A detached read-only
observer will archive and independently verify terminal evidence; no automatic
model retry. Evidence: fullsend-vertex-opus-ten-rfe-c10-20261015 under the same
private run-data root. Completion is pending.

### Ten-ticket Opus result: repeated identical recommendation breaks capture

The run failed after 51m24s of model-container runtime. Native Workflow failed
after 44m47s; outer CLI exited 0 and the host validator exited 1. All ten
strategies were created/refined/pushed and scored. All forty assigned role
reports returned to callers, but only 38 were captured for review composition.
RHAISTRAT-3's feasibility report and RHAISTRAT-7's testability report each
repeated the same Recommendation: revise within its body and at the end. The live
report_verdict parser requires exactly one match, so it rejected both reports
and left their composition inputs absent. Eight final reviews published; these
two did not. The callers returned inconsistent approve/needs_attention=true
receipts, which the Workflow rejected. Its final completion check correctly
failed rather than declaring partial business work complete.

Both failures reproduce with the archived reports and current parser without
inference. Removing only the duplicate agreeing line in memory makes each pass.
Follow-up: tolerate repeated identical decisions, reject conflicting decisions,
and preserve original report text/hashes. This is a live hardening-code parser
defect; three additional feasibility rejections in the historical benchmark
are the separate, already recorded numbered-findings false negative.

Lock release exited 0. The release record and archived Jira readback confirm
all ten claims removed. The post-script did not publish the batch bundle.
Relay recorded one 502, but all forty reports were delivered and the terminal
errors identify the parser condition. Native/CLI/business completion remain
separate signals. Markov itself completed its evaluation with a FAIL result.

Archive complete/final and independently verified: 10,935 files /
20,472,635,632 bytes, no capture errors, receipt published. Includes native
state/journal/transcripts, 1,898 API body files and 7,392 syscall trace files.
No retry, resume or additional paid run. [Audit](../notes/s1-fullsend-opus-ten-rfe-20261015.md),
[capture bug](../bugs/fixed/strat-review-duplicate-recommendation-capture.md).

Prompt inspection gives a likely explanation for the repetition: both reviewer
Skills include Recommendation in their output template and separately say to
end with exactly one recommendation line. The parser requires one occurrence
in the entire report, a stronger condition than the ending instruction clearly
expresses. RHAISTRAT-3 repeats its summary verdict after findings; RHAISTRAT-7
repeats its verdict after requested changes. Both end as instructed. Clarify
the whole output layout and retain robust extraction of agreeing repeats;
the observed evidence does not establish the model's internal motivation.

### Agreeing duplicate recommendation fix verified locally

User authorized accepting repeated recommendations when their verdict agrees.
The plugin capture helper and trusted-host helper now require one unique valid
verdict across the report's Recommendation fields. Repeated agreeing values
pass without rewriting report text or hashes; missing, malformed, blank and
conflicting values still fail, and only architecture may skip. Numeric scores
remain the sole approval gate. Breadboard's independent benchmark classifier
now applies the same agreement rule while retaining its other content checks.

Both unchanged failed reports pass all three consumers in offline replay;
the live parser accepts all forty archived role reports. Composition checks
verify exact bytes, hashes and provenance survive through host verification.
Fullsend fork tests: 47 focused checks, 575 unit passes / five skips, 1,033
full-suite passes / seven skips. All 79 benchmark checks pass with offline
Markov execution. Changed component files pass Ruff; both diff checks pass.

These are local working-tree edits, not yet committed/pushed or synced into
Markovd. No paid run, resume, archive alteration or regrading of the historical
FAIL. The independent numbered-findings checker issue remains separate.
[Fix task](../tasks/done/strat-review-agreeing-recommendations.md).

### Next scenario: mixed-state batch

The user requests a batch cap of ten against 20–30 Jira records containing
fresh RFEs, existing STRATs at intermediate/final states and gated controls.
Discovery, preparation and freshness rules have been read from the current
fork. Review-only recovery requires genuine matching prior push provenance;
labels alone are not sufficient. The present seed/checker assumes all-new
RFEs and needs an explicit mixed-state manifest and per-ticket before/after
checks. A no-reset discovery/preparation repeat can test the finished state
without a second model invocation. The current late human-sign-off gate can
reduce acquired work below the discovery batch cap; record that explicitly.
[Scenario design](strat-workflow-mixed-state-batch.md). No Jira/model action yet.

## PR 85 follow-up qualification, 2026-10-16

Deeper review of the same successful mixed Opus run confirms all nine reviewers
worked around the known scorer-path defect by staging files inside the repo.
All nine scorers lacked Bash for their required recovery preflight. Strace also
shows the refinement StructuredOutput guard and final completion guard killed
by Claude after about ten seconds, with execution continuing. Host completion
validation still passed. Operational completion therefore does not establish
that every guard ran or that only benchmark-parser defects remain. A complex
Markdown round-trip probe also confirms a review-only fingerprint coverage gap.
These are open defects/qualification gaps; no new model run or source repair.
[Review disposition and exact evidence](../notes/strat-creator-pr85-review-triage.md).

### Post-review one-ticket Opus smoke: blocking hook still exceeds its budget

One authorized run, `markov-run-64a6b4f4`, tested repaired PR 85 head 18cdf46
with Claude Code 2.1.296, one RFE and cap ten. The model job failed in 15m46s.
Creation/refinement succeeded; no scoring or specialist review started. The
refinement checkpoint agent carried the correct helper JSON, but its
`refine_checkpoint_guard.py` PreToolUse hook exceeded ten seconds on five
attempts. The now-blocking timeout behavior correctly failed the Workflow;
valid local work alone did not produce a deliverable receipt.

Moving Jira work out of short hooks did not establish a safe local runtime
budget: the guard still performs duplicate source/context freshness scans.
That code path is verified; precise cost attribution requires profiling with
the full staged architecture tree and instrumentation. Retain fail-closed
validation and address the bounded-work problem. A small native fixture passing
without provider calls did not cover this production-size hook execution.

The failure monitor stopped the primary after native failure, the host checker
rejected missing final output, and all claims were released. All 81 captured
inference requests used Opus, with no recorded API/rate-limit errors. Markov
`completed` only means its evaluation finished; the model job and benchmark
failed. Final archive complete/verified: 1,228 files, no capture errors, receipts
published. No retry or resume. [Result](../tasks/done/strat-creator-pr85-reviewed-opus-one-rfe.md),
[guard defect](../bugs/fixed/strat-refine-checkpoint-hook-timeout.md).

Archived syscall follow-up confirms the immediate cost: 453 source and 1,846
architecture files are scanned, then scanned again through saved-progress
verification. The initial single-pass guard completed in 5.60 seconds. Each
later failed guard made over 82,000 metadata calls and about 5,000 file opens
before Claude sent SIGTERM at ten seconds; the progress lock was acquired and
no network connection occurred. Roughly 60 MB of trace was generated per failed
guard. Benchmark instrumentation is part of the observed runtime environment;
its contribution needs a model-free matched replay rather than attributing
the full cost to filesystem speed. Full snapshot and tracing budget coverage
must accompany short-hook verification, not only miniature fixtures.

### Model-free profiling and checkpoint performance repair

The isolated replay matches all 453 source and 1,846 architecture hashes,
preserves seven Git symlinks, and uses the original absolute path, image
(Python 3.13.16), resource limits and tracing flags. Original hook: 1.386s plain,
10.731s traced; a ten-second cutoff reproduces its SIGTERM. The repaired hook:
0.366s plain, 1.921s traced, and passes the same cutoff in 2.096s. Traced metadata
calls decrease from 91,133 to 1,133. These are single matched mechanical
measurements; they do not establish a new model-run success rate.

The repair combines input/progress verification into one full baseline check,
and uses directory-entry traversal with explicit alias/cycle containment.
All logical content hashes are recomputed on every invocation. No freshness
cache, added agent/hook, timeout increase or failure-policy relaxation is used.
Thirteen new regression cases cover alias behavior, unchanged-size/timestamp
edits and absent/empty/foreign progress. Full-size traced rejection cases still
block forged return JSON, changed source/context and forged artifact provenance.

All 84 focused checks pass. `make test-unit` and `make test` each pass 1,080
tests, with five/six existing optional skips. Ruff, descriptor validation and
diff checks pass. Signed-off 2a4b7c9 is pushed to PR 85's existing branch; its
component worktree is clean. Evidence, exact fixtures/patch, profiles, traces, image identity,
controllers and logs: `refine-checkpoint-profile-20261016/` under the private
hardening run-data root. Preliminary controller/copy-topology measurements are
retained and excluded from the final pair. The temporary profiling pod is
removed; no model calls or Jira reset occurred. A later authorized smoke must
use the new source SHA and fresh host preparation, preserving the failed run's
baseline rather than adopting its progress across a code change.

The final profiling archive independently verifies 4,372 entries / 504,789,902
bytes with no problems. Its saved verifier and checksums permit later replay.
The published source diff exactly matches the profiled candidate patch. No
end-to-end model run has been repeated; the original smoke verdict stays FAIL.

### Authorized checkpoint-fixed one-RFE Opus retest: PASS

Run `markov-run-f5a9eb0a` tested published 2a4b7c9 with the same pinned Claude
Code 2.1.296 and benchmark 440d864, one RFE and cap ten. The job completed in
26m38s; native Workflow completed in 25m24s. Independent evaluation passes
every check, and all pipeline stage exit codes are zero. One strategy was
created/refined/pushed and reviewed, all four assigned assessments returned
without reruns, and all claims were released. Final score 7/8 approves under
the numeric-only approval policy, although two role reports recommend revision.

The refinement checkpoint that previously failed completed on its first attempt.
The checkpoint agent's full 10.454s includes inference and its helper command;
it does not mean the ten-second hook cutoff was exceeded. CLI stderr contains
no hook timeout. The final business receipt also validates. This is one
successful integration retest, not a measured reliability rate or independent
content-quality judgment. The original failed run remains FAIL.

All 117 captured requests use Opus 4.6, with no recorded API/rate-limit errors.
Accounted usage totals 4,897,354 tokens, mostly cached input. Job evidence is
collected under `pr85-checkpoint-fixed-vertex-opus-one-rfe-20261016/` in the
private hardening run-data root. Final archive independently verifies 1,742
entries, complete/final, no capture errors, and receipts are published.
No further paid run or resume was launched.
[Run task](../tasks/done/strat-creator-checkpoint-fixed-opus-one-rfe.md).

### Fresh ten-ticket batch authorized

The user requests one ten-ticket batch and explicitly requires distinct RFEs.
The earlier all-new fixture reused historical templates, so a separate
`batch-ten-distinct-v2` scenario introduces ten newly authored requests with
independent deliverables and explicit scope boundaries. Historical fixtures
and verdicts remain intact. The `s1-pr85-distinct-ten-opus` tier pins 2a4b7c9,
one Opus iteration, batch size/cap ten, native capture and failure monitoring.
Preflight and offline rendering must pass before the single paid submission.
[Task and scope review](../tasks/done/strat-creator-pr85-distinct-ten-opus.md).

Published benchmark 2963585, 99 tests (one optional skip), directory validation
and exact-payload offline execution pass. All 80 imported files match. Prior
archives independently reverify before Jira reset. One run launched through
markovd-cli at 2026-10-17 01:59:22 UTC: `markov-run-0e40b64c`. Live readback
confirms all ten new RFE descriptions exactly match their fixtures, with ten
unique hashes. Process inspection verifies candidate 2a4b7c9, acquired keys
RHAIRFE-1 through RHAIRFE-10, cap ten and Opus for primary/helpers/aliases;
successful Vertex requests use the intended service-account profile. The
detached observer archived terminal evidence and published verified receipts.

### Fresh ten-ticket result: completed business work, final hook timeout

The job ends FAIL after 37m21s; native Workflow fails after 35m38s. All ten
distinct RFEs produced separate created/refined/pushed/scored/reviewed strategies,
with no deduplication or skips. All forty role assessments returned with one
launch each and no reruns. All final recommendations approve by the requested
numeric-only policy (three 8/8, six 7/8, one 6/8). All claims were released.
The host's business validator passes and independent evaluation passes every
check except `finished`. This is not independent validation of strategy quality.

The final result helper produced a valid receipt at 02:33:54 UTC. The `write
result` agent returned it unchanged, but its `strat_completion_guard.py`
PreToolUse hook timed out at ten seconds on all five attempts. Blocking behavior
failed native completion; the failure monitor stopped the primary. CLI exit 1
is a real runtime failure even though trusted host validation and post/release
steps return 0. Do not call the native Workflow successful from saved artifacts.

The repaired refinement checkpoint passes first try. The final guard has a
separate repeated-work path: completion verifies progress, business validation
does so again, and each ticket's review verification scans freshness again.
Full-batch local replay under tracing is needed to measure this scaling cost.
Short-hook tests must cover the largest supported batch, not just the full
architecture tree with one ticket. [Final-hook defect and repair](../bugs/fixed/strat-completion-hook-ten-ticket-timeout.md).

Accounted usage: 31,994,117 tokens, exclusively Opus 4.6; 866 request captures
and 865 usage-bearing responses, no recorded API/rate errors. Final archive
complete/final, independently verified: 10,951 entries / 16,586,566,882 bytes,
no collection errors and receipts published. No paid retry or resume occurred.

### Ten-ticket completion hook optimized without model calls

Matched replay reproduces the ten-second kill: the old final hook takes
20.423s under original tracing. cProfile measures twelve full freshness checks
within one completion call. The repaired hook takes 2.465s traced and passes
the same ten-second cutoff in 2.601s; plain runtime is 2.858s before, 0.643s
after. File opens fall from 32,116 to 3,186 and trace bytes from 81,091,443 to
9,634,165. These are single matched mechanical observations, not a measured
reliability rate or a successful new model run.

Completion verifies the complete input/progress baseline once, then checks
every task, score, role report, attribution and manifest through private data
validators. Standalone public validators retain freshness checks; separate
calls rescan content. There is no cross-call cache or exposed skip flag, and
the configured timeout and blocking/numeric policies are unchanged.

Replay preserves all 453 source and 1,846 architecture hashes, 113 receipt
input hashes, ten strategies and seven Git symlinks, with the original absolute
path, Python 3.13.16 image and resource/tracing settings. A separate authored
candidate fixture records changed-code provenance, never a production baseline
rewrite. Eight final traced tampering cases block within 0.45–2.60s, including
rehashing outer receipts after changing the tenth ticket. The source negative
preserves valid Python, size and mtime and fails specifically on freshness.

The first full suite caught a missed bundled review-helper copy and a permission
fixture affected by the profiling launcher's umask. Both are corrected; initial
logs/measurements are retained and excluded from final candidate numbers. The
synchronized final candidate is reprofiled under the same image/resources.
Required unit/full suites each pass 1,089 tests (five/six existing optional
skips); 140 focused checks, Ruff, descriptor and diff/credential checks pass.

Signed-off 6ed858b is pushed to the existing PR 85 feature branch. Its patch
matches the final profiled candidate. Evidence is collected under
`completion-hook-profile-20261017/`; its final archive independently verifies
10,093 entries / 852,391,176 bytes with no problems. The original ten-ticket
run archive also re-verifies unchanged. Profiling pods are removed. No model
calls, deployed Jira reset or paid retry.
A future authorized fresh run must select the new source SHA; the historical
ten-ticket FAIL and its archived source/progress remain unchanged.
[Repair task](../tasks/done/strat-completion-hook-performance.md).

### Authorized ten-ticket retest on the completion-hook repair

The user authorized one rerun with the same ten distinct fixtures, Opus 4.6,
high effort and cap ten. New tier `s1-pr85-completion-fixed-opus` pins 6ed858b;
benchmark source f980238 is published and all 80 imported files match. Both
historical pins and failed verdicts are retained. Directory/exact-payload
validation and 99 offline tests pass; incomplete discovery and invalid model,
design or repeat settings stop before inference.

Earlier preparation stopped before submission. When the user checked status,
no launch intent/response or new Markov run existed. Missing temporary files
were restored from durable campaign evidence and checks repeated with the
repo-local binaries. Prior archives and all completion-fix evidence independently
verify; provider readiness and idle/schedule checks pass before Jira reset.

One run submitted through `checkouts/markovd/bin/markovd-cli` at 2026-10-18
01:56:31 UTC: `markov-run-0b098f6e`. Startup verifies clean 6ed858b source,
ten acquired keys, all Opus aliases, cap ten, expected pipeline image and
successful Vertex service-account requests. Actual Jira descriptions exactly
match the ten distinct fixtures. A detached observer collects/verifies terminal
evidence under `pr85-completion-fixed-vertex-opus-ten-rfe-20261017/` in the
private hardening run-data root. No automatic paid retry.
[Retest task](../tasks/done/strat-creator-completion-fixed-ten-opus.md).

### Completion-hook retest: native success, two checker format false negatives

Run markov-run-0b098f6e completes the native Workflow in 36m41s and the model
job in 38m26s. All 36 Workflow agents complete on their first attempt. CLI,
host validation, post step and release exit 0; all ten distinct strategies are
created/refined/pushed/scored/reviewed, none merged/skipped, all claims released.
The final completion guard passes its first receipt in 2.525709s traced,
with the unchanged ten-second timeout. StructuredOutput round trip is 2.572s;
the entire write-result agent takes 20.998s, which includes separate work.
This is one real full-batch qualification of the optimized guard, not a
reliability rate. The preceding failed run and its source remain unchanged.

Pinned evaluation retains FAIL solely for reviewer_outputs_returned: 38 reports
accepted and two complete reports rejected. Feasibility for RHAISTRAT-5 has
9,265 characters and detailed Markdown-numbered headings the checker misses;
architecture for RHAISTRAT-6 has 6,391 characters and a judgment beginning
“Core architecture is sound.” These reproduce the known findings/prefix defects.
Independent joins confirm all forty producer transcripts, receiving Skill
results, provenance hashes and composed reviews agree. Formatting-only probes
in memory make both reports pass. No raw report, historical verdict or checker
source was changed. Fix/replay the checker without paid inference before
considering another model test. [Audit](../notes/s1-completion-fixed-opus-ten-rfe-20261018.md).

Reviews occupy a 15m11s envelope and remain the longest phase. Ten ticket reviews
overlap, but the four roles within each ticket still run sequentially. Peak
reviewer transcript overlap is ten. Scope checks find no peer-ticket headings,
IDs or tool paths. The 43 denied reads recover through authorized inputs;
41 involve the assigned ticket's local/ alias and two other invalid paths.
These checks do not establish semantic accuracy. All final numeric decisions
approve (four 8/8, two 7/8, four 6/8), while 23 role reports recommend revise;
their dissent is retained under the user's numeric-only policy.

Usage: 854 captured/usage-bearing Opus calls, 33,214,640 accounted tokens,
no recorded API/rate errors. Recorded Opus API list equivalent $55.27; thinking
is included in output. The primary's ~1.2M-token prose summary omits cumulative
API usage and is unsuitable for cost accounting. Job duration is 65s longer
than the failed predecessor; differing model work prevents attributing the
whole-job change to the hook. Matched replay and the traced guard establish
the optimization directly.

Archive complete/final with 11,033 files / 17,094,202,740 bytes, no capture
errors; independent checksum verification passes and final receipts are
published. Reproducible read-only analysis is saved separately from the raw
archive. No paid retry/resume or new source deployment occurred during analysis.

### Checker format repair, verified without model calls

On the user's approval, repaired Breadboard's mechanical assessment checker,
versioned `role-assessment-v2`. Numbered Markdown findings contribute their
explanatory body rather than just a title. The reader excludes fenced examples
and stops at the next heading. Explicit architecture subjects (“Core
architecture is” / “Architecture is”) are removed before matching the existing
completed verdicts. That subject is not counted as explanatory content.
Status, TODO/placeholder, empty/quoted/code-only findings, wrong-ticket sections,
ambiguous judgments, conflicting decisions and receiving-channel/history
substitutions remain negative cases. S1 and its numeric-only policy are unchanged.

The actual latest before/after receiving-channel replay moves 38/40 to 40/40,
changing exactly RHAISTRAT-5 feasibility and RHAISTRAT-6 architecture. Input
hashes match before/after, and the historical original gate/overall FAIL remain
beside the new delivery result. Five other historical captures replay too:
mixed-state Opus 36/36; completed S2 12/12; failed S1 stream 0/12, quota-stopped
S2 7/12 and completed S1 with lost handoffs 2/12 remain failed. This evaluates
delivery only, not content accuracy or a new pipeline trial.

Six new authored regression methods demonstrate the failures before the patch
and pass afterward. Focused tests: 27 pass. Full benchmark suite with offline
Markov simulations enabled: 104 pass, one optional emulator integration skip.
Compilation and diff checks pass. Existing repeated-judgment normalization is
also confirmed against the mixed-state report; that previously fixed logic
predates this patch, and its stale open ledger status is corrected.

Sixteen evidence files / 1,769,863 bytes independently verify under the latest
campaign's separate `analysis/checker-format-fix-20261018/`, including old/new
checker sources, test sources/logs and immutable before/after/control replays.
No inference tokens, Jira changes, source-pin edits or deployment. Changes are
local/uncommitted; a future benchmark must pin a published revision containing
the fix. [Completed task](../tasks/done/strat-review-checker-format-compatibility.md).

### Current-source mixed batch: ten actual acquisitions

The user authorized one mixed-state Opus batch on repaired S1. Published
Breadboard 9232633 includes checker v2 and a new s1-pr85-mixed-ten-opus tier
pinned to 6ed858b. Historical tiers/pins and failed results are unchanged.
The new fixture has 29 issues, eighteen distinct RFE subjects, four fresh,
four refinement and two verified review-only work items. Controls are seeded
between the prior-push pair and the other eight work items, so lexical discovery
selects all ten actionable RFEs. The human-only control is excluded by the first
cap and exercised as a late skip during the model-free repeat, which must
acquire nothing and exit 78. No gate or concurrency semantics change.

106 offline tests pass, two optional isolated-emulator tests skipped; directory,
exact-payload Markov simulation, staged secret scan and diff checks pass.
The optional local emulator process did not start while waiting for sandbox
approval. On the user's path clarification, real integration preflight used
the normal Breadboard seed and pre-inference guard. All 81 imported files
match the published source; archive/routing/idle/schedule preflight passes.

Submitted once through markovd-cli at 17:30:29 UTC on October 18:
markov-run-bfc0b766. Actual seed/read-back confirms all eighteen distinct
summaries/descriptions. Live guard passes ten acquisitions and 4/4/2 resume
points with two verified prior pushes. Direct process inspection confirms clean
6ed858b, Opus for all aliases, cap ten, native failure monitoring and the
qualified image. Successful requests use the intended Vertex service account.
Observer 878799 will archive and verify terminal evidence; it cannot resubmit.
Data root is pr85-mixed-ten-vertex-opus-20261018 under the private hardening
run-data directory. Outcome/repeat/terminal archive pending; no automatic paid retry.
[Completed run task](../tasks/done/s1-pr85-mixed-ten-opus.md).

Terminal result: markov-run-bfc0b766 completed at 18:01:28 UTC, model job
30m07s. Pinned evaluation PASS with no failed checks, ten completed strategies
and forty accepted role assessments. Four new clones, eight refinement/push
paths and two review-only preservation paths meet the mixed checks. Controls
stay unchanged and all claims release. The model-free repeat passes with no
acquisitions, no duplicate effects, exit 78 and zero model calls. Usage records
855 Opus calls / 32,138,772 accounted tokens, no recorded API/rate errors.
Archive collection ran 18:01:36–18:19:40 UTC. The final manifest is complete;
independent checksum verification passes with no problems, and verified receipts
were published at 18:19:53 UTC. Source match and benchmark PASS are recorded in
launch-context/result.json. No paid retry/resume.

## 2026-10-18: migration verdict and why the testing mattered

### Verdict and remaining limits

The migration is functionally successful for the tested configuration. The
recommendation is to proceed with the hardened Workflow implementation for
strat-creator and qualify it in the actual Fullsend deployment before broad
rollout. This is a recommendation, not a production deployment approval.

The fresh ten-RFE run completed natively in 38m26s with all forty reports
delivered and preserved. Its original benchmark FAIL remains recorded; the
two remaining checker false negatives were subsequently repaired and verified
by immutable replay. The current-source mixed ten-RFE run is a clean PASS in
30m07s, covering four fresh, four refinement and two review-only paths. Controls,
lock cleanup and the model-free repeat pass, with no duplicate effects.

Reliability comes from explicit assignments, persisted assessments, provenance,
completion receipts, ordinary Python validators/hooks and recovery/freshness
rules alongside Workflow scheduling. Deterministic JavaScript does not make
the agents beneath it deterministic. Those checks are part of the design and
must remain in the production integration.

These results support this implementation; they do not establish a general
cost, simplicity or reliability advantage over scripted orchestration. The
benchmarks used Kubernetes jobs through Breadboard and Markovd, not the Fullsend
runner/OpenShell boundary. Independent strategy-quality judging and statistical
failure-rate measurement remain unperformed. Numeric scores remain the user's
sole approval gate; preserved reviewer requests for revision are informational,
so final approval does not imply unanimous reviewer agreement.

External source/baseline protection remains an [open follow-up](../bugs/open/s1-primary-edits-source-and-freshness-after-failure.md).
Overlapping jobs also need stronger ownership than [Jira labels](../bugs/open/strat-jira-label-locks-not-atomic.md)
to establish atomic distributed claims. A clean batch does not close either
qualification gap. Reviewer fan-out remains deferred by the user.

### Cumulative testing cost

The [deduplicated accounting](../notes/strat-workflow-total-token-usage-20261018.md)
records 478,893,465 recoverable reported tokens, plus about 10 million from a
rounded early smoke summary: approximately **489 million tokens** overall.
The original comparisons account for about 187.5 million; subsequent S1
hardening/integration accounts for 301.4 million.

With GLM treated as free, standard global API list-price equivalent is about
**$485**, with a calculated range of $481.26–$487.44. Opus contributes $475.02,
Haiku $6.24–$12.42 and GLM $0. Hardening contributes $345.51; original benchmarks
contribute $135.75–$141.93. Failed/stopped/replacement runs are included;
duplicate captures and synthetic model responses are excluded.

These are usage equivalents, not reconciled invoice charges. Development-chat
tokens, infrastructure/labor costs and usage missing from captures are excluded.
The Haiku range reflects missing per-request context tiers in old summaries;
most recorded tokens are cached input. No cost-per-defect or financial return
on testing has been measured.

### Which testing was necessary, and which expense was avoidable

Most testing was necessary to establish that the pipeline performed the work
it claimed to perform. A successful CLI exit or a review comment in Jira could
conceal a lost assessment. We needed to inspect what the receiving agent
actually obtained and what persisted, not just whether agents ran.

- Single-target and batch tests exposed whole-batch reviewing despite a
  single-ticket assignment. One-ticket tests cannot expose that interference.
- Full-size tests exposed hooks that passed for one ticket but exceeded their
  timeout at ten. Testing only the average workload would miss the supported
  maximum's failure.
- Mixed-state tests covered refinement, verified review-only continuation,
  untouched controls and exclusion of completed work. Fresh-only runs could
  not answer these questions.
- Model-specific integration mattered: GLM accepted a schema that Anthropic
  rejected. A GLM pass could not qualify that boundary for Opus.
- Controlled failure/recovery tests checked safe reuse and side effects without
  paying for whole model batches. Native controls and checker replays often
  required zero provider calls.

Some paid expense could have been avoided with earlier deterministic checks
and stronger preparation. Relay failures, quota interruptions, incorrect model
selection and overly narrow checker rules consumed time without directly
answering the architectural comparison. Full-size local hook profiling could
have exposed scaling defects before paid integration runs. The final checker
repair demonstrated the better sequence: replay saved reports, repair the
parser, retain genuine negative cases, then use a live run for a new integration
question. Those operational incidents still produced useful findings; their
entire cost is not an unavoidable cost of evaluating a Workflow.

The campaign combined comparison, debugging, infrastructure repair and
integration qualification. Changed revisions and fixtures cannot be pooled as
independent repetitions of one stable implementation to claim a failure rate.
The conclusion is sufficient functional evidence to stop repeating ordinary
clean batches on this revision. Further paid testing should answer a specific
remaining question; prioritize model-free fault/replay checks, actual Fullsend
integration and separately scoped content judging. This recommendation does not
authorize another paid run.

### Consequences of shipping without the tests and repairs

The most serious risk was false confidence: a run could publish a strategy as
reviewed while the intended specialist assessments had not reached the final
review. Downstream readers would see ordinary documents, comments and approval
labels without knowing the process behind them was incomplete.

| Demonstrated problem | Likely production consequence |
| --- | --- |
| Specialist reports lost at the Skill return | Missing findings; coordinator-written replacement sections could be mistaken for delivered specialist assessments |
| Reviewers cover the batch despite one assigned target | Individual strategies receive reasoning insufficiently specific to their own requirements |
| Malformed refinement receipt disagrees with saved progress | Ready work can be excluded from review and require manual reconciliation |
| Anthropic rejects the Workflow schemas | Opus jobs fail when they reach the affected stages |
| Final completion hook times out at ten tickets | Completed business work is reported as failed, making safe retry decisions difficult |
| Missing recovery/freshness safeguards | Retries risk duplicate side effects or reuse of results that no longer match their inputs |
| Primary edits Workflow source/baselines and relaunches | Execution departs from reviewed code, spends more tokens and can publish side effects before a trusted final check refuses it |

Visible failures would create stalled work and operator investigation. Silent
failures would be harder to discover because the expected Jira artifacts
could already exist. In one observed ten-ticket run, all substantive work
finished before the final hook failed; artifact presence alone could not tell
an operator whether restarting was safe.

The mechanisms were observed in tests or controlled fault cases. Their
production consequences are engineering inferences, not observed production
incidents or measured occurrence rates. Some defects belonged to shared Skills
and helpers and predated the migration. The original implementation would have
inherited them. Testing moved discovery into a controlled environment and
exposed failure modes that the original success checks themselves missed.

## Authorized Opus 5.5 mixed-state comparison, 2026-10-18

The user requests one repeat of the passing ten-acquisition mixed-state batch
with claude-opus-5-5. This asks a new model-compatibility question, while holding
candidate 6ed858b, fixture, high effort, concurrency ten and single iteration
constant. Native capture, failure monitoring, numeric-only approval and the
model-free repeat remain unchanged. No automatic paid retry or model fallback.

Published benchmark 0b89021 adds variant opus55 and a separate restricted tier;
prior model mappings and historical tiers stay intact. The 109-test offline
suite passes with two optional skips, exact-payload Markov simulation passes,
and all 81 imported files match. The existing Vertex upstream now permits the
exact model; a one-output-token availability probe returns HTTP 200 through the
same relay credentials the jobs use. Archive/idle/schedule preflight precedes
the single CLI submission. [Completed run task](../tasks/done/s1-pr85-mixed-ten-opus55.md).

Run markov-run-296d9e2e completed: native Workflow 23m19s, model job 25m18s,
all pipeline exits zero. All ten mixed-state paths and model-free repeat pass.
Independent audit confirms forty final reports delivered and preserved, with
no mechanical scope problems; there were two additional testability launches.
Pinned benchmark remains FAIL solely because a 6,119-character scope judgment
begins "The capability is right-sized" and the checker expects "right-sized"
at the field's start. An in-memory wording diagnostic passes; no source/report
or historical result has been changed. [Parser finding, subsequently fixed](../bugs/fixed/strat-review-gate-scope-subject-false-negative.md).

All 791 requests use Opus 5.5; accounted usage 37,261,081 tokens, CLI list-price
equivalent $42.80, no recorded API/rate errors. Compared with the preceding
same-fixture Opus 4.6 observation, runtime is about 16% shorter and equivalent
cost about 17% lower. Numeric decisions are five approve/five revise versus
nine approve/one revise, without an independent accuracy judgment. Same S1
script, Claude 2.1.296 and image are verified from retained runtime evidence;
the late live process inspection missed the completed primary. Archive is now
complete/final and independently verified: 13,930 files / 18.85 GB, no capture
errors, receipts published. All 791 model responses uniquely match successful
Vertex service-account telemetry on the intended provider. No checker fix or
paid retry occurred during the run/audit. [Analysis](../notes/s1-opus55-mixed-ten-20261018.md).

### Scope-checker repair, no inference

The user requested this fix before considering revision-rate differences.
role-assessment-v3 accepts a bounded capability/scope subject before the existing
canonical judgment. It does not count the subject as rationale or search the
whole report for a verdict. Unfinished, negated, ambiguous/conflicting,
wrong-target, error and invalid-receipt controls remain negative.

Unchanged Opus 5.5 receiving-channel replay moves 39/40 to **40/40**, changing
only RHAISTRAT-1 scope. Input hashes, report bytes, original gate and overall
FAIL are preserved. Seven prior captures retain their v2 results, including
genuine failed/lost-handoff cases. Five regression methods reproduce the defect;
32 focused checks pass, and full suite is 112 passed / two optional skips.

Published Breadboard d3a8a8f contains only checker/tests/README changes. All 81
Markovd-imported files match the pushed revision. The model-free replay archive
independently verifies: 27 files / 2,649,699 bytes, complete/final, no problems.
No model calls, Jira changes, S1 changes, paid rerun or image rebuild. Historical
pins/verdicts remain unchanged; future benchmarks can use the published fix.
Revision-rate analysis is still deferred. [Completed repair](../tasks/done/strat-review-scope-subject-checker.md).

## Saved-content comparison: Opus 4.6 and 5.5

The user requested judging the refined strategies after the checker repair.
One assistant pass with producer labels masked preferred 5.5 in all eight
new-output pairs: four fresh/create/refine and four identical-draft refinements.
RFEs/comments match apart from terminal whitespace, initial drafts match
exactly, and all 321 frozen reference files match. Preferences/criterion ratings
were frozen before labels and pipeline scores were revealed.

Concrete advantages include Standard-mode canary prerequisites, shared-artifact
and cache-deletion safety, Kueue borrowing, explicit archive freshness and
authorization, and provider-specific export provenance. The two unchanged
review-only controls were excluded from the output tally. Their pipeline scores
still decrease (6 to 4 and 4 to 3 of eight), showing that the lower approval
count cannot be attributed solely to worse generated content.

Important gaps remain in 5.5: inferred credential adoption can still produce
false readiness; CronJob delay/skip semantics are unsettled; destructive
cross-service races remain; database transactions are overstated as isolation;
queue-position causality and canary metrics access need correction. No gate,
prompt, S1 source or original benchmark verdict changed. These are synthetic
fixture content findings, not new defects in relay credential management.

This is an exploratory single-judge assessment of one batch pair, not calibrated
accuracy or eight independent model trials. No new pipeline/provider inference
or external judge run; separate provider cost $0, excluding this Codex
conversation usage. [Comparison, evidence and limits](../notes/strat-content-opus46-vs55-20261018.md).

## Revision-decision investigation

Saved evidence reconciles all 20 assessor reports and published decisions;
parser and composer agree on all 81 score vectors. Four approval flips explain
the move from one to five revise outcomes. Most concerns are substantive; the
queue strategy's scope penalty remains debatable. Scope/architecture account
for ten of twelve fewer score points. Unchanged controls independently show
reviewing behavior/variation. Numeric-only approval remains unchanged.

The useful follow-up is readiness calibration: distinguish sourced requirements,
unresolved owner-bound discovery and implementation blockers without inventing
targets or treating required cross-component work as optional scope. No blind
automatic rewrite loop is indicated.

A separate existing report-format bug explains both extra testability calls:
prose-bearing Recommendation fields fail capture, then the parent diagnoses
missing files and regenerates. It is not the scope checker, five numeric revise
decisions or strategy rewriting. Original/replacement reports preserved; fix
remains pending. [Full findings and proposed next step](../notes/strat-opus55-revision-analysis-20261018.md).

## Native Fullsend and OpenShell qualification

The user authorized one single-RFE Opus 4.6 smoke through the copied GitLab CI
branch, rather than the Markov/Breadboard job path. RHAIRFE-19 is a new,
distinct workbench-storage-expansion RFE; existing Jira records are preserved.
Candidate `6ed858b`, benchmark context `7d61f09`, high effort and cap ten remain
pinned. Released Fullsend launches its stock Claude agent, which must launch
the Workflow; the relay key stays in the OpenShell provider.

Zero-inference setup failures found gaps the model-free connection probe did
not exercise: optional Fullsend CLI debug syntax, broken aliases in the
default cone sparse checkout, certificate-export ordering, and the compiled
Claude executable identity in the provider allowlist. Host-clone symlinks also
exposed an evidence-loss path in the redactor. These are copied-adapter/context
integration fixes; Workflow source is unchanged. Nineteen model-free checks
pass. Preserve the known native-artifact gap in 2097 explicitly.

2099 reached Claude but OpenShell blocked every request before the relay:
zero tokens and $0, no strategy output, correct validation failure, no host
publication, owned claim released, complete native archive verified. Its API
and syscall captures provide the exact denied executable. One Fullsend
validation iteration still permits multiple native SDK transport retries;
those controls govern different layers.

The corrected adapter `fdc770c1` **passes single-ticket pipeline 2100/job 4068
in 26m05s**. RHAIRFE-19 produces RHAISTRAT-16, approval, all four role reports
and a verified native business receipt. Host validation/report publication,
downstream dashboard 2101, owned-lock release and gateway cleanup all pass.
Opus 4.6 requests use the intended managed Vertex relay account. The complete
private archive and a separate checksum verification pass: 5,535 files /
910.12 MB, including native sessions, 218 API capture files and syscall traces.
This qualifies one real Fullsend/OpenShell integration smoke; prior benchmark
verdicts and source pins are unchanged. [Run, repairs and evidence](../tasks/done/fullsend-claude-workflow-opus-single-smoke.md).

Two portable fixes remain for the feature branch: default context fetching must
avoid broken sparse aliases, and host preflight must check host dependencies
while sandbox hooks enforce the Claude version. Local relay/provider settings,
certificates and evidence tooling remain deployment configuration.
[Source portability follow-up](../bugs/open/strat-creator-default-fullsend-portability.md).

### Lessons from the GitLab / Fullsend smoke

- **The native integration works for one RFE.** All 120 relay requests bearing
  `gitlab-job-4068` completed with HTTP 200, model `claude-opus-4-6`, and managed
  upstream `vertex-strat-evals`. The unchanged Workflow delivered the strategy
  and four role reports, then passed native validation and publication.
- **Preflight must exercise the real execution boundary.** Python model
  discovery passed while Claude's compiled leaf executable was blocked. Agent
  registration also did not catch optional debug-flag parsing in the actual
  run command. Host and sandbox have separate runtimes, dependencies and trust
  stores. Test the exact launch and calling executable before buying inference.
- **Reference data is an execution input.** Sparse checkout left aliases to
  missing releases, so freshness correctly stopped preparation. Use an explicit
  immutable subset and retain its source identity; preserve the strict check.
- **Failure handling was exercised, not merely specified.** Failed inference
  produced a failed job, missing-result validation, skipped publication and
  released ownership. Keep receipt validation, host publication and cleanup
  independent from the agent's completion claim. This is observed behavior for
  these failures, not proof of recovery from a hard kill.
- **Retry controls belong to different layers.** One Fullsend iteration still
  allowed about three minutes of native SDK connection retries. The blocked
  attempts used zero tokens. Interpret iteration, network retry and job timeout
  settings separately when estimating cost and delay.
- **Evidence collection needs its own acceptance checks.** The original
  redactor dropped early artifacts on source symlinks. Recording links as data
  preserves evidence without following targets; absent required artifacts now
  prevent a complete-archive claim. Native OpenShell logs named the exact
  rejected executable, which the top-level connection error did not explain.
- **CI time includes substantial work outside Claude.** The successful job's
  26m05s comprises about 4m20s before the agent, 19m56s of native agent execution,
  and 1m49s afterward. The setup includes image acquisition/building. This one
  fixture does not establish a speed difference from the Markov runs.

The result qualifies a single-ticket Fullsend/OpenShell path with the local
adapter. Ten-ticket mixed-state, resume and interruption behavior still need
qualification on that path. The earlier Markov results remain evidence for
their original execution environment. No further paid run is implied here.

### Existing SME revision contract audited, 2026-10-19

SME-driven reprocessing already exists in upstream main (`b396172`, fetched)
and the supplied GitLab pipeline (`fd36b15`). The documented human loop is
pull, edit the strategy's Staff Engineer / SME Input, refine/review locally,
then `/strategy-push`. Push publishes the changes and removes the current
`needs-attention` or `rubric-pass` label so a later eligible batch imports,
refines and reviews the existing strategy. Local mode deliberately bypasses
pipeline review-label gates while preserving human input. A Jira description
edit alone does not reopen the ticket. Earlier characterization of all SME
reprocessing as missing was too broad.

The existing `strat-dashboard-sme-loop-test` ran successfully as
`markov-run-bb4af08c` on July 31: initial refinement and two SME revisions,
expected counts 1/2/3. Its continuation explicitly clears review labels and
prompts the agent to synchronize the Jira SME section. This proves that
assisted revision flow on the historical fork, not automatic edit-triggered
selection or the new Fullsend runtime. The recent mixed-state fixture seeded
a human-cleared state; it did not exercise actual SME feedback resubmission.

S1 `6ed858b` preserves the human pull/push/refine skills. An eligible new job
imports updated SME input and establishes a new freshness baseline; an older
run cannot publish against changed inputs. Preserve a separate parity
question: GitLab manual `reprocess-strat` accepts approved post-CI strategies
and pulls in local mode, whereas S1 resume skips a still-approved strategy.
The human resubmission flow removes that gate first. Do not equate the two
entry points or implement an edit watcher merely to reproduce the human loop.

Thirty-six model-free checks pass across current-main helpers, the demo
contract, S1 freshness and temporary isolated edit/reopen probes. No source
changes, paid runs or shared resets. [Contract, evidence and qualification
limits](../notes/strat-sme-revision-flow-20261019.md).

### SME local-to-native-CI qualification in progress, 2026-10-19

The user authorized the connected SME test on the existing native smoke's
RHAIRFE-19 / RHAISTRAT-16. All 35 Jira issues are preserved. Initial source is
still clean 6ed858b; adapter fdc770c1. Local helper/scope tests pass 114 cases,
four additional local-hook/composition probes pass, and all 19 adapter checks
pass with the released Fullsend binary. The isolated human workspace uses
the qualified Claude 2.1.296 rather than changing the host's 2.1.300 default.

Actual pull passes and leaves Jira unchanged. A new SME directive changes the
PVC PATCH API design, rejects a custom backend state field and adds retry/UID
acceptance cases. This is a content-compliance check, beyond retaining a marker.

The first local refinement fails on transport before writing its revised body.
HTTP 200 is not evidence of a completed stream: the host Go ingress proxy's
absolute 120s write deadline repeatedly cancels the requests. Native retry
recovery lasts 38m04s and eventually returns an API error, yet forked Skill
CLI status is success / exit 0. Independent content checks reject the result;
Jira and tracked source are unchanged. Local commands need artifact/error
validation as well as exit status. [CLI status defect](../bugs/open/claude-local-forked-skill-transport-error-exit-zero.md).

The proxy issue is reproduced with a mock upstream and repaired without
changing S1: only dedicated inference virtual hosts lose their absolute write
and response-header deadlines. HTTP/HTTPS/HTTP2, long nonstream, ordinary
console deadline and cancellation tests pass with Go race detection. Both
replicas run repaired image 6f997256; an actual model response now completes
beyond the former 120s limit. [Transport repair](../bugs/fixed/ingress-proxy-model-response-write-deadline.md).

The failed attempt's data is independently checksum-verified in a separate
private archive. An earlier symlink-verification failure remains preserved;
new captures record native links as metadata. Old ingress replica logs were
not collected before rollout and are explicitly unavailable. Subsequent
captures now include all proxy replicas.

A single explicit continuation started at 17:00:30 UTC with identical SME
input, source, architecture and Opus 4.6 settings. Local refinement/review,
human publication, normal CI batch rediscovery, sign-off and unchanged repeat
are not yet qualified. No second CI batch or replacement ticket was seeded.
[Task history and evidence](../tasks/done/strat-sme-local-to-fullsend-validation.md).

The transport-fixed local attempt then exposes a harness setup mistake:
loading the editable checkout itself with --plugin-dir makes its local/
artifacts sensitive plugin assets to native Edit. The test is stopped without
applying model-generated candidate text manually. Four corrected native
Read/Edit probes against a localhost mock establish the boundary in ordinary
and forked calls: inline-root edits are denied; a separate plugin installation
permits the working checkout's artifacts, even with its dormant manifest and
project skills still present. These probes are synthetic and use zero upstream
tokens. This is not a strategy-content or S1 business-logic defect.

A source-identical separate plugin is installed for the human test. One
explicit refinement starts 17:18:40 UTC; current stage is
refine-installed-plugin. Existing failed and stopped evidence is retained;
the stopped-attempt/probe archive independently records complete and verifies
checksums. The human review guide should document the qualified CLI and plugin
setup: [documentation gap, now fixed](../bugs/fixed/strat-human-review-guide-runtime-and-plugin-setup.md).

### SME connected flow: results, 2026-10-19

Actual local pull/edit/refine/review/push passes on RHAIRFE-19 / RHAISTRAT-16:
human sections preserved byte for byte, all Jira unchanged until push, and
push reopens the old approval gate. A separate clean plugin installation fixes
the inline-plugin test setup. The human guide now documents that setup and the
qualified runtime/dependencies, with local publication still pending.

Normal default-JQL CI pipeline 2102/job 4071 passes in 29m06s through GitLab
emulator, Kubernetes Runner, job-owned Podman, Fullsend and OpenShell. It imports
the full SME section, refines the same strategy and captures all four distinct
role reports with matching hashes and caller/run attribution. Native completion
receipt and host business validation pass. All 128 CI requests complete on the
intended Opus 4.6 Vertex account. Dashboard pipeline 2103 also passes. No special
SME-sync prompt, manual label edit, reset or duplicate strategy is used.

The original source does **not** pass the entire human round trip: post-CI
pull into the existing workspace appends a second document. The body-preserving
frontmatter helper was followed by an append. Three model-free regressions
reproduce it. The local fix builds a fresh validated file and replaces the old
one after successful writing. All 26 pull tests and 1,092 required suite checks
pass (five conditional dispatch checks skip for missing CLI on test PATH).
Live helper refresh then passes without inference or Jira writes. The paid
slash-command failure is preserved; no additional paid pull or CI run is used
to qualify the repair. [Pull defect, now published](../bugs/fixed/strat-pull-appends-existing-local-body.md).

Actual human sign-off displays the summary and waits for confirmation; after
confirmation in the same CLI session it publishes, attaches the review, adds
human-sign-off and removes DRAFT. Canonical ADF read-back proves the complete
latest CI body and SME section were published once. The source business fields,
link identity and controls are unchanged. A checker initially confused the
linked strategy's updated embedded title with an RFE mutation; the retained
false-negative is corrected by checking relationship identity separately.
All 35 issues remain present. Final normal host preparation exits 78, acquires
nothing and leaves Jira unchanged with zero inference. The test ticket is no
longer selected; the existing human-signed-off control is also skipped.

SME directions change actual design content, not just a marker. Quality limits
remain: requested route/state acceptance tests are not explicit enough; an
unsupported polling target survives; a quota example mistakes reaching 50Gi for
exceeding it. CI scores 8/8 while preserving feasibility/testability requests
for revision. This honors the user's numeric-only approval policy, and shows
why flow qualification and independent content-quality judging are different
tests. No new paid judge call is used.

[Full results and evidence](../notes/strat-sme-local-fullsend-validation-20261019.md)
preserve failed/stopped attempts and qualification boundaries. The deployed
proxy repair is separate from S1. At test completion the human guide/pull repair
were local; the user then authorized publication. Signed-off commit 1bcb8f4 is
pushed to the feature branch, verified by remote read-back, and the checkout is
clean. Full pre-push make test passes 1,092 tests with six conditional skips.
No new paid run. The two previously recorded default bootstrap fixes and native CLI
false-success defect remain follow-up work.
