# Scorer is required to run a shell command without a shell tool

Feature head f5691f7: workflows/strat-pipeline.js asks strat-scorer to run
publish_review.py --check-only. Its agent definition permits Read/Write/Glob/
Grep and explicitly no other capabilities. All nine scorers in mixed Opus run
markov-run-5d3327ed invoked no Bash, proceeded to score and wrote outputs.
Thus the successful fresh-review run does not validate that recovery preflight.
The check belongs in a capable mechanical step or another explicit supported
contract. Review comment 4295376508 is confirmed; no repair made here.

[PR triage](../../notes/strat-creator-pr85-review-triage.md).

## Fixed in source, 2026-10-16

strat-creator commit f941955 on feat/s1-workflow-hardening. A shell-capable prepare-reviews step runs deterministic recovery before scorer dispatch. The restricted scorer prompt contains no shell preflight. Regressions recover completed/fully captured reviews without the original scorer file and skip both scorer/reviewer agents.
No paid model batch was rerun for this remediation; historical evidence is unchanged.
