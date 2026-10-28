# Interrupted results copy poisons identified-run recovery

PR #85 comment 4381545489, reproduced on b8d67c3. A child writes 128 bytes
of a larger real strategy artifact and dies by SIGKILL (or raises a copy error).
The partial file is already at its final publication path. A later attempt
rejects its hash as conflicting instead of completing the copy.

Expected: verify a private temporary copy before atomic publication. Orphans
from process death must not enter the strict published-file inventory. Genuine
conflicting destination bytes must still be preserved and rejected.

Evidence: /tmp/strat-pr85-three-concerns-red.log.
Task: [approved review fixes](../../tasks/done/strat-pr85-review-b8d67c3.md).

Fixed in a0158d9: private .git staging, fsync, expected-hash check, atomic
replace and parent fsync. SIGKILL orphan bytes remain outside the published
inventory. Genuine final-file conflicts still stop. Full offline suite passes
(1,394 passed, six skips); fault/retry regressions pass.
Evidence: var/run-data/20261026-strat-pr85-human-gates-publication-ownership/.
