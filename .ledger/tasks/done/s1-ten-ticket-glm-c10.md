# Launch one ten-ticket S1 GLM batch at concurrency ten

The initial controller interpreted the 2026-10-15 launch request as the next
iterative GLM pass. The user then clarified that Opus was intended and chose
to stop GLM, archive, then run Opus. Initial settings were
rits/zai-org/glm-5-3, one S1 run, ten distinct RFEs and outer Workflow cap ten.
Reviewer Skill dispatch remained unchanged and its optimization stays deferred.

Sources: Breadboard 0359a9a394e3f27beee084031958fd91fa932da6; Fullsend fork
jctanner-fullsend-ai/strat-creator at 6a05210215247b287bb0fb61ed02e423c9de8692.
Use s1-hardening-glm, only_tests=S1, repeats=1, wipe_at_start=false,
job_timeout=18000 and workflow_bg_wait_ceiling_ms=17700000. Native timeout295min.

Verify imported source/settings, idle jobs/conflicting schedules, all retained
prior model-job archives and GLM relay routing before reset. Persist launch
intent, submit one POST and reconcile uncertain responses instead of retrying.
Attach a detached read-only observer that collects and independently verifies
all terminal evidence, including failures. No automatic model retry or Opus
continuation. Read back actual process settings and seeded ownership.

Evidence root:
var/run-data/strat-workflow-hardening/fullsend-glm-ten-rfe-c10-20261015/.

Status: cancelled after the user identified the wrong model. Archival recovery
is complete and independently verified. This is an interrupted run, not a completed benchmark or a
model failure. The subsequent explicit instruction authorizes one Opus run
after archival, superseding the original controller's no-Opus restriction.

## Launch

Markov run markov-run-d72c2f57 started at 2026-10-15T19:10:43.687267Z.
The ten-ticket seed completed and exact discovery passed. Model job
script-run-workflow-all-glm-5-3-1015-191057-721118 is running; the seed job's
Haiku model name is setup metadata and does not imply Haiku inference.

The exact GLM launch variables passed offline execution. All 64 imported files
match source 0359a9a. All five prior retained model-job archives independently
verified before seeding; no active jobs or conflicting schedules were found.
The relay project is enabled and routes the exact GLM model to enmaas-personal,
with its managed API token ready. No private upstream key is placed in jobs.

Observer PID 33397 polls read-only and will collect all terminal evidence with
a 2,400-second stream timeout, independently verify checksums and publish archive
receipts. Launch intent/request, source import, offline result, preflight/archive
verification, relay readiness and live status are retained in launch-context/.
Startup readback verifies actual Claude source 6a05210 with an empty tracked
diff, batch mode, ten distinct acquired RFE keys, BATCH_SIZE=10 and the native
Workflow cap ten. Primary, subagents and all aliases are the exact hosted GLM
model, medium effort. Initial relay telemetry contains successful GLM generation
requests through enmaas-personal. initial-process.json, initial-verification.json
and initial-relay-telemetry.json retain these checks. The job remains running;
no terminal outcome was inferred at that point.

## Cancellation and recovery

The user selected “Stop GLM, archive, then run Opus.” Dashboard access logs
record successful stop requests for the GLM job at 19:20:32 UTC and its Markov
runner at 19:20:41 UTC. Those endpoints delete Kubernetes jobs and pods. The
controller's guarded graceful-stop attempts sent no signal before deletion.
Markovd still reported running, so its cancel endpoint was called to reconcile
the stale state. The original read-only observer was stopped and replaced by
a collector that handles deleted jobs and preserves cancellation provenance.

The shared volume retained the workflow stream and stderr, 95 API dump files
and 678 syscall trace files. Pod-local native session files and the pipeline
worktree were not copied out before deletion. The final archive must disclose
these losses and distinguish observed HTTP status from an uncaptured stop
response body. All retained shared service data is being captured before the
next Jira reset. Recovery script: /tmp/recover-s1-ten-glm.py; private provenance
and recovery-archive.log are under launch-context/.

Final recovery capture: markov-run-d72c2f57/20261015T192802999222Z under
the evidence root. All 894 files / 6,123,261,163 bytes pass checksum verification;
no capture-source errors. Final receipt published. Missing native/pod-local data
remains an explicit limitation, not a claim of complete original evidence.
