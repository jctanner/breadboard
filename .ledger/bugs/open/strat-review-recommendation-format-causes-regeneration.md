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
