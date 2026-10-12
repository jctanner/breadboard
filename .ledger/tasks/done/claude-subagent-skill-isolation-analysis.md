# Task: Prove or refute subagent skill discovery leaking into the primary agent

## Goal

Investigate the user's observation that subagents exploring an
opendatahub-io/architecture-context checkout cause its skills to become loaded
in the primary agent. Trace exact Claude Code 2.1.296 binary control flow and
separate skill registration, metadata injection, and full instruction loading.

## Acceptance criteria

- [x] Trace file-operation skill discovery and its registry scope.
- [x] Trace subagent/primary command lookup and skill-listing injection.
- [x] Identify agent-scoped state and any shared state that crosses the boundary.
- [x] Correlate available unofficial source without treating it as authoritative.
- [x] Run credential-free controls for a nested fixture checkout if supported.
- [x] Save findings, pseudocode, exact offsets/hashes and evidence under
  `scripts/claude_binary_analysis/docs/`; update its index.
- [x] Validate claims, evidence paths, relevant tooling and whitespace.

## Status

Done. [Report](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-subagent-skill-isolation-analysis.md)
and pseudocode, 38 exact symbol ranges/hashes, nine evidence-labeled claims,
and ten verified runtime controls saved in the documentation home.

Confirmed: child Read discovery changes a host-shared registry, then the
primary receives the discovered skill's availability metadata despite a fixed
child answer without skill details. This reproduces for Explore,
general-purpose and Workflow children. Full bodies stay out of the primary
until a primary Skill invocation in these controls. No read, Bash cat alone,
gitignored checkout and disabled project settings are negative controls.

The local architecture-context layout has fourteen skill files; captured its
HEAD/paths/hashes for correspondence, without modifying or running its skills.
Added an isolated runner and outcome verifier. Python compile checks, ten
controls, claim paths, JSON, thirty documentation links, exact payload hashes
and whitespace passed. No real credentials, paid model calls or deployment
changes. [Issue](../../bugs/open/claude-subagent-discovery-shares-skill-metadata.md)
tracks the shared-registry behavior; no upstream publication or fix attempted.
