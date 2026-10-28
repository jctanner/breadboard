# Task: Establish the existing SME revision contract

## Goal

Trace SME input through the supplied GitLab strat-pipeline source, current
upstream strat-creator main, the existing SME-loop demo and S1 hardening.
Distinguish intended manual reprocessing, scheduled discovery, importing human
input, freshness protection and automatic edit-triggered requeueing.

## Acceptance criteria

- [x] Record inspected repository identities and current upstream main.
- [x] Explain scheduled and manual GitLab job behavior and label handling.
- [x] Trace current-main SME import/refinement/publication and its tests.
- [x] Establish what the existing SME-loop workflow exercises and supplies.
- [x] Compare S1 behavior and identify concrete parity gaps without inferring
      that an intentional human gate is automatically a defect.
- [x] Save findings and correct any overbroad earlier characterization.

## Scope

Read-only source/evidence analysis and model-free checks. No inference, Jira
reset, job submission, feature edits or pushes are authorized by this task.

## Status

Done. GitLab local main is `fd36b15`; upstream `fullsend/main` was refreshed
and is `b3961721822d709034c346d642b533fd9573fcb3`. S1 remains clean at
`6ed858b2294a29457153a90f187a801022c21e8b`.

The existing `var/demos/strat-dashboard-sme-loop-test` was found. It explicitly
clears review labels and supplies an SME-sync prompt between successive
productive refinements, so it is not evidence of edit-triggered discovery.

The historical three-pass demo completed as `markov-run-bb4af08c` on July 31.
Current main documents local pull/edit/refine/review/push; push removes the CI
verdict so the next eligible batch reprocesses. S1 preserves that human loop.
Its new runtime has not yet exercised the actual SME edit/resubmit sequence;
the mixed-state fixture seeded the cleared state instead. Manual approved-ticket
GitLab reprocessing and gate-respecting S1 resume remain distinct entry points.

All 36 model-free checks pass: 17 current-main helper cases, five demo contract
checks, eleven S1 freshness cases, three temporary isolated edit/reopen/pull
probes. No model calls, shared Jira reset, launch or feature modification.

[Full findings](../../notes/strat-sme-revision-flow-20261019.md) and
[hardening plan](../../plans/strat-workflow-s1-hardening.md#existing-sme-revision-contract-audited-2026-10-19).
