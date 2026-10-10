#!/bin/bash
# Arm script: run strat-creator PR #83's Claude Workflow on one RFE, the way
# fullsend runs its strat-single harness, inside a dashboard script job.
#
#   run-workflow.sh RHAIRFE-N
#
# Environment (from the job; extra_env can override):
#   STRAT_CREATOR_REF   strat-creator commit (default: PR #83, 6b78355)
#   STRAT_CREATOR_REPO  default: the GitHub emulator's opendatahub-io/strat-creator
#   STRAT_ARCHITECTURE_CONTEXT_PATH  pinned snapshot on the context volume
#   STRAT_DRY_RUN       1 for no Jira writes (default: real writes)
#   STRAT_TIMEOUT_MINUTES  per attempt (default 90, as strat-single)
#   STRAT_EFFORT        claude --effort (default high, as strat-single)
#   JIRA_SERVER, JIRA_USER, JIRA_TOKEN, ANTHROPIC_MODEL: set by the job
#
# Steps, as fullsend does them:
#   1. pre-strategy.sh: clone and verify the pinned commit, load the
#      architecture context, lock the RFE, write tmp/strat-input.json
#      (exit 78: nothing to do);
#   2. claude --agent strat-single with the strat-pipeline plugin, headless;
#   3. validate-output.sh; on failure, one more attempt with its feedback
#      appended to the prompt (validation_loop: max_iterations 2, append);
#   4. post-strategy.sh: hand-off and report (no push: RESULTS_REPO_URL unset);
#   5. release-locks.sh, always.
# Everything worth keeping lands in $JOB_ARTIFACT_DIR, with a summary in
# run-summary.json. Exit 0 only when an attempt validated and post succeeded.

set -uo pipefail

RFE_KEY="${1:-}"
if [[ ! "$RFE_KEY" =~ ^RHAIRFE-[0-9]+$ ]]; then
  echo "usage: run-workflow.sh RHAIRFE-N" >&2
  exit 2
fi
export RFE_KEY

export STRAT_MODE=single
export STRAT_CREATOR_REF="${STRAT_CREATOR_REF:-6b78355ebc450ff4737fd10ba4857c26086ceac0}"
export STRAT_CREATOR_REPO="${STRAT_CREATOR_REPO:-https://github.local/opendatahub-io/strat-creator.git}"
export STRAT_ARCHITECTURE_CONTEXT_PATH="${STRAT_ARCHITECTURE_CONTEXT_PATH:-/app/.context/snapshots/architecture-context/7d61f097a9220aeb1280837b66b532177ec558b6}"
export STRAT_DRY_RUN="${STRAT_DRY_RUN:-}"
export STRAT_RUN_ID="${STRAT_RUN_ID:-${PIPELINE_JOB_NAME:-run-$$}}"
TIMEOUT_MINUTES="${STRAT_TIMEOUT_MINUTES:-90}"
DEFAULT_PROMPT="Run the agent task"

OUT="${JOB_ARTIFACT_DIR:?run under run_script.sh (JOB_ARTIFACT_DIR unset)}"
WORK="${PIPELINE_TMP_DIR:-/tmp}/strat-workflow/${STRAT_RUN_ID}"
export TARGET_REPO_DIR="$WORK/repo"
export REPO_DIR="$TARGET_REPO_DIR"
export STRAT_STATE_DIR="$WORK/state"
export STRAT_PUBLISH_DIR="$OUT/publish"
unset RESULTS_REPO_URL ORG_PULSE_URL
SHARED="$STRAT_STATE_DIR/strat-creator/.fullsend/shared"

rm -rf "$WORK"
mkdir -p "$WORK" "$OUT"

PRE_RC=""
POST_RC=""
RELEASE_RC=""
VALIDATED=""
ATTEMPTS_JSON="[]"

summary() {
  python3 - "$OUT/run-summary.json" <<EOF
import json, sys, pathlib
attempts = json.loads('''$ATTEMPTS_JSON''')
result_file = pathlib.Path("$OUT/agent-result.json")
summary = {
    "rfe": "$RFE_KEY",
    "strat_creator_ref": "$STRAT_CREATOR_REF",
    "model": "${ANTHROPIC_MODEL:-}",
    "dry_run": "$STRAT_DRY_RUN" in ("1", "true"),
    "job": "${PIPELINE_JOB_NAME:-}",
    "mlflow_experiment": "${MLFLOW_EXPERIMENT_NAME:-}",
    "pre_rc": int("${PRE_RC:-0}" or 0) if "$PRE_RC" else None,
    "attempts": attempts,
    "validated_attempt": int("$VALIDATED") if "$VALIDATED" else None,
    "post_rc": int("$POST_RC") if "$POST_RC" else None,
    "release_rc": int("$RELEASE_RC") if "$RELEASE_RC" else None,
    "result": json.loads(result_file.read_text()) if result_file.exists() else None,
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
EOF
}

finish() {
  local rc=$?
  trap - EXIT
  # Locks are released whatever happened, as the CI cleanup does.
  if [ -f "$SHARED/release-locks.sh" ]; then
    echo "=== release locks ==="
    bash "$SHARED/release-locks.sh" "$STRAT_STATE_DIR"
    RELEASE_RC=$?
  fi
  # Keep the run record and progress next to the job's other artifacts.
  mkdir -p "$OUT/state"
  cp -f "$STRAT_STATE_DIR"/run.json "$STRAT_STATE_DIR"/owned-rfe-ids.txt* "$OUT/state/" 2>/dev/null || true
  [ -d "$TARGET_REPO_DIR/tmp" ] && cp -R "$TARGET_REPO_DIR/tmp" "$OUT/repo-tmp" 2>/dev/null
  [ -d "$TARGET_REPO_DIR/artifacts" ] && cp -R "$TARGET_REPO_DIR/artifacts" "$OUT/repo-artifacts" 2>/dev/null
  echo "=== run summary ==="
  summary
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
cp -f "$STRAT_STATE_DIR/run.json" "$OUT/run.json" 2>/dev/null || true

# fullsend installs the harness agent into the Claude config; a project-scope
# copy resolves the same --agent name (as PR #83's own smoke test does).
mkdir -p "$TARGET_REPO_DIR/.claude/agents"
cp -f "$TARGET_REPO_DIR/.fullsend/strat-single/prompt.md" "$TARGET_REPO_DIR/.claude/agents/strat-single.md"

export FULLSEND_OUTPUT_SCHEMA="$SHARED/result.schema.json"
PROMPT="$DEFAULT_PROMPT"
for attempt in 1 2; do
  ITER="$OUT/iteration-$attempt"
  mkdir -p "$ITER/output"
  echo "=== attempt $attempt: claude --agent strat-single (Workflow strat-pipeline) ==="
  (
    cd "$TARGET_REPO_DIR" || exit 1
    export FULLSEND_OUTPUT_DIR="$ITER/output"
    export RFE_SKIP_BOOTSTRAP=1
    export DISABLE_AUTOUPDATER=1
    timeout "$((TIMEOUT_MINUTES * 60))" claude --print --verbose --output-format stream-json \
      ${ANTHROPIC_MODEL:+--model "$ANTHROPIC_MODEL"} --effort "${STRAT_EFFORT:-high}" \
      --plugin-dir "$TARGET_REPO_DIR/.fullsend/plugins/strat-pipeline" \
      --agent strat-single --dangerously-skip-permissions "$PROMPT" \
      2>"$ITER/claude-stderr.log" | tee "$ITER/stream.jsonl" | python3 -u /app/scripts/stream-claude.py
    exit "${PIPESTATUS[0]}"
  )
  CLAUDE_RC=$?
  echo "claude exit: $CLAUDE_RC"

  echo "=== attempt $attempt: validate-output.sh ==="
  (cd "$ITER" && bash "$SHARED/validate-output.sh") >"$ITER/validation.txt" 2>&1
  VALIDATE_RC=$?
  cat "$ITER/validation.txt"
  ATTEMPTS_JSON="$(python3 -c 'import json,sys; a=json.loads(sys.argv[1]); a.append({"attempt": int(sys.argv[2]), "claude_rc": int(sys.argv[3]), "validate_rc": int(sys.argv[4])}); print(json.dumps(a))' "$ATTEMPTS_JSON" "$attempt" "$CLAUDE_RC" "$VALIDATE_RC")"
  if [ "$VALIDATE_RC" = 0 ]; then
    VALIDATED="$attempt"
    cp -f "$ITER/output/agent-result.json" "$OUT/agent-result.json"
    break
  fi
  # feedback_mode: append, as fullsend's validation loop does.
  PROMPT="$DEFAULT_PROMPT

Validation feedback from the previous attempt:
$(cat "$ITER/validation.txt")"
done

if [ -z "$VALIDATED" ]; then
  echo "ERROR: no attempt passed validation" >&2
  exit 1
fi

echo "=== post-strategy.sh (hand-off and report; nothing pushed) ==="
(cd "$OUT" && FULLSEND_VALIDATED_ITERATION_DIR="$OUT/iteration-$VALIDATED/output" bash "$SHARED/post-strategy.sh")
POST_RC=$?
exit "$POST_RC"
