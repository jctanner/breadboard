#!/usr/bin/env python3
"""Seed one fresh, distinct RFE for the agent-led POC in local Jira.

Earlier POC runs reused one `rhai-cli diagnose` template (RHAIRFE-1..10).
Each scenario here is a different area that the fetched architecture context
(rhoai-3.6-ea.2) documents, so reviews can check real claims:

- `dsp-retention` (RHAIRFE-11, run in pipeline 2077): Data Science Pipelines
  artifact retention (data-science-pipelines-operator, persistence agent,
  Argo WorkflowArtifactGCTask).
- `registry-serving-guard`: Model Registry protection for served versions
  (the registry's InferenceService sync controller).

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

SCENARIOS = {
    'dsp-retention': ('fullsend-agent-led-poc-a3',
                      'Configurable retention for Data Science Pipelines run artifacts',
                      DSP_RETENTION),
    'registry-serving-guard': ('fullsend-agent-led-poc-a3-registry',
                               'Block archiving Model Registry versions that are still being served',
                               REGISTRY_SERVING_GUARD),
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
