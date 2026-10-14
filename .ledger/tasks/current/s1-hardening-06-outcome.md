# S1 hardening 6: reconcile final business and runtime outcome

Determine completion from required artifacts and workflow state/journal rather
than CLI exit or a single success event. Cover null/failed branches, cancellation,
stall exhaustion and failed notification after successfully completed work.

Acceptance: each controlled outcome has an accurate recorded result and does
not repeat completed work merely because notification failed.

Current, after item 5. [Plan](../../plans/strat-workflow-s1-hardening.md).

Implement a saved business-completion receipt checked against current progress,
artifacts and numeric review outcomes. Validate the receipt at the final
structured-output boundary and in the trusted host validator; failed/null final
outcomes must fail the Workflow. A read-only native-state/journal observer keeps
work completion distinct from CLI/notification status. Test faults without
provider calls, then one focused exact-GLM scenario if live boundary validation
is needed. No changes to Fullsend's entrypoint or broad replay/side-effect policy.

Observed during item 2: all three diagnostic GLM receiver verdicts say revise
while needs_attention=false. Scope delivery passes, business consistency does
not. [Recorded issue](../../bugs/open/strat-workflow-verdict-attention-disagree.md).
