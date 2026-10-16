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
[new parser false negative](../bugs/open/strat-review-gate-numbered-findings-false-negative.md).
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
