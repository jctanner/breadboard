"""Privileged mirrors reject symlinks instead of exporting host files."""
import importlib.util
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_seed(name, monkeypatch):
    directory = ROOT / 'deploy/fullsend/seed'
    monkeypatch.syspath_prepend(str(directory))
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), directory / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('name', ['seed-upstream-agents', 'seed-upstream-fullsend'])
@pytest.mark.parametrize('kind', ['regular', 'file_symlink', 'directory_symlink'])
def test_mirror_collection_rejects_symlink_sources(tmp_path, monkeypatch, name, kind):
    module = load_seed(name, monkeypatch)
    source = tmp_path / 'source'
    source.mkdir()
    subprocess.run(['git', 'init', str(source)], check=True, capture_output=True)
    external = tmp_path / 'host-file'
    external.write_text('must never be mirrored')
    if kind == 'file_symlink':
        (source / 'payload').symlink_to(external)
    elif kind == 'directory_symlink':
        (source / 'payload').symlink_to(tmp_path, target_is_directory=True)
    else:
        (source / 'payload').write_text('public fixture')
    subprocess.run(['git', '-C', str(source), 'add', 'payload'], check=True, capture_output=True)
    monkeypatch.setattr(module, 'SOURCE', source)
    if name == 'seed-upstream-fullsend':
        monkeypatch.setattr(module, 'MIRRORED_PATHS', ('payload',))
    if kind == 'regular':
        assert module.collect_sources() == [(source / 'payload', 'payload')]
    else:
        with pytest.raises(RuntimeError, match='symlink'):
            module.collect_sources()


@pytest.mark.parametrize('relative', ['../host-file', '/etc/passwd'])
def test_mirror_source_rejects_escape(tmp_path, monkeypatch, relative):
    module = load_seed('seed-upstream-agents', monkeypatch)
    with pytest.raises(RuntimeError, match='inside'):
        module.seed_source_path(tmp_path, relative)


def test_fetched_mirror_links_are_removed_without_following(tmp_path, monkeypatch):
    module = load_seed('seed-upstream-fullsend', monkeypatch)
    outside = tmp_path / 'outside'
    outside.mkdir()
    retained = outside / 'keep'
    retained.write_text('must survive')
    mirror = tmp_path / 'mirror'
    mirror.mkdir()
    (mirror / '.git').mkdir()
    (mirror / '.github').symlink_to(outside, target_is_directory=True)
    (mirror / 'action.yml').symlink_to(outside / 'missing')
    (mirror / 'obsolete').mkdir()
    (mirror / 'obsolete/file').write_text('remove')
    module.clear_mirror_worktree(mirror)
    assert retained.read_text() == 'must survive'
    assert not (outside / 'missing').exists()
    assert list(mirror.iterdir()) == [mirror / '.git']
