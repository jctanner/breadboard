# Task: Diagram the benchmark workflow

## Goal

Add a high-level Mermaid overview to the benchmark README, showing Markov
coordination, alternative job designs, result checks and separate host archival.

## Acceptance criteria

- [x] Match the checked-in main, round, variant, run-test and wipe workflows.
- [x] Show sequential selections and one design per test.
- [x] Keep failed-job checks, archive guards and host collection clear.
- [x] Render the diagram and check documentation formatting.
- [x] Keep the session log empty; no inference or deployment.

## Status

Done, 2026-10-12.

## Evidence

- Added a Mermaid flowchart near the beginning of the
  [README](../../../var/benchmarks/strat-workflow/README.md#workflow-overview).
- Compared the graph against main.yaml, round.yaml, test-variants.yaml,
  run-test.yaml and wipe.yaml. The branches are selected designs, while the
  return edge represents sequential repeats/tests/models.
- Shown archive guards before resets and a separate host collection handoff.
  Caption explains that missing receipts stop a reset and failed design jobs
  still reach the checks. Host collection is not depicted as a Markov step.
- Mermaid CLI successfully rendered a temporary PNG; visually checked labels,
  branch/loop edges and the dashed host handoff. No generated image is added
  to the repository. git diff --check passes; session log remains empty.
- No model calls, workflow execution, deployment, commit or push.
