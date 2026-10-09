#!/usr/bin/env bash
set -Eeuo pipefail
source "$PWD/.fullsend/scripts/ci/ca-bundle.sh"
fullsend_prepare_ca_bundle /tmp/model-smoke-ca.pem
source "$PWD/.fullsend/scripts/ci/strategy-model.sh"
# Exactly one inference turn, no tools, issue writes or strategy skills.
exec fullsend-claude --max-turns 1 --tools '' <<'PROMPT'
Reply with exactly PINNED_MODEL_SMOKE_OK. Do not inspect files, run commands, use tools, contact Jira, or perform strategy work.
PROMPT
