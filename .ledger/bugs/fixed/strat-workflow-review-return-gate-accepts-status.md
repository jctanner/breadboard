# Reviewer return gate accepts status messages and errors as reviews

## Summary

The original benchmark's `reviewer_outputs_returned` detector treated nonempty tool
result text as a returned review. It accepted a progress-only response
or error string without an actual assessment. Keep the captured results;
the repair distinguishes completed assessments from nonempty text and retains
the original gate outcome alongside historical replays.

## Evidence

S2 `markov-run-6bcb3c32`, final archive
`var/run-data/strat-workflow/markov-run-6bcb3c32/20261011T191550355513Z/`,
job `script-strategy-entrypoint-all-claude-opus-4-1011-181949-e387e8`.
`artifacts/eval-result.json` marks RHAISTRAT-1 architecture returned=true
with 170 result characters. Actual Skill result in
`api-dumps/7b43b84e-238e-466e-871e-cc1a5a23b8ec.request.json`, tool ID
`toolu_01GsR1JLaV6U7T9m1N9WydWr`, says only that four research agents
were launched and it will wait before assembling the architecture review.
It contains no assessment. Whether a later asynchronous path delivered
research or an assessment elsewhere is not established by this tool return.

Previously, S1 `markov-run-7845a7f1` architecture for RHAISTRAT-3 returned
a connection-error string that the same detector labeled returned=true;
see `strat-workflow-reviewer-output-loss.md`.

## Expected

Check for substantive reviewer output associated with the requested target
and completed role. Progress messages and errors must not satisfy delivery.
The existing scope-drift bug tracks target mismatch separately.

## Impact and status

Fixed in Breadboard's working tree on 2026-10-14, hardening item 5. The original
evaluation overstated specialist delivery. S2's original overall gate still
failed because strategy 3's reviews were never launched after the account
rate-limit abort; that original record remains unchanged.

`role-assessment-v1` now checks the assigned section, completed role judgment,
recommendation and explanatory content in the actual receiving tool result.
It rejects acknowledgements, progress/errors and incomplete scaffolding, records
skips separately and rejects conflicting histories. Historical replay corrects
the two reported false positives; completed real GLM/Opus reports pass.
Scope exclusivity, final incorporation and accuracy stay separate.

62 benchmark tests pass (six optional Markov checks skipped); nine independent
reference-checker tests pass. Six complete original captures verify, and the
new offline evidence capture verifies. No inference tokens spent, S1/S2 source
change, deployment or reset. Future jobs must use the updated Breadboard checker.
[Repair and private evidence](../../notes/s1-hardening-05-delivery-gate.md).
