# Task: Archive complete evaluation evidence under var/run-data

## Requirement

User requested 2026-10-11: retain each run's strace, API dumps, MLflow
traces, logs, Jira data, and related system evidence under `var/run-data`
before data is cleared for another run. The existing directory is a local
symlink to `/data/breadboard`; never commit generated archives.

## Acceptance criteria

- [x] Host collector exports a structured archive for an explicit Markov run.
- [x] Preserve exact API index/body files, strace, outputs, seed, eval/summary,
      job/runner/service logs, Kubernetes state, and workflow identity.
- [x] Snapshot Jira, MLflow and Observatory consistently, with their stored files;
      preserve relay request/event telemetry and current health.
- [x] Integrity manifest, explicit incomplete/provisional state, and verification.
- [x] Implement archive checks before wipe and each seed reset, including direct helpers.
- [x] Collect and verify the completed first S1 batch; do not launch any new run.
- [x] Record acceptance criterion and limitations in the plan.
- [ ] Publish/sync updated guards before another deployed benchmark invocation.

## Evidence

Final S1 capture:
`var/run-data/strat-workflow/markov-run-02336f23/20261011T143354300275Z/`.
Twenty sources collected without errors. Original packed evidence: 364 files,
703,026,093 bytes, including all retained shared artifacts and consistent
Jira/MLflow/Observatory snapshots. MLflow snapshot has 33 traces and 488 spans.
After user feedback, expose job evidence directly in `jobs/<job>/api-dumps/`,
`strace/`, and `artifacts/`, retaining tarballs and extending checksums.
S1 contains 605 API dump files and 3,698 strace files.
Expanded capture: 4,694 checksummed files totaling 1,601,583,672 bytes.
Expanded checksums verified live and the final receipt refreshed.
Twenty offline tests pass, including unpack safety and integrity checks.
Guard implementation is local; the already deployed workflow remains pinned
to `2cf4540` pending publication/sync. Detailed S1 failure analysis remains
in the separate S1 task.
