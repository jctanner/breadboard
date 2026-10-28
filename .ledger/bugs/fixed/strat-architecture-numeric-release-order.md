# Architecture release discovery compares numbers lexicographically

PR #85 comment 4380483679. On 95a5c8f, the CI fetcher and both shell fetch
paths choose 3.9 over 3.10 and ea.2 over ea.10. The remote shell path also
considers non-directory GitHub listing entries.

Reproduced against committed local Git fixtures and an offline HTTP listing
substitute. Local repair shares one numeric directory-name selector across all
paths, accepts actual directories and preserves the existing suffix convention.
It does not introduce a GA/prerelease policy change or a context commit pin.
Focused regressions pass. Fixed in 2ecd758, published in PR #85 head b8d67c3.
Combined full suite: 1,362 pass, six optional skips. Evidence is sealed under
var/run-data/20261026-strat-pr85-review-and-merge/.
