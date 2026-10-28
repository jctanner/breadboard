# A partial import is mistaken for completion on retry

Review 4355503650 on 0707b5b: pull_strategy replaces the task before downloading
RFE comments, strategy comments and the prior review attachment. An error after
that replacement leaves the task in place. import_strategy then returns
already_imported, skipping missing context. Stage downloads, mark completion
only after publication, and preserve an existing task's refined text on retry.

[Repair task](../../tasks/done/strat-pr85-import-recovery-fixes.md).

## Resolution

Prepared import stages all downloads, publishes context files atomically and
writes a per-run completion record last. Task existence alone cannot skip
recovery. Retrying incomplete publication repairs context and preserves existing
refined task bytes; completed imports preserve later refinement/review output.
Bound-review recovery, missing completed context and mismatched run identity
stop instead of claiming success. Tests include three late read failures,
actual SIGKILL and interruption after task publication. Ninety related checks
and 1,275 full-suite tests pass (six optional skips); lint/types/diff pass.
Published as signed-off fbbbc6e; exact PR #85 head verified and component clean.
No model call or live Jira/export mutation.
[Evidence and limits](../../notes/strat-pr85-import-recovery-20261023.md).
