# Task: CC-75 Initiatives test scenario and demo on w530

## Goal

Mirror the Initiative pipelines and repos (strat-pipeline, strat-creator,
rfe-creator/rfe-autofixer, epic-creator/epic-decomposer) into breadboard on w530,
seeded with fully synthetic Initiatives. The result is both a test scenario and
an end-to-end demo.

## Plan

[cc75-w530-initiatives-scenario-plan.md](../../plans/cc75-w530-initiatives-scenario-plan.md)

## Status

2026-11-16: phase 2 has started. S0, S1, S1b and the S2 gateway smoke are done (see the plan's "Phase 2 progress").
Model-free scenarios through S4 pass, and the relay route and sandbox egress are in place. S6 (dry strategy canary) passes through Model Relay. S7 is next; S5 and S8 need their own adaptations.

Blocked on human review of the phase 1 plan, and on w530 being unreachable
(2026-11-15). Model scenarios also wait on the human configuring Claude
credentials in w530's Model Relay (plan §7).

## Acceptance criteria

- [x] Inventory: what's needed and what's available; prior work reviewed (phase 1)
- [x] Human approves proceeding (2026-11-15); Q4 and R6 settled by the code; Q1 recommendation: #124
- [x] Human configures the relay upstream account (`rh-vertex-strat-evals`)
- [x] Route a relay project to it (`cc75-initiatives`, approved 2026-11-16)
- [x] Human: enable `claude-opus-5-5` in the `rh-vertex-strat-evals` inventory (2026-11-16)
- [x] glab working for the private GitLab sources (2026-11-16)
- [x] S0, S1, S1b, S2 gateway smoke, S3, S4 pass without a model (S9 pending)
- [ ] S5–S8, S10 pass with a model; evidence recorded (S6 passed 2026-11-16)
- [ ] Demo rehearsed
