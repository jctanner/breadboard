"""Checks for the agent-led POC CI fixtures (run with pytest)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CI = yaml.safe_load((HERE / 'ci' / 'gitlab-ci.yml').read_text())


def test_jobs_and_rules():
    assert {k for k in CI if k not in ('workflow', 'default', 'stages', 'variables')} \
        == {'strat-single', 'strat-batch'}
    assert CI['workflow']['rules'][0] == {'if': '$CI_PIPELINE_SOURCE == "push"', 'when': 'never'}
    single, batch = CI['strat-single'], CI['strat-batch']
    assert single['rules'] == [{'if': '$STRATEGY_MODE == "strat-single" && $RFE_KEY != ""'}]
    assert single['resource_group'] == 'strat-agent-led'
    assert batch['rules'] == [
        {'if': '$CI_PIPELINE_SOURCE == "schedule" && $RFE_KEY == ""'},
        {'if': '$STRATEGY_MODE == "strat-batch" && $RFE_KEY == ""'}]
    assert batch['resource_group'] == 'strat-batch'
    for job, agent in ((single, 'strat-single'), (batch, 'strat-batch')):
        assert job['image'] == 'quay.io/aipcc/agentic-ci/openshell:0.3.46'
        assert job['script'][-1] == f'bash ci-scripts/agent-led-strategy.sh {agent}'
        assert job['artifacts']['when'] == 'always'


def test_pins_and_results_target():
    v = CI['variables']
    assert v['STRAT_CREATOR_BRANCH'] == 'feat/fullsend-agent-led-strategy'
    assert len(v['STRAT_CREATOR_SHA']) == 40
    assert v['FULLSEND_VERSION'] == '0.43.0'
    assert v['FULLSEND_TARBALL_SHA256'] == \
        'e56be72bb2af7210418307e784d65a8ead4ff736540c077f75d258865e595f10'
    assert v['RESULTS_REPO_URL'] == \
        'https://gitlab.local/redhat/rhel-ai/agentic-ci/strat-pipeline-data.git'
    # No feature binary build or script-led entrypoint.
    text = (HERE / 'ci' / 'gitlab-ci.yml').read_text()
    assert 'build-fullsend' not in text and 'strategy-entrypoint' not in text


def test_scripts_parse():
    for name in ('source.sh', 'strategy.sh', 'gateway.sh'):
        subprocess.run(['bash', '-n', str(HERE / 'ci' / name)], check=True)


def test_stream_redaction_masks_tokens(tmp_path):
    env = {**os.environ, 'JIRA_TOKEN': 'sekrit-jira-token-value',
           'RESULTS_PUSH_TOKEN': 'glpat-results-token-value'}
    env.pop('GOOGLE_APPLICATION_CREDENTIALS', None)
    proc = subprocess.run(
        [sys.executable, str(HERE / 'ci' / 'redact.py'), '--stream'],
        input=b'a sekrit-jira-token-value b glpat-results-token-value\n',
        capture_output=True, env=env, check=True)
    assert proc.stdout == b'a [REDACTED] b [REDACTED]\n'


def test_artifact_redaction_tolerates_removed_credential(tmp_path):
    out = tmp_path / 'fullsend-ci-artifacts'
    out.mkdir()
    (out / 'log.txt').write_text('token=sekrit-jira-token-value\n')
    env = {**os.environ, 'CI_PROJECT_DIR': str(tmp_path),
           'JIRA_TOKEN': 'sekrit-jira-token-value',
           'GOOGLE_APPLICATION_CREDENTIALS': str(tmp_path / 'gone.json')}
    proc = subprocess.run([sys.executable, str(HERE / 'ci' / 'redact.py')],
                          capture_output=True, text=True, env=env, check=True)
    assert json.loads(proc.stdout)['files_changed'] == 1
    assert (out / 'log.txt').read_text() == 'token=[REDACTED]\n'


def test_ci_defines_every_harness_variable():
    """Fullsend fails env validation on any referenced host variable that is
    unset, so the job must define each one (pipeline 2075/job 4036)."""
    import re
    fork = HERE.parents[2] / 'checkouts.fullsend_agent_led_poc' / 'jctanner.strat-creator' / '.fullsend'
    if not fork.is_dir():
        import pytest
        pytest.skip('strat-creator fork checkout not present')
    referenced = set()
    for name in ('strat-single', 'strat-batch'):
        referenced |= set(re.findall(r'\$\{([A-Z0-9_]+)\}', (fork / name / f'{name}.yaml').read_text()))
    script = (HERE / 'ci' / 'strategy.sh').read_text()
    defined_in_script = set(re.findall(r'export ([A-Z0-9_]+)=', script)) | set(
        re.findall(r' ([A-Z0-9_]+)="\$\{', script))
    project_vars = {'JIRA_SERVER', 'JIRA_USER', 'JIRA_TOKEN'}  # required, checked by publish.py
    missing = referenced - defined_in_script - project_vars - set(CI['variables'])
    assert not missing, f'harness references unset host variables: {sorted(missing)}'
