# Task: Reverse engineer Claude Code auto-mode

## Goal

Investigate how Claude Code's "auto-mode" works under the covers: the
classifier that decides whether a next step is risky and auto-processes
less-risky actions. Establish whether and how it makes ancillary model calls,
what model/prompt/schema it uses, when it triggers, and how decisions map to
auto-approval versus escalation. Use the pinned 2.1.296 binary, the existing
carving/indexing tooling, and mock-only runtime probes.

User authorized this investigation on 2026-10-12.

## Existing anchors

- Operational observation (ledger): `make host-rebuild-relay` and other
  shared-resource deploys are denied by the auto-mode classifier for agents.
- `CLAUDE_CODE_ENABLE_AUTO_MODE` appears in the 2.1.296 payload string table.
- Eight tiny non-stream generations (four Haiku 4.5, four Sonnet 4.5,
  22 input / 1 output) captured by the relay during the S2 Opus batch
  outside the job API pairs; caller unestablished — candidate classifier
  traffic.

## Acceptance criteria

- [x] Locate auto-mode control flow in the exact binary (settings, env,
      permission-mode integration, classifier invocation).
- [x] Recover the classifier call: model selection, request shape, prompt,
      output schema, fallback behavior.
- [x] Runtime-control the behavior with the loopback mock API; capture any
      ancillary requests verbatim.
- [x] Reconcile with the archived relay evidence if possible.
- [x] Save a maintained report, claims, and executable verifier; update the
      docs index and ledger.

## Boundaries

No real credentials, no paid model calls, no deployed-service changes, no
upstream publication. Raw evidence stays under the ignored
`tmp/claude-code-binary-analysis/2.1.296/` tree.

## Status

Done. Auto mode is default-on, skipped for acceptEdits-allowed actions, and
makes ancillary non-streaming Sonnet classifier calls: stage 1 (max_tokens 64,
stop at </severity>, harm-only grading) and, only when stage 1 severity
exceeds the boundary, stage 2 (max_tokens 8192, user intent and ALLOW
exceptions). The 139,988-char system prompt embeds 1 HARD BLOCK, 68 SOFT
BLOCK and 17 ALLOW rules; verdicts are <severity>0-100</severity> with 50 the
boundary. Classifier calls bill to the user's account unless the gateway
implements the classifier-billing protocol. No-verdict outcomes deliver
flagged (fail-open); parse failures block (fail-closed). The eight tiny relay
calls in the S2 archive are not classifier traffic (zero cache activity).
[Report](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-auto-mode-analysis.md),
[claims](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-auto-mode-claims.json),
[controls](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-auto-mode-controls.json).

No real credentials, paid model calls, deployed-service changes or commits.
