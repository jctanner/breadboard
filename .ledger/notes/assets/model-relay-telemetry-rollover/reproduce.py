"""Reproduce page-limited telemetry using the real relay's local mock backend.

Build first: cargo build --offline --manifest-path checkouts/model-relay/Cargo.toml
Run from Breadboard: python3 .ledger/notes/assets/model-relay-telemetry-rollover/reproduce.py

Requires Node.js and the compiled relay. All relay state and fixture credentials
are temporary; no host credentials or deployed data are used. No model process
is launched. Mock requests return fixed responses rather than invoking inference.
"""

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[4]
    parser.add_argument('--relay', type=Path, default=root / 'checkouts/model-relay')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    relay = args.relay.resolve()
    report = {
        'relay_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=relay, text=True).strip(),
        'console_sha256': hashlib.sha256((relay / 'src/admin_ui/admin.js').read_bytes()).hexdigest(),
        'console_probe': 'Real admin.js in Node VM with a minimal DOM and empty filters; real localhost API reads',
        'backend': 'mock', 'provider_calls': 0, 'paid_tokens': 0,
        'observations': [],
    }
    with tempfile.TemporaryDirectory(prefix='model-relay-telemetry-rollover-') as raw:
        directory = Path(raw)
        client_key, admin_key = secrets.token_hex(24), secrets.token_hex(24)
        for name, value in {
            'keys.json': json.dumps({'keys': [{
                'client_id': 'telemetry-repro', 'key_id': 'telemetry-repro',
                'sha256': hashlib.sha256(client_key.encode()).hexdigest(),
                'models': ['telemetry-repro'], 'backends': ['mock'],
            }]}),
            'models.json': json.dumps({'telemetry-repro': {'window_tokens': 200000}}),
            'admin-key': admin_key,
        }.items():
            path = directory / name
            path.write_text(value)
            path.chmod(0o600)
        inference = f'http://127.0.0.1:{free_port()}'
        admin = f'http://127.0.0.1:{free_port()}'
        assert inference != admin
        database = directory / 'telemetry.sqlite'
        # Pass an explicit environment instead of inheriting provider settings.
        environment = {
            'PATH': os.environ['PATH'], 'SHIM_BACKEND': 'mock',
            'SHIM_LISTEN': inference.removeprefix('http://'),
            'SHIM_ADMIN_LISTEN': admin.removeprefix('http://'),
            'SHIM_KEYS_FILE': str(directory / 'keys.json'),
            'SHIM_MODELS_FILE': str(directory / 'models.json'),
            'SHIM_ADMIN_KEY_FILE': str(directory / 'admin-key'),
            'SHIM_DB': str(database), 'SHIM_CLAUDE_BIN': '/bin/false',
        }

        def request(base, path, body=None, credential=None):
            headers = {}
            if credential:
                headers['Authorization'] = f'Bearer {credential}'
            if body is not None:
                headers['Content-Type'] = 'application/json'
                headers['anthropic-version'] = '2023-06-01'
                headers['x-shim-run-id'] = 'local-telemetry-rollover'
            payload = None if body is None else json.dumps(body).encode()
            with urlopen(Request(base + path, data=payload, headers=headers), timeout=10) as response:
                return json.load(response)

        def start():
            log = (directory / 'relay.log').open('ab')
            process = subprocess.Popen([str(relay / 'target/debug/vertex-shim')], cwd=directory,
                                       env=environment, stdout=log, stderr=log)
            log.close()
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Isolated relay failed to start; see configuration/startup checks.')
                try:
                    status = request(inference, '/health')
                    assert status['backend'] == 'mock' and status['synthetic'] is True
                    return process
                except OSError:
                    time.sleep(0.05)
            process.terminate()
            process.wait(timeout=5)
            raise RuntimeError('Isolated relay readiness timed out.')

        def stop(process):
            process.terminate()
            process.wait(timeout=5)

        def settled(expected):
            for _ in range(100):
                health = request(admin, '/api/private/v1/health', credential=admin_key)
                if health['pending_writes'] == 0:
                    with sqlite3.connect(database) as connection:
                        count = connection.execute('SELECT COUNT(*) FROM requests').fetchone()[0]
                    if count == expected:
                        assert health['dropped_requests'] == 0 and health['storage_errors'] == 0
                        return
                time.sleep(0.01)
            raise AssertionError('Fixture writes did not settle.')

        def generate(count, output):
            for _ in range(count):
                value = request(inference, '/v1/messages', {
                    'model': 'telemetry-repro', 'max_tokens': output,
                    'messages': [{'role': 'user', 'content': 'Local synthetic telemetry fixture.'}],
                }, client_key)
                assert value['usage']['output_tokens'] == output

        def storage():
            with sqlite3.connect(database) as connection:
                count, outputs, providers = connection.execute(
                    "SELECT COUNT(*), SUM(json_extract(payload,'$.usage.output_tokens')), "
                    "SUM(json_extract(payload,'$.synthetic')=0) FROM requests"
                ).fetchone()
            assert providers == 0
            return {'requests': count, 'output_tokens': outputs, 'provider_requests': providers}

        def probe(exercise_refresh=False):
            config = directory / 'console-probe.json'
            config.write_text(json.dumps({
                'base': admin, 'admin_key': admin_key,
                'source': str(relay / 'src/admin_ui/admin.js'),
                'exercise_refresh': exercise_refresh,
            }))
            config.chmod(0o600)
            return json.loads(subprocess.check_output(
                ['node', str(Path(__file__).with_name('console_probe.js')), str(config)], text=True
            ))

        process = start()
        try:
            # These fixed-response calls never contact any upstream provider.
            generate(100, 3)
            settled(100)
            report['observations'].append({'stored': storage(), 'console': probe()})
            generate(1, 1)
            settled(101)
            report['observations'].append({'stored': storage(), 'console': probe()})
            generate(49, 1)
            settled(150)
            # Accelerate the fixture's history to span five hours without waiting.
            now = datetime.now(timezone.utc)
            with sqlite3.connect(database) as connection:
                rows = connection.execute('SELECT sequence,payload FROM requests ORDER BY sequence').fetchall()
                for index, (sequence, payload) in enumerate(rows):
                    value = json.loads(payload)
                    started = now - timedelta(minutes=2 * (149 - index))
                    value['started_at'] = started.isoformat()
                    value['finished_at'] = (started + timedelta(seconds=1)).isoformat()
                    connection.execute('UPDATE requests SET payload=? WHERE sequence=?',
                                       (json.dumps(value), sequence))
            report['fixture_span_minutes'] = 298
            report['observations'].append({'stored': storage(), 'console': probe(True)})
            first = request(admin, '/api/private/v1/telemetry/summary?limit=100&order=desc', credential=admin_key)
            report['summary_api'] = {
                'output_tokens': first['generation_tokens']['output_tokens'],
                'has_next_cursor': first['next_cursor'] is not None, 'scope': first['scope'],
            }
            all_items = []
            cursor = None
            while True:
                path = '/api/private/v1/telemetry/requests?limit=100&order=desc'
                if cursor is not None:
                    path += f'&cursor={cursor}'
                page = request(admin, path, credential=admin_key)
                all_items.extend(page['items'])
                cursor = page['next_cursor']
                if cursor is None:
                    break
            assert len(all_items) == 150 and len({item['request_id'] for item in all_items}) == 150
            assert sum(item['usage']['output_tokens'] for item in all_items) == 350
            assert all(item['synthetic'] is True for item in all_items)
            report['paginated_api'] = {'requests': len(all_items), 'output_tokens': 350}
            report['storage_health'] = request(admin, '/api/private/v1/health', credential=admin_key)
        finally:
            stop(process)
        process = start()
        try:
            report['after_restart'] = storage()
            assert report['after_restart']['requests'] == 150
            assert report['after_restart']['output_tokens'] == 350
        finally:
            stop(process)
        observations = report['observations']
        assert observations[0]['console'][0]['output_tokens'] == 300
        assert observations[1]['console'][0]['output_tokens'] == 298
        assert observations[2]['console'][0]['output_tokens'] == 200
        assert observations[2]['console'][1]['output_tokens'] == 350
        assert observations[2]['console'][2]['output_tokens'] == 200
        report['reproduced'] = True
    content = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(content)
    print(content, end='')


if __name__ == '__main__':
    main()
