# Task: Investigate native Workflow production boundaries

## Goal

Execute the [handoff](../../notes/claude-workflow-production-gaps-handoff.md)
against the immutable Claude Code 2.1.296 binary and read-only real-run archives.
Separate engine behavior, integration contracts, configuration and model choices.
Do not modify or deploy the strategy pipeline.

## Acceptance criteria

- [x] Reproduce nested specialist return behavior with a one-factor mock matrix.
- [x] Establish per-call provenance for twelve S1 Opus specialist handoffs,
  using S2 Opus and GLM controls where useful; label missing evidence explicitly.
- [x] Write those two priority findings before extending other controls.
- [ ] Exercise bounded cross-process recovery/side-effect and journal cases.
- [ ] Exercise cancellation/deadlines and queued/running fixture work.
- [ ] Trace/test budget and concurrency limits without real prices or quota use.
- [ ] Inject bounded API/stream failures and verify retries/side effects.
- [ ] Check replay with changed shared state and reversed completions.
- [ ] Maintain reports, exact symbols, claims and executable outcome verifiers;
  append benchmark implications to the evaluation plan and verify all checks.

## Status

Current. Verified input binary SHA-256 matches the pinned manifest. Reading
archive API indexes and tracing Workflow-schema to nested Skill/fork context.
Existing mock controls and sharing/variable reports are the baseline. All new
runtime artifacts will use fresh ignored directories and runner snapshots.

## Priority 1–2 findings (2026-10-12)

Completed twenty matrix cases plus a custom Read-only specialist workaround.
Forks inherit StructuredOutput/schema/description; tool-ending results select
the last tool-only assistant record and return acknowledgement instead of
assessment/dissent. Prose-ending controls deliver. Ordinary CLI --json-schema
also reproduces, so native Workflow scheduling is not a necessary cause.
A narrowed custom Skill agent removes the tool and preserves the parent's
outer schema. Direct schema completions work. CLI schema prose-only control
returns success without structured_output; output validation remains necessary.

Audited thirty-two archived calls. S1 Opus: ten missing expected returns, two
delivered; all ten end in StructuredOutput, all receive correct target keys.
S2 Opus: twelve prose returns, no SO tool in specialist requests. S1 GLM:
four missing expected returns, followed by explicit transcript recovery of
three full selected bodies and substantial architecture prose. S2 GLM: four
direct prose returns. Architecture-2 Opus continuation joined across compaction
using unique tool-result IDs. Three final strategy-1 sections closely reuse
within-run scorer material read before specialists; delivered testability-1
faithfully preserves several specific findings/dissent. Other semantic fidelity
remains limited. Missing expected prose does not establish fabrication.

Reports and compact evidence are in scripts/claude_binary_analysis/docs/:
workflow-specialist-handoff and workflow-review-provenance, ten claims,
nine exact symbols, controls and four provenance records. New tools:
run_workflow_handoff_experiments.py, mock_api_support.py,
verify_workflow_handoff_controls.py, audit_workflow_review_provenance.py,
verify_workflow_review_provenance.py. Claim validator now supports archive-observed
with required existing paths; nine tooling tests run, eight pass/one optional
Bun compiler skip. First two priority reports written before broader controls.

Next: finish priority evidence checks/snapshots and record benchmark implications;
then build bounded lifecycle/recovery/retry/accounting/replay controls. No pipeline
changes, real credentials, paid inference, deployment or external publication.
