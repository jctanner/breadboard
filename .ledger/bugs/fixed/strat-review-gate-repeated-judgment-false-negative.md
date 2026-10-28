# Consistent repeated role judgment rejected by benchmark

Observed in markov-run-5d3327ed, Opus 4.6, RHAISTRAT-4 testability.
The 8,959-character report was delivered in the receiving Skill tool result,
captured with matching provenance and included verbatim in the composed review.
It opens with Testability: partially testable and repeats the same judgment
with explanation in its closing summary. Recommendation is revise.

review_assessment.py requires len(judgments)==1, so it reports missing or
unfinished assigned-role judgment despite two consistent completed judgments.
Original SHA-256:
3ad8c9d53399656194571e5f5e92f7f3653665ed602c956c0dbf0c5fdac87ef1.

Read-only replay reproduces failure. Renaming only the first field label to
Testability summary in memory produces assessment_present=true. No archived
report or historical result was changed. A repair should accept equivalent
completed repeated judgments or explicitly enforce one canonical producer
field, while continuing to reject contradictory, unfinished or placeholder
judgments. Preserve historical FAIL. No paid rerun is needed for parser tests.

[Run audit](../../notes/s1-mixed-state-opus-20261016.md).

## Closure confirmed, 2026-10-18

The current v1 checker already normalized repeated completed judgments and
required them to agree; that behavior predates today's format compatibility
patch. Its ledger state had remained open. Existing authored regressions reject
contradictory, pending and placeholder companion judgments. The unchanged
mixed-state receiving-channel replay now confirms all 36 reports pass, including
this testability report. Today's v2 adds the two separate format repairs and
does not claim to introduce the existing repeat handling.

Full benchmark suite: 104 passed, one optional integration skip. Original
reports and historical FAIL remain unchanged; no model calls.
[Verification](../../tasks/done/strat-review-checker-format-compatibility.md).
