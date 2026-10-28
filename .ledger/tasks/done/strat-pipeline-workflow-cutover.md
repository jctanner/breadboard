# Task: Switch the strategy pipelines to the Claude Workflow

## Goal

Replace the legacy separate Claude invocations in strat-pipeline with the
Fullsend/OpenShell integration running strat-creator's Claude Workflow.

## Context

Requested 2026-10-26. Pipeline checkout:
`checkouts.tmp/jtanner1/strat-pipeline`.
Branch: `feat/fullsend-workflow-cutover`, from updated upstream main.
The existing integration is manual-only and rejects schedules, CONFIG_FILE,
RFE_FILTER, and STRAT_KEY. Do not claim that changing job rules alone supplies
parity. Owner confirmed all four job types must remain, including the necessary
strat-creator changes.

## Acceptance criteria

- [x] Fetch upstream main over SSH, update main, create a separate feature branch.
- [x] Scheduled batches and manual single-ticket jobs use the Workflow integration.
- [x] Resolve config-batch/reprocess parity and remove legacy execution paths.
- [x] Preserve direct Vertex, provided secrets, current architecture context,
  ownership cleanup, strict completion checks, results publication, dashboard.
- [x] Keep push/MR pipelines model-free; paid/live execution needs separate approval.
- [x] Update configuration tests and usage documentation; offline checks pass.

## Implementation

Consumer base: `9bbac1eb3205c12060831c44be2ef6000cdb0743`.
Companion checkout: `checkouts.tmp/jctanner-fullsend-ai/strat-creator`, new
`feat/fullsend-ci-cutover` branch from reviewed `95a5c8f`.
The existing S1 hardening branch is unchanged.

All four original consumer job names now use versioned Fullsend wrappers;
legacy and duplicate opt-in trial execution are removed. Preserve the batch
queue and immediate single/reprocess jobs. Schedule remains six-hourly.
Consumer defaults explicitly select live Jira/publication; shared launcher
defaults remain dry/no-publication. No job or schedule has been launched.

Config batch discovery passes the exact source-local YAML file, baseline
filter and size/offset, then deduplicates keys before owned claims. Reprocess
uses the existing resume harness with an explicit prepared request, host-imports
the exact STRAT and prior review, and starts new refinement. Only that request
may reassess a rubric pass; human gates, active/completed states, missing
pipeline provenance and ambiguous clones refuse. Ordinary resume still skips
approved work. Approval labels are not deleted to force progress.

Final checks: 63 consumer tests pass (14.05s). Full source suite: 1,343 pass,
six optional skips (464.49s). Source wrapper/input checks also pass all 85 cases
on the final test formatting. Real Jira emulator tests cover config selection,
live/dry imports, reprocess idempotence, wrong-key refusal and human gates.
Ruff, types, shell syntax and diff checks pass. The actual consumer's three
registrations materialize from a single source snapshot with commit/hash-bound
runtime URLs. GitLab CI lint: valid, no errors or warnings.

An initial sandbox-only run could not create a loopback socket; repeated
outside the sandbox successfully. No model calls, live Jira writes, real jobs,
deployment, component commits, pushes, MR or merge.

Thirty-file source/patch/test/receipt archive:
`var/run-data/20261026-strat-pipeline-workflow-cutover/`.
Hash readback passes; credential findings: zero. The tested component branches
were subsequently committed and pushed at the owner's request, source first:

- strat-creator: `284389cdd36938714c1819bbf1c68aa4ead7ec98`,
  `feat/fullsend-ci-cutover`, 15 files, signed off.
- strat-pipeline: `48f4eebc639ba3862bfa385b6fa7ce55ad20e6ba`,
  `feat/fullsend-workflow-cutover`, six files, signed off.

All staged bytes match the verified zero-finding archive, including the recorded
deletion. Both SSH pushes completed and authenticated remote SHA readback
matched the commits. Both component worktrees are clean. The existing archive
is unchanged and records its pre-publication state. No PR/MR was created; the
owner will create it. A paid GitLab/Fullsend smoke remains separate validation.

Owner subsequently clarified that the consumer is for after the upstream source
merge. Correction committed/pushed as signed-off
`c51451357c6b833be4d55b0918a2b509f6d8a548`: bootstrap and all registrations now
target `fullsend-ai/strat-creator` on `main`; personal fork removed from the
allowlist. All 63 consumer tests, upstream GitLab CI lint and local packaging
checks pass. Remote SHA verified, component clean. The required source interfaces
must be merged into upstream main before enabling the cutover. Source branch
284389c is unchanged. Owner-created consumer MR !18 is now linked in the notes.

See [notes](../../notes/strat-pipeline-workflow-cutover-20261026.md).

## Constraints

Default Opus 4.6, concurrency ten, one validation iteration. No relay.local,
model-relay, new custom Fullsend entrypoint, or architecture-context commit pin.
Keep the pipeline repository small: reusable runtime belongs in strat-creator.
The owner-approved temporary Org Pulse TLS exception remains.
User subsequently authorized commit and push and will create the PR/MR.
No new model run, live Jira change, deployment or merge was authorized.
