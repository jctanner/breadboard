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
- [x] Both final reviews have no blockers; should-fixes fixed or explicitly deferred.
- [x] Final tested commits pushed.
- [x] Replacement PR opened and handed to the human, preserving authorship.

## Evidence

[Review and dispositions](../../notes/cc61-pr8-review.md).
Git SSH push works. The human explicitly authorized the `.env.github` token for
GitHub API calls; replacement [PR #10](https://github.com/jctanner/breadboard/pull/10)
is open and credits the original author. No credential values were printed.

## Status

Complete: Codex and Claude report no blockers at implementation head `cea968c`;
fixes are pushed and replacement PR #10 is ready for the human to merge manually.
Nothing is merged, #8 remains unchanged, and the live install is untouched.
