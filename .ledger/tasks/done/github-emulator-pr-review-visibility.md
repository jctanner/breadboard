# Task: Display API-posted pull request reviews

## Goal

Show submitted review summaries in the PR conversation and review comments in file diffs.

## Evidence

PR experiment/markov-test-repo#2 has submitted review 70 and README.md comments
20 and 21 in the API. PullDetailPage only loads issue comments; PullFilesPage
only loads files. Neither renders review activity.

## Acceptance criteria

- Submitted review states, authors, dates and bodies appear in conversation order.
- Inline comments render at matching diff lines, including replies and left-side comments.
- Comments outside the available diff remain visible with their file context.
- Review/comment pagination is handled; loading failures are visible.
- Relevant frontend tests, production build, diff checks and live deployment pass.

## Status

Done. Existing unrelated emulator changes in README.md, pulls.py, bare_repo.py,
main.py and tests/test_pull_diff.py were preserved.

## Implementation and verification

- Added paginated review/comment reads to the PR conversation and Files changed pages.
- Submitted review summaries join the issue conversation timeline; pending reviews
  are excluded. Inline feedback includes file/line context and links to the diff.
- Diff placement supports LEFT/RIGHT line anchors, legacy positions across hunks,
  replies, and visible fallback sections for file comments or unavailable locations.
- Review and comment fragment links scroll to their target after asynchronous loading.
- Seven focused Vitest tests pass, including both page integrations, pagination,
  error handling, pending reviews, diff sides/replies/legacy/fallback cases.
- Production TypeScript/Vite build, ESLint on all changed TS/TSX files and both
  repositories' `git diff --check` pass.
- `make host-rebuild-github` completed and the deployment rolled out successfully.
- Browser verification on experiment/markov-test-repo#2 confirms summary review 70
  and comments 20/21 in conversation. Clicking the line 13 link opens Files changed
  at discussion_r20, scrolled into view. Both comments appear directly after the
  expected added lines (13 and 6). Browser console has no errors on the final flow.
- Initial navigation used a cached old HTML shell; a fresh URL loaded the new bundle.
  Hard refresh is sufficient for existing tabs. No review/comment data was mutated.
