"""Architecture-context fetch inside the strategy sandbox; no model or writes.

Runs the pinned fetch script in a temporary directory, checks the sparse clone
and the selected version, and probes that push and other repositories' fetches
stay denied. Records statuses, names and sandbox decisions; no credentials.
"""
import json
import os
import re
import shutil
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

root = Path.cwd()
out = Path(os.environ['FULLSEND_OUTPUT_DIR'])
out.mkdir(parents=True, exist_ok=True)
work = Path(tempfile.mkdtemp(prefix='architecture-fetch.', dir='/tmp'))
started = time.monotonic()
fetch = subprocess.run(['timeout', '180', 'bash', str(root / 'scripts/fetch-architecture-context.sh')],
                       cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
(out / 'architecture-fetch.log').write_text(fetch.stdout)
print(fetch.stdout, end='', flush=True)
ctx = work / '.context/architecture-context'


def git(*args):
    return subprocess.run(['git', '-C', str(ctx), *args], capture_output=True, text=True).stdout.strip()


def files(path):
    return sorted(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else []


def version_directories(path):
    # Cone mode retains parent-level symlinks, including early-access -> latest.
    # Count materialized directories rather than aliases to the same checkout.
    return sorted(p.name for p in path.iterdir() if p.is_dir() and not p.is_symlink()) if path.is_dir() else []


latest = (ctx / 'LATEST_VERSION').read_text().strip() if (ctx / 'LATEST_VERSION').is_file() else ''
tree_versions = sorted(name.rsplit('/', 1)[-1] for name in git('ls-tree', '--name-only', 'HEAD', 'architecture/').splitlines()
                       if name.rsplit('/', 1)[-1].startswith('rhoai-'))
documents = files(ctx / 'architecture' / latest) if latest else []
overlays = files(ctx / 'overlays')
report = {
    'fetch_exit': fetch.returncode,
    'fetch_seconds': round(time.monotonic() - started, 1),
    'head': git('rev-parse', 'HEAD'),
    'latest_version': latest,
    'newest_version_in_tree': tree_versions[-1] if tree_versions else '',
    'checked_out_versions': version_directories(ctx / 'architecture'),
    'version_aliases': {p.name: os.readlink(p) for p in (ctx / 'architecture').iterdir() if p.is_symlink()} if (ctx / 'architecture').is_dir() else {},
    'sparse_paths': git('sparse-checkout', 'list').splitlines(),
    'partial_clone_filter': git('config', 'remote.origin.partialclonefilter'),
    'shallow': (ctx / '.git/shallow').is_file(),
    'document_files': len(documents),
    'document_bytes': sum(p.stat().st_size for p in documents),
    'sample_documents': [str(p.relative_to(ctx)) for p in documents[:5]],
    'overlay_files': len(overlays),
    'overlay_bytes': sum(p.stat().st_size for p in overlays),
}
context = ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE'))
for name, path in {'receive_pack_post': '/opendatahub-io/architecture-context/git-receive-pack',
                   'other_repo_upload_pack_post': '/opendatahub-io/opendatahub-operator/git-upload-pack'}.items():
    request = urllib.request.Request('https://github.com' + path, data=b'0000', method='POST',
                                     headers={'Content-Type': 'application/x-git-%s-request' % path.rsplit('/git-', 1)[1]})
    try:
        with urllib.request.urlopen(request, timeout=15, context=context) as response:
            report[name] = response.status
    except urllib.error.HTTPError as error:
        report[name] = error.code
    except Exception as error:
        report[name] = type(error).__name__
# Sandbox L7 decisions for github.com: method, path, verdict only.
decisions = []
for log in sorted(Path('/var/log').glob('openshell.*.log')):
    for line in log.read_text(errors='replace').splitlines():
        match = re.search(r'OCSF HTTP:\w+ \[\w+\] (ALLOWED|DENIED) (\w+) http://(github\.com|api\.github\.com):443(/[^ ?]*)', line)
        if match:
            decisions.append(' '.join(match.groups()))
report['sandbox_decisions'] = decisions
shutil.rmtree(work, ignore_errors=True)
(out / 'architecture-fetch.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
assert report['fetch_exit'] == 0, 'fetch failed'
assert re.fullmatch(r'rhoai-[\w.-]+', latest) and latest == report['newest_version_in_tree'], 'unexpected LATEST_VERSION'
assert report['checked_out_versions'] == [latest], 'sparse checkout selected other versions'
assert set(report['sparse_paths']) == {'architecture/' + latest, 'overlays'}, 'unexpected sparse paths'
assert report['partial_clone_filter'] == 'blob:none' and report['shallow'], 'not a filtered shallow clone'
assert report['document_files'] and report['document_bytes'], 'architecture documents missing'
assert report['overlay_files'] and report['overlay_bytes'], 'overlays missing'
assert report['receive_pack_post'] == 403 and report['other_repo_upload_pack_post'] == 403, 'policy permits more than the context fetch'
print('ARCHITECTURE_FETCH_PASS', latest, flush=True)
