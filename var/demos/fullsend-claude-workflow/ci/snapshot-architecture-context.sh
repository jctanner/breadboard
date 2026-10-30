#!/bin/bash
# Pin one architecture-context snapshot on the shared /app/.context volume, so
# every benchmark run reads the same reference material and nothing is fetched
# mid-test. Run it as a dashboard script job (it needs the pipeline-context
# volume) and pass the snapshot path to strat-creator as
# STRAT_ARCHITECTURE_CONTEXT_PATH.
#
#   snapshot-architecture-context.sh [<commit>]
#
# Without a commit it pins the current main of
# opendatahub-io/architecture-context. The snapshot holds the newest
# architecture/rhoai-* directory and overlays/, the same subset
# strat-creator's fetch-architecture-context.sh checks out, at
#   /app/.context/snapshots/architecture-context/<commit>/
# with SNAPSHOT.json recording its source. Existing snapshots are kept as they
# are.

set -euo pipefail

REPO="https://github.com/opendatahub-io/architecture-context"
ROOT="${CONTEXT_SNAPSHOT_ROOT:-/app/.context/snapshots/architecture-context}"

COMMIT="${1:-}"
if [ -z "$COMMIT" ]; then
  COMMIT="$(git ls-remote "$REPO" refs/heads/main | cut -f1)"
  echo "Pinning current main: $COMMIT"
fi
if [[ ! "$COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  echo "ERROR: commit must be a full 40-character sha: $COMMIT" >&2
  exit 2
fi

DEST="$ROOT/$COMMIT"
if [ -f "$DEST/SNAPSHOT.json" ]; then
  echo "Snapshot already present: $DEST"
  cat "$DEST/SNAPSHOT.json"
  exit 0
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git init -q "$WORK/src"
git -C "$WORK/src" fetch -q --depth 1 --filter=blob:none "$REPO" "$COMMIT"
LATEST="$(git -C "$WORK/src" ls-tree --name-only FETCH_HEAD architecture/ \
  | sed 's|^architecture/||' | grep '^rhoai-' | sort | tail -1)"
if [ -z "$LATEST" ]; then
  echo "ERROR: no architecture/rhoai-* directory at $COMMIT" >&2
  exit 1
fi
git -C "$WORK/src" sparse-checkout set --no-cone "/architecture/$LATEST/" "/overlays/"
git -C "$WORK/src" -c advice.detachedHead=false checkout -q FETCH_HEAD
if [ ! -f "$WORK/src/architecture/$LATEST/PLATFORM.md" ]; then
  echo "ERROR: architecture/$LATEST/PLATFORM.md missing at $COMMIT" >&2
  exit 1
fi

mkdir -p "$ROOT"
STAGE="$ROOT/.tmp-$COMMIT-$$"
rm -rf "$STAGE"
mkdir -p "$STAGE/architecture"
cp -R "$WORK/src/architecture/$LATEST" "$STAGE/architecture/"
[ -d "$WORK/src/overlays" ] && cp -R "$WORK/src/overlays" "$STAGE/"
echo "$LATEST" > "$STAGE/LATEST_VERSION"
FILES="$(find "$STAGE" -type f | wc -l)"
SIZE="$(du -sh "$STAGE" | cut -f1)"
cat > "$STAGE/SNAPSHOT.json" <<EOF
{
  "repo": "$REPO",
  "commit": "$COMMIT",
  "latest_version": "$LATEST",
  "files": $FILES,
  "size": "$SIZE",
  "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "job": "${PIPELINE_JOB_NAME:-}"
}
EOF
mv "$STAGE" "$DEST"

echo "Snapshot ready: $DEST"
cat "$DEST/SNAPSHOT.json"
[ -n "${JOB_ARTIFACT_DIR:-}" ] && cp "$DEST/SNAPSHOT.json" "$JOB_ARTIFACT_DIR/"
exit 0
