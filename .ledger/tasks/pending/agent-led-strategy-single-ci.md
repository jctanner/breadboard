# A3: Wire the GitLab branch and run one native strategy

Depends on [A2 prompts](../done/agent-led-strategy-prompts.md).

## Acceptance criteria

- [ ] Add fixtures under `var/demos/fullsend-agent-led-poc/`; create and publish
  `feat/fullsend-agent-led-poc` in the existing GitLab project
  `redhat/rhel-ai/agentic-ci/strat-pipeline`. Record its branch base; preserve
  `main` and the completed `feat/fullsend-strategy-poc` branch.
- [ ] Add the new `.gitlab-ci.yml` on that branch, following rfe-autofixer.
  Fetch the public strat-creator fork's `feat/fullsend-agent-led-strategy`
  branch and pin the tested commit for its prompts, skills and harness files.
  Use the maintained runner and existing approved credentials, with separate
  results/dashboard targets. Preserve shared project variables; use distinct
  POC variables or job overrides instead of changing the old workflow's pins.
- [ ] Invoke released `fullsend run strat-single --fullsend-dir ... --target-repo ...`.
  No compile job, feature binary or custom entrypoint. Retain job-owned gateway
  readiness, CA trust, EXIT redaction and deterministic cleanup.
- [ ] Reuse rfe-autofixer's working release/image combination, starting with
  Fullsend 0.43.0, and record version/checksum and image pins. Check native
  hooks, providers, pre/post scripts and result extraction while bringing up
  this workflow. Fix specific integration failures here; do not create a
  separate smoke harness, temporary probe branch or general infrastructure
  validation milestone. Explain any required published-version change.
- [ ] Seed one fresh eligible RFE from existing fixtures without reset or
  processed-issue replay; verify identity and bounded inputs before launch.
- [ ] Prove actual Vertex Opus 4.6 parent/child inference, create/refine/Jira
  push/context-backed review, validated structured output, released owned lock,
  results commits and sanitized artifacts. Truthful revise is an allowed outcome.
- [ ] Verify Org Pulse readback and fresh post-publication dashboard separately;
  record any emulator recovery required. Verify gateway/container/network cleanup.
- [ ] Exercise no-work/failure boundaries without more model writes. Retain
  partial effects, incomplete phases and original failure; no blind auto-rerun.
- [ ] Run relevant checks and `git diff --check`; commit/push the new CI branch,
  run acceptance jobs explicitly on it, and record branch/source SHAs,
  pipeline/job IDs, issue/result references and remaining differences.

## Inputs from A2

CI sets `STRAT_RUN_ID` (e.g. the job ID) and `STRAT_STATE_DIR`, a host
directory in the job container that is not mounted in the sandbox. It
optionally sets `STRAT_LOCAL_CA_FILE`, `STRAT_PUBLISH_DIR` and
`STRAT_ARCHITECTURE_CONTEXT_PATH`. After `fullsend run`, whatever its exit
status, CI runs `.fullsend/shared/release-locks.sh "$STRAT_STATE_DIR"`. On a
pre-script skip, CI publishes `$STRAT_STATE_DIR/preflight-result.json`.

## Status

Pending.
