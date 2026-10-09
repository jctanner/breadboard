# Fullsend sandbox Jira connectivity (M4.2)

Run a bounded, read-only Jira probe in a real Fullsend/OpenShell sandbox using
the strategy checkout's applied policy and `scripts/jira_utils.py`. No strategy
skills, model calls, Jira reset, or issue mutations occur. The fixture also
checks valid/invalid Jira credentials and records the deployed emulator auth
limitation, allowed GitHub HTTPS, denied `example.com`,
TLS verification (including rejection without the local CA), output transfer, and job-owned Podman/gateway cleanup.

## Maintained runner after M7

The CI fixture now selects `aipcc-small-x86_64` on the maintained runner.
Supply `JIRA_SERVER`, `JIRA_USER`, `JIRA_TOKEN` and
`M42_EXPECTED_JIRA_AUTH_MODE` through project CI variables; credentials are
masked. Its smoke script accepts these variables without a separate secret
mount. `start-runner.py` and `cleanup.py` below record the original isolated
M4.2 experiment; they are not required for the maintained-runner path.
Use `make host-deploy-gitlab-runner` and the current runner-validation fixture.

## Original M4.2 experiment prerequisites

Use Breadboard's deployed local GitLab, Jira, maintained runner service account,
and `gitlab-runner-ca` secret. The disposable runner has tag `m42-smoke` and
uses separate Kubernetes job storage. It copies the existing deployed Jira
identity into a temporary secret without printing its values. The maintained
runner remains unchanged. Run from the Breadboard root with Python `httpx` and
`kubectl` configured for this cluster.

Supply these environment variables from existing secret management:

- `GITLAB_ADMIN_USER`, `GITLAB_ADMIN_PASSWORD`: local emulator admin access.
- `GITLAB_RUNNER_REGISTRATION_TOKEN`: local runner registration credential.
- `GITLAB_CA_FILE`: readable CA PEM for `https://gitlab.local`.
- `STRAT_CREATOR_CHECKOUT` (optional): strat-creator checkout directory; defaults
  to `checkouts.fullsend_prototype/jctanner.strat-creator` beneath Breadboard.
- `GITLAB_API_URL` (optional): defaults to `https://gitlab.local/api/v4`.

The scripts operate on local GitLab project `admin/ci-testing` (ID 1). Start
with its `main` branch and the existing `.gitlab-ci.yml`. The fixture needs
`FULLSEND_GITLAB_ANALYST_TOKEN` to satisfy Fullsend's role preflight, although
it does not call GitLab from the sandbox. It creates a deliberately invalid
placeholder only when the variable is absent and removes its own placeholder
on cleanup.

```bash
python3 var/demos/fullsend-entrypoint-poc/jira-connectivity/start-runner.py
python3 var/demos/fullsend-entrypoint-poc/jira-connectivity/pipeline.py
# Repeat with a new branch and CI job to prove a fresh job succeeds.
python3 var/demos/fullsend-entrypoint-poc/jira-connectivity/pipeline.py
python3 var/demos/fullsend-entrypoint-poc/jira-connectivity/cleanup.py
```

The pipeline uploads the current fork's build, gateway/CA helpers, base policy,
and Jira client. The probe harness omits Vertex and has the same pinned sandbox
image and applied service policy as strategy. The CI image and supervisor
versions match M4.1. No credentials are uploaded through repository commits;
Jira credentials arrive through the runner's temporary Kubernetes secret.

## Evidence

`pipeline.py` prints pipeline/job IDs and saves traces and downloaded artifacts
under `/tmp/m42-job-ID-*`. The sandbox writes `jira-connectivity.json`, with
only selected API fields and an identity-match boolean. Successful output
includes `M42_SANDBOX_JIRA_PASS` and a zero entrypoint exit status. Inspect
`cleanup.log`, empty `podman-after-cleanup.txt`, and
`networks-after-cleanup.txt` to verify that job resources were removed.

Direct `getaddrinfo` and `getent` are diagnostic probes. The restricted child
uses the OpenShell HTTP CONNECT proxy, which resolves the destination outside
the child network namespace; raw DNS failure alone is not the HTTP gate.
The comparison container on the same Podman bridge confirms DNS and HTTPS
with the runner CA independently, without receiving Jira credentials.

The fixture enables structured OCSF logging on its job-owned gateway and
retains selected non-secret Jira failure messages from the sandbox log. Raw
container stderr alone can omit upstream error details. Logs and runtime artifacts remain outside source
control. Cleanup removes the temporary runner registration, deployment,
configmap, credential secrets, and `openshell-m42-validation-*` branches; CI
pipeline/job records remain available as evidence.

The emulator's `serverInfo` reports the synthetic Cloud identity
`https://jira-emulator.atlassian.net`, as defined in its metadata router, rather
than echoing the transport URL. The probe checks that contract and the title.
The current deployment defaults to permissive authentication: `/myself` echoes
the Basic identity but does not validate its password. An invalid-token probe
records this limitation; it does not count as token-authentication proof.
`M42_EXPECTED_JIRA_AUTH_MODE` is copied from the deployed setting by the runner
helper (default `permissive`), so unexpected token acceptance fails the probe.
M5/M6 must recheck the intended identity and auth mode after resetting Jira.
