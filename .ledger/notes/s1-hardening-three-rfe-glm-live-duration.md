# Live GLM three-RFE duration diagnosis

2026-10-14, observations around 22:18–22:23 UTC, while the job remained active.
Read-only inspection; no kill, restart, model call or live pipeline edit.

Run `markov-run-cf0dfe9a`, job
`script-run-workflow-all-glm-5-3-1014-204524-5924cf`, hardened source `0e7e752`.
The job started at 20:45:24 UTC. This is interim evidence, not a terminal result.

## Progress and where time went

At roughly 93 minutes, all three strategies were created, refined and pushed.
RHAISTRAT-2 review was marked complete at 22:09:39; RHAISTRAT-1 at 22:18:33.
Both numeric verdicts were approve. RHAISTRAT-3 was still reviewing; its first
specialist began at 22:16:38. Responses and new artifacts continued to arrive.
The pod had no restarts. No inference was launched by this investigation.

| Activity | Observed elapsed time |
| --- | --- |
| Read input | 27s |
| Create all three strategies | 7m41s |
| Refine RHAISTRAT-1 / -2 / -3 | 20m12s / 13m20s / 15m50s |
| Push all three | 1m38s |
| Score RHAISTRAT-1 / -2 / -3 | 7m21s / 6m36s / 5m27s |
| Review RHAISTRAT-2 / -1 | 37m34s / 41m35s |
| Review RHAISTRAT-3 | Still active at inspection |

Activities overlap, so their durations do not sum to wall time. The runtime
started two refinement agents first, then the third when one finished. Scoring
and ticket review also ran with two outer agents at a time. There was no explicit
`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` override in Claude's process.
The pod's CPU quota was two cores; Node reported availableParallelism=1 and
16 enumerated CPUs. The pinned binary's CPU-derived concurrency formula has a
floor of two, consistent with the observed outer scheduling. This is not a new
controlled scheduler test.

Each completed review submitted its four specialist Skill calls within one
second, but child transcripts show serial execution within that ticket. For
RHAISTRAT-1 the role durations were about 6m30s feasibility, 3m51s testability,
2m10s scope and 9m54s architecture. The architecture Skill's 22m50s parent wait
included waiting behind the earlier roles. Two ticket review agents overlapped.
Do not infer parallel execution merely from a batched tool request.

## Concrete integration bug

All three review agents hit a scorer-path mismatch: Workflow outputs are in
`/tmp/strat-assess/<KEY>/`, but composition requires repository-contained inputs.
Each recovered by copying the result to repository `tmp/strat-assess/<KEY>/`,
verifying equal hashes, then retrying begin. The rejected-to-success intervals
were 9m26s, 13m39s and 3m02s. `git diff --stat` on the live target was empty.

[Open bug, reproduction and proposed repair](../bugs/fixed/strat-workflow-scorer-path-outside-composition-scope.md).
The initial scope report for RHAISTRAT-2 was also rejected by composition for
two Recommendation lines. Its parent launched one replacement scope Skill,
which returned a captured report. This is an extra specialist call inside the
single job attempt, not another benchmark iteration. Final delivery/consistency
gates have not yet been evaluated.

## Model and context work

Completed architecture specialists made 47–48 tool calls each, including reads
across the overlays. A successful GLM response reporting 16,608 output tokens
took about 292 seconds. At the 370-response snapshot, provider-reported output
tokens totaled 386,662. These are recorded usage categories, not a GLM invoice
or a measured split between visible answer and hidden reasoning.

The native journal then contained one launch, 13 agent starts, 12 results and
no failed-agent entries. This rules out an observed Workflow restart loop at
that snapshot; it does not independently enumerate every HTTP retry.

## Relay check

At 22:22:40 UTC the relay returned 414 records since job start, all GLM on
`enmaas-personal`: 373 stream-generation and 41 token-counting requests. All
recorded requests were complete, HTTP 200, with no recorded errors. Generation
latency median 11.384s, p95 113.333s, maximum 291.576s; time to first event
median 4.447s, p95 14.050s, maximum 66.158s. Long successful generation and
queued/serialized work explain more than a relay timeout at this snapshot.

This is a time/model-scoped relay export, not an exact join to every job request
ID. In-flight work and later failures remain outside this completed-record count.
Private read-only telemetry snapshot:
`var/run-data/strat-workflow-hardening/three-rfe-glm-opus/diagnostics/20261014T222239233070Z/`.
Native source transcripts, API captures and journal remain in the active job
and will be retained by the campaign's terminal collector. No final archive
receipt was published by this diagnostic.

[Batch authorization and conditional Opus gate](../tasks/done/s1-hardening-three-rfe-glm-opus.md).

## Completed timeline

Final archive confirms GLM job 20:45:24–22:58:50 UTC (16:45:24–18:58:50 Eastern),
133m26s, followed by approximately 11 minutes of archival/verification. All
benchmark, completion, native-journal and 12-report preservation gates pass.

Exact intervals in minutes from job creation: create 1.09–8.77; refine tickets
1/2/3 at 8.77–28.96, 8.77–22.10, 22.10–37.93; check/push 37.94–40.09;
score 1/2/3 at 40.09–47.44, 40.09–46.70, 46.73–52.18; review 1/2/3 at
52.18–93.76, 47.44–85.00, 85.00–127.59; write result 127.59–129.71;
remaining host work ends at 133.43. Only two outer agents ran concurrently;
the third ticket review waited until minute 85.

The last ticket's 43-minute review breaks down approximately as: setup/path
workaround 6m, feasibility 6m, testability 4m, scope 3m, architecture 7m,
format diagnosis 7m, replacement reviews 6m, composition/publication 4m.
Its initial testability and scope reports each contained two Recommendation
lines, so both were regenerated after diagnosis. This extra work explains the
long tail missed by the earlier ETA. RHAISTRAT-2 also regenerated its scope report.
[Formatting gap](../bugs/open/strat-review-recommendation-format-causes-regeneration.md).

Source: finalized archive
`var/run-data/strat-workflow-hardening/three-rfe-glm-opus/markov-run-cf0dfe9a/20261014T225916540357Z/`,
native state `wf_00663744-1bf`, outer progress and parent/child transcripts.
