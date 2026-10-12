# Task: Identify other subagent-to-primary information channels

## Goal

Extend the pinned Claude Code 2.1.296 investigation beyond skill metadata.
Distinguish automatic model-context propagation, deliberate result/trace access,
shared mutable state, and state that remains scoped to the child.

## Acceptance criteria

- [x] Trace changed-file attachments, nested instructions and agent reporting.
- [x] Inspect shared permission, artifact and other context state without
  equating shared references with proven automatic prompt injection.
- [x] Run isolated mock-API controls for selected additional channels.
- [x] Save maintained findings and exact evidence in the analysis docs home.
- [x] Verify outcomes, evidence hashes, Python compilation and whitespace.

## Status

Done. [Report](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-subagent-information-sharing.md)
records six verified controls, eight evidence-labeled claims and twenty-two
exact symbol/property ranges and hashes.

Confirmed child file edits can enter primary context through changed-file
attachments when the primary previously wrote the file. Ordinary Read cache
entries are skipped by this release's scanner. Child Bash output reaches SDK
child events but not primary model requests in the fixed-answer control.
Background receipts supply full transcript paths outside coordinator mode.
Shared permissions and artifact/browser state are statically identified,
without claiming automatic context delivery from shared references alone.

Nested instruction propagation code exists, but its typed flag object has an
empty shape in this binary. Both default and coordinator/flag controls keep
the nested instruction body out of the primary after a subsequent tool turn.
Earlier incomplete mock attempts remain ignored and excluded from verified
controls. Successful runs retain the exact runner snapshot and fixture hashes.

Six new outcome controls, the original ten skill controls, eight claim/path
checks, twenty-two payload hash checks, thirty-two documentation links, JSON,
Python compilation and git diff --check passed. No paid inference, real
credentials, deployment changes or source-checkout modifications.
