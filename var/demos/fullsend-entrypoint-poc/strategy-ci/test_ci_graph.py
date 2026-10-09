"""Focused normal/diagnostic job graph regression (run with pytest)."""
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parent


def jobs(config, variables):
    result = set()
    for name, job in config.items():
        if name.startswith('.') or not isinstance(job, dict) or 'stage' not in job:
            continue
        merged = dict(job)
        if 'extends' in job:
            merged = dict(config[job['extends']], **job)
        rules = merged.get('rules', [{'when': 'always'}])
        for rule in rules:
            condition = rule.get('if', 'True')
            condition = re.sub(r'\$([A-Z0-9_]+)', lambda m: repr(variables.get(m[1], '')), condition)
            condition = condition.replace('&&', ' and ').replace('||', ' or ')
            if eval(condition, {'__builtins__': {}}):
                if rule.get('when') != 'never': result.add(name)
                break
    return result


def test_normal_batch_single_and_schedule_graphs():
    config = yaml.safe_load((ROOT / 'gitlab-ci.yml').read_text())
    for mode in ('single-rfe', 'batch-discover'):
        variables = {'STRATEGY_MODE': mode, 'RFE_KEY': 'RHAIRFE-99' if mode == 'single-rfe' else '', 'CI_PIPELINE_SOURCE': 'api'}
        selected = jobs(config, variables)
        assert selected == {'build-fullsend-feature', mode, 'build-dashboard-' + mode}
        for name in selected:
            for dependency in config[name].get('needs', []) + config[name].get('dependencies', []):
                assert dependency in selected
    assert jobs(config, {'CI_PIPELINE_SOURCE': 'schedule'}) == {'build-fullsend-feature', 'batch-discover', 'build-dashboard-batch-discover'}
    assert config['batch-discover']['resource_group'] == 'strat-batch'
    assert config['batch-discover']['timeout'] == '5h'
    assert 'redact' in config['default']['before_script'][0]
    assert not {'batch-jql', 'batch-config', 'batch-selected', 'model-smoke', 'lifecycle-check', 'sandbox-connectivity'} & set(config)


def test_opt_in_diagnostics_exclude_capability_matrix():
    config = yaml.safe_load((ROOT.parent / 'runner-validation/gitlab-ci.yml').read_text())
    for diagnostic in ('model-smoke', 'lifecycle-check', 'sandbox-connectivity', 'batch-controls'):
        assert jobs(config, {'M8_DIAGNOSTIC': diagnostic}) == {'build-fullsend-feature', diagnostic}
