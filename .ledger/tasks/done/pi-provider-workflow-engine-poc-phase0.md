# Task: pi provider workflow-engine POC — Phase 0 contract study

## Goal

Produce the Phase 0 deliverable for
[pi-provider-workflow-engine-poc](../../plans/pi-provider-workflow-engine-poc.md):
a written contract-study notes file with excerpts of the pi provider/stream
event shapes, fullsend's event-parser and metrics expectations, the usage-file
format and folding invariants, the harness/plugin validation path, the
Option-B dispatch internals, and the test-container/relay wiring. No
workflow-engine implementation, no fullsend runs.

## Acceptance criteria

- [x] pi provider/stream contract documented with excerpts (Provider
      interface, a real stream implementation's event shapes, `--mode json`
      normalized output, extension API surfaces used: registerProvider,
      tools, session_start/session_shutdown, event bus).
- [x] fullsend expectations documented: pi_progress.go event mappings and
      stall watchdog counting, agent_end ResultEvent metrics fields,
      pi_subagents.go usage-file format + foldPiSubagentUsage invariants.
- [x] Harness/plugin validation path (plugin_spec.go, injection scan)
      documented enough to pre-clear the extension tree.
- [x] Option B: createAgentTool dispatch internals (env, gateway config
      copy, usage record, slots) + pi RPC mode command set excerpted.
- [x] Test container + relay models.json wiring sketched; relay GLM
      surface verification either done (minimal) or explicitly deferred
      to Phase 1 start with reason.
- [x] Notes file written; exit criteria recorded; plan/task updated.

## Boundaries

Read-only study of the fullsend checkout (6316706f2) and the pi install
tree. No inference runs, no cluster changes, no commits.

## Status

Done. Notes at
[pi-provider-workflow-engine-poc-phase0](../../notes/pi-provider-workflow-engine-poc-phase0.md).
Key findings: pi 1.1.0 wire format is compatible with fullsend's 0.84/0.85
parser (additions ignored); Risk 2 resolved (extension tools must be named
in --tools / the agent tools list); plugin env deny-list forbids *_API_KEY
names (relay credential must be e.g. WORKFLOW_RELAY_KEY); plan fact 3
partial — the stall watchdog (FULLSEND_STALL_TIMEOUT) is not in either
available tree, R3's premise unverified; grounding sha 6316706f2 does not
resolve, re-pinned to a734637c; pi 1.1.0.
