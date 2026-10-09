#!/usr/bin/env python3
"""Seed one fresh, distinct RFE for the agent-led POC in local Jira.

Earlier POC runs reused one `rhai-cli diagnose` template (RHAIRFE-1..10).
Each scenario here is a different area that the fetched architecture context
(rhoai-3.6-ea.2) documents, so reviews can check real claims:

- `dsp-retention` (RHAIRFE-11, run in pipeline 2077): Data Science Pipelines
  artifact retention (data-science-pipelines-operator, persistence agent,
  Argo WorkflowArtifactGCTask).
- `registry-serving-guard` (RHAIRFE-12, pipeline 2078): Model Registry
  protection for served versions (the registry's InferenceService sync
  controller).
- `workbench-cull-exemption` (A4 batch): per-workbench idle-culling
  exemptions (the notebook controller's optional culling).
- `trustyai-drift-alerts` (A4 batch): alerting on scheduled TrustyAI drift
  metrics (the service's metric scheduler and Prometheus publication).
  RHAIRFE-13/14 ran in pipeline 2083, which stopped mid-batch.
- `feast-scheduled-materialization` (A4 batch 2): scheduled incremental
  materialization of Feast feature views (feature server materialization).
- `kueue-admission-visibility` (A4 batch 2): explaining why a queued
  workload is not admitted (Kueue LocalQueue/ClusterQueue admission).
- `kserve-canary-rollback` (A5 single): automatic rollback of a canary
  model rollout on error or latency regressions (KServe InferenceService
  canary traffic split).

Content is fictional; no customer or person names.

Idempotent per scenario: if an RFE with the scenario's marker exists, prints
it and creates nothing. No reset, and no change to existing issues.

Environment: JIRA_CA_FILE; credentials come from the
`ai-pipeline/fullsend-strategy-jira` secret (the bot identity CI uses).
"""
import argparse
import base64
import json
import os
import subprocess
from urllib.parse import quote

import httpx

SERVER = 'https://jira.local'
ELIGIBILITY = ['strat-creator-3.6', 'rfe-creator-autofix-rubric-pass',
               'rfe-creator-feasibility-pass']

DSP_RETENTION = """h2. Problem Statement

Data science teams run pipelines many times a day while iterating on a model.
Every run writes intermediate artifacts (datasets, feature files, model
checkpoints, metrics) to the S3-compatible object storage configured for the
project's pipeline server. Nothing removes them when the run record is
deleted or ages out, so storage grows without bound. Platform administrators
find out when the bucket fills or the storage bill arrives, and then clean up
by hand with object-store tools, with no reliable way to tell which artifacts
still back a registered model or a run someone needs for an audit.

h2. Desired Outcome

A project administrator can set an artifact retention policy on the pipeline
server for a project: keep artifacts for N days after the run finishes, and
always keep artifacts of runs that are pinned or whose outputs were
registered as a model version. Expired artifacts are deleted from object
storage automatically, and each deletion is recorded so the administrator can
see what was removed and why.

h2. Acceptance Criteria

* A retention period (in days) can be set per pipeline server; the default keeps today's behaviour (no automatic deletion)
* Runs can be pinned so their artifacts are never deleted by the policy
* Artifacts referenced by a registered model version are never deleted by the policy
* Expired artifacts are removed from the configured object storage without deleting the run record or its metadata
* A deletion log records run ID, artifact path, size and reason, and is visible to project administrators
* A dry-run mode reports what would be deleted and the storage that would be reclaimed, without deleting anything
* Deletion failures (for example, missing permissions on the bucket) are reported and retried, and never block new pipeline runs
* Upgrading an existing installation does not delete anything until a retention period is explicitly set

h2. User Stories

* As a project administrator, I want artifacts of old experiment runs removed automatically so object storage stays within budget.
* As a data scientist, I want to pin the runs that produced a promising model so their artifacts are kept.
* As an auditor, I want a record of what was deleted, when, and under which policy.

h2. Technical Notes

Pipeline servers are configured per project today. Workflow artifact garbage
collection already exists in the underlying workflow engine, and the
persistence agent already performs run retention work; the strategy should
decide whether to build on those rather than add a new controller. The
model registry is the source of truth for which artifacts back a registered
model version.
"""


REGISTRY_SERVING_GUARD = """h2. Problem Statement

Teams register model versions in the Model Registry and deploy them with
KServe. The registry already learns which versions are being served, but
nothing stops someone from archiving a version that a live inference service
still uses. When that happens, the version disappears from the default
registry views, lineage and approval checks treat it as retired, and the
on-call engineer debugging the endpoint cannot find the model it serves.
Cleanup jobs that act on archived versions can also remove artifacts that a
running service still loads on restart.

h2. Desired Outcome

Archiving a model version that is currently deployed is blocked by default.
The user sees which inference services, in which namespaces, still serve it,
and can archive only after those services stop using it. A registry
administrator can override the block with a recorded reason when an
emergency requires it.

h2. Acceptance Criteria

* Archiving a model version that one or more inference services serve fails with a clear error listing those services and namespaces
* The same check applies through the UI, the REST API and the Python client
* Versions with no active deployments archive exactly as today
* A registry administrator can force-archive with a required reason; the override is recorded with user, time and reason
* Deployment status shown for a version reflects the registry's synchronized serving state, including services in other namespaces that select this registry
* If serving state is stale or unavailable, the user is warned rather than silently allowed or blocked
* Existing archived versions are not changed by the upgrade

h2. User Stories

* As an ML engineer, I want to be stopped before I archive a model that production still serves.
* As an on-call engineer, I want the model behind a live endpoint to stay discoverable.
* As a registry administrator, I want an audited override for emergencies.

h2. Technical Notes

The registry already has a controller that watches inference services and
synchronizes their serving state into the registry through its API; the
strategy should decide whether the guard belongs in the registry API, the UI
backend, or both, and how cross-namespace registry selection affects the
check.
"""

WORKBENCH_CULL_EXEMPTION = """h2. Problem Statement

Workbenches are stopped automatically when they look idle, which saves GPU
and memory for everyone. Data scientists who run long training or data
preparation cells inside a notebook lose that work when the culler decides
the kernel is idle because nobody has touched the browser tab for a while.
Today the only escape is to ask an administrator to disable culling for the
whole cluster, or to keep a browser tab open and click around.

h2. Desired Outcome

A user can mark a single workbench as temporarily exempt from idle culling
for a bounded period, within limits an administrator sets. The exemption is
visible on the workbench, expires on its own, and is recorded so
administrators can see who is holding resources and why.

h2. Acceptance Criteria

* A workbench can be exempted from idle culling for a chosen period, up to an administrator-defined maximum
* Administrators can disable exemptions entirely or limit them per project
* The exemption and its expiry are visible in the dashboard on the workbench
* When the exemption expires, normal idle culling resumes without restarting the workbench
* Exemptions are recorded with user, workbench, start, end and an optional reason
* Workbenches without an exemption are culled exactly as today
* Upgrading leaves existing culling configuration and behaviour unchanged

h2. User Stories

* As a data scientist, I want my overnight training cell to finish without my workbench being stopped.
* As a platform administrator, I want exemptions to be bounded and visible so idle resources are still reclaimed.

h2. Technical Notes

Idle culling is an optional behaviour of the notebook controller. The
strategy should decide where an exemption is stored, how the culler reads it,
and how the dashboard presents it, without changing culling for other
workbenches.
"""

TRUSTYAI_DRIFT_ALERTS = """h2. Problem Statement

Teams configure scheduled drift and fairness metrics for deployed models in
TrustyAI. The values are calculated in the background and exposed as
Prometheus metrics, but nothing tells the model owner when a metric crosses
an acceptable threshold. Owners find out from dashboards they rarely open, or
after a downstream complaint, by which time a drifting model may have served
bad predictions for days.

h2. Desired Outcome

When a scheduled metric for a model crosses a threshold the owner set, the
project's owners are notified through the cluster's existing alerting, with
the model, metric, value, threshold and a link to the details. Thresholds are
set alongside the scheduled metric, and alerts clear when the metric
recovers.

h2. Acceptance Criteria

* A threshold and severity can be set on a scheduled drift or fairness metric
* Crossing the threshold raises an alert through the cluster's existing alerting stack; no new notification service is required
* The alert identifies project, model, metric, current value and threshold
* The alert resolves automatically when the metric returns within the threshold
* Metrics without a threshold behave exactly as today
* Alert rules are created and removed with the scheduled metric, scoped to the project
* Missing or stale metric data produces a distinct, lower-severity alert rather than silence

h2. User Stories

* As a model owner, I want to be told when my model drifts so I can retrain before users notice.
* As a platform administrator, I want alerts to use the alerting we already run.

h2. Technical Notes

TrustyAI Service already calculates configured metrics on a schedule and
publishes them through Prometheus-compatible metrics. The strategy should
decide whether thresholds live with the metric request or in separate
alert-rule resources, and who owns the rules' lifecycle.
"""

FEAST_SCHEDULED_MATERIALIZATION = """h2. Problem Statement

Data scientists define feature views in a project's feature store and serve
them online to models. Keeping the online store current means running
materialization by hand or from a home-grown cron job per feature view. When
someone forgets, or the job breaks, models quietly read old feature values,
and nobody can see when a feature view was last loaded or whether the last
load succeeded.

h2. Desired Outcome

A feature view owner can give a feature view a materialization schedule.
The platform then loads only the new data since the last successful run, on
that schedule, and shows each feature view's last successful
materialization, the next scheduled run and the outcome of recent runs.

h2. Acceptance Criteria

* A schedule (interval or cron expression) can be set per feature view
* Scheduled runs materialize incrementally from the last successful end time
* A failed run is retried with backoff and does not advance the last successful end time
* Each feature view shows last successful materialization time, next run and recent run outcomes
* Runs for one feature view never overlap; a run still in progress delays the next one
* Feature views without a schedule are unchanged and can still be materialized on demand
* Schedules are removed when their feature view is deleted

h2. User Stories

* As a data scientist, I want my online features refreshed on a schedule without maintaining my own cron job.
* As a model owner, I want to see how fresh the features behind my model are.

h2. Technical Notes

The feature server already exposes materialization and incremental
materialization. The strategy should decide where schedules run (a
platform scheduler, a per-feature-store controller or pipelines) and where
run history is kept.
"""

KUEUE_ADMISSION_VISIBILITY = """h2. Problem Statement

Training jobs and other batch workloads submitted from a project wait in a
queue until the cluster admits them. Users see only that their job is
pending. They cannot tell whether it is waiting for quota, blocked by a
higher-priority workload, or will never fit, so they resubmit, delete and
recreate jobs, or ask administrators to investigate a queue they cannot see.

h2. Desired Outcome

For any pending workload in their project, users can see its position in
the queue, the reason it has not been admitted in plain language, and the
quota it is waiting for. Administrators can see the same information across
queues, without granting users access to cluster-scoped queue
configuration.

h2. Acceptance Criteria

* A pending workload shows its queue, its position and the current reason it is not admitted
* Reasons distinguish insufficient quota, preemption by higher priority, and requests that can never fit the queue
* A request that can never fit is reported as such immediately, not left pending silently
* Users see only workloads in projects they can access; cluster-scoped queue details are summarised, not exposed
* Administrators can list pending workloads across queues with the same reasons
* The information is available in the dashboard and through the CLI
* Workloads in namespaces not managed by queueing are unaffected

h2. User Stories

* As a data scientist, I want to know why my training job is still pending and roughly when it will start.
* As a platform administrator, I want to answer "why is my job stuck?" without reading queue internals.

h2. Technical Notes

Admission is handled by Kueue through namespaced LocalQueues and
cluster-scoped ClusterQueues, and only for namespaces opted in to queueing.
The strategy should decide how pending reasons and positions are derived and
exposed to project users without widening their RBAC.
"""

KSERVE_CANARY_ROLLBACK = """h2. Problem Statement

Teams roll out a new model version to a served endpoint by sending a share
of traffic to it as a canary. Today someone must watch dashboards and
manually shift traffic back if the new version returns more errors or is
slower. Regressions found overnight or during busy periods reach many
users before anyone reacts, and the manual rollback steps differ between
teams.

h2. Desired Outcome

Model owners can declare health thresholds for a canary rollout. The
platform compares the canary with the current version during the rollout,
and either promotes it in steps or rolls it back automatically, recording
why. Owners are told what happened without watching the rollout.

h2. Acceptance Criteria

* Owners can set error-rate and latency thresholds, an observation window and promotion steps for a rollout
* During a rollout, canary and current versions are compared over the same window
* A threshold breach returns all traffic to the current version within one observation window
* A healthy canary is promoted step by step until it serves all traffic
* Each promotion or rollback records the metrics and reason, visible in the dashboard and CLI
* Rollouts without thresholds behave exactly as today
* Rollback never removes the current version while it still serves traffic

h2. User Stories

* As a model owner, I want a bad model version to be rolled back automatically when it starts failing.
* As a platform engineer, I want rollouts to follow the same safe procedure across teams.

h2. Technical Notes

Served models use KServe InferenceServices, which already support a canary
traffic percentage between the previous and latest revisions. The strategy
should decide where the comparison and promotion logic runs and which
metrics source it uses.
"""

SCENARIOS = {
    'dsp-retention': ('fullsend-agent-led-poc-a3',
                      'Configurable retention for Data Science Pipelines run artifacts',
                      DSP_RETENTION),
    'registry-serving-guard': ('fullsend-agent-led-poc-a3-registry',
                               'Block archiving Model Registry versions that are still being served',
                               REGISTRY_SERVING_GUARD),
    'workbench-cull-exemption': ('fullsend-agent-led-poc-a4-workbench',
                                 'Per-workbench exemptions from idle culling for long-running work',
                                 WORKBENCH_CULL_EXEMPTION),
    'trustyai-drift-alerts': ('fullsend-agent-led-poc-a4-trustyai',
                              'Alert model owners when scheduled TrustyAI drift metrics cross a threshold',
                              TRUSTYAI_DRIFT_ALERTS),
    'feast-scheduled-materialization': ('fullsend-agent-led-poc-a4-feast',
                                        'Scheduled incremental materialization for feature store feature views',
                                        FEAST_SCHEDULED_MATERIALIZATION),
    'kueue-admission-visibility': ('fullsend-agent-led-poc-a4-kueue',
                                   'Show users why a queued workload is not admitted and its queue position',
                                   KUEUE_ADMISSION_VISIBILITY),
    'kserve-canary-rollback': ('fullsend-agent-led-poc-a5-kserve',
                               'Automatic rollback of canary model rollouts on error or latency regressions',
                               KSERVE_CANARY_ROLLBACK),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--scenario', choices=sorted(SCENARIOS), required=True)
    parser.add_argument('--dry-run', action='store_true',
                        help='Print the issue that would be created')
    args = parser.parse_args()
    marker, summary, description = SCENARIOS[args.scenario]
    fields = {'project': {'key': 'RHAIRFE'}, 'issuetype': {'name': 'Feature Request'},
              'summary': summary, 'description': description,
              'priority': {'name': 'Major'}, 'labels': [marker, *ELIGIBILITY]}
    if args.dry_run:
        print(json.dumps(fields, indent=2))
        return
    secret = json.loads(subprocess.check_output(
        ['kubectl', '-n', 'ai-pipeline', 'get', 'secret', 'fullsend-strategy-jira', '-o', 'json']))
    creds = {k: base64.b64decode(v).decode() for k, v in secret['data'].items()}
    if creds.get('JIRA_SERVER', SERVER) != SERVER:
        raise SystemExit('Local Jira only')
    auth = (creds['JIRA_USER'], creds['JIRA_TOKEN'])
    with httpx.Client(verify=os.environ['JIRA_CA_FILE'], auth=auth, timeout=30) as client:
        query = quote(f'project = RHAIRFE AND labels = "{marker}"', safe='')
        found = client.get(f'{SERVER}/rest/api/2/search?jql={query}&fields=summary,labels,status')
        found.raise_for_status()
        issues = found.json().get('issues', [])
        if issues:
            issue = issues[0]
            print(json.dumps({'key': issue['key'], 'created': False,
                              'summary': issue['fields']['summary']}, indent=2))
            return
        created = client.post(f'{SERVER}/rest/api/2/issue', json={'fields': fields})
        created.raise_for_status()
        key = created.json()['key']
        issue = client.get(f'{SERVER}/rest/api/2/issue/{key}',
                           params={'fields': 'summary,labels,status'}).json()
        print(json.dumps({'key': key, 'created': True,
                          'status': issue['fields']['status']['name'],
                          'labels': sorted(issue['fields']['labels'])}, indent=2))


if __name__ == '__main__':
    main()
