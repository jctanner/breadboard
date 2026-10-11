# Task: Launch and analyze the first tier 2 S1 pass

## Authorization

2026-10-11: user said "lets proceed ... i want to kick off the single S1
pass" after reviewing the implemented harness. This authorizes publishing
the harness, syncing/importing in markovd, Jira scenario reset/seed, and
exactly one S1 Haiku run. S2 and additional runs require later authorization.

## Acceptance criteria

- [x] Commit and push the prepared Breadboard changes after validation.
- [x] Sync/import the benchmark in markovd at that exact commit.
- [x] Launch `tier2-smoke`, S1 only, Haiku, one repeat, no artifact wipe.
- [x] Verify seed discovery and actual S1 job/model/commit/batch selection.
- [x] Record run/job IDs, status, and evidence locations in the plan.
- [ ] After completion, analyze all three items, reviewer returns, actual
      concurrency, usage, context growth, and relay behavior. Stop after S1.

## References

- [Plan and findings](../../plans/strat-workflow-eval-plan.md)
- [Completed harness preparation](../done/strat-workflow-tier2-three-rfe-smoke.md)

## Live run

Started 2026-10-11 13:47:49 UTC: `markov-run-02336f23`, Breadboard
`2cf4540113a38fbbed7e3366e55ce84e942ea40e` (pushed and imported).
Seed job `script-seed-scenario-all-claude-haiku-5-5-1011-134751-1e1732`
completed; exact discovery RHAIRFE-1/2/3 passed.
S1 job `script-run-workflow-all-claude-haiku-5-5-1011-134802-315418`
started at 13:48:02 UTC, native batch mode on pinned S1 `1bd7f17`.
Markov completed at 14:18:35.968 UTC; the S1 job failed validation.
Three distinct strategies were created. Evaluation reports `pass=false`:
finished, steps_done, one_review, records_agree, and reviewer_outputs_returned
failed. RHAISTRAT-1/3 have revise 4/8 reviews; RHAISTRAT-2 has no returned
review. Native summary: Claude exit 0, validation exit 1, final exit 1.
Immediate cause confirmed from raw API records: RHAISTRAT-2 refine saved
successfully but returned a JSON string inside `recorded`, so S1's exact-key
comparison excluded it from scoring/review. Also reproduced reviewer prose
loss: 14/16 calls returned only `Skill execution completed`. Full concurrency,
usage, context growth, and reviewer transport analysis remain pending.
Final evidence is verified under
`var/run-data/strat-workflow/markov-run-02336f23/20261011T143354300275Z/`,
with directly browsable API dumps, strace, and job artifacts.
No wipe, S2, or repeat; do not automatically start another run.
