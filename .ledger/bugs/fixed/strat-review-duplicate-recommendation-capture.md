# Duplicate identical recommendation prevents review capture

Status: fixed and published on feat/s1-workflow-hardening in the Fullsend fork
as fbc335bedb4a4eb97265da89d36bc29009a41fde, with the independent Breadboard
benchmark rule aligned. The mixed-state tier pins this fix; historical
run/source pins remain unchanged.

## Summary

The live S1 review-composition hook rejects a delivered report when the same
`**Recommendation**: revise` line appears twice in the report. The decisions
agree, but `report_verdict()` requires exactly one
regex match. A detailed, scoped assessment is consequently absent from the
composition session and cannot be published.

## Observed failure

Ten-RFE Opus run markov-run-fbc62d49, model job
script-run-workflow-all-claude-opus-4-6-1015-193904-1a3da4, candidate 6a05210,
Claude Code 2.1.296, cap ten, 2026-10-15:

| Strategy | Role | Delivered characters | Recommendation matches | Captured |
| --- | --- | ---: | --- | --- |
| RHAISTRAT-3 | feasibility | 8,564 | revise, revise | No |
| RHAISTRAT-7 | testability | 7,878 | revise, revise | No |

All forty role assessments returned across the ten review callers. Thirty-eight
were captured. For the two rows above, the PostToolUse capture rejects the
report, `compose` fails with a missing feasibility.json or testability.json,
and publication and record-review cannot finish. The callers return
approve/needs_attention=true; the JavaScript workflow rejects those inconsistent
receipts. Final business validation fails, as it should for partial work.
Eight final reviews were published, two remained incomplete. The numeric scores
were not changed to follow the prose reviewers; numeric-only-v1 remains intact.

The fragile parser is
.fullsend/plugins/strat-pipeline/scripts/review_composition.py:report_verdict
in the Fullsend strat-creator fork. This is a live pipeline defect, separate
from the benchmark checker's additional feasibility-format false negatives.

## Offline reproduction against the original parser

Extract each unchanged report from its saved review caller's native tool_result.
Call 6a05210's `report_verdict` with the assigned strategy/RFE scope and role.
Both produce `Report must contain one exact Recommendation: approve, revise,
reject (architecture may be skipped)`. Scope checks pass first.

Remove only the second identical recommendation line in memory and call the
same function again: both return revise. No source, report, historical verdict
or saved result was edited. No model calls were needed.

## Follow-up

The reviewer instructions likely contribute to this behavior. Both Skills
include a Recommendation field in their output template and separately say
to end with exactly one Recommendation line. This specifies the ending without
explicitly prohibiting an earlier occurrence. RHAISTRAT-3 puts the template
summary verdict at line 7 and repeats it after detailed findings at line 86.
RHAISTRAT-7 gives its verdict at line 53, lists requested changes, and repeats
the verdict as its final line 63. Both follow the ending instruction. The model's
internal reason is unknown, but the observed structure fits summary plus
explanation plus a required final verdict. The parser imposes a stricter global
occurrence count than the prompt clearly states.

Follow-up inspection located the actual reviewer agents ae6f7f8cdac0287f0
(feasibility RHAISTRAT-3) and ab8e7bc014b1a1cf0 (testability RHAISTRAT-7),
separate from their receiving Workflow callers. Their native transcripts contain
six and three thinking blocks respectively. No explicit plan to duplicate the
verdict was found in the recorded material; the relevant reasoning concerns
the assessment content. The matched API responses redact their thinking.
Receiving callers explicitly discuss the duplication after capture fails.
Those later explanations establish recognition of the parser failure, not
the original reviewers' intent. Prompt ambiguity remains a likely explanation,
not a demonstrated deliberate decision to repeat the verdict.

Clarify that the template describes the whole assessment, including where
findings/requested changes belong, with one final canonical decision field.
Accept repeated identical recommendations while rejecting absent, unfinished
or conflicting recommendations. Preserve the original report bytes and hash;
normalize only decision extraction. Keep wrong-ticket and architecture-only
skip checks. Cover both archived reports and negative cases offline before any
new inference. GLM remains the iterative model; another Opus run needs approval.

## Evidence

Final verified archive under var/run-data/strat-workflow-hardening/:
fullsend-vertex-opus-ten-rfe-c10-20261015/markov-run-fbc62d49/20261015T203122658615Z.

Review caller IDs a8b03cca0d98e337f (RHAISTRAT-3) and a6ebd476708d3c33e
(RHAISTRAT-7) are saved under the native Workflow journal directory. Their
composition sessions, failed result, validation text and all original reports
remain in the archive. [Run audit](../../notes/s1-fullsend-opus-ten-rfe-20261015.md).

## Local fix and validation

The plugin and scripts/review_composition.py extract all canonical
Recommendation fields and require one unique valid value. Repeated agreeing
values are accepted. Missing, blank, placeholder, invalid or conflicting values
fail, and skipped remains architecture-only. Report text and hashes are not
normalized or rewritten; the numeric-only decision policy is unchanged.

The independent benchmark classifier applies the same agreement rule while
retaining its existing completed-assessment checks. Its separate numbered-
findings false negatives remain open. Historical source, reports and FAIL stay
unchanged.

Validation: 47 focused composition tests; make test-unit, 575 passed / five
skipped; make test, 1,033 passed / seven skipped; all 79 benchmark tests pass.
Ruff for the changed component files and both git diff --check pass. Both
unchanged failing reports pass the plugin helper, host helper and benchmark
classifier. The live parser accepts all forty original role reports. Tests
cover capture, composition, trusted host verification, exact exported bytes and
hashes, numeric policy, architecture skips and rejection of missing/conflicting
or invalid decisions. No model calls or new run.

[Fix task](../../tasks/done/strat-review-agreeing-recommendations.md).
