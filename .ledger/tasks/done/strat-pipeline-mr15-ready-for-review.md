# Mark strategy pipeline MR !15 ready for review

## Goal

Refresh the existing MR description with the real GitLab smoke result, the
current credential mapping and known follow-ups, then remove Draft. The user
confirmed readiness after distinguishing data-repository publication from
the missing standalone documents in the downloadable CI archive.

## Acceptance criteria

- [x] Verify expected head, passing CI and unresolved-blocker state.
- [x] Describe tested behavior and untested live publication accurately.
- [x] Remove Draft and verify the resulting remote state and description.

## Boundaries

No merge, production schedule change, model run or secret provisioning.
Strat-creator PR #85 is a separate source review/deployment dependency; the
GitLab archive export gap remains a follow-up to this opt-in trial.

## Completed: 2026-10-20

[MR !15](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/15)
is open, `draft=false`, title `Add opt-in Fullsend strategy Workflow jobs`,
head `d27a314f965d7c09a0589d77c1a01a93c26a82a3`, no conflicts. Pre-write
checks confirmed passing head pipeline 2969641024 and resolved blocking
discussions. Final merge status is `not_approved`; reviewer approval remains
required. No merge or automatic merge was requested.

Description now records 74 pipeline tests, 1,136 source tests/six skips,
the successful real runner dry-run, the subsequent offline-tested credential
mapping, current source pin 080700e and its separate PR #85 dependency. It
distinguishes implemented data-repository publication (disabled in the smoke)
from the follow-up for missing standalone files in the downloadable CI ZIP.

Updated title and description in one PUT, then reconciled by GET. The first
exact-description assertion failed because GitLab strips the final newline;
a separate read confirmed the complete text otherwise matches and Draft is
removed. No write retry was made. Root `git diff --check` passes; no code,
model run, secret or production schedule change.
