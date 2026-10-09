#!/usr/bin/env python3
"""Redact exact job credential values from retained artifacts without logging them."""
import base64
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote


def values():
    secrets=set()
    for key,value in os.environ.items():
        if not any(word in key.upper() for word in ('TOKEN','PASSWORD','SECRET','CREDENTIAL','ADC')):
            continue
        if key.endswith(('_FILE','_PATH','_URL')) or len(value)<8:
            continue
        secrets.add(value)
        try:
            try: credential=json.loads(value)
            except ValueError: credential=json.loads(base64.b64decode(value))
            if isinstance(credential,dict):
                for name in ('refresh_token','client_secret','private_key'):
                    if credential.get(name):secrets.add(credential[name])
        except (ValueError,UnicodeError):pass
    credential_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if credential_path:
        # strategy.sh removes the raw credential environment variable before
        # launch. Retain masking for the private credential file's fields.
        credential = json.loads(Path(credential_path).read_text())
        for name in ('refresh_token', 'client_secret', 'private_key'):
            if credential.get(name): secrets.add(credential[name])
    for user_key,password_key in (('JIRA_USER','JIRA_TOKEN'),('RESULTS_GIT_USER','RESULTS_PUSH_TOKEN')):
        if os.environ.get(password_key):
            secrets.add(base64.b64encode((os.environ.get(user_key,'oauth2')+':'+os.environ[password_key]).encode()).decode())
    return sorted({variant.encode() for secret in secrets for variant in (secret,quote(secret,safe=''),json.dumps(secret)[1:-1])},key=len,reverse=True)


def stream():
    """Mask live output before it reaches the runner, preserving complete lines."""
    needles = values()
    for data in sys.stdin.buffer:
        for needle in needles:
            data = data.replace(needle, b'[REDACTED]')
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()


def main():
    root=Path(os.environ['CI_PROJECT_DIR'])
    needles=values()
    changed=0
    for folder in ('fullsend-ci-artifacts','fullsend-run-output'):
        directory=root/folder
        if not directory.exists():continue
        for path in directory.rglob('*'):
            if path.is_symlink():raise RuntimeError('Refusing artifact symlink')
            if not path.is_file():continue
            data=path.read_bytes();clean=data
            for needle in needles:clean=clean.replace(needle,b'[REDACTED]')
            if clean!=data:path.write_bytes(clean);changed+=1
    print(json.dumps({'artifact_redaction_complete':True,'files_changed':changed}))


if __name__=='__main__':
    if sys.argv[1:] == ['--stream']: stream()
    else: main()
