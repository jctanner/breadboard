# Latest hardened S1: one full mixed-state Opus batch

User authorized 2026-10-18: publish the checker and run one mixed-state batch
with ten acquired RFEs, Opus 4.6, concurrency ten, then a model-free repeat.
Use candidate 6ed858b in Fullsend PR 85. No automatic paid retry or resume.

New fixture: four fresh, four refine and two verified review-only RFEs, plus
eight distinct controls. Preserve the legacy nine-acquired fixture and tiers.
Create the two review-only fixtures first, then controls, then other work:
actual lexical discovery selects ten actionable keys, and the repeat explicitly
skips the remaining human-only control. No S1 gate or batch-limit change.
Generate prior-push proof with the pinned real helpers, not fabricated receipts.

- [x] Implement new scenario/tier and validate all eighteen subjects are distinct.
- [x] Verify exact Markov payload without model calls; publish only benchmark
      changes and the checker. Integration preflight uses Breadboard's normal
      model-free seed and job-side guard before Claude starts.
- [x] Sync/import through markovd-cli and verify every imported source file.
- [x] Verify prior archives, idle state, schedules and intended Vertex routing.
- [x] Submit once, verify actual ten acquisitions, 4/4/2 resume points, source,
      Opus primary/helpers, cap ten and native capture; attach archive observer.
- [x] Archive terminal evidence, verify checksums and record outcome.

The run is Kubernetes/Markov/Breadboard integration, not Fullsend/OpenShell
qualification or independent strategy judging. All runtime data stays private
under var/run-data; never commit credentials, raw captures or generated Jira data.

## Published preparation

Breadboard `9232633963f509addbf2197d453e68fb1236e03f` is committed/pushed on
main. Its twelve files contain only the new mixed fixture/tier, checker v2,
benchmark wiring, tests and README. Unrelated pending root ledger/CLI work is
excluded. Gitleaks staged scan, diff checks, directory validation and exact-
payload Markov rendering pass. All 81 imported files match the published SHA.

Offline suite: 108 tests run, 106 passed, two optional isolated-emulator tests
skipped. Initial test-harness metadata assumptions and the historical-fixture
comparison's cutoff were corrected; final checks pass. The proposed local
emulator process never started because sandbox network approval remained
pending; after the user asked about the path, integration qualification moved
to the existing Breadboard/Markovd seed and pre-inference guard. No model job
or live Jira reset had occurred during those offline checks.

Fixture `batch-mixed-ten-distinct-v2`: 18 RFEs + 11 existing STRATs = 29 issues,
all eighteen subjects and full descriptions distinct. Lexical selection is
RHAIRFE-1, RHAIRFE-11 through RHAIRFE-18, RHAIRFE-2. These split 4 create,
4 refine, 2 review-only. Human-only RFE 3 remains outside the first batch;
the model-free repeat must discover it, skip it, acquire nothing and exit 78.
No new model invocation occurs during repeat. Expected outputs: four clones,
eight refinements/pushes, ten reviews and forty role assessments.

Campaign:
`var/run-data/strat-workflow-hardening/pr85-mixed-ten-vertex-opus-20261018/`.
Durable `launch-context/` holds the exact request, source import, controller,
test/rendering logs, subject inventory and dry-run result. The controller uses
markovd-cli for sync/import/submission/status. Read-only API fallbacks cover
the CLI's omitted workflow source_commit and missing schedules command.
Read-only mixed dry-run needs JOB_ARTIFACT_DIR even without Jira writes;
the first launcher check omitted it and stopped, then it was supplied locally.
Archive and routing preflight passed. Prior terminal capture independently
verifies, there are no active conflicting jobs/schedules, and vertex-strat-evals
is ready with Google service-account auth.

## Submitted once

`markov-run-bfc0b766`, started 2026-10-18 17:30:29 UTC (13:30:29 New York),
submitted through markovd-cli. Exact intent/request, CLI response and configured
mounts are saved before any inference. Detached observer PID 878799 polls
read-only and will archive/verify/publish receipts at terminal state. It never
starts a replacement run. The early startup read saw no model job yet and was
repeated after the normal seed completed; it did not submit another run.

## Actual integration startup verified

Model job `script-run-workflow-all-claude-opus-4-6-1018-173102-3b74fa` is running.
Breadboard's model-free seed completed and created all 29 issues. Independent
Jira read-back confirms all eighteen summaries/descriptions match the published
templates and remain distinct, including controls.

The actual pre-inference guard passes all checks: ten discovery candidates and
ten acquisitions, RFE 1/2 review-only with two verified prior pushes, 11–14
fresh, 15–18 refine. No human-only control consumes a slot. Direct process
inspection confirms clean source 6ed858b, batch cap ten, stop-on-native-failure,
Opus 4.6 for primary/helpers/all aliases, and the qualified pipeline image.
Successful Vertex requests use vertex-strat-evals with service-account auth.
No GLM run was launched. Exact state, guard, source, image, Jira and telemetry
receipts are retained in launch-context; startup-verification.json was saved
at 17:36:20 UTC. Observer status is current and no observer error is recorded.
Terminal outcome, model-free repeat and completed archival verification are
recorded below.

## Terminal pipeline PASS; archive verified

Markov reports completed at 18:01:28 UTC. Model job duration is 30m07s
(17:31:02–18:01:09 UTC); pre, Claude, trusted validation, post and release all
exit 0. Pinned evaluation records pass=true with no failed checks. All ten
acquired RFEs complete, all forty reviewer assessments pass the repaired gate,
and the four new strategies match the four fresh RFEs. Eight refinement/push
paths and both review-only preservation paths pass their checks.

All controls remain unchanged and all owned locks release. The model-free
repeat passes every check: completed work excluded, human-only control skipped,
no tickets acquired, no duplicate effects, exit 78 and zero model invocations.
Usage records 855 Opus calls, 32,138,772 accounted tokens, no recorded API
errors or rate limits. No paid retry/resume occurred.

Observer collected terminal evidence from 18:01:36 through 18:19:40 UTC.
The archive manifest records complete=true and final=true. Independent
checksum verification passes with no problems, and the verified job receipt
was published at 18:19:53 UTC. launch-context/result.json confirms the source
match, pipeline exit 0, benchmark PASS, verified archive and published receipts;
there is no observer-error.json. Task complete, with no automatic paid retry.
