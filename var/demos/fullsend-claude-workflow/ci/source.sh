#!/usr/bin/env bash
# Clone the pinned public strat-creator fork for this job.
# Adapted from Breadboard var/demos/fullsend-entrypoint-poc/strategy-ci/source.sh.
set -Eeuo pipefail
: "${CI_PROJECT_DIR:?}" "${STRAT_CREATOR_REPO:?}" "${STRAT_CREATOR_BRANCH:?}" "${STRAT_CREATOR_SHA:?}"
cd "$CI_PROJECT_DIR"
# The runner's local-only GIT_SSL_CAINFO must not replace public root CAs.
system_ca=""
for candidate in /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt /etc/ssl/cert.pem; do
  if [[ -r "$candidate" ]]; then system_ca="$candidate"; break; fi
done
[[ -n "$system_ca" ]] || { echo "No system public CA bundle" >&2; exit 1; }
cat "$system_ca" /etc/gitlab-runner/certs/ca.crt > "$CI_PROJECT_DIR/.ci-ca-bundle.pem"
export GIT_SSL_CAINFO="$CI_PROJECT_DIR/.ci-ca-bundle.pem"
git clone --single-branch --branch "$STRAT_CREATOR_BRANCH" "$STRAT_CREATOR_REPO" target
git -C target checkout --quiet --detach "$STRAT_CREATOR_SHA"
actual=$(git -C target rev-parse HEAD)
[[ "$actual" == "$STRAT_CREATOR_SHA" ]] || { echo "Unexpected strategy source revision: $actual" >&2; exit 1; }
mkdir -p fullsend-ci-artifacts
python3 - "$actual" <<'SOURCE'
import json, os, sys
from pathlib import Path
Path('fullsend-ci-artifacts/source.json').write_text(json.dumps({
    "repo": os.environ['STRAT_CREATOR_REPO'],
    "branch": os.environ['STRAT_CREATOR_BRANCH'],
    "sha": sys.argv[1]}, indent=2) + '\n')
SOURCE
echo "strat-creator source pinned at $actual"
