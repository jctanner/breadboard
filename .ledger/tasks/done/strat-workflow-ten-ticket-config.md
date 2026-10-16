# Prepare a ten-ticket S1 batch with concurrency ten

User request, 2026-10-15: raise the Claude Workflow agent concurrency to ten,
raise the ticket batch to ten and prepare additional distinct fake RFEs.
The reviewer dispatch optimization remains deferred.

## Scope

- Update current S1 hardening GLM/Opus tiers to ten tickets and cap ten, retaining
  source pin 6a05210, one iteration, model policies and archival guards.
- Add a ten-RFE scenario using seven existing independent capabilities and three
  new complete RFE templates. Preserve the one- and three-ticket scenarios and
  historical tier definitions outside the current hardening tiers.
- Exercise real offline Markov rendering, exact ten-key discovery, submitted
  environment/source settings and forty expected reviewer returns.
- Publish the required benchmark source and sync/read back Markovd's imported
  workflow so the configuration is ready to launch.

No model run, Jira reset or live issue creation is part of this preparation.
The next authorized benchmark run's seed step creates the fixture issues after
the existing archive and idle-job checks. No reviewer scheduling change.

Status: done. Published and synced; no model run launched.

## Result and checks

Both current hardening tiers now use scenario batch-ten-new-rfes, BATCH_SIZE=10,
CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS=10 and one iteration, with the same
Fullsend fork and exact 6a05210 component pin. Reviewer Skill dispatch is
unchanged. Historical smoke/tier-2 definitions and one-/three-ticket scenarios
remain available.

The scenario reuses seven existing full RFE templates and adds three fictional
requests: distributed training checkpoint recovery, project connection credential
rotation/readiness, and portable language-model evaluation report export. All
ten have independent problem statements, full acceptance criteria and distinct
summaries/descriptions. Real-run seeding will create them after archival checks.

All 75 benchmark tests pass with the current Markov binary, including real
offline execution of both ten-ticket tiers, rejection of nine discovered keys,
forty reviewer returns with a missing-fortieth negative case, and historical
single-/three-ticket behavior. Markov directory validation and diff checks pass.

Only seven benchmark source/fixture/test files were staged and published in
Breadboard commit 0359a9a394e3f27beee084031958fd91fa932da6. An explicit staged-file
allowlist and credential-pattern scan passed. Other pending repository changes
remain outside that commit.

Markovd project 1 synced and imported workflow var-benchmarks-strat-workflow,
ID 744, from this exact commit. All 64 imported files match the pushed source;
both tier settings were read back. A live read-only seed dry run against local
Jira and candidate source confirms ten distinct eligible planned RFEs. No
reset, issue creation or inference. Operational checks are retained in
/tmp/strat-ten-ticket-config/verification.json and seed-dry-run.json.

## Next run settings

Use the saved tier definitions directly; no run-only tiers JSON override is
needed. GLM remains the iterative model, with Opus requiring separate approval.

```yaml
tier: s1-hardening-glm
only_tests: S1
variants: glm
repeats: "1"
wipe_at_start: "false"
breadboard_ref: 0359a9a394e3f27beee084031958fd91fa932da6
job_timeout: "18000"
workflow_bg_wait_ceiling_ms: "17700000"
```

The native timeout stays 295 minutes. Archive and independently verify the
terminal run before any subsequent seed/reset, including failed runs.
