# Task: Run one mixed-state S1 batch with GLM

## Goal

Exercise fresh processing, existing STRAT import, verified review-only recovery,
stale/missing proof, human gates and repeat safety in one retained scenario.

## Acceptance criteria

- [x] Publish the agreeing-recommendation fix and pin its exact commit.
- [x] Validate 18 RFEs and 11 STRATs with real review-only push provenance locally.
- [x] Confirm discovery, acquisition, skips and resume points before inference.
- [x] Launch one GLM batch at limit ten and agent concurrency ten.
- [x] Check side effects and record the skipped repeat after native failure.
- [x] Archive and independently verify all evidence, including failures.

## Decisions

The human-sign-off-only control consumes a discovery slot before preparation
skips it. Preserve this behavior: ten candidates, nine acquired, one actionable
RFE deferred. Repeat preparation must exclude completed work and preserve the
deferred RFE, rather than claim that all Jira work is exhausted.

## Evidence

Parser fix published as strat-creator fbc335bedb4a4eb97265da89d36bc29009a41fde.
Before publication: 1,033 tests passed, seven skipped; unit suite 575 passed,
five skipped. No additional component behavior changes for fixture preparation.

Offline validation: 89 benchmark tests pass (one optional integration skipped in
that suite), including actual Markov expression execution. The optional real
local Jira emulator suite separately passes all eight tests, including genuine
preparation/push, import verification and repeat preparation, with no model calls.
Ruff, shell syntax and git diff --check pass. Six retained benchmark job archives
plus the cancelled GLM capture were independently verified before the live reset.
Logs: /tmp/strat-mixed-benchmark-tests.log, /tmp/strat-mixed-local-integration.log,
/tmp/strat-mixed-prior-check.log.

## Live execution

Breadboard a75c72b7b0ef688e891937c515009899d89063cb is pushed and synced.
All imported benchmark files match that source. GLM routing preflight is ready
through enmaas-personal. One run launched, with an exclusive saved launch intent:

- Markov: markov-run-eaf92e4d, created 2026-10-15T23:16:30Z.
- Model job: script-run-workflow-all-glm-5-3-1015-231702-8b0253.
- Model: rits/zai-org/glm-5-3, medium; batch limit ten, agent cap ten.
- Archive root: var/run-data/strat-workflow-hardening/fullsend-glm-mixed-state-c10-20261015.
- Detached archive observer PID 330749; launch-context/observer.log and result.json
  record terminal collection and independent verification. No automatic model retry.

The live seed job completed and the pre-inference guard passed. The actual
Claude process is verified at the pinned candidate with no source diff, GLM
and all model aliases pinned, medium effort, cap ten and nine acquired RFEs.
Actual resume points: RFE 1/2 review; RFE 3/4/5/6 create; RFE 7/8/10 refine.
RFE 13 is skipped for human sign-off; RFE 9 is deferred. Fourteen initial GLM
stream requests were observed through enmaas-personal, including successful
completions. Verification is saved in launch-context/initial-verification.json
and initial-process.json. Full run and archival outcomes remain pending;
a Markov completed status alone does not mean benchmark pass.

## User-requested stop

On 2026-10-16 at 01:18:49.949092Z (9:18 PM Eastern on October 15), sent
SIGTERM to the verified primary Claude PID 157, without deleting its pod.
Claude exited 143; host validation exited one, post-script did not run, and
release-locks.sh exited zero with all nine owned keys recorded as released.
The Job has backoffLimit=0 and restartPolicy=Never. No model process remains;
the pod completed Failed, preserving logs and native-project copies.

Native Workflow wf_e5abd8fa-a12 had already failed at 01:04:10.704Z after
106m02s: both review-only strategies were rejected as not refined. The parent
continued and another Workflow invocation failed at 01:15:36.774Z with three
agents. Last result reports a review input/provenance mismatch. This was inside
the same CLI invocation, not a second host-submitted job.

The finish checker passed its Jira/identity/control/clone/lock checks. The
model-free repeat was deliberately skipped because the run failed. Markov's
independent check then failed to start because its 306,233-byte seed argument
exceeded the operating-system argument limit. Markov terminal state is failed
at 01:20:18Z. Neither final business completion nor live repeat safety passed.

Tracked: [review-only status mismatch](../../bugs/fixed/strat-review-only-import-status-contract.md)
and [oversized checker argument](../../bugs/fixed/strat-mixed-seed-exceeds-exec-argument-limit.md).
The existing archive observer started terminal collection at 01:20:37Z;
archive.log records collection. Final capture and independent verification have
completed, with final receipts published: 17,077 files / 23,296,581,194 bytes,
complete and final, no source errors. The experiment is finished with a failed
pipeline outcome; neither business completion nor live repeat safety passed.

Transcript follow-up confirms the primary changed both task statuses using
frontmatter.py at 01:12:57Z, then invoked Workflow again at 01:13:10Z.
Offline, restoring only Draft in memory reproduces both saved review hashes;
the status-only repair caused the subsequent input/provenance mismatch.
No pipeline source edits appear in this post-failure primary sequence.
