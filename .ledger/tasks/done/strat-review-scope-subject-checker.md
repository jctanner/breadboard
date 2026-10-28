# Accept completed scope judgments with a grammatical subject

User requested 2026-10-18: fix the scope-checker false negative from the Opus
5.5 mixed-state batch first; defer the revision-rate investigation.

- [x] Reproduce the failure in the unchanged saved receiving channel.
- [x] Normalize a bounded scope subject before judgment and rationale checks;
      retain unfinished, negated, ambiguous, wrong-target and error negatives.
- [x] Add regression coverage, run focused/full offline checks and replay
      passing and genuinely failing historical captures without inference.
- [x] Save versioned before/after evidence outside original archives, close
      the parser bug and update the plan.
- [x] Publish the repaired checker and attest Markovd's imported files.

Scope: Breadboard benchmark checker only. Preserve S1, numeric approval policy,
the original report, source pins and historical FAIL. No paid run, Jira writes,
component image rebuild or content-quality/revision-rate conclusion is part of
this repair. Publishing the benchmark checker makes it available to future runs.
Version the revised recognition contract so new results are distinguishable.

## Repair

role-assessment-v3 strips only the bounded lead-ins "The capability is",
"Capability is", "The scope is" or "Scope is" from the assigned scope field
before matching its canonical verdict and explanatory content. It does not
search arbitrary prose for a verdict. Negation, unfinished/ambiguous/conflicting
judgments, missing rationale, wrong targets, errors and invalid receiving
boundaries still fail. S1, numeric policy and specialist recommendations are
unchanged; revision-rate analysis is deferred as requested.

## Validation

The unchanged Opus 5.5 receiving channel reproduces 39/40 before and **40/40
after**, changing only RHAISTRAT-1 scope. Before/after input hashes, original
gate and historical overall FAIL agree. No report was rewritten or normalized
in the capture. There are still 42 launches and two testability reruns.

Five authored regression methods cover the grammatical subjects, existing
canonical outcomes, missing rationale, negation/templates, ambiguity, repeated
judgments/conflicts and receiving-channel constraints. Before the repair,
positive/repeated/channel cases reproduce 18 failures; after repair all 32
focused checks pass. Full suite with real offline Markov simulations: 114 tests,
112 passed, two optional isolated-emulator skips. Compilation, staged redacted
Gitleaks and diff checks pass. Existing SQLite ResourceWarnings remain warnings.

Seven other archived jobs replay unchanged: mixed Opus 4.6 40/40, fresh Opus
4.6 40/40, prior mixed Opus 36/36, failed S1 stream 0/12, quota-stopped S2 7/12,
completed S1 with lost handoffs 2/12, completed S2 12/12. Genuine failures remain
failed. Prior v2 replay input hashes and pair classifications agree.

## Publication and evidence

Breadboard d3a8a8f859393f6eae1b0098ff6ab36d720390c8 is committed/pushed on
main. Only the checker, authored tests and README were committed; unrelated
ledger/CLI work is excluded. Markovd was idle before sync/import, and all 81
imported files match the published revision and tested source. No run was
submitted. Existing runs and explicitly pinned historical revisions keep v2.

Private evidence is retained separately from the immutable model-run archive:
var/run-data/strat-workflow-hardening/pr85-mixed-ten-vertex-opus55-20261018/analysis/checker-scope-subject-fix-20261018/.
It contains 27 files / 2,649,699 bytes: before/after sources, authored tests,
test logs, eight after replays, target before replay, input hashes, patch,
publication receipt and reproduction/retention scripts. Complete/final manifest
independently verifies with no problems. Model calls and new inference tokens: 0.
