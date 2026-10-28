# Restore legacy cleanup tests after Federico's MR comment

Federico Mosca correctly flagged tests/test_cleanup_shell.py as deleted in
MR !18 despite legacy jobs remaining the default. The deletion came from the
original full cutover and was missed when the legacy path was restored. The
runtime after_script already matches upstream; this is a test coverage fix.

Restore the original file byte-for-byte from upstream baseline 9bbac1e.
Its 14 shell-level tests extract the actual YAML after_script and run Bash with
errexit/pipefail, substituting a temporary bookkeeping path and recording the
unlock command instead of calling Jira. Cases cover missing/empty/whitespace
records, one/multiple keys, duplicate keys and blank lines, plus diagnostics.
No runtime or CI configuration change, new hook, new source ref or executor switch.

Signed-off commit 200b04b1a6cf413280f60647f69f4adffdf94232 restores one file.
Source/staged-patch credential scans found zero secrets; component clean. The
original file no longer has any change in the MR's baseline-to-head diff.

Focused: 14 passed in 0.41 seconds. Full consumer suite: 148 passed in 14.96
seconds. git diff --check passes. No inference, live Jira write or model job.
The file will no longer be a deletion in the MR diff; the restored bytes match
the baseline exactly. Existing structural CI/selector tests are retained.

Evidence destination: var/run-data/20261027-strat-pipeline-cleanup-tests/.
No public reply or thread resolution; the owner can answer Federico after the
source restoration is published.

Ten-file evidence archive sealed with zero credential findings; manifest and
byte readback verified. Pushed 200b04b normally and verified exact Git/GitLab
head, component clean. The file no longer has a diff relative to the upstream
MR baseline. MR description now reports 148 tests and restored cleanup coverage.
Separate sealed receipt:
var/run-data/20261027-strat-pipeline-cleanup-tests-publication/.

New-head MR pipeline 2995309329 was pending at publication. No reply or thread
resolution was posted, no executor/runtime setting changed, and no model job,
live Jira write or merge occurred.
