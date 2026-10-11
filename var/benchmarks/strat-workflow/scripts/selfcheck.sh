#!/bin/bash
# Wiring check for script-entrypoint jobs. Confirms that the job's setup
# reached the script: relay routing, model pinning, MLflow hooks, OTel, API
# dumps, strace, the artifact directory and access to the GitHub emulator.
# Makes no model call unless --call-model is given.
#
#   selfcheck.sh [--call-model]

set -uo pipefail

CALL_MODEL=""
[ "${1:-}" = "--call-model" ] && CALL_MODEL=1

FAILED=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; FAILED=1; }
check() {  # check <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then pass "$desc"; else fail "$desc"; fi
}

echo "=== selfcheck: script-entrypoint job wiring ==="

check "ANTHROPIC_VERTEX_BASE_URL points at Model Relay" \
  bash -c '[[ "${ANTHROPIC_VERTEX_BASE_URL:-}" == *model-relay* ]]'
check "GOOGLE_CLOUD_PROJECT matches ANTHROPIC_VERTEX_PROJECT_ID" \
  bash -c '[ -n "${GOOGLE_CLOUD_PROJECT:-}" ] && [ "$GOOGLE_CLOUD_PROJECT" = "${ANTHROPIC_VERTEX_PROJECT_ID:-}" ]'
check "relay inference port answers" \
  bash -c 'curl -fsS --max-time 5 "${ANTHROPIC_VERTEX_BASE_URL%/v1}/health"'

check "ANTHROPIC_MODEL set (${ANTHROPIC_MODEL:-unset})" bash -c '[ -n "${ANTHROPIC_MODEL:-}" ]'
if [[ "${ANTHROPIC_MODEL:-}" == claude-* || "${ANTHROPIC_MODEL:-}" == */* ]]; then
  check "subagent model and aliases pinned to $ANTHROPIC_MODEL" bash -c '
    m="$ANTHROPIC_MODEL"
    for v in CLAUDE_CODE_SUBAGENT_MODEL ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL ANTHROPIC_DEFAULT_HAIKU_MODEL; do
      [ "${!v:-}" = "$m" ] || exit 1
    done'
fi

check "MLflow experiment set (${MLFLOW_EXPERIMENT_NAME:-unset})" bash -c '[ -n "${MLFLOW_EXPERIMENT_NAME:-}" ]'
check "MLflow hooks in ~/.claude/settings.json" \
  python3 -c 'import json,os,sys; s=json.load(open(os.path.expanduser("~/.claude/settings.json"))); sys.exit(0 if "mlflow" in json.dumps(s.get("hooks",{})).lower() else 1)'
check "Vertex provider in ~/.claude/settings.json" \
  python3 -c 'import json,os,sys; s=json.load(open(os.path.expanduser("~/.claude/settings.json"))); sys.exit(0 if s.get("apiProvider")=="vertex" else 1)'

if [ "${ENABLE_OTEL:-1}" = "1" ]; then
  check "OTel exporter points at Observatory" bash -c '[[ "${OTEL_EXPORTER_OTLP_ENDPOINT:-}" == *observatory* ]]'
  check "API body dump directory exists" bash -c 'd="${OTEL_LOG_RAW_API_BODIES#file:}"; [ -d "$d" ]'
fi

if [ "${ENABLE_STRACE:-}" = "1" ]; then
  check "running under strace" bash -c 'grep -q "^TracerPid:[[:space:]]*[1-9]" /proc/$$/status'
fi

check "artifact directory writable (${JOB_ARTIFACT_DIR:-unset})" \
  bash -c 'touch "$JOB_ARTIFACT_DIR/.selfcheck" && rm -f "$JOB_ARTIFACT_DIR/.selfcheck"'
check "GitHub emulator reachable (strat-creator)" \
  git ls-remote --exit-code https://github.local/opendatahub-io/strat-creator.git HEAD
check "claude CLI present ($(claude --version 2>/dev/null || echo missing))" claude --version

if [ -n "$CALL_MODEL" ]; then
  reply="$(claude -p "Reply with exactly: selfcheck ok" 2>&1 | tail -1)"
  if [[ "$reply" == *"selfcheck ok"* ]]; then pass "model call through the relay"; else fail "model call through the relay: $reply"; fi
fi

{
  echo "{"
  echo "  \"job\": \"${PIPELINE_JOB_NAME:-}\","
  echo "  \"model\": \"${ANTHROPIC_MODEL:-}\","
  echo "  \"mlflow_experiment\": \"${MLFLOW_EXPERIMENT_NAME:-}\","
  echo "  \"passed\": $([ "$FAILED" = 0 ] && echo true || echo false)"
  echo "}"
} > "${JOB_ARTIFACT_DIR:-/tmp}/selfcheck.json"

echo "=== selfcheck: $([ "$FAILED" = 0 ] && echo PASSED || echo FAILED) ==="
exit "$FAILED"
