#!/bin/bash
# Shared setup for pipeline-agent job wrappers. Source this file; each
# function configures one part of the environment that every `claude` the job
# starts inherits. Blocks are taken from run_skill.sh, which still carries its
# own copies; moving it onto these functions is a follow-up.

# Custom CA bundle for every tool (emulators use Breadboard's internal CA).
job_setup_ca() {
  if [ -f /shared/ca-certificates.crt ]; then
    export SSL_CERT_FILE=/shared/ca-certificates.crt
    export REQUESTS_CA_BUNDLE=/shared/ca-certificates.crt
    export NODE_EXTRA_CA_CERTS=/shared/ca-certificates.crt
    export GIT_SSL_CAINFO=/shared/ca-certificates.crt
    echo "✓ Using custom CA certificate bundle"
  fi
  git config --global url."https://github.com/".insteadOf "git@github.com:"
}

# Vertex provider settings and the optional Atlassian MCP server in
# ~/.claude/settings.json. Sets CLAUDE_SETTINGS_FILE.
job_setup_claude_settings() {
  CLAUDE_SETTINGS_FILE="$HOME/.claude/settings.json"
  export CLAUDE_SETTINGS_FILE
  echo "Configuring Claude CLI for Vertex AI..."
  python3 -c "
import json
import os

settings_file = os.path.expanduser('~/.claude/settings.json')
os.makedirs(os.path.dirname(settings_file), exist_ok=True)
settings = {}
if os.path.exists(settings_file):
    with open(settings_file, 'r') as f:
        settings = json.load(f)

settings['apiProvider'] = 'vertex'
settings['vertexProjectId'] = os.environ.get('ANTHROPIC_VERTEX_PROJECT_ID', '')
settings['vertexRegion'] = os.environ.get('CLOUD_ML_REGION', 'global')

atlassian_mcp_url = os.environ.get('ATLASSIAN_MCP_URL', '')
if atlassian_mcp_url:
    settings.setdefault('mcpServers', {})['atlassian'] = {'type': 'sse', 'url': atlassian_mcp_url}
    print('✓ Atlassian MCP server configured')

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
print('✓ Vertex AI settings merged')
"
}

# MLflow tracing hooks for every claude CLI session the job starts.
job_setup_mlflow() {
  if [ -z "${MLFLOW_TRACKING_URI:-}" ]; then
    echo "⚠ MLFLOW_TRACKING_URI not set, skipping MLflow tracing setup"
    return 0
  fi
  echo "Configuring MLflow tracing for Claude CLI..."
  local autolog_args=(-u "$MLFLOW_TRACKING_URI" -d "${MLFLOW_CLAUDE_HOME:-/home/pipelineagent}")
  if [ -n "${MLFLOW_EXPERIMENT_NAME:-}" ]; then
    autolog_args+=(-n "$MLFLOW_EXPERIMENT_NAME")
  fi
  /app/.venv/bin/mlflow autolog claude "${autolog_args[@]}"
  /app/.venv/bin/python /app/scripts/bound_mlflow_claude_hooks.py "$CLAUDE_SETTINGS_FILE"
  echo "✓ MLflow tracing configured (experiment: ${MLFLOW_EXPERIMENT_NAME:-default})"
}

# Point common fallback working directories at the shared volumes, so
# relative writes such as artifacts/... land on the PVC.
job_setup_shared_links() {
  local base
  for base in "/home/pipelineagent" "$HOME"; do
    [ -n "$base" ] || continue
    mkdir -p "$base" 2>/dev/null || true
    local name
    for name in artifacts tmp .context; do
      local target="/app/$name"
      [ "$name" = "tmp" ] && target="$PIPELINE_TMP_DIR"
      local link="$base/$name"
      if [ -L "$link" ]; then
        ln -sfn "$target" "$link"
      elif [ ! -e "$link" ]; then
        ln -s "$target" "$link" 2>/dev/null || true
      else
        echo "WARNING: $link exists and is not a symlink; leaving it unchanged"
      fi
    done
  done
}

# Model for every claude the job starts. A full model ID (claude-...) also
# pins the subagent model and every alias, so helper agents and background
# requests use the same model; an alias (opus, sonnet, haiku) only sets the
# main model.
job_setup_model_env() {
  local model="$1"
  [ -n "$model" ] || return 0
  export ANTHROPIC_MODEL="$model"
  if [[ "$model" == claude-* ]]; then
    export CLAUDE_CODE_SUBAGENT_MODEL="$model"
    export ANTHROPIC_DEFAULT_OPUS_MODEL="$model"
    export ANTHROPIC_DEFAULT_SONNET_MODEL="$model"
    export ANTHROPIC_DEFAULT_HAIKU_MODEL="$model"
    export ANTHROPIC_DEFAULT_FABLE_MODEL="$model"
    echo "✓ Model pinned for sessions, subagents and aliases: $model"
  else
    echo "✓ Model alias for sessions: $model"
  fi
}

# OpenTelemetry to Observatory and raw API body dumps (enabled by default).
job_setup_otel() {
  if [ "${ENABLE_OTEL:-1}" != "1" ]; then
    echo "OTel telemetry disabled"
    return 0
  fi
  local job_tag="${PIPELINE_JOB_NAME:-$(hostname)}"
  local apibodies_dir="/app/artifacts/apibodies/${job_tag}"
  mkdir -p "$apibodies_dir"
  local observatory_url="${OBSERVATORY_URL:-http://observatory.ai-pipeline.svc.cluster.local:8000}"
  export CLAUDE_CODE_ENABLE_TELEMETRY=1
  export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
  export OTEL_EXPORTER_OTLP_PROTOCOL=http/json
  export OTEL_EXPORTER_OTLP_ENDPOINT="${observatory_url}/otel"
  export OTEL_METRICS_EXPORTER=otlp
  export OTEL_LOGS_EXPORTER=otlp
  export OTEL_TRACES_EXPORTER=otlp
  export OTEL_LOG_USER_PROMPTS=1
  export OTEL_LOG_TOOL_DETAILS=1
  export OTEL_LOG_TOOL_CONTENT=1
  export OTEL_LOG_RAW_API_BODIES="file:${apibodies_dir}"
  export OTEL_METRIC_EXPORT_INTERVAL=10000
  export OTEL_LOGS_EXPORT_INTERVAL=5000
  export OTEL_TRACES_EXPORT_INTERVAL=5000
  echo "OTel telemetry enabled: OTLP → ${observatory_url}/otel, API bodies → $apibodies_dir"
}

# Optional strace wrapper; -f follows every process the command starts.
# Sets the STRACE_CMD array (empty when strace is off).
job_setup_strace() {
  STRACE_CMD=()
  if [ "${ENABLE_STRACE:-}" = "1" ]; then
    local job_tag="${PIPELINE_JOB_NAME:-$(hostname)}"
    local strace_dir="/app/artifacts/strace/${job_tag}"
    mkdir -p "$strace_dir"
    STRACE_CMD=(strace -ffttv -s 1024 -o "${strace_dir}/${job_tag}")
    echo "strace enabled: output → $strace_dir"
  fi
}
