#!/usr/bin/env bash
# Start an isolated job-owned Podman service and OpenShell gateway, run one
# command, then clean up. Adapted from the script-led POC's
# .fullsend/scripts/ci/with-openshell.sh (strat-creator 78ab3f1), which follows
# rfe-autofixer's autofix-rfe-stage-dry-fullsend job. Changes: no feature
# binary check and no provider shim; released Fullsend 0.43.0 registers the
# upstream Vertex provider itself.
set -Eeuo pipefail

if [[ $# -lt 2 || $1 != -- ]]; then
  echo "usage: gateway.sh -- <command> [args...]" >&2
  exit 2
fi
shift

JOB_ID="${CI_JOB_ID:-}"
if [[ -z "$JOB_ID" || ! "$JOB_ID" =~ ^[[:alnum:]_-]+$ ]]; then
  echo "ERROR: CI_JOB_ID must uniquely identify this job" >&2
  exit 2
fi

VERSION=0.0.112-rhaiv.0
SOCKET=/run/podman/podman.sock
NAME="strat-$JOB_ID"
NETWORK="openshell-strat-$JOB_ID"
STATE="${CI_PROJECT_DIR:?}/.gateway-state/$JOB_ID"
ARTIFACTS="${FULLSEND_CI_ARTIFACTS_DIR:-$CI_PROJECT_DIR/fullsend-ci-artifacts}"
SUPERVISOR_TAG="quay.io/opendatahub/odh-openshell-supervisor:v$VERSION"
SANDBOX_IMAGE="ghcr.io/fullsend-ai/fullsend-sandbox@sha256:259605fea321353552fdefd3a6a55e8b5c260998dfc5a622ed143e41a429995a"
PODMAN_URL="unix://$SOCKET"
PODMAN_PID=""
GATEWAY_PID=""
mkdir -p "$STATE" "$ARTIFACTS" /run/podman /var/lib/containers/storage /run/containers/storage

cleanup() {
  local rc=$? cleanup_rc=0
  trap - EXIT HUP INT TERM
  set +e
  openshell gateway remove "$NAME" >>"$ARTIFACTS/cleanup.log" 2>&1
  if [[ -n "$GATEWAY_PID" ]]; then
    kill -TERM "$GATEWAY_PID" 2>/dev/null
    wait "$GATEWAY_PID" 2>/dev/null
  fi
  if podman --url "$PODMAN_URL" info >/dev/null 2>&1; then
    podman --url "$PODMAN_URL" rm -af >>"$ARTIFACTS/cleanup.log" 2>&1
    podman --url "$PODMAN_URL" network rm "$NETWORK" >>"$ARTIFACTS/cleanup.log" 2>&1
    podman --url "$PODMAN_URL" ps -aq --no-trunc >"$ARTIFACTS/podman-after-cleanup.txt" 2>&1
    podman --url "$PODMAN_URL" network ls >"$ARTIFACTS/networks-after-cleanup.txt" 2>&1
    if [[ -s "$ARTIFACTS/podman-after-cleanup.txt" ]]; then
      echo "job-local Podman containers remain after cleanup" >>"$ARTIFACTS/cleanup.log"
      cleanup_rc=1
    fi
    if grep -Fq "$NETWORK" "$ARTIFACTS/networks-after-cleanup.txt"; then
      echo "job-local Podman network remains after cleanup" >>"$ARTIFACTS/cleanup.log"
      cleanup_rc=1
    fi
  fi
  if [[ -n "$PODMAN_PID" ]]; then
    kill -TERM "$PODMAN_PID" 2>/dev/null
    wait "$PODMAN_PID" 2>/dev/null
  fi
  cp "$STATE/gateway.log" "$ARTIFACTS/gateway.log" 2>/dev/null
  cp "$STATE/podman.log" "$ARTIFACTS/podman.log" 2>/dev/null
  rm -rf -- "$STATE"
  # Record the wrapped command and the cleanup separately (the script-led
  # wrapper folded them into one cleanup_exit, which misread job 4038).
  printf 'command_exit=%s\ncleanup_exit=%s\n' "$rc" "$cleanup_rc" >>"$ARTIFACTS/cleanup.log"
  if [[ "$rc" -eq 0 ]]; then rc=$cleanup_rc; fi
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

for tool in podman openshell openshell-gateway curl openssl; do
  command -v "$tool" >/dev/null || { echo "ERROR: required CI image tool missing: $tool" >&2; exit 127; }
done
if [[ -S "$SOCKET" ]]; then
  echo "ERROR: refusing to reuse an existing Podman socket: $SOCKET" >&2
  exit 1
fi
openshell --version | tee "$ARTIFACTS/openshell-version.txt"
openshell-gateway --version | tee "$ARTIFACTS/openshell-gateway-version.txt"
if ! openshell --version | grep -Fq "$VERSION" || \
   ! openshell-gateway --version | grep -Fq "$VERSION"; then
  echo "ERROR: expected OpenShell CLI and gateway $VERSION" >&2
  exit 1
fi

cat >"$STATE/storage.conf" <<CONF
[storage]
driver = "vfs"
graphroot = "/var/lib/containers/storage"
runroot = "/run/containers/storage"
CONF
export CONTAINERS_STORAGE_CONF="$STATE/storage.conf"
# Rootless user-namespace remapping is unavailable in the job container.
: > /etc/subuid
: > /etc/subgid
chmod 0777 /run/podman
podman system service --time=0 "$PODMAN_URL" >"$STATE/podman.log" 2>&1 &
PODMAN_PID=$!
for ((attempt = 0; attempt < 30; attempt++)); do
  podman --url "$PODMAN_URL" info >/dev/null 2>&1 && break
  kill -0 "$PODMAN_PID" 2>/dev/null || { cat "$STATE/podman.log" >&2; exit 1; }
  sleep 1
done
podman --url "$PODMAN_URL" info >/dev/null || { echo "Podman API did not become ready" >&2; exit 1; }

podman --url "$PODMAN_URL" pull -q "$SUPERVISOR_TAG" >/dev/null
podman --url "$PODMAN_URL" pull -q "$SANDBOX_IMAGE" >/dev/null
SUPERVISOR_DIGEST="$(podman --url "$PODMAN_URL" image inspect --format '{{.Digest}}' "$SUPERVISOR_TAG")"
SANDBOX_DIGEST="$(podman --url "$PODMAN_URL" image inspect --format '{{.Digest}}' "$SANDBOX_IMAGE")"
printf 'ci_image=quay.io/aipcc/agentic-ci/openshell:0.3.46\nsupervisor=%s@%s\nsandbox=%s@%s\n' \
  "$SUPERVISOR_TAG" "$SUPERVISOR_DIGEST" "${SANDBOX_IMAGE%@*}" "$SANDBOX_DIGEST" \
  | tee "$ARTIFACTS/image-pins.txt"

export XDG_CONFIG_HOME="$STATE/config" XDG_STATE_HOME="$STATE/state" XDG_DATA_HOME="$STATE/data"
mkdir -p "$XDG_CONFIG_HOME/openshell" "$XDG_STATE_HOME/openshell" "$XDG_DATA_HOME"
openshell-gateway generate-certs \
  --output-dir "$XDG_STATE_HOME/openshell/tls" \
  --server-san 127.0.0.1 \
  --server-san localhost \
  --server-san host.containers.internal >"$ARTIFACTS/certgen.log" 2>&1

cat >"$STATE/gateway.toml" <<CONF
[openshell]
version = 1
[openshell.gateway]
bind_address = "0.0.0.0:17670"
compute_drivers = ["podman"]
[openshell.drivers.podman]
socket_path = "$SOCKET"
supervisor_image = "$SUPERVISOR_TAG"
network_name = "$NETWORK"
grpc_endpoint = "https://host.containers.internal:17670"
default_image = "$SANDBOX_IMAGE"
image_pull_policy = "missing"
guest_tls_ca = "$XDG_STATE_HOME/openshell/tls/ca.crt"
guest_tls_cert = "$XDG_STATE_HOME/openshell/tls/client/tls.crt"
guest_tls_key = "$XDG_STATE_HOME/openshell/tls/client/tls.key"
CONF

env -u KUBERNETES_SERVICE_HOST -u KUBERNETES_SERVICE_PORT -u KUBERNETES_PORT \
  openshell-gateway \
    --config "$STATE/gateway.toml" \
    --bind-address 0.0.0.0 \
    --health-port 17671 \
    --tls-cert "$XDG_STATE_HOME/openshell/tls/server/tls.crt" \
    --tls-key "$XDG_STATE_HOME/openshell/tls/server/tls.key" \
    --tls-client-ca "$XDG_STATE_HOME/openshell/tls/ca.crt" \
    --enable-mtls-auth true \
    --db-url "sqlite:$STATE/openshell.db?mode=rwc" \
    --log-level info \
    --drivers podman >"$STATE/gateway.log" 2>&1 &
GATEWAY_PID=$!
for ((attempt = 0; attempt < 90; attempt++)); do
  curl -fsS http://127.0.0.1:17671/healthz >/dev/null 2>&1 && break
  kill -0 "$GATEWAY_PID" 2>/dev/null || { cat "$STATE/gateway.log" >&2; exit 1; }
  sleep 2
done
curl -fsS http://127.0.0.1:17671/healthz >/dev/null || { echo "OpenShell gateway health check failed" >&2; exit 1; }
openshell gateway add "https://127.0.0.1:17670" --local --name "$NAME"
openshell gateway select "$NAME"
openshell settings set --global --key providers_v2_enabled --value true --yes
echo "gateway: $NAME ready on network $NETWORK"

"$@"
