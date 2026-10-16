#!/bin/bash
# Arm script for the Claude Workflow design (strat-creator PR #83).
#
#   run-workflow.sh RHAIRFE-N | batch-discover
#
# Runs the design as it is, with nothing between Claude and its output:
#   1. PR #83's pre-strategy.sh: clone and verify the pinned commit, load the
#      architecture context, lock the RFE, write tmp/strat-input.json
#      (exit 78: nothing to do). The design keeps this step outside the
#      Workflow; PR #80's entrypoint does the same work itself.
#   2. The Workflow, started directly as its slash command, once:
#        claude -p --plugin-dir .fullsend/plugins/strat-pipeline "/strat-pipeline:strat-pipeline"
#      No agent prompt around it and no retry: a failed step is a failure,
#      as for PR #80's entrypoint. Raw output goes, unprocessed, to files and
#      to the job log (tee).
#   3. PR #83's checker (validate-output.sh), as an observer, and its post
#      step (post-strategy.sh: hand-off, report, and a push to
#      RESULTS_REPO_URL when the job sets one, as PR #80 does) when the run
#      validated.
#   4. release-locks.sh, always.
#
# Environment (from the job; extra_env can override):
#   STRAT_CREATOR_REF   strat-creator commit (default: PR #83, 6b78355)
#   STRAT_CREATOR_REPO  default: github.local/opendatahub-io/strat-creator
#   STRAT_ARCHITECTURE_CONTEXT_PATH  pinned snapshot on the context volume
#   STRAT_DRY_RUN       1 for no Jira writes (default: real writes)
#   STRAT_EFFORT        claude --effort (default high, as PR #83 declares)
#   STRAT_TIMEOUT_MINUTES  default 90, as PR #83's strat-single declares
#   CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS  optional explicit Workflow
#                       agent cap; empty/unset uses Claude's CPU-derived default
#   STRAT_BG_WAIT_CEILING_MS  how long claude -p waits for the background
#                       Workflow after its last turn (default 30 minutes;
#                       Claude Code's own default is 10)
#   JIRA_SERVER, JIRA_USER, JIRA_TOKEN, ANTHROPIC_MODEL: set by the job
#
# Outputs in $JOB_ARTIFACT_DIR, with run-summary.json. Exit status: claude's
# when it failed, else the checker's, else the post step's.

set -uo pipefail
BENCH_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RFE_KEY="${1:-}"
if [ "$#" != 1 ]; then
  echo "usage: run-workflow.sh RHAIRFE-N | batch-discover" >&2
  exit 2
fi
if [ "$RFE_KEY" = batch-discover ]; then
  export STRAT_MODE=batch
elif [[ "$RFE_KEY" =~ ^RHAIRFE-[0-9]+$ ]]; then
  export STRAT_MODE=single
else
  echo "usage: run-workflow.sh RHAIRFE-N | batch-discover" >&2
  exit 2
fi
export RFE_KEY

export STRAT_CREATOR_REF="${STRAT_CREATOR_REF:-6b78355ebc450ff4737fd10ba4857c26086ceac0}"
export STRAT_CREATOR_REPO="${STRAT_CREATOR_REPO:-https://github.local/opendatahub-io/strat-creator.git}"
export STRAT_ARCHITECTURE_CONTEXT_PATH="${STRAT_ARCHITECTURE_CONTEXT_PATH:-/app/.context/snapshots/architecture-context/7d61f097a9220aeb1280837b66b532177ec558b6}"
export STRAT_DRY_RUN="${STRAT_DRY_RUN:-}"
export STRAT_RUN_ID="${STRAT_RUN_ID:-${PIPELINE_JOB_NAME:-run-$$}}"
TIMEOUT_MINUTES="${STRAT_TIMEOUT_MINUTES:-90}"
WORKFLOW_COMMAND="/strat-pipeline:strat-pipeline"
if [ -n "${CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS:-}" ]; then
  if [[ ! "$CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS" =~ ^[1-9][0-9]*$ ]]; then
    echo "ERROR: CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS must be a positive integer" >&2
    exit 2
  fi
else
  unset CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS
fi

OUT="${JOB_ARTIFACT_DIR:?run under run_script.sh (JOB_ARTIFACT_DIR unset)}"
WORK="${PIPELINE_TMP_DIR:-/tmp}/strat-workflow/${STRAT_RUN_ID}"
export TARGET_REPO_DIR="$WORK/repo"
export REPO_DIR="$TARGET_REPO_DIR"
export STRAT_STATE_DIR="$WORK/state"
export STRAT_PUBLISH_DIR="$OUT/publish"
unset ORG_PULSE_URL
SHARED="$STRAT_STATE_DIR/strat-creator/.fullsend/shared"
RUN_OUT="$OUT/workflow"

rm -rf "$WORK"
mkdir -p "$WORK" "$RUN_OUT/output"

PRE_RC=""
CLAUDE_RC=""
VALIDATE_RC=""
POST_RC=""
RELEASE_RC=""

finish() {
  local rc=$?
  trap - EXIT
  if [ -f "$SHARED/release-locks.sh" ]; then
    echo "=== release locks ==="
    bash "$SHARED/release-locks.sh" "$STRAT_STATE_DIR"
    RELEASE_RC=$?
  fi
  if [ -n "${STRAT_MIXED_SEED_JSON:-}" ] && [ "$PRE_RC" = 0 ]; then
    echo "=== mixed-state checks and model-free repeat preparation ==="
    python3 "$BENCH_SCRIPTS/mixed_state.py" finish "$STRAT_MIXED_SEED_JSON" \
      "$TARGET_REPO_DIR" "$STRAT_STATE_DIR" "$OUT" "$rc"
    local mixed_rc=$?
    if [ "$rc" = 0 ] && [ "$mixed_rc" != 0 ]; then rc=$mixed_rc; fi
  fi
  mkdir -p "$OUT/state"
  cp -f "$STRAT_STATE_DIR"/run.json "$STRAT_STATE_DIR"/owned-rfe-ids.txt* "$OUT/state/" 2>/dev/null || true
  [ -d "$TARGET_REPO_DIR/tmp" ] && cp -R "$TARGET_REPO_DIR/tmp" "$OUT/repo-tmp" 2>/dev/null
  [ -d "$TARGET_REPO_DIR/artifacts" ] && cp -R "$TARGET_REPO_DIR/artifacts" "$OUT/repo-artifacts" 2>/dev/null
  if [ "${STRAT_CAPTURE_NATIVE:-0}" = 1 ]; then
    python3 - "$TARGET_REPO_DIR" "$OUT" <<'PY'
import json, os, pathlib, shutil, subprocess, sys
repo, out = map(pathlib.Path, sys.argv[1:])
config = pathlib.Path(os.environ.get('CLAUDE_CONFIG_DIR', str(pathlib.Path.home() / '.claude')))
slug = ''.join(char if char.isascii() and char.isalnum() else '-' for char in str(repo.resolve()))
project = config / 'projects' / slug
if project.is_dir():
    shutil.copytree(project, out / 'native-projects' / slug, dirs_exist_ok=True)
version = subprocess.run(['claude', '--version'], capture_output=True, text=True, timeout=15)
(out / 'native-version.json').write_text(json.dumps({'version': version.stdout.strip(), 'exit': version.returncode, 'project_found': project.is_dir()}, indent=2) + '\n')
PY
  fi
  python3 - "$OUT/run-summary.json" <<EOF
import json, pathlib, sys
num = lambda v: int(v) if v else None
result = pathlib.Path("$RUN_OUT/output/agent-result.json")
summary = {
    "arm": "workflow",
    "rfe": "$RFE_KEY",
    "mode": "$STRAT_MODE",
    "strat_creator_repo": "$STRAT_CREATOR_REPO",
    "strat_creator_ref": "$STRAT_CREATOR_REF",
    "launch": "claude -p --plugin-dir .fullsend/plugins/strat-pipeline $WORKFLOW_COMMAND",
    "model": "${ANTHROPIC_MODEL:-}",
    "effort": "${STRAT_EFFORT:-high}",
    "workflow_max_concurrent_agents": num("${CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS:-}"),
    "stop_on_workflow_failure": "${STRAT_STOP_ON_WORKFLOW_FAILURE:-0}" == "1",
    "bg_wait_ceiling_ms": int("${STRAT_BG_WAIT_CEILING_MS:-1800000}"),
    "dry_run": "$STRAT_DRY_RUN" in ("1", "true"),
    "job": "${PIPELINE_JOB_NAME:-}",
    "mlflow_experiment": "${MLFLOW_EXPERIMENT_NAME:-}",
    "pre_rc": num("$PRE_RC"),
    "claude_rc": num("$CLAUDE_RC"),
    "validate_rc": num("$VALIDATE_RC"),
    "post_rc": num("$POST_RC"),
    "release_rc": num("$RELEASE_RC"),
    "exit": $rc,
    "result": json.loads(result.read_text()) if result.exists() else None,
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k != "result"}, indent=2))
EOF
  exit "$rc"
}
trap finish EXIT

echo "=== clone strat-creator $STRAT_CREATOR_REF ==="
git init -q "$TARGET_REPO_DIR"
git -C "$TARGET_REPO_DIR" fetch -q --depth 1 "$STRAT_CREATOR_REPO" "$STRAT_CREATOR_REF" || exit 1
git -C "$TARGET_REPO_DIR" -c advice.detachedHead=false checkout -q FETCH_HEAD || exit 1
if [ "$(git -C "$TARGET_REPO_DIR" rev-parse HEAD)" != "$STRAT_CREATOR_REF" ]; then
  echo "ERROR: target checkout is not at $STRAT_CREATOR_REF" >&2
  exit 1
fi

if [ -n "${STRAT_MIXED_SEED_JSON:-}" ]; then
  export STRAT_PREVIOUS_PROGRESS
  STRAT_PREVIOUS_PROGRESS="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["previous_progress_path"])' "$STRAT_MIXED_SEED_JSON")" || exit 1
fi

echo "=== pre-strategy.sh (prepare, lock $RFE_KEY) ==="
(cd "$TARGET_REPO_DIR" && bash .fullsend/shared/pre-strategy.sh)
PRE_RC=$?
if [ "$PRE_RC" = 78 ]; then
  echo "pre-strategy: nothing to do (exit 78)"
  exit 78
elif [ "$PRE_RC" != 0 ]; then
  echo "ERROR: pre-strategy.sh failed ($PRE_RC)" >&2
  exit "$PRE_RC"
fi

if [ -n "${STRAT_MIXED_SEED_JSON:-}" ]; then
  echo "=== verify mixed-state acquisition and resume points before inference ==="
  python3 "$BENCH_SCRIPTS/mixed_state.py" guard "$STRAT_MIXED_SEED_JSON" \
    "$TARGET_REPO_DIR" "$STRAT_STATE_DIR" "$OUT" || exit 1
fi

echo "=== workflow: claude -p $WORKFLOW_COMMAND ==="
echo "output: $RUN_OUT/stream.jsonl (stderr: $RUN_OUT/claude-stderr.log)"
(
  cd "$TARGET_REPO_DIR" || exit 1
  export FULLSEND_OUTPUT_DIR="$RUN_OUT/output"
  export RFE_SKIP_BOOTSTRAP=1
  export DISABLE_AUTOUPDATER=1
  # claude -p waits for background tasks (the Workflow) only up to a ceiling,
  # 10 minutes by default; a strategy run takes 10-20 minutes.
  export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS="${STRAT_BG_WAIT_CEILING_MS:-1800000}"
  # Raw output, unprocessed, to files and to the job log at the same time.
  if [ "${STRAT_STOP_ON_WORKFLOW_FAILURE:-0}" = 1 ]; then
    command_prefix=(python3 "$BENCH_SCRIPTS/watch_workflow.py" --repository "$TARGET_REPO_DIR"
      --report "$OUT/workflow-failure-stop.json" --timeout "$((TIMEOUT_MINUTES * 60))" --)
  else
    command_prefix=(timeout "$((TIMEOUT_MINUTES * 60))")
  fi
  "${command_prefix[@]}" claude --print --verbose --output-format stream-json \
    ${ANTHROPIC_MODEL:+--model "$ANTHROPIC_MODEL"} --effort "${STRAT_EFFORT:-high}" \
    --plugin-dir "$TARGET_REPO_DIR/.fullsend/plugins/strat-pipeline" \
    --dangerously-skip-permissions "$WORKFLOW_COMMAND" \
    2> >(tee "$RUN_OUT/claude-stderr.log" >&2) | tee "$RUN_OUT/stream.jsonl"
  exit "${PIPESTATUS[0]}"
)
CLAUDE_RC=$?
echo "claude exit: $CLAUDE_RC"

echo "=== validate-output.sh (PR #83's checker) ==="
export FULLSEND_OUTPUT_SCHEMA="$SHARED/result.schema.json"
(cd "$RUN_OUT" && bash "$SHARED/validate-output.sh") >"$RUN_OUT/validation.txt" 2>&1
VALIDATE_RC=$?
cat "$RUN_OUT/validation.txt"

if [ "$VALIDATE_RC" = 0 ]; then
  echo "=== post-strategy.sh (hand-off, report${RESULTS_REPO_URL:+, push to $RESULTS_REPO_URL}) ==="
  (cd "$OUT" && FULLSEND_VALIDATED_ITERATION_DIR="$RUN_OUT/output" bash "$SHARED/post-strategy.sh")
  POST_RC=$?
fi

[ "$CLAUDE_RC" != 0 ] && exit "$CLAUDE_RC"
[ "$VALIDATE_RC" != 0 ] && exit "$VALIDATE_RC"
exit "${POST_RC:-0}"
