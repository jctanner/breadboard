#!/usr/bin/env bash
# Bootstrap bot-owned emulator tokens and deploy the development-only Fullsend mint.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/render_domain_manifest.py" /dev/null "${BREADBOARD_DOMAIN:-local}" >/dev/null
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
GITHUB_URL="${GITHUB_EMULATOR_URL:-https://github.${BREADBOARD_DOMAIN:-local}}"
GITHUB_TOKEN="${GITHUB_EMULATOR_TOKEN:-ghp_admin_default_token}"
API="${GITHUB_URL%/}/api/v3"
FULLSEND_ORG="${FULLSEND_GITHUB_ORG:-fullsend-dev}"

# Bootstrap with the selected cluster's public CA; never bypass TLS for credentials.
if [ -z "${BREADBOARD_CA_FILE:-}" ]; then
  SEED_CA=$(mktemp /tmp/breadboard-mint-ca.XXXXXX)
  trap 'rm -f "${SEED_CA}"' EXIT
  kubectl get configmap internal-ca-cert -n ai-pipeline \
    -o jsonpath='{.data.ca\.crt}' > "${SEED_CA}"
  export BREADBOARD_CA_FILE="${SEED_CA}"
fi
openssl x509 -in "${BREADBOARD_CA_FILE}" -noout >/dev/null


EXPECTED_APP_PERMISSIONS='{}'
ensure_app() {
  local app_id="$1"
  local name="$2"
  local slug="$3"
  local permissions="$4"
  local app_status
  app_status="$(curl --connect-timeout 10 --max-time 60 --silent --show-error --cacert "${BREADBOARD_CA_FILE}" \
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
  reconcile_status="$(curl --connect-timeout 10 --max-time 60 --silent --show-error --cacert "${BREADBOARD_CA_FILE}" \
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
  EXPECTED_APP_PERMISSIONS="$(jq -nc --argjson all "${EXPECTED_APP_PERMISSIONS}" \
    --arg id "${app_id}" --argjson permissions "${permissions}" '$all + {($id): $permissions}')"
}

echo "==> Ensuring separate Fullsend App/bot identities"
# Permissions follow Fullsend's canonicalRolePermissions (write level), so an
# installation carries exactly what the role's tokens may be downscoped from.
ensure_app 1001 "Fullsend Triage" fullsend-triage \
  '{"contents":"read","issues":"write","metadata":"read"}'
ensure_app 1002 "Fullsend Scribe" fullsend-scribe \
  '{"contents":"read","issues":"write","metadata":"read"}'
ensure_app 1003 "Fullsend Code" fullsend-code \
  '{"contents":"write","packages":"read","pull_requests":"write","issues":"write","checks":"read","metadata":"read"}'
ensure_app 1004 "Fullsend Review" fullsend-review \
  '{"contents":"read","pull_requests":"write","issues":"write","checks":"read","metadata":"read"}'
ensure_app 1005 "Fullsend Fix" fullsend-fix \
  '{"contents":"write","packages":"read","pull_requests":"write","issues":"write","metadata":"read"}'
ensure_app 1006 "Fullsend" fullsend \
  '{"actions":"write","actions_variables":"read","contents":"write","pull_requests":"write","workflows":"write","metadata":"read"}'
ensure_app 1007 "Fullsend Retro" fullsend-retro \
  '{"actions":"read","contents":"read","pull_requests":"write","issues":"write","metadata":"read"}'
ensure_app 1008 "Fullsend Prioritize" fullsend-prioritize \
  '{"contents":"read","issues":"write","organization_projects":"write","metadata":"read"}'

# The Code and Fix bots used to be granted push as collaborators here. Their
# access now comes from their Apps' installations (contents: write), which is
# what an installation token carries on GitHub; a collaborator row would let a
# read-level token push regardless of its level, so none is granted.

mint_pat() {
  local role="$1"
  local scopes="$2"
  local login="$3"
  local response
  response="$(curl --connect-timeout 10 --max-time 60 --silent --show-error --fail --cacert "${BREADBOARD_CA_FILE}" \
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
# The static per-role tokens are no longer what the mint hands out; it mints
# installation tokens from the role Apps below. This Secret survives for the
# named legacy direct-token smoke (25-fullsend-direct-token-smoke.yaml), which
# reads the fullsend token from it directly and is not on the conformance path.
kubectl -n ai-pipeline create secret generic fullsend-mint-dev-credentials \
  --from-literal=role-tokens="${ROLE_TOKENS}" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null

echo "==> Installing the role Apps on ${FULLSEND_ORG} and collecting their keys for the mint"
# Each role App is installed on the seed organisation with repository
# selection "all", so a repository onboarded later is covered without a
# reseed; an older installation that named specific repositories is replaced.
# The Apps' private keys go to a Secret the mint mounts as one file, and the
# mint signs a ten-minute JWT per exchange for a one-hour installation token.
export EXPECTED_APP_PERMISSIONS
ROLE_APPS="$(python3 - "${API}" "${GITHUB_URL%/}" "${GITHUB_TOKEN}" "${FULLSEND_ORG}" <<'PY'
import json, os, ssl, sys, urllib.error, urllib.request
api, base, token, org = sys.argv[1:5]
expected_grants = json.loads(os.environ["EXPECTED_APP_PERMISSIONS"])
ctx = ssl.create_default_context(cafile=os.environ["BREADBOARD_CA_FILE"])
def decode(payload):
    try:
        return json.loads(payload) if payload else None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

def call(url, body=None, method=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "token " + token, "Content-Type": "application/json",
                                          "Accept": "application/vnd.github+json"}, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            payload = r.read(); return r.status, decode(payload)
    except urllib.error.HTTPError as e:
        payload = e.read(); return e.code, decode(payload)
roles = {"triage": "1001", "scribe": "1002", "coder": "1003", "review": "1004", "fix": "1005",
         "fullsend": "1006", "retro": "1007", "prioritize": "1008"}
out = {}
for role, app_id in roles.items():
    status, app = call(f"{api}/admin/apps/{app_id}")
    if status != 200 or not isinstance(app, dict) or not isinstance(app.get("permissions"), dict) or not app["permissions"]:
        sys.exit(f"could not read permissions for App {app_id}: HTTP {status}")
    if app["permissions"] != expected_grants.get(app_id):
        sys.exit(f"App {app_id} permissions differ from requested bootstrap grants")
    # The UI inventory has installation selections but omits App permissions.
    status, inventory = call(f"{base}/admin/api/apps/{app_id}")
    if status != 200 or not isinstance(inventory, dict):
        sys.exit(f"could not read installations for App {app_id}: HTTP {status}")
    installations = inventory.get("installations")
    if not isinstance(installations, list) or any(
        not isinstance(inst, dict) or type(inst.get("id")) is not int or inst["id"] <= 0
        or not isinstance(inst.get("owner"), str) or not isinstance(inst.get("repositories"), list)
        for inst in installations
    ):
        sys.exit(f"invalid installation inventory for App {app_id}")
    for inst in installations:
        if inst.get("owner") == org and inst.get("repositories"):
            status, _ = call(f"{base}/admin/api/apps/{app_id}/installations/{inst['id']}", method="DELETE")
            if status != 204:
                sys.exit(f"could not replace installation {inst['id']} of App {app_id}: HTTP {status}")
    status, inst = call(f"{api}/admin/apps/{app_id}/installations",
                        {"account_login": org, "account_type": "Organization", "repositories": [],
                         "permissions": app["permissions"]})
    if status not in (200, 201):
        sys.exit(f"could not install App {app_id} on {org}: HTTP {status} {inst}")
    if not isinstance(inst, dict) or inst.get("permissions") != app["permissions"] or inst.get("repository_selection") != "all":
        # Roll back only an installation this invocation just created. Do not
        # delete an existing operator installation on a failed verification.
        installation_id = inst.get("id") if isinstance(inst, dict) else None
        cleanup = "returned existing installation left unchanged; any replaced selected installations were already removed"
        if status == 201 and type(installation_id) is int and installation_id > 0:
            try:
                rollback_status, _ = call(f"{base}/admin/api/apps/{app_id}/installations/{installation_id}", method="DELETE")
                cleanup = "new installation removed" if rollback_status == 204 else f"rollback failed: HTTP {rollback_status}; installation {installation_id} may remain"
            except (urllib.error.URLError, OSError):
                cleanup = f"rollback failed: network error; installation {installation_id} may remain"
        elif status == 201:
            cleanup = "new installation ID invalid; cleanup could not be attempted"
        sys.exit(f"installation permissions do not match the configured App {app_id} or repository selection is not all; {cleanup}")
    status, key = call(f"{base}/admin/api/apps/{app_id}/private-key")
    if status != 200 or not isinstance(key, dict) or not key.get("private_key"):
        sys.exit(f"could not read the private key of App {app_id}: HTTP {status}")
    out[role] = {"app_id": app_id, "private_key": key["private_key"]}
print(json.dumps(out))
PY
)"
kubectl -n ai-pipeline create secret generic fullsend-mint-role-apps \
  --from-literal=role-apps.json="${ROLE_APPS}" \
  --dry-run=client -o yaml | kubectl apply -f - >/dev/null

echo "==> Deploying fullsend-mint-dev"
"${SCRIPT_DIR}/apply-domain-manifests.sh" "${PROJECT_ROOT}/deploy/k8s/24-fullsend-mint-dev.yaml"
kubectl -n ai-pipeline rollout restart deployment/fullsend-mint-dev
kubectl -n ai-pipeline rollout status deployment/fullsend-mint-dev --timeout=120s
echo "==> fullsend-mint-dev is ready"
