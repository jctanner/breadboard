# Bug: strat-batch agent ends its turn after a skill's user report

## Summary

In headless mode, Claude ends the session on `end_turn`. After the
`strategy-review` skill finished for the first strategy of a batch, with its
"Step 8: Advise the User" summary, the parent agent wrote "Now review
RHAISTRAT-14" and then stopped with `stop_reason: end_turn`. The second
review and `agent-result.json` were never produced.

## Reproduction

Pipeline 2083 / job 4044: a schedule-started strat-batch run at fork
`a2b888a`, with `BATCH_EXPECTED_KEYS="RHAIRFE-13 RHAIRFE-14"`. The agent
ran for 1551.9 s over 74 turns ($7.90); all 107 parent messages were
`claude-opus-4-6`.

## Expected

Review both strategies, record `phase_review`, write the result, validate
and publish.

## Actual

- **Phases:** `strat-progress.yaml` records create, refine and push, with
  mappings 13 -> RHAISTRAT-13 and 14 -> RHAISTRAT-14. No review phase.
- **Validation:** "output/agent-result.json not found". The post-script was
  skipped and nothing was published.
- **Locks:** release-locks unlocked RHAIRFE-13 and RHAIRFE-14.
- **Jira:**
  - RHAISTRAT-13 is complete: auto-created, auto-refined and rubric-pass
    labels; review attached; comment posted.
  - RHAISTRAT-14 was created, refined and pushed (auto-created and
    auto-refined labels), with no review and no verdict label.
  - Each STRAT is Cloners-linked to its own RFE, and the titles match.

## Impact

High for batch: whether the loop continues past each skill's
"advise the user" step depends on the prompt alone. Single mode was not
affected, because review is its last step before output. The validator
behaved as designed: partial work never publishes.

## Fix (option 3 chosen by the user, 2026-10-07)

Fork `9350c89`; CI repinned, branch head `6e3ab46`.
`validation_loop.max_iterations: 2` with append feedback, as in
rfe-creator.
- **Retry environment:** Fullsend 0.43.0 runs the retry in the same sandbox
  but runs `rm -rf <workspace>/output/*` first (`runtime/claude.go:202`).
- **Progress:** now kept in `tmp/strat-progress.yaml` through
  `.fullsend/shared/progress.sh`, mirrored to the output directory.
- **Prompts:** resume from recorded `phase_` and per-strategy
  `refine_`/`review_` markers; never edit artifacts to pass a check; do not
  end the turn before the result exists.
- **Validator:** requires the per-strategy markers, and tells the retry to
  resume when the result is missing.
- **Checks:** `make test` 839 passed, 1 skipped.

Not yet proven in CI, because the stop is not deterministic; B4.2 or B4.3
must show a real retry. Kept open until then.

### Options considered

1. Harden the prompt only: say that skill reports are not the end, and
   that the turn must not end before `agent-result.json` exists.
2. (1) plus a project Claude `Stop` hook that blocks `end_turn` in CI while
   `$FULLSEND_OUTPUT_DIR/agent-result.json` is missing, with a bounded
   retry count.
3. Use the rfe-creator pattern: `validation_loop.max_iterations: 2`, where
   iteration 2 resumes from progress state. Needs proof that resume
   repeats no Jira effects.

## Related Tasks

- tasks/done/agent-led-strategy-batch-events.md
- tasks/pending/agent-led-strategy-recovery-ci.md (A6: prove the retry in CI)
