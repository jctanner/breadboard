# Address automated review follow-ups after 32700ec

## Scope

The user directed us to tend new automated PR #85 comments before a paid smoke.
Fetch the current discussion, compare new/updated findings with current source
and prior dispositions, reproduce relevant defects and implement bounded fixes.
Preserve the owner's stated scope, numeric-only approval gate, current Workflow
architecture and temporary Org Pulse certificate exception. Host-only Jira
publication and immutable sandbox redesign remain outside this work.

## Acceptance

- [x] Fetch complete current discussion and identify new/updated automated findings.
- [x] Check each finding against source and prior test evidence; record disposition.
- [x] Repair confirmed in-scope defects with appropriate offline regression checks.
- [x] Complete required repository checks and sanitized evidence archival.
- [x] Record exact source state and remaining limitations before any smoke run.

## Baseline

Clean feat/s1-workflow-hardening at 32700ec, pushed and PR head verified in
previous task. Prior suite 1,230 pass/six optional skips. No paid smoke, live
Jira/export mutation, review reply, thread resolution or deployment in scope.

## Result

Fetched 137 entries (17 regular/34 reviews/86 inline). Latest review5618750397
has three inline findings: one real attachment-history bug, the retained
owner-approved TLS exception, and authorization metadata. Other updated rollups
acknowledge earlier parser/SME/dry-run fixes; Qodo reports zero bugs.

Fixed the shared attachment reconciler to use the newest exact-filename copy,
matching readers and live review verification. Eight before-fix regressions
fail; after-fix focused group39 passes, covering strategy/review A→B→A
publication-to-pull, timestamp/ID ordering, repeated-current-byte idempotence,
and superseded pending/verified same-run writes. Generic journal unchanged.

Complete required suite:1,238 passed/six optional skips,365.65s. Lint/types/diff
pass. Thirteen-file archive plus included SHA manifest verified, configured
credential scan zero findings:
`var/run-data/20261022-strat-pr85-post327-review-followup/`.

[Full dispositions and implementation](../../notes/strat-pr85-post327-review-followup-20261022.md).
The three component files were committed with signoff as
`73c454bbc5c3a7f6907b3f2b3878c7a04d3477d6` and pushed to
`jctanner-fullsend-ai/strat-creator:feat/s1-workflow-hardening` on October 22.
Staged bytes match the tested archive; full staged credential scan has zero
findings. GitHub API confirms PR #85's exact head, and the component is clean.
Remote Python 3.11/3.12 tests, lint, Unicode and DCO checks pass.
The subsequent automated review has additional findings tracked in
[the next review task](../pending/strat-pr85-review-73c454b.md).
No paid smoke, live writes/export, governance approval, reviewer reply,
thread resolution or deployment was performed.
