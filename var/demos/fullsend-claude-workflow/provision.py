#!/usr/bin/env python3
"""Provision an Opus 4.6 relay client key as a masked GitLab variable.

Reads the relay admin key from its existing Kubernetes Secret in memory only.
Existing upstream and Jira/publication credentials are never modified.
"""
import base64
import json
import os
import subprocess
from urllib.parse import quote

import httpx

from publish import api, client, PROJECT

MODEL = 'claude-opus-4-6'
CLIENT = 'fullsend-claude-workflow'
GRANTS = {'client_id': CLIENT, 'models': [MODEL], 'backends': ['anthropic'],
          'catalog_models': False, 'vertex_catalog_models': False,
          'mock_adc': False, 'exchange_only': False}


def main():
    secret = json.loads(subprocess.check_output([
        'kubectl', '-n', 'ai-pipeline', 'get', 'secret', 'model-relay-admin', '-o', 'json']))
    admin = base64.b64decode(secret['data']['admin-api-key']).decode().strip()
    with client() as gitlab, httpx.Client(base_url='https://relay.local/api/private/v1',
            headers={'Authorization': 'Bearer ' + admin}, verify=os.environ['GITLAB_CA_FILE'], timeout=30) as relay:
        pid = api(gitlab, 'GET', '/projects/' + quote(PROJECT, safe=''))['id']
        variable = f'/projects/{pid}/variables/MODEL_RELAY_API_KEY'
        existing = gitlab.get(variable)
        if existing.status_code == 200:
            item = existing.json()
            if not item.get('masked') or not item.get('value'):
                raise RuntimeError('Existing relay variable is empty or unmasked')
            # Reconcile a possibly interrupted earlier GLM provisioning attempt
            # without replacing its secret. Touch only this integration's key.
            listing = api(relay, 'GET', '/projects/vertex-shim-local/credentials', params={'limit': 500})
            rows = listing.get('items', []) if isinstance(listing, dict) else listing
            matches = [r for r in rows if r.get('client_id') == CLIENT]
            if len(matches) != 1:
                raise RuntimeError('Cannot uniquely identify the existing integration credential')
            key = matches[0]
            if key.get('models') != [MODEL]:
                api(relay, 'PUT', '/projects/vertex-shim-local/credentials/' + key['key_id'], json=GRANTS)
            # Some hosts only register relay.local in /etc/hosts. Preserve
            # inference SNI/hostname verification while reusing that address.
            # Pass the credential on stdin, never in process arguments.
            catalog = json.loads(subprocess.check_output([
                'curl', '--silent', '--show-error', '--fail', '--max-time', '30',
                '--cacert', os.environ['GITLAB_CA_FILE'],
                '--connect-to', 'relay-api.local:443:relay.local:443',
                '--header', '@-', 'https://relay-api.local/v1/models'],
                input=('x-api-key: ' + item['value'] + '\n').encode()))
            if MODEL not in [m['id'] for m in catalog['data']]:
                raise RuntimeError('Existing CI credential cannot discover Opus 4.6')
            print(json.dumps({'relay_secret': 'existing masked CI variable retained',
                              'key_id': key['key_id'], 'models': [MODEL]}))
            return
        if existing.status_code != 404:
            raise RuntimeError('Cannot inspect existing relay variable')
        # The user selected Opus 4.6 for this exercise. No wildcard model grant.
        issued = api(relay, 'POST', '/projects/vertex-shim-local/credentials', json={
            **GRANTS, 'token_type': 'maas',
            'name': 'Fullsend Workflow GitLab', 'expiresIn': '90d',
        })
        try:
            api(gitlab, 'POST', f'/projects/{pid}/variables', json={
                'key': 'MODEL_RELAY_API_KEY', 'value': issued['api_key'], 'variable_type': 'env_var',
                'masked': True, 'protected': False, 'environment_scope': 'fullsend-claude-workflow'})
        except Exception:
            api(relay, 'DELETE', '/projects/vertex-shim-local/credentials/' + issued['key_id'])
            raise
        print(json.dumps({'relay_project': 'vertex-shim-local', 'key_id': issued['key_id'],
                          'models': [MODEL], 'gitlab_variable': 'MODEL_RELAY_API_KEY',
                          'masked': True, 'environment_scope': 'fullsend-claude-workflow'}))


if __name__ == '__main__':
    main()
