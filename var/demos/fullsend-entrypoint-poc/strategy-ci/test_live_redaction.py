import base64
import json
import os
from pathlib import Path
import subprocess

SCRIPT = Path(__file__).with_name('redact-artifacts.py')


def test_stream_masks_credentials_without_trimming():
    credential = {'type': 'authorized_user', 'refresh_token': 'refresh-test-sensitive',
                  'client_secret': 'client-test-sensitive'}
    env = {**os.environ, 'VERTEX_CREDENTIALS_JSON': json.dumps(credential),
           'JIRA_USER': 'bot', 'JIRA_TOKEN': 'jira-test-sensitive'}
    basic = base64.b64encode(b'bot:jira-test-sensitive').decode()
    line = 'x' * 100000
    text = '\n'.join([line, credential['refresh_token'], credential['client_secret'], basic, 'last'])
    result = subprocess.run(['python3', str(SCRIPT), '--stream'], input=text,
                            text=True, capture_output=True, env=env, check=True)
    assert result.stdout == line + '\n[REDACTED]\n[REDACTED]\n[REDACTED]\nlast'


def test_stream_masks_private_credential_file(tmp_path):
    credential = tmp_path / 'credential.json'
    credential.write_text(json.dumps({'refresh_token': 'private-refresh-test',
                                     'client_secret': 'private-client-test'}))
    env = dict(os.environ)
    env.pop('VERTEX_CREDENTIALS_JSON', None)
    env['GOOGLE_APPLICATION_CREDENTIALS'] = str(credential)
    result = subprocess.run(['python3', str(SCRIPT), '--stream'],
        input='private-refresh-test private-client-test', text=True,
        capture_output=True, env=env, check=True)
    assert result.stdout == '[REDACTED] [REDACTED]'
