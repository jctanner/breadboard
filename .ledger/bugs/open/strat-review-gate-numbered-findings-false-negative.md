# Feasibility report rejected despite delivered numbered findings

## Evidence

Fullsend/Vertex smoke `markov-run-d7043ace`, model job
`script-run-workflow-all-claude-opus-4-6-1015-171835-332613`, completed on
2026-10-15 with all four reviewer reports delivered and preserved verbatim.
The pinned benchmark rejects only RHAISTRAT-1's feasibility report under
`reviewer_outputs_returned`, with reason
`no explanatory role content beyond verdict/status/boilerplate`.

The actual report contains 11,809 characters, a completed `feasible` judgment,
an `approve` recommendation, and eight numbered analysis sections. It identifies
concrete concerns about per-revision metric labels, Prometheus access and RBAC,
reconciler ordering, effort estimates and minimum sample size. Producer
transcript, parent Skill return, provenance hash and composed review agree.
The body SHA-256 is
`ade14c7a9258e58f40347a38a524be0e8230949def4605b5d98ac88854f494a7`.

## Cause and local reproduction

`review_assessment.py` accepts explanatory text only under recognized role
fields or headings named Findings, Detailed findings or Rationale. This report's
recognized support fields are short: `credible (slightly optimistic)`,
`delivers`, and `listed below`. A following `Prior review:` field absorbs the
first detailed sections. Later prose containing a colon is also parsed as
unrecognized fields. The numbered findings never reach `_explains()` through
the recognized support fields, although they are present in the assigned-ticket
section. The parser therefore mistakes section organization for missing content.

Replaying the original archived body produces the recorded rejection. Adding
only `#### Findings` immediately before `#### 1. Can we build this with the
proposed approach?` in memory produces `assessment_present=true`. No report,
result or pinned source was changed. No inference was required.

`check_run.py` sets `result_chars=0` after classification rejects the body;
`content_chars=11809` describes the actual received content. This is another
external checker false negative, separate from the earlier
[qualified architecture judgment failure](strat-review-gate-mostly-sound-false-negative.md).

## Follow-up

Keep the historical FAIL unchanged. Repair the format contract explicitly:
either require canonical findings headings from producers or recognize detailed
numbered sections within the assigned-ticket assessment. Use archived-report
replays, retaining negative cases for acknowledgements, status text, templates,
wrong-ticket reports and unfinished recommendations. No paid rerun is needed to
reproduce or fix this parser issue.

[Run audit](../../notes/s1-fullsend-vertex-opus-smoke-20261015.md).

## Ten-ticket recurrence

Run markov-run-fbc62d49 also rejects feasibility reports for RHAISTRAT-2
(10,016 chars), RHAISTRAT-4 (12,471 chars) and RHAISTRAT-10 (7,841 chars)
with the same no-explanatory-content reason. All three were captured by the
live hook and included in published reviews. Preserve the historical result.
That run genuinely failed for a separate
[duplicate recommendation capture defect](../fixed/strat-review-duplicate-recommendation-capture.md)
affecting two other reports. [Audit](../../notes/s1-fullsend-opus-ten-rfe-20261015.md).

## Mixed-state Opus recurrence

Run markov-run-5d3327ed rejects RHAISTRAT-15 feasibility (10,733 characters)
for the same numbered-findings organization. Its complete parent return, saved
report, provenance hash and composed review match. Adding only a Findings
heading in memory makes the classifier pass. Pipeline and mixed-state/repeat
checks passed; historical eval remains failed.
[Audit](../../notes/s1-mixed-state-opus-20261016.md).
