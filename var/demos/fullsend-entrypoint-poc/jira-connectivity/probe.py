import json
import os
import signal
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / 'scripts'))
import jira_utils

report = {'python': sys.executable, 'tls_required': jira_utils.ssl_ctx.verify_mode == ssl.CERT_REQUIRED, 'hostname_check': jira_utils.ssl_ctx.check_hostname}
def timeout_handler(*_):
    raise TimeoutError('bounded probe timeout')
signal.signal(signal.SIGALRM, timeout_handler)
def probe(name, function):
    started = time.monotonic()
    try:
        signal.alarm(12)
        result = function()
        report[name] = {'ok': True, 'result': result}
    except Exception as e:
        report[name] = {'ok': False, 'error': str(e), 'type': type(e).__name__}
    finally:
        signal.alarm(0)
        report[name]['seconds'] = round(time.monotonic() - started, 2)
    print(json.dumps({name: report[name]}), flush=True)

report['resolv_conf'] = Path('/etc/resolv.conf').read_text()
report['hosts_local_entries'] = [line for line in Path('/etc/hosts').read_text().splitlines() if '.local' in line]
report['ssl_cert_file'] = os.environ.get('SSL_CERT_FILE')
report['proxy'] = {key: {'scheme': urllib.parse.urlparse(value).scheme, 'host': urllib.parse.urlparse(value).hostname, 'port': urllib.parse.urlparse(value).port} for key, value in urllib.request.getproxies().items() if key != 'no'}
probe('dns', lambda: sorted({entry[4][0] for entry in socket.getaddrinfo('jira.local', 443, type=socket.SOCK_STREAM)}))
probe('getent', lambda: {'exit': (p := subprocess.run(['getent', 'hosts', 'jira.local'], timeout=8, capture_output=True, text=True)).returncode, 'stdout': p.stdout, 'stderr': p.stderr})
server = os.environ['JIRA_SERVER']
user = os.environ['JIRA_USER']
token = os.environ['JIRA_TOKEN']
def server_info():
    data = jira_utils.api_call(server, '/serverInfo', user, token)
    assert data.get('baseUrl') == 'https://jira-emulator.atlassian.net', 'unexpected Jira emulator base URL'
    assert data.get('serverTitle') == 'Jira Emulator', 'unexpected Jira server title'
    assert data.get('serverTitle') and data.get('version'), 'response is not Jira server information'
    return {key: data.get(key) for key in ('baseUrl', 'serverTitle', 'version', 'deploymentType')}
def identity():
    data = jira_utils.api_call(server, '/myself', user, token)
    identity = data.get('name') or data.get('accountId')
    assert identity == user, 'unexpected Jira identity'
    return {'identity_matches_ci_user': True, 'active': data.get('active')}
def reject_untrusted_ca():
    context = ssl.create_default_context(cafile='/etc/ssl/certs/ca-certificates.crt')
    try:
        urllib.request.urlopen(server + '/rest/api/3/serverInfo', timeout=8, context=context)
    except urllib.error.URLError as error:
        assert isinstance(error.reason, ssl.SSLCertVerificationError), 'unexpected wrong-CA failure'
        return {'untrusted_ca_rejected': True}
    raise AssertionError('Jira HTTPS accepted without local CA')
probe('jira_untrusted_ca', reject_untrusted_ca)
probe('jira_server_info', server_info)
probe('jira_authenticated_identity', identity)
def invalid_identity():
    try:
        jira_utils.api_call(server, '/myself', user, 'invalid-m42-token')
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403), f'unexpected invalid credential status {e.code}'
        return {'status': e.code, 'invalid_credentials_rejected': True}
    assert os.environ.get('M42_EXPECTED_JIRA_AUTH_MODE') == 'permissive', 'Jira unexpectedly accepted invalid credentials'
    return {'status': 200, 'invalid_credentials_rejected': False, 'authentication_enforced': False, 'limitation': 'deployed emulator permissive mode accepts Basic identity without password validation'}
probe('jira_invalid_identity', invalid_identity)
def public():
    with urllib.request.urlopen('https://api.github.com/zen', timeout=8, context=jira_utils.ssl_ctx) as response:
        return {'status': response.status, 'bytes': len(response.read())}
def blocked():
    try:
        with urllib.request.urlopen('https://example.com/', timeout=8, context=jira_utils.ssl_ctx) as response:
            raise AssertionError('blocked endpoint unexpectedly allowed')
    except urllib.error.HTTPError as e:
        assert e.code == 403, f'unexpected deny status {e.code}'
        return {'status': e.code, 'blocked': True}
    except urllib.error.URLError as e:
        assert '403 Forbidden' in str(e), 'unexpected network error for blocked endpoint'
        return {'status': 403, 'blocked': True, 'stage': 'proxy_CONNECT'}
probe('allowed_public', public)
probe('blocked_endpoint', blocked)
# Preserve only non-secret upstream failure messages from structured supervisor logs.
report['supervisor_failures'] = []
for log in Path('/var/log').glob('openshell-ocsf*'):
    try:
        for line in log.read_text().splitlines():
            event = json.loads(line)
            if 'jira.local' in line and any(term in line.lower() for term in ('relay error', 'certificate', 'failed', 'rejected')):
                report['supervisor_failures'].append(event.get('message', event.get('status_detail', 'structured failure without message')))
    except (OSError, ValueError):
        pass
output = Path(os.environ['FULLSEND_OUTPUT_DIR'])
output.mkdir(parents=True, exist_ok=True)
(output / 'jira-connectivity.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2), flush=True)
assert report['tls_required'] and report['hostname_check']
assert all(report[key]['ok'] for key in ('jira_server_info', 'jira_authenticated_identity', 'jira_invalid_identity', 'jira_untrusted_ca', 'allowed_public', 'blocked_endpoint')), 'M4.2 connectivity checks did not all pass'
print('M42_SANDBOX_JIRA_PASS', flush=True)
