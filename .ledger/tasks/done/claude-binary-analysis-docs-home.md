# Task: Establish the Claude binary analysis documentation home

## Goal

Keep maintained reverse-engineered insights under
`scripts/claude_binary_analysis/docs/`, as requested on 2026-10-11.

## Result

Moved fourteen plugin/workflow reports, pseudocode, discovery guidance and
compact evidence files out of ledger notes. Added the
[documentation index](../../../scripts/claude_binary_analysis/docs/README.md)
and updated the tooling README, product documentation index, ledger index
and workflow task links. Project plans/tasks/history remain in `.ledger/`;
raw artifacts remain in ignored `tmp/claude-code-binary-analysis/`.

## Validation

- Nine JSON evidence files parsed; twenty-seven documentation links checked.
- Both claim ledgers validated with local evidence paths: eleven plugin
  claims and seventeen workflow claims.
- No stale report paths found; tracked and new-file whitespace checks passed.

## Status

Done. Documentation organization only; no runtime experiments rerun.
