# ADR-0005: One platform runner for GitLab CI

## Status

Accepted by explicit user direction.

## Decision

The plan must finish with one maintained runner registration and deployment
for `gitlab.local`, supporting ordinary CI, native strategy jobs, and the
validated Podman/OpenShell job requirements. Extend the existing Kubernetes
runner; do not retain separate permanent runners for individual capabilities.

## Consequences

Temporary runners may isolate validation work, but their configuration must
be incorporated into the platform runner and those temporary resources removed.
Job images supply the tools; the runner supplies the required execution
settings. One runner may execute multiple concurrent jobs, each owning its
gateway, sandbox, and temporary state. Deployment and reset must not create
duplicate registrations. Record and test the final privilege settings as
part of the shared runner configuration.

See the [POC plan](../plans/fullsend-entrypoint-strategy-poc.md).

## Implementation evidence — M7, 2026-10-06

The authoritative deployment now reuses one paused/drained registration and
removes duplicates before resuming one Recreate manager. Shared jobs use
privileged=true and separate pod emptyDirs for container storage/runtime.
Tags and run_untagged=false are preserved. Capability pipeline 2042 passed
ordinary, native setup, nested Podman and overlapping job-owned OpenShell
checks. Live registration reset and repeat deployment converge on one runner;
full clean-all control flow was checked with mocked kubectl. See the
[M7 task](../tasks/done/consolidate-gitlab-runner-capabilities.md) for exact
reset scope and known DNS/emulator limitations, and
[maintenance documentation](../../docs/deployment/gitlab-runner.md).
