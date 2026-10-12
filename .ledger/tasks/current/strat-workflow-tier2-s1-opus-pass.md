# Task: Launch and archive one three-ticket S1 Opus batch

## Authorization

2026-10-11: user said "okay lets do a single S1 batch run w/ claude-opus-4-6".
Publish/sync the needed harness changes and launch exactly one S1 Opus run,
with the existing distinct three-RFE scenario and unchanged S1/S2 pins.
Preserve the completed Haiku evidence before Jira reset. No S2 or repeats.

## Acceptance criteria

- [x] Publish validated archive guards, separate Opus tier and model checks.
- [x] Sync/import exact pushed benchmark commit in markovd.
- [x] Launch one S1 `tier2-opus` run, Opus 4.6, three RFEs, retained evidence.
- [x] Verify exact seed set, model, design pin and 90-minute wait budget.
- [x] Arrange a background collector to save a verified final archive on completion.
- [x] Record IDs and evidence in the evaluation plan; stop after this run.
- [ ] Verify completed run's final archive and analyze results; no automatic rerun.

## Preflight

No active pipeline jobs or Markov runs. Previous final Haiku archive passes
host checksums; live reset guard recognizes its refreshed receipt at
`/data/breadboard/strat-workflow/markov-run-02336f23/20261011T143354300275Z`.
Runtime estimate: about 50 minutes, planning range 40–60. Runner wait
override 5,400,000 ms; pinned design is unchanged.
All 23 offline tests, Markov validation, compilation, shell syntax and diff
checks passed. Relay preflight: zero dropped records/requests/events,
pending writes and storage errors.

## Live run

Submitted 2026-10-11 **15:10:00.522 UTC / 11:10:00 EDT**:
`markov-run-7845a7f1` (database ID 565), running on imported/pushed
Breadboard `2615e72e79704874620be092af2ae5fffc76b8e9`.
Seed `script-seed-scenario-all-claude-haiku-5-5-1011-151003-ca726b`
completed and exactly discovered RHAIRFE-1/2/3.
S1 `script-run-workflow-all-claude-opus-4-6-1011-151014-95af64` created
15:10:14 UTC, model `claude-opus-4-6`, batch-discover, BATCH_SIZE=3,
expected keys matching seed order, pinned S1 `1bd7f17`, wait 5,400,000 ms.
Creation done; refinement started. First 23 captured requests all Opus.
Estimated completion 15:50–16:10 UTC / 11:50–12:10 EDT.

Final archive collector is running as detached host process **2315335**,
with `--wait 8100` and stdout/stderr saved to
`var/run-data/strat-workflow/markov-run-7845a7f1/archive-collector.log`.
Host process visibility requires escalated inspection; sandbox `ps` hid the
live collector. A duplicate managed waiter was started during diagnosis,
then stopped after host inspection confirmed the original remained active.
The shared status log can contain a null-filled gap from that temporary
second writer; raw model evidence was unaffected. The collector waits for
terminal Markov/jobs, then creates the timestamped final archive, verifies
checksums, and publishes a receipt. It does not launch model work.
S1 workflow traces/output and raw API/strace are still on the artifacts
volume until the final host capture. No wipe, S2, or repeat was submitted.

## Completed-run checkpoint

S1 completed 2026-10-11 16:21:59 UTC (71.8 minutes); Markov completed
16:22:08.825 UTC. All runner exit codes zero; exactly three strategies and
three APPROVE reviews (8/8, 8/8, 7/8), all locks released. Evaluation FAIL
solely on `reviewer_outputs_returned`: 11/12 empty completion markers and
one connection-error string mistakenly counted as a nonempty return.
Final review documents have prose; recovery path remains to investigate.
Review agents took 24.5, 20.4 and 29.3 minutes.

Automatic capture verified and receipts published, final/complete=true,
zero errors: `var/run-data/strat-workflow/markov-run-7845a7f1/20261011T162230677725Z/`.
2,517 files, 1,210,005,016 bytes, including browsable 587 API dumps and
1,471 strace files for S1. Initial results are recorded in the evaluation
plan. Further context-growth/handoff/relay analysis remains; no rerun or S2.
