# Recording an unplanned review raises an uncontrolled StopIteration

PR #85 comment 4380387603. With valid current-run composition but no matching
create-inventory entry, cmd_record_review uses next() without a default and
prints a raw traceback. It does not save the in-memory mutation, but fails
without the helper's controlled inventory error.

Reproduced via the real CLI using a legacy-compatible local state fixture;
managed freshness can reject corrupted state earlier. This is error handling,
not evidence that a managed run accepted an out-of-scope review.
Local repair requires one unique inventory match before mutating progress.
Focused regression passes. Fixed in 2ecd758, published in PR #85 head b8d67c3.
Combined full suite: 1,362 pass, six optional skips. Evidence is sealed under
var/run-data/20261026-strat-pr85-review-and-merge/.
