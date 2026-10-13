# Task: Keep one Workflow comparison report

## Goal

Retire the technical sibling at the user's request and keep the human report as
the single maintained account of the benchmarks, testing ladder and recommendation.

## Acceptance criteria

- [x] Remove the technical report and update every tracked link to it.
- [x] Preserve the human report, chart and underlying benchmark/binary evidence.
- [x] Explain the six-hour planning requirement and older schedule ambiguity.
- [x] Check local links and whitespace; keep the session log empty.

## Status

Done, 2026-10-12.

## Evidence and decisions

- The [human report](../../../var/benchmarks/strat-workflow/analysis.md)
  is the only maintained comparison report. Its ten-RFE level 3/4 ladder and
  independent level 5 judge budget remain unchanged. The retired version is
  recoverable from git history; raw evidence and binary investigations remain.
- Updated the work index, benchmark plan, report evidence section and original
  report task. Tracked references to the removed filename are absent.
- Read the 9 October source eval plan: it already records README three-hour
  versus CI-comment six-hour descriptions and says scheduling lives in GitLab's
  UI. It does not verify the live schedule. It also distinguishes observed
  120–300 strategies/month from the rejected 2,430/month estimate. Our report
  uses the user's six-hour production requirement and nominal capacity, with
  the three-hour overrun consequence now explicit. No deployed schedule changed.
- Retained the aggregate batch/cadence requirements and named benchmark tools:
  the user supplied these to explain production fit and requested their inclusion.
  No raw production cases, credentials or new operational endpoints were added.
- Local links and git diff --check pass. No model runs, deployment, commit or push.
