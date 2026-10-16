# Reviewer Skills execute serially despite being requested together

## Status: deferred

On 2026-10-15 the user deferred this optimization. The estimated single-ticket
saving is about six minutes under ideal overlap, not a measured improvement.
Full simultaneous review of ten tickets would require 40 reviewer workers, plus
any overlapping scoring/coordination, with additional session binding, receipt
validation and partial-failure/recovery work. That complexity and unmeasured
production benefit do not justify proceeding now. Retain the current dispatch
and this evidence; no concurrency implementation or qualification runs are
planned until the user revisits it. This remains an unresolved performance
finding, not a repaired or permanently rejected bug.

## Findings

The one-ticket Fullsend/Vertex Opus smoke `markov-run-d7043ace` requests all four
reviewer Skills together, as required by strategy-review/SKILL.md, but the actual
child transcripts show no overlap. All four tool uses share one API response,
`msg_vrtx_011Cg4RbxJezfuB8yRwiXqhP`; the model did not wait for each reviewer
before requesting the next.

Feasibility, testability, scope and architecture execute in that order over
8m49s, with individual spans of 2m50s, 1m44s, 1m35s and 2m21s. Each later child
starts after the preceding child's parent tool_result. The outer Workflow cap
is five and only one ticket review is active. The same per-ticket ordering is
visible in the successful overnight three-ticket run, whose ticket review
agents themselves overlap.

The internal cause is now verified against the exact local 2.1.296 binary.
The generic tool constructor defaults isConcurrencySafe to false; the Skill
tool retains that default. The dispatcher permits an unsafe tool only when no
other tool is executing. The rule also applies to context: fork. Four calls in
one response therefore serialize regardless of an outer agent cap of five.

Two native controls use an isolated loopback API and zero real provider calls.
One Workflow agent emitting four Skill calls reaches maximum child concurrency
one; four Workflow agents each invoking one Skill reach concurrency four. Both
controls return all four Skills and exit zero. The existing pipeline has not
been modified. A production repair must revalidate report delivery and receipt
contracts around any revised dispatch arrangement, not just request parallelism
more strongly. [Binary proof and controls](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-skill-concurrency.md).

A third native control confirms the same maximum concurrency one under plain
`claude -p "/concurrency-review"` with Workflows disabled. It verifies that the
authored slash-command prompt loaded and all four Skills returned, exit zero,
zero provider calls. Archived S2 Opus calls also show all four reviewers requested
together and their child response ranges proceeding in role order for all three
tickets; corresponding launch/first/last response hashes match retained provenance.
This is a shared Claude Skill-dispatch restriction, not introduced by S1.

At unchanged individual timings, ideal overlap would save about six minutes in
the one-ticket run. This is an upper-bound arithmetic estimate for this reviewer
interval, not a measured end-to-end improvement. Preserve report isolation,
actual receiving-channel checks, provenance and numeric-only approval if the
dispatch arrangement changes. Local/stubbed controls can investigate without
paying for another benchmark.

[Timings and source comparison](../../notes/s1-fullsend-vertex-opus-smoke-20261015.md).
