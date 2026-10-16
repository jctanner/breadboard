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
