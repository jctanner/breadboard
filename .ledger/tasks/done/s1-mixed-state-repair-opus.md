# Repair mixed-state recovery and run one Opus test

User authorized fixing the failures from markov-run-eaf92e4d and then one
claude-opus-4-6 test. This authorizes the Opus pass directly after local
validation; no extra paid GLM iteration is planned.

- [x] Restore verified review-only import status before scoring/review hashes.
- [x] Reject unverified promotion and preserve existing reviewed inputs.
- [x] Send the full seed report through stdin instead of one exec argument.
- [x] Prevent a failed native Workflow from entering parent-led repair/relaunch.
- [x] Regress the actual Draft import and final validation without inference.
- [x] Run required component suite and offline benchmark/monitor checks.
- [x] Publish exact commits, sync Markovd and verify prior archive receipts.
- [x] Launch one mixed-state Opus pass, cap ten, one iteration, retain evidence.

Earlier GLM capture is complete, independently verified and has a final receipt:
var/run-data/strat-workflow-hardening/fullsend-glm-mixed-state-c10-20261015/
markov-run-eaf92e4d/20261016T012038554137Z.

The fixture still has 29 initial issues, ten discovery candidates, nine acquired
(four fresh, three refine, two review-only), one late human skip and one deferred.
Keep earlier benchmark pins/results and numeric-only approval unchanged.

Candidate f5691f7e01b392be6b177356dbf204918a1b42af is published. Full suite
1,041 passed / six skipped; focused recovery 57 passed; benchmark 96 checks
passed (one optional test skipped), separate real local Jira suite nine passed.
Logs: /tmp/strat-mixed-opus-full-tests-final.log,
/tmp/strat-mixed-opus-benchmark-tests.log,
/tmp/strat-mixed-opus-local-integration.log. No inference in these checks.

## Live execution

Breadboard a2aec3c758567b68428322d4e9f42d89d4cd7a25 is pushed and
imported into Markovd, with every imported benchmark file verified. Prior
archives and receipts are verified; Vertex Opus routing is ready. One run
was submitted at 2026-10-16T13:49:39Z: markov-run-5d3327ed. Tier
s1-mixed-opus, one iteration, batch cap ten, agent cap ten, high effort.
Expected acquisition is nine from ten candidates in the unchanged fixture.

Archive root: var/run-data/strat-workflow-hardening/
fullsend-vertex-opus-mixed-state-c10-20261016. Detached terminal archive observer
PID 1194342 finished terminal collection; launch-context/observer.log records collection, followed
by independent verification and receipt publication. No automatic model-job
retry. Live process verification passed; terminal result is recorded below.

Live model job: script-run-workflow-all-claude-opus-4-6-1016-135017-13fd26.
Actual primary PID 151 uses candidate f5691f7 with no source diff, Opus and
all subagent aliases pinned, high effort, cap ten and failure monitor enabled.
Initial relay verification recorded 13 Opus stream requests, including successful
completions through vertex-strat-evals. Guard confirmed all nine acquisitions:
RFE 1/2 review-only, 3/4/5/6 create, 7/8/10 refine; RFE 13 human-skipped.
Observer polling remained current at 13:57:10Z with no observer error.

## Terminal result

Pipeline exit zero; native Workflow completed once in 41m09.550s, model job
45m14s. All nine acquired tickets and all mixed-state checks passed, including
review-only preservation, seven pushes, four clones, controls and lock release.
The model-free repeat passed with only deferred work acquired and no duplicate
effects. Seven strategies approve; two revise.

Pinned benchmark remains pass=false for reviewer_outputs_returned only. All
36 role reports were delivered and match saved provenance/composed text. Three
format false negatives recur: numbered feasibility findings, Mostly sound
architecture, and a repeated consistent testability judgment. Historical result
unchanged. Full evidence archived and independently verified, receipts published:
11,940 files / 22,344,722,063 bytes. No further model run.

[Run audit](../../notes/s1-mixed-state-opus-20261016.md).
