# ADR-0006: Scope the entrypoint POC to Claude and strategy pipeline fidelity

## Status

Accepted by explicit user direction.

## Decision

Implement Claude entrypoint/runtime support only for now. The POC should
replicate the current strat-pipeline inside the Fullsend sandbox as closely
as possible, reusing its helpers and deterministic orchestration. Make only
necessary adaptations and record behavioral differences.

## Consequences

Codex/Pi entrypoint bootstrap, child invocation, and telemetry adapters are
deferred and do not gate M3 or the POC. Preserve their existing agent-led
behavior. Common entrypoint validation and execution remain reusable; reject
unsupported selections explicitly. Do not describe this scoped feature as
the complete implementation of ADR 127.

See the [POC plan](../plans/fullsend-entrypoint-strategy-poc.md).
