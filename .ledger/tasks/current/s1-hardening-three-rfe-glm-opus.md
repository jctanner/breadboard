# S1 hardening: three-RFE GLM batch, then conditional Opus batch

Authorized 2026-10-14: run one three-ticket batch through markovd with GLM.
Run one matching `claude-opus-4-6` batch only after GLM succeeds and its complete
archive verifies. No extra repeats or paid wiring probe.

## Source and workload

- Hardened S1: `eval/s1-hardening`,
  `0e7e752702727076818001d3a29208532b40dbab`, local GitHub emulator.
- Add separate hardening tiers to the existing Markov directory workflow;
  preserve historical S1/S2 pins and tier definitions.
- Existing distinct three-RFE scenario: workbench culling exemptions, pipeline
  retention, scheduled feature-store materialization.
- GLM primary/helpers/aliases: `rits/zai-org/glm-5-3`, medium effort.
- Conditional Opus primary/helpers/aliases: `claude-opus-4-6`, high effort.
- One run per model; no artifact wipe. Archive guards precede Jira reset.

## Checks

- [ ] Offline Markov checks verify the new tiers, exact source, selection and model wiring.
- [ ] Publish benchmark harness, sync/import in markovd and verify source identity.
- [ ] Launch one GLM Markov run and retain available evidence.
- [ ] GLM completes all three strategies with 12 substantive reviewer reports,
  matching numeric verdicts/Jira records, valid completion and released locks.
- [ ] Final GLM archive under private `var/run-data` verifies before another reset.
- [ ] If GLM passes, launch one Opus Markov run on the same source/scenario.
- [ ] Archive, verify and analyze Opus, including failure if any.

## Status

Preparing the Markov harness. Fullsend/OpenShell deployment and strategy-content
judging remain separate qualification. Existing unrelated changes are preserved.

[Hardening plan](../../plans/strat-workflow-s1-hardening.md).
