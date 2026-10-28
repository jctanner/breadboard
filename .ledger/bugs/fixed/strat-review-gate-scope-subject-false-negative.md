# Reviewer gate rejects a completed scope judgment with a grammatical subject

Observed 2026-10-18 in Opus 5.5 mixed-state run markov-run-296d9e2e, benchmark
0b89021 and unchanged S1 candidate 6ed858b. Original benchmark remains FAIL on
reviewer_outputs_returned. The checker repair below is subsequent to that run;
no paid rerun has been performed.

RHAISTRAT-1's 6,119-character scope report says:

> **Scope assessment**: The capability is right-sized but loosely bounded.

It contains explicit findings, requested revisions and Recommendation: revise.
role-assessment-v2 requires the judgment to begin with a canonical outcome and
does not normalize this scope subject. It therefore reports a missing/unfinished
judgment and projects result_chars=0 despite content_chars=6119.

Independent audit joins the report to its actual receiving Skill result,
native producer, provenance hash and verbatim composed review. All forty
selected role reports pass these delivery/preservation checks. No lost handoff
or peer-ticket access was found by the mechanical audit.

An in-memory diagnostic removes only "The capability is" from the scope field.
The same checker then accepts the report. Neither the report nor the pinned
checker or historical evaluation is modified. This reproduces a mechanical
format false negative, without establishing that the report's technical claims
are correct.

Proposed repair: support a bounded grammatical subject for the scope judgment,
with negative controls for unfinished/ambiguous/conflicting judgments and
wrong-target/status/error content. Validate by replay against the retained
receiving channel and existing negative captures; another paid batch is not
needed to demonstrate this parser defect.

## Resolution

Fixed in role-assessment-v3, published in Breadboard
d3a8a8f859393f6eae1b0098ff6ab36d720390c8 and synced/imported into Markovd.
Normalize only the bounded scope/capability subject before the existing verdict
and rationale checks. The unchanged receiving channel now passes all 40/40
required pairs, with only RHAISTRAT-1 scope changing. The original FAIL stays
unchanged. Five authored regression methods, 32 focused checks and the full
114-test suite pass (two optional skips); seven historical controls retain
their previous results. No inference calls or revision-rate analysis.
[Completed repair and verified evidence](../../tasks/done/strat-review-scope-subject-checker.md).

See [run analysis](../../notes/s1-opus55-mixed-ten-20261018.md) and
[hardening plan](../../plans/strat-workflow-s1-hardening.md).
