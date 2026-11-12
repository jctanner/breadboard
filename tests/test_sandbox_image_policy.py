"""The pinned image policy remains equivalent under OpenShell's new TLS spelling."""
import importlib.util
import io
import tarfile
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('image_policy', ROOT / 'deploy/scripts/prepare_sandbox_policy.py')
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)

POLICY = '''version: 1
filesystem_policy:
  read_only: [/usr, /etc]
  read_write: [/sandbox, /tmp]
process: {run_as_user: sandbox, run_as_group: sandbox}
network_policies:
  github:
    endpoints:
      - {host: github.local, port: 443, protocol: rest, tls: terminate, access: read-only}
      - {host: public.example, port: 443, tls: passthrough}
      - {host: default.example, port: 443}
    binaries: [{path: /usr/bin/git}]
'''


def test_migration_preserves_permissions_and_other_tls_modes():
    expected = yaml.safe_load(POLICY)
    expected['network_policies']['github']['endpoints'][0]['tls'] = ''
    migrated = helper.migrate_policy(POLICY)
    assert yaml.safe_load(migrated) == expected
    assert helper.migrate_policy(migrated) == migrated


@pytest.mark.parametrize('raw', ['[]', 'version: 2', 'version: 1\nnetwork_policies: []',
                               'version: 1\nnetwork_policies: {x: {endpoints: [bad]}}'])
def test_invalid_policy_fails_closed(raw):
    with pytest.raises(ValueError):
        helper.migrate_policy(raw)


@pytest.mark.parametrize('failure', [None, 'missing', 'invalid', 'symlink', 'oversized', 'hardlink', 'directory', 'multiple', 'archive_oversized'])
def test_image_is_never_executed_and_container_is_always_removed(tmp_path, monkeypatch, failure):
    calls = []
    container_id = 'a'*64
    def create(args, **kwargs):
        calls.append(args)
        assert args[:4] == ['sudo', 'podman', 'create', '--name']
        assert args[4].startswith('breadboard-policy-')
        assert args[5:] == ['--entrypoint', '/bin/true', 'fixture@sha256:'+'b'*64]
        return container_id+'\n'
    def run(args, **kwargs):
        calls.append(args)
        if args[2] == 'cp':
            if failure == 'missing':
                raise subprocess.CalledProcessError(1, args)
            assert args[-1] == '-'
            raw = ('x'*1_048_577 if failure == 'oversized' else ('[]' if failure == 'invalid' else POLICY)).encode()
            with tarfile.open(fileobj=kwargs['stdout'], mode='w:') as archive:
                member = tarfile.TarInfo('policy.yaml')
                member.mode = 0o600  # Root-owned/private image metadata must not prevent parsing.
                member.uid = 0
                if failure in {'symlink', 'hardlink', 'directory'}:
                    member.type = {'symlink': tarfile.SYMTYPE, 'hardlink': tarfile.LNKTYPE, 'directory': tarfile.DIRTYPE}[failure]
                    member.linkname = str(tmp_path / 'private-file')
                    archive.addfile(member)
                else:
                    member.size = len(raw)
                    archive.addfile(member, io.BytesIO(raw))
                if failure == 'multiple':
                    archive.addfile(tarfile.TarInfo('other.yaml'))
            if failure == 'archive_oversized':
                kwargs['stdout'].write(b'x'*2_097_152)
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(helper.subprocess, 'check_output', create)
    monkeypatch.setattr(helper.subprocess, 'run', run)
    output = tmp_path / 'output.yaml'
    if failure:
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            helper.prepare_policy('fixture@sha256:'+'b'*64, output, ['sudo', 'podman'])
        assert not output.exists()
    else:
        helper.prepare_policy('fixture@sha256:'+'b'*64, output, ['sudo', 'podman'])
        assert yaml.safe_load(output.read_text())['network_policies']['github']['endpoints'][0].get('tls') == ''
        assert output.stat().st_mode & 0o777 == 0o644
    assert calls[-1] == ['sudo', 'podman', 'rm', '-v', calls[0][4]]
    assert not any('run' in call or 'start' in call for call in calls)


@pytest.mark.parametrize('spelling', ['terminate', "'terminate'", '"terminate"'])
def test_scalar_only_migration_keeps_unrelated_yaml_spelling(spelling):
    raw = ('# comment\nversion: 1\ncustom: {enabled: on, disabled: off, mode: 0755, time: 1:30}\n'
           'network_policies:\n  x:\n    endpoints:\n      - host: github.local\n'
           f'        tls: {spelling} # preserve comment\n'
           f'      - {{host: other.local, tls: {spelling}, access: read-only}}\n')
    assert helper.migrate_policy(raw) == raw.replace('tls: '+spelling, 'tls: ""')


@pytest.mark.parametrize('raw', [
    'version: 1\nnetwork_policies: &p {}',
    'version: 1\nnetwork_policies: {x: &p {endpoints: []}, y: *p}',
    'version: 1\nversion: 1',
])
def test_ambiguous_policy_requires_explicit_migration(raw):
    with pytest.raises(ValueError):
        helper.migrate_policy(raw)


@pytest.mark.parametrize('value', ['>-\n          terminate\n', '|-\n          terminate\n',
                                 '!!str terminate', '!foo terminate'])
def test_unusual_legacy_tls_scalars_fail_before_output(value):
    raw = 'version: 1\nnetwork_policies:\n  x:\n    endpoints:\n      - tls: '+value+'\n'
    with pytest.raises(ValueError, match='explicit migration'):
        helper.migrate_policy(raw)


def test_bad_container_id_still_cleans_named_container(tmp_path, monkeypatch):
    calls = []
    def create(args, **kwargs):
        calls.append(args)
        return 'unexpected output'
    def cleanup(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(helper.subprocess, 'check_output', create)
    monkeypatch.setattr(helper.subprocess, 'run', cleanup)
    with pytest.raises(ValueError, match='container ID'):
        helper.prepare_policy('fixture', tmp_path/'output', ['podman'])
    assert calls[-1] == ['podman', 'rm', '-v', calls[0][3]]


def test_cleanup_failure_preserves_original_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(helper.subprocess, 'check_output', lambda *a, **kw: 'bad-id')
    monkeypatch.setattr(helper.subprocess, 'run', lambda args, **kw: subprocess.CompletedProcess(args, 1))
    with pytest.raises(ValueError, match='container ID'):
        helper.prepare_policy('fixture', tmp_path/'output', ['podman'])
    assert 'could not remove' in capsys.readouterr().err


def test_migration_preserves_utf8_and_crlf():
    raw = ('# café\n'+POLICY).replace('\n', '\r\n')
    assert helper.migrate_policy(raw) == raw.replace('tls: terminate', 'tls: ""')
