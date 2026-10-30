#!/usr/bin/env bash
set -Eeuo pipefail
MODE="${1:?}"
python3 "$CI_SCRIPTS/workflow-configure.py" "$TARGET"
cd "$TARGET"
# Register through the released CLI, without committing installer-owned config.
for agent in strat-single strat-batch strat-resume; do
  fullsend agent add "$agent/$agent.yaml" --fullsend-dir "$TARGET/.fullsend" --name "$agent"
done
fullsend agent list --fullsend-dir "$TARGET/.fullsend" >"$FULLSEND_CI_ARTIFACTS_DIR/agents.txt"
fullsend lock strat-single --fullsend-dir "$TARGET/.fullsend" --offline
fullsend lock strat-batch --fullsend-dir "$TARGET/.fullsend" --offline
cp "$TARGET/.fullsend/config.yaml" "$FULLSEND_CI_ARTIFACTS_DIR/harness-config/config.yaml"
python3 -c 'import jsonschema, yaml, certifi, diff_match_patch'
if [[ "$MODE" == preflight ]]; then
  bash "$CI_SCRIPTS/workflow-preflight.sh"
else
  # Retain the sandbox until the gateway wrapper collects raw evidence, then
  # destroy all job-owned state. This is not a workflow entrypoint override.
  fullsend run "$MODE" --fullsend-dir "$TARGET/.fullsend" --target-repo "$TARGET" \
    --output-dir "$RUN_OUTPUT" --keep-sandbox --debug=api,hooks
fi
