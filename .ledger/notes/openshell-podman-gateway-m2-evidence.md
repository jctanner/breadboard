# M2: OpenShell Podman gateway evidence

## Result

**M2 passed on 2026-10-05 UTC.** A disposable GitLab Kubernetes-executor job
bootstrapped its own Podman API service and OpenShell gateway, created a stock
sandbox, exercised its supervisor and network policy, exported an artifact,
and removed its sandbox, per-job network, gateway registration, and runtime
containers. No host container-engine socket or central OpenShell gateway was
used. The job had no model credentials or strategy work.

Final validation was project `admin/ci-testing` (ID 1), pipeline `1989`, job
`3855`, branch `openshell-m2-validation-1791165390`. The job trace identifies
the temporary runner `openshell-m2-k8s-runner` and contains
`M2_SMOKE_PASS job=3855 openshell=0.0.116 sandbox=m2-3855`.

## Runtime and image pins

- Job image: `quay.io/aipcc/agentic-ci/podman@sha256:672706f01b9d7155d3e4595d7920d6608b7f462674fd1bfcaf5c80ea7e802784`.
- Podman API: 5.8.2, API 5.8.2, VFS store, cgroups v2, netavark; the outer
  kernel reported `7.2.8-200.fc44.x86_64`.
- OpenShell source pin from Fullsend: commit
  `d1155aa70042d3e2ee49dbfa15346b108b7c1d92`; the job installed CLI and
  gateway RPMs from release `v0.0.116`. Both report version `0.0.116`.
- Supervisor: `ghcr.io/nvidia/openshell/supervisor@sha256:1f02f37ee9e16c3b1245b80899a954fc8198099494d4fe0cd1e891fc63adf127`
  (tag `0.0.116`).
- Stock sandbox: `ghcr.io/nvidia/openshell-community/sandboxes/base@sha256:aeef1c63f00e2913ea002ccb3aaf925f338b5c5d70e63576f0d95c16a138044e`
  (resolved from `latest` at job execution).

The final job artifact archive is available at
`/tmp/openshell-m2-3855-artifacts.zip` for this work session. Its extracted
files include the gateway log, Podman API info, image inspection, policy
results, downloaded output, and before/after cleanup snapshots.

## Configuration and checks

The temporary runner used the pinned M1 job image, Kubernetes executor,
`privileged = true`, and fresh `emptyDir` volumes at `/var/lib/containers`
and `/run/containers` for each job pod. Podman exposed only its job-local
socket at `/run/podman/podman.sock`. Gateway state and the socket were inside
the job; there was no hostPath or socket mount. The outer job pod used its
ordinary Kubernetes network. OpenShell created the per-job bridge network
`openshell-m2-3855`.

The job launched `podman system service` and `openshell-gateway` directly;
it did not use systemd. The gateway used `compute_drivers = ["podman"]`,
`grpc_endpoint = "http://host.containers.internal:17670"`, a dedicated
health listener on port 17671, and the matching v0.0.116 supervisor image. CLI
traffic used the job-local endpoint `http://127.0.0.1:17670`. The gateway log
confirms the Podman API connection, cgroups v2, bridge network, and successful
supervisor RelayStream/ForwardTcp calls from the sandbox.

The sandbox ran a shell command that wrote
`/sandbox/output/result.txt`; `openshell sandbox download` exported it and the
job checked the exact contents `openshell-m2-artifact-ok`. The policy allowed
the sandbox's `/usr/bin/curl` to GET `https://api.github.com/zen` (response:
`Speak like a human.`). The same binary's request to `https://example.com/`
was blocked with HTTP 403, and the job required that attempt to fail.

The exit trap saved gateway and Podman logs before shutdown, deleted the
sandbox, removed the unique network, pruned only the job-local Podman store,
and removed the local gateway registration. The post-cleanup snapshot had no
containers and only Podman's default `podman` network. It recorded
`cleanup_exit=0`. The Kubernetes executor removed the completed job pod and
its emptyDirs; after test cleanup, the only pod in `gitlab-runner` was the
maintained `gitlab-runner` manager.

## Findings and limitations

- The Fullsend installer needs the `v` prefix in the release tag
  (`OPENSHELL_VERSION=v0.0.116`). It reports a non-fatal systemd user-service
  restart warning in the job; directly launching the gateway worked.
- A Kubernetes job pod exports `KUBERNETES_SERVICE_HOST` and related
  variables. OpenShell 0.0.116 then attempts in-cluster Kubernetes
  ServiceAccount JWT bootstrap, which requires a Kubernetes-driver config.
  The Podman gateway process must unset those variables so it does not mistake
  its local Podman backend for an OpenShell-in-Kubernetes deployment.
- The gateway health endpoint is on a separate health listener. The passing
  job configures `health_bind_address = "0.0.0.0:17671"` and probes
  `/healthz`; the primary API listener returns 404 for health paths.
- Rootful Podman, VFS, cgroups v2, netavark, a privileged job pod, and an
  isolated bridge were enough here. The passing configuration did not reuse
  M1's `--network=host` or `--cgroups=disabled` for sandbox containers.
- The temporary Kubernetes runner required `privileged = true`. The current
  maintained runner does not set this. With the required single Kubernetes
  runner, that setting is runner-wide rather than tag-specific; final runner
  consolidation must explicitly validate the privilege impact on ordinary
  jobs before applying it. M2 proves provider functionality, not that the
  eventual shared privilege posture is acceptable.
- Podman is selected as the provider for the remaining POC based on this
  evidence and the user's Podman-first direction. Docker compatibility remains
  untested.

## Reproduction

From the Breadboard root, inspect
`var/demos/fullsend-entrypoint-poc/openshell-smoke/`. Its helper creates a
dedicated test branch, commits the fixture, waits for the push pipeline, and
downloads job artifacts to `/tmp`. The successful IDs above and digest pins
are from the final job. The helper/runner are disposable; do not use them as a
permanent second runner.
