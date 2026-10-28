# Results publication follows directory symlinks

PR #85 comment 4382320349, reproduced on a0158d9 with real local Git
repositories and clones. Commit a directory symlink at RHAISTRAT, the run
directory or either tested artifact-parent depth, then publish a normal bundle.
Existing targets receive copied artifact bytes before the later manifest check
rejects the symlink; dangling targets produce uncontrolled filesystem errors.
A source artifact-root symlink also reaches copying before cleanup refuses it.

Expected: validate paths before reading state or publishing, reject symlinks at
every component below the chosen checkout root, and preserve outside content
and source files. The intentional current symlink is not an artifact directory.
This needs write access to the results repository; it is not a remote Jira input.

Evidence: /tmp/strat-pr85-path-label-red.log (19 failed, one control passed).
Task: [review fixes](../../tasks/done/strat-pr85-review-a0158d9.md).

Fixed in 0d60824. Validate every path component, traversal and resolved
containment before state reads/planned copies; recheck the destination before
atomic replacement. Source artifact roots use the same guard. Real cloned-link
regressions and existing atomic-copy/retry controls pass. Full offline suite:
1,413 pass, six skips. Evidence:
var/run-data/20261026-strat-pr85-path-label/.
