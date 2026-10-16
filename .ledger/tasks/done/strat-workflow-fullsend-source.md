# Use the Fullsend S1 fork in the Markov benchmark

User request: point the current strat-creator Markov flow at upstream PR #85,
from `jctanner-fullsend-ai/strat-creator`, branch `feat/s1-workflow-hardening`.
Both remote refs were verified at
`6a05210215247b287bb0fb61ed02e423c9de8692` on 2026-10-15.

## Scope

- Update both current S1 hardening tiers to the new HTTPS repository and exact
  branch-head commit, retaining reproducible pins and historical A/B baselines.
- Propagate the repository to both seeding and execution, including the seed
  helper's own clone. Record the selected repository with run provenance.
- Retain existing run counts, models, batch size, concurrency, timeout and
  archival guards. Do not launch a model run or reset shared state.
- Validate source access and offline Markov rendering, commit/push the required
  Breadboard source, sync project 1 in Markovd and verify its imported definition.

## Validation

The public HTTPS fork ref is reachable; upstream PR #85 and the fork
branch match the already tested local port. That port passed 1,005 component
tests with seven skips. No component source edit is needed for this rewiring.

Both S1 hardening tiers now select the requested repository and exact candidate.
The seed job receives the same source as the native execution job. The seed
helper accepts an explicit repository or `STRAT_CREATOR_REPO`; the host reset
helper can pass it too. Seed reports, run summaries and evaluations retain source
provenance. Historical smoke/tier-2 source pins still point to the emulator.

Checks: 72 benchmark tests pass with a freshly built current Markov binary;
`markov validate`, shell syntax and `git diff --check` pass. The old ignored
`checkouts/markov/bin/markov` predates step descriptions, so its initial parser
failures were resolved by building current source to `/tmp/strat-source-tools`.
A read-only seed dry run against the new fork and live Jira validates discovery
configuration and three eligible planned RFEs. The cluster fetched and checked
out the exact commit in a temporary directory, then removed that directory.

Published only the ten benchmark files in Breadboard commit
`54934699e61ee86a1e00117925e3ff3a0b79ae7f` on origin/main. Existing pending
Breadboard notes, credential ignore rule and Model Relay documentation were
left unstaged. The staged credential scan found no private key material.

Synced Markovd project 1 (`ai-first-pipeline`). Its existing directory workflow
`var-benchmarks-strat-workflow` (ID 744) now records source commit `5493469`.
Imported files and both hardening tiers were read back and verified. No model
run was submitted, no shared data was reset, and no inference tokens were spent.
