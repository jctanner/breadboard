# S1 hardening 1: preserve reviewer Skill assessments

## Goal

Deliver all four reviewer reports to a schema-bearing Workflow receiver through
their intended Skill results, without native-transcript scraping.

## Acceptance

- [x] Preserve historical pins; create an isolated local hardening branch.
- [x] Configure real reviewer Skills with explicit agent tools excluding StructuredOutput.
- [x] Preserve the outer schema and the tools needed by each role.
- [x] Pass focused offline/native controls once per case.
- [x] Run one focused GLM scenario; verify effective tools and all four delivered bodies.
- [x] Archive available system and job evidence under private var/run-data.
- [x] Record limitations, source/binary/model pins and results before item 2.
- [x] Run relevant checks and git diff --check.

## Status

Done, 2026-10-13. Focused repair verified on GLM. No Haiku/Opus or repeated scenario.

## References

[Plan](../../plans/strat-workflow-s1-hardening.md),
[bug](../../bugs/open/strat-workflow-reviewer-output-loss.md),
[verified workaround](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-specialist-handoff.md).

## Progress

Candidate `c49b43c` published on local `eval/s1-hardening`; original pins unchanged.
835 repository tests passed (7 opt-in tests skipped). One native stub control
confirmed effective reviewer tools and delivered assessment/dissent/target with
the outer schema intact. The one focused GLM job completed: 4/4 assessments
delivered, exact three-tool reviewer whitelist, valid outer result and completed
native state. All 50 model requests are GLM. The final archive and separate native
control archive independently verify; no reset occurred.
[Evidence and limitations](../../notes/s1-hardening-01-reviewer-delivery.md).
