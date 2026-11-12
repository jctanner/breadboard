"""The scenario reads a file the fresh-target seeder actually creates."""
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_seed(name, monkeypatch):
    directory = ROOT/'deploy/fullsend/seed'
    monkeypatch.syspath_prepend(str(directory))
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), directory/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checkout_assertions_use_the_fresh_targets_seeded_shim(monkeypatch):
    producer = load_seed('seed-triage-auto-code-off', monkeypatch)
    scenario = load_seed('seed-behaviour-script', monkeypatch)
    ops = yaml.safe_load(scenario.render())['ops']
    repo_assertions = [op['args'] for op in ops if op['op']=='assert_file' and op['args'].startswith('target-repo/')]
    reads = [op['args'] for op in ops if op['op']=='read_file']
    assert repo_assertions == ['target-repo/'+producer.SHIM_PATH]
    assert reads == [producer.SHIM_PATH]


def test_real_seeder_writes_the_scenarios_witness_and_is_idempotent(monkeypatch):
    import base64
    producer = load_seed('seed-triage-auto-code-off', monkeypatch)
    scenario = load_seed('seed-behaviour-script', monkeypatch)
    files = {}
    writes = []
    monkeypatch.setattr(producer, 'ensure_org', lambda: None)
    monkeypatch.setattr(producer, 'ensure_repo', lambda: None)
    monkeypatch.setattr(producer, '_mirror_pin', lambda: ('a'*40, 'b'*64))
    prefix = f'/repos/{producer.ORG}/{producer.REPO}/contents/'
    def api(method, path, body=None):
        assert path.startswith(prefix)
        relative = path[len(prefix):]
        if method == 'GET':
            if relative not in files:
                return 404, None
            return 200, {'content': base64.b64encode(files[relative]).decode(), 'sha': 'fixture'}
        assert method == 'PUT'
        writes.append(relative)
        files[relative] = base64.b64decode(body['content'])
        return 201, {}
    monkeypatch.setattr(producer, 'api_request', api)
    producer.main()
    ops = yaml.safe_load(scenario.render())['ops']
    for op in ops:
        if op['op']=='read_file':
            assert files[op['args']]
        elif op['op']=='assert_file' and op['args'].startswith('target-repo/'):
            assert files[op['args'].removeprefix('target-repo/')]
    assert 'README.md' not in files  # A fresh target need not invent user content.
    writes.clear()
    producer.main()
    assert not writes
