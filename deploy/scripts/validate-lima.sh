#!/usr/bin/env bash
set -euo pipefail
: "${PROJECT_ROOT:?PROJECT_ROOT is required}"
cd "${PROJECT_ROOT}/deploy/validation"
bash test-cluster.sh
bash test-certificates.sh
