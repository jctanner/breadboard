# Specialist reviewer returns cover the batch despite individual targets

## Evidence

In relay-fixed S1 Opus `markov-run-c5ba3904`, two testability Skill calls
are launched for RHAISTRAT-1 and RHAISTRAT-2 respectively. Both returned
prose has headings for **RHAISTRAT-1, RHAISTRAT-2 and RHAISTRAT-3**.
The second explicitly says it has all three strategies/RFEs before its
assessment. These are separate launches reviewing the same full batch.

Verified archive:
`var/run-data/strat-workflow/markov-run-c5ba3904/20261011T175615927646Z/`.
Under S1 job `script-run-workflow-all-claude-opus-4-6-1011-170435-3f61ed`,
`artifacts/eval-result.json` records target identities and tool IDs.
Parent tool-result bodies are preserved in API requests
`a256f4b2-1b94-476d-bd85-566585442968.request.json` (target 1) and
`60e11825-ed18-4be0-a9fe-c8b8fe9ebbb0.request.json` (target 2).

## Impact and limits

Duplicated batch review work undermines intended per-strategy isolation
and complicates attributing specialist evidence, duration and token cost.
All three RFEs still receive distinct strategies and one final review;
this is not deduplication of the seed RFEs. This scope issue is distinct
from missing Skill returns and the repaired relay timeout. The exact
prompt/argument propagation cause has not been diagnosed.

## Status

Open. Recorded without modifying S1/S2 or launching another run.

## 2026-10-11 — Also reproduced in S2

S2 `markov-run-6bcb3c32`, final archive
`var/run-data/strat-workflow/markov-run-6bcb3c32/20261011T191550355513Z/`,
job `script-strategy-entrypoint-all-claude-opus-4-1011-181949-e387e8`.
Seven substantive Skill returns cover RHAISTRAT-1/2/3 despite per-strategy
launches: feasibility/testability/scope for target 1, and all four roles
for target 2. All seven have separate headings for each of the three
strategies. Results preserved in API request files
`7b43b84e-238e-466e-871e-cc1a5a23b8ec.request.json` (target 1) and
`09cf2531-d9ad-42e0-aed4-125b81b1b889.request.json` (target 2).

Target 1 architecture returns only a progress message, a separate gate
false positive. The run later aborts on an upstream account HTTP 429;
target 3 reviewers are never launched. Only target 1's final review is
published. This extends the scope finding to both workflow designs;
underlying prompt/argument propagation remains undiagnosed.

## 2026-10-12 — All 12 roles/targets in completed S2 Opus repeat

S2 markov-run-79d3241a completes all three reviews and passes the benchmark.
Final verified archive:
`var/run-data/strat-workflow/markov-run-79d3241a/20261012T021947729737Z/`.
Job: `script-strategy-entrypoint-all-claude-opus-4-1012-005035-b81781`.
All 12 substantive Skill results (8952–18350 chars excluding wrappers) have
separate assessment headings for all three strategies despite each launch
request targeting one strategy. Four roles times three targets, repeated
whole-batch assessment; no missing-return false positive in this attempt.
Exact launch tool IDs/targets and result previews in artifacts/eval-result.json;
full returned assessments preserved in API request histories and index.jsonl.
Total job runtime 88.7 min, 248 captured Opus generations; do not quantify the
extra cost/time caused by scope drift without a controlled comparison.
[Completed task](../../tasks/done/strat-workflow-tier2-s2-opus-rate-limit-retry.md).

## 2026-10-12: Argument delivery verified in captured prompts

The production-gap audit joins expanded Skill prompts to original launches.
The requested per-strategy key is present in the specialist prompt and the
conditional instruction to review only that key. Therefore the observed
whole-batch assessment cannot be attributed to missing argument substitution
in these captures. Directory-wide input availability and advisory prompt scope
remain integration/model-behavior concerns; no harness fault or scope fix is
established from those facts alone. No S1/S2 source or benchmark pin changed.
