# Restored legacy jobs lack their deleted cleanup tests

Federico Mosca reported the tests/test_cleanup_shell.py deletion in GitLab
strat-pipeline MR !18. Confirmed at e8f3959: .rfe-unlock-cleanup and all four
legacy jobs are restored/default, but the full-cutover deletion of their Bash
regression tests remains in the branch. Structural configuration assertions
do not replace executing the cleanup shell.

Expected: retain existing regression coverage for missing, empty, whitespace,
normal and duplicate bookkeeping entries against the actual after_script.
Restore upstream tests unchanged; no production behavior change is required.

Task: [cleanup coverage](../../tasks/done/strat-pipeline-legacy-cleanup-tests.md).

Fixed in 200b04b by restoring the original upstream file unchanged. All 14 Bash
cleanup regressions and full 148-test consumer suite pass. No runtime change.
MR baseline-to-head diff no longer removes/modifies this test file. Evidence:
var/run-data/20261027-strat-pipeline-cleanup-tests/.
