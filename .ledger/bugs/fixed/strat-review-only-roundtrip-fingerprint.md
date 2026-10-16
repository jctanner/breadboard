# Review-only import proof is sensitive to Jira Markdown round trips

Feature head f5691f7 compares the imported strategy() fingerprint to the earlier
local pushed strategy fingerprint. Two simple verified imports passed in mixed
Opus run markov-run-5d3327ed, so review-only recovery does not universally fail.
However, an independent model-free probe with a strategy containing HTML
comments and a list gains six blank lines through markdown_to_adf then
adf_to_markdown; strategy() no longer matches. Restore/freshness can reject an
otherwise equivalent real import. Review comment 4295376550 identifies a real
coverage gap, including the separate attachment-fallback import scenario.

Test the full import from recorded published data, normalizing only irrelevant
formatting without losing strategy identity/content. Oversized attachment reuse
also needs qualification. No repair made; historical passed cases preserved.

[PR triage](../../notes/strat-creator-pr85-review-triage.md).

## Fixed in source, 2026-10-16

strat-creator commit f941955 on feat/s1-workflow-hardening. The prepared import uses full Jira descriptions/overflow attachments and a publisher-matched semantic ADF fingerprint. Full local Jira push/delete/import/reuse tests cover lists/comments and oversized attachment content; later published-strategy edits invalidate reuse.
No paid model batch was rerun for this remediation; historical evidence is unchanged.
