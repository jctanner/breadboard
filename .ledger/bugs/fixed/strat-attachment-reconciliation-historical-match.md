# Attachment reconciliation accepts obsolete content

## Finding

Automated PR #85 inline comment4351850963 on `32700ec` reports that matching any
historical attachment can mark an upload complete while readers select a newer
different attachment. After A then B then intentional A, the helper adopts the
old A rather than appending a fresh A. Strategy and review attachments share
the helper; publication verification also uses it.

## Scope and expected repair

Match only the newest attachment for the exact filename using the existing
shared attachment_sort_key. Preserve append-only history and same-run journal
identity/uncertainty refusal. Prove A→B→A publication-to-pull and that an
intervening write does not cause blind re-upload from a pending/verified ledger.
No model or live Jira calls are needed.

## Resolution

Implemented locally on `32700ec`: newest exact-filename attachment is the only
candidate, with append-only history and the existing same-run journal intact.
Eight regressions fail before the repair; after repair the focused recovery
group39 passes and full suite1,238 passes/six optional skips. Lint/types/diff
pass. [Dispositions and evidence](../../notes/strat-pr85-post327-review-followup-20261022.md).
Thirteen-file archive passes credential scan and hash readback. Published as
signed-off `73c454b`; PR #85 head verified and component clean. Remote Python 3.11/3.12
tests, lint, Unicode and DCO checks pass. No model or live Jira call, nor a
changed security architecture.
