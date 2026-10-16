# Launch one ten-ticket S1 Opus batch at concurrency ten

## Authorization and scope

The user explicitly selected “Stop GLM, archive, then run Opus” after spotting
that the previous ten-ticket run used GLM. Run exactly one S1 iteration with
claude-opus-4-6, ten distinct RFEs and Workflow concurrency ten. Archive and
independently verify the stopped GLM evidence first. No automatic model retry.
Reviewer dispatch optimization remains deferred.

Breadboard source: 0359a9a394e3f27beee084031958fd91fa932da6.
Fullsend fork: https://github.com/jctanner-fullsend-ai/strat-creator.git,
feat/s1-workflow-hardening at 6a05210215247b287bb0fb61ed02e423c9de8692.

Use s1-hardening-opus, only_tests=S1, variants=opus, repeats=1,
wipe_at_start=false, job_timeout=18000 and
workflow_bg_wait_ceiling_ms=17700000. Native timeout is 295 minutes. Opus uses
the managed vertex-strat-evals upstream; private credentials stay in the relay.

## Checks and evidence

- [x] Exact launch variables pass offline Markov execution with ten RFEs,
  one Opus result and cap ten; no provider calls.
- [x] Cancelled GLM archive independently verified, limitations recorded:
  894 files / 6.12 GB, final receipt published.
- [x] Imported source/settings, prior archives, idle state, schedules and
  Vertex route verified before seeding.
- [x] One launch intent and one submission, with detached terminal archiver.
- [x] Live Claude process confirms source, ten acquired tickets, cap ten and
  Opus identity; relay confirms successful Opus calls through Vertex.

Evidence root:
var/run-data/strat-workflow-hardening/fullsend-vertex-opus-ten-rfe-c10-20261015/.
Launcher: /tmp/s1-ten-ticket-opus.py. Archived controller copies and launch
metadata will be retained under launch-context/.

Status: done. The authorized run failed business validation; diagnosis and final
archival are complete. No model retry or additional run submitted. Repair work
is tracked separately in the duplicate-recommendation capture bug.

## Launch and startup verification

Run [markov-run-fbc62d49](https://markovd.local/runs/markov-run-fbc62d49)
started at 2026-10-15T19:38:50.886162Z. Model job:
script-run-workflow-all-claude-opus-4-6-1015-193904-1a3da4.

All 64 imported source files match 0359a9a. Five retained earlier model archives
and the cancelled GLM recovery archive independently verify before reset.
No active jobs or conflicting schedules; managed Vertex upstream ready.

Actual Claude PID 145, excluding the timeout wrapper, verifies clean candidate
6a05210, batch mode, all ten RHAIRFE keys, batch size ten, concurrency ten and
high effort. Primary, subagents and Opus/Sonnet/Haiku aliases are all
claude-opus-4-6. The first nine streaming generation calls are all Opus, all
HTTP 200 and all routed through vertex-strat-evals. The seed job's Haiku label
is setup metadata and does not indicate a Haiku inference request.

Detached read-only observer PID 65418 polls terminal status, then collects all
run evidence with the 2,400-second per-stream timeout, independently verifies
the archive and publishes its receipt. It cannot launch a model retry.
launch-context/ retains intent, request, offline checks, source import, archive
checks, readiness, initial process/configuration and relay evidence. Completion
and final archival were pending at startup.

## Final result

The model container ran 51m24s and exited 1; native Workflow failed after
44m47s, outer CLI exited 0. All ten strategies were created/refined/pushed and
scored. All forty role reports returned; the composition hook captured 38.
Duplicate identical revise recommendations in RHAISTRAT-3's feasibility and
RHAISTRAT-7's testability reports caused capture rejection, missing composition
inputs and unpublished/unrecorded final reviews. Eight final reviews succeeded.
The completion guard and host validator rejected partial work. Post-script did
not run; lock release exited 0, and all ten RFEs are confirmed unclaimed in the
archived Jira readback. Markov completed its evaluation with benchmark_pass=false.

Final archive independently verified: 10,935 files / 20,472,635,632 bytes,
complete/final, no capture-source errors, receipt published. Includes native
evidence, 1,898 API body files and 7,392 syscall trace files. Capture:
markov-run-fbc62d49/20261015T203122658615Z under the evidence root.

Both parser failures reproduce offline; removing only the duplicate agreeing
line in memory makes each report pass. Original evidence and FAIL unchanged.
[Audit](../../notes/s1-fullsend-opus-ten-rfe-20261015.md) and
[bug](../../bugs/fixed/strat-review-duplicate-recommendation-capture.md).
