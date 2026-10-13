# Task: Write a narrative version of the Workflow report

## Goal

Create var/benchmarks/strat-workflow/analysis.md in the user's
direct, conversational style, with short sections suitable for Google Docs and
eventual slides. Keep the original report intact.

## Acceptance criteria

- [x] Explain the tested Workflow architecture and its useful features and limits.
- [x] Preserve measured outcomes, pricing/model labels and evidence boundaries.
- [x] Explain testing levels, simple confidence arithmetic and validation after changes.
- [x] Give a supported production recommendation in connected prose.
- [x] Check local links, arithmetic, Markdown formatting and the unchanged original.
- [x] Keep the session log empty; do not launch inference or commit/push.

## Status

Done, 2026-10-12. User requested a separate human-readable version.

## Evidence

- [Narrative report](../../../var/benchmarks/strat-workflow/analysis.md):
  about 3,400 words across three chapters and thirteen short sections. Connected
  prose follows the user's direct conversational style, with three compact tables.
- Preserves the recorded 51.2/88.7-minute comparison, 2/12 versus 12/12 delivery,
  Opus 4.6 price basis, zero-failure calculation and pending retest status.
- Twelve local evidence links resolve. Heading/list/table spacing, pricing
  arithmetic and model labels pass focused checks. git diff --check passes.
- Original report SHA-256 remains
  0572920bdcbb5d287ba1f79b0851720a1960edb3a684fdf8364f1604390e9820.
- Session log remains empty. No inference calls, deployments or commits.

## Editorial follow-up

- Expanded the introduction with the Haiku, Opus and GLM campaigns and binary/
  archive investigation, named the four reviewer roles, removed the unnecessary
  RFE definition and em dashes, and explained that Part B budgets the missing
  performance/reliability evidence.
- Corrected model coverage: level 1 includes all three models; level 2 includes
  one Haiku S1 batch and Opus on both designs. GLM has no recorded batch run.
- Added B.6's Opus-only per-pair budgets. Historical single-RFE categories total
  about 26.8M tokens across three pairs, or about 8.9M per pair. Recorded Opus API
  equivalents total $42.54, or $14.18 per pair. The completed batch pair remains
  25.16M tokens / $45.83. These are historical captured-usage estimates.
- Exact archived request/response pairing confirms the 167579-token sample is
  the architecture reviewer, with platform/component document reads. The plan
  records its IDs and 13 direct Read targets; no claim of reading all overlays.
- GLM pricing remains unverified. Haiku's token-only smoke estimate is kept
  separate from the Opus dollar rows.
- Clarified the execution platform: Markov drives Breadboard job API submissions
  and checks, with the strategy workloads in Kubernetes jobs. These benchmarks
  reused strategy code but did not use Fullsend's runner or OpenShell sandbox.
  The release/configuration statement explicitly names Claude Code 2.1.296.
- Revised future coverage to the user's ten-RFE production limit and six-hour
  schedule. Three-RFE measurements remain historical baselines; production
  capacity is not reduced. Level 3 proposes ten paired ten-RFE batches, and
  level 4's full-size budgets scale the historical pair provisionally by 10/3.
  Rounded planning values are 84M tokens / $153 per pair and 840M / $1530 for ten
  pairs, with larger totals calculated from those same rounded values.
- Reliability bounds from full-size trials apply to the sampled workload;
  ordinary production failure frequency needs representative batch-size coverage.
  The existing R1 retest remains three RFEs and is explicitly a scheduling check.
  No paid run or fixture implementation was authorized by this report revision.
- Added a separate content-judging subsection and budget example: 200 strategies,
  two judge models and two samples produce 800 assessments before retries.
  Pipeline budget rows exclude that new spend. A pinned harness inspection and
  [integration assessment](../../notes/strat-workflow-content-eval-harness-assessment.md)
  document independent judge configuration, rescoring and pricing limitations.
- Promoted content judging to its own level 5 section after level 4. It can
  evaluate saved outputs from earlier levels and is not dependent on completing
  a reliability campaign. Renumbered the remaining sections consistently.

## Single-report follow-up

The user subsequently requested removal of the technical version. That request
supersedes the initial requirement to preserve it. The human report is now the
single maintained report; the initial version remains in git history. See the
[consolidation task](claude-workflow-report-consolidation.md) for link updates
and schedule provenance.

## Report location

At the user's request, moved the report to
[var/benchmarks/strat-workflow/analysis.md](../../../var/benchmarks/strat-workflow/analysis.md).
Report prose is unchanged; relative evidence/chart links, incoming links and the
chart data's source reference are updated. The benchmark README links to the
analysis. Resolved-link comparison confirms the moved report targets the same
evidence and chart files. Local links and git diff --check pass; session log empty.
