# M4.2: Make Jira reachable from the Fullsend sandbox

## Goal

Resolve and reach `https://jira.local` from the actual strategy sandbox,
with trusted TLS and the intended network policy. Complete this before
[M5's Jira reset and seed](../done/fullsend-strategy-seed-rfe.md) and
[M6's strategy run](../done/fullsend-strategy-poc-integration.md).

## Starting evidence

[M4.1](../done/strat-creator-rfe-autofixer-images.md) pipeline 2011, jobs
3898/3899, proved runner-side DNS and HTTPS. Inside the sandbox, DNS hung
and a request pinned to Jira's ClusterIP timed out. The cause is not yet
established; do not assume this is only a DNS problem. Track the failure in
the [Jira connectivity bug](../../bugs/fixed/fullsend-sandbox-jira-connectivity.md).

Reuse M4.1's shared images, job-owned Podman/OpenShell gateway, Fullsend
feature commit `8f628aec6d113181914e2a2307fce17488e2c4b4`, and strat-creator
branch `feat/fullsend-strategy-entrypoint` starting at
`602766cdd96ca857e433385d2c6a2b30f27e5d4f`.

## Work and acceptance criteria

- [x] Reproduce in a local GitLab CI job. Compare runner, gateway, and sandbox
  DNS, routing, policy decisions, and TLS trust using bounded timeouts.
  Identify the failing layer before choosing a fix.
- [x] Implement the smallest durable fix. Read component instructions and
  authoritative Breadboard deployment manifests first. Keep local routing
  and CA settings configurable; do not bake an ephemeral ClusterIP into the
  public fork. Preserve hostname verification and the intended network policy.
- [x] From inside the actual sandbox, use the strategy's Python HTTP path
  and intended policy to call a read-only Jira API over `https://jira.local`.
  Verify the response is from Jira, and prove authenticated access with the
  intended CI identity where available. Runner-side success alone does not
  pass this gate. A curl-only probe is insufficient if its policy differs
  from the strategy process.
- [x] Repeat in a fresh CI job without manual container edits. Confirm an
  allowed public endpoint still works, a blocked endpoint stays blocked,
  and job cleanup removes its sandbox, gateway, and Podman resources.
- [x] Run relevant checks and `git diff --check`. Commit/push any fork changes
  on the existing feature branch; keep Breadboard deployment changes in
  Breadboard. Record the root cause, fix, source SHAs, image versions,
  pipeline/job references, and sanitized proof of DNS, trusted HTTPS, and
  API success. Close the linked bug only after sandbox verification passes.

## Scope and handoff

No Jira reset, issue mutations, or full strategy/model run is needed here.
Use existing service credentials without recording their values. M5 owns
resetting and seeding Jira, including restoring credentials after the reset.
M6 reuses this fix, rechecks access after M5, and validates the other required
services and actual Jira writes as part of the workflow.

## Status

Done, 2026-10-06. Both fresh CI jobs passed; fork fix is pushed and temporary resources are removed.
The diagnostic fixture uses the same image and gateway, the applied strategy
base policy, and `scripts/jira_utils.py`. It uses the deployed emulator identity
through a temporary Kubernetes secret, with bounded DNS/TLS probes and no
issue mutations or model calls.

## M4.2 diagnosis

- Pipelines 2013/2014 (smoke jobs 3903/3905) show immediate raw child DNS
  failure (`getaddrinfo` errno -3; `getent` exit 2), not a DNS hang. Python
  uses OpenShell's CONNECT proxy at `10.200.0.1:3128`, which resolves upstream.
  The M4.1 observations did not establish a broken bridge route.
- Job 3905's unfiltered comparison container on the same Podman bridge and
  pinned sandbox image resolved Jira and returned trusted HTTPS 200. No Jira
  credentials were passed to that container.
- The harness imported a service provider profile but never attached it. The
  base sandbox policy had no network rules. OPA denied Python Jira and public
  GitHub before any upstream request. The actual executable is Python 3.14
  under `/sandbox/.uv/python/.../bin/python3.14`; `**/python3` was insufficient.
- Job 3909 confirms the pinned CLI rejects empty permission-only providers,
  including with `--runtime-credentials`. Move endpoint permissions into the
  applied base policy and match `**/python3*`; retain the Vertex provider.
- Pipeline 2017 smoke job 3911 confirms the corrected policy allows Python
  `api.github.com` HTTPS 200 and denies `example.com` CONNECT 403. Jira now
  passes OPA, then resets during proxied HTTPS. Upstream diagnostics continue.
- Current checks: 512 unit tests passed; full suite 776 passed, one skipped.
  Repeat after the final configuration fix before pushing.

- Pipeline 2020/job 3917 enabled structured OCSF logging and reproduced
  inspection mode deliberately. The exact upstream cause is
  `TLS relay error: invalid peer certificate: UnknownIssuer` (four bounded
  Jira attempts). Thus the second defect is supervisor upstream CA trust,
  not bridge routing or missing private-IP permission on this pinned version.
- Pipeline 2019/job 3915 used Jira TLS passthrough and reached `/myself` over
  verified HTTPS with the intended CI identity. Its probe failed on two wrong
  assertions: `serverInfo.baseUrl` is intentionally the emulator's synthetic
  `https://jira-emulator.atlassian.net`; default permissive auth does not
  validate Basic passwords. Corrected probes record identity propagation and
  the absence of password validation without claiming strict authentication.
- The durable fix uses Jira-only `tls: skip` (opaque CONNECT, no supervisor
  TLS termination or HTTP inspection), preserving host/port/executable policy
  and existing client certificate/hostname verification. Public GitHub retains
  enforced read-only HTTP inspection. No ClusterIP is committed. GitLab and
  Org Pulse still need M6 validation of their original inspection rules.

- Final strat-creator fix committed and pushed on
  `feat/fullsend-strategy-entrypoint` at
  `bd20534f5b904ae7808d167ad3cde671e17d5ab1`. `git ls-remote` matches.
  Final `make test-unit`: 512 passed. Final `make test`: 776 passed, one
  skipped. A sandboxed unit rerun encountered a read-only runtime lock
  directory; the permitted rerun passed. Source and root `git diff --check`
  pass; reproducible fixture Python/CI YAML and shell parse checks pass.
  Both fresh sandbox acceptance jobs subsequently passed below.

## Fresh-job verification

Pipeline 2022, build 3920 and smoke 3921, passed. Sandbox
`fs-jir-a2ebbaf9ed58` ran the strategy's `scripts/jira_utils.py` with the
applied base policy, reference image, Python 3.14 virtual environment, and
combined CA bundle. The report proves:

| Check | Observed result |
| --- | --- |
| `/rest/api/3/serverInfo` via Python | Jira Emulator, version `1000.0.0`, synthetic Cloud identity; success |
| `/rest/api/3/myself` with intended CI identity | Identity matches CI user, active; success |
| Invalid Basic password | Accepted in deployed permissive mode; password validation unavailable |
| Certificate/hostname verification | `CERT_REQUIRED`, hostname check true |
| Same Jira URL without local CA | `SSLCertVerificationError`; rejected |
| Public `https://api.github.com/zen` | HTTPS 200 under read-only inspection |
| Blocked `https://example.com/` | CONNECT 403 from OPA |
| Supervisor Jira TLS failures | None after passthrough |
| Output transfer | `iteration-1/output/jira-connectivity.json` downloaded |
| Job cleanup | Gateway registration removed, `cleanup_exit=0`, zero Podman containers, only default `podman` network remains |

The same-image unfiltered comparison on the job's Podman bridge resolved
`jira.local` and returned trusted HTTPS 200. Raw child DNS still fails
immediately by policy; CONNECT resolution succeeds upstream. The repeat
pipeline 2023 also passed with the same checks and cleanup; sandbox
`fs-jir-3f488080932b`, build job 3922, smoke job 3923. Neither job required
manual container changes.

Durable fixture:
`var/demos/fullsend-entrypoint-poc/jira-connectivity/README.md` (start runner,
launch fresh pipelines, collect sanitized output, cleanup). Diagnosis artifacts
remain in `/tmp/m42-job-ID-artifacts`; CI job records remain in project
`admin/ci-testing` (ID 1). No runtime logs or credentials are committed.
See [ADR-0010](../../decisions/ADR-0010-jira-sandbox-tls-passthrough.md).

## Final pins and cleanup

| Component | Verified source/version |
| --- | --- |
| Strat-creator feature branch | `bd20534f5b904ae7808d167ad3cde671e17d5ab1`, pushed and remote SHA checked |
| Fullsend source | `8f628aec6d113181914e2a2307fce17488e2c4b4`, feature binary `feature-8f628aec6d11` |
| CI job image | `quay.io/aipcc/agentic-ci/openshell:0.3.46` |
| OpenShell CLI/gateway | `0.0.112-rhaiv.0` |
| Supervisor | `quay.io/opendatahub/odh-openshell-supervisor:v0.0.112-rhaiv.0@sha256:48062232ebda6c4479edb00121899f401f95dacc656ae75202520b1a032b0db2` |
| Sandbox | `ghcr.io/fullsend-ai/fullsend-sandbox@sha256:259605fea321353552fdefd3a6a55e8b5c260998dfc5a622ed143e41a429995a` |

The feature binary checksum in the accepted job is
`5fa82795ce58458c69498f551a1d4880bcb67bd8002e592fd07617def4f01aee`.
Both accepted jobs preserved the same supervisor/sandbox pins. No custom image
or persistent Breadboard deployment change was needed.

Ran the durable cleanup helper with verified GitLab TLS. It unregistered the
M4.2 runner, removed 12 temporary validation branches and the dummy role
variable, and deleted its deployment, configmap, runner-token secret, and
Jira-credential secret. Kubernetes now has only the maintained
`gitlab-runner` deployment/pod, its config and CA secret. GitLab has only runner
ID 2, `glemu-k8s-runner`; no M4.2 branches or smoke variable remain. The
maintained runner was not changed. CI job records remain available:
[2022](https://gitlab.local/admin/ci-testing/-/pipelines/2022) and
[2023](https://gitlab.local/admin/ci-testing/-/pipelines/2023).

M5 may now reset/seed Jira. M6 must consume the pushed fix, recheck identity
and auth mode after reset, and validate GitLab/Org Pulse and real writes as
part of the strategy workflow. No Jira reset, issue mutation, model call, or
strategy execution occurred in M4.2.
