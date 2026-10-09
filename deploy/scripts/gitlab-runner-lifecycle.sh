#!/usr/bin/env bash
# Shared by deployment and reset; never source a runtime token into logs.

runner_registry() {
  kubectl exec -i -n ai-pipeline deployment/gitlab-emulator -c gitlab-emulator -- \
    python3 - "$@" < "${PROJECT_ROOT}/deploy/scripts/gitlab-runner-registration.py"
}

runner_drain_and_stop() {
  runner_registry drain --drain-timeout "${RUNNER_DRAIN_TIMEOUT:-180}"
  # The runner namespace is dedicated to GitLab managers/job pods. Stop all
  # managers only after jobs drain, including leftover experiment managers.
  local manager managers selector
  managers=$(kubectl get deployment -n "$RUNNER_NAMESPACE" -o name)
  while IFS= read -r manager; do
    [[ -n "$manager" ]] || continue
    kubectl scale -n "$RUNNER_NAMESPACE" "$manager" --replicas=0
    kubectl rollout status -n "$RUNNER_NAMESPACE" "$manager" --timeout=120s
    selector=$(kubectl get -n "$RUNNER_NAMESPACE" "$manager" -o json | python3 -c '
import json,sys
print(",".join(k+"="+v for k,v in json.load(sys.stdin)["spec"]["selector"]["matchLabels"].items()))
')
    [[ -n "$selector" ]] || { echo "Manager has no label selector" >&2; return 1; }
    kubectl wait --for=delete pod -n "$RUNNER_NAMESPACE" -l "$selector" --timeout=120s
  done <<< "$managers"
  # Running job pods can outlive the manager. Refuse deletion until drained.
  local remaining
  remaining=$(kubectl get pods -n "$RUNNER_NAMESPACE" -o json | python3 -c '
import json,sys
pods=json.load(sys.stdin)["items"]
print(sum(p["status"]["phase"] in {"Pending", "Running", "Unknown"} for p in pods))
')
  if [[ "$remaining" != 0 ]]; then
    echo "ERROR: live pods remain in runner namespace; leave paused and inspect" >&2
    return 1
  fi
}

runner_remove_experiments() {
  local resource resources
  resources=$(kubectl get deployment -n "$RUNNER_NAMESPACE" -o name)
  while IFS= read -r resource; do
    [[ -n "$resource" ]] || continue
    if [[ "$resource" != deployment.apps/gitlab-runner ]]; then
      kubectl delete -n "$RUNNER_NAMESPACE" "$resource"
    fi
  done <<< "$resources"
  # Experiment resources from M1/M2/M4.1/M4.2; the maintained CA is retained.
  kubectl delete configmap -n "$RUNNER_NAMESPACE" \
    podman-m1-runner-config openshell-m2-runner-config \
    openshell-m41-runner-config openshell-m42-runner-config --ignore-not-found
  kubectl delete secret -n "$RUNNER_NAMESPACE" \
    podman-m1-runner-token openshell-m2-runner-token \
    openshell-m41-runner-token openshell-m42-runner-token \
    m41-jira-credentials m42-jira-credentials --ignore-not-found
}
