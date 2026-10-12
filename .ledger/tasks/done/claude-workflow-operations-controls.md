# Task: Complete the remaining workflow production controls

## Goal

Finish the Claude Workflow production-gap investigation's remaining controls
(3–7 of the 2026-10-12 handoff): crash recovery and side effects,
cancellation and deadlines, budget and concurrency enforcement, retries and
incomplete streams, and replay with changed shared state. The first two
priorities (specialist handoff diagnosis and review provenance) were already
complete; the twenty-three operational probe cases had been run but never
analyzed, verified or written up.

## Acceptance criteria

- [x] Analyze all twenty-three `workflow-operations-*` trace results against
      their journals, counters, workflow states, API captures and terminal
      results.
- [x] Complete the crash-recovery control: the original crash cases captured
      only the crash boundary because an external SIGKILL leaves no workflow
      state file to derive a resume handle from. Add a driver that derives
      the resume handle from the surviving journal and script, and run the
      fresh-process resume phase for all three boundaries.
- [x] Write an executable outcome verifier covering all cases, including the
      crash-resume completions.
- [x] Save a maintained report and controls record; update the documentation
      index and the stale static-only note in the workflow analysis report.
- [x] Record findings and benchmark implications in the evaluation plan and
      session log.

## Evidence

- Pinned binary `24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`,
  verified before every run.
- Original traces: `tmp/claude-code-binary-analysis/2.1.296/traces/workflow-operations-<case>-v1`
  (unchanged). Crash-resume completions: `workflow-operations-crash-<case>-resume-v1`.
- [Maintained report](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-operations.md)
  and [verified controls](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-operations-controls.json).

## Status

Done. Twenty-three verified controls pass. Headline findings: recovery is
at-least-once for un-journaled agents (side effects duplicate on crash,
journal truncation, retry exhaustion and stall recovery); request-level
retries are side-effect safe; cancellation, SIGTERM and the print
background-wait ceiling all terminate children with no late writes (the
ceiling kills the workflow rather than detaching it); the budget gate fires
at agent launches and at completion, so a final agent can exceed it while the
workflow still completes; nested Skill usage is counted; the concurrency
override is shared globally with nested workflows; replay ignores changed
shared state. SIGTERM and stall exhaustion emit success-looking CLI result
events while the workflow dies or fails. These strengthen the existing
production recommendation without changing it.

No real credentials, paid model calls, deployed service changes, S1/S2 edits
or commits. Raw evidence stays under the ignored
`tmp/claude-code-binary-analysis/2.1.296/` tree.
