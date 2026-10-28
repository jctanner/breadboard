# Strategy type descriptor omits pending reviewer values

During PR #85 review check on 0d60824, comment 4382955276 repeated the request
to document pending in the review schema. The executable runtime schema at
scripts/artifact_utils.py:218-243 accepts pending (and architecture skipped),
while types/rfe-strategy/type.yaml:109-116 still lists only approve/revise/reject
and says reviewers use the recommendation enum. CLAUDE.md documents pending's
provisional meaning and existing downstream tests pass, but the declarative
descriptor does not match the runtime contract.

Expected: align reviewer enums/descriptions with runtime, preserving the
separate numeric approval decision. No new consumer failure has been observed.
This is a source-level contract mismatch; no implementation/reproduction run
in the read-only status check.

Related task: [latest PR review](../../tasks/done/strat-pr85-review-0d60824.md).
Review: https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4382955276.

Fixed in 364e1ca. Descriptor reviewer enums now exactly match runtime, including
pending and architecture skipped, with comments explaining their provisional
meaning. Recommendation vocabulary and numeric gate unchanged. Four parity
tests and a recommendation control pass; full offline: 1,434 pass/six skips.
Evidence: var/run-data/20261026-strat-pr85-lock-schema/.
