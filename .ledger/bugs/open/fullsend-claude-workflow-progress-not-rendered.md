# Fullsend omits Claude Workflow progress from console output

Upstream: [fullsend-ai/fullsend issue 8908](https://github.com/fullsend-ai/fullsend/issues/8908),
open, labeled bug; created at the owner's request on 2026-10-29.

Confirmed 2026-10-29 by read-only inspection of the real GitLab single-ticket
smoke archive and Fullsend v0.47.1 source. No new inference was needed.

## Evidence

Pipeline 2996306877 / job 17518703899 retained Claude's raw stream in
`fullsend-output/runs/fs-str-03767796b95b/iteration-1/output.jsonl` inside
`var/run-data/20261027-real-gitlab-postmerge-single-opus46/job-17518703899-workflow-single-rfe/artifacts.zip`.
The member SHA-256 is
`2c8e2a453ac963664605c284b7721056fb9ebfaf72238d899fc3a3549236fe70`.

It contains 135 `type: system`, `subtype: task_progress` events. Of those,
33 contain `workflow_progress`, including `workflow_phase` and
`workflow_agent` records. Phase titles include Read, Create, Refine, Push,
Score, Review, and Result. Live descriptions advance through input reading,
strategy creation, refinement, scoring, review, and result writing.
Agent records include state, phase attribution, and tool progress fields.

The phase-title inventory includes predeclared `meta.phases`; its presence
alone does not establish that those phases ran. Live advancement is established
separately by changing descriptions and `workflow_agent` states: `read input`
moves from start to done with two tool calls, followed by strategy creation,
and subsequent descriptions advance through refinement, push, score, review,
and result. Score/Review are also attributed through agent `phase:` options;
not every phase title comes from a top-level `phase()` call.

In Fullsend v0.47.1, `internal/runtime/claude_progress.go::parseClaudeStream`
handles `system` subtypes `init` and `api_retry` only. It does not normalize
`task_progress`, `task_started`, `task_updated`, or `task_notification` into
renderable agent events. `claude.go` tees raw stdout to the output artifact
before parsing, explaining why the data survives there despite disappearing
from the human-facing console. Parser source SHA-256 at that tag:
`c2b4d19ad9cb234e4763994a2fe726c8ade0bbbf838aab8a9df7d3f287f92634`.

## Classification and repair boundary

The missing phase/progress display is a Fullsend event-adapter/rendering gap,
not an absence of Claude Workflow progress emission. `phase()` updates the
Workflow progress channel; it is not necessarily a literal stdout print.
The captured stream establishes that useful events reached Fullsend.

Add explicit task/progress normalization and safe rendering, including task
identity, phase, agent state, available tool context, and terminal outcome.
Handle repeated snapshots without flooding logs and redact displayed fields.
Preserve business validation: a progress event is not proof of completion.
Fixture replays of the real event shapes can test this without model calls.

This diagnosis does not establish that full nested tool stdout/stderr is
exported, or that rendering task progress alone would provide every desired
diagnostic. The inspected local checkout also lacks these subtype handlers;
no claim is made about an uninspected newer release. No source fix, deployment,
upstream issue, or paid test was performed.

Read-only extraction summary: `/tmp/strat-workflow-progress-evidence-20261029.json`.
Related: [retrospective](../../notes/strat-workflow-migration-lessons.md#live-stdout-did-not-show-workflow-progress).

## Independent Claude review

Owner requested `claude -p` validation. Claude Code 2.1.312, Opus 4.6/high,
reviewed the exact v0.47.1 parser and Claude runner source, then completed a
focused follow-up against tagged event/renderer snapshots and the original
archive via the read-only verification script. Verdict: **Confirmed**.

The first pass could not run its altered verification command under the
permission allowlist and initially missed two source snapshots. The follow-up
used the exact permitted absolute-path command and resolved those gaps:
135 progress events, 33 Workflow snapshots, matching member hash, live state
advancement, and no task-progress normalization/rendering at v0.47.1.

Review refinements: distinguish predeclared phases from live advancement,
and keep structured progress separate from full tool output. Proposed local
regressions cover parsing, state/phase rendering, deduplication, redaction,
terminal notifications, and metrics non-interference; none were implemented.

Reviewer output has incidental slips that do not affect the diagnosis: the
follow-up overstates that all additional system subtypes are dropped (`init`
is handled), says the hash was absent from this report (it is above), and
overstates renderer coverage of all event types (no `ToolResultEvent` branch).
The source, rather than those summaries, governs the repair.

Review evidence: `/tmp/strat-workflow-progress-claude-review-20261029/`, including
`review.md`, `followup-review.md`, both prompts/streams, tagged snapshots, and
usage receipts. Two invocations: 277.16s and 47.21s; CLI list-price estimates
$1.590145 and $0.203465, total $1.793610. These are review costs, not another
Workflow qualification run. No component edits, live model batch, runtime
changes, or upstream publication occurred.

## Upstream duplicate search on 2026-10-29

Live GitHub searches found no exact open issue or PR for `task_progress` or
`workflow_progress`. Broader Workflow/Claude progress searches were fully
paginated (235 and 199 matches), with additional searches for the parser file,
stream-json, console, logging, and heartbeat symptoms. No direct duplicate was
identified; search absence is not proof that none exists under other wording.

Closest related work:

- [PR 6595](https://github.com/fullsend-ai/fullsend/pull/6595), open:
  detects stalled agents from output-stream inactivity. Its description cites
  misleading agent-running heartbeats but explicitly excludes changing the
  heartbeat. The inspected 21-file patch at `3f7c31e` does not add Workflow
  task/phase progress handling. Liveness detection is distinct from rendering.
- [PR 7687](https://github.com/fullsend-ai/fullsend/pull/7687), open:
  recovers turn counts from incomplete Claude streams. The seven-file patch
  at `7e03869` does not implement Workflow progress display.

Search results and inspected PR metadata/patches are retained under
`/tmp/fullsend-workflow-progress-upstream-search*-20261029.json` and
`/tmp/fullsend-workflow-progress-related-prs-20261029.json`.
Read-only search only; no upstream issue, PR, or comment was created.

## Upstream publication

Owner subsequently requested filing the bug with sufficient detail and the
format used by other bugs. The live repository has no dedicated bug form;
blank issues are enabled. Followed recent human-filed bugs with Problem,
observed evidence, reproduction, expected behavior, cause, scope/acceptance,
and related-work sections.

Created [issue 8908](https://github.com/fullsend-ai/fullsend/issues/8908):
"Claude Workflow task_progress events are captured but omitted from console output".
The body includes a reduced sanitized NDJSON fixture for model-free parser
testing, exact-release source links, private-run evidence summarized in text,
and limits on full nested output and newer-runtime claims. Only the bug label
was requested; no ready-to-code dispatch label was added.

POST succeeded once (HTTP 201); GET readback verified title, body, label,
and open state. Prepared text/payload, credential-scan result, fresh duplicate
search, creation intent, creation response, and readback receipts are under
`/tmp/fullsend-workflow-progress-issue-20261029/`. No implementation, PR,
comment, runtime change, or model qualification job was submitted.

## Connection to runtime Workflow support

At the owner's request, updated issue 8908's Related work section to connect
[ADR 0130 / PR 8225](https://github.com/fullsend-ai/fullsend/pull/8225),
which follows the rejected custom-entrypoint proposal 7947, and its implementation:
[fetch/lock/deliver 8226](https://github.com/fullsend-ai/fullsend/pull/8226) and
[runner launch 8228](https://github.com/fullsend-ai/fullsend/pull/8228).
Delivery and launch support do not supply progress normalization/rendering.
The bug already affects the released agent-launched path; it is not caused by
those unmerged changes, and its fix need not await them.

Updated the issue body in place; no separate comment or changes to title/labels.
GET readback verified the exact updated body and unchanged title. Before/after
receipts are retained under the publication directory above.

## Local implementation (2026-10-29)

Owner supplied a clean rebased fork at
`checkouts.tmp/jctanner-fullsend-ai/fullsend`; implementation is staged on
`fix/8908-claude-workflow-progress`, based on `d70721c50`.
[Implementation task](../../tasks/done/fullsend-8908-workflow-progress.md)
records the parser/display change, red-first regression, archived-stream
replay, race coverage, lint, and full-suite validation status. Keep this bug
open pending upstream delivery; the local change has not been committed,
pushed, deployed, or published as a PR.


The owner then requested broader useful event coverage. The
[event coverage task](../../tasks/done/fullsend-8908-workflow-event-coverage-audit.md)
records completed lifecycle/partial-patch handling and advisory display for
hooks, permission denials, session/compaction, notifications, background
membership and rate limits. Tests, safe-display boundaries, event matrix,
version qualification and the full CLI timeout limitation are recorded there.
All thirteen intended component files remain staged and unpublished.


[Opus 5.5 review repairs](../../tasks/done/fullsend-8908-claude-review-fixes.md)
are complete locally: duplicate terminal/error loss, unkeyed warning suppression,
per-request status chatter and mixed run-ID routing all have red-first
regressions and passing repairs. Follow-up review found and verified an
additional anonymous-restart/old-run-history correction. Final read-only
Opus 5.5 verdict reports no new material defect. Runtime/CLI-path race tests,
coverage, staged lint/vet/links and original-stream replay pass; the previous
full CLI timeout remains documented. Still staged and unpublished.


Owner subsequently authorized commit and push. Signed-off `7f266ee9f` passed
all commit hooks and was pushed to the fork branch:
https://github.com/jctanner-fullsend-ai/fullsend/tree/fix/8908-claude-workflow-progress
No upstream PR or deployment yet; bug remains open pending delivery.


Owner opened https://github.com/fullsend-ai/fullsend/pull/8913. At the owner's
request, updated its description with sourced BEFORE/AFTER console excerpts,
explicitly distinguishing the recorded pre-fix job from a model-free patched
replay. Exact body/title/head verified by readback; merge still pending.


PR review follow-up completed in signed-off 8e1fd4028 and pushed to PR 8913:
sparse hook/agent context retention, explicit clearing, transient metadata
reset on recovery, per-run visibility, generated scanner fixture and requested
organization/docs fixes. Red-first regressions, runtime/CLI-path race tests,
lint/vet/links, replay and final Opus 5.5 review pass. Scope objection ignored
per owner's explicit instruction. [Task](../../tasks/done/fullsend-8913-review-comments.md).
Remote ref and PR head verified; merge pending.


Human review follow-up a4c647466 addresses waynesun09's stable-index and
undocumented-protocol findings. Indexed agent IDs are display metadata, with
ID-only updates suppressed and completion updating one stable row. Private
workflow_progress/task_summary contract risks are explicit. Runtime/CLI race,
lint, replay and Opus 5.5 review pass. Signed-off commit pushed and PR head
verified; description examples refreshed. [Task](../../tasks/done/fullsend-8913-waynesun-review.md).
