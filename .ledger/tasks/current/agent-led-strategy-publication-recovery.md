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

## B5.1: emulator fixes deployed (2026-10-08)

### GitLab emulator: bridges wait (`checkouts/gitlab-emulator` `3fc4480`, main, not pushed)

- **`app/services/bridge_jobs.py` (new):** `dispatch_ready_bridges()`
  creates the downstream pipeline for each `pending` bridge whose stage or
  `needs:` are satisfied, using the runner's `_job_stage_is_unblocked`. A
  creation failure marks the bridge `failed` and skips later stages.
  Without `strategy: depend`, the bridge succeeds once the child exists.
- **Called from** both `_derive_pipeline_status` functions (runner and
  pipelines APIs), which every job update, play, retry and cancel already
  goes through. `_create_pipeline` no longer dispatches every bridge at
  creation. Runner polls exclude bridges. A retried bridge clears its
  downstream ID, so it creates a new child.
- **Tests (new):** later-stage bridge waits, then dispatches, and the runner
  never receives it; failed upstream skips the bridge and creates no child;
  `needs:` dispatches it before an unrelated stage; retry creates a new
  child. Full suite: 746 passed, 3 failed. The 3 failures also fail on the
  unmodified code (`test_pipeline_variables_merge_with_yaml_and_job_precedence`,
  `test_project_variables_reach_runner_payload_with_precedence`,
  `test_parse_gitlab_ci_applies_richer_rules_if_expressions`).
- Deployed with `make host-rebuild-gitlab` (data on the PVC kept).

### Org Pulse: stale key cleared on ingest (`checkouts/rhai-org-pulse` `718ffa29`, branch `feature/configurable-forge-hosts`, not pushed)

The cause had two parts. AI Impact's post-ingest sync ran only when a
review was `created`, and it called `refresh-all` with a `handlers`
selector that core ignores, so the 12h cadence skipped `jira-sync`.
- **Releases `POST /ai-review/bulk`:** reports `stale`, the number of
  incoming keys whose feature file has `_stale`. It does not clear the
  flag; only Jira sync decides whether the key exists.
- **AI Impact bulk ingest:** when `created > 0` or `stale > 0`, runs
  `POST /api/admin/refresh/handler` with `handlerId: releases:jira-sync`,
  the same call as the manual recovery, which ignores cadence. A non-2xx
  answer (for example 409 while another refresh runs) is logged.
- **Unchanged:** jira-sync still marks keys absent from Jira stale and
  keeps the original `detectedAt`; existing aiReview and human-review
  fields are merged as before.
- **Tests:** three AI Impact route tests (created, stale, neither) and one
  releases bulk test (stale count, `_stale` kept). Full suite 6069 passed,
  11 skipped; eslint clean on changed files.
- Deployed with `make host-rebuild-org-pulse`; the running backend contains
  both changes.

### Agent-led CI: `build-dashboard` trigger

`ci/gitlab-ci.yml` adds stage `trigger` and `build-dashboard`, modelled on
strat-pipeline's: it triggers strat-dashboard `main`, with rules matching
either strategy job. `test_ci.py` checks it (6 passed). Published to GitLab
branch head `89c879b`.

### No-model pipelines

Discovery against local Jira first returned 0 eligible RFEs (16 found, all
processed).

| Pipeline | Strategy job | Bridge | Child pipeline |
| --- | --- | --- | --- |
| 2087 (`--rfe RHAIRFE-0 --allow-invalid-rfe`) | 4048 failed in the pre-script (lock of an invalid key), 12:30:32 | `pending` while the job ran, then `skipped` | none |
| 2088 (`--batch`, no work) | 4050 success, native skip (exit 78), 12:30:33 | `pending` while the job ran, then `success` at 12:30:33 | 2089 (`parent_pipeline`), created 12:30:33 |

Child 2089's pages job 4052 succeeded (12:31:11). Before this fix, the child was created as soon as the parent pipeline was.

The job pods for 2087 and 2088 (project 7, concurrent 0 and 1) were also
left in `Error`; that is A7's bug and is noted there.

## Status

Current, 2026-10-08. B5.1 evidence recorded; waiting for the verdict.
