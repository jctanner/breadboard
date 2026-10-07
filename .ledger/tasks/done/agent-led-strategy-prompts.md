# A2: Native strat-single and strat-batch agents

Depends on [A1 checkout synchronization](agent-led-strategy-foundation.md). Follow the
[prompt contract](../../plans/fullsend-agent-led-strategy-poc.md).

## Acceptance criteria

- [x] Follow the native harness imported by rfe-autofixer and existing
  rfe-creator prompt conventions. Record source references; target the same
  released Fullsend configuration. No separate infrastructure smoke gate.
- [x] Add `.fullsend/config.yaml`, `strat-single/prompt.md`,
  `strat-single/strat-single.yaml`, `strat-batch/prompt.md`, and
  `strat-batch/strat-batch.yaml`. Use native `agent:`/Claude, exact model and
  subagent pins, normal hooks, supported providers and validated local policy.
- [x] Add shared setup/post scripts, result schema and validator as needed.
  Reuse existing skills and Python helpers; carry necessary fixes with provenance.
  No custom script entrypoint or nested fullsend-claude phase launcher.
- [x] Port single/batch ordering, gates, owned-lock context, persistent progress
  and current-run scoping. Keep final publication in trusted deterministic
  helpers; validate actual outputs rather than claimed counts.
- [x] Test headless inputs, phase order, partial/blocked/no locks, multiple
  items, old artifacts, missing context, invalid/false-completed output,
  failure cleanup and reconciled resume without duplicate Jira creation.
  Begin with one agent attempt unless safe native retry is proven.
- [x] Run component-required checks, document invocation and recovery, and
  `git diff --check`. Commit/push the new fork branch and record its SHA.

## Breakpoints

Stop at each one and wait for an explicit go, pivot, or stop.

| # | What you get | How to check | Question |
| --- | --- | --- | --- |
| B2.1 | `.fullsend/` config, strat-single harness/prompt, pre/post scripts, result schema, host validator, outer-cleanup script; fixture tests | `make test`; run the validator and cleanup script against the fixtures listed in the handoff | Is the split right: agent locks via helper and records owned keys straight into `$FULLSEND_OUTPUT_DIR`; host validator checks artifacts; outer CI unlocks from that record? |
| B2.2 | strat-batch harness/prompt; resume/reconcile path; emulator-backed tests for partial/blocked/no locks, several items, old artifacts, resume without a second clone | `make test`; named tests in the handoff | Are batch ordering and resume semantics right before docs and push? |
| B2.3 | Invocation/recovery README, provenance, pushed fork branch SHA | `git ls-remote`; read the README | Go to A3? |

## Verdict log

| Breakpoint | Verdict | Date | Notes |
| --- | --- | --- | --- |
| B2.1 | Go, with pivot | 2026-10-07 | Split accepted. Pivot: host-side locking and discovery (see ADR-0012 amendment). First B2.2 change. |
| B2.2 | Go | 2026-10-07 | Batch order and failure/resume rules accepted. Stay on Fullsend 0.43.0; v0.45.0 checked, no pre-script `FULLSEND_RUN_DIR` or always-run hook, so no benefit. |

## Design notes

- Fullsend 0.43.0 runs `post_script` only after validation passes
  (`internal/cli/run.go` ~1692), and deletes the downloaded repo on exit
  unless `--keep-sandbox`. Iteration output files are extracted after every
  agent run, pass or fail (~2332). Lock release therefore cannot live in the
  post-script, and the owned-lock record must be written to
  `$FULLSEND_OUTPUT_DIR`, which the outer CI cleanup reads after `fullsend run`
  returns. Hard sandbox or runner loss still needs Jira reconciliation.
- `strategy-create` Path A imports an existing Cloners-linked STRAT instead of
  cloning again, which is the basis for resume without duplicate creation.

## B2.1 handoff (2026-10-07)

Uncommitted in the checkout on `feat/fullsend-agent-led-strategy`:
`.fullsend/` (config, `strat-single/`, `shared/`, `SOURCE-PROVENANCE.md`),
`tests/test_fullsend_agents.py` (43 tests) and the carried
`scripts/fetch-architecture-context.sh` fix. `make test` 811 passed,
1 skipped; `make lint` clean; `git diff --check` clean. Released Fullsend
0.43.0 `fullsend lock strat-single` resolves the harness (one benign
`.env.d`/`env.sandbox` coexistence warning, as in rfe-creator's harness).

Shape: host pre-script does a read-only eligibility check and fetches
architecture context (no work -> exit 78, no sandbox, no model, skipped
record in `$FULLSEND_RUN_DIR/preflight-result.json`); the agent locks via
`lock_issues.py --locked-keys-file $FULLSEND_OUTPUT_DIR/owned-rfe-ids.txt`,
keeps progress with `state.py` in the output dir, and runs create, refine,
`push_refined_strategies.py`, review; the host validator checks result
claims against the owned record, progress, artifacts and Jira; the
post-script hands off regular artifact files and publishes; the outer CI
runs `release-locks.sh` after `fullsend run` regardless of outcome.

Open question for the verdict: `lock_issues.py` truncates the owned file on
each call, so a second lock call by the agent could orphan locks; the prompt
says lock once. A Jira backstop (release preflight-eligible keys that are
locked after the run) would also cover sandbox loss, but is only safe while
strategy jobs are serialized. Not built yet.

## B2.2 handoff (2026-10-07)

Still uncommitted on `feat/fullsend-agent-led-strategy`. Host-side locking
and discovery are in place, and strat-batch has been added:

- `shared/prepare_run.py` (replaces `preflight.py`) takes candidates from
  `RFE_KEY` or `list-rfe-ids.py --jql-default` (size, offset and expected
  bound), calls `lock_issues.py lock --locked-keys-file` once, and writes
  `$STRAT_STATE_DIR/run.json` plus `owned-rfe-ids.txt`. The agent input is
  `tmp/strat-input.json`. Nothing locked -> exit 78 and a
  `preflight-result.json`. It refuses a state directory that still holds
  live locks.
- `pre-strategy.sh` order: clean, settings, context (optional
  `STRAT_ARCHITECTURE_CONTEXT_PATH`), then lock. A context failure takes no
  locks.
- The validator checks results against the host run record. It rejects
  claims that differ from it, extra locks, strategies for unlocked RFEs,
  unaccounted, double-counted or foreign keys, and agent-reported `skipped`
  while locks are held.
- The prompts read `tmp/strat-input.json` and never lock. strat-batch runs
  create once over the batch, then refine all, push once and review all; any
  unrecovered failure is a `failed` result.
- `release-locks.sh <state-dir>` releases the record and renames it
  `.released`.
- Fullsend 0.43.0 does not pass `FULLSEND_RUN_DIR` to the pre-script, which
  is why `STRAT_STATE_DIR` is an explicit runner variable.

Checks: 62 tests in `tests/test_fullsend_agents.py`; `make test` 830 passed,
1 skipped; lint clean; `git diff --check` clean. Released 0.43.0
`fullsend lock` resolves both harnesses.

Covered by emulator-backed tests: partial, blocked and no locks; several
items; processed exclusion; size, offset and expected bound; old artifacts;
missing context; false-completed output; an existing STRAT is rediscovered
and must be reused, never cloned again; the full pre-script; lock-release
round trip. Not covered until A3: the prompts themselves, since no model
runs in A2.

A3 must provide `STRAT_STATE_DIR` and `STRAT_RUN_ID` in CI, and must run
`release-locks.sh "$STRAT_STATE_DIR"` after `fullsend run` in every case.

## B2.3 handoff (2026-10-07)

Committed and pushed `feat/fullsend-agent-led-strategy` at
`508ea33c0c024a459ffbef3179a08e8ddd8ea3e6` (one commit on upstream `main`
`cc1ba8c`). Verified with `git ls-remote origin`. 27 files: `.fullsend/`
(README with invocation, outcomes, policy and recovery;
SOURCE-PROVENANCE.md; config; both harnesses and prompts; shared host
scripts; carried publication helpers), `tests/test_fullsend_agents.py`, and
the `fetch-architecture-context.sh` fix. On the committed tree: `make test`
830 passed, 1 skipped; `make lint` clean; `git diff --cached --check` clean.
Runtime stays on Fullsend 0.43.0.

## Status

Done, 2026-10-07. A3 waits for an explicit go. Prompts control workflow progression;
helpers remain tools.
