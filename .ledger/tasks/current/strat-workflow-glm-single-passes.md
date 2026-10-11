# Task: One GLM single-RFE iteration each of S1 and S2

## Authorization and scope

User authorized 2026-10-11: one GLM run of S1 and one GLM run of S2,
each one RFE and one iteration. Run S1 first, archive and analyze it, then
run S2 separately. Include one tiny job wiring check before S1. No automatic
benchmark retries, sweeps or batch expansion. Preserve S1/S2 pins and real skills.

Use existing Vertex relay project `vertex-shim-local`, routing hosted model
`rits/zai-org/glm-5-3` to `enmaas-personal`. Keep the private EnMaaS key on
the relay. Pin helper and default model aliases explicitly in job env and
use medium effort. Other models must not silently consume Anthropic quota.

## Acceptance criteria

- [x] Add isolated `glm-smoke` tier with one design/repeat/RFE per invocation.
- [x] Validate model identity against exact requests and the verified GLM
      response spelling without relaxing Claude checks.
- [ ] Offline checks; commit/push only required harness changes; sync/import.
- [ ] Run one S1 pass after wiring check; archive all run/system evidence.
- [ ] Analyze S1 before the separately submitted S2 pass.
- [ ] Run one S2 pass; archive and analyze, including failures.
- [ ] Record outcomes in the benchmark plan, without claiming quality parity
      or GLM invoice pricing from Claude client fallback metadata.

## Status

Current. Implementation/validation in progress. Existing unrelated local
changes are preserved. No benchmark launched yet.

## Offline preparation

Markov validate passed; all 26 offline tests passed with real workflow expressions,
including GLM single-arm/repeat guards, explicit helper/effort settings, provider
response aliases and rejected Claude helper calls. Existing tier 1/2 tests pass.
Shell syntax and Python compile checks passed. Service preflight found no active
pipeline jobs or Markov runs. The deployed dashboard already targets the built-in
Vertex relay project. No agent/dashboard/relay rebuild is needed for these
harness-only changes; imported/pushed scripts supply the GLM-specific settings.
