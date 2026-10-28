# Fix the three actionable findings on 73c454b

## Scope

The owner explicitly requested all three repairs: final Jira review readback,
scope frontmatter parsing, and credential-bearing recovery filenames. Work in
the existing strat-creator feature branch, starting from clean 73c454b. Preserve
the Org Pulse certificate exception, numeric approval gate and workflow design.
Use offline tests only; no paid model or live Jira/export calls.

## Acceptance

- [x] Reproduce all three defects with regression tests before code changes.
- [x] Host reads back exact review summary, newest attachment and consistent verdict labels.
- [x] Valid frontmatter titles containing `---` work in root and bundled hooks.
- [x] Recovery export rejects credential-bearing paths with credential-free errors.
- [x] Full suite, lint, type descriptors and diff checks pass.
- [x] Archive sanitized evidence and document limits and source state.

## Related review

[Full assessment queue](../pending/strat-pr85-review-73c454b.md).
This task implements only comments 4354198477, 4354198483 and 4354198490.

[Implementation and current checks](../../notes/strat-pr85-three-review-fixes-20261022.md).
All 27 selected checks pass. Full suite: 1,261 passed, six optional skips,
406.12 seconds. Ruff, type descriptors and diff checks pass.
Eighteen-file archive at `var/run-data/20261022-strat-pr85-three-review-fixes/`
passes credential scanning (zero findings) and hash readback. The scanner
recognizes the one pre-existing synthetic non-key fixture explicitly.
All eight tested component files were published in signed-off commit
`0707b5baf546b2e0712cb4f9861a8f7705b4815f` to the existing
`feat/s1-workflow-hardening` fork branch. The full staged scan has zero credential
findings and every staged byte matches the archive. GitHub API confirms the exact
PR #85 head, and the component worktree is clean. No paid run, live Jira/export
mutation, review reply or deployment. Remote CI on this new commit has not been
assessed in this publication task.
