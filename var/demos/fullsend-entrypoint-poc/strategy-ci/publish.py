#!/usr/bin/env python3
"""Publish the Fullsend CI branch while retaining native main (no pipeline run)."""
import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import httpx

FIXTURE = Path(__file__).resolve().parent
PROJECT = 'redhat/rhel-ai/agentic-ci/strat-pipeline'
BRANCH = 'feat/fullsend-strategy-poc'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enable-runner', action='store_true', help='Deploy the authoritative maintained runner with Podman/OpenShell capabilities')
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--rfe', help='Create a pipeline with this RFE; single-rfe remains manual')
    scope.add_argument('--batch-discover', action='store_true', help='Create a manually gated discovery batch')
    parser.add_argument('--batch-size', type=int)
    parser.add_argument('--batch-offset', type=int)
    parser.add_argument('--expected-keys', help='Exact space-separated discovery safety bound')
    args = parser.parse_args()
    if not args.batch_discover and any(v is not None for v in (args.batch_size,args.batch_offset,args.expected_keys)):
        parser.error('batch limits require --batch-discover')
    if any(v is not None and v < 0 for v in (args.batch_size,args.batch_offset)):
        parser.error('batch limits must be nonnegative')
    ca = os.environ['GITLAB_CA_FILE']
    base = os.environ.get('GITLAB_API_URL', 'https://gitlab.local/api/v4')
    with httpx.Client(verify=ca, timeout=30) as client:
        response = client.post(base+'/admin/tokens', auth=(os.environ['GITLAB_ADMIN_USER'], os.environ['GITLAB_ADMIN_PASSWORD']), json={'login':'admin','name':'fullsend-m6-bootstrap','scopes':['api','read_repository','write_repository']})
        response.raise_for_status()
        headers = {'PRIVATE-TOKEN':response.json()['token']}
        def api(method, path, **kwargs):
            response = client.request(method, base+path, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        project = api('GET', '/projects/'+quote(PROJECT, safe=''))
        pid = project['id']
        native = api('GET', f'/projects/{pid}/repository/branches/main')['commit']['id']
        branches = api('GET', f'/projects/{pid}/repository/branches', params={'per_page':100})
        if BRANCH not in {b['name'] for b in branches}:
            api('POST', f'/projects/{pid}/repository/branches', json={'branch':BRANCH,'ref':'main'})
        secret = json.loads(subprocess.check_output(['kubectl','-n','ai-pipeline','get','secret','fullsend-strategy-jira','-o','json']))
        variables = {key:base64.b64decode(value).decode() for key,value in secret['data'].items() if key in {'JIRA_SERVER','JIRA_USER','JIRA_TOKEN'}}
        gcp = json.loads(subprocess.check_output(['kubectl','-n','ai-pipeline','get','secret','gcp-credentials','-o','json']))
        variables['VERTEX_CREDENTIALS_JSON'] = base64.b64decode(gcp['data']['credentials.json']).decode()
        settings = json.loads(subprocess.check_output(['kubectl','-n','ai-pipeline','get','secret','pipeline-secrets','-o','json']))
        for key in ('ANTHROPIC_VERTEX_PROJECT_ID','CLOUD_ML_REGION','CLAUDE_CODE_USE_VERTEX'):
            if key in settings['data']:
                variables[key]=base64.b64decode(settings['data'][key]).decode()
        # Preserve existing results/Org Pulse tokens.
        existing = api('GET', f'/projects/{pid}/variables', params={'per_page':100})
        keys = {v['key'] for v in existing}
        values = {v['key']:v['value'] for v in existing}
        for target, source in {'RESULTS_PUSH_TOKEN':'RHAISTRAT_GITLAB_TOKEN','FULLSEND_GITLAB_ANALYST_TOKEN':'RHAISTRAT_GITLAB_TOKEN','ORG_PULSE_API_TOKEN':'RHAISTRAT_ORG_PULSE_TOKEN'}.items():
            if target not in keys and source in values:
                variables[target]=values[source]
        for key,value in variables.items():
            suffix = '/'+quote(key,safe='') if key in keys else ''
            api('PUT' if key in keys else 'POST',f'/projects/{pid}/variables'+suffix,json={'key':key,'value':value,'masked':key not in {'JIRA_SERVER','JIRA_USER','ANTHROPIC_VERTEX_PROJECT_ID','CLOUD_ML_REGION','CLAUDE_CODE_USE_VERTEX'},'protected':False})
        files = {'.gitlab-ci.yml':'gitlab-ci.yml','ci-scripts/fullsend-source.sh':'source.sh','ci-scripts/fullsend-strategy.sh':'strategy.sh','ci-scripts/fullsend-redact.py':'redact-artifacts.py'}
        actions=[]
        for remote,local in files.items():
            response=client.get(base+f'/projects/{pid}/repository/files/'+quote(remote,safe=''),headers=headers,params={'ref':BRANCH})
            if response.status_code != 404: response.raise_for_status()
            actions.append({'action':'create' if response.status_code==404 else 'update','file_path':remote,'content':(FIXTURE/local).read_text()})
        # Remove obsolete diagnostic sources from the normal branch.
        for remote in ('ci-scripts/fullsend-connectivity.sh','ci-scripts/fullsend-connectivity.py','ci-scripts/fullsend-model-smoke.sh'):
            response=client.get(base+f'/projects/{pid}/repository/files/'+quote(remote,safe=''),headers=headers,params={'ref':BRANCH})
            if response.is_success: actions.append({'action':'delete','file_path':remote})
            elif response.status_code != 404: response.raise_for_status()
        commit=api('POST',f'/projects/{pid}/repository/commits',json={'branch':BRANCH,'commit_message':'Add Fullsend strategy batch-discover CI [skip ci]','actions':actions})
        runners=api('GET','/runners')
        if args.enable_runner:
            env = dict(os.environ, PROJECT_ROOT=str(FIXTURE.parents[3]))
            subprocess.run(['bash', str(FIXTURE.parents[3]/'deploy/scripts/15-deploy-gitlab-runner.sh')],
                           env=env, check=True, stdout=sys.stderr)
            runners=api('GET','/runners')
        report={'project':PROJECT,'project_id':pid,'branch':BRANCH,'commit':commit['id'],'native_main':native,'runner_count':len(runners),'runner_enabled':args.enable_runner,'variable_keys':sorted(keys|set(variables))}
        if args.rfe or args.batch_discover:
            payload={'ref':BRANCH,'variables':[]}
            mode='single-rfe' if args.rfe else 'batch-discover'
            payload['variables'].append({'key':'STRATEGY_MODE','value':mode})
            if args.rfe: payload['variables'].append({'key':'RFE_KEY','value':args.rfe})
            for key,value in [('BATCH_SIZE',args.batch_size),('BATCH_OFFSET',args.batch_offset),('BATCH_EXPECTED_KEYS',args.expected_keys)]:
                if value is not None: payload['variables'].append({'key':key,'value':str(value)})
            pipeline=api('POST',f'/projects/{pid}/pipeline',json=payload)
            report['pipeline_id']=pipeline['id']
        print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
