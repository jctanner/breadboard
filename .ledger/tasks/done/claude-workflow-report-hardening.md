# Task: Harden the Workflow comparison report

## Goal

Keep the readable report neutral and concise while making its measured findings,
mechanisms, limitations, applicability and follow-up experiments explicit.

## Scope

User asks for the changes following review of /tmp/prompt-benchmark-hardening.md.
Use the prompt as a checklist, correcting proposed claims where evidence does not
support them. No paid batch is authorized by reading that prompt. Preserve
original S1/S2 baseline pins, private archives and the empty session log.

## Acceptance criteria

- [x] Explain what the single completed pair establishes and what it cannot.
- [x] Distinguish state transcription, nested Skill projection and recovery.
- [x] Separate delivery, scope, incorporation and factual accuracy.
- [x] Present both concurrency tradeoffs; avoid unsupported causality/intent.
- [x] Name isolation/cache reuse as an unmeasured comparison axis.
- [x] Bound applicability to equivalent runtime/configuration; no unverified PR claims.
- [x] Distinguish recorded delivery counts from future failure-rate estimates.
- [x] Pre-register a matched-concurrency test with explicit paid-run gate.
- [x] R2: archive one reproduction on the current installed binary and report it.
- [x] R3: provide a manifest-driven expected-result checker, tests and archive replay.
- [x] Keep sources, limitations and word count suitable for the readable report.
- [x] Run relevant checks; do not commit/push without a further request.

## Status

Done for the authorized report/mock/checker scope, 2026-10-12. R1's paid run is
separate [pending work](../pending/strat-workflow-matched-concurrency-retest.md);
the full prompt's matched-concurrency-run criterion remains unmet.

## Evidence

- Current installed Claude is still 2.1.296 with the original pinned hash.
  One mock reproduction repeats the lost return: earlier prose persists in
  the native transcript, expected Skill result is acknowledgement-only,
  Workflow completes and CLI exits zero. Newer versions remain untested.
- R3 requires complete normalized selected-report text against hashed references
  and exact tool IDs; replays match 2/12 versus 12/12. Expected pair sets are
  independently checked as three archived strategy keys times four roles.
- [Compact evidence](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-benchmark-hardening-evidence.json)
  identifies sources and hashes. Private archive has 92 verified files;
  original archives are unchanged. No paid model call or cluster mutation.
- 17 tests pass, one optional Bun compiler fixture skipped. Nine tests exercise
  the new checker's contracts, missing/error/progress returns, conflicts,
  identity mismatches, repeated histories and reference tampering.
- Source links, Python/JSON syntax, all referenced/archive hashes, credential
  scan and git diff --check pass. Session log remains empty.
- Report retains eleven short sections (about 2,500 words including sources).
  Sentence-by-sentence review keeps mechanism, frequency, configuration,
  scheduling, recovery and content claims distinct. No motive/PR-status claims.

The older companion eval plan was available but its architecture claims were
not substituted for current evidence. The named companion dispute-status note
was not found. Neither gap affects the technical reproduction or archive replay.
