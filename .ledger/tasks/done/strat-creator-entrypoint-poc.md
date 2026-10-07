# M4: Prepare, commit, and push the strat-creator feature branch

Follow step 3 of the [POC plan](../../plans/fullsend-entrypoint-strategy-poc.md)
in the user's strat-creator fork on `feat/fullsend-strategy-entrypoint`.
Depends on the Fullsend entrypoint contract.
Use Claude only and preserve the current strat-pipeline behavior as closely
as possible; adaptations must be justified by the sandbox/launch contract.

## Acceptance criteria

- [x] Confirm [M1 Podman in k3s](../done/podman-in-k3s-feasibility.md) passed before migration; recorded evidence reviewed.
- [x] Create `feat/fullsend-strategy-entrypoint` in `checkouts.fullsend_prototype/jctanner.strat-creator` after reading its local instructions and inspecting existing work.
- [x] Copy Bash and required Python helpers with source provenance.
- [x] Document source differences; preserve prompts, ordering, locks, gates, and outputs.
- [x] Extract YAML orchestration into an explicit script entrypoint.
- [x] Adapt workspace, credentials, runtime calls, and image dependencies.
- [x] Add CI bootstrap and cleanup for a job-owned gateway using the agreed provider.
- [x] Test sequencing, failure/cleanup, and publication; pass repository tests.
- [x] Include the Fullsend harness/config, entrypoint, required Bash/Python helpers, dependency/image definition, and CI gateway launcher/cleanup files. Start with `single-rfe` and Claude.
- [x] Run `make test-unit`, the full `make test` before pushing, and `git diff --check`; coverage thresholds remain deferred under ADR-0008.
- [x] Commit and push the branch to `github.com/jctanner-opendatahub-io/strat-creator`; verify the remote branch and record the commit SHA and source-script provenance.
- [x] Document the invocation and required non-secret variable names so GitLab CI can consume the pushed branch. Do not open the eventual upstream Fullsend PR here.

The Fullsend hooks switch remains a separate follow-up. It must be implemented
before setting `security.sandbox_hooks.enabled: false`; file preparation can
proceed using the current supported contract. Record the intended hook mode
and required Fullsend feature commit.

## Status

Complete. Branch `feat/fullsend-strategy-entrypoint` was created from `cc1ba8c`
after reading the fork's `CLAUDE.md` and confirming a clean `main` checkout.
Commit `97562dbee8cf2aa792de01160890a6dcfda61cde` is pushed to and verified on
`origin`. Source pipeline commit: `fd36b15c5095c9f20a270b1d69933c578c04d9da`.
The unit suite passed (509 tests); the full suite passed (773 passed, 1
skipped). `git diff --check` passed. A live Fullsend/Jira/GitLab run remains M6
work and is not claimed by this milestone.

## Source fidelity and current work

The user subsequently requested [M4.1](../done/strat-creator-rfe-autofixer-images.md)
to replace the two custom Containerfiles with rfe-autofixer's shared images.
M4 remains complete as the original branch/files delivery; M4.1 supersedes
its image choice and will publish an updated branch commit.

- Source CI file: `checkouts.tmp/gitlab_rhel_agentic_ci/strat-pipeline/.gitlab-ci.yml`,
  job `single-rfe`. Required ordering: acquire issue lock; create strategy;
  refine it; publish the refined strategy to Jira; review; produce the
  `single-rfe` report and run data; unlock in cleanup.
- Source helper provenance and each intentional adaptation are recorded in
  `.fullsend/scripts/ci/SOURCE-PROVENANCE.md` in the pushed branch. The source
  checkout remains untouched.
- M3 Fullsend dependency is commit `8f628aec6d113181914e2a2307fce17488e2c4b4`
  on `feat/entrypoint-harness`. Intended hook mode is enabled/default; do not
  opt out before the separate hooks-switch follow-up lands.
