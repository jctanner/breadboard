#!/usr/bin/env bash
# Live Jira locks and no-work/failure behavior, with no inference or publication.
set -Eeuo pipefail
root="$PWD"
source "$root/.fullsend/scripts/ci/ca-bundle.sh"
fullsend_prepare_ca_bundle /tmp/batch-controls-ca.pem
export STRAT_CREATOR_ROOT="$root" BATCH_SIZE=0 BATCH_OFFSET=0 BATCH_EXPECTED_KEYS=''
bash "$root/.fullsend/scripts/strategy-entrypoint.sh" batch-discover
[[ ! -e "$root/artifacts/locked-rfe-ids.txt" ]]
echo M8_EMPTY_BATCH_PASS
wrapper="$root/.fullsend/scripts/ci/run-claude.sh"
cp "$wrapper" /tmp/m8-run-claude-original.sh
trap 'cp /tmp/m8-run-claude-original.sh "$wrapper"' EXIT
printf '#!/usr/bin/env bash\necho M8_CONTROLLED_PHASE_FAILURE >&2\nexit 37\n' > "$wrapper"
export BATCH_SIZE=1 BATCH_EXPECTED_KEYS="${M8_CONTROL_RFE:?}"
set +e
bash "$root/.fullsend/scripts/strategy-entrypoint.sh" batch-discover
rc=$?
set -e
[[ "$rc" -eq 37 ]]
[[ ! -e "$root/artifacts/locked-rfe-ids.txt" ]]
python3 - <<'PY'
import os,sys
sys.path.insert(0,'scripts')
from jira_utils import get_issue,require_env
f=get_issue(*require_env(),os.environ['M8_CONTROL_RFE'],fields=['labels','issuelinks','attachment'])['fields']
assert 'strat-creator-processing' not in f['labels']
assert not f.get('issuelinks') and not f.get('attachment')
print('M8_FAILURE_37_UNLOCKED_NO_JIRA_STRATEGY_PASS')
PY
