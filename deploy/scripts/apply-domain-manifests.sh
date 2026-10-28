#!/usr/bin/env bash
# Apply Kubernetes manifests parameterized with BREADBOARD_DOMAIN.
# When BREADBOARD_DOMAIN is unset or "local", manifests are applied unchanged.
# When BREADBOARD_DOMAIN is set (e.g. "bb.internal"), manifests are rendered
# with both .local and .${BREADBOARD_DOMAIN} SANs and routes before applying.
#
# Usage:
#   apply-domain-manifests.sh <file1.yaml> [file2.yaml ...]
#   apply-domain-manifests.sh --render <file1.yaml> [file2.yaml ...]
#   cat manifest.yaml | apply-domain-manifests.sh -

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN="${BREADBOARD_DOMAIN:-local}"

RENDER_ONLY=false
if [ "${1:-}" = "--render" ]; then
  RENDER_ONLY=true
  shift
fi

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 [--render] <manifest.yaml ...>"
  exit 1
fi

for file in "$@"; do
  if [ "$RENDER_ONLY" = true ]; then
    python3 "${SCRIPT_DIR}/render_domain_manifest.py" "$file" "$DOMAIN"
  else
    python3 "${SCRIPT_DIR}/render_domain_manifest.py" "$file" "$DOMAIN" | kubectl apply -f -
  fi
done
