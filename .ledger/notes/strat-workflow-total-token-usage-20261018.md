# Strategy Workflow investigation: cumulative token usage

Through the completed mixed-state run markov-run-bfc0b766 on 2026-10-18,
the estimate is **about 489 million tokens**. The exact recoverable reported
usage is **478,893,465 tokens**; an additional early Haiku run survives only
as a rounded summary of about 10 million tokens. These totals include the
original S1/S2 comparison and subsequent S1 hardening, failed/stopped jobs,
replacement runs, focused real-provider tests and the GLM wiring check.

This is cumulative model-job usage, not the tokens used by Codex/ChatGPT to
develop the code, investigate failures or write reports. It is not an invoice.

## By model

| Model | Exact recoverable reported tokens | Additional rounded estimate |
| --- | ---: | ---: |
| Claude Opus 4.6 | 288,078,188 | 0 |
| GLM 5.3 | 108,686,856 | 0 |
| Claude Haiku, captured ID claude-haiku-5-5 | 82,128,421 | About 10,025,000 |
| Total | **478,893,465** | **About 10 million** |

Both GLM response spellings, zai-org/GLM-5.3 and rits/zai-org/glm-5-3,
are combined. Counts use the provider's reported categories; this does not
establish GLM billing semantics or rates.

## By phase

| Phase | Exact reported tokens | Including rounded early smoke |
| --- | ---: | ---: |
| Original benchmarks, including S1/S2 | 177,477,908 | About 187.5 million |
| S1 hardening and integration tests | 301,415,557 | 301.4 million |
| Total | **478,893,465** | **About 488.9 million** |

The hardening subtotal comprises 209,740,091 Opus tokens and 91,675,466 GLM
tokens. It includes profiling-related live integration runs; model-free
profiling, native controls, checker replays and repeat checks add no inference.

## What was counted

Count input + cache creation + cache read + output, once per API response.
Thinking is already part of output and is not added again. The exact total is:

| Category | Tokens |
| --- | ---: |
| Uncached input | 15,214,670 |
| Cache creation | 49,617,492 |
| Cache read | 404,429,059 |
| Output, including reported thinking | 9,632,244 |
| Total | **478,893,465** |

Approximately 94.8% of this reported total is cache creation/read input.
Repeated cached input across agents and requests is usage, not unique text or
the size of one context window. Token categories have different prices.

The accounting covers 47 jobs with exact reported usage and 11,032
usage-bearing calls. One additional job has 181 calls and rounded usage only.
The audit itself made no model calls.

## Sources and checks

1. Read per-job API response dumps from strat-workflow and
   strat-workflow-hardening under private var/run-data. Include focused GLM
   jobs and stopped jobs that have no final eval-result.json.
2. Recover the first retained reference runs from
   strat-workflow/markov-run-02336f23/20261011T143354300275Z/system-state/dashboard-files.tar.gz.
   This contributes original single-RFE references and the quota-aborted Opus
   attempt that a completed-results-only sum would omit.
3. Deduplicate by job and response filename across captures: 870 repeated
   response records removed, zero conflicting values. All 10,473 remaining
   raw usage responses also have distinct message IDs. Their combined total
   is 450,624,083 tokens.
4. Use markovd-cli first to inventory/get original runs. Its step type omits
   output_json, so use the read-only API fallback for saved checker outputs.
   Six additional jobs contribute exact saved usage of 28,269,382 tokens,
   bringing the exact total to 478,893,465. Five are from the original smoke
   campaign; one is from its preceding cancelled launch.
5. The original markov-run-9d30a751 summarize output retains the remaining
   smoke job's rounded row: 181 calls, 8.40M cache read, 1.31M cache creation
   and 315k output. Their sum is approximately 10.025M, giving about 488.9M
   overall. Uncached input for this row is unavailable. Do not present the
   combined estimate as an exact integer.
6. Raw totals agree with all 19 distinct available per-job eval usage summaries.
   Independent sums by job, model, phase and category agree. Authored native
   control responses are excluded; their synthetic usage is not provider spend.

## Estimated cost with GLM free

At the user's requested GLM cost of $0, the cumulative standard global API
list-price equivalent is **about $485**, with a calculated range of
**$481.26–$487.44** for the accounted usage and rounded first smoke.

| Model | Estimated API-equivalent cost |
| --- | ---: |
| Claude Opus 4.6 | $475.02 |
| Claude Haiku 5.5 | $6.24–$12.42 |
| GLM 5.3 | $0 |
| Total | **$481.26–$487.44** |

By phase, S1 hardening accounts for $345.51. The original benchmarks account
for $135.75–$141.93. Failed/stopped runs remain included in their respective
phases. Development-chat usage and the preceding capture gaps remain excluded.

Prices checked against the [official Claude pricing table](https://platform.claude.com/docs/en/about-claude/pricing)
on 2026-10-18. Opus 4.6 uses $5 input, $6.25 five-minute cache creation,
$0.50 cache read and $25 output per million tokens. All 6,475 directly
accessible Opus responses report zero one-hour cache tokens; historical
Opus pricing checks also recorded five-minute creation. Existing recorded
costs for the completed runs agree with this pricing basis.

Haiku 5.5 uses $0.10 input, $0.125 five-minute cache creation, $0.01 cache
read and $0.50 output per million for prompts up to 100,000 tokens. Above
100,000 prompt tokens, all these prices increase fivefold. Prompt length
includes uncached input and both cache categories. Price each request's
entire usage at its applicable tier, not just the excess above the threshold.

The 984 raw Haiku calls include 125 above that threshold and cost $4.69280621.
This calculation reproduces the archived Haiku batch's CLI cost of
$1.937333395. The six recovered summaries cost between $1.139627695 and
$5.698138475, depending on their unavailable per-request tiers. The remaining
rounded smoke adds about $0.40525–$2.02625. These tier bounds produce the
reported range; missing uncached input for the rounded row is not fabricated.

These are usage equivalents, not actual additional charges. Early tests used
Claude account/OAuth allowances, later tests used Vertex, and no invoices or
subscription allocation were reconciled. Global standard pricing is used;
no discount, tax or infrastructure expense is added. cost-estimate.json in
the private audit directory records the calculation and assumptions.

## Limits

The exact figure is recorded usage, not complete upstream billing. Broken
streams can consume tokens without a captured final usage response. The early
entrypoint job script-strategy-entrypoint-all-claude-haiku-1010-153711-92e255
has a surviving job reference but no recovered usage. Small standalone provider
probes outside the job captures are excluded. No estimate is added for these
gaps, or for this development conversation.

Private, ignored evidence is saved at
var/tmp/strat-workflow-token-audit-20261018/: usage.json, raw-usage-rows.json,
saved-evaluations.json, original-smoke-rounded-summary.txt, verification.json,
the inventory script and a checksum manifest. Source archives remain unchanged.
