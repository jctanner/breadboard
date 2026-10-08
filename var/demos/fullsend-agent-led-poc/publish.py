#!/usr/bin/env python3
"""Publish the agent-led POC CI branch to the local strat-pipeline project.

Creates `feat/fullsend-agent-led-poc` from `main` if it is missing and commits
the CI files with `[skip ci]`. Shared project variables are only checked by
name, never created or changed: `main` and the script-led POC branch keep
their configuration. Optionally creates a pipeline.

Environment: GITLAB_ADMIN_USER, GITLAB_ADMIN_PASSWORD, GITLAB_CA_FILE,
optional GITLAB_API_URL (default https://gitlab.local/api/v4).

Adapted from var/demos/fullsend-entrypoint-poc/strategy-ci/publish.py.
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import httpx

FIXTURE = Path(__file__).resolve().parent
PROJECT = 'redhat/rhel-ai/agentic-ci/strat-pipeline'
BRANCH = 'feat/fullsend-agent-led-poc'
PROTECTED_BRANCHES = ('main', 'feat/fullsend-strategy-poc')
FILES = {
    '.gitlab-ci.yml': 'ci/gitlab-ci.yml',
    'ci-scripts/agent-led-source.sh': 'ci/source.sh',
    'ci-scripts/agent-led-strategy.sh': 'ci/strategy.sh',
    'ci-scripts/agent-led-gateway.sh': 'ci/gateway.sh',
    'ci-scripts/agent-led-redact.py': 'ci/redact.py',
}
REQUIRED_VARIABLES = ('JIRA_SERVER', 'JIRA_USER', 'JIRA_TOKEN',
                      'VERTEX_CREDENTIALS_JSON', 'ANTHROPIC_VERTEX_PROJECT_ID')
PUBLISH_VARIABLES = ('RESULTS_PUSH_TOKEN', 'ORG_PULSE_API_TOKEN')
RFE_RE = re.compile(r'^RHAIRFE-\d+$')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--publish', action='store_true',
                        help='Create the branch if needed and commit the CI files')
    run = parser.add_mutually_exclusive_group()
    run.add_argument('--rfe', help='Create a strat-single pipeline for this RFE')
    run.add_argument('--batch', action='store_true',
                     help='Create a strat-batch pipeline (native discovery)')
    run.add_argument('--schedule-once', action='store_true',
                     help='Start strat-batch from a one-shot pipeline schedule, '
                          'then delete the schedule (no recurring schedule remains)')
    parser.add_argument('--context-path',
                        help='Failure-path testing: set STRAT_ARCHITECTURE_CONTEXT_PATH')
    parser.add_argument('--batch-size', type=int)
    parser.add_argument('--batch-offset', type=int)
    parser.add_argument('--expected-keys', help='Exact space-separated discovery bound')
    parser.add_argument('--allow-invalid-rfe', action='store_true',
                        help='Failure-path testing: skip the local --rfe format check')
    args = parser.parse_args()
    if args.rfe and not RFE_RE.match(args.rfe) and not args.allow_invalid_rfe:
        parser.error('--rfe must look like RHAIRFE-NNNN')
    limits = (args.batch_size, args.batch_offset, args.expected_keys)
    if not (args.batch or args.schedule_once) and any(v is not None for v in limits):
        parser.error('batch limits require --batch or --schedule-once')
    if any(v is not None and v < 0 for v in limits[:2]):
        parser.error('batch limits must be non-negative')

    base = os.environ.get('GITLAB_API_URL', 'https://gitlab.local/api/v4')
    with httpx.Client(verify=os.environ['GITLAB_CA_FILE'], timeout=60) as client:
        response = client.post(
            base + '/admin/tokens',
            auth=(os.environ['GITLAB_ADMIN_USER'], os.environ['GITLAB_ADMIN_PASSWORD']),
            json={'login': 'admin', 'name': 'fullsend-agent-led-poc',
                  'scopes': ['api', 'read_repository', 'write_repository']})
        response.raise_for_status()
        headers = {'PRIVATE-TOKEN': response.json()['token']}

        def api(method, path, **kwargs):
            response = client.request(method, base + path, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None

        project = api('GET', '/projects/' + quote(PROJECT, safe=''))
        pid = project['id']
        branches = {b['name']: b['commit']['id'] for b in
                    api('GET', f'/projects/{pid}/repository/branches',
                        params={'per_page': 100})}
        report = {'project': PROJECT, 'project_id': pid, 'branch': BRANCH,
                  'protected_branch_heads': {b: branches.get(b) for b in PROTECTED_BRANCHES}}

        names = {v['key'] for v in api('GET', f'/projects/{pid}/variables',
                                       params={'per_page': 100})}
        missing = [k for k in REQUIRED_VARIABLES if k not in names]
        report['variables_present'] = sorted(n for n in names if n in
                                             REQUIRED_VARIABLES + PUBLISH_VARIABLES)
        if missing:
            report['variables_missing'] = missing
            print(json.dumps(report, indent=2))
            sys.exit(f'missing required shared project variables: {missing}')

        if args.publish:
            if BRANCH not in branches:
                created = api('POST', f'/projects/{pid}/repository/branches',
                              json={'branch': BRANCH, 'ref': 'main'})
                report['branch_created_from_main'] = created['commit']['id']
            else:
                report['branch_existing_head'] = branches[BRANCH]
            actions = []
            for remote, local in FILES.items():
                response = client.get(
                    base + f'/projects/{pid}/repository/files/' + quote(remote, safe=''),
                    headers=headers, params={'ref': BRANCH})
                if response.status_code != 404:
                    response.raise_for_status()
                actions.append({'action': 'create' if response.status_code == 404 else 'update',
                                'file_path': remote,
                                'content': (FIXTURE / local).read_text()})
            commit = api('POST', f'/projects/{pid}/repository/commits', json={
                'branch': BRANCH, 'actions': actions,
                'commit_message': 'Agent-led Fullsend strategy CI [skip ci]'})
            report['commit'] = commit['id']
            after = {b['name']: b['commit']['id'] for b in
                     api('GET', f'/projects/{pid}/repository/branches',
                         params={'per_page': 100})}
            changed = [b for b in PROTECTED_BRANCHES if after.get(b) != branches.get(b)]
            if changed:
                sys.exit(f'protected branches moved unexpectedly: {changed}')

        if args.schedule_once:
            report.update(schedule_once(api, pid, args))

        if args.rfe or args.batch:
            if args.rfe:
                variables = [{'key': 'STRATEGY_MODE', 'value': 'strat-single'},
                             {'key': 'RFE_KEY', 'value': args.rfe}]
            else:
                variables = [{'key': 'STRATEGY_MODE', 'value': 'strat-batch'}]
                for key, value in (('BATCH_SIZE', args.batch_size),
                                   ('BATCH_OFFSET', args.batch_offset),
                                   ('BATCH_EXPECTED_KEYS', args.expected_keys)):
                    if value is not None:
                        variables.append({'key': key, 'value': str(value)})
            if args.context_path is not None:
                variables.append({'key': 'STRAT_ARCHITECTURE_CONTEXT_PATH',
                                  'value': args.context_path})
            pipeline = api('POST', f'/projects/{pid}/pipeline',
                           json={'ref': BRANCH, 'variables': variables})
            report['pipeline_id'] = pipeline['id']
            report['pipeline_url'] = pipeline.get('web_url')
            report['pipeline_variables'] = variables
        print(json.dumps(report, indent=2))


def schedule_once(api, pid, args):
    """Create a schedule for one minute a few minutes ahead (it would next
    recur a year later), wait for its pipeline, then delete it."""
    fire = (datetime.now(timezone.utc) + timedelta(minutes=3)).replace(second=0, microsecond=0)
    cron = f'{fire.minute} {fire.hour} {fire.day} {fire.month} *'
    schedule = api('POST', f'/projects/{pid}/pipeline_schedules', json={
        'description': 'agent-led POC one-shot strat-batch (deleted after firing)',
        'ref': BRANCH, 'cron': cron, 'cron_timezone': 'UTC', 'active': True})
    sid = schedule['id']
    report = {'schedule_id': sid, 'schedule_cron': cron, 'schedule_variables': []}
    try:
        for key, value in (('BATCH_SIZE', args.batch_size),
                           ('BATCH_OFFSET', args.batch_offset),
                           ('BATCH_EXPECTED_KEYS', args.expected_keys)):
            if value is not None:
                api('POST', f'/projects/{pid}/pipeline_schedules/{sid}/variables',
                    json={'key': key, 'value': str(value)})
                report['schedule_variables'].append({'key': key, 'value': str(value)})
        deadline = time.time() + 600
        while time.time() < deadline:
            current = api('GET', f'/projects/{pid}/pipeline_schedules/{sid}')
            last = current.get('last_pipeline') or {}
            if last.get('id'):
                report['pipeline_id'] = last['id']
                break
            time.sleep(15)
        else:
            report['pipeline_id'] = None
    finally:
        api('DELETE', f'/projects/{pid}/pipeline_schedules/{sid}')
        remaining = api('GET', f'/projects/{pid}/pipeline_schedules')
        report['schedules_remaining'] = len(remaining)
    if report.get('pipeline_id'):
        pipeline = api('GET', f'/projects/{pid}/pipelines/{report["pipeline_id"]}')
        report['pipeline_source'] = pipeline.get('source')
    return report


if __name__ == '__main__':
    main()
