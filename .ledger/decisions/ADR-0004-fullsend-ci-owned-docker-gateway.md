# ADR-0004: Each Fullsend POC job owns its OpenShell gateway

## Status

Accepted requirement, supplied by the user after discussion with Fullsend
core developers on 2026-10-04.

Amended by subsequent user direction: Podman inside k3s is the first milestone
and gates all later POC work. M2 passed with the Podman provider and selected
it for the remaining POC. Docker compatibility remains untested.

## Decision

Each CI job bootstraps an OpenShell gateway using the Podman compute provider,
runs its harness, collects artifacts, and cleans up its gateway and sandboxes.
The POC must not depend on Breadboard's central OpenShell deployment.

## Consequences

M2 demonstrated the Podman driver's required API socket, VFS storage,
cgroups-v2 runtime, supervisor callback, policy-enforced bridge networking,
artifact export, and cleanup in a disposable Kubernetes-executor job. It
required a privileged job pod and job-local emptyDir storage; the existing
maintained runner was not changed. Since the final outcome requires one
maintained Kubernetes runner, consolidation must validate the privilege impact
on ordinary jobs before adoption. Existing strategy jobs did not need
privilege. Docker compatibility is untested and is not part of the selected
POC path.

See the [POC plan](../plans/fullsend-entrypoint-strategy-poc.md) for feasibility,
isolation, networking, and cleanup checks.
