# S1 hardening 6: reconcile final business and runtime outcome

Determine completion from required artifacts and workflow state/journal rather
than CLI exit or a single success event. Cover null/failed branches, cancellation,
stall exhaustion and failed notification after successfully completed work.

Acceptance: each controlled outcome has an accurate recorded result and does
not repeat completed work merely because notification failed.

Done, 2026-10-14. [Plan](../../plans/strat-workflow-s1-hardening.md).

Implement a saved business-completion receipt checked against current progress,
artifacts and numeric review outcomes. Validate the receipt at the final
structured-output boundary and in the trusted host validator; failed/null final
outcomes must fail the Workflow. A read-only native-state/journal observer keeps
work completion distinct from CLI/notification status. Test faults without
provider calls, then one focused exact-GLM scenario if live boundary validation
is needed. No changes to Fullsend's entrypoint or broad replay/side-effect policy.

Acceptance met on local `eval/s1-hardening` at `4c32d21`: verified business receipt,
enforced final structured boundary, invalid/null outcomes fail the Workflow,
trusted host validation, separate native/CLI/reporting observations and saved-work
recovery. 941 component tests pass (seven opt-in live checks skipped), three
zero-provider native controls pass, and one 57-second GLM final-step fixture
independently verifies. Its complete live archive and separate control archive
verify. Numeric policy and historical refs unchanged; Fullsend/OpenShell and
full-pipeline qualification remain separate. Items 7–9 are pending.
[Evidence and exact limits](../../notes/s1-hardening-06-final-outcome.md).

Published test-only follow-up `b6a228d` adjusts the opt-in headless test for the
completion preflight; 941 tests pass with seven opt-in checks skipped. The GLM-
tested implementation remains `4c32d21`; no additional model trial.

Observed during item 2: all three diagnostic GLM receiver verdicts say revise
while needs_attention=false. Scope delivery passes, business consistency does
not. [Recorded issue](../../bugs/fixed/strat-workflow-verdict-attention-disagree.md).
