# Native Workflow production hardening

Created 2026-10-13 from the completed strategy benchmarks and Claude Code
2.1.296 controls. Fullsend maintainers rejected custom entrypoints, so the
production work now targets S1. The earlier S1/S2 comparison remains historical
evidence; S2 is not a production candidate for this plan.

## Working rules

- Work through the nine items below in priority order, starting with report
  delivery. Keep repairs separately identifiable and review results before
  moving to the next item.
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
| 6 | CLI, Workflow and business completion disagree | Final outcome checks required results and persistent state, including null/failed branches and notification failures | [Outcome, current](../tasks/current/s1-hardening-06-outcome.md) |
| 7 | Crash/restart can repeat side effects | Publication and other externally visible writes are idempotent or reconciled before repetition | [Recovery](../tasks/pending/s1-hardening-07-recovery.md) |
| 8 | Replay can reuse stale results | Reuse checks relevant input/source identity; changed inputs invalidate or explicitly reject cached work | [Freshness](../tasks/pending/s1-hardening-08-freshness.md) |
| 9 | Budget/deadline boundaries need application policy | Defined limits, overshoot reporting and safe handling of quota exhaustion, timeout and cancellation | [Limits](../tasks/pending/s1-hardening-09-limits.md) |

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

## Evidence

- [Maintained benchmark analysis](../../var/benchmarks/strat-workflow/analysis.md)
- [Benchmark plan and run inventory](strat-workflow-eval-plan.md)
- [Reviewer-return bug](../bugs/open/strat-workflow-reviewer-output-loss.md)
- [Schema inheritance and verified remedy](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-specialist-handoff.md)
- [Runtime controls](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-operations.md)

## Status

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
item 6 is current; items 7–9 remain pending. The diagnostic's revise/needs_attention=false result is
tracked for items 4/6 and does not change the scope result. User authorized S1 repair work and
single-execution GLM iterative tests; the earlier requests to keep benchmark
implementations unchanged and ask before each exploratory run do not prevent
this newly requested hardening work. Historical branches and findings remain intact.
