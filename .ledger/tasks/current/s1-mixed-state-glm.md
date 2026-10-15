# Task: Run one mixed-state S1 batch with GLM

## Goal

Exercise fresh processing, existing STRAT import, verified review-only recovery,
stale/missing proof, human gates and repeat safety in one retained scenario.

## Acceptance criteria

- [x] Publish the agreeing-recommendation fix and pin its exact commit.
- [x] Validate 18 RFEs and 11 STRATs with real review-only push provenance locally.
- [ ] Confirm discovery, acquisition, skips and resume points before inference.
- [ ] Run one GLM batch at limit ten and agent concurrency ten.
- [ ] Check side effects and repeat preparation without another model call.
- [ ] Archive and independently verify all evidence, including failures.

## Decisions

The human-sign-off-only control consumes a discovery slot before preparation
skips it. Preserve this behavior: ten candidates, nine acquired, one actionable
RFE deferred. Repeat preparation must exclude completed work and preserve the
deferred RFE, rather than claim that all Jira work is exhausted.

## Evidence

Parser fix published as strat-creator fbc335bedb4a4eb97265da89d36bc29009a41fde.
Before publication: 1,033 tests passed, seven skipped; unit suite 575 passed,
five skipped. No additional component behavior changes for fixture preparation.

Offline validation: 89 benchmark tests pass (one optional integration skipped in
that suite), including actual Markov expression execution. The optional real
local Jira emulator suite separately passes all eight tests, including genuine
preparation/push, import verification and repeat preparation, with no model calls.
Ruff, shell syntax and git diff --check pass. Six retained benchmark job archives
plus the cancelled GLM capture were independently verified before the live reset.
Logs: /tmp/strat-mixed-benchmark-tests.log, /tmp/strat-mixed-local-integration.log,
/tmp/strat-mixed-prior-check.log.
