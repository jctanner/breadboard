# Bug: Agent-led validator required unanimous prose reviewers for approve

## Summary

`validate_result.py` (strat-creator fork `508ea33`) failed any `approve`
recommendation where a prose reviewer said something other than approve.
The strategy-review skill derives the recommendation from the numeric scores
only; prose reviewer verdicts are informational (SKILL.md Step 6, line 191).

## Reproduction

Pipeline 2077 / job 4038, strat-single on RHAIRFE-11: score 6/8 with no
zeros, so `approve` by `compute_verdict`. Prose reviewers: feasibility,
testability and architecture said revise; scope said approve. The
validator reported "approve recommended but a reviewer did not approve".

## Expected

Validation passes, and the post-script publishes.

## Actual

Validation failed and Fullsend skipped the post-script. Nothing was published
to `strat-pipeline-data` or Org Pulse, and the job failed. The Jira write
path had already completed correctly: RHAISTRAT-11 was cloned and linked,
the refined description pushed, labels `auto-created`, `auto-refined` and
`rubric-pass` applied, the review attached and the comment posted. Host
cleanup released RHAIRFE-11's lock. Because a check had already failed, the
validator's Jira readback never ran in CI; the same facts were checked by
hand.

## Fix

Fork `a2b888a`: check that the review's recommendation and needs_attention
follow from its scores using the skill's own `compute_verdict`
(`scripts/assess-strat/parse_results.py`), and that the total equals the sum
of the dimensions. Prose verdicts only need to be present. Tests cover a 6/8
approve with three dissenting reviewers, a recommendation that contradicts
its scores, an inconsistent total and missing scores. `make test`: 833
passed, 1 skipped.

## Impact

High for publication, none for Jira correctness. Run 4038's local artifacts
are gone, because the downloaded repository is deleted after the run.
RHAIRFE-11 is now processed (its STRAT has `rubric-pass`), so a rerun would
gate-skip it. Proving publication needs another fresh RFE.

## Related Tasks

- tasks/done/agent-led-strategy-single-ci.md
