# S1 hardening 4: preserve findings, provenance and dissent

Define how final reviews incorporate each role's findings and unresolved
concerns. Require source attribution and explicit treatment of revision or
attention flags; earlier scorer material must not silently replace a report.

## Acceptance

- [x] Preserve all four actual delivered reports unchanged with role/target attribution.
- [x] Retain caller/child/tool identities, report hashes and independently verifiable sources.
- [x] Keep scorer assessment separate; pending specialist verdicts cannot borrow its verdict.
- [x] User policy: numeric scores remain the sole gate; reviewer dissent is informational and explicit.
- [x] Numeric rules unchanged across all 81 score combinations; attention flag agrees with numeric verdict.
- [x] Missing, substituted or changed sources prevent composed-review completion/host validation.
- [x] Native zero-provider controls and one GLM two-target authored fixture pass (8/8 reports).
- [x] Full private system/job archive independently verifies before any reset.

## Status

Done on local `eval/s1-hardening`, candidate `7cfcada`. Component suite:
906 passed, seven opt-in live checks skipped. The GLM case ran the real review
orchestrator, completed in 6m02s, and preserved eight authored reports with
their opposing findings and unchanged numeric decisions. No premium model,
Jira writes/resets or historical-pin change. Full generation/production
qualification and content accuracy remain separate.
[Evidence, policy and limits](../../notes/s1-hardening-04-review-composition.md).
[Plan](../../plans/strat-workflow-s1-hardening.md).

Observed during item 2: all three diagnostic GLM receiver verdicts say revise
while needs_attention=false. Scope delivery passes, business consistency does
not. [Recorded issue](../../bugs/open/strat-workflow-verdict-attention-disagree.md).
