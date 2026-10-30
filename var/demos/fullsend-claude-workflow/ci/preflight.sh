#!/usr/bin/env bash
# Real sandbox/provider checks. No fullsend run, Jira mutations or inference.
set -Eeuo pipefail
NAME="wf-pre-$CI_JOB_ID"
for profile in model-relay local-jira; do
  openshell provider profile import --file "$TARGET/.fullsend/profiles/$profile.yaml"
done
# Bare-key arguments keep credential values out of process arguments.
ANTHROPIC_API_KEY="$MODEL_RELAY_API_KEY" openshell provider create \
  --name model-relay --type local-model-relay --credential ANTHROPIC_API_KEY
openshell provider create --name local-jira --type local-strategy-jira --credential JIRA_TOKEN
openshell sandbox create --name "$NAME" --keep --no-auto-providers --no-tty \
  --from "$WORKFLOW_SANDBOX_IMAGE" --policy "$TARGET/.fullsend/shared/policy.yaml" \
  --provider model-relay --provider local-jira --detach -- /bin/sleep infinity
openshell sandbox upload "$NAME" "$CI_SCRIPTS/workflow-probe.py" /sandbox/workspace/
openshell sandbox upload "$NAME" "$TARGET/scripts/check_claude_runtime.py" /sandbox/workspace/
# The non-secret Jira username is used for its normal Basic authentication.
openshell sandbox exec --name "$NAME" --no-tty -- \
  python3 /sandbox/workspace/workflow-probe.py "$JIRA_SERVER" "$JIRA_USER" "$WORKFLOW_MODEL" \
  | tee "$FULLSEND_CI_ARTIFACTS_DIR/preflight.json"
