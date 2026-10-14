# Fixed: scope diagnostic passed a plugin path as the prompt

## Summary

The 9ec3db8 diagnostic launcher supplied two plugin paths after one
`--plugin-dir` flag. Claude Code 2.1.296 interpreted the second path as the
user prompt. GLM inspected that fixture and attempted to launch the test script
through Bash instead of entering the intended named Workflow. No live scope
result was established. Host stopped the job to prevent recursive model work.

## Repair and evidence

107e7af repeats `--plugin-dir` for each plugin and disallows Bash/Edit/Write/Agent
for this diagnostic. Production S1 tools are unchanged. The native v5 control
loads both plugins and the exact named fixture, verifies the expanded initial
prompt and tool list, then passes all 12 role/target deliveries and scope hooks
with zero provider calls. Component suite: 867 passed, 7 opt-in skipped.

The failed attempt remains archived separately, including explicit cancellation
and deleted-pod limitations. The corrected live execution remains a separate
result. [Evidence](../../notes/s1-hardening-02-reviewer-scope.md).

## Status

Fixed on local eval/s1-hardening at 107e7af. Premium models were not used.
