# S1 hardening 5: reject non-assessments at the delivery gate

Repair the benchmark checker that treats nonempty text as a returned review.
Distinguish substantive targeted assessments from completion markers, progress
messages and errors. Preserve original gate outcomes in historical archives.

Acceptance: negative fixtures fail, valid role/target reports pass, and gate
results remain separate from scope, incorporation and technical accuracy.

Done, 2026-10-14. [Plan](../../plans/strat-workflow-s1-hardening.md).

Repair the deterministic benchmark checker and replay actual archived receiving
channels. This does not require another model run or changing S1's numeric
approval policy. Keep delivery distinct from exclusive scope, final composition
and correctness; record intentional architecture skips separately.

Acceptance met by shared role/target/content validation, negative/positive
fixtures and read-only replay of six checksum-verified real captures. The two
historical false positives fail; valid saved reports pass. Original gate/pass
values are retained beside the recomputed results. 62 benchmark tests and nine
reference-checker tests pass; six optional Markov checks remain skipped.
Zero provider calls/tokens; no S1 source, numeric policy or deployment change.
[Results, evidence and limits](../../notes/s1-hardening-05-delivery-gate.md).
