# A7: GitLab runner job pod cleanup

Follows [A4](../done/agent-led-strategy-batch-events.md). Plan:
[agent-led strategy POC](../../plans/fullsend-agent-led-strategy-poc.md).

## Goal

Kubernetes-executor job pods are deleted when their job finishes.

## Context

Pods for jobs 3924 and 4037 stayed in `Error` (both containers exit 137)
after the jobs finished; GitLab status and artifacts were unaffected
([bug](../../bugs/open/gitlab-runner-job-pods-left-in-error.md)). They are
kept as evidence. Likely in the runner's pod-deletion path, or a grace
period or finalizer interaction in K3s.

## Acceptance criteria

- [ ] Root cause found from runner logs, pod events and the runner config
  in `deploy/k8s/21-gitlab-runner.yaml`.
- [ ] Fix in the runner deployment (`deploy/k8s/`, `deploy/scripts/`).
- [ ] A new successful job and a new failed job each leave no pod behind.
- [ ] Retained evidence pods deleted after the fix is proven; bug moved to
  `fixed/`; `git diff --check`.

## Breakpoints

| # | What you get | How to check | Question |
| --- | --- | --- | --- |
| B7.1 | Root cause and proposed fix | Ledger note, diff | Apply it? |
| B7.2 | Two test jobs with no pod left; evidence pods removed | `kubectl get pods -n gitlab-runner` | Close A7? |

## Verdict log

| Breakpoint | Verdict | Date | Notes |
| --- | --- | --- | --- |

## Status

Pending, 2026-10-08.
