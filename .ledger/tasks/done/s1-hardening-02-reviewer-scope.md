# S1 hardening 2: enforce per-strategy reviewer scope

## Goal

Each reviewer assesses only its assigned strategy while other distinct tickets
share the same workspace. Correct arguments alone did not enforce this earlier.

## Acceptance

- [x] Single target is mandatory; no whole-directory fallback.
- [x] Enforce input scope and report attribution, including shared architecture.
- [x] Offline controls block foreign ticket reads, broad searches and wrong reports.
- [x] Concurrent assignments use per-agent identity and handle transcript flush.
- [x] One GLM scenario delivers four scoped assessments per each of three tickets.
- [x] Captures verify effective hooks, tools, input scope and delivered targets.
- [x] Final private archive independently verifies before any reset.

## Status

Done: 12/12 scoped assessments in the GLM scenario on 107e7af; archive verified.
Final local candidate 4102e7a additionally supports Fullsend's frozen RFE inputs,
with 868 offline tests and a zero-provider native control. That final path
adjustment is not claimed as live-model tested. Fullsend execution and full
production batches remain separate. The verdict/attention inconsistency is
tracked under items 4/6. [Evidence](../../notes/s1-hardening-02-reviewer-scope.md).
[Plan](../../plans/strat-workflow-s1-hardening.md).
