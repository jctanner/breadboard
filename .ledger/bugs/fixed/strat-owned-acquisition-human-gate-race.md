# Owned RFE acquisition misses concurrent human gates

PR #85 comment 4382955258, reproduced on 0d60824 against local Jira. After
the first label read, add human-sign-off or needs-attention before the lock
write/final read. Fresh and recovered acquisition return the gated RFE anyway.
Recovered claims already gated at the initial read fail, but can omit the
candidate from a rebuilt cleanup record. A source RFE gate captured in a valid
freshness baseline also escapes the ownership-only downstream write guard.

The bounded acquisition/release audit also found the lock reader still accepts
malformed requested labels; use the existing shared validator rather than an
empty-label fallback. These are related checks within owned acquisition and
publication, not a claim of atomic Jira leases or a sandbox redesign.

Expected: reject work, retain durable candidate intent for owner-checked cleanup,
preserve human/unrelated labels, keep foreign-owner refusal, and block managed
writes even if the gate was captured in the baseline. Numeric policy unchanged.

Evidence: /tmp/strat-pr85-lock-schema-red.log (19 failures, two controls).
Task: [approved review work](../../tasks/done/strat-pr85-review-0d60824.md).

Fixed in 364e1ca. Final acquisition reads reject human gates; recovered owned
claims are recorded before rejecting their gate. The existing label validator
also protects acquisition reads. Downstream writes reject source RFE human gates
even when the baseline matches. Real release-script regressions preserve human
labels and refuse foreign claims. Full offline: 1,434 pass, six optional skips.
Evidence: var/run-data/20261026-strat-pr85-lock-schema/.
