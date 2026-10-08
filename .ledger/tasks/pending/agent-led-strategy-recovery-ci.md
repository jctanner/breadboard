# A6: Recovery paths proven in CI

Follows [A4](../done/agent-led-strategy-batch-events.md). Plan:
[agent-led strategy POC](../../plans/fullsend-agent-led-strategy-poc.md).

## Goal

Observe, in real pipelines, the recovery paths that A4 proved only in unit
and emulator tests.

## Context

- **In-run retry:** fork `9350c89` adds `validation_loop.max_iterations: 2`
  with resume from `tmp/strat-progress.yaml`, as in rfe-creator. The
  mid-batch `end_turn` from pipeline 2083 did not recur in 2084 or 2086, so
  iteration 2 has never run in CI
  ([bug](../../bugs/open/agent-led-batch-ends-turn-after-skill-report.md)).
- **Locks:** partial and blocked locks are covered by `TestPrepareBatch`
  and `TestPrepareSingle` against the emulator, not in CI.
- **Recovery finding (2086):** a cross-run recovery re-refines and re-pushes
  a strategy that has no verdict label, because the skills skip only
  verdict-labelled work. Accepted for A4; not a change target here unless
  the user decides otherwise.

## Acceptance criteria

- [ ] Decide (breakpoint) how to make iteration 1 end without a result.
  Check rfe-creator first; prefer an existing mechanism over a new test
  hook, and keep any hook off by default and out of normal pipelines.
- [ ] One strat-batch pipeline runs iteration 2, which resumes from the
  recorded markers: no second clone, no repeated refine, push or review
  for completed strategies, and a validated, published result.
- [ ] Partial lock in CI: one of two eligible RFEs carries the lock label
  before the run; the batch processes only the other and leaves the label.
  Blocked: all candidates locked gives a native skip with no model run.
  Temporary labels are removed afterwards.
- [ ] End_turn bug moved to `fixed/` (or kept open with the evidence if
  iteration 2 does not resume cleanly).
- [ ] Opus 4.6 metadata, redaction, lock release and cleanup verified; no
  schedules or test jobs left; `git diff --check`; fork tests pass.

## Breakpoints

| # | What you get | How to check | Question |
| --- | --- | --- | --- |
| B6.1 | Proposed way to force iteration 1 to fail, compared with rfe-creator | Ledger note, diff if any | Use this mechanism? |
| B6.2 | Real pipeline that runs iteration 2 and publishes | Per-iteration output, progress markers, Jira history | Did resume repeat nothing? |
| B6.3 | Partial- and blocked-lock pipelines | Traces, Jira labels before and after | Close A6? |

## Verdict log

| Breakpoint | Verdict | Date | Notes |
| --- | --- | --- | --- |

## Files likely involved

- `checkouts.fullsend_agent_led_poc/jctanner.strat-creator/.fullsend/`
- `var/demos/fullsend-agent-led-poc/{publish.py,seed_rfe.py}`

## Status

Pending, 2026-10-08.
