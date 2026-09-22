#!/usr/bin/env bash
# Reset the state the conformance check depends on, including the OpenShell
# gateway.
#
# This exists because "clean" did not mean clean. clean-all.sh wipes PVC data
# in ai-pipeline and gitlab-runner and never touches openshell-system, so a
# reset left the gateway holding whatever it already had. That is not a
# theoretical gap: the gateway served a 26-day-old provider profile while every
# run reported importing it, and an agent was denied access its own policy file
# granted (G42/G43). Three things conspired, and a reset has to undo all three:
#
#   1. Sandboxes outlive their runs when cleanup fails, and the gateway refuses
#      to delete a profile a live sandbox references.
#   2. Fullsend caches a profile's content hash on the runner, keyed by profile
#      id, and skips the import when it matches. A profile that failed to
#      replace still gets the new hash written, so every later run skips.
#   3. The profile therefore stays stale with nothing reporting it.
#
# Deliberately NOT a data wipe. clean-all.sh remains the separate, heavier
# operation for PVC contents; this resets only what the conformance scenario
# reads and writes. It is also deliberately not chained into a target named
# "all" - destroying state should be something someone asked for by name.
#
# Usage: 25-reset-conformance.sh [--yes]
#   --yes   skip the confirmation prompt

set -euo pipefail

ASSUME_YES=0
for arg in "$@"; do
  case "${arg}" in
    --yes) ASSUME_YES=1 ;;
    *) echo "unknown argument: ${arg}" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

FORGE="${CONFORMANCE_FORGE:-https://github.local}"
REPO="${CONFORMANCE_REPO:-fullsend-dev/triage-target}"
TOKEN="${GITHUB_EMULATOR_TOKEN:-ghp_admin_default_token}"
API="${FORGE}/api/v3/repos/${REPO}"
NAMESPACE="${CONFORMANCE_NAMESPACE:-ai-pipeline}"
RUNNER_DEPLOYMENTS="${CONFORMANCE_RUNNERS:-github-actions-runner github-actions-config-runner}"

note() { echo "==> $*"; }

if [ "${ASSUME_YES}" -eq 0 ]; then
  cat <<EOF
This will reset the conformance state:

  - delete every OpenShell sandbox on the gateway
  - delete the user-scoped fullsend provider profiles (re-imported on the
    next run from the agents mirror)
  - clear Fullsend's profile hash cache on the runner pods
  - close every open issue on ${REPO}

It does NOT wipe PVC data; deploy/scripts/clean-all.sh does that separately.

EOF
  read -r -p "Proceed? [y/N] " reply
  case "${reply}" in
    y|Y|yes|YES) ;;
    *) echo "Aborted."; exit 1 ;;
  esac
fi

runner_exec() {
  # Run a command on the first available runner deployment.
  local dep
  for dep in ${RUNNER_DEPLOYMENTS}; do
    if kubectl get "deploy/${dep}" -n "${NAMESPACE}" >/dev/null 2>&1; then
      kubectl exec -n "${NAMESPACE}" "deploy/${dep}" -- "$@" 2>/dev/null && return 0
    fi
  done
  return 1
}

# --- 1. Sandboxes ---------------------------------------------------------
# First, because the gateway refuses to delete a profile that one references.
note "Deleting OpenShell sandboxes"
SANDBOXES="$(runner_exec openshell sandbox list -o json 2>/dev/null \
  | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
items = d if isinstance(d, list) else d.get("sandboxes", d.get("items", []))
for s in items:
    name = s.get("name") or s.get("metadata", {}).get("name")
    if name:
        print(name)
' 2>/dev/null || true)"
if [ -n "${SANDBOXES}" ]; then
  # shellcheck disable=SC2086
  runner_exec openshell sandbox delete ${SANDBOXES} || true
  note "  deleted: $(echo "${SANDBOXES}" | tr '\n' ' ')"
else
  # The JSON shape is not guaranteed across versions; fall back to the
  # documented bulk flag rather than silently skipping the step.
  runner_exec openshell sandbox delete --all >/dev/null 2>&1 || true
  note "  none listed (used --all as a fallback)"
fi

# --- 2. Provider profiles -------------------------------------------------
# Derived state: Fullsend re-imports them from the agents mirror on the next
# run. Deleting is what makes that import actually replace rather than no-op.
note "Deleting user-scoped fullsend provider profiles"
PROFILES="$(runner_exec openshell provider list-profiles 2>/dev/null \
  | awk '$3 == "user" { print $1 }' || true)"
if [ -n "${PROFILES}" ]; then
  for id in ${PROFILES}; do
    if runner_exec openshell provider profile delete "${id}" >/dev/null 2>&1; then
      note "  deleted ${id}"
    else
      # Worth saying out loud: this is exactly how the profile went stale.
      note "  WARNING: could not delete ${id} (something still references it)"
    fi
  done
else
  note "  none found"
fi

# --- 3. Fullsend's profile hash cache -------------------------------------
# Keyed by profile id in os.TempDir() on the runner. Without clearing it, the
# next run takes the fast path and skips the import regardless of the gateway.
note "Clearing Fullsend's profile hash cache on the runners"
for dep in ${RUNNER_DEPLOYMENTS}; do
  if kubectl get "deploy/${dep}" -n "${NAMESPACE}" >/dev/null 2>&1; then
    kubectl exec -n "${NAMESPACE}" "deploy/${dep}" -- \
      sh -c 'rm -f /tmp/fullsend-profile-*.sha256 /tmp/fullsend-profile-*.lock' 2>/dev/null || true
    note "  cleared on ${dep}"
  fi
done

# --- 4. Forge baseline ----------------------------------------------------
# An issue resembling an open one is correctly triaged as a duplicate, so a
# backlog changes what the scenario exercises.
note "Closing open issues on ${REPO}"
python3 - "${API}" "${TOKEN}" <<'PY'
import json, ssl, sys, time, urllib.request
api, token = sys.argv[1:3]
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
hdrs = {"Authorization": "token " + token, "Content-Type": "application/json"}
def call(url, data=None, method=None):
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    return json.load(urllib.request.urlopen(req, context=ctx))
closed = 0
while True:
    page = call(f"{api}/issues?state=open&per_page=50")
    if not page:
        break
    for issue in page:
        call(f"{api}/issues/{issue['number']}",
             data=json.dumps({"state": "closed"}).encode(), method="PATCH")
        closed += 1
        # Each close fires an issues event; pace them so the emulator is not
        # driven into the SQLite lock contention seen under bulk writes.
        time.sleep(1.5)
    if len(page) < 50:
        break
print(f"  closed {closed} issue(s)")
PY

note "Conformance state reset. Next run re-imports profiles from the agents mirror."
