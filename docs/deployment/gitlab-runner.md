# Maintained GitLab runner

Breadboard uses one `glemu-k8s-runner` registration and one `gitlab-runner`
Deployment in namespace `gitlab-runner`. The manager uses the Kubernetes
executor and runs up to four concurrent jobs. Deployment inventory is
`deploy/k8s/21-gitlab-runner.yaml`; generated manager/configuration and
registration reconciliation are owned by `deploy/scripts/15-deploy-gitlab-runner.sh`.

## Job requirements

| Capability | Job image and requirements |
| --- | --- |
| Ordinary CI | Default `alpine:3.20`, or the workflow's selected image |
| Native strategy | Native UBI image with its existing Claude/Python setup; existing Vertex and Jira CI variables |
| Nested Podman | Image supplies Podman, shell, CA roots; use validated `vfs` storage and job-local paths |
| Fullsend/OpenShell | `quay.io/aipcc/agentic-ci/openshell:0.3.46`, pinned feature Fullsend build and sandbox/supervisor images from the strategy fixture |

Tags are `k8s-incluster,aipcc-small-x86_64`. Untagged jobs are rejected by
`run_untagged=false`; tags select eligible jobs, not different security settings.
Jobs mount the local CA read-only at `/etc/gitlab-runner/certs/ca.crt`.
Combine it with public roots when contacting public GitHub or other public sites.

The validated runner setting is **`privileged=true` for every job**, including
ordinary/native jobs and helper containers. This permits nested Podman mounts,
cgroups and sandbox networking. Treat workflows using this runner as trusted
platform workloads; OpenShell policy governs sandbox operations, while the
outer privileged CI container retains its Kubernetes/node privilege boundary.
The manager itself does not need privileged mode. Narrowing privileges requires
new validation; tags do not provide that isolation within this registration.

Each job pod gets independent emptyDirs at `/var/lib/containers` and
`/run/containers`. There is no host engine/socket or shared hostPath mount.
Fullsend creates a job-specific network, gateway name, certificate/database
state and sandbox. Equal socket paths or gateway ports in different pods do
not share runtime state. Collect artifacts before teardown; do not archive
engine storage, gateway keys/databases, the target checkout or credentials.

## Deployment and reset

From the repository root:

```bash
make host-deploy-gitlab-runner
# Exercise registration reset without wiping service data:
PROJECT_ROOT="$PWD" bash deploy/scripts/clean-all.sh --gitlab-runner-only
```

Deployment pauses all registrations, waits up to `RUNNER_DRAIN_TIMEOUT`
(default 180 seconds) for assigned work to finish, stops manager pods, removes
experiment managers/resources, and reuses the maintained registration/token.
Duplicate registrations are removed only after draining. Repeated deployment
leaves one registration and one manager. Manager strategy is `Recreate`.
The runner namespace is reserved for these managers and their CI job pods.

The runner-only reset invalidates registrations and rebuilds config/CA using
the same deployment path. Projects, job history, Jira and results remain intact.
The full `clean-all.sh` path drains before stopping/wiping the emulator, then
uses this same deployment script against its empty runner database. Full reset
still requires its existing explicit wipe confirmation or `--yes`.

Failures leave runners paused rather than deleting active work or reporting
success. Inspect the reported active job IDs/live pods, let jobs finish, then
rerun deployment. A rollout failure must be resolved before registration resume.

## Maintenance and rollback

```bash
kubectl get deployment,pods -n gitlab-runner
kubectl logs -n gitlab-runner deployment/gitlab-runner
# Native strategy workflow remains on strat-pipeline main.
# Disable nested capabilities if reverting to ordinary/native CI only:
PROJECT_ROOT="$PWD" RUNNER_PRIVILEGED=false bash deploy/scripts/15-deploy-gitlab-runner.sh
# Restore the validated default:
make host-deploy-gitlab-runner
```

`RUNNER_TAGS`, `RUNNER_IMAGE`, `RUNNER_MANAGER_IMAGE`, `RUNNER_RUN_UNTAGGED`
and `RUNNER_PRIVILEGED` are supported deployment overrides. Defaults preserve
the platform tags and untagged behavior. Disabling privilege prevents the
validated Podman/OpenShell path; use native strategy `main` for workflow rollback.
Never print the runner token or commit runtime configuration/credentials.

The reproducible capability fixture is
`var/demos/fullsend-entrypoint-poc/runner-validation/`; it checks ordinary CI,
native setup/processed-issue protection, nested execution and two overlapping
OpenShell jobs. The M6 task records real Vertex strategy execution separately.
