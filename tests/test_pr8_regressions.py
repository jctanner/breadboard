"""Offline regression checks for deployment/domain and release safety."""
import importlib.util
import runpy
import ssl
import sys
from pathlib import Path
from unittest import mock

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render = load('render_pr8', 'deploy/scripts/render_domain_manifest.py')


@pytest.mark.parametrize('domain', ['x\ny: z', 'x/y', 'x&y', 'x;id', 'x$(id)', '-bad', 'UPPER', 'a..b'])
def test_domain_rejects_config_and_shell_syntax(domain):
    with pytest.raises(ValueError):
        render.transform_manifest('', domain)


@pytest.mark.parametrize('domain', ['local', 'bb.internal'])
def test_all_certificate_names_fit_ca_constraints(domain):
    ca_docs = yaml.safe_load_all(render.transform_manifest((ROOT / 'deploy/k8s/01-ca-issuer.yaml').read_text(), domain))
    ca = next(d for d in ca_docs if d['kind'] == 'Certificate')
    permitted = ca['spec']['nameConstraints']['permitted']
    paths = list((ROOT / 'deploy/k8s').glob('*.yaml')) + [ROOT / 'deploy/golang-reverse-proxy/deployment.yaml']
    for path in paths:
        for doc in yaml.safe_load_all(render.transform_manifest(path.read_text(), domain)):
            if not isinstance(doc, dict) or doc.get('kind') != 'Certificate':
                continue
            for name in doc['spec'].get('dnsNames', []):
                assert any(name == constraint or name.endswith('.' + constraint.lstrip('.'))
                           for constraint in permitted['dnsDomains']), (path, name)
            for ip in doc['spec'].get('ipAddresses', []):
                assert ip + '/32' in permitted['ipRanges']
    if domain != 'local':
        assert 'local' not in permitted['dnsDomains']
        assert '.local' not in permitted['dnsDomains']
        assert 'svc.cluster.local' in permitted['dnsDomains']


@pytest.mark.parametrize(('machine', 'arch'), [(62, 'amd64'), (183, 'arm64')])
def test_release_architecture_comes_from_binary(tmp_path, machine, arch):
    with mock.patch.object(sys, 'path', [str(ROOT / 'deploy/fullsend/seed'), *sys.path]):
        release = load('release_pr8', 'deploy/fullsend/seed/seed-fullsend-release.py')
    binary = tmp_path / 'fullsend'
    binary.write_bytes(b'\x7fELF\x02\x01' + b'\0' * 12 + machine.to_bytes(2, 'little'))
    assert release.binary_arch(binary) == arch
    binary.write_bytes(b'not an executable')
    with pytest.raises(RuntimeError):
        release.binary_arch(binary)


def test_bb_preserves_operator_context_and_verifies_tls():
    with mock.patch.object(sys, 'argv', ['bb']):
        bb = runpy.run_path(str(ROOT / 'scripts/bb'), run_name='bb_test')
    with mock.patch.dict('os.environ', {}, clear=True):
        assert bb['resolve_domain']() == 'local'
        context = bb['get_ssl_context']()
        assert context.check_hostname
        assert context.verify_mode == ssl.CERT_REQUIRED
        bb['setup_env']()
        import os
        assert 'KUBECONFIG' not in os.environ


def test_bb_does_not_invent_healthy_runners():
    with mock.patch.object(sys, 'argv', ['bb']):
        bb = runpy.run_path(str(ROOT / 'scripts/bb'), run_name='bb_test')
    with mock.patch('urllib.request.urlopen', side_effect=OSError('offline')):
        assert bb['fetch_runners']('local') == []


def test_cve_runtime_transition_removes_canned_result(tmp_path):
    with mock.patch.object(sys, 'path', [str(ROOT / 'deploy/fullsend/seed'), *sys.path]):
        seed = load('cve_pr8', 'deploy/fullsend/seed/seed-cve-fixture.py')
    seed.stage_files(tmp_path, 'https://github.bb.internal', 'a' * 40, 'b' * 64)
    scenario = tmp_path / '.fullsend/behaviour/current-scenario.yaml'
    assert 'SYNTHETIC' in scenario.read_text()
    seed.stage_files(tmp_path, 'https://github.bb.internal', 'a' * 40, 'b' * 64, runtime='pi')
    assert not scenario.exists()
    assert 'itpc-' not in (tmp_path / '.fullsend/triage.yaml').read_text()


def test_reset_requires_confirmation_before_commands():
    with mock.patch.object(sys, 'argv', ['bb']):
        bb = runpy.run_path(str(ROOT / 'scripts/bb'), run_name='bb_test')
    with mock.patch('subprocess.run') as command:
        with pytest.raises(SystemExit) as exc:
            bb['cmd_openshell']('local', 'reset')
        assert exc.value.code == 2
        command.assert_not_called()


def test_git_remote_handles_http_and_escapes_credentials():
    with mock.patch.object(sys, 'path', [str(ROOT / 'deploy/fullsend/seed'), *sys.path]):
        emulator = load('emulator_pr8', 'deploy/fullsend/seed/emulator.py')
    with mock.patch.object(emulator, 'BASE_URL', 'http://127.0.0.1:8000'), mock.patch.object(emulator, 'TOKEN', 'a@b/c'):
        assert emulator.git_remote('owner', 'repo') == 'http://x-access-token:a%40b%2Fc@127.0.0.1:8000/owner/repo.git'


def test_lima_uses_repository_only_mount_and_argv(tmp_path):
    lima = load('lima_pr8', 'scripts/lima.py')
    root = tmp_path / "repo ' $(command)"
    calls = []

    def run(*args, **kwargs):
        calls.append(args)
        return mock.Mock(stdout='')

    with mock.patch.object(lima, 'ROOT', root), mock.patch.object(lima, 'run', side_effect=run), mock.patch('subprocess.run'), mock.patch.object(sys, 'argv', ['lima.py', 'up']), mock.patch.dict('os.environ', {}, clear=True):
        lima.main()
    create = next(call for call in calls if call[0] == 'start')
    assert '--mount-only' in create
    assert str(root) + ':w' in create
    assert '~' not in create
    assert not any('bash' in call for call in calls)


@pytest.mark.parametrize(('domain', 'allowed', 'forbidden'), [
    ('local', 'dashboard.local', 'unrelated.local'),
    ('bb.internal', 'dashboard.bb.internal', 'dashboard.local'),
])
def test_openssl_enforces_rendered_ca_dns_constraints(tmp_path, domain, allowed, forbidden):
    """Exercise X.509 chain validation, not just YAML/string expectations."""
    import datetime
    import ipaddress
    import shutil
    import subprocess
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    if not shutil.which('openssl'):
        pytest.skip('openssl is required for chain validation')
    docs = yaml.safe_load_all(render.transform_manifest((ROOT / 'deploy/k8s/01-ca-issuer.yaml').read_text(), domain))
    permitted = next(d for d in docs if d['kind'] == 'Certificate')['spec']['nameConstraints']['permitted']
    now = datetime.datetime.now(datetime.timezone.utc)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Offline test CA')])
    base = x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=1)).not_valid_after(now + datetime.timedelta(days=1))
    constraints = [x509.DNSName(name) for name in permitted['dnsDomains']]
    constraints += [x509.IPAddress(ipaddress.ip_network(value)) for value in permitted['ipRanges']]
    ca = base.add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True).add_extension(x509.NameConstraints(permitted_subtrees=constraints, excluded_subtrees=None), critical=True).sign(key, hashes.SHA256())
    ca_path = tmp_path / 'ca.crt'
    ca_path.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    for name, expected in [(allowed, 0), (forbidden, 2)]:
        leaf = x509.CertificateBuilder()
        leaf = leaf.subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=1)).not_valid_after(now + datetime.timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName(name)]), critical=False).sign(key, hashes.SHA256())
        leaf_path = tmp_path / 'leaf.crt'
        leaf_path.write_bytes(leaf.public_bytes(serialization.Encoding.PEM))
        result = subprocess.run(['openssl', 'verify', '-CAfile', str(ca_path), '-verify_hostname', name, str(leaf_path)], capture_output=True, text=True)
        assert result.returncode == expected, result.stderr


def test_demo_seeder_finds_existing_issue_after_first_page():
    seed = load('demo_pr8', 'deploy/scripts/seed_demo_tickets.py')
    seeder = seed.GitLabSeeder('https://gitlab.local')
    response1 = mock.Mock()
    response1.json.return_value = [{'iid': i, 'title': str(i)} for i in range(100)]
    response2 = mock.Mock()
    response2.json.return_value = [{'iid': 101, 'title': 'existing target'}]
    seeder.session = mock.Mock()
    seeder.session.get.side_effect = [response1, response2]
    assert seeder.ensure_issue(1, 'existing target', '', []) == (101, False)
    seeder.session.post.assert_not_called()
    assert seeder.session.get.call_args.kwargs['params']['page'] == 2


def test_cve_issue_lookup_failure_does_not_create_duplicate():
    with mock.patch.object(sys, 'path', [str(ROOT / 'deploy/fullsend/seed'), *sys.path]):
        seed = load('cve_lookup_pr8', 'deploy/fullsend/seed/seed-cve-fixture.py')
    with mock.patch.object(seed, 'api_request', return_value=(503, None)) as api:
        with pytest.raises(RuntimeError, match='Cannot check'):
            seed.ensure_assessment_issue()
        assert api.call_count == 1
        assert api.call_args.args[0] == 'GET'
