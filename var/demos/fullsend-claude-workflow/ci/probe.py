#!/usr/bin/env python3
"""Prove credential substitution and blocked egress using GET requests only."""
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


def get(url, headers=None):
    with urlopen(Request(url, headers=headers or {}), timeout=20) as response:
        return json.load(response)


def main():
    jira, user, model = sys.argv[1:]
    # Give the trusted external observer time to attach to this diagnostic.
    time.sleep(2)
    for name in ('ANTHROPIC_API_KEY', 'JIRA_TOKEN'):
        if not os.environ.get(name, '').startswith('openshell:resolve:env:'):
            raise RuntimeError(f'{name} must be an OpenShell placeholder')
    for key in ('GOOGLE_APPLICATION_CREDENTIALS', 'VERTEX_CREDENTIALS_JSON', 'MODEL_RELAY_API_KEY',
                'RESULTS_PUSH_TOKEN', 'ORG_PULSE_API_TOKEN'):
        if os.environ.get(key):
            raise RuntimeError(f'host-only credential leaked: {key}')
    version = subprocess.run(['python3', '/sandbox/workspace/check_claude_runtime.py'], check=True,
                             capture_output=True, text=True)
    subprocess.run(['python3', '-c', 'import jsonschema, yaml, certifi, diff_match_patch'], check=True)
    models = get('https://relay-api.local/v1/models',
                 {'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'})
    assert model in [m['id'] for m in models['data']], 'requested model absent from authorized catalog'
    auth = base64.b64encode(f'{user}:{os.environ["JIRA_TOKEN"]}'.encode()).decode()
    get(jira + '/rest/api/2/myself', {'Authorization': 'Basic ' + auth})
    # Model hosts and the relay admin listener must not be reachable.
    blocked = []
    for url in ('https://api.anthropic.com/v1/models', 'https://aiplatform.googleapis.com/',
                'https://relay.local/api/private/v1/projects'):
        try:
            get(url)
        except URLError as exc:
            # An upstream HTTP 401/403 would demonstrate reachable egress.
            if getattr(exc, 'code', None) is not None:
                raise RuntimeError('denied host returned an HTTP response') from None
            blocked.append(url)
        else:
            raise RuntimeError('denied host was reachable')
    trace_files = [p for p in Path('/sandbox/workspace/evidence/strace').glob('trace-*') if p.stat().st_size]
    if not trace_files:
        raise RuntimeError('external observer produced no syscall traces')
    print(json.dumps({'result': 'PASS', 'inference_requests': 0, 'jira_mutations': 0,
                      'runtime': json.loads(version.stdout),
                      'syscall_trace_files': len(trace_files),
                      'provider_placeholders': True, 'relay_model': model,
                      'jira_identity_get': True,
                      'jira_password_validation': 'Local emulator does not enforce passwords',
                      'blocked_hosts': blocked}))


if __name__ == '__main__':
    main()
