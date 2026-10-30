#!/usr/bin/env python3
"""Apply local integration settings to the job's disposable, pinned checkout.

Only configuration changes here. Workflow code, prompts, hooks and host helpers
remain the published PR 85 source. Credential values never enter generated files.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

AGENTS = ('strat-single', 'strat-batch', 'strat-resume')
DEFAULT_MODEL = 'claude-opus-4-6'
RELAY = 'https://relay-api.local'


def configure(target, image, model, effort, concurrency):
    if not re.fullmatch(r'[A-Za-z0-9_./@-]+', model):
        raise ValueError('invalid model ID')
    if effort not in ('low', 'medium', 'high', 'xhigh', 'max'):
        raise ValueError('invalid effort')
    if not 1 <= concurrency <= 100:
        raise ValueError('concurrency must be between 1 and 100')
    fullsend = target / '.fullsend'
    profile_dir, provider_dir = fullsend / 'profiles', fullsend / 'providers'
    profile_dir.mkdir(exist_ok=True)
    provider_dir.mkdir(exist_ok=True)
    definitions = (
        ('model-relay', 'local-model-relay', 'ANTHROPIC_API_KEY', 'MODEL_RELAY_API_KEY',
         'relay-api.local', ['**/claude', '**/node', '**/python3*',
                             '/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe'],
         [{'allow': {'method': 'GET', 'path': '/v1/models'}},
          {'allow': {'method': 'POST', 'path': '/v1/messages'}},
          {'allow': {'method': 'POST', 'path': '/v1/messages/count_tokens'}}]),
        ('local-jira', 'local-strategy-jira', 'JIRA_TOKEN', 'JIRA_TOKEN',
         'jira.local', ['**/python3*'],
         [{'allow': {'method': m, 'path': '/rest/api/**'}}
          for m in ('GET', 'POST', 'PUT')] +
         [{'allow': {'method': 'DELETE', 'path': '/rest/api/3/attachment/*'}}]),
    )
    for name, profile_id, env, source_env, host, binaries, rules in definitions:
        profile = {'id': profile_id, 'display_name': name, 'category': 'inference' if name == 'model-relay' else 'data',
                   'credentials': [{'name': env, 'env_vars': [env], 'required': True}],
                   'endpoints': [{'host': host, 'port': 443, 'protocol': 'rest',
                                  'enforcement': 'enforce', 'rules': rules}],
                   'binaries': binaries}
        (profile_dir / f'{name}.yaml').write_text(yaml.safe_dump(profile, sort_keys=False))
        (provider_dir / f'{name}.yaml').write_text(yaml.safe_dump({
            'name': name, 'type': profile_id, 'credentials': {env: '${' + source_env + '}'}}, sort_keys=False))
    for agent in AGENTS:
        path = fullsend / agent / f'{agent}.yaml'
        h = yaml.safe_load(path.read_text())
        h.update(model=model, effort=effort, image=image)
        h['host_files'] = []  # No raw Google credential or Vertex env file.
        h['providers'] = ['model-relay', 'local-jira']
        h['openshell'] = {'profiles': ['profiles/model-relay.yaml', 'profiles/local-jira.yaml']}
        sandbox = h['env']['sandbox']
        # Jira uses its provider placeholder, not an expanded secret in .env.
        sandbox.pop('JIRA_TOKEN', None)
        sandbox.update({
            'ANTHROPIC_BASE_URL': RELAY,
            'CLAUDE_CODE_USE_VERTEX': '0',
            'CLAUDE_CODE_USE_BEDROCK': '0',
            'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
            'CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY': '1',
            'CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS': str(concurrency),
            'CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS': str(h['timeout_minutes'] * 60000),
            'DISABLE_AUTOUPDATER': '1',
            'ANTHROPIC_CUSTOM_HEADERS': 'x-shim-run-id: ${STRAT_RUN_ID}',
            'CLAUDE_CODE_ENABLE_TELEMETRY': '1',
            'CLAUDE_CODE_ENHANCED_TELEMETRY_BETA': '1',
            'OTEL_LOG_RAW_API_BODIES': 'file:/sandbox/workspace/evidence/api-dumps',
            'OTEL_METRICS_EXPORTER': 'none', 'OTEL_LOGS_EXPORTER': 'none', 'OTEL_TRACES_EXPORTER': 'none',
        })
        for key in ('ANTHROPIC_MODEL', 'CLAUDE_CODE_SUBAGENT_MODEL', 'ANTHROPIC_DEFAULT_OPUS_MODEL',
                    'ANTHROPIC_DEFAULT_SONNET_MODEL', 'ANTHROPIC_DEFAULT_HAIKU_MODEL', 'ANTHROPIC_DEFAULT_FABLE_MODEL'):
            sandbox[key] = model
        assert h['validation_loop']['max_iterations'] == 1
        # Fullsend executes this on the host, which does not run Claude.
        # The unchanged plugin's SessionStart and pre-launch guards check the
        # actual sandbox CLI; the diagnostic also checks that pinned image.
        h['validation_loop']['preflight_check'] = 'python3 -c "import jsonschema, yaml, certifi, diff_match_patch"'
        path.write_text(yaml.safe_dump(h, sort_keys=False))
    policy_file = fullsend / 'shared/policy.yaml'
    policy = yaml.safe_load(policy_file.read_text())
    # Both endpoint layers come from the named provider profiles. Removing
    # the production Jira entry also removes all opaque TLS bypasses.
    policy['network_policies'] = {}
    policy_file.write_text(yaml.safe_dump(policy, sort_keys=False))
    (fullsend / 'config.yaml').write_text('version: "1"\nruntime: claude\nagents: []\n')
    return {'model': model, 'effort': effort, 'concurrency': concurrency, 'relay': RELAY,
            'sandbox_image': image, 'providers': ['model-relay', 'local-jira'],
            'validation_iterations': 1, 'runtime': 'claude', 'agents': list(AGENTS)}


if __name__ == '__main__':
    target = Path(sys.argv[1]).resolve()
    report = configure(target, os.environ['WORKFLOW_SANDBOX_IMAGE'], os.environ['WORKFLOW_MODEL'],
                       os.environ['WORKFLOW_EFFORT'], int(os.environ['WORKFLOW_CONCURRENCY']))
    output = Path(os.environ['FULLSEND_CI_ARTIFACTS_DIR'])
    (output / 'integration.json').write_text(json.dumps(report, indent=2) + '\n')
    shutil.copytree(target / '.fullsend', output / 'harness-config',
                    ignore=shutil.ignore_patterns('.fullsend-cache', '__pycache__'))
