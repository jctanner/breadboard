"""Model-free checks for the GitLab Fullsend Workflow integration."""
import base64
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import httpx
import pytest
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'checkouts.tmp/jctanner-fullsend-ai/strat-creator'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CONFIGURE = module('workflow_configure', HERE / 'ci/configure.py')
PUBLISH = module('workflow_publish', HERE / 'publish.py')


@pytest.fixture
def target(tmp_path):
    destination = tmp_path / 'target'
    shutil.copytree(SOURCE / '.fullsend', destination / '.fullsend',
                    ignore=shutil.ignore_patterns('.fullsend-cache', '__pycache__'))
    return destination


def configure(target):
    return CONFIGURE.configure(target, 'localhost/strat-workflow:123', CONFIGURE.DEFAULT_MODEL, 'high', 10)


def test_workflow_and_guard_code_are_preserved(target):
    before = {p.relative_to(target): p.read_bytes() for p in target.rglob('*') if p.is_file()}
    configure(target)
    for rel, data in before.items():
        if rel.suffix == '.md' or '/plugins/' in str(rel) or rel.suffix in ('.py', '.sh', '.js', '.json'):
            assert (target / rel).read_bytes() == data, rel
    for name in CONFIGURE.AGENTS:
        h = yaml.safe_load((target / f'.fullsend/{name}/{name}.yaml').read_text())
        assert h['validation_loop']['max_iterations'] == 1
        assert h['plugins'] == ['plugins/strat-pipeline']
        assert h['pre_script'] == 'shared/pre-strategy.sh'
        assert h['post_script'] == 'shared/post-strategy.sh'
        assert h['model'] == CONFIGURE.DEFAULT_MODEL and h['effort'] == 'high'
        env = h['env']['sandbox']
        assert env['CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS'] == '10'
        for key in ('ANTHROPIC_MODEL', 'CLAUDE_CODE_SUBAGENT_MODEL', 'ANTHROPIC_DEFAULT_HAIKU_MODEL',
                    'ANTHROPIC_DEFAULT_OPUS_MODEL', 'ANTHROPIC_DEFAULT_SONNET_MODEL'):
            assert env[key] == CONFIGURE.DEFAULT_MODEL


def test_credentials_are_only_host_references(target, monkeypatch):
    secrets = ['canary-relay-key-7b4f281d', 'canary-jira-token-dc13907a']
    monkeypatch.setenv('MODEL_RELAY_API_KEY', secrets[0])
    monkeypatch.setenv('JIRA_TOKEN', secrets[1])
    configure(target)
    for name in CONFIGURE.AGENTS:
        h = yaml.safe_load((target / f'.fullsend/{name}/{name}.yaml').read_text())
        assert not h['host_files']
        assert not ({'JIRA_TOKEN', 'ANTHROPIC_API_KEY', 'MODEL_RELAY_API_KEY'} & h['env']['sandbox'].keys())
        assert h['providers'] == ['model-relay', 'local-jira']
    for p in (target / '.fullsend').rglob('*'):
        if p.is_file():
            assert all(s.encode() not in p.read_bytes() for s in secrets)
    provider = yaml.safe_load((target / '.fullsend/providers/model-relay.yaml').read_text())
    assert provider['credentials'] == {'ANTHROPIC_API_KEY': '${MODEL_RELAY_API_KEY}'}


def test_policies_have_exact_endpoints_and_no_tls_bypass(target):
    configure(target)
    policy = yaml.safe_load((target / '.fullsend/shared/policy.yaml').read_text())
    assert policy['network_policies'] == {}
    hosts = set()
    for name in ('model-relay', 'local-jira'):
        p = yaml.safe_load((target / f'.fullsend/profiles/{name}.yaml').read_text())
        for endpoint in p['endpoints']:
            hosts.add(endpoint['host'])
            assert endpoint['protocol'] == 'rest'
            assert endpoint['enforcement'] == 'enforce'
            assert not endpoint.get('allow_uninspected_credentials')
            assert endpoint.get('tls') != 'skip'
    assert hosts == {'relay-api.local', 'jira.local'}
    relay = yaml.safe_load((target / '.fullsend/profiles/model-relay.yaml').read_text())
    # Actual leaf executable in OpenShell's denied-action record for 2099.
    assert '/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe' in relay['binaries']


@pytest.mark.parametrize('model,effort,cap', [(CONFIGURE.DEFAULT_MODEL, 'bogus', 10),
        (CONFIGURE.DEFAULT_MODEL, 'medium', 0), (CONFIGURE.DEFAULT_MODEL, 'medium', 101), ('bad;command', 'high', 10)])
def test_invalid_configuration_fails_before_writes(target, model, effort, cap):
    with pytest.raises(ValueError):
        CONFIGURE.configure(target, 'image', model, effort, cap)
    assert not (target / '.fullsend/config.yaml').exists()


def test_redaction_includes_relay_and_encoded_jira_credentials(tmp_path):
    relay, jira = 'canary-relay-api-key-cd381d2a', 'canary-jira-token-dc13907a'
    auth = base64.b64encode(f'fixture-user:{jira}'.encode()).decode()
    env = {**os.environ, 'MODEL_RELAY_API_KEY': relay, 'JIRA_USER': 'fixture-user', 'JIRA_TOKEN': jira}
    p = subprocess.run([sys.executable, str(HERE / 'ci/redact.py'), '--stream'],
        input=f'{relay} {jira} {auth}\n', env=env, text=True, capture_output=True, check=True)
    assert p.stdout == '[REDACTED] [REDACTED] [REDACTED]\n'


def test_ci_does_not_auto_launch_and_shares_the_batch_lock():
    ci = yaml.safe_load((HERE / 'ci/gitlab-ci.yml').read_text())
    assert ci['workflow']['rules'][0]['when'] == 'never'
    assert ci['variables']['WORKFLOW_MODEL'] == CONFIGURE.DEFAULT_MODEL
    assert ci['variables']['WORKFLOW_EFFORT'] == 'high'
    assert ci['variables']['STRAT_CREATOR_BRANCH'] == 'feat/s1-workflow-hardening'
    assert ci['variables']['FULLSEND_VERSION'] == '0.47.1'
    assert ci['variables']['STRAT_CREATOR_SHA'] == '6ed858b2294a29457153a90f187a801022c21e8b'
    for name in ('strat-single', 'strat-batch', 'workflow-preflight'):
        assert ci[name]['environment'] == 'fullsend-claude-workflow'
        assert ci[name]['artifacts']['when'] == 'always'
    assert ci['strat-single']['resource_group'] == ci['strat-batch']['resource_group'] == 'strat-batch'
    assert all('schedule' not in r.get('if', '') for r in ci['strat-batch']['rules'])


def test_scripts_parse():
    for path in (HERE / 'ci').glob('*.sh'):
        subprocess.run(['bash', '-n', str(path)], check=True)


def test_strategy_exports_combined_ca_before_any_network_bootstrap(tmp_path):
    bundle = tmp_path / '.ci-ca-bundle.pem'
    bundle.write_text('fixture-public-bundle')
    commands = tmp_path / 'bin'
    commands.mkdir()
    curl = commands / 'curl'
    curl.write_text('#!/bin/sh\nprintf "%s\\n" "$SSL_CERT_FILE" "$REQUESTS_CA_BUNDLE" '
                    '"$GIT_SSL_CAINFO" > "$CI_PROJECT_DIR/observed-ca.txt"\nexit 42\n')
    curl.chmod(0o755)
    env = {**os.environ, 'PATH':str(commands) + os.pathsep + os.environ['PATH'],
        'CI_PROJECT_DIR':str(tmp_path), 'CI_JOB_ID':'fixture-job',
        'FULLSEND_VERSION':'0.47.1', 'FULLSEND_TARBALL_SHA256':'unused-fixture',
        'MODEL_RELAY_API_KEY':'canary-relay-key', 'JIRA_SERVER':'https://jira.local',
        'JIRA_USER':'fixture-user', 'JIRA_TOKEN':'canary-jira-token',
        'GIT_SSL_CAINFO':str(tmp_path / 'inherited-local-only-ca')}
    result = subprocess.run(['bash', str(HERE/'ci/strategy.sh'), 'preflight'],
        env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 42  # Stub stops before downloads or inference.
    assert (tmp_path/'observed-ca.txt').read_text().splitlines() == [str(bundle)] * 3


def test_publisher_copies_exact_base_and_never_creates_a_pipeline():
    heads = {'main': 'a' * 40, PUBLISH.BASE: PUBLISH.BASE_SHA, 'feat/fullsend-strategy-poc': 'b' * 40}
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path))
        p = request.url.path
        if p == '/projects/' + PUBLISH.PROJECT:
            return httpx.Response(200, json={'id': 7})
        if p.endswith('/repository/branches'):
            if request.method == 'POST':
                payload = json.loads(request.content)
                assert payload['ref'] == PUBLISH.BASE_SHA
                heads[PUBLISH.BRANCH] = PUBLISH.BASE_SHA
                return httpx.Response(201, json={'commit': {'id': PUBLISH.BASE_SHA}})
            return httpx.Response(200, json=[{'name': n, 'commit': {'id': s}} for n, s in heads.items()])
        if p.endswith('/variables'):
            return httpx.Response(200, json=[{'key': n} for n in ('JIRA_SERVER', 'JIRA_USER', 'JIRA_TOKEN',
                'MODEL_RELAY_API_KEY', 'RESULTS_PUSH_TOKEN', 'ORG_PULSE_API_TOKEN')])
        if '/repository/files/' in p:
            return httpx.Response(404)
        if p.endswith('/repository/commits'):
            body = json.loads(request.content)
            assert body['branch'] == PUBLISH.BRANCH
            assert '[skip ci]' in body['commit_message']
            heads[PUBLISH.BRANCH] = 'c' * 40
            return httpx.Response(201, json={'id': 'c' * 40})
        raise AssertionError((request.method, p))

    with httpx.Client(transport=httpx.MockTransport(handler), base_url='https://fixture') as c:
        report = PUBLISH.publish(c, True)
    assert report['baselines_unchanged']
    assert all('/pipeline' not in p and '/schedules' not in p for _, p in calls)


def test_released_cli_registers_and_locks_the_harness(target):
    binary = os.environ.get('WORKFLOW_TEST_FULLSEND')
    if not binary:
        pytest.skip('Set WORKFLOW_TEST_FULLSEND to the checksum-verified released CLI')
    configure(target)
    for name in CONFIGURE.AGENTS:
        subprocess.run([binary, 'agent', 'add', f'{name}/{name}.yaml', '--name', name,
                        '--fullsend-dir', str(target / '.fullsend')], check=True, capture_output=True)
        subprocess.run([binary, 'lock', name, '--fullsend-dir', str(target / '.fullsend'), '--offline'],
                       check=True, capture_output=True)


def test_released_cli_accepts_the_actual_launch_debug_arguments(tmp_path):
    binary = os.environ.get('WORKFLOW_TEST_FULLSEND')
    if not binary:
        pytest.skip('Set WORKFLOW_TEST_FULLSEND to the checksum-verified released CLI')
    launch = (HERE / 'ci/launch.sh').read_text()
    debug = shlex.split(launch.split('--keep-sandbox', 1)[1].splitlines()[0])
    # A missing configuration guarantees this reaches no sandbox or model.
    result = subprocess.run([binary, 'run', 'strat-single', '--fullsend-dir',
        str(tmp_path / 'missing'), '--target-repo', str(tmp_path),
        '--keep-sandbox', *debug], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'no config and agents-repo fallback unavailable' in result.stderr
    assert 'received 2' not in result.stderr


def test_archive_rejects_traversal_and_symlinks(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, 'publish', PUBLISH)
    archiver = module('workflow_archive', HERE / 'archive.py')
    for index, name in enumerate(('../escape.txt', '/absolute.txt', 'link')):
        path = tmp_path / f'{index}.zip'
        with zipfile.ZipFile(path, 'w') as z:
            item = zipfile.ZipInfo(name)
            if name == 'link':
                item.external_attr = 0o120777 << 16
            z.writestr(item, b'outside')
        with pytest.raises(ValueError):
            archiver.unpack(path, tmp_path / f'capture-{index}')
    assert not (tmp_path / 'escape.txt').exists()


def test_archive_preserves_valid_native_evidence_and_refuses_overwrite(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, 'publish', PUBLISH)
    archiver = module('workflow_archive', HERE / 'archive.py')
    zipped, target = tmp_path / 'evidence.zip', tmp_path / 'capture'
    data = b'{"type":"native-session-fixture"}\n'
    with zipfile.ZipFile(zipped, 'w') as z:
        z.writestr('fullsend-ci-artifacts/sandbox/claude-config/session.jsonl', data)
    archiver.unpack(zipped, target)
    assert (target / 'fullsend-ci-artifacts/sandbox/claude-config/session.jsonl').read_bytes() == data
    with pytest.raises(FileExistsError):
        archiver.unpack(zipped, target)


def test_downloaded_symlinks_are_recorded_without_reading_their_targets(tmp_path):
    collector = module('workflow_collect', HERE / 'ci/collect.py')
    outside = tmp_path / 'outside'
    outside.mkdir()
    secret = outside / 'private'
    secret.write_text('must-not-be-read')
    captured = tmp_path / 'capture'
    captured.mkdir()
    (captured / 'link-file').symlink_to(secret)
    (captured / 'link-dir').symlink_to(outside, target_is_directory=True)
    (captured / 'native.json').write_text('{}')
    records = collector.record_links(captured)
    assert len(records) == 2
    assert secret.read_text() == 'must-not-be-read'
    assert not (captured / 'link-file').exists()
    assert not (captured / 'link-dir').exists()
    assert (captured / 'native.json').read_text() == '{}'
    assert 'must-not-be-read' not in (captured / 'symlink-inventory.json').read_text()
    before = (captured / 'symlink-inventory.json').read_bytes()
    assert collector.record_links(captured) == []
    assert (captured / 'symlink-inventory.json').read_bytes() == before


def test_redactor_preserves_host_clone_evidence_without_following_links(tmp_path):
    outside = tmp_path / 'private'
    outside.write_text('outside-content-must-not-be-captured')
    directory = tmp_path / 'fullsend-ci-artifacts'
    directory.mkdir()
    (directory / 'trusted-clone-alias').symlink_to(outside)
    (directory / 'metadata.json').write_text('{"value":"canary-relay-key-cb973cdd"}')
    env = {**os.environ, 'CI_PROJECT_DIR': str(tmp_path),
           'MODEL_RELAY_API_KEY': 'canary-relay-key-cb973cdd'}
    for _ in range(2):
        subprocess.run([sys.executable, str(HERE / 'ci/redact.py')], env=env,
                       check=True, capture_output=True)
    assert outside.read_text() == 'outside-content-must-not-be-captured'
    assert not (directory / 'trusted-clone-alias').exists()
    assert json.loads((directory / 'metadata.json').read_text())['value'] == '[REDACTED]'
    assert len(json.loads((directory / 'symlink-inventory.json').read_text())) == 1
    assert all('outside-content-must-not-be-captured' not in p.read_text()
               for p in directory.rglob('*') if p.is_file())


def test_archive_cannot_claim_completeness_without_required_job_artifacts(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, 'publish', PUBLISH)
    archiver = module('workflow_archive', HERE / 'archive.py')
    collector = archiver.archive.Collector(tmp_path, 'unused')
    def handler(request):
        if request.url.path.endswith('/jobs'):
            return httpx.Response(200, json=[{'id': 4062, 'name': 'strat-single',
                'status': 'failed', 'artifacts': [], 'artifacts_file': None}])
        if request.url.path.endswith('/trace'):
            return httpx.Response(200, content=b'preparation failed\n')
        raise AssertionError(request.url.path)
    with httpx.Client(transport=httpx.MockTransport(handler), base_url='https://fixture') as c:
        archiver.collect_jobs(c, collector, tmp_path, 7, 2097, 'gitlab')
    assert len(collector.errors) == 1
    assert 'Required native job artifacts' in collector.errors[0]['error']
    assert (tmp_path / 'gitlab/jobs/4062/trace.log').read_bytes() == b'preparation failed\n'
