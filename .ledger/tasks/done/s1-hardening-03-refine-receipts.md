# S1 hardening 3: reconcile refinement receipts and persisted readiness

Reject malformed or wrong-target receipts explicitly. Reconcile saved progress
before deciding whether an actually completed strategy is ready for review.
Do not accept arbitrary nested JSON as proof of the requested target.

## Acceptance

- [x] Assigned-key receipt schema rejects nested JSON and wrong targets.
- [x] Completion marks require valid current-run ownership and saved artifacts.
- [x] Fresh readiness reconciliation agrees with progress plus saved files.
- [x] Completed work survives a malformed/missing return without repetition.
- [x] Plausible receipts without completion and invented checkpoints cannot advance.
- [x] Offline/native fault controls and one focused GLM scenario pass.
- [x] Final system/job archive independently verifies before any reset.

## Status

Done on local `eval/s1-hardening`, candidate `30cf850`. Component suite:
886 passed, seven opt-in live checks skipped. Native forked-Skill controls
use zero provider calls. The one GLM two-ticket fixture scenario recovered
one injected receipt fault; both targets are ready with one refinement each.
Full-pipeline, content quality and Fullsend qualification remain separate.
[Evidence and limits](../../notes/s1-hardening-03-refine-receipts.md).
[Plan](../../plans/strat-workflow-s1-hardening.md).
