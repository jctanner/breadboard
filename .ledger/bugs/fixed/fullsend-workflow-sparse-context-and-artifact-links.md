# Bug: Fullsend Workflow bootstrap rejects sparse context and drops evidence

## Observed

Pipeline 2097/job 4062 at `96d6f1c9` ran 01:42:27–01:46:31 UTC. Native
Fullsend passed argument parsing and host preparation acquired RHAIRFE-19.
The architecture freshness hash then failed with `unsafe freshness input`.
Outer cleanup released the owned RFE and **no inference request was sent**.

The default cone sparse checkout selects `architecture/rhoai-3.6-ea.2` and
`overlays`, but also includes sibling symlinks such as `current-ga`,
`latest-released`, `future-ga` and `newest`. Their target directories are
excluded. The strict freshness guard correctly refuses these broken inputs.
This was reproduced locally against the same repository layout.

The artifact redactor separately refused ordinary symlinks in the trusted
host source clone. Its fail-closed EXIT trap removed both artifact folders.
CI traces and shared-service snapshots survive, but those local native
artifacts cannot be recovered from the completed job. There was no sandbox,
raw API dump or syscall trace for agent execution because inference never
started. Do not describe this as a complete native-evidence archive.

## Fix

- Reuse the benchmark snapshot builder in the copied CI adapter. Pin context
  to `7d61f097a9220aeb1280837b66b532177ec558b6`, with only the selected release
  and overlays. Pass that immutable host snapshot to the unchanged pre-script.
  Preserve `SNAPSHOT.json` in CI evidence. No freshness check is bypassed.
- Before redacting/uploading either artifact root, record all remaining
  symlinks as metadata and remove only the captured links, never their targets.
  Preserve the inventory across repeated EXIT/after_script redaction.
- The archiver now records absent required job artifacts as a collection
  error instead of treating a trace-only capture as complete.

## Validation

All **18 model-free checks** pass. Real pinned snapshot construction produces
1,807 architecture files and 37 overlay files. The unchanged candidate's
freshness walker accepts those files; its negative control rejects the sparse
checkout. Redactor regression proves outside targets stay untouched, ordinary
evidence is retained/redacted, and a second pass preserves the link inventory.
Missing-artifact regression prevents a false complete archive.

Original available-evidence capture:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2097/20261019T014902.898665Z`.
Its hashes verify, but its historical `complete` flag predates the strengthened
artifact requirement and must not be taken as proof of retained native files.

Related: [single-RFE smoke](../../tasks/done/fullsend-claude-workflow-opus-single-smoke.md).
