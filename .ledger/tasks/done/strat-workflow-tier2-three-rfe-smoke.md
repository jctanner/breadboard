# Task: Prepare the first tier 2 three-RFE smoke test

## Goal

Implement F1 using three distinct existing RFE templates, native batch entry
points, and batch-aware checks. Preserve tier 1 and both pinned designs.

## Acceptance criteria

- [x] Separate Haiku tier with exactly one selected design and one run.
- [x] Seed workbench exemptions, pipeline retention, and feature-store scheduling.
- [x] Check all RFEs and distinct strategies, reviews, verdicts, and locks.
- [x] Record reviewer return failures without patching the designs.
- [x] Validate locally, including tier 1 compatibility and guard failures.
- [x] Document settings and implementation evidence in the evaluation plan.

## Scope

Implement locally. Commit, push, sync, reset/seed Jira, and live model runs are
subsequent actions. The first authorized batch run will be S1; stop and
analyze it before requesting a separate S2 run.

## References

- [Evaluation plan](../../plans/strat-workflow-eval-plan.md)
- [Benchmark](../../../var/benchmarks/strat-workflow/README.md)

## Validation

2026-10-11: 12 offline tests passed with `/tmp/strat-tier2-markov`, built
from current component source because the checkout's existing binary is
stale. Actual workflow validation, Python compile, shell syntax, and diff
checks passed. Read-only replay detects historical S1 lost reviewer outputs
and passes S2's four returned reviews. Full evidence is in the plan above.
