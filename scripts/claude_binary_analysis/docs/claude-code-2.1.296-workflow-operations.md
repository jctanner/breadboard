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
resume phase added. All outcomes are checked by an executable verifier.

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

## Control 6: retries and incomplete streams

With `CLAUDE_CODE_MAX_RETRIES=1` and a single injected fault after the
counter side effect:

| Fault | Outcome | Side-effect executions |
| --- | --- | --- |
| HTTP 429 + `Retry-After: 0` | retried once, completed | 1 |
| HTTP 500 | retried once, completed | 1 |
| Broken SSE stream (`message_start`, then close) | retried once, completed | 1 |
| Persistent 500 until exhaustion | journal `launched, started, failed`; workflow `completed` with result `null`; exit 1, `is_error` final result | 2 (conversation restarted once) |
| Delayed response past `stallMs` (single) | fresh agent conversation (new `agentId`, same key); completed | 2 |
| Delayed response past `stallMs` (persistent) | five recovery iterations (six executions), journal `failed`, workflow `failed`; exit 0 with `success` result event | 6 |

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
  twenty-three checked outcomes, including the three crash-resume cases.
- Runners: `run_workflow_operations_experiments.py` (23 cases) and
  `run_workflow_crash_resume_experiments.py` (crash-resume completion);
  verifier: `verify_workflow_operations_controls.py`. See
  [the tooling README](../README.md).
- Immutable traces under `tmp/claude-code-binary-analysis/2.1.296/traces/`:
  `workflow-operations-<case>-v1` for the original cases and
  `workflow-operations-crash-<case>-resume-v1` for the completed crash
  controls. Each retains the runner, manifest with binary/runner hashes and
  fixture provenance, per-phase command/env, API captures, journals, config
  snapshots, stdout/stderr and debug logs.

Every claim above is runtime-confirmed against the pinned binary except
where marked "not exercised".
