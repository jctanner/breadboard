# Maintained runner capability validation

Run after `make host-deploy-gitlab-runner`. This fixture uses the existing
strategy project and masked CI variables from M6, with a separate
`feat/fullsend-runner-validation` branch. Native `main`, the M6 workflow,
Jira issues and results are preserved.

Supply `GITLAB_API_TOKEN` and `GITLAB_CA_FILE` through secret management:

```bash
python3 var/demos/fullsend-entrypoint-poc/runner-validation/publish.py
```

Use `--publish-only` to refresh the branch and source pin without starting a
validation pipeline.

The publisher copies the current M6 source/connectivity/redaction scripts and
M1 nested smoke into a validation branch based on native main. Checks:

- Ordinary Alpine CI and artifact upload using `k8s-incluster`.
- Native UBI/Claude installation, trusted local Jira bot read and native
  processed-RFE exclusion using the original `setup-claude-ci.sh` and pinned
  public strategy fork. No model call or issue/result write occurs.
- Nested Podman execution, bind output, nonzero exit propagation, DNS/HTTPS
  and empty-container cleanup.
- Two simultaneous feature Fullsend/OpenShell connectivity jobs using
  `aipcc-small-x86_64`, with job-owned engines, gateways and sandboxes.

The OpenShell jobs hold for 90 seconds after reporting `M6_LIFECYCLE_READY`.
While both are ready, collect each pod UID, emptyDir mounts, privileged
security context, job-specific gateway/network/state paths, database presence
and gateway certificate fingerprint. Assert distinct fingerprints, pods,
networks and state paths; no hostPath mounts; each engine sees its own
sandbox. After completion verify cleanup exit 0, no remaining containers,
removed networks and retained artifacts. Store runtime evidence outside git.
GitLab job traces/runner APIs prove assignment; the emulator may omit
`CI_RUNNER_DESCRIPTION` from the job environment.

A separate negative eligibility probe checks the unchanged untagged behavior:

```bash
python3 var/demos/fullsend-entrypoint-poc/runner-validation/publish.py --untagged
```

The tagged ordinary job must pass while `untagged-probe` remains pending
without a runner. Record that observation, then cancel only that probe to
leave no queued work. This pending job is intentional and must not be used
as a failed capability claim.

For deployment/reset regression and rollback instructions, see
[`docs/deployment/gitlab-runner.md`](../../../../docs/deployment/gitlab-runner.md).
M6 separately proves actual Vertex create/refine/review and publication;
this fixture checks runner compatibility without repeating those writes.

## Failure artifact check

`publish.py --redaction-failure` runs only a synthetic failure job. It must
fail with exit 37 and upload `failure-fixture.txt` containing `[REDACTED]`.
An inherited EXIT trap protects failure paths because the emulator appends
after_script to step_script and skips it after an error. This expected failed
job is separate from the passing capability matrix.

## Opt-in milestone diagnostics

Use `publish.py --diagnostic sandbox-connectivity`, `--diagnostic model-smoke`,
or `--diagnostic lifecycle-check --lifecycle cancel|timeout|hard-kill`. These
select only the feature build and chosen diagnostic. Ordinary/native/concurrent
capability probes are excluded. The smoke uses one tool-free Vertex turn and
the pinned strategy helper; lifecycle checks hold without strategy/model work.
These diagnostics are excluded from the normal strategy branch.

`publish.py --diagnostic batch-controls --control-rfe RHAIRFE-N` checks an empty
batch, then acquires one fresh eligible RFE lock and injects exit 37 in the
phase wrapper before any model call. It requires that RFE to be the first
native-discovery candidate, verifies lock release and absence of new strategy
links/attachments, and never publishes results. Use a fresh unprocessed
fixture; this validation is excluded from normal strategy CI.

`publish.py --diagnostic architecture-fetch` runs the pinned
`scripts/fetch-architecture-context.sh` in a temporary directory inside a
sandbox using the pinned strategy policy and image, with no model, Jira,
results or Vertex credentials. It passes only if the fetch exits 0, sparse
checkout holds exactly `architecture/<LATEST_VERSION>` and `overlays`, that
version is the newest in the tree, the clone is shallow with `blob:none`, and
document and overlay files have content. Unauthenticated POSTs to
`git-receive-pack` and to another repository's `git-upload-pack` must both get
the policy's 403. `architecture-fetch.json` records statuses, names and the
sandbox's github.com L7 decisions.
