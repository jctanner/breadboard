# Recovery can retain optional context absent from the new import

## Finding

[Review comment 4359883142](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4359883142)
on fbbbc6e reports that receipt-less recovery publishes files present in staging
but does not reconcile allowed optional paths absent from Jira. An older local
review or summary may survive, while the new completion inventory omits it.
`strategy-refine` reads an existing prior review as revision context.

Source inspection shows `prepare_import` publishes `sorted(files)` without
checking `allowed - files` against existing optional context. The managed-run
reproduction below confirms the reported behavior. A local repair is recorded
under Resolution.

## Reproduced

On clean fbbbc6e, a local Jira/Fullsend host-fixture probe runs actual managed
preparation and live freshness checks. SIGKILL after prior-review publication
leaves no task/receipt. After removing the remote attachment, the normal import
retry succeeds, writes an inventory omitting the review and preserves that stale
file. Repeated import claims already_imported, and record-create/freshness read
also pass. A clean no-review control leaves no review file. Two observation
checks pass in 6.71s; this is confirmation of the defect, not a correctness test.
No model call or component source change.
[Evidence and limits](../../notes/strat-stale-optional-reproduction-20261023.md).

## Proposed validation

Create pre-existing optional context with no corresponding remote input, run
incomplete-import recovery and check that it cannot silently feed refinement.
Reconcile known import-owned leftovers or stop when ownership is uncertain;
preserve refined task bytes and completed review work.

[Review follow-up](../../tasks/pending/strat-pr85-review-fbbbc6e.md).

## Resolution

Recovery now checks omitted optional context before publication. Ambiguous local
files remain intact and cause an explicit reconciliation error, with no new
completion record. v2 completion metadata prevents reuse of the pre-fix record
contract; reviews created after a completed v2 import remain supported.
The create Skill's exact empty-comments placeholder is validated against the
remote absence and retained byte-for-byte in the inventory.

Seven new regression cases and related checks: 65 pass. Full suite 1,282
pass/six optional skips; lint/types/diff pass. Seventeen-file archive passes
secret scan and hash readback. Published as signed-off 95a5c8f; exact PR #85
head verified and component clean. No model/live service action.
[Repair task](../../tasks/done/strat-import-optional-context-fix.md),
[implementation and evidence](../../notes/strat-import-optional-context-fix-20261023.md).
