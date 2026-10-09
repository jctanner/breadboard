#!/bin/sh
set -eu

VERSION=0.0.116
SHA=d1155aa70042d3e2ee49dbfa15346b108b7c1d92
ARTIFACTS="$CI_PROJECT_DIR/openshell-artifacts"
STATE="$CI_PROJECT_DIR/.openshell-m2"
SOCKET=/run/podman/podman.sock
NAME="m2-${CI_JOB_ID:-local}"
mkdir -p "$ARTIFACTS" "$STATE" /run/podman /var/lib/containers/storage /run/containers/storage
: > /etc/subuid
: > /etc/subgid
chmod 0777 /run/podman
printf '[storage]\ndriver = "vfs"\ngraphroot = "/var/lib/containers/storage"\nrunroot = "/run/containers/storage"\n' > /etc/containers/storage.conf

gateway_pid=
podman_pid=
cleanup() {
  status=$?
  set +e
  if command -v openshell >/dev/null 2>&1; then
    openshell sandbox delete "$NAME" >> "$ARTIFACTS/cleanup.log" 2>&1
  fi
  cp "$STATE/gateway.log" "$ARTIFACTS/gateway.log" 2>/dev/null
  cp "$STATE/podman.log" "$ARTIFACTS/podman.log" 2>/dev/null
  if [ -n "$gateway_pid" ]; then
    kill -TERM "$gateway_pid" 2>/dev/null
    wait "$gateway_pid" 2>/dev/null
  fi
  podman --url "unix://$SOCKET" ps -a --no-trunc > "$ARTIFACTS/podman-containers.txt" 2>&1
  podman --url "unix://$SOCKET" network ls > "$ARTIFACTS/podman-networks.txt" 2>&1
  podman --url "unix://$SOCKET" rm -f "$NAME" >> "$ARTIFACTS/cleanup.log" 2>&1
  podman --url "unix://$SOCKET" network rm "openshell-m2-$CI_JOB_ID" >> "$ARTIFACTS/cleanup.log" 2>&1
  podman --url "unix://$SOCKET" system prune --force >> "$ARTIFACTS/cleanup.log" 2>&1
  podman --url "unix://$SOCKET" ps -aq --no-trunc > "$ARTIFACTS/podman-after-cleanup.txt" 2>&1
  podman --url "unix://$SOCKET" network ls > "$ARTIFACTS/networks-after-cleanup.txt" 2>&1
  if [ -s "$ARTIFACTS/podman-after-cleanup.txt" ] || grep -Eq "openshell-m2-$CI_JOB_ID" "$ARTIFACTS/networks-after-cleanup.txt"; then
    echo 'job-owned Podman containers or network remain after cleanup' >> "$ARTIFACTS/cleanup.log"
    status=1
  fi
  cp "$STATE/gateway.log" "$ARTIFACTS/gateway.log" 2>/dev/null
  cp "$STATE/podman.log" "$ARTIFACTS/podman.log" 2>/dev/null
  if command -v openshell >/dev/null 2>&1; then
    openshell gateway remove m2 2>>"$ARTIFACTS/cleanup.log"
  fi
  if [ -n "$podman_pid" ]; then
    kill -TERM "$podman_pid" 2>/dev/null
    wait "$podman_pid" 2>/dev/null
  fi
  printf 'cleanup_exit=%s\n' "$status" >> "$ARTIFACTS/cleanup.log"
  exit "$status"
}
trap cleanup EXIT HUP INT TERM

echo "M2_JOB=$CI_JOB_ID OpenShell=$VERSION source=$SHA"
podman --version | tee "$ARTIFACTS/podman-version.txt"
podman system info > "$ARTIFACTS/podman-info.txt"
podman system service --time=0 "unix://$SOCKET" > "$STATE/podman.log" 2>&1 &
podman_pid=$!
i=0
until podman --url "unix://$SOCKET" info >/dev/null 2>&1; do
  i=$((i + 1)); [ "$i" -lt 30 ] || { cat "$STATE/podman.log"; exit 1; }
  sleep 1
done
podman --url "unix://$SOCKET" info --format json > "$ARTIFACTS/podman-api-info.json"

# The pinned Fullsend release installer installs both CLI and gateway packages.
curl -fsSL "https://raw.githubusercontent.com/NVIDIA/OpenShell/$SHA/install.sh" -o "$STATE/install.sh"
OPENSHELL_VERSION="v$VERSION" sh "$STATE/install.sh" > "$ARTIFACTS/install.log" 2>&1
cat "$ARTIFACTS/install.log"
openshell --version | tee "$ARTIFACTS/openshell-version.txt"
command -v openshell-gateway | tee "$ARTIFACTS/gateway-binary.txt"
SUPERVISOR_TAG="ghcr.io/nvidia/openshell/supervisor:$VERSION"
SANDBOX_TAG=ghcr.io/nvidia/openshell-community/sandboxes/base:latest
podman --url "unix://$SOCKET" pull "$SUPERVISOR_TAG"
podman --url "unix://$SOCKET" pull "$SANDBOX_TAG"
SUPERVISOR_IMAGE=$(podman --url "unix://$SOCKET" image inspect --format '{{index .RepoDigests 0}}' "$SUPERVISOR_TAG")
SANDBOX_IMAGE=$(podman --url "unix://$SOCKET" image inspect --format '{{index .RepoDigests 0}}' "$SANDBOX_TAG")
printf 'supervisor=%s\nsandbox=%s\n' "$SUPERVISOR_IMAGE" "$SANDBOX_IMAGE" | tee "$ARTIFACTS/image-pins.txt"
mkdir -p "$STATE/jwt"
umask 077
openssl genpkey -algorithm Ed25519 -out "$STATE/jwt/signing.pem" >/dev/null 2>&1
openssl pkey -in "$STATE/jwt/signing.pem" -pubout -out "$STATE/jwt/public.pem" >/dev/null 2>&1
openssl rand -hex 16 > "$STATE/jwt/kid"
openshell-gateway generate-certs --output-dir "$STATE/pki" --server-san host.containers.internal > "$ARTIFACTS/certgen.log" 2>&1

cat > "$STATE/gateway.toml" <<EOF
[openshell]
version = 1
[openshell.gateway]
name = "$NAME"
bind_address = "0.0.0.0:17670"
health_bind_address = "0.0.0.0:17671"
compute_drivers = ["podman"]
disable_tls = true
[openshell.gateway.auth]
allow_unauthenticated_users = true
[openshell.gateway.gateway_jwt]
signing_key_path = "$STATE/jwt/signing.pem"
public_key_path = "$STATE/jwt/public.pem"
kid_path = "$STATE/jwt/kid"
gateway_id = "$NAME"
ttl_secs = 0
[openshell.drivers.podman]
socket_path = "$SOCKET"
default_image = "$SANDBOX_IMAGE"
image_pull_policy = "missing"
network_name = "openshell-m2-$CI_JOB_ID"
grpc_endpoint = "http://host.containers.internal:17670"
supervisor_image = "$SUPERVISOR_IMAGE"
guest_tls_ca = "$STATE/pki/ca.crt"
guest_tls_cert = "$STATE/pki/client/tls.crt"
guest_tls_key = "$STATE/pki/client/tls.key"
EOF

export XDG_CONFIG_HOME="$STATE/config" XDG_STATE_HOME="$STATE/state" XDG_DATA_HOME="$STATE/data"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_STATE_HOME" "$XDG_DATA_HOME"
env -u KUBERNETES_SERVICE_HOST -u KUBERNETES_SERVICE_PORT -u KUBERNETES_PORT \
  openshell-gateway --config "$STATE/gateway.toml" > "$STATE/gateway.log" 2>&1 &
gateway_pid=$!
i=0
until curl -fsS http://127.0.0.1:17671/healthz >/dev/null 2>&1; do
  i=$((i + 1)); [ "$i" -lt 90 ] || { cat "$STATE/gateway.log"; exit 1; }
  kill -0 "$gateway_pid" 2>/dev/null || { cat "$STATE/gateway.log"; exit 1; }
  sleep 2
done
openshell gateway add http://127.0.0.1:17670 --local --name m2
openshell gateway select m2

podman --url "unix://$SOCKET" image inspect "$SUPERVISOR_IMAGE" > "$ARTIFACTS/supervisor-image.json"
podman --url "unix://$SOCKET" image inspect "$SANDBOX_IMAGE" > "$ARTIFACTS/sandbox-image.json"

openshell sandbox create --name "$NAME" --detach --policy "$CI_PROJECT_DIR/policy.yaml" -- /bin/sleep 3600
openshell sandbox exec --name "$NAME" --no-tty -- sh -ec 'mkdir -p /sandbox/output; printf "openshell-m2-artifact-ok\\n" > /sandbox/output/result.txt; cat /sandbox/output/result.txt' | tee "$ARTIFACTS/sandbox-command.log"
openshell sandbox exec --name "$NAME" --no-tty -- /usr/bin/curl -fsS --max-time 20 https://api.github.com/zen > "$ARTIFACTS/allowed-network.txt"
if openshell sandbox exec --name "$NAME" --no-tty -- /usr/bin/curl -fsS --max-time 10 https://example.com/ > "$ARTIFACTS/disallowed-network.txt" 2> "$ARTIFACTS/disallowed-network.log"; then
  echo 'disallowed network unexpectedly succeeded' >&2
  exit 1
fi
openshell sandbox download "$NAME" output "$ARTIFACTS/exported"
test "$(cat "$ARTIFACTS/exported/result.txt")" = openshell-m2-artifact-ok
echo "M2_SMOKE_PASS job=$CI_JOB_ID openshell=$VERSION sandbox=$NAME"
