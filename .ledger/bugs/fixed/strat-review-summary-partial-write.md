# Interrupted review-summary writes block recovery

PR #85 comment 4380387588. On 95a5c8f, publish_review.publish writes the
derived comment directly after checking for mismatched existing content.
A process terminated during that write leaves a partial destination; the next
call refuses it as mismatched. A retry can also truncate an already complete
matching summary because the original implementation rewrites it.

Reproduced using the real composer/publisher and a child process file-size
limit, with no external writes. Covers absent and previously complete files.
Local repair uses a temporary file and atomic replace, avoids rewriting a
matching completed file, and retains refusal of genuinely different content.
Focused regressions pass. Fixed in 2ecd758, published in PR #85 head b8d67c3.
Combined full suite: 1,362 pass, six optional skips. Evidence is sealed under
var/run-data/20261026-strat-pr85-review-and-merge/.
