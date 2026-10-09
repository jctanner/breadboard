#!/bin/sh
set -eu

IMAGE="${SMOKE_IMAGE:-docker.io/library/alpine:3.20}"
WORKSPACE="${SMOKE_WORKSPACE:-/workspace}"
STORAGE_CONF=/etc/containers/storage.conf
SMOKE_NETWORK_MODE="${SMOKE_NETWORK_MODE:-}"
SMOKE_CGROUPS_MODE="${SMOKE_CGROUPS_MODE:-}"

podman_run() {
  if [ -n "$SMOKE_CGROUPS_MODE" ] && [ -n "$SMOKE_NETWORK_MODE" ]; then
    podman run --cgroups="$SMOKE_CGROUPS_MODE" --network="$SMOKE_NETWORK_MODE" "$@"
  elif [ -n "$SMOKE_CGROUPS_MODE" ]; then
    podman run --cgroups="$SMOKE_CGROUPS_MODE" "$@"
  elif [ -n "$SMOKE_NETWORK_MODE" ]; then
    podman run --network="$SMOKE_NETWORK_MODE" "$@"
  else
    podman run "$@"
  fi
}

# Match rfe-autofixer's Podman setup while keeping each run's state in this pod.
: > /etc/subuid
: > /etc/subgid
mkdir -p "$(dirname "$STORAGE_CONF")" /var/lib/containers/storage /run/containers/storage
mkdir -p "$WORKSPACE"
printf '[storage]\ndriver = "vfs"\ngraphroot = "/var/lib/containers/storage"\nrunroot = "/run/containers/storage"\n' > "$STORAGE_CONF"

cleanup() {
  podman rm -f podman-smoke-ok podman-smoke-fail podman-smoke-network 2>/dev/null || true
  podman system prune --all --force >/dev/null 2>&1 || true
}
trap cleanup EXIT HUP INT TERM

podman --version
podman pull "$IMAGE"

# Inner container exits successfully and writes through a bind-mounted workspace.
podman_run --name podman-smoke-ok --volume "$WORKSPACE:/workspace" "$IMAGE" \
  sh -ec 'printf "nested-podman-ok\\n" > /workspace/nested.txt; cat /workspace/nested.txt'
test "$(cat "$WORKSPACE/nested.txt")" = nested-podman-ok

# The outer podman client must return the inner process's nonzero status.
set +e
podman_run --name podman-smoke-fail "$IMAGE" sh -c 'exit 37'
failure_status=$?
set -e
test "$failure_status" -eq 37

# Check cluster DNS and outbound HTTPS from the inner container.
podman_run --name podman-smoke-network "$IMAGE" sh -ec \
  'nslookup quay.io; wget -q -O /dev/null https://example.com/; echo nested-dns-https-ok'

podman rm -f podman-smoke-ok podman-smoke-fail podman-smoke-network
test -z "$(podman ps -aq)"
podman system prune --all --force
test -z "$(podman ps -aq)"
printf 'M1_SMOKE_PASS image=%s workspace=%s network_mode=%s cgroups_mode=%s\n' "$IMAGE" "$WORKSPACE" "${SMOKE_NETWORK_MODE:-default}" "${SMOKE_CGROUPS_MODE:-default}"
