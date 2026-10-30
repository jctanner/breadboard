#!/usr/bin/env python3
"""Copy the green agent-led GitLab branch and publish the Workflow CI adapter.

Default is inspection only. --publish never launches a model or a pipeline.
--preflight starts only the model-free sandbox diagnostic job.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote

import httpx

HERE = Path(__file__).resolve().parent
PROJECT = 'redhat/rhel-ai/agentic-ci/strat-pipeline'
BRANCH = 'feat/fullsend-claude-workflow'
BASE = 'feat/fullsend-agent-led-poc'
BASE_SHA = '89c879b69366cb2a9b21068f0781c7277b8f04e8'
FILES = {'.gitlab-ci.yml': HERE / 'ci/gitlab-ci.yml'}
FILES.update({f'ci-scripts/workflow-{p.name}': p for p in sorted((HERE / 'ci').iterdir())
              if p.is_file() and p.name != 'gitlab-ci.yml'})


def client():
    return httpx.Client(base_url=os.environ.get('GITLAB_API_URL', 'https://gitlab.local/api/v4'),
                        auth=(os.environ.get('GITLAB_ADMIN_USER', 'admin'),
                              os.environ.get('GITLAB_ADMIN_PASSWORD', 'admin')),
                        verify=os.environ['GITLAB_CA_FILE'], timeout=120)


def api(c, method, path, **kw):
    r = c.request(method, path, **kw)
    # Never include response bodies or request headers in credential errors.
    if not r.is_success:
        raise RuntimeError(f'{method} {path}: HTTP {r.status_code}')
    return r.json() if r.content else None


def publish(c, do_publish=False, preflight=False):
    pid = api(c, 'GET', '/projects/' + quote(PROJECT, safe=''))['id']
    root = f'/projects/{pid}'
    heads = {b['name']: b['commit']['id'] for b in api(c, 'GET', root + '/repository/branches', params={'per_page': 100})}
    if heads.get(BASE) != BASE_SHA:
        raise RuntimeError('Base branch changed; inspect before copying')
    baseline = {n: sha for n, sha in heads.items() if n != BRANCH}
    report = {'project_id': pid, 'branch': BRANCH, 'base_sha': BASE_SHA, 'baseline_heads': baseline}
    names = {v['key'] for v in api(c, 'GET', root + '/variables', params={'per_page': 100})}
    required = {'JIRA_SERVER', 'JIRA_USER', 'JIRA_TOKEN', 'MODEL_RELAY_API_KEY', 'RESULTS_PUSH_TOKEN', 'ORG_PULSE_API_TOKEN'}
    report['missing_variables'] = sorted(required - names)
    if do_publish:
        if report['missing_variables']:
            raise RuntimeError('Missing CI variable names: ' + ', '.join(report['missing_variables']))
        if BRANCH not in heads:
            api(c, 'POST', root + '/repository/branches', json={'branch': BRANCH, 'ref': BASE_SHA})
        actions = []
        manifest = {}
        for path, local in FILES.items():
            content = local.read_text()
            existing = c.get(root + '/repository/files/' + quote(path, safe=''), params={'ref': BRANCH})
            if existing.status_code not in (200, 404):
                raise RuntimeError('Cannot inspect destination file')
            manifest[path] = hashlib.sha256(local.read_bytes()).hexdigest()
            if existing.status_code == 200:
                import base64
                if base64.b64decode(existing.json()['content']).decode() == content:
                    continue
            actions.append({'action': 'update' if existing.status_code == 200 else 'create',
                            'file_path': path, 'content': content})
        if actions:
            body = {'branch': BRANCH, 'commit_message': 'Use hardened Claude Workflow through model-relay [skip ci]',
                    'actions': actions}
            if BRANCH in heads:
                body['last_commit_id'] = heads[BRANCH]
            commit = api(c, 'POST', root + '/repository/commits', json=body)
            report['commit'] = commit['id']
        else:
            report['commit'] = heads[BRANCH]
        report['file_sha256'] = manifest
    if preflight:
        if report['missing_variables']:
            raise RuntimeError('Provision required variables before preflight')
        run = api(c, 'POST', root + '/pipeline', json={
            'ref': BRANCH, 'variables': [{'key': 'STRATEGY_MODE', 'value': 'preflight'}]})
        report['preflight_pipeline'] = {k: run.get(k) for k in ('id', 'status', 'sha', 'web_url')}
    after = {b['name']: b['commit']['id'] for b in api(c, 'GET', root + '/repository/branches', params={'per_page': 100})}
    if any(after.get(n) != sha for n, sha in baseline.items()):
        raise RuntimeError('A preserved baseline head changed')
    report['baselines_unchanged'] = True
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    with client() as c:
        report = publish(c, args.publish, args.preflight)
    text = json.dumps(report, indent=2) + '\n'
    if args.report:
        args.report.write_text(text)
    print(text)
