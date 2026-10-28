# PR #85 follow-up input, recovery and publication defects

Diagnosed against 02dd13b on 2026-10-21. Malformed shared dry-run inputs can
select live mode. Owned cleanup depends on caller freshness and stops at the
first failed key. Pipeline imports can commit a task with an unresolved RFE
reference. History omits intentionally empty published runs. Concurrent summary
retries can push stale aggregates. An all-provisional Org Pulse dry run
indexes an empty list.

[Comment inventory and evidence](../../notes/strat-creator-pr85-review-20261021.md).
[Authorized repair task](../../tasks/done/strat-pr85-new-review-fixes-20261021.md).

Tests must use isolated Jira/Git fixtures and no model calls. Preserve foreign
owners, uncertain-write reconciliation, immutable run publications, numeric-only
approval and specialist dissent. Opt-in smoke integration is not a production
cutover. Human protected-path approval and anticipated security feedback remain
separate from these code repairs.

## Resolution

Fixed and published signed-off b3c10ec to existing PR #85. Strict mode parsing,
isolated per-key owned cleanup, fail-closed prepared reconstruction, sealed
empty history and skip-table compatibility, regenerate-after-sync summary
retries and empty-export handling have regression coverage. A real local Git
race verifies both publishers' runs survive and a replay leaves HEAD unchanged.

Full suite: 1,189 passed/six optional skips; focused suite 108 passed, plus
six extra format/heading variants in the full suite. Lint/types, shell syntax,
diff and staged secret checks pass. Published-source bootstrap and native
single/batch dependency locks pass. No strategy inference, live Jira change
or production cutover. Human/security approval and real OpenShell/CI smoke
remain separate qualification.
