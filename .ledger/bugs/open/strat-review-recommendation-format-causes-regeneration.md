# Recommendation formatting causes unnecessary report regeneration

Observed in finalized GLM `markov-run-cf0dfe9a` on candidate `0e7e752`.
Composition rejected three completed reports for two Recommendation lines:
scope on RHAISTRAT-2, testability and scope on RHAISTRAT-3. The Skill templates
include a Recommendation field and separately instruct the agent to end with
one such line; some reports emit both. Clarify that it appears exactly once
in the entire report, at its end, and align the template with that contract.

The final ticket's first four calls returned by 22:36:31 UTC, 26 minutes into
review. The parent diagnosed capture failures until relaunching two roles at
22:43:02. Replacements returned at 22:47:20/22:49:15, and final review progress
completed at 22:52:59. Roughly seven minutes of diagnosis and six of replacement
reviews were added before four minutes of composition/publication. These were
internal calls in one benchmark job, not new benchmark iterations.

Open; no Skill/helper edit or new inference test. Preserve original and replacement
reports. Consider whether an identical repeated verdict needs regeneration;
do not silently discard conflicting verdicts or change the numeric gate.

[Timeline and archived evidence](../../notes/s1-hardening-three-rfe-glm-live-duration.md).

## Remaining variant in Opus 5.5, 2026-10-18

Exact repeated scalar verdicts were subsequently accepted by the earlier
duplicate-recommendation fix. Candidate `6ed858b` still rejects a different
format: a Recommendation field containing `revise.` plus rationale followed by
a canonical standalone `revise` field. `report_verdict` treats the entire first
line as an invalid enum, even though the last field is canonical.

In `markov-run-296d9e2e`, first testability reports for RHAISTRAT-12 and
RHAISTRAT-2 return through Skill but fail capture. Native parent transcripts
show compose failing on missing testability.json, parser inspection, then a
second Skill call for each role. Both replacements are captured and composed.
The resulting 42 launches are not strategy revisions or whole-Workflow retries.
The final five numeric revise decisions are independent of this format defect.

Do not conflate this with the fixed scope-assessment subject checker. Keep
source report bytes and conflicts protected. A narrow producer-completion
validation/repair contract and explicit invalid-receipt handling should avoid
full specialist regeneration. No component code or instructions changed here.
[Analysis and separate private evidence](../../notes/strat-opus55-revision-analysis-20261018.md).
