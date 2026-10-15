# S1 hardening 9: budget and deadline proposal rejected

## Resolution

Closed 2026-10-14 at the user's direction: **rejected as not a bug**. No repair
implemented and no new model tests run. This is a rejected proposal, not a ninth
implemented fix.

Fullsend's existing per-iteration timeout applies to the Claude invocation,
whether it uses a Workflow or an ordinary agent. The local runner source exports
`FULLSEND_ITERATION_DEADLINE`, applies the timeout through the runtime, and
attempts to terminate remaining sandbox processes after timeout. This does not
establish a need for a separate Workflow budget system.

Run-wide spending caps and deadline-aware pacing are optional application
policies. Timeout, cancellation and quota-failure testing can qualify the
existing outcome/recovery repairs from items 6–8, but no additional S1 defect
was demonstrated here. A concrete future failure should be recorded separately.
Actual Fullsend/OpenShell deployment qualification remains outstanding.

The verified native budget overshoot and cancellation observations remain valid;
the rejected claim is that they require another Workflow-specific repair in this
plan.

## Original proposal

Define application-level limits and reporting for agent-boundary budget checks,
last-agent overshoot, quota exhaustion, workflow wait ceilings and cancellation.
Require explicit configured limits and safe recovery. Withdrawn from the repair
scope for the reasons above.

[Plan](../../plans/strat-workflow-s1-hardening.md).
[Fullsend timeout contract](../../../checkouts/fullsend-ai/fullsend/docs/cli/run.md#budget-and-deadline).
[Verified native controls](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-operations.md).
