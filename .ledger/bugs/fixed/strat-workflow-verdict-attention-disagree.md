# Bug: diagnostic review verdict and attention flag disagree

## Observed

The focused GLM scope job on 107e7af completed its native Workflow and delivered
12 correctly targeted reports. All three schema-bearing receiving agents returned
`recommendation: revise` with `needs_attention: false`, despite the diagnostic
prompt requiring attention for unresolved concerns. The shape-only S1 VERDICT
schema permits that combination. Successful runtime/schema completion does not
establish a consistent business outcome.

Job: `script-run-all-glm-5-3-1014-004354-220e59`, Claude Code 2.1.296,
exact hosted GLM, medium effort, 2026-10-14 UTC.

## Scope and expected behavior

This is observed in the diagnostic receivers, not a claim that production Jira
labels were written incorrectly: this test does not score, compose or publish.
A revision/rejection outcome requires an attention flag under the existing
numeric review policy. Add a deterministic cross-field check or derive that
flag from the declared decision policy, and cover unresolved role concerns.

## Follow-up

Track under hardening items [4](../../tasks/done/s1-hardening-04-review-composition.md)
and [6](../../tasks/done/s1-hardening-06-outcome.md). Preserve the passing scope
result while reporting these contradictions separately. No premium-model test
or additional paid run is needed to demonstrate the recorded result.

[Exact source, captures and archive](../../notes/s1-hardening-02-reviewer-scope.md).

2026-10-14: local repair `7cfcada` derives recommendation and needs_attention
from numeric scores and couples their allowed combinations in the actual
Workflow schema. Native controls reject the original revise/false combination;
one GLM composition case confirms both numeric decisions and saved progress.
The user explicitly retained numeric scores as the sole approval gate.
Approve/false with an individual specialist recommending revise is therefore
valid when that specialist's dissent is retained separately. The historical
diagnostic/pin remains unchanged; broader CLI/Workflow/business outcome
consistency was item 6. [Repair evidence](../../notes/s1-hardening-04-review-composition.md).

2026-10-14: item 6's focused repair is complete on `4c32d21`. Final deterministic
validation checks saved progress against the verified numeric decision and
composition, and its receipt is enforced at the structured boundary and trusted
host validation. Inconsistent progress/attention flags fail the offline fault
checks; one GLM final-step fixture validates both approve/false and revise/true.
941 component tests and three zero-provider native controls pass, with complete
private archives verified. Fixed on the local hardening branch; historical
diagnostic results remain unchanged. Fullsend/OpenShell and full-batch deployment
qualification are separate. [Final outcome evidence](../../notes/s1-hardening-06-final-outcome.md).
