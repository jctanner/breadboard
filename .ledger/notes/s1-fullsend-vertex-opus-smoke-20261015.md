# One-ticket S1 integration through the Fullsend fork and Vertex

The authorized single-ticket smoke completed successfully on 2026-10-15.
The separate pinned benchmark remains FAIL because it misclassifies a delivered
feasibility assessment. This run verifies the source/provider integration and
business completion; it does not independently establish strategy accuracy.

| Item | Observed result |
| --- | --- |
| Markov run | `markov-run-d7043ace`, completed |
| Model job | `script-run-workflow-all-claude-opus-4-6-1015-171835-332613` |
| Job time | 17:18:35–17:46:29 UTC, 27m54s |
| Native Workflow time | 26m17s, one launch |
| Source | `jctanner-fullsend-ai/strat-creator`, `feat/s1-workflow-hardening`, exact `6a05210215247b287bb0fb61ed02e423c9de8692` |
| Benchmark source | Breadboard `54934699e61ee86a1e00117925e3ff3a0b79ae7f` |
| Model | `claude-opus-4-6`, primary and subagents |
| Business outcome | RHAIRFE-1 → RHAISTRAT-1, approve, 7/8 |
| Pipeline stages | Preflight, Claude, validation, post-processing and lock release all exit zero |
| Captured generation calls | 108, no errors or rate-limit responses |
| Upstream | All 108 matched by message ID to `vertex-strat-evals`, Google service-account authentication, HTTP 200, complete usage |

The relay time window also contains eight successful `count_tokens` operations.
These are separate from the 108 generation calls. Relay generation usage agrees
exactly with the archived API responses:

| Token category | Tokens |
| --- | ---: |
| Uncached input | 135 |
| Cache creation | 598,199 |
| Cache reads | 3,081,812 |
| Output | 62,855 |
| Total, including cache | 3,743,001 |

The 22,219 thinking tokens are already included in output. These totals are
usage, not a Vertex invoice or a measurement of unique context size.

## Completion and report audit

The final result and completion receipt agree. Every input hash matches the
captured artifact, including all reviewer reports and the published review.
The native Workflow's stored script exactly matches the pinned source, and its
final result points to the same receipt and receipt hash. The primary's recorded
tools are one Workflow launch, one Read and one Bash call that reads the result
file. It did not rewrite or relaunch the Workflow.

All four role reports match their actual producer transcript, their parent
Skill return and their provenance hash. Each report has one assigned-ticket
section, and each complete body appears verbatim in the composed review:

| Reviewer | Report characters | Recommendation | Pinned checker |
| --- | ---: | --- | --- |
| Feasibility | 11,809 | approve | Rejects format |
| Testability | 9,963 | revise | Accepts |
| Scope | 5,169 | approve | Accepts |
| Architecture | 15,079 | approve | Accepts |

Scores are feasibility 1, testability 2, scope 2 and architecture 2. Numeric
scores remain the sole approval gate, as the user requested. The testability
reviewer's `revise` recommendation is retained in provenance; it does not veto
the numeric approval. Substantive concerns include unvalidated per-revision
metric labels and an undefined minimum sample size. No independent judge was run.

## Benchmark disagreement

Nine of ten strict checks pass. Only `reviewer_outputs_returned` fails. The
feasibility report's short summary fields point to detailed numbered sections,
but the parser only counts prose attached to recognized fields or a canonical
Findings/Rationale heading. A `Prior review:` line captures the first detailed
sections as an unrecognized field. The parser then reports missing explanation.

A local replay reproduces the rejection. Adding only a Findings heading in
memory makes the same content pass. The original report and historical result
remain unchanged. This is a
[checker bug](../bugs/open/strat-review-gate-numbered-findings-false-negative.md),
with no observed recurrence of reviewer transport loss.

## Evidence and archival

Evidence root:
`var/run-data/strat-workflow-hardening/fullsend-vertex-opus-one-rfe-20261015/`.
Capture: `markov-run-d7043ace/20261015T174649748747Z/`.

The final archive completed at 17:53:01 UTC and independently verifies:
1,612 files, 6,357,233,437 bytes (6.36 GB), complete/final, errors=[]. The archive
receipt is published. Captured evidence includes 1,102 strace files, 217 API-dump
files, native transcripts/state, job artifacts, shared databases, Jira export,
MLflow, service logs and relay telemetry. Retained shared history is included;
this archive's total size is not storage attributable only to this one job.

The launch context contains exact launch/preflight/process evidence, final relay
records and their message-ID correlation summary, audit scripts and
`fullsend-opus-audit.json`. `archive-verification.json` records the independent
verification and `result.json` records the observer's final outcome. The audit verifies
completion hashes, source parity and all four actual receiving channels. No new
inference request, reset or paid retry was made while checking these results.

## Why one ticket still took almost half an hour

The successful overnight three-ticket run took 36m28s. This one-ticket run took
27m54s, only 24% less elapsed time, although token usage fell from 10.51M to
3.74M, about 64% less. Three tickets did not require three serial executions:
their refinement agents ran together, their scoring agents ran together, and
their review agents overlapped. Batch latency follows the slowest dependency
chain; aggregate token work still grows across tickets.

| Elapsed work | One ticket | Three tickets |
| --- | ---: | ---: |
| Create | 2m03s | 4m33s |
| Refine | 6m29s | 6m03s, three agents overlap |
| Scoring and review | 15m42s | 20m54s, ticket pipelines overlap |
| Other job work | 3m40s | 4m58s |
| Whole job | 27m54s | 36m28s |

Rounded seconds sum to the job totals. Scoring/review is measured from the first
scorer start to the last review completion, so overlap is counted once. Other
work includes input/readiness checks, push, final result and job setup/teardown.
External archive collection is excluded from both job times.

There is also a concrete bottleneck inside each ticket's review. The model
requested all four reviewer Skills in one API response, message
`msg_vrtx_011Cg4RbxJezfuB8yRwiXqhP`, streamed at 17:34:20.601–17:34:21.927 UTC.
Their actual child transcripts show serial execution:

| Reviewer | Actual child span, UTC | Duration |
| --- | --- | ---: |
| Feasibility | 17:34:26.6–17:37:16.7 | 2m50s |
| Testability | 17:37:23.2–17:39:06.7 | 1m44s |
| Scope | 17:39:13.2–17:40:47.8 | 1m35s |
| Architecture | 17:40:54.3–17:43:15.6 | 2m21s |

Together these occupy an 8m49s interval; the longest individual review takes
2m50s. Perfect overlap at unchanged individual durations would remove about six
minutes from that interval. That is arithmetic, not a tested speedup: concurrency
can change provider latency and resource contention. The full review agent
took 12m34s, including preparation, composition, publication and recording.
The same within-ticket reviewer ordering appears in all three overnight tickets.

The configured outer agent cap was already five. It did not make these four
Skill executions overlap. Follow-up exact-binary inspection confirms that Skill
inherits isConcurrencySafe=false and the dispatcher waits for each unsafe call
to finish. Two zero-provider native controls reproduce serial calls from one
Workflow agent and four overlapping calls from separate Workflow agents.
This is a separate [performance finding](../bugs/open/strat-reviewer-skills-serialized.md).
[Binary proof and controls](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-skill-concurrency.md).

There is no indication of a broad Vertex request slowdown in this pair: median
matched generation latency was 5.0s here versus 6.0s overnight, and median time
to first event was 1.6s versus 2.4s. These are descriptive request statistics,
not a controlled provider comparison. The fixtures differ, the older run used
the personal Anthropic provider, and the source revisions differ. Both runs
used Opus 4.6 and cap five. No paid run was made for this diagnosis.
