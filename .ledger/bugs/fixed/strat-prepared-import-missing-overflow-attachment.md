# Prepared import accepts an overflow stub without its full attachment

Review 4355503644 on 0707b5b: pull_strategy expands overflow only when the named
strategy attachment exists. If the description still carries the overflow
notice but that attachment is absent, it writes the short stub as strategy
content. Prepared pipeline import should reject that incomplete source before
replacing any existing strategy file. Preserve standalone human pull behavior.

[Repair task](../../tasks/done/strat-pr85-import-recovery-fixes.md).

## Resolution

Prepared pulls reject the missing exact-filename full strategy attachment
before writing artifacts. Four regressions cover direct and CLI import paths,
with and without an existing task, and confirm prior workspace bytes survive.
Ninety related import/pull/freshness checks pass; full suite 1,275 pass/six skips.
Lint/types/diff pass. Published as signed-off fbbbc6e; exact PR #85 head verified
and component clean. No model call or live Jira/export mutation.
[Evidence and limits](../../notes/strat-pr85-import-recovery-20261023.md).
