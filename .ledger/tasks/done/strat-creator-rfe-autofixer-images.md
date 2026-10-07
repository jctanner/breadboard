# M4.1: Reuse rfe-autofixer's CI and sandbox images

## Goal

Update the pushed `feat/fullsend-strategy-entrypoint` branch in
`checkouts.fullsend_prototype/jctanner.strat-creator` to use the images selected
by rfe-autofixer's `autofix-rfe-stage-dry-fullsend` job. Remove the custom image
builds introduced in M4. Keep our Fullsend feature binary for entrypoint support.
See [ADR-0009](../../decisions/ADR-0009-reuse-rfe-autofixer-images.md).

## Reference image set

The inspected rfe-autofixer checkout is at `28bccc8`; its `.gitlab-ci.yml`
and imported `.fullsend` harness define three distinct image roles:

| Role | Reference |
| --- | --- |
| GitLab CI job | `quay.io/aipcc/agentic-ci/openshell:0.3.46` |
| Inner Fullsend sandbox | `ghcr.io/fullsend-ai/fullsend-sandbox@sha256:259605fea321353552fdefd3a6a55e8b5c260998dfc5a622ed143e41a429995a` |
| OpenShell supervisor | `quay.io/opendatahub/odh-openshell-supervisor:v0.0.112-rhaiv.0` |

The sandbox reference comes from rfe-creator commit
`fae245e778384a0fc823c1df6a71bd2b38489882`, file
`.fullsend/rfe-creator/rfe-creator.yaml`, imported by rfe-autofixer's config.
Recheck these source references before implementation; record any intentional
change and the resolved image digests. The CI image tag is not the OpenShell
binary version: inspect actual CLI/gateway versions rather than inferring them.

## Acceptance criteria

- [x] Read the fork's local instructions; work on the existing M4 feature
  branch without changing strategy orchestration or the rfe-autofixer source.
- [x] Use the reference CI image directly. Supply Fullsend built from a
  recorded `jctanner/fullsend` feature commit as a binary/artifact (or a
  separate build step), verifying its source revision and runtime compatibility.
  Do not substitute rfe-autofixer's released Fullsend 0.43.0.
- [x] Point the strategy harness directly at the reference Fullsend sandbox.
  Inspect required commands and Python imports, including Claude, hook tools,
  Git, Bash, and PyYAML. Record an actual dependency gap if one exists before
  proposing an extension; do not create another custom image by default.
- [x] Adapt `with-openshell.sh` to the reference gateway/supervisor combination.
  Remove the forced 0.0.116 check, local sandbox build/tag, and unrelated
  `base:latest` pull. Preserve per-job Podman storage, readiness checks,
  isolation, and cleanup. Use version-correct TLS/auth configuration suitable
  for later credential-bearing runs; do not blindly copy fixed sleeps.
- [x] Remove `.fullsend/images/ci.Containerfile` and
  `.fullsend/images/sandbox.Containerfile` and update docs, tests, provenance,
  and invocation instructions to the shared-image setup.
- [x] Repeat the applicable M2 checks with these images: job-owned gateway,
  sandbox execution, artifact transfer, allowed/blocked network access,
  and cleanup. Check local-service DNS/TLS and run a small Claude entrypoint
  through the supported helper with the intended hook mode. Record images,
  binary versions, commands, and evidence. This does not require the M5 RFE
  reset or a complete strategy run.
- [x] Run relevant tests, `make test-unit`, `make test` before push, and
  `git diff --check`. Coverage thresholds remain deferred under ADR-0008.
- [x] Commit and push the changes to the same strat-creator feature branch;
  verify the remote SHA and hand M6 the tested image/binary references.

## Status

Complete on 2026-10-06 UTC. The feature branch now uses the rfe-autofixer job
image directly, builds Fullsend from `jctanner/fullsend` feature commit
`8f628aec6d113181914e2a2307fce17488e2c4b4`, and selects the pinned reference
sandbox plus its matching supervisor. It removes both custom Containerfiles.
The completed changes were pushed to
`feat/fullsend-strategy-entrypoint` at commit
`602766cdd96ca857e433385d2c6a2b30f27e5d4f`.

Validation passed in local GitLab project `admin/ci-testing` (ID 1), pipeline
2011, branch `openshell-m41-validation-1791254370`: build job 3898 and smoke
job 3899 both succeeded. The smoke confirmed Fullsend `feature-8f628aec6d11`
(binary SHA-256 `5fa82795ce58458c69498f551a1d4880bcb67bd8002e592fd07617def4f01aee`),
OpenShell CLI/gateway `0.0.112-rhaiv.0`, Claude's `M4_1_CLAUDE_SMOKE_OK`
sentinel, allowed GitHub API traffic, blocked `example.com`, artifact
download, Jira DNS (`10.43.17.62`) and trusted HTTPS (`200`) from the runner,
and successful removal of the sandbox, gateway registration, Podman containers,
and per-job network (`cleanup_exit=0`). The final run artifacts were collected
at `/tmp/m41-job-3899-artifacts/` during the session.

The first validation correctly surfaced a boundary: sandbox DNS for `jira.local`
hung, and a pinned request to its Kubernetes ClusterIP timed out. The runner
container itself resolves the name and reaches the service over trusted HTTPS.
M4.1 records that check at the runner boundary; M6 must validate and configure
the actual strategy sandbox's access to local Jira before processing the seeded
RFE. This does not change M4.1's image/gateway compatibility result.

`make test-unit` passed (511 tests); `make test` passed (775 passed, 1 skipped).
Shell syntax, YAML parsing, and `git diff --check` passed. Reference image
digests: CI job image `quay.io/aipcc/agentic-ci/openshell:0.3.46` resolved to
`sha256:547ca127b48eae2e5b7c1b6a1a8edf7f22321e65454356c696a4c82c6da65be0`;
supervisor `quay.io/opendatahub/odh-openshell-supervisor:v0.0.112-rhaiv.0`
resolved to `sha256:48062232ebda6c4479edb00121899f401f95dacc656ae75202520b1a032b0db2`;
sandbox `ghcr.io/fullsend-ai/fullsend-sandbox@sha256:259605fea321353552fdefd3a6a55e8b5c260998dfc5a622ed143e41a429995a`.

The smoke credential was `authorized_user` ADC with a cloud-platform refresh
token. Keep it scoped to controlled smoke only. M6 must use a dedicated
Vertex-only service-account credential, as documented in the POC guide.

The sandbox Jira follow-up is complete in
[M4.2](fullsend-sandbox-jira-connectivity.md), before M5's reset
and seed. M6 consumes that fix and rechecks access after the reset.

M4.2 correction and resolution: bounded probes found immediate raw child DNS
failure, proxy-based HTTP resolution, working Podman bridge routing, unattached
service permissions, and supervisor upstream `UnknownIssuer`. The pushed fix
and two fresh sandbox passes are recorded in the completed M4.2 task. M4.1's
original DNS/ClusterIP observations did not establish a routing defect.
