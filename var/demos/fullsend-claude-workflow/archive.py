#!/usr/bin/env python3
"""Archive a terminal GitLab integration run privately, with checksum verification.

Reuse the benchmark collector for online SQLite backups and paginated relay
events. Never overwrite a previous capture. A failed run is still archived.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import zipfile

from publish import api, client

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BENCH = ROOT / 'var/benchmarks/strat-workflow/scripts/archive_run.py'
spec = importlib.util.spec_from_file_location('strat_archive', BENCH)
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


def download(c, path, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with c.stream('GET', path, timeout=600) as response:
        if not response.is_success:
            raise RuntimeError(f'archive download HTTP {response.status_code}')
        with destination.open('xb') as output:
            for chunk in response.iter_bytes():
                output.write(chunk)


def unpack(source, target):
    with zipfile.ZipFile(source) as z:
        for member in z.infolist():
            path = Path(member.filename)
            if path.is_absolute() or '..' in path.parts or stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError('unsafe CI artifact path')
            if member.is_dir():
                continue
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with z.open(member) as data, destination.open('xb') as output:
                shutil.copyfileobj(data, output)


def collect_jobs(c, collector, capture, project, pipeline, relative):
    jobs = api(c, 'GET', f'/projects/{project}/pipelines/{pipeline}/jobs',
               params={'per_page': 100, 'include_retried': 'true'})
    collector.save(relative + '/jobs.json', jobs)
    for job in jobs:
        identity = f'{relative}/jobs/{job["id"]}'
        collector.source(f'project {project} job {job["id"]} trace', lambda job=job, identity=identity:
            download(c, f'/projects/{project}/jobs/{job["id"]}/trace', capture / identity / 'trace.log'))
        if job.get('artifacts_file') or job.get('artifacts'):
            def artifacts(job=job, identity=identity):
                destination = capture / identity / 'artifacts.zip'
                download(c, f'/projects/{project}/jobs/{job["id"]}/artifacts', destination)
                unpack(destination, capture / identity / 'artifacts')
            collector.source(f'project {project} job {job["id"]} artifacts', artifacts)
        elif job['name'] in ('strat-single', 'strat-batch', 'workflow-preflight') and job['status'] != 'skipped':
            def missing_artifacts():
                raise RuntimeError('Required native job artifacts were not uploaded; traces alone are incomplete')
            collector.source(f'project {project} job {job["id"]} required artifacts', missing_artifacts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pipeline', type=int)
    parser.add_argument('--root', type=Path, default=ROOT / 'var/run-data/fullsend-claude-workflow')
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--context', type=Path, action='append', default=[],
                        help='Additional run receipts or launch source to retain privately')
    args = parser.parse_args()
    if args.verify:
        result = archive.verify(args.verify)
        print(json.dumps(result, indent=2))
        return 0 if result['ok'] else 1
    if not args.pipeline or args.pipeline < 1:
        parser.error('--pipeline is required')
    os.umask(0o077)
    capture = args.root / f'gitlab-pipeline-{args.pipeline}' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    capture.mkdir(parents=True, exist_ok=False)
    collector = archive.Collector(capture, 'ai-pipeline')
    with client() as c:
        prefix = f'/projects/7/pipelines/{args.pipeline}'
        pipeline = api(c, 'GET', prefix)
        if pipeline['status'] not in ('success', 'failed', 'canceled', 'skipped'):
            raise RuntimeError('Pipeline must be terminal before final archival')
        collector.save('gitlab/pipeline.json', pipeline)
        bridges = api(c, 'GET', prefix + '/bridges', params={'per_page': 100})
        collector.save('gitlab/bridges.json', bridges)
        collector.source('exact CI source', lambda: download(c,
            '/projects/7/repository/archive.tar.gz?sha=' + pipeline['sha'],
            capture / 'context/ci-source.tar.gz'))
        collect_jobs(c, collector, capture, 7, args.pipeline, 'gitlab')
        for bridge in bridges:
            child = bridge.get('downstream_pipeline')
            if not child:
                continue
            # The fixture's sole downstream is strat-dashboard, project 9.
            # The emulator omits project_id from its bridge summary.
            project = child.get('project_id', 9)
            if project != 9:
                raise RuntimeError('Unexpected downstream project; inspect before collection')
            relative = f'gitlab/downstream/{project}-{child["id"]}'
            child_pipeline = api(c, 'GET', f'/projects/{project}/pipelines/{child["id"]}')
            collector.save(relative + '/pipeline.json', child_pipeline)
            if child_pipeline['status'] not in ('success', 'failed', 'canceled', 'skipped'):
                raise RuntimeError('Downstream dashboard pipeline must also be terminal')
            collect_jobs(c, collector, capture, project, child['id'], relative)
            collector.source('dashboard CI source', lambda project=project, child_pipeline=child_pipeline, relative=relative:
                download(c, f'/projects/{project}/repository/archive.tar.gz?sha=' + child_pipeline['sha'],
                         capture / relative / 'source.tar.gz'))
        results = api(c, 'GET', '/projects/8/repository/branches/main')
        collector.save('gitlab/results-head.json', results)
    for file in args.context:
        collector.source('run context ' + file.name,
                         lambda file=file: shutil.copyfile(file, capture / 'context' / file.name))
    for file in ('/tmp/fullsend-workflow-publish.json', '/tmp/fullsend-workflow-preflight.json'):
        p = Path(file)
        if p.is_file():
            collector.save('context/' + p.name, json.loads(p.read_text()))
    shutil.copytree(HERE, capture / 'context/fixture', ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    collector.save('context/fixture-scope.json', {
        'fixture': 'Capture-time helper source; may be newer than the run.',
        'ci-source.tar.gz': 'The exact CI repository at the pipeline commit.',
    })
    collector.source('pinned candidate source', lambda: collector.command(['git', '-C',
        str(ROOT / 'checkouts.tmp/jctanner-fullsend-ai/strat-creator'), 'archive', '--format=tar.gz',
        '6ed858b2294a29457153a90f187a801022c21e8b'], 'context/strat-creator.tar.gz'))
    for deployment, database in (('jira-emulator', '/data/jira.db'), ('mlflow', '/data/mlflow.db'),
                                 ('observatory', '/data/observatory.db'), ('gitlab-emulator', '/data/gitlab_emulator.db')):
        collector.source(deployment + ' database', lambda deployment=deployment, database=database:
            collector.tar(deployment, 'database', [database, '[]'], f'system-state/{deployment}.tar.gz'))
    collector.source('readable Jira export', lambda: collector.remote('pipeline-dashboard', 'jira', relative='jira/issues.json'))
    for deployment in ('gitlab-emulator', 'model-relay', 'jira-emulator', 'observatory', 'mlflow', 'markovd', 'pipeline-dashboard'):
        collector.source(deployment + ' logs', lambda deployment=deployment:
            collector.command(collector.kubectl('logs', 'deploy/' + deployment, '--all-containers=true',
                '--timestamps', '--since-time=' + pipeline['created_at']), f'logs/{deployment}.log'))
    collector.source('relay request lifecycle', lambda: collector.relay(pipeline['created_at']))
    collector.source('all ingress proxy replica logs', lambda:
        collector.command(collector.kubectl('logs', '-l', 'app=ingress-proxy',
            '--all-containers=true', '--prefix', '--timestamps', '--since-time=' + pipeline['created_at']),
            'logs/ingress-proxy-all-replicas.log'))
    collector.source('runner logs', lambda: collector.command(['kubectl', '-n', 'gitlab-runner', 'logs',
        'deploy/gitlab-runner', '--timestamps', '--since-time=' + pipeline['created_at']], 'logs/gitlab-runner.log'))
    collector.save('manifest.json', {'schema_version': 1, 'run_id': f'gitlab-pipeline-{args.pipeline}',
        'execution': 'gitlab-fullsend-openshell', 'final': True, 'complete': not collector.errors,
        'sources': collector.sources, 'errors': collector.errors, 'files': archive.manifest_files(capture),
        'scope': 'GitLab jobs and full native CI evidence; individually consistent shared-service SQLite backups; service logs and relay telemetry since pipeline creation',
        'limitations': ['Database backups are individually consistent, not one cross-service transaction.',
                        'No synthetic strace/API data is created when a run exits before Claude starts.']})
    result = archive.verify(capture)
    print(json.dumps({'archive': str(capture), 'complete': not collector.errors, 'verification': result}, indent=2))
    return 0 if result['ok'] and not collector.errors else 1


if __name__ == '__main__':
    sys.exit(main())
