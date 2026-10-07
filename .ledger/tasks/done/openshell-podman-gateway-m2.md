# M2: Prove a job-owned OpenShell Podman gateway

## Goal

Prove OpenShell can bootstrap a gateway inside one disposable GitLab
Kubernetes-executor job using the Podman compute driver, create and operate a
stock sandbox, enforce network policy, export an artifact, and clean up all
job-owned resources. This is separate from M1 and includes no model calls,
strategy processing, or central OpenShell gateway.

## Provider scope

Use the Podman provider for this experiment based on M1 and the Fullsend/
rfe-autofixer references. M2 selected Podman for the remaining POC after
demonstrating the required sandbox behavior. Docker compatibility remains
untested. The final shared-runner privilege impact is recorded in the M2
evidence and remains part of runner consolidation.

## Acceptance criteria

- [x] Run through a real GitLab Kubernetes-executor job with a dedicated
  temporary runner/configuration; do not alter the maintained runner yet.
- [x] Each job starts its own Podman API service and OpenShell gateway using
  job-local state/storage, without mounting a host container-engine socket.
- [x] Pin and record the OpenShell CLI/gateway commit and version, supervisor
  image version/digest, and stock sandbox image digest.
- [x] Verify the gateway socket/API, bind paths, cgroups/kernel assumptions,
  supervisor connection, sandbox callback, and nested network routing.
- [x] Create a stock sandbox, run a command, export an artifact, and verify
  that policy-allowed traffic succeeds while disallowed traffic is blocked.
- [x] Collect job/gateway logs before teardown. Verify graceful cleanup of the
  gateway, sandbox container/workspace, network, and job storage.
- [x] Record configuration, commands, job/pipeline IDs, image digests, and
  pass/failure evidence in the ledger.

## Evidence location

`var/demos/fullsend-entrypoint-poc/openshell-smoke/`

## Status

Complete. OpenShell/Fullsend implementation and strategy migration may
proceed. Final shared-runner security settings remain gated on consolidation.
