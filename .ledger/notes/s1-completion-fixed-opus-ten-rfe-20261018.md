# Ten-ticket Opus run after the completion-hook repair

Run [markov-run-0b098f6e](https://markovd.local/runs/markov-run-0b098f6e),
candidate `6ed858b2294a29457153a90f187a801022c21e8b`, benchmark `f980238`.
Claude Code 2.1.296, Opus 4.6, ten distinct RFEs, Workflow concurrency ten.
One authorized run; no automatic paid retry or resume.

## Outcome

The native Workflow and model job completed successfully. CLI, host validation,
post-processing and lock release each exit 0. All ten acquired RFEs have one
created, refined, pushed, scored and reviewed strategy; none were merged or
skipped. All forty role reports reached their callers and were preserved in
the final reviews. All 36 Workflow step agents completed on their first attempt.

The repaired completion guard passed its first receipt. Its Python process
lasted **2.525709 seconds** in strace and exited 0; the StructuredOutput
call/return interval is 2.572 seconds. The unchanged timeout is ten seconds.
The complete `write result` agent took 20.998 seconds, including model calls
and the separate result helper. That agent duration is not the hook duration.
This validates the repair in one full-size integration run; it does not measure
a long-term failure rate. The previous native failure remains unchanged.

## Recorded benchmark failure

The pinned benchmark still records `pass=false`, solely for
`reviewer_outputs_returned`. It accepts 38 reports and rejects two complete,
delivered reports for formatting. All nine other checks pass. Preserve the
historical FAIL and its source rather than changing archived results.

| Report | Received characters | Why the checker rejects it |
| --- | ---: | --- |
| RHAISTRAT-5 feasibility | 9,265 | Findings use `#### 1.`, `#### 2.`, etc.; the recognized support fields contain short summaries, so detailed explanations never reach the content check. |
| RHAISTRAT-6 architecture | 6,391 | The judgment starts “Core architecture is sound with two unresolved validation items,” outside the accepted verdict prefixes. |

The feasibility report explicitly recommends revise and explains its concerns.
The architecture report explicitly recommends approve and discusses validation
items. Producer transcripts, receiving Skill results, saved report text and
provenance hashes agree for all forty reports; all forty appear verbatim in
their composed reviews. All forty also have allowed SubagentStop audit events.
No missing specialist handoff was found.

Read-only diagnostic replay reproduces both rejections. Adding only a Findings
heading before the feasibility numbered sections makes it pass. Replacing only
the architecture verdict prefix with “sound” makes it pass. These edits exist
only in memory; no report, source pin or historical verdict was modified.
The defects are already tracked under
[numbered findings](../bugs/fixed/strat-review-gate-numbered-findings-false-negative.md)
and [qualified architecture judgments](../bugs/fixed/strat-review-gate-mostly-sound-false-negative.md).
Repair/replay the checker against saved positive and negative cases before
spending on another run; reproducing these failures needs no inference.

## Timing and concurrency

Model job: **01:56:49–02:35:15 UTC on October 18, 38m26s**, corresponding to
21:56:49–22:35:15 New York time on October 17. Native Workflow:
01:57:20.441–02:34:01.904 UTC, **36m41s**. Markov orchestration:
01:56:32.962–02:35:34.343 UTC, **39m01s**. Archive collection is outside these
times; it ran 02:35:40–02:52:32 UTC.

| Phase | Elapsed envelope |
| --- | ---: |
| Read prepared input | 13s |
| Create ten strategies | 8m25s |
| Refine ten in parallel, then verify | 8m41s |
| Push | 1m30s |
| Prepare reviews and score ten | 4m22s |
| Review ten | 15m11s |
| Write validated result | 21s |

Score and review overlap: each ticket begins review after its own score returns.
These envelopes therefore cannot be added to get wall time. Reviews remain the
largest phase. The ten ticket reviews overlap, while each ticket's four role
reviews remain sequential. Reviewer transcript intervals show a peak overlap
of ten. The deferred reviewer-dispatch redesign was not part of this repair.

The previous ten-ticket job took 37m21s but failed native completion. This one
took 65 seconds longer overall and succeeded. Agent work varies between runs;
hook optimization is demonstrated by the matched replay and the actual guard
process, not by comparing two total job durations.

## Outputs, scope and remaining friction

Numeric decisions: four 8/8, two 7/8 and four 6/8, all approve with no attention
flag. Role recommendations are 17 approve and 23 revise. Their dissent remains
in the composed reviews. This follows the user's numeric-only approval policy;
final approval does not mean all four reviewers agreed or that technical content
was independently judged correct.

Every reviewer prompt names its assigned strategy. All forty reports have only
that strategy's target heading and no other ticket IDs. Audit paths show no
cross-ticket read attempts or allowed access to another ticket. These mechanical
checks found no cross-ticket contamination; they do not establish semantic
accuracy.

Review-scope audits contain 586 events: 543 allowed and 43 denied. Forty-one
denials concern the assigned ticket under the unauthorized `local/` path;
the other two concern a malformed architecture path and a tool-output file.
Agents recovered through authorized inputs. This is remaining avoidable work,
not a lost report or a new terminal failure. Claude also emits the existing
workspace-trust warnings about ignored permission entries.

## Usage and archive

854 captured requests and 854 usage-bearing responses; only `claude-opus-4-6`
appears in the captured model check. No recorded API errors or rate limits.

| Token category | Tokens |
| --- | ---: |
| Uncached input | 991 |
| Cache creation | 4,586,041 |
| Cache read | 28,125,940 |
| Output | 501,668 |
| Total accounted usage | **33,214,640** |

The 168,282 reported thinking tokens are included in output, not added again.
This total includes repeated cached input across requests and separate agents;
it is not the size of one context window. The CLI records **$55.27238125** at
the Opus API list-price basis, about **$5.53 per RFE**. This is a usage equivalent,
not an invoice. The primary's prose summary of “~1.2M tokens” is not total API
usage and should not be used for cost accounting.

Private archive:
`var/run-data/strat-workflow-hardening/pr85-completion-fixed-vertex-opus-ten-rfe-20261017/markov-run-0b098f6e/20261018T023540533633Z/`.
Complete/final, no collection errors, **11,033 manifest files /
17,094,202,740 regular-file bytes**. API dumps, 7,409 syscall-trace files,
native transcripts/state, Jira, MLflow, logs and shared-service snapshots are
retained. Final receipts are published; independent checksum verification passes.

The campaign's separate `analysis/` directory contains `analyze_run.py` and
`audit.json`, reproducing parent delivery, native producer identity, provenance
hashes, final incorporation, scope, timing and the two in-memory format probes.
The raw archive remains unchanged. This was Kubernetes/Markov/Breadboard
integration, not Fullsend/OpenShell qualification or independent content judging.

## Checker repair follow-up

On October 18 the user authorized the offline fix. `role-assessment-v2` now
accepts all forty unchanged receiving-channel reports, with exactly these two
classifications changing. The original benchmark FAIL stays preserved. Six
archived cases were replayed; real error/progress/lost-handoff failures still
fail, completed S2 stays 12/12, and the mixed-state run passes 36/36. Full suite:
104 pass, one optional integration skip. Private source/test/replay evidence is
saved separately under `analysis/checker-format-fix-20261018/` and verifies.
No model calls or deployment; the local changes remain uncommitted.
[Repair and evidence](../tasks/done/strat-review-checker-format-compatibility.md).
