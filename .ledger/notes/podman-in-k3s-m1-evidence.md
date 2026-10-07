# M1: Podman inside k3s evidence

**Result: pass.** Tested 2026-10-05 UTC in the configured `default` k3s
context. No OpenShell, agent calls, or strategy processing were involved.

## Image and configuration

- Outer job image: `quay.io/aipcc/agentic-ci/podman:latest`, resolved by the
  direct pod to `quay.io/aipcc/agentic-ci/podman@sha256:672706f01b9d7155d3e4595d7920d6608b7f462674fd1bfcaf5c80ea7e802784`.
- Podman version: `5.8.2`.
- Inner test image: `docker.io/library/alpine:3.20`, image/config digest
  `sha256:bf8527eb54c3680e728d5b4b383a8ba730d72dae7236fbc8dff97ed6b224a731`.
- Storage: VFS; graphroot `/var/lib/containers/storage`, runroot
  `/run/containers/storage`; both are backed by pod-local `emptyDir` storage.
- Direct pod: `securityContext.privileged: true`, no added capability list,
  host PID and host networking unset. The unprivileged/default-permission pod was
  also tried and failed as detailed below.
- Nested Podman: `--network=host --cgroups=disabled`. In this configuration,
  the inner container uses the outer Kubernetes pod's network namespace.
- GitLab job: official GitLab Runner Kubernetes executor `19.1.1`, using a
  temporary runner tagged `podman-m1`; that runner's configuration had
  `privileged = true`. It used the same outer image reference, and Kubernetes
  events confirmed it pulled that image. The executor deleted job pods before
  their container `imageID` could be recorded; the digest above is from the
  direct pod pull of the same image reference during this run.

## Results

- With runner-equivalent unprivileged pod permissions and default Podman
  networking, Podman pulled the inner image but failed before starting it:
  `pasta` could not open `/dev/net/tun`.
- Setting inner `--network=host` bypassed the TUN requirement, then `crun`
  failed because `/sys/fs/cgroup/cgroup.subtree_control` is read-only.
- Adding `--cgroups=disabled` exposed the next restriction: mounting `/proc`
  failed with `Operation not permitted`. This establishes that the ordinary
  job security context is insufficient.
- In the isolated privileged pod, Podman pulled and ran the inner Alpine
  container, wrote `nested.txt` through a workspace bind mount, and the outer
  job read the expected content. A second inner command exited 37, which
  Podman propagated. An inner container resolved `quay.io` through cluster DNS
  (`10.43.0.10`) and completed `wget https://example.com/`.
- Cleanup removed the named inner containers and pruned images/storage; the
  script verified `podman ps -aq` was empty. An `EXIT` trap also performed
  cleanup after failed launch attempts. Deleting each disposable pod removed
  its `emptyDir` runtime state.
- The direct smoke passed in a fresh pod after deleting the first test pods,
  and passed again in a third fresh pod while recording Podman `5.8.2`.
- The same smoke script passed through GitLab's Kubernetes executor twice:
  pipeline `1980`, job `3846`; and pipeline `1981`, job `3847`. Both traces
  contained `nested-podman-ok`, `nested-dns-https-ok`, and
  `M1_SMOKE_PASS`; the artifact `nested.txt` was uploaded. Runner traces named
  `podman-m1-k8s-runner`. The emulator's job API returns the generic runner
  description for these jobs, so the trace and runner-manager log establish
  the actual assignment.
- During initial setup, a job started after only the CI YAML had been
  committed and failed while the second test file was still being added. The
  subsequent jobs ran with both files present and passed.

## Reproduction

From the Breadboard root, use the files in
[`var/demos/fullsend-entrypoint-poc/podman-smoke/`](../../var/demos/fullsend-entrypoint-poc/podman-smoke/).

Direct baseline attempt:

```sh
kubectl apply -f var/demos/fullsend-entrypoint-poc/podman-smoke/baseline-pod.yaml
kubectl wait --for=condition=Ready pod/podman-smoke-baseline -n ai-pipeline --timeout=180s
kubectl exec -i -n ai-pipeline pod/podman-smoke-baseline -- sh -s \
  < var/demos/fullsend-entrypoint-poc/podman-smoke/smoke.sh
```

Passing isolated pod attempt:

```sh
kubectl apply -f var/demos/fullsend-entrypoint-poc/podman-smoke/privileged-pod.yaml
kubectl wait --for=condition=Ready pod/podman-smoke-privileged -n ai-pipeline --timeout=180s
kubectl get pod podman-smoke-privileged -n ai-pipeline \
  -o jsonpath='{.status.containerStatuses[0].imageID}'
kubectl exec -i -n ai-pipeline pod/podman-smoke-privileged -- sh -c \
  'SMOKE_NETWORK_MODE=host SMOKE_CGROUPS_MODE=disabled sh -s' \
  < var/demos/fullsend-entrypoint-poc/podman-smoke/smoke.sh
kubectl delete pod podman-smoke-privileged -n ai-pipeline --wait=true
```

The GitLab run used `gitlab-runner-template.yaml`, `register-runner.py`,
`gitlab-ci.yml`, `gitlab-pipeline.py`, and `smoke.sh`. The test branch was
`podman-m1-validation-1791162517` in project `admin/ci-testing` (ID 1). The
temporary branches, runner registration, token secret, ConfigMap, Deployment,
and all smoke pods were removed after evidence collection.

## Limits

The passing setup requires a privileged job pod and shares the outer pod's
network namespace for inner containers. M1 proves nested Podman execution,
workspace mounts, outbound DNS/HTTPS, cleanup, and fresh-pod repeatability. It
does not establish OpenShell provider compatibility, network isolation, or
whether this privilege model is acceptable for the later sandbox design.
