# Task: Reverse engineer the latest Claude Code workflow system

## Goal

Repeat the Bun binary analysis method for Claude Code's native workflow
system, using the newest official binary and the older unofficial source
snapshot as a correspondence aid. User authorized this investigation on
2026-10-11.

## Acceptance criteria

- [x] Verify the official latest release and record binary/payload provenance.
- [x] Recover workflow discovery, schema, execution, agent lifecycle, return
  handling, state/progress, permissions, and cancellation control flow.
- [x] Correlate the older snapshot without treating it as authoritative.
- [x] Run isolated controls where the unmodified release permits them; record
  feature gates and limitations explicitly.
- [x] Save a readable report, original pseudocode, and offset/hash evidence.
- [x] Validate evidence paths and run relevant tooling checks.

## Evidence workspace

`tmp/claude-code-binary-analysis/2.1.296/` (ignored generated material).
Latest release endpoint returned `2.1.296` on 2026-10-11, matching the
installed `/home/jtanner/.local/share/claude/versions/2.1.296`.

## Status

Done. [Report](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-analysis.md), original
pseudocode, binary manifest, twelve topic groups of parsed symbol hashes,
seventeen evidence-labeled claims, and sixteen verified runtime controls saved.
The source baseline is `deploy/repos.bak/claude-code` at `126c31154f72`;
missing implementation directories were recovered from the exact target.

Tooling: byte-accurate module parser/indexer, credential-free mock API probes,
and persisted-outcome verifier. Seven tooling tests passed; the optional Bun
compiler fixture was skipped. Python/Node compile checks, claim paths, exact
payload hashes and whitespace checks passed.

Static-only limitations include interactive permissions, cancellation races,
plugin collision precedence, cross-process resume, retry/quota branches and
concurrency stress. No paid model calls, real credentials, deployed service
changes, or committed raw binary/source material.
