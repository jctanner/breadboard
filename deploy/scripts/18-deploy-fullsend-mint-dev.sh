#!/usr/bin/env bash
# Bootstrap bot-owned emulator tokens and deploy the development-only Fullsend mint.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
GITHUB_URL="${GITHUB_EMULATOR_URL:-https://github.local}"
GITHUB_TOKEN="${GITHUB_EMULATOR_TOKEN:-ghp_admin_default_token}"
OIDC_TOKEN="${FULLSEND_DEV_OIDC_TOKEN:-fullsend-dev-oidc}"
API="${GITHUB_URL%/}/api/v3"
FULLSEND_ORG="${FULLSEND_GITHUB_ORG:-fullsend-dev}"

ensure_app() {
  local app_id="$1"
  local name="$2"
  local slug="$3"
  local permissions="$4"
  local app_status
  app_status="$(curl --silent --show-error --insecure \
    -o /dev/null -w '%{http_code}' \
    -X POST "${API}/admin/apps" \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H 'Content-Type: application/json' \
    -d "$(jq -nc \
      --arg app_id "${app_id}" --arg name "${name}" --arg slug "${slug}" \
      --argjson permissions "${permissions}" \
      '{app_id:$app_id,name:$name,slug:$slug,permissions:$permissions}')")"
  if [[ "${app_status}" != 201 && "${app_status}" != 409 ]]; then
    echo "ERROR: could not ensure ${slug} App (HTTP ${app_status})" >&2
    exit 1
  fi

  local reconcile_status
  reconcile_status="$(curl --silent --show-error --insecure \
    -o /dev/null -w '%{http_code}' \
    -X PATCH "${API}/admin/apps/${app_id}" \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H 'Content-Type: application/json' \
    -d "$(jq -nc \
      --arg name "${name}" --arg slug "${slug}" \
      --argjson permissions "${permissions}" \
      '{name:$name,slug:$slug,permissions:$permissions,sync_installations:true}')")"
  if [[ "${reconcile_status}" != 200 ]]; then
    echo "ERROR: could not reconcile ${slug} App (HTTP ${reconcile_status})" >&2
    exit 1
  fi
}

echo "==> Ensuring separate Fullsend App/bot identities"
ensure_app 1001 "Fullsend Triage" fullsend-triage \
  '{"contents":"read","issues":"write","metadata":"read"}'
ensure_app 1002 "Fullsend Scribe" fullsend-scribe \
  '{"contents":"read","issues":"write","metadata":"read"}'
ensure_app 1003 "Fullsend Code" fullsend-code \
  '{"contents":"write","issues":"write","pull_requests":"write","metadata":"read"}'
ensure_app 1004 "Fullsend Review" fullsend-review \
  '{"contents":"read","issues":"write","pull_requests":"write","metadata":"read"}'
ensure_app 1005 "Fullsend Fix" fullsend-fix \
  '{"contents":"write","issues":"write","pull_requests":"write","metadata":"read"}'
ensure_app 1006 "Fullsend" fullsend \
  '{"contents":"write","issues":"write","pull_requests":"write","metadata":"read"}'

echo "==> Granting Code and Fix bots push access to seeded repositories"
for bot_login in fullsend-code%5Bbot%5D fullsend-fix%5Bbot%5D; do
  repository="${FULLSEND_ORG}/triage-target"
  collaborator_status="$(curl --silent --show-error --insecure \
    -o /dev/null -w '%{http_code}' \
    -X PUT "${API}/repos/${repository}/collaborators/${bot_login}" \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H 'Content-Type: application/json' \
    -d '{"permission":"push"}')"
  if [[ "${collaborator_status}" != 201 ]]; then
    echo "ERROR: could not grant ${bot_login} access to ${repository} (HTTP ${collaborator_status})" >&2
    exit 1
  fi
done

mint_pat() {
  local role="$1"
  local scopes="$2"
  local login="$3"
  local response
  response="$(curl --silent --show-error --fail --insecure \
    -X POST "${API}/admin/tokens" \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H 'Content-Type: application/json' \
    -d "$(jq -nc --arg login "${login}" --arg name "fullsend-dev-${role}" --argjson scopes "${scopes}" \
      '{login:$login,name:$name,scopes:$scopes}')")"
  jq -er '.token' <<<"${response}"
}

echo "==> Creating development role tokens in the GitHub emulator"
readonly ISSUE_SCOPES='["repo","repo:status","read:org"]'
TRIAGE_TOKEN="$(mint_pat triage "${ISSUE_SCOPES}" 'fullsend-triage[bot]')"
SCRIBE_TOKEN="$(mint_pat scribe "${ISSUE_SCOPES}" 'fullsend-scribe[bot]')"
CODER_TOKEN="$(mint_pat coder "${ISSUE_SCOPES}" 'fullsend-code[bot]')"
REVIEW_TOKEN="$(mint_pat review "${ISSUE_SCOPES}" 'fullsend-review[bot]')"
FIX_TOKEN="$(mint_pat fix "${ISSUE_SCOPES}" 'fullsend-fix[bot]')"
FULLSEND_TOKEN="$(mint_pat fullsend "${ISSUE_SCOPES}" 'fullsend[bot]')"

ROLE_TOKENS="$(jq -nc \
  --arg triage "${TRIAGE_TOKEN}" \
  --arg scribe "${SCRIBE_TOKEN}" \
  --arg coder "${CODER_TOKEN}" \
  --arg review "${REVIEW_TOKEN}" \
  --arg fix "${FIX_TOKEN}" \
  --arg fullsend "${FULLSEND_TOKEN}" \
  '{triage:$triage,scribe:$scribe,coder:$coder,review:$review,fix:$fix,fullsend:$fullsend}')"

echo "==> Creating fullsend-mint-dev credentials secret"
kubectl -n ai-pipeline create secret generic fullsend-mint-dev-credentials \
  --from-literal=oidc-token="${OIDC_TOKEN}" \
  --from-literal=role-tokens="${ROLE_TOKENS}" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null

echo "==> Deploying fullsend-mint-dev"
kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/24-fullsend-mint-dev.yaml"
kubectl -n ai-pipeline rollout restart deployment/fullsend-mint-dev
kubectl -n ai-pipeline rollout status deployment/fullsend-mint-dev --timeout=120s
echo "==> fullsend-mint-dev is ready"
