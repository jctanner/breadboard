# Task: Add the testing overview chart

## Goal

Add a visual before section 6 of the human Workflow report that relates testing
levels to cost, time and reliability evidence, with portable Google Docs exports.

## Acceptance criteria

- [x] Verify Mermaid/GitHub chart capabilities from official documentation.
- [x] Keep dollars, job hours and failure-rate bounds on separate axes.
- [x] Label measured references, forecasts, hypothetical bounds and unknowns.
- [x] Explain the selected level 4 scenario and independent level 5 budget.
- [x] Export PNG/SVG with reproducible data and plotting source.
- [x] Inspect the chart and check arithmetic, links and formatting.
- [x] Preserve the original report, empty session log and paid-run policy.

## Status

Done, 2026-10-12. User requested a chart for Part B's overview.

## Evidence and choices

- [GitHub Mermaid documentation](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
  confirms fenced rendering and version-dependent syntax;
  [Mermaid XY charts](https://mermaid.js.org/syntax/xyChart.html) support line
  charts with one numerical y-axis. Mixing dollars, hours and percentages on
  that axis would obscure their meaning.
- Used Matplotlib for a scientific figure portable into Google Docs:
  [PNG](../../notes/assets/strat-workflow-testing/overview.png),
  [SVG](../../notes/assets/strat-workflow-testing/overview.svg),
  [data](../../notes/assets/strat-workflow-testing/data.json), and
  [plotter](../../notes/assets/strat-workflow-testing/plot.py).
- Three aligned graphs separate Opus reference costs, recorded combined job
  hours and hypothetical 95% upper failure-rate bounds. Level 4 explicitly uses
  60 clean runs per design. Level 5 has no invented numeric endpoint and can
  reuse earlier outputs. Costs are per-level totals, not cumulative.
- Level 1 uses historical Opus reference averages, with transport interruptions
  flagged; future smoke policy remains Haiku. Full ten-RFE time is unmeasured.
  Level 3/4 costs are projections, and failure bounds require qualifying zero-
  failure trials, not the currently defective benchmark versions.
- Visually inspected exports and corrected footer spacing. Arithmetic, null
  values, references, report placement, PNG dimensions (2160 x 2472) and SVG XML
  checks pass; git diff --check passes. Plotter executed successfully with the
  repository venv. Original report unchanged; session log empty; no paid run,
  deployment, commit or push.

## Runtime forecast follow-up

Added the user's requested forecast to the middle chart. Linear ticket-count
and repeat scaling of the measured three-RFE pair gives about 78 job hours for
level 3 and 466 for the 60-run level 4 example. Source JSON retains the unrounded
calculations and original scheduling assumption. Projected time uses hollow
markers and dashed lines; level 5 remains unknown. These are active job-hour
totals for sequential benchmark jobs, excluding quota waits, collection and
independent judging. Full ten-RFE runtime remains unmeasured.

Validation: regenerated and visually checked the PNG; checked forecast arithmetic
and SVG labels. The SVG export uses stable IDs and removes generated trailing
whitespace. XML parsing and git diff --check pass.

The cost graph title now names `claude-opus-4-6` explicitly, using the model
field from the source JSON. Regenerated PNG/SVG exports and checked the label
and layout; git diff --check passes.
