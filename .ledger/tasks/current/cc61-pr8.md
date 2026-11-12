# CC-61: prepare PR #8 for manual merge

## Goal

Review durandom's domain/CA/Lima/Fullsend patch, fix findings, obtain independent
Codex and Claude no-blocker verdicts, and publish an approved fallback PR.

## Constraints

Work only in `/tmp/cc61-pr8`; preserve all 16 author commits. Never change the
live install, deploy services, merge, modify the author's fork, or comment on #8.

## Acceptance

- [x] Whole diff reviewed and first-round fixes committed.
- [x] Offline tests, compiler checks and shell syntax checks pass.
- [x] Approved fallback branch pushed to jctanner/breadboard.
- [ ] Both final reviews have no blockers; should-fixes fixed or explicitly deferred.
- [ ] Final tested commits pushed.
- [ ] Replacement PR opened and handed to the human, preserving authorship.

## Evidence

[Review and dispositions](../../notes/cc61-pr8-review.md).
Git SSH push works. GitHub CLI has no logged-in API account; PR creation requires
an existing authenticated session (`gh auth login`), requested from the human.
