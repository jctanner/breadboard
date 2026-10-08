# A5: Publication and dashboard without manual recovery

Follows [A4](../done/agent-led-strategy-batch-events.md). Plan:
[agent-led strategy POC](../../plans/fullsend-agent-led-strategy-poc.md).

## Goal

A strategy run publishes, appears in Org Pulse and rebuilds the dashboard
with no manual step. Every A3 and A4 run needed two recoveries: a manual
`releases:jira-sync`, and a hand-started dashboard pipeline.

## Context

- **Org Pulse:** a recreated Jira key keeps its `_stale` flag after a
  valid ingest, so the feature returns 404 until `releases:jira-sync` runs
  ([bug](../../bugs/open/org-pulse-ingest-recreated-jira-keys-stay-stale.md)).
- **GitLab emulator:** `_create_pipeline` starts downstream bridges as soon
  as the parent jobs exist, so the dashboard builds before results are
  committed
  ([bug](../../bugs/open/gitlab-emulator-downstream-trigger-runs-before-upstream.md)).
  Both POCs work around it by rebuilding the dashboard by hand.
  Real GitLab treats a bridge like any other job: it starts after earlier
  stages and its `needs:`, is skipped when they fail (`when: on_success`),
  and without `strategy: depend` succeeds once the child pipeline exists.
  The emulator differs only in starting bridges at pipeline creation
  (`app/api/pipelines.py:2311`); ordinary jobs are already gated by the
  runner (`app/api/runner.py`, `_job_dependencies_are_terminal`).
- **Agent-led CI has no dashboard trigger:** `ci/gitlab-ci.yml` has no
  `build-dashboard` job, unlike strat-pipeline
  (`checkouts.tmp/gitlab_rhel_agentic_ci/strat-pipeline/.gitlab-ci.yml:211`,
  stage `trigger` after `strategy`). The dashboards for 2079 and 2085 were
  built by hand.
- **RHAISTRAT-11:** processed in Jira by pipeline 2077, but never
  published, because the validator then wrongly required unanimous prose
  reviewers ([A3](../done/agent-led-strategy-single-ci.md)).

## Acceptance criteria

- [ ] Org Pulse: a valid ingest of a previously stale key makes it readable
  immediately; genuinely absent Jira issues still go stale; existing
  human-review metadata is kept. Tests cover Jira reset and key reuse.
  Deployed with `make host-rebuild-org-pulse`.
- [ ] GitLab emulator: a bridge job is created waiting and is dispatched
  under the same stage, `needs:`, manual and failure rules the runner uses
  for ordinary jobs; a failed upstream skips it and starts no child.
  Without `strategy: depend` the bridge succeeds once the child exists, as
  in GitLab. Tests added; emulator redeployed.
- [ ] Agent-led CI gains a `build-dashboard` trigger job modelled on
  strat-pipeline's (stage `trigger` after the strategy jobs, triggering
  strat-dashboard `main`), with fixture tests updated.
- [ ] One agent-led run (single is enough) shows Org Pulse readback and a
  dashboard pipeline started by the native trigger after the results
  commit, with no manual step.
- [ ] RHAISTRAT-11 published from pipeline 2077's retained artifacts
  through the host validator and post-script, with no new model run and
  no Jira write. If the artifacts no longer validate, record why instead.
- [ ] Bugs moved to `fixed/`; `git diff --check`; component tests pass.

## Breakpoints

| # | What you get | How to check | Question |
| --- | --- | --- | --- |
| B5.1 | Both emulator fixes with tests, deployed | Test output; a no-model pipeline showing the bridge waits | Are the fixes right? |
| B5.2 | One real run with automatic Org Pulse and dashboard | Org Pulse GET, dashboard pipeline timestamps vs. results commit | Is the end-to-end path clean? |
| B5.3 | RHAISTRAT-11 published from retained artifacts | strat-pipeline-data commit, dashboard | Close A5? |

## Verdict log

| Breakpoint | Verdict | Date | Notes |
| --- | --- | --- | --- |

## Files likely involved

- `checkouts/` Org Pulse core (feature store, ingest, refresh handlers)
- `checkouts/gitlab-emulator/app/api/pipelines.py`
- `checkouts/gitlab-emulator/app/api/runner.py`
- `var/demos/fullsend-agent-led-poc/{ci/gitlab-ci.yml,test_ci.py,publish.py}`

## Status

Pending, 2026-10-08.
