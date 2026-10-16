# Mixed-state S1 Opus result, 2026-10-16

Run: markov-run-5d3327ed. Model job:
script-run-workflow-all-claude-opus-4-6-1016-135017-13fd26.
Breadboard a2aec3c758567b68428322d4e9f42d89d4cd7a25;
strat-creator f5691f7e01b392be6b177356dbf204918a1b42af.
One authorized Opus 4.6 pass, high effort, batch cap ten, agent cap ten.

## Result

Pipeline succeeded: pre, Claude, output validation, post and release all exited
zero. Native Workflow wf_51366308-dc3 completed once, with 30 workflow agents.
Model job: 13:50:17–14:35:31 UTC, 45m14s. Native Workflow: 41m09.550s.
Markov: 13:49:40.953–14:35:45.864 UTC, 46m04.911s.

All nine acquired RFEs completed: four fresh strategies, three refinements,
two review-only recoveries. Four clones and seven refinements/pushes matched
the plan. All nine reviews published with one review attachment per strategy.
Numeric decisions: seven approve, two revise/needs-attention. Revision outcomes
are completed reviews, not execution failures. Review-only published content
and prior effects stayed intact. Controls/deferred work stayed unchanged;
all nine owned locks released, and the foreign owner's claim was preserved.

The model-free repeat passed: completed work excluded, only deferred RFE 9
acquired, human-signed-off RFE 13 skipped, no duplicate side effects, zero model
invocations. This establishes the scenario's repeat behavior, not universal
crash recovery. The native-failure monitor was enabled but did not trigger in
this successful run; its negative-path evidence remains the local process tests.

## Separate benchmark failure

The pinned eval-result.json records pass=false solely for
reviewer_outputs_returned. All other checks passed, including model identity,
all mixed-state checks and the repeat. Do not rewrite that historical result.

Independent read-only inspection found all 36 role reports in parent API
receiving tool results, byte-matching the saved report text. All 36 SHA-256
values agree with review provenance; every report is present verbatim in its
composed review. No missing handoff was found. The checker accepts 33 and
rejects three for formatting:

| Strategy / role | Received characters | Rejection cause |
| --- | ---: | --- |
| RHAISTRAT-15 / feasibility | 10,733 | Eight numbered findings fall outside recognized support/findings fields. |
| RHAISTRAT-3 / architecture | 5,819 | Judgment starts with “Mostly sound”; checker requires a canonical prefix. |
| RHAISTRAT-4 / testability | 8,959 | Two consistent “partially testable” judgment fields; checker requires exactly one. |

Original report hashes, in table order:

- e12092ed4e0408faaf4564e3e0343f0d3cf888f71b4010d9ca76e6499fcd243b
- e511ef80b6fa6a7a861abfad533ed469dd0b0ccbd26e52cc1dfbe84d2c46dbe1
- 3ad8c9d53399656194571e5f5e92f7f3653665ed602c956c0dbf0c5fdac87ef1

Read-only diagnostic replay reproduced each rejection. Independent in-memory
format edits each make its original report pass: add a Findings heading before
the feasibility numbered sections; change Mostly sound to Sound; rename only
the first Testability label to Testability summary. These are diagnostic edits,
not changes to stored reports, source rules or the historical result. They do
not judge the technical accuracy of the reports.

The first two defects were already tracked. The repeated judgment is a new
[checker defect](../bugs/open/strat-review-gate-repeated-judgment-false-negative.md).
Repair the checker with retained positive and negative report replays; a paid
rerun is unnecessary to reproduce these cases. No new run was submitted.

## Usage and evidence

API dump accounting: 753 calls, 870 uncached input tokens, 4,060,535 cache-write,
23,366,431 cache-read, 420,359 output; 27,848,195 total. Thinking is a reported
subset of output and is not added again. Zero recorded API errors/rate limits.
Only claude-opus-4-6 appears in the recorded request/response model check.

Archive:
var/run-data/strat-workflow-hardening/fullsend-vertex-opus-mixed-state-c10-20261016/
markov-run-5d3327ed/20261016T143613185865Z.
11,940 files / 22,344,722,063 bytes; complete/final, no source errors. Includes
API dumps, strace, native journals, artifacts, Jira and service/system captures.
Independent verification passed and final receipts were published at terminal
collection. launch-context/result.json and archive-verification.json retain
that verification. Observer finished at 14:53:30 UTC.

## Cross-ticket contamination check

The user noticed apparent duplicates. The seed itself reused eight subjects
for excluded/human-skipped controls: 18 RFEs draw on ten subject templates.
All nine acquired RFEs have distinct templates/subjects. These duplicate
subjects predate model work and were created by fixture setup, not inferred
from the resulting strategies. Examples: registry RFE 7/11 (STRAT 3/7),
queue RFE 8/12 (STRAT 4/8), workbench RFE 3/13 (STRAT 12/9 after creation).
Their control states are approved, needs-attention and human-signed-off,
respectively; the control issues remained unchanged.

All 36 role reports have exactly one assigned target heading, no other ticket
IDs anywhere in the report, and no conflicting recorded launch/result history.
Review-scope logs contain 511 events from 36 reviewer agents: 474 allowed and
37 denied. Matching agent assignments against every tool path finds no
cross-ticket read attempts. Every denial is a Read of the correct ticket
under local/ rather than its authorized artifacts/ path. No allowed tool path
contains a different strategy/RFE key.

All nine strategy frontmatters match their expected source RFE/title and have
distinct content hashes. A supplementary ten-word-sequence comparison over
task bodies found the highest pairwise Jaccard similarity was 3.69%; this is
a copying screen, not a semantic quality score. Shared templates and platform
context can legitimately repeat. No cross-ticket contamination was detected
by these checks; this does not establish the factual accuracy of every claim.
A future fixture can give the controls unique subjects too, making visual
inspection clearer and avoiding confusion with agent-created duplicates.

## Recorded Gantt chart

Timings come from native workflow agent startedAt/durationMs and saved job
metadata. Per-ticket bars show refinement, score and review agents; batch
creation/import and push are shown once above. New York time (EDT).

```text
Opus 4.6 | 2026-10-16 | New York time
Job: 09:50:17 -> 10:35:31 (45m14s)
Workflow: 09:51:22 -> 10:32:31 (41m10s)

Minutes from job start    0    5    10   15   20   25   30   35   40   45
                          |----|----|----|----|----|----|----|----|----|-
Setup / launch            H.............................................
Read prepared input       .I............................................  00:23
Create / import (batch)   .CCCCCCCCCCCC.................................  11:36
Refine 7 + verify         .............RRRRRRR..........................  07:16
Push 7                    ....................PPP.......................  02:18
Score 9                   .......................SSS....................  03:31
Review 9                  .........................VVVVVVVVVVVVVVVV.....  16:04
Write validated result    .........................................F....  01:34
Reporting / host finish   ..........................................HHH.

Per ticket (RFE -> STRAT)
Minutes                   0    5    10   15   20   25   30   35   40   45
 1 -> 1                   .......................SSVVVVVVVVVVVVVVV......  review-only
10 -> 6                   .............RRRRRR....SSSVVVVVVVVVVVVVV......  existing / refine
 2 -> 2                   .......................SSVVVVVVVVVVVVV........  review-only
 3 -> 12                  .............RRRRRR....SSVVVVVVVVVVVVVVV......  fresh
 4 -> 13                  .............RRRRR.....SSSVVVVVVVVVVVVVVV.....  fresh
 5 -> 14                  .............RRRRRR....SSVVVVVVVVVVVVVV.......  fresh
 6 -> 15                  .............RRRRRRR...SSSVVVVVVVVVVVVVVV.....  fresh
 7 -> 3                   .............RRRRR.....SSVVVVVVVVVVVVVV.......  existing / refine
 8 -> 4                   .............RRRRR.....SSVVVVVVVVVVVVVVV......  existing / refine

C=create/import  R=refine  P=push  S=score  V=review
I=read input  F=write result  H=host/primary overhead
One character ~= one minute; bars rounded. Dots mean no plotted step.
```

The batch limit was ten; nine tickets acquired because human-signed-off
RFE 13 was skipped. Archive collection/independent verification finished at
10:53:30 New York time, outside this job/workflow timeline.
