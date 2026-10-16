# Claude Code 2.1.296 workflow operations: recovery, cancellation, limits, retries

Investigated 2026-10-12 against the pinned Linux x64 binary
(SHA-256 `24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`).
This completes the remaining production controls (3–7) of the
[production-gap handoff](../../../.ledger/notes/claude-workflow-production-gaps-handoff.md):
crash recovery and side effects, cancellation and deadlines, budget and
concurrency enforcement, retries and incomplete streams, and replay with
changed shared state. Twenty-three cases were run by
`run_workflow_operations_experiments.py`; the three crash cases captured only
their crash boundary there (the runner could not derive a resume handle
without a workflow state file, which an external SIGKILL never leaves), so
`run_workflow_crash_resume_experiments.py` re-ran them with the fresh-process
resume phase added. Four further network-fault cases (persistent rate limit,
connection reset, spend-limit 429, 529 overload) were run by
`run_workflow_network_fault_experiments.py`. All outcomes are checked by an
executable verifier.

## Headline results

1. **Recovery is at-least-once for any agent without a journaled result.**
   After a hard crash, resume re-executes un-journaled agents from scratch,
   including their tool side effects. Journaled results are reused and their
   agents are not re-run. A truncated journal entry is treated as a missing
   result, not as corruption.
2. **Cancellation terminates children.** `TaskStop`, SIGTERM and the
   `--print` background-wait ceiling all stopped in-flight fixture shell
   children; no late writes appeared after any of them. The ceiling kills the
   workflow (state `killed`) rather than detaching it to finish later.
3. **The budget gate fires at agent-launch boundaries and at completion.**
   A final agent (or a single-agent workflow) can exceed `--max-budget-usd`
   and still complete; the failure then surfaces only in the CLI's final
   result event and exit code. Nested Skill fork usage is counted.
4. **Request-level retries are side-effect safe; agent-level restarts are
   not.** Single 429/500/broken-stream faults were retried without duplicating
   a counter side effect. Retry exhaustion and stall recovery restart the
   agent conversation from scratch, re-executing side effects. Stall recovery
   permits five iterations (six total executions) before failing.
5. **Replay does not detect changed shared state.** Resuming with identical
   prompt/options after changing a read file, project instructions and
   discovered skills served the cached journal result unchanged. Freshness is
   the caller's responsibility.

## Method

Same mock-only approach as the earlier workflow controls: fresh
`CLAUDE_CONFIG_DIR`, committed fixture repositories, a deterministic loopback
Anthropic SSE/JSON server, `--print --output-format stream-json
--permission-mode bypassPermissions --max-turns 8`, and no real credentials
or paid model calls. Environment controls per case:
`CLAUDE_CODE_MAX_RETRIES=1`, `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`
(1 or 2), `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=100` for the ceiling case,
and `--max-budget-usd .01` with mocked 50,000-output-token final responses
for the budget cases. Supervisor signals (SIGKILL/SIGTERM) are sent only to
the fixture-owned CLI process, bounded at 45 s; each phase wait is bounded at
30 s. The mock tags every capture with role, injected fault, request message
hash and fixture tool results; phases snapshot config, journals and fixture
side effects (a counter file, a started-PID file, a late-write file).

Mock cost counters are response accounting, not real prices; nothing here
measures provider enforcement, quota allowance or real billing.

## Control 3: crash recovery and side effects

Three SIGKILL boundaries, each followed by a fresh-process resume
(`--resume <session>` plus a new Workflow launch with `resumeFromRunId` and
the persisted `scriptPath`):

| Boundary | Journal at crash | Counter at crash | After resume | Side-effect executions |
| --- | --- | --- | --- | --- |
| During first agent request | `launched, started` | none | completed; new `started`+`result` | 1 (no duplication) |
| After side effect, before result journaling | `launched, started` | `A` | completed; new `started`+`result` | 2 (**duplicated**) |
| After result journaling, next agent started | `launched, started, result, started` | `A` | completed; first agent reused, second re-ran | 1 + 1 (no duplication of the first) |

An external SIGKILL leaves no workflow state file; the state JSON is written
only at terminal transitions. The journal and the persisted script survive,
and `resumeFromRunId` restores from them alone. Each re-execution uses a new
`agentId` under the same journal key.

A truncated journal (last line cut mid-entry) is not detected as corruption:
the affected agent re-executed, a fresh `result` was appended after the
unparseable line, and the workflow completed, with the side effect
duplicated. Two concurrent resumptions of a *completed* run (different
scripts, same journal) both served cached results with no re-execution and no
journal damage. Competing resumptions of an *incomplete* run were not
exercised.

## Control 4: cancellation and deadlines

| Probe | Exit | Workflow state | Late write | Notes |
| --- | --- | --- | --- | --- |
| `TaskStop` on running workflow | 0 | `killed` | no | "Successfully stopped task"; in-flight Bash child terminated |
| SIGTERM to CLI mid-workflow | 143 | none persisted | no | journal left at `launched, started`; a final `success` result event is still emitted for the controller conversation |
| Print bg-wait ceiling (100 ms) exceeded | 0 | `killed` | no | `task_updated` → `killed`, notification `stopped`, task removed; the workflow is killed, not detached |

Logical cancellation (`TaskStop`) and process termination both reached the
actual fixture child: a `sleep 2; late-write` shell started (PID file
present) but never wrote its late marker, verified after a 2.3 s observation
window. The ceiling result is a hard stop: `--print` does not leave the
background workflow running past its wait ceiling. The SIGTERM case's
emitted `success` result event describes only the controller conversation;
the workflow itself died without a terminal state.

## Control 5: budget and concurrency enforcement

With `--max-budget-usd .01` and mocked 50k-output-token agent responses:

- Three-agent parallel workflow: the first agent completed and journaled;
  the gate fired when the *next* agent launched. Workflow `killed`, terminal
  `error_max_budget_usd`, exit 1.
- Single-agent workflow with a nested `context: fork` Skill (also reporting
  50k): the workflow **completed** (journal `launched, started, result`),
  emitted a `success` result event, then a second terminal result
  `error_max_budget_usd` with exit 1 and cost ≥ $2. The nested Skill's usage
  is counted; the gate fires at agent launches and at completion, so a final
  agent can exceed the budget while the workflow still reports completion.

`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` is honored: 1 serialized agent
requests (strict `started/result` alternation in the journal), 2 overlapped
them. A nested `workflow()` child shares the parent's cap globally: parent
agent A plus nested B and C never exceeded two concurrent requests under the
override at 2. In the reversed-delay case the first agent launched alone
before the remaining two overlapped, and journal entry order did not strictly
follow API response order (`started B` precedes `result A` although A
responded first) — the journal is an ordered log of engine transitions, not a
response chronology. Replay of that journal reused every result.

Forked Skill execution has a separate restriction: the Skill tool inherits
`isConcurrencySafe=false`, so four Skill calls from one agent serialize even
when requested in the same response. Two additional native loopback controls
confirm one active child request from one caller versus four active requests
from four Workflow callers at cap five. The outer cap does not override tool
eligibility. [Dispatch rule and controls](claude-code-2.1.296-skill-concurrency.md).

## Control 6: retries and incomplete streams

With `CLAUDE_CODE_MAX_RETRIES=1` and a single injected fault after the
 counter side effect (original controls; the network-fault extension below
uses 2):

| Fault | Outcome | Side-effect executions |
| --- | --- | --- |
| HTTP 429 + `Retry-After: 0` | retried once, completed | 1 |
| HTTP 500 | retried once, completed | 1 |
| Broken SSE stream (`message_start`, then close) | retried once, completed | 1 |
| Persistent 500 until exhaustion | journal `launched, started, failed`; workflow `completed` with result `null`; exit 1, `is_error` final result | 2 (conversation restarted once) |
| Delayed response past `stallMs` (single) | fresh agent conversation (new `agentId`, same key); completed | 2 |
| Delayed response past `stallMs` (persistent) | five recovery iterations (six executions), journal `failed`, workflow `failed`; exit 0 with `success` result event | 6 |

### Network-fault taxonomy and the retry policy

The retry engine was recovered from the exact bundle and confirmed by four
additional controls (`workflow-network-*-v1`, `CLAUDE_CODE_MAX_RETRIES=2`).

**Retry decision (bundle-confirmed).** Network errors without HTTP status
(including `ECONNREFUSED`, `ECONNRESET`, `ETIMEDOUT`, `EPIPE` — the bundle
carries an explicit socket-error taxonomy), 408, 409, SSE failures and
≥500 are retryable. 401 consumes a credential-renewal budget (max 2) before
failing. 404 triggers one retry *without streaming*. 529 (overloaded) counts
into a separate `overloaded` bucket with fallback-model handling after three
repeated overloads, and background queries can be dropped early on 529. 429
is retryable **unless** it carries a spend/usage-limit marker
(`service_spend_limit_reached`, `org_spend_cap_reached`, `out_of_credits`,
`org_level_disabled`…) — those fail immediately.

**Retry budget and backoff (bundle-confirmed).** Default max retries: **300
for first-party auth, 10 for third-party/gateway**; `CLAUDE_CODE_MAX_RETRIES`
is honored but clamped to 15 for non-first-party use. Delay is exponential
with proportional jitter: `min(capMs, baseMs·2^(attempt-1)) + jitter`, cap
32 s by default. `Retry-After` is honored and overrides the computed delay;
a 429 with `Retry-After` ≥ 20 s (or absent) enters a long-wait path of at
least 10 minutes (capped at 30 minutes) that can be woken early, and the
`anthropic-ratelimit-unified-reset` header (capped at 6 h) is also honored.
Separate buckets cap stalls (1), truncations (1), post-thinking failures,
overloads and slept-through suspensions independently of the main retry
count.

**Runtime-confirmed outcomes** (all four fault classes, single-agent
workflow, `CLAUDE_CODE_MAX_RETRIES=2`):

| Fault | Request retries | Conversation restarts | Outcome |
| --- | --- | --- | --- |
| Persistent 429 (`rate_limit_error`, `Retry-After: 0`) | 2 per conversation, backoff gaps 0.53 s → 1.09 s | 1 | journal `failed`; workflow `completed`/null; exit 1 |
| Connection reset (no HTTP response) | 2 per conversation, gaps 0.59 s → 1.21 s | 1 | same |
| Persistent 529 (`overloaded_error`) | 2 per conversation, gaps 0.59 s → 1.06 s | 1 | same |
| Spend-limit 429 (`service_spend_limit_reached`) | **0** — fails in <1 s, no backoff | 1 | same |

The measured gaps confirm the recovered base ≈0.5 s with factor 2. Every
retryable class behaves identically at the workflow level: request-level
retries with backoff, then **one conversation restart from scratch**
(re-executing tool side effects — the counter ran twice in every case), then
a journaled `failed` entry, a workflow that *completes* with a `null` result,
and CLI exit 1 with an `is_error` result. The spend-limit 429 skips
request-level retries entirely — matching the benchmark's real-world
observation that account usage-limit 429s fail jobs outright — but still
gets the one conversation restart before final failure.

### The primary layer is quiescent during execution

In every captured timeline the controller conversation made exactly two API
calls around a background workflow — the launch turn and the launch-receipt
turn — and then **zero requests for the entire execution window**; the wait
is host-side (bounded locally by the background-wait ceiling, or by a blocking
`TaskOutput` call, which is also a local wait). Network errors during
execution are therefore invisible at the primary layer: they are handled
entirely inside the workflow's agent-call retry stack. The primary's exposure
window is the **notification-delivery turn** after the workflow reaches a
terminal state.

The `notify-fault` control exercises exactly that window: the workflow
completed (journal `launched, started, result`; state `completed` with the
result persisted; side effect executed once), and then every
notification-turn request was injected with a 429. The turn received the
same request-level retry engine (three attempts, backoff gaps 0.64 s and
1.20 s) and, on terminal failure, the CLI's final result became
`API Error: Request rejected (429)` with exit code 1 — **despite the
workflow having succeeded and its result being durably journaled**. The
success is recoverable only from the workflow state/journal (or a session
resume), not from the CLI's exit status or result event.

Request-level retries resend the same conversation and do not replay tool
results. Agent-level restarts (retry exhaustion, stall recovery) begin a new
conversation and re-execute tool side effects. The stalled original request
can still be in flight while its replacement runs (two concurrent agent
requests observed). Exhausted stall recovery leaves the workflow `failed`
while the CLI exits 0 with a `success` result event — exit status alone does
not establish workflow outcome.

## Control 7: replay with changed shared state

Resuming with identical prompt/options after changing `context.txt`
(`CONTEXT_v1` → `CONTEXT_v2`), `CLAUDE.md` (`OPS_INSTRUCTION_OLD` →
`OPS_INSTRUCTION_NEW`) and adding a new discovered skill: no agent
re-executed and the cached journal result (`CONTEXT_v1`) was returned
unchanged. Journal/replay keys are derived from the script and agent
prompt/options, not from the files, instructions or skills those agents
read. Detecting stale cache entries is the caller's responsibility.

Out-of-order and concurrent completions (two agents responding within 1 ms)
produced a journal that replayed correctly with all results reused.

## Classification

- **Engine behaviors, production-relevant:** at-least-once re-execution of
  un-journaled agents (crash, truncation, retry exhaustion, stall recovery);
  budget gate timing (launch boundaries and completion, post-hoc failure
  after a completed workflow); print-ceiling workflow kill; `success` result
  events accompanying killed/failed workflows (SIGTERM, stall exhaustion);
  no shared-state change detection on replay.
- **Expected/documented behavior:** request-level retry without tool-result
  replay; journaled-result reuse; global concurrency cap shared with nested
  workflows; `TaskStop` killing children.
- **Not exercised:** competing resumptions of an incomplete run; interactive
  cancellation races; real quota/provider enforcement; remote-isolation
  agents (unavailable in this build).

## Production implications

For the strategy pipeline comparison (S1 native Workflow vs S2 external
runner): neither execution path gets exactly-once side effects for free. S1's
journal replay gives cheap restart, but any agent whose result was not
journaled re-executes from scratch on resume — publication steps must be
idempotent and externally validated, matching the existing recommendation to
persist and validate specialist results outside the workflow boundary. The
budget-gate timing means a budget cap does not bound the work of a final
agent; ceilings and cancellation do terminate children, but CLI exit status
and `success` result events do not reflect workflow outcome in the SIGTERM
and stall-exhaustion paths. These findings strengthen, and do not change,
the production recommendation in the evaluation plan.

## Evidence and reproduction

- [Verified controls](claude-code-2.1.296-workflow-operations-controls.json):
  twenty-eight checked outcomes, including the three crash-resume
  completions, four network-fault cases and the notification-turn fault.
- Runners: `run_workflow_operations_experiments.py` (23 cases),
  `run_workflow_crash_resume_experiments.py` (crash-resume completion) and
  `run_workflow_network_fault_experiments.py` (network faults); verifier:
  `verify_workflow_operations_controls.py`. See
  [the tooling README](../README.md).
- Immutable traces under `tmp/claude-code-binary-analysis/2.1.296/traces/`:
  `workflow-operations-<case>-v1` for the original cases,
  `workflow-operations-crash-<case>-resume-v1` for the completed crash
  controls, and `workflow-network-<case>-v1` for the network faults. Each
  retains the runner, manifest with binary/runner hashes and fixture
  provenance, per-phase command/env, API captures, journals, config
  snapshots, stdout/stderr and debug logs.

Every claim above is runtime-confirmed against the pinned binary except
where marked "not exercised".
