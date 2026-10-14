# Task: pi provider workflow-engine POC — Phase 1 standalone pi

## Goal

Implement and verify the Phase 1 deliverable of
[pi-provider-workflow-engine-poc](../../plans/pi-provider-workflow-engine-poc.md):
the `workflow-engine` extension (provider + tool + demo pipeline), the
scripted `test-child` provider, the test container, and the check script —
3/3 deterministic runs with the check script green, children recorded in the
usage file, zero parent usage. Then one real-children pass via relay GLM
(Layer 4) if the cluster is available.

## Acceptance criteria

- [x] `workflow-engine` extension: provider `workflow-engine/v1` (zero-cost
      model, deterministic two-turn stream), `workflow` tool executing the
      demo pipeline (ingest → fan-out children with concurrency 2 →
      aggregate + completeness).
- [x] `test-child` scripted provider: deterministic classification child,
      zero inference.
- [x] Host smoke passes (scratch HOME; host pi untouched).
- [x] Container built (podman, pi pinned 1.1.0, dedicated network); 3/3
      deterministic runs inside it via the check script.
- [x] Check script asserts: exit 0, event sequence (tool call, tool result,
      final message), zero parent usage, 3 usage-file records, artifact
      completeness, byte-identical normalized event streams across runs.
- [x] Layer 4 relay-GLM pass, or explicit deferral with reason.
- [x] Plan/task/session-log updated; exit criteria recorded.

## Status

Done. POC tree at var/demos/workflow-engine-poc (extension, test-child,
check script, Containerfile, README). Results: 3/3 deterministic container
runs (Layers 1-3, offline, byte-identical normalized streams) and a Layer 4
pass with real GLM children through the relay — usage records carry real
tokens matching the relay's telemetry exactly (independent usage oracle).
Parent usage zero throughout. Implementation findings (registration
placeholders, partial block types, child stdin/PI_* hygiene, host-gateway
wiring, relay client-key grants) recorded in the POC README. Relay client
key minted per-run via the admin API, passed only as an env var; no key
material in the repo or run dirs (verified).
