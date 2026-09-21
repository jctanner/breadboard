#!/usr/bin/env bash
# Run the Fullsend/Claude result smoke (formerly "M6") and verify its
# emulator-side issue comment. This is a named legacy compatibility test, not
# the conformance path - see
# .ledger/plans/fullsend-integration-conformance-plan.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
SOURCE_MANIFEST="${PROJECT_ROOT}/deploy/k8s/25-fullsend-direct-token-smoke.yaml"
ARTIFACTS_DIR="${PROJECT_ROOT}/deploy/fullsend/legacy/artifacts/result-smoke"
MANIFEST="$(mktemp)"
trap 'rm -f "${MANIFEST}" "${MANIFEST}.tmp"' EXIT

sed \
  -e 's/fullsend-direct-token-smoke/fullsend-result-smoke/g' \
  -e 's/direct-token-smoke/result-smoke/g' \
  -e 's/runtime: dummy/runtime: claude/g' \
  -e 's/name: triage/name: claude/g' \
  -e 's/fullsend run triage/fullsend run claude/g' \
  -e 's/breadboard\.dev\/fixture: direct-token-smoke/breadboard.dev\/fixture: result-smoke/' \
  -e 's/--forge github \\/--forge github/' \
  -e '/--no-post-script/d' \
  "${SOURCE_MANIFEST}" > "${MANIFEST}"

awk '
/^    env:$/ && !runner_env_added {
  print "    host_files:"
  print "      - src: /var/run/secrets/gcp/credentials.json"
  print "        dest: /sandbox/workspace/gcp-credentials.json"
  print "        optional: true"
  print
  print "      runner:"
  print "        FULLSEND_STATUS_REPO: fullsend-dev/triage-target"
  print "        FULLSEND_STATUS_NUMBER: \"1\""
  runner_env_added = 1
  next
}
/^[[:space:]]+GITHUB_API_URL: http:\/\/github\.local\/api\/v3$/ {
  print
  print "        CLAUDE_CODE_USE_VERTEX: ${CLAUDE_CODE_USE_VERTEX}"
  print "        CLOUD_ML_REGION: ${CLOUD_ML_REGION}"
  print "        ANTHROPIC_VERTEX_PROJECT_ID: ${ANTHROPIC_VERTEX_PROJECT_ID}"
  print "        GOOGLE_APPLICATION_CREDENTIALS: /sandbox/workspace/gcp-credentials.json"
  next
}
/^[[:space:]]+role: triage$/ && !post_script_added {
  print
  print "    post_script: scripts/post-triage.sh"
  post_script_added = 1
  next
}
/^---$/ && !post_script_data_added {
  print "  post-triage.sh: |"
  print "    #!/bin/sh"
  print "    set -eu"
  print "    api=\"${GITHUB_API_URL:-http://github.local/api/v3}\""
  print "    repo=\"${FULLSEND_STATUS_REPO:?FULLSEND_STATUS_REPO is required}\""
  print "    number=\"${FULLSEND_STATUS_NUMBER:?FULLSEND_STATUS_NUMBER is required}\""
  print "    token=\"${GITHUB_TOKEN:?GITHUB_TOKEN is required}\""
  print "    body=\"<!-- fullsend-result-smoke:triage -->\\nFullsend result smoke Claude/Vertex triage completed through OpenShell.\""
  print "    curl_args=\"\""
  print "    if [ \"${NO_SSL_VERIFY:-0}\" = \"1\" ]; then curl_args=\"-k\"; fi"
  print "    curl ${curl_args} -fsS -o /dev/null -X POST \"${api}/repos/${repo}/issues/${number}/comments\" -H \"Authorization: token ${token}\" -H \"Content-Type: application/json\" -d \"$(jq -nc --arg body \"${body}\" \x27{body:$body}\x27)\""
  print "    echo \"Fullsend result smoke comment posted to ${repo}#${number}\""
  post_script_data_added = 1
}
/^[[:space:]]+- key: behaviour-current-scenario\.yaml$/ {
  print
  getline
  print
  print "              - key: post-triage.sh"
  print "                path: scripts/post-triage.sh"
  next
}
{ print }
' "${MANIFEST}" > "${MANIFEST}.tmp"
mv "${MANIFEST}.tmp" "${MANIFEST}"

if [ -n "${RESULT_SMOKE_MANIFEST_OUTPUT:-}" ]; then
  cp "${MANIFEST}" "${RESULT_SMOKE_MANIFEST_OUTPUT}"
  exit 0
fi

kubectl -n ai-pipeline delete job fullsend-result-smoke --ignore-not-found --wait=true
kubectl -n ai-pipeline delete pods -l job-name=fullsend-result-smoke --ignore-not-found --wait=true
kubectl apply -f "${MANIFEST}"

POD=""
for _ in $(seq 1 600); do
  POD="$(kubectl -n ai-pipeline get pods -l job-name=fullsend-result-smoke -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  if [ -n "${POD}" ] && kubectl -n ai-pipeline exec "${POD}" -c artifact-holder -- test -f /artifacts/.fullsend-done >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [ -z "${POD}" ] || ! kubectl -n ai-pipeline exec "${POD}" -c artifact-holder -- test -f /artifacts/.fullsend-done >/dev/null 2>&1; then
  echo "Fullsend result smoke did not produce completion marker" >&2
  kubectl -n ai-pipeline get pods -l job-name=fullsend-result-smoke -o wide >&2 || true
  exit 1
fi

kubectl -n ai-pipeline logs "${POD}"
mkdir -p "${ARTIFACTS_DIR}"
kubectl -n ai-pipeline cp "${POD}:/artifacts" "${ARTIFACTS_DIR}" --container=artifact-holder --retries=2
STATUS="$(kubectl -n ai-pipeline exec "${POD}" -c artifact-holder -- cat /artifacts/.fullsend-status)"

GITHUB_URL="${GITHUB_EMULATOR_URL:-https://github.local}"
GITHUB_API="${GITHUB_URL%/}/api/v3"
GITHUB_TOKEN="${GITHUB_EMULATOR_TOKEN:-ghp_admin_default_token}"
COMMENTS="$(curl --silent --show-error --fail --insecure \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H 'Accept: application/vnd.github+json' \
  "${GITHUB_API}/repos/fullsend-dev/triage-target/issues/1/comments")"
mkdir -p "${ARTIFACTS_DIR}"
jq '[.[] | {id,body,user:.user.login,created_at}]' <<<"${COMMENTS}" > "${ARTIFACTS_DIR}/emulator-comments.json"
if ! jq -e 'any(.[]; .body | contains("<!-- fullsend-result-smoke:triage -->"))' "${ARTIFACTS_DIR}/emulator-comments.json" >/dev/null; then
  echo "Fullsend result smoke did not create the expected marked issue comment" >&2
  kubectl -n ai-pipeline delete job fullsend-result-smoke --ignore-not-found
  exit 1
fi

kubectl -n ai-pipeline delete job fullsend-result-smoke --ignore-not-found

if [ "${STATUS}" != "0" ]; then
  echo "Fullsend result smoke exited with status ${STATUS}" >&2
  exit 1
fi

echo "Result smoke verified against the emulator; artifacts copied to ${ARTIFACTS_DIR}"
