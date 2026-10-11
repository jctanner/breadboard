# Task: Launch and analyze the first tier 2 S1 pass

## Authorization

2026-10-11: user said "lets proceed ... i want to kick off the single S1
pass" after reviewing the implemented harness. This authorizes publishing
the harness, syncing/importing in markovd, Jira scenario reset/seed, and
exactly one S1 Haiku run. S2 and additional runs require later authorization.

## Acceptance criteria

- [ ] Commit and push the prepared Breadboard changes after validation.
- [ ] Sync/import the benchmark in markovd at that exact commit.
- [ ] Launch `tier2-smoke`, S1 only, Haiku, one repeat, no artifact wipe.
- [ ] Verify seed discovery and actual S1 job/model/commit/batch selection.
- [ ] Record run/job IDs, status, and evidence locations in the plan.
- [ ] After completion, analyze all three items, reviewer returns, actual
      concurrency, usage, context growth, and relay behavior. Stop after S1.

## References

- [Plan and findings](../../plans/strat-workflow-eval-plan.md)
- [Completed harness preparation](../done/strat-workflow-tier2-three-rfe-smoke.md)
