# Architecture report rejected for “Mostly sound” wording

Scheduled Opus run `markov-run-dd4a838118bd23d18c693b01` completed all three
strategies, with 12 reviewer report files. The pinned benchmark records
`reviewer_outputs_returned=false` for RHAISTRAT-3 architecture. The actual Skill
return is 7,179 characters and contains a detailed assigned-ticket assessment
and an explicit approve recommendation. It is saved and published.

The role-assessment-v1 checker requires the architecture judgment to start with
`sound`, `concerns identified`, or `conflicts with platform`. The report starts
`Mostly sound, with two architectural concerns requiring clarification`, so
classify() marks it incomplete. check_run.py then reports result_chars=0 for a
rejected assessment despite content_chars=7179. This is not missing transport
content and is not evidence that StructuredOutput loss recurred.

Keep the pinned result unchanged. A future repair should explicitly decide
whether to enforce canonical producer wording or accept supported qualified
judgments, with negative tests for unfinished/ambiguous assessments. Do not
silently weaken the checker to turn the historical run green.

## Mixed-state Opus recurrence

Run markov-run-5d3327ed rejects RHAISTRAT-3 architecture (5,819 characters):
“Mostly sound; one incorrect assumption and one under-documented dependency
require revision.” Its delivered report, provenance and composed review match.
Replacing only Mostly sound with Sound in memory makes the classifier pass.
Recommendation revise is explicit; no missing handoff. Historical eval retained.
[Audit](../../notes/s1-mixed-state-opus-20261016.md).
