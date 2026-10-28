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

## Completion-hook retest recurrence

Run markov-run-0b098f6e rejects RHAISTRAT-6 architecture (6,391 characters)
because its judgment begins “Core architecture is sound with two unresolved
validation items.” The detailed assessment and approve recommendation reach
the caller and appear in the published review. SHA-256:
`6ad54f24e8a3838a428dd9626021a5fb69aaebab649750533d1f77034f29bc16`.
Replacing only the judgment prefix with “sound” in memory makes it pass.
Current parser support for mostly/largely sound does not cover this prefix.
Historical FAIL remains unchanged; no source repair or inference during analysis.
[Audit](../../notes/s1-completion-fixed-opus-ten-rfe-20261018.md).

## Fixed in the local checker, 2026-10-18

The current parser already recognizes mostly/largely sound. `role-assessment-v2`
also removes the bounded grammatical subjects “Core architecture is” and
“Architecture is” before validating the completed judgment. It does not search
arbitrarily for sound or count the subject as explanatory content. Equivalent
subject-prefixed/canonical repeated judgments agree; unfinished, placeholder,
negated or alternative judgments still fail.

The unchanged latest report passes through its actual receiving channel, taking
the full latest delivery replay from 38/40 to 40/40 alongside the numbered-
findings fix. The mixed-state replay passes 36/36. Negative historical controls
retain their failing counts; 104 benchmark tests pass with one optional skip.
Archived verdicts and reports stay unchanged. No model calls or deployment.
[Repair task](../../tasks/done/strat-review-checker-format-compatibility.md).
