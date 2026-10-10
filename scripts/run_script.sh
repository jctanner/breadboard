#!/bin/bash
# K8s job wrapper for script-entrypoint jobs: the usual job setup (Vertex via
# Model Relay, MLflow tracing, OTel, API dumps, strace), then a script instead
# of a single `claude -p`. Every claude the script starts inherits the setup.
#
# Usage:
#   run_script.sh --path var/benchmarks/<name>/scripts/x.sh [--model M] [--issue K] -- [args...]
#   run_script.sh --repo https://host/owner/repo --ref <40-char sha> --path dir/x.sh ... -- [args...]
#
# Without --repo the script comes from the image (/app/<path>, under
# var/benchmarks/). With --repo/--ref the repository is cloned at that exact
# commit and the script runs from the clone. The dashboard validates both
# (src/dashboard/job_scripts.py); this wrapper checks them again.

set -euo pipefail

export PATH="/app/.venv/bin:/app/scripts/job-bin:${PATH}"

LOG_DIR="/app/artifacts/jobs"
mkdir -p "$LOG_DIR" 2>/dev/null || true
LOG_FILE="${PIPELINE_LOG_FILE:-${LOG_DIR}/${PIPELINE_JOB_NAME:-$(hostname)}.log}"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
exec > >(tee -a "$LOG_FILE") 2>&1

PIPELINE_TMP_DIR="/app/tmp"
if ! mkdir -p "$PIPELINE_TMP_DIR" 2>/dev/null; then
  PIPELINE_TMP_DIR="/tmp/pipeline-tmp"
  mkdir -p "$PIPELINE_TMP_DIR"
fi
export PIPELINE_TMP_DIR

SCRIPT_PATH=""
REPO=""
REF=""
MODEL=""
ISSUE_KEY=""
SCRIPT_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --path) SCRIPT_PATH="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --ref) REF="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --issue) ISSUE_KEY="$2"; shift 2 ;;
    --) shift; SCRIPT_ARGS=("$@"); break ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$SCRIPT_PATH" ]; then
  echo "Usage: $0 --path <path> [--repo URL --ref SHA] [--model M] [--issue K] -- [args...]" >&2
  exit 2
fi
case "$SCRIPT_PATH" in
  /*|*..*) echo "ERROR: script path must be relative without '..': $SCRIPT_PATH" >&2; exit 2 ;;
esac
if [ -n "$REPO" ] || [ -n "$REF" ]; then
  if [[ ! "$REF" =~ ^[0-9a-f]{40}$ ]] || [[ ! "$REPO" =~ ^https:// ]]; then
    echo "ERROR: --repo must be an https URL and --ref a full 40-character commit" >&2
    exit 2
  fi
elif [[ "$SCRIPT_PATH" != var/benchmarks/* ]]; then
  echo "ERROR: an image script must be under var/benchmarks/" >&2
  exit 2
fi

JOB_TAG="${PIPELINE_JOB_NAME:-$(hostname)}"

echo "============================================================"
echo "Running script: $SCRIPT_PATH"
[ -n "$REPO" ] && echo "From: $REPO @ $REF"
echo "Args: ${SCRIPT_ARGS[*]:-(none)}"
echo "Issue: ${ISSUE_KEY:-(none)}"
echo "Model: ${MODEL:-(default)}"
echo "============================================================"
echo

echo "=== Environment ==="
env | sort
echo "=== End environment ==="
echo

# shellcheck source=lib/job_setup.sh
source /app/scripts/lib/job_setup.sh

job_setup_ca
job_setup_claude_settings
job_setup_mlflow
job_setup_shared_links
job_setup_model_env "$MODEL"
job_setup_otel
job_setup_strace
echo

# Resolve the script: from the image, or from a clone at the pinned commit.
if [ -n "$REPO" ]; then
  SCRIPT_ROOT="$PIPELINE_TMP_DIR/script-src/$JOB_TAG"
  echo "Cloning $REPO at $REF..."
  rm -rf "$SCRIPT_ROOT"
  git init -q "$SCRIPT_ROOT"
  git -C "$SCRIPT_ROOT" fetch -q --depth 1 "$REPO" "$REF"
  git -C "$SCRIPT_ROOT" -c advice.detachedHead=false checkout -q FETCH_HEAD
  if [ "$(git -C "$SCRIPT_ROOT" rev-parse HEAD)" != "$REF" ]; then
    echo "ERROR: clone of $REPO is not at $REF" >&2
    exit 1
  fi
  echo "✓ Clone at $REF"
else
  SCRIPT_ROOT="/app"
fi
SCRIPT_FILE="$(realpath -e "$SCRIPT_ROOT/$SCRIPT_PATH" 2>/dev/null || true)"
if [ -z "$SCRIPT_FILE" ] || [ ! -f "$SCRIPT_FILE" ]; then
  echo "ERROR: script not found: $SCRIPT_ROOT/$SCRIPT_PATH" >&2
  exit 1
fi
case "$SCRIPT_FILE" in
  "$(realpath "$SCRIPT_ROOT")"/*) ;;
  *) echo "ERROR: script resolves outside $SCRIPT_ROOT: $SCRIPT_FILE" >&2; exit 1 ;;
esac

# What the script can rely on.
JOB_ARTIFACT_DIR="/app/artifacts/scripts/$JOB_TAG"
mkdir -p "$JOB_ARTIFACT_DIR"
export SCRIPT_ROOT JOB_ARTIFACT_DIR ISSUE_KEY
export PIPELINE_MODEL="$MODEL"
export PIPELINE_JOB_NAME="$JOB_TAG"
# Entrypoints written for fullsend expect an output directory from their
# harness; give them one in the job's artifacts unless the job sets it.
export FULLSEND_OUTPUT_DIR="${FULLSEND_OUTPUT_DIR:-$JOB_ARTIFACT_DIR/output}"
mkdir -p "$FULLSEND_OUTPUT_DIR"

case "$SCRIPT_FILE" in
  *.sh) RUNNER=(bash "$SCRIPT_FILE") ;;
  *.py) RUNNER=(python3 "$SCRIPT_FILE") ;;
  *)
    if [ ! -x "$SCRIPT_FILE" ]; then
      echo "ERROR: $SCRIPT_FILE is neither .sh, .py nor executable" >&2
      exit 1
    fi
    RUNNER=("$SCRIPT_FILE")
    ;;
esac

echo "Working directory: $SCRIPT_ROOT"
echo "Artifacts: $JOB_ARTIFACT_DIR"
echo "Starting script at: $(date)"
echo
cd "$SCRIPT_ROOT"
set +e
"${STRACE_CMD[@]}" "${RUNNER[@]}" "${SCRIPT_ARGS[@]}"
EXIT_CODE=$?
set -e

echo
echo "Script finished at: $(date)"
echo "Exit code: $EXIT_CODE"
echo
echo "============================================================"
echo "Script execution complete"
echo "============================================================"

exit "$EXIT_CODE"
