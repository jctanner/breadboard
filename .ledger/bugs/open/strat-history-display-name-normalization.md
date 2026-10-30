# STRAT history display-name normalization gap

Low severity; conditional compatibility issue. Found by owner-requested local
Claude review of PR93/13a4f71, then reproduced with synthetic offline history.
No evidence yet that live Jira emits the affected field representation.

In scripts/strat_history.py:165-173, STRAT evidence compares field names without
normalization, unlike rfe_change. A valid post-cursor sign-off history item with
field="Labels" and no fieldId is ignored. Lowercase labels, or canonical
fieldId="labels", is recognized. Description has the same comparison pattern.
For reverted changes this may cause an unnecessary batch failure; it cannot
approve stale output. Missing/unverifiable history should continue failing closed.

Potential repair: normalize recognized STRAT history field names consistently
with RFE history, retaining malformed-value handling, and cover both canonical
IDs and display-name-only entries. Not implemented during the read-only review.

Evidence: var/run-data/20261028-strat-pr93-local-claude-review/ contains review.md,
assessment.md, offline-verification.json and verify-findings.py.
Related task: [Local Claude review](../../tasks/done/strat-pr93-local-claude-review.md).
