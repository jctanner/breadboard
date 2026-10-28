# Accept completed reviewer assessments in observed Markdown formats

Requested 2026-10-18: fix the remaining checker false negatives from the
ten-ticket Opus run without another model call. Work in Breadboard's benchmark
checker; no strat-creator, hook, numeric approval policy or source-pin change.

- [x] Reproduce the two failures from unchanged archived receiving channels.
- [x] Accept numbered Markdown findings with explanatory bodies and a bounded
      architecture judgment prefix; retain incomplete/conflicting negatives.
- [x] Add authored regressions and run the benchmark suite.
- [x] Replay original reports through the repaired checker, keeping historical
      results, report bytes and manifests unchanged.
- [x] Save replay evidence, update the bugs and hardening plan, and diff-check.

Use a new contract version to distinguish the revised recognition rules from
historical results. Check both real regressions and negative cases for status,
templates, wrong tickets, ambiguous judgments and conflicting recommendations.

## Repair and validation

Implemented `role-assessment-v2` in `review_assessment.py`. Numbered Markdown
sections contribute their explanatory body, excluding their titles/fenced
examples and stopping at the next heading. Architecture judgments may begin
with the explicit subjects “Core architecture is” or “Architecture is”; strip
that subject before verdict matching and explanation checks. No arbitrary
substring search or report-length shortcut. Existing attribution, ambiguity,
repeat/conflict, error, skip and recommendation checks remain.

Six authored regression methods reproduce four pre-repair failures, including
both observed formats and the real receiving-channel join. Focused suite:
27 pass. Full suite with `MARKOV_BIN=checkouts/markovd/bin/markov`:
105 tests run, 104 pass, one existing optional emulator integration skip.
Python compilation and `git diff --check` pass. Existing SQLite ResourceWarnings
are printed by the suite; no test fails.

## Read-only archived-channel replay

| Run | Accepted assessments / expected |
| --- | ---: |
| Latest ten-ticket Opus, markov-run-0b098f6e | 38/40 before, **40/40 after** |
| Mixed-state Opus, markov-run-5d3327ed | **36/36** |
| Failed S1 stream, markov-run-7845a7f1 | 0/12, remains failed |
| Quota-stopped S2, markov-run-6bcb3c32 | 7/12, remains failed |
| Completed S1 with lost handoffs, markov-run-c5ba3904 | 2/12, remains failed |
| Completed S2, markov-run-79d3241a | 12/12, remains passed |

Exactly RHAISTRAT-5 feasibility and RHAISTRAT-6 architecture change for the
latest capture. Before/after replay input hashes match; original gate and
overall FAIL are preserved alongside the new delivery result. All replays
re-hash their API/evaluation inputs after reading. This recomputes delivery
only, not historical pipeline outcomes or content accuracy.

The already implemented consistent-repeat handling is also verified against
the mixed-state report; its stale open bug is closed with this qualification.
It was present in the retained pre-patch v1 source and is not a new v2 feature.

## Durable evidence and scope

Private evidence directory:
`var/run-data/strat-workflow-hardening/pr85-completion-fixed-vertex-opus-ten-rfe-20261017/analysis/checker-format-fix-20261018/`.
Sixteen files / 1,769,863 bytes, complete/final, checksum verification passes.
Contains before/after replays, all control results, exact old/new checker and
test sources, test log, summary, runner and capture script. Manifest kind is
model-free checker replay; no new model-run receipt is published.

Changes are local/uncommitted. No paid run, inference tokens, Jira writes,
strat-creator changes, numeric-policy changes, historical pin edits or deployment.
Future deployed benchmarks must pin a published Breadboard revision containing
the repaired checker; old pins deliberately keep their original behavior.

Published with the authorized mixed-batch setup as Breadboard
`9232633963f509addbf2197d453e68fb1236e03f` on October 18. The commit includes
only benchmark source/test/README files; pending ledger changes remain local.
Markovd's imported workflow matches all 81 published files. Historical run
pins and original verdicts stay unchanged.
