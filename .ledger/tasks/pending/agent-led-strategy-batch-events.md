# A4: Native strategy batch and Fullsend event dispatch

Depends on [A3 single CI](../done/agent-led-strategy-single-ci.md); use its tested release.

## Acceptance criteria

- [ ] Extend `.gitlab-ci.yml` on the existing strat-pipeline project's
  `feat/fullsend-agent-led-poc` branch; add batch-discover CI calling native
  strat-batch with JQL gates,
  size/offset, candidate bounds and resource_group strat-batch.
- [ ] Seed two fresh distinguishable RFEs. One agent run processes the acquired
  subset in native order, excludes processed work, and creates two linked
  strategies, refinements, truthful reviews and output mappings.
- [ ] Verify actual 4.6 model metadata, validated phases/artifacts, lock release,
  results/summary, Org Pulse and refreshed dashboard, redaction and runtime cleanup.
- [ ] Determine the selected release's supported native event interface and
  existing producer/schema. Configure supported native triggers; prove matching,
  input mapping and
  actual dispatch of single versus batch events through the selected existing
  path. Missing/ambiguous input must not launch unintended writes. Direct CLI
  invocation alone is insufficient evidence of event dispatch.
- [ ] Exercise no-work, partial locks and interrupted-phase recovery using
  bounded fixtures; resume/reconcile without duplicating completed effects.
- [ ] Run required checks and `git diff --check`, commit/push/publish changes,
  and record pins, pipeline/job IDs and comparison with the script-led POC.
  Leave no test job or unattended recurring schedule active.

## Status

Pending. Batch-selected and reprocess-strat remain outside this POC.
