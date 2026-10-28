# Repair prepared strategy import completeness and recovery

## Scope

The owner approved addressing the two functional findings from review 5623201873
on PR #85: 4355503644 (overflow without the full strategy attachment) and
4355503650 (task existence mistaken for completed import). Begin from clean
0707b5b on feat/s1-workflow-hardening. Use local emulator regressions and the
required full suite; no paid smoke, live service mutation or push in this task.
Preserve Org Pulse's accepted exception and current workflow/approval design.

## Acceptance

- [x] Reproduce missing-overflow attachment and interrupted-context import.
- [x] Reject incomplete overflow input before replacing an existing task.
- [x] Completion means all required context downloads and local publication finished.
- [x] Retry completes missing context while preserving existing refined task bytes.
- [x] Completed imports remain idempotent and refuse ambiguous/bound-review recovery.
- [x] Required full suite, lint, descriptors and diff checks pass.
- [x] Archive sanitized evidence and update notes/bugs with source state and limits.

[Implementation and evidence](../../notes/strat-pr85-import-recovery-20261023.md).
All 90 focused checks pass. Full suite: 1,275 passed/six optional skips,
417.30 seconds. Lint, type descriptors and whitespace checks pass.
Sixteen-file archive `var/run-data/20261023-strat-pr85-import-recovery-fixes/`
passes configured-credential scanning (zero findings) and hash readback.
The owner subsequently authorized commit and push. All four tested files were
published as signed-off `fbbbc6eb10e67472d15bad0a80b850873bce8d95` to
the existing fork branch `feat/s1-workflow-hardening`. Staged bytes match the
archive, with zero credential findings. GitHub API confirms this exact PR #85
head; the component worktree is clean. No paid smoke, live Jira/export mutation,
review reply, deployment or merge. New remote CI/review results were not assessed
in this publication task.
