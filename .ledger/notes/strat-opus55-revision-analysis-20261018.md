# Why Opus 5.5 asked for more revisions

The higher revision rate is mostly a content-readiness and scoring-calibration
question. There is no demonstrated verdict-arithmetic or workflow-completion
defect behind the five final revise decisions. A separate report-format defect
caused the two extra specialist calls.

## What the counts mean

| Result | Opus 4.6 | Opus 5.5 |
| --- | ---: | ---: |
| Final numeric approvals | 9/10 | 5/10 |
| Final numeric revisions | 1/10 | 5/10 |
| Specialist prose requests for revision | 28/40 | 39/40 |

The numeric assessor runs before the four prose reviewers. Its four scores,
each 0–2, determine the published decision: approve requires at least 6/8
and no zero. Prose recommendations are retained separately, as the user
requested. Thus 39 specialist requests do not mean 39 strategy rewrites,
39 workflow failures, or even 39 changes to the final gate.

The Workflow refines once for each of the eight relevant tickets, pushes,
scores and reviews, then records the decision. It does not loop through
refinement until all reviewers approve. A completed review with revise is a
valid business outcome requiring human attention. The two review-only controls
were intentionally not refined.

All 20 saved numeric-assessor reports reconcile with their hashes, parsed
scores, provenance and final decisions. The parser and composer also agree on
all 81 possible four-criterion vectors. No score-parsing or arithmetic repair
is indicated.

## Where the four additional revise decisions came from

| Strategy | Subject | 4.6 score | 5.5 score | Assessment |
| --- | --- | ---: | ---: | --- |
| RHAISTRAT-1 | Drift alerts, unchanged seeded control | 6 | 4 | A reasonable revision request. The draft does not identify the rule lifecycle owner, size the work or resolve monitoring prerequisites. The frozen TrustyAI reference describes REST-registered metrics and an asyncio scheduler, not a metric-request CR owner. |
| RHAISTRAT-15 | Canary rollback | 6 | 5 | Reasonable despite better generated content: actual serving-mode support, metrics and baseline retention remain prerequisites to prove. |
| RHAISTRAT-9 | Queue visibility | 7 | 5 | Mixed. Missing verification of priority-blocking reasons is real; penalizing required dashboard/CLI delivery and inherent team coordination as scope expansion is debatable. An architecture score of 2 coexists with valid feasibility/testability concerns. |
| RHAISTRAT-10 | Credential rotation | 6 | 5 | Reasonable: exact-revision adoption, derived Secret propagation, ownership and validation/activation binding remain unresolved. |

RHAISTRAT-2, the unchanged training-recovery control, already needed revision
under 4.6 (4/8); 5.5 gives it 3/8. The RFE explicitly excludes automatic retry
scheduling, while the seeded draft includes infrastructure retries and backoff.
It also omits several requested recovery and authorization contracts. That is
a real fixture-content problem, not a regression introduced by 5.5 generation.

Across the ten tickets, score sums fall from 64 to 52. Scope falls by five
points and architecture by five; feasibility falls by three, while testability
increases by one. Most of the numerical difference therefore comes from scope
and architecture, not a uniform reduction in every score.

The unchanged controls demonstrate reviewer behavior or variation independent
of new generated text. They do not establish that every 5.5 criticism is
correct, that all reviewers saw identical prior-review context, or that the
models have a measured, stable calibration difference.

## The rubric needs a clearer readiness standard

Refinement explicitly forbids invented performance targets and requires
unsourced targets to become PM/Engineering open questions. The assessor
penalizes missing numeric NFRs and unresolved critical-path questions. Those
instructions are not logically incompatible: they can intentionally require
human input before implementation approval. But the pipeline cannot produce
that missing input merely by rewriting a strategy.

The practical distinction is between a strategy that is useful for a discovery
spike and one ready for implementation. A bounded spike with an owner,
deliverable and stop/go criterion is useful engineering work. It is not proof
that the dependency has already passed. The rubric should state how each
readiness level affects each numeric score. It should also distinguish
required cross-component delivery from optional independently shippable scope.

Keep the numeric-only gate and its threshold. Do not raise scores just to
restore the old approval rate, invent targets, or add a blind automatic
refine-until-green loop. First make missing inputs, genuine blockers and
optional improvements explicit. Calibrating the judge on the same saved
documents is a separate experiment; it needs no new pipeline generations.

## The two extra calls were a format/retry defect

Both first testability returns, for RHAISTRAT-12 and RHAISTRAT-2, contain a
field beginning `**Recommendation**: revise.` followed by a rationale and a
later standalone `**Recommendation**: revise`. They express the same apparent
decision, but the capture parser compares entire field values. A prose-bearing
value is outside its canonical enum, so no testability capture file is saved.
The parent sees that missing file at compose, inspects the parser, and reruns
the specialist. Replacement reports satisfy the contract, giving 42 launches
for 40 required reports. Neither strategy is rewritten by this recovery.

This is a remaining variant of the existing
[report-format regeneration bug](../bugs/open/strat-review-recommendation-format-causes-regeneration.md).
Exact repeated scalar verdicts were already fixed; prose on the same line
still fails. It is separate from the repaired scope-assessment checker.

The narrow next fix is to enforce the canonical recommendation contract before
the child returns, with a clear repair instruction, and make the parent stop
explicitly on an invalid receipt instead of diagnosing it through a missing
file and regenerating the review. Any decision to accept an additional bounded
format should preserve report bytes and still reject conflicts. Do not silently
take the last line as the answer. No such fix was implemented in this analysis.

## Evidence

Source candidate `6ed858b` is still clean. The analysis uses the original
`markov-run-bfc0b766` and `markov-run-296d9e2e` archives and the
[saved-content comparison](strat-content-opus46-vs55-20261018.md).
Private evidence:
`var/run-data/strat-workflow-hardening/revision-analysis-opus46-vs55-20261018/`.
It retains the reconciliation script, source/rubric snapshots, 20 scorer
reports, four original/replacement testability returns, hashes and results.

No new pipeline or provider inference, no gate/prompt changes, and no edits to
the archived runs. This Codex conversation's usage is outside the benchmark
meter. The causal review is observational, not a paid fixed-judge crossover.
