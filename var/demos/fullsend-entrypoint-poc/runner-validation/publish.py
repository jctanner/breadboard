#!/usr/bin/env python3
"""Publish read-only capability checks on the existing strategy CI project."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import quote

import httpx


def main():
    parser=argparse.ArgumentParser()
    scope=parser.add_mutually_exclusive_group()
    scope.add_argument('--untagged',action='store_true')
    scope.add_argument('--redaction-failure',action='store_true')
    scope.add_argument('--publish-only',action='store_true')
    scope.add_argument('--diagnostic',choices=('sandbox-connectivity','architecture-fetch','model-smoke','lifecycle-check','batch-controls'))
    parser.add_argument('--lifecycle',choices=('cancel','timeout','hard-kill'))
    parser.add_argument('--control-rfe')
    args=parser.parse_args()
    if args.control_rfe and args.diagnostic != 'batch-controls': parser.error('--control-rfe requires batch-controls')
    if args.diagnostic == 'batch-controls' and not args.control_rfe: parser.error('--control-rfe required')
    if args.lifecycle and args.diagnostic != 'lifecycle-check': parser.error('--lifecycle requires --diagnostic lifecycle-check')
    fixture=Path(__file__).resolve().parent
    branch='feat/fullsend-runner-validation'
    base=os.environ.get('GITLAB_API_URL','https://gitlab.local/api/v4')
    with httpx.Client(verify=os.environ['GITLAB_CA_FILE'],timeout=30,
                      headers={'PRIVATE-TOKEN':os.environ['GITLAB_API_TOKEN']}) as client:
        def api(method,path,**kwargs):
            r=client.request(method,base+path,**kwargs)
            if not r.is_success: raise RuntimeError(f'{method} {path}: HTTP {r.status_code}')
            return r.json()
        project=api('GET','/projects/'+quote('redhat/rhel-ai/agentic-ci/strat-pipeline',safe=''))
        prefix=f'/projects/{project["id"]}'
        native=api('GET',prefix+'/repository/branches/main')['commit']['id']
        r=client.get(base+prefix+'/repository/branches/'+quote(branch,safe=''))
        if r.status_code==404:
            api('POST',prefix+'/repository/branches',json={'branch':branch,'ref':'main'})
        elif not r.is_success: raise RuntimeError('Cannot inspect validation branch')
        files={'.gitlab-ci.yml':fixture/'gitlab-ci.yml','ci-scripts/m7-native.sh':fixture/'native.sh',
               'ci-scripts/m7-podman.sh':fixture.parent/'podman-smoke/smoke.sh'}
        for remote,local in {'source.sh':'fullsend-source.sh',
                             'connectivity.py':'fullsend-connectivity.py','redact-artifacts.py':'fullsend-redact.py'}.items():
            files['ci-scripts/'+local]=fixture.parent/'strategy-ci'/remote
        for local,remote in {'connectivity.sh':'fullsend-connectivity.sh','connectivity.py':'fullsend-connectivity.py','model-smoke.sh':'fullsend-model-smoke.sh','model-strategy.sh':'fullsend-model-strategy.sh','batch-controls.sh':'fullsend-batch-controls.sh','architecture-fetch.sh':'fullsend-architecture-fetch.sh','architecture-fetch.py':'fullsend-architecture-fetch.py'}.items():
            files['ci-scripts/'+remote]=fixture/local
        actions=[]
        for remote,local in files.items():
            r=client.get(base+prefix+'/repository/files/'+quote(remote,safe=''),params={'ref':branch})
            if r.status_code!=404 and not r.is_success: raise RuntimeError('Cannot inspect validation file')
            actions.append({'action':'create' if r.status_code==404 else 'update','file_path':remote,'content':local.read_text()})
        commit=api('POST',prefix+'/repository/commits',json={'branch':branch,'commit_message':'Validate maintained runner capabilities [skip ci]','actions':actions})
        assert api('GET',prefix+'/repository/branches/main')['commit']['id']==native
        variables=[{'key':'M7_UNTAGGED_PROBE','value':'1'}] if args.untagged else []
        if args.redaction_failure: variables=[{'key':'M7_REDACTION_FAILURE','value':'1'}]
        if args.diagnostic:
            variables=[{'key':'M8_DIAGNOSTIC','value':args.diagnostic}]
            if args.control_rfe: variables.append({'key':'M8_CONTROL_RFE','value':args.control_rfe})
            if args.lifecycle: variables.append({'key':'M6_LIFECYCLE','value':args.lifecycle})
        report={'project_id':project['id'],'branch':branch,'commit':commit['id'],
                'native_main':native,'untagged':args.untagged,'redaction_failure':args.redaction_failure}
        if not args.publish_only:
            report['pipeline_id']=api('POST',prefix+'/pipeline',json={'ref':branch,'variables':variables})['id']
        print(json.dumps(report))


if __name__=='__main__': main()
