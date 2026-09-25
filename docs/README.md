# Breadboard Documentation

## Architecture

System design, component docs, and diagrams.

- [agent-parallelism.md](architecture/agent-parallelism.md) — Two-layer parallelism: orchestrator + agent self-parallelism
- [agent-runner.md](architecture/agent-runner.md) — Pipeline job lifecycle from dashboard to K8s execution
- [cli-runner.md](architecture/cli-runner.md) — CLI runner mode proposal (SDK limitations workaround)

### Diagrams

Mermaid `.mmd` files — render on GitHub or paste into [Mermaid Live Editor](https://mermaid.live/).

- [architecture-overview.mmd](architecture/diagrams/architecture-overview.mmd) — High-level system architecture
- [architecture-infrastructure.mmd](architecture/diagrams/architecture-infrastructure.mmd) — K3s cluster, storage, services, secrets
- [architecture-jobs-runners.mmd](architecture/diagrams/architecture-jobs-runners.mmd) — K8s Jobs, agent runners, skill config
- [architecture-data-flow.mmd](architecture/diagrams/architecture-data-flow.mmd) — Data pipeline from bug fetch to dashboard
- [pipeline-execution-flow.mmd](architecture/diagrams/pipeline-execution-flow.mmd) — End-to-end execution sequence
- [architecture.mmd](architecture/diagrams/architecture.mmd) — Legacy single-diagram view (replaced by above)

## Deployment

- [README.md](deployment/README.md) — K3s deployment quick start, .env setup, troubleshooting

## Fullsend Integration

- [fullsend-integration.md](fullsend-integration.md) — Fullsend services, event flow, token exchange, and sandbox boundaries
- [fullsend-compatibility-profile.md](fullsend-compatibility-profile.md) — every local substitution this deployment makes, and the two credential deviations that need a reviewer's judgement
- [fullsend-openshell-tutorial.md](fullsend-openshell-tutorial.md) — trigger a Fullsend job and watch its OpenShell sandbox
- [fullsend-services.mmd](architecture/diagrams/fullsend-services.mmd) — Fullsend and Breadboard service topology
- [fullsend-event-flow.mmd](architecture/diagrams/fullsend-event-flow.mmd) — GitHub event, Actions, OIDC, mint, and agent sequence
- [fullsend-agent-sandbox.mmd](architecture/diagrams/fullsend-agent-sandbox.mmd) — Agent sandbox mounts, egress policy, and artifacts

## Reference

Stable reference material.

- [CONVENTIONS.md](reference/CONVENTIONS.md) — Agent skill analysis: parallelism, idempotency, consistency
- [arch-query-design.md](reference/arch-query-design.md) — arch-query CLI design document
- [arch-context-testing.md](reference/arch-context-testing.md) — Benchmark corpus tiers, judge rubric, MLflow structure
- [data-sources-and-access.md](reference/data-sources-and-access.md) — Pipeline data sources, field mappings, access methods
- [mlflow-basics.md](reference/mlflow-basics.md) — MLflow evaluations with Claude via Vertex API
- [mlflow-claude.md](reference/mlflow-claude.md) — Claude Code tracing via MLflow autolog

## Reference (top-level)

- [vertex-claude-runtime.md](vertex-claude-runtime.md) — Vertex AI Claude runtime wiring
