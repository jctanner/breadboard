#!/bin/bash
# Deploy an in-cluster GitLab Runner (Kubernetes executor) that polls
# the gitlab-emulator coordinator and creates CI job pods.

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"

RUNNER_NAME="${RUNNER_NAME:-glemu-k8s-runner}"
RUNNER_TAGS="${RUNNER_TAGS:-k8s-incluster,aipcc-small-x86_64}"
RUNNER_IMAGE="${RUNNER_IMAGE:-alpine:3.20}"
RUNNER_MANAGER_IMAGE="${RUNNER_MANAGER_IMAGE:-gitlab/gitlab-runner:v19.1.1}"
RUNNER_NAMESPACE="${RUNNER_NAMESPACE:-gitlab-runner}"
REGISTRATION_TOKEN="${REGISTRATION_TOKEN:-runner-registration-token}"
RUNNER_RUN_UNTAGGED="${RUNNER_RUN_UNTAGGED:-false}"
RUNNER_PRIVILEGED="${RUNNER_PRIVILEGED:-true}"
source "${PROJECT_ROOT}/deploy/scripts/gitlab-runner-lifecycle.sh"
[[ "$RUNNER_RUN_UNTAGGED" == true || "$RUNNER_RUN_UNTAGGED" == false ]]
[[ "$RUNNER_PRIVILEGED" == true || "$RUNNER_PRIVILEGED" == false ]]
# RBAC inventory and reset use this namespace; reject partial overrides.
[[ "$RUNNER_NAMESPACE" == gitlab-runner ]] || { echo "Unsupported runner namespace" >&2; exit 1; }
EMULATOR_URL="https://gitlab-emulator.ai-pipeline.svc.cluster.local"

echo "==> Deploying GitLab Runner (in-cluster Kubernetes executor)..."

# Step 1: Apply RBAC
echo "--- Creating namespace and RBAC ---"
kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/21-gitlab-runner.yaml"

# Step 2: Wait for gitlab-emulator to be ready
echo "--- Waiting for gitlab-emulator to be ready ---"
kubectl wait --for=condition=Available --timeout=120s \
  deployment/gitlab-emulator -n ai-pipeline || {
  echo "ERROR: gitlab-emulator deployment not ready"
  exit 1
}

for i in $(seq 1 15); do
  if kubectl exec -n ai-pipeline deployment/gitlab-emulator -- \
    python3 -c "import httpx; httpx.get('http://127.0.0.1:8000/api/v4').raise_for_status()" 2>/dev/null; then
    echo "  gitlab-emulator API is responding"
    break
  fi
  echo "  Waiting for gitlab-emulator API... ($i/15)"
  sleep 4
done

# Step 3: Pause/drain, then reuse one persisted registration (or create after reset).
# Existing registration tokens are recovered privately via the local emulator API.
echo "--- Draining and reconciling the maintained runner ---"
runner_drain_and_stop
runner_remove_experiments
RUNNER_TOKEN=$(runner_registry reconcile --name "$RUNNER_NAME" \
  --tags "$RUNNER_TAGS" --run-untagged "$RUNNER_RUN_UNTAGGED" \
  --registration-token "$REGISTRATION_TOKEN")
[[ -n "$RUNNER_TOKEN" ]] || { echo "ERROR: no runner token received" >&2; exit 1; }

# Step 4: Extract CA certificate
echo "--- Extracting CA certificate ---"
CA_CERT=$(kubectl get configmap internal-ca-cert \
  -n ai-pipeline \
  -o jsonpath='{.data.ca\.crt}' 2>/dev/null || true)

if [ -z "$CA_CERT" ]; then
  echo "ERROR: internal-ca-cert is required for verified runner TLS" >&2
  exit 1
fi

# Step 5: Build config.toml
echo "--- Building runner config ---"
CONFIG_TOML=$(cat <<EOF
concurrent = 4
check_interval = 3

[[runners]]
  name = "${RUNNER_NAME}"
  url = "${EMULATOR_URL}"
  token = "${RUNNER_TOKEN}"
  tls-ca-file = "/etc/gitlab-runner/certs/ca.crt"
  executor = "kubernetes"
  environment = ["GIT_SSL_CAINFO=/etc/gitlab-runner/certs/ca.crt"]

  [runners.kubernetes]
    namespace = "${RUNNER_NAMESPACE}"
    image = "${RUNNER_IMAGE}"
    privileged = ${RUNNER_PRIVILEGED}
    poll_timeout = 180
    service_account = "gitlab-runner"

    # Per-job emptyDirs: never hostPath or a shared container engine socket.
    [[runners.kubernetes.volumes.empty_dir]]
      name = "fullsend-podman-storage"
      mount_path = "/var/lib/containers"

    [[runners.kubernetes.volumes.empty_dir]]
      name = "fullsend-podman-run"
      mount_path = "/run/containers"

    [[runners.kubernetes.volumes.secret]]
      name = "gitlab-runner-ca"
      mount_path = "/etc/gitlab-runner/certs"
      read_only = true
EOF
)

# Step 6: Create ConfigMap and Secret
echo "--- Creating runner config and CA secret ---"
kubectl -n "${RUNNER_NAMESPACE}" create configmap gitlab-runner-config \
  --from-literal=config.toml="${CONFIG_TOML}" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "${RUNNER_NAMESPACE}" create secret generic gitlab-runner-ca \
  --from-literal=ca.crt="${CA_CERT}" --dry-run=client -o yaml | kubectl apply -f -

# Step 7: Deploy runner manager
echo "--- Deploying runner manager ---"
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gitlab-runner
  namespace: ${RUNNER_NAMESPACE}
  labels:
    app: gitlab-runner
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: gitlab-runner
  template:
    metadata:
      labels:
        app: gitlab-runner
    spec:
      serviceAccountName: gitlab-runner
      containers:
        - name: gitlab-runner
          image: ${RUNNER_MANAGER_IMAGE}
          imagePullPolicy: IfNotPresent
          command: ["gitlab-runner"]
          args:
            - run
            - --working-directory=/home/gitlab-runner
            - --config=/etc/gitlab-runner/config.toml
            - --service=gitlab-runner
            - --user=gitlab-runner
          volumeMounts:
            - name: runner-config
              mountPath: /etc/gitlab-runner/config.toml
              subPath: config.toml
              readOnly: true
            - name: runner-ca
              mountPath: /etc/gitlab-runner/certs
              readOnly: true
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
      volumes:
        - name: runner-config
          configMap:
            name: gitlab-runner-config
        - name: runner-ca
          secret:
            secretName: gitlab-runner-ca
EOF

# Step 8: Wait for deployment
echo "--- Waiting for runner manager to be ready ---"
kubectl rollout status deployment/gitlab-runner \
  -n "${RUNNER_NAMESPACE}" --timeout=120s
runner_registry resume --name "$RUNNER_NAME"

echo ""
echo "==> GitLab Runner deployed successfully"
echo ""
echo "Runner details:"
echo "  Name:       ${RUNNER_NAME}"
echo "  Tags:       ${RUNNER_TAGS}"
echo "  Namespace:  ${RUNNER_NAMESPACE}"
echo "  Executor:   kubernetes"
echo "  Job image:  ${RUNNER_IMAGE}"
echo "  Manager:    ${RUNNER_MANAGER_IMAGE}"
echo "  Untagged:   ${RUNNER_RUN_UNTAGGED}"
echo "  Privileged: ${RUNNER_PRIVILEGED} (applies to every job image)"
echo ""
echo "Check status:"
echo "  kubectl get pods -n ${RUNNER_NAMESPACE}"
echo "  kubectl logs -n ${RUNNER_NAMESPACE} -l app=gitlab-runner"
echo ""
echo "Verify runner is registered:"
echo "  curl --cacert /path/to/internal-ca.pem https://gitlab.local/api/v4/runners"
echo "  Visit https://gitlab.local/admin/runners"
