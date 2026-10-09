#!/usr/bin/env bash
# Exercise the real native setup and selector without modifying Jira/results.
set -Eeuo pipefail
trap 'rm -f /tmp/gcp-key.json' EXIT
: "${VERTEX_CREDENTIALS_JSON:?}"
export GCP_SERVICE_ACCOUNT_KEY
if [[ "$VERTEX_CREDENTIALS_JSON" == *'{'* ]]; then
  GCP_SERVICE_ACCOUNT_KEY=$(printf '%s' "$VERTEX_CREDENTIALS_JSON" | base64 -w0)
else
  GCP_SERVICE_ACCOUNT_KEY="$VERTEX_CREDENTIALS_JSON"
fi
bash ci-scripts/setup-claude-ci.sh
chmod 0600 /tmp/gcp-key.json
bash ci-scripts/fullsend-source.sh
export SSL_CERT_FILE="$CI_PROJECT_DIR/.ci-ca-bundle.pem"
runuser -u claude-ci -- /home/claude-ci/.local/bin/claude --version
python3 target/scripts/list-rfe-ids.py --jql 'key = RHAIRFE-1' > fullsend-ci-artifacts/native-eligible.txt
# M6 processed this seed; native duplicate protection must now exclude it.
test ! -s fullsend-ci-artifacts/native-eligible.txt
python3 - <<'PY'
import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path('target/scripts').resolve()))
import jira_utils
identity=jira_utils.api_call(os.environ['JIRA_SERVER'],'/myself',os.environ['JIRA_USER'],os.environ['JIRA_TOKEN'])
assert (identity.get('name') or identity.get('accountId'))==os.environ['JIRA_USER']
assert jira_utils.ssl_ctx.check_hostname
Path('fullsend-ci-artifacts/native.json').write_text(json.dumps({'native_setup':True,'claude_installed':True,'jira_bot_matches':True,'processed_seed_excluded':True})+'\n')
PY
echo "M7_NATIVE_PASS job=$CI_JOB_ID runner_description=${CI_RUNNER_DESCRIPTION:-not-injected}"
