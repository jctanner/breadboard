# S1 hardening 8: validate replay freshness

Track relevant input, instruction, Skill and source identity when saving reusable
phase results. Changed shared files must invalidate or explicitly reject stale
results, even when the original prompts/options still match.

Acceptance: unchanged inputs reuse valid work; changed inputs do not silently
reuse incompatible results. Record the chosen freshness contract.

Pending, after item 7. [Plan](../../plans/strat-workflow-s1-hardening.md).
