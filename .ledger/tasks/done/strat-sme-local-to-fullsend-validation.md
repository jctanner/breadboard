# Task: Validate the SME local-review to native Fullsend CI loop

## Goal

Exercise the documented human pull/edit/refine/review/push flow on the hardened
strat-creator branch, then allow normal CI batch discovery to reprocess the
updated strategy through GitLab emulator, Kubernetes GitLab Runner, job-owned
Podman, Fullsend, OpenShell and model-relay.

## Authorization and scope

User authorized starting SME flow testing on 2026-10-19 after the recap.
Use Opus 4.6, one targeted ticket and one pass per stage; model-free checks
first. Preserve existing issues, previous run archives and historical outcomes.
No automatic paid retries or fallback models. Reuse the prior smoke's
RHAIRFE-19 / RHAISTRAT-16 if its live state is suitable. Do not reset Jira.

## Acceptance criteria

- [x] Record live ticket, source/runtime, idle state and prior verified evidence.
- [x] Check local-mode hooks, helper paths and skill registration without inference.
- [x] Pull the reviewed strategy using the documented skill and edit SME input.
- [x] Run local refinement and review; verify concrete SME compliance, preserved
      human sections and no Jira changes before push.
- [x] Push through the documented skill; verify content and verdict removal.
- [x] Launch one normal CI batch, verify discovery/import and exactly the intended
      reopened ticket's processing, new review and no duplicate strategy.
- [x] Verify final human sign-off after approval and unchanged selection/repeat
      without new inference.
- [x] Archive all stages, including API captures, syscall traces, Jira state and
      logs; independently verify checksums and record any gaps honestly.
- [x] Record verdict, problems and follow-up work in the hardening plan.

## Context

[Designed flow audit](../../notes/strat-sme-revision-flow-20261019.md) records
current-main b396172, unchanged S1 6ed858b and the historical three-pass demo.
That demo supplied explicit label reopening/input sync. The mixed-state tests
seeded reopened state. Neither qualifies this complete current-runtime loop.

## Status

Completed with findings and a local pull repair. CI and sign-off pass, controls
are preserved and unchanged preparation performs zero inference. The original
post-CI human pull failed content validation; the repaired helper passes
model-free verification and was subsequently published as signed-off 1bcb8f4.
Full pre-push make test passes 1,092 tests with six conditional skips; remote
read-back matches and the component checkout is clean. Full results:
[SME connected flow](../../notes/strat-sme-local-fullsend-validation-20261019.md).

## Initial preflight and historical attempts

Thirty-five existing Jira issues preserved; target RHAISTRAT-16 remains
approved, source RHAIRFE-19 unlocked, no active copied-branch pipeline or schedule.
The mixed fixture's deliberately locked RHAIRFE-10 control remains untouched.
CI adapter remains fdc770c1 and candidate 6ed858b. The default host CLI is 2.1.300;
the isolated workspace uses the already-installed qualified 2.1.296 binary.

Model-free helper/scope tests: 114 passed. Four additional temporary probes
verify local-mode composition with four captured roles, local Skill/Workflow
launch without a CI run record, and unrelated structured-output handling.
The first attempt was sandbox-blocked (localhost sockets/lock directory);
the same tests pass with normal host access. No product defect inferred.

The actual `/strategy-pull RHAISTRAT-16` passes in 31 seconds, unchanged Jira
and tracked source, 9 API capture files / 121 syscall files. Native plugin,
skills and hooks load. Raw evidence and per-stage receipts are staged privately
under `/tmp/strat-sme-flow-20261019` for separate final archival to var/run-data.

A single synthetic SME directive changes the strategy's generic PVC PATCH API
design, prohibits a new backend expansionState field, and requires lost-response
retry tests preserving PVC UID. It leaves the original Business Need unchanged.
One local refinement started 13:57:54 UTC with Opus 4.6. It ended 14:35:58 UTC
without changing the generated body or Jira. Native transport recovery retried
streams ten times plus nonstream fallback; the outer CLI still reported success
and exit 0. Independent artifact/error checks correctly fail this stage.

Root cause reproduced without inference: host ingress proxy absolute 120s
write deadline. Repaired only dedicated inference-host response and upstream
header deadlines. HTTP/HTTPS/HTTP2 stream and nonstream cases, ordinary console
deadline and client cancellation pass with Go race detection. Both proxy
replicas now run image 6f997256. No strat-creator source change.

Failed attempt archive is independently verified at
`var/run-data/fullsend-claude-workflow/sme-loop-20261019/local-refine-failed-links-recorded-20261019T163135.528241Z`.
The earlier capture fails verification on absolute native latest links and is
preserved. Subsequent captures record links as metadata. Old ingress replica
logs were not in that initial capture and were lost on rollout; preserve this
collection limitation rather than claim exhaustive old-proxy logs. New captures
include all ingress replicas.

One separately identified continuation, `refine-proxy-fixed`, started
17:00:30 UTC using the same candidate, ticket, SME input and model after the
model-free repair and deployment. Its expected inference vhost is confirmed
in the new proxy logs. No background script submits replacement model work.

That continuation receives complete responses beyond 120s, but native Edit
rejects local artifacts as sensitive because the test loaded the entire
editable checkout as the plugin directory. It was stopped with SIGINT at
17:11:29 UTC before any artifact/Jira mutation. This is a harness setup error,
not an SME handling defect. The wrapper again gets native exit 0; independent
content checks correctly fail it. All generated candidate text remains in the
actual API/native evidence; it was not applied manually to manufacture a pass.

Four corrected zero-upstream native permission probes reproduce inline plugin
denials in direct/forked calls and successful edits with an external plugin.
The final probes retain a dormant manifest and project skills in the editable
workspace too. The initial probe lacked Read-before-Edit and is kept separately
as a fixture precondition failure. Mock evidence is explicitly marked synthetic
and must not count as model usage or live SME qualification.

The source-identical installed plugin is now `/tmp/strat-sme-flow-20261019-plugin`
(clean 6ed858b), separate from the editable human checkout. One explicit
`refine-installed-plugin` attempt starts 17:18:40 UTC. Raw evidence stays under
`/tmp/strat-sme-flow-20261019/local-stages/refine-installed-plugin` until archival.
The controller saves its exact driver alongside each new stage. Archive of the
earlier stopped attempt/probes is running separately. Neither push nor CI has
started. [Setup documentation gap, now fixed](../../bugs/fixed/strat-human-review-guide-runtime-and-plugin-setup.md).

## Successful local stages and CI submission

`refine-installed-plugin` passes 17:18:40–17:28:21 UTC (9m41s). Productive
refine_count=1, version diff saved, generated body changed, Business Need and
SME input preserved byte for byte, no transport/permission error or tracked
source edit. Main SME API/state/retry/consent directions are incorporated.
`local-content-review.json` separately preserves content caveats: incomplete
explicit contract-test coverage, an unsupported new polling target, and the
inherited quota arithmetic error. Do not treat this as blanket quality approval.

Actual local review passes 17:31:15–17:43:25 UTC (12m10s). Current numeric score
8/8 approves; testability requests revision, the other three roles approve.
All four exported reports and hashes/caller attribution pass pinned composition
verification under local/, with no workflow run record. The source and separate
plugin remain clean. Independent live comparison verifies all 35 Jira issues
still unchanged after the local review.

Pre-push archive is complete and checksum-verified at
`var/run-data/fullsend-claude-workflow/sme-loop-20261019/local-before-push-20261019T175407.787936Z`.
It includes actual native/API/strace evidence, earlier attempts, clearly marked
synthetic probes, source and deployed proxy identity and shared-service data.

Actual `/strategy-push` passes 17:55:42–17:56:05 UTC (23s). Live check confirms
only RHAISTRAT-16 changes, SME marker published, rubric-pass removed, source
RFE/control content unchanged, same single linked strategy and 35 issue keys.
No test-driver label manipulation or special SME-sync prompt was supplied.

One normal default-JQL CI batch was submitted as **pipeline 2102** through the
copied GitLab branch fdc770c1. Discovery independently returns exactly
RHAIRFE-19 with batch size one; BATCH_EXPECTED_KEYS is an assertion only.
Candidate/model/settings remain 6ed858b, Opus 4.6, high effort and cap ten.
Exclusive launch receipt `/tmp/strat-sme-flow-20261019/ci-launch.json` prevents
accidental resubmission. Read-only observer is active and archives/verifies at
terminal state; it cannot start or retry model work. Terminal CI, sign-off and
unchanged-selection checks remain pending.

CI live sandbox checks establish a current-run import of the exact SME marker
at the same RHAISTRAT-16 mapping, productive refinement completed 18:08:13 UTC
and strategy push 18:08:37 UTC. The full SME section's whitespace-normalized
SHA-256 equals the original human input after the Jira ADF round trip. Live
input/progress and staff-preservation receipts are retained under the campaign.
Three CI role reports are captured by 18:22:13; architecture remains pending.
Recorded API requests all resolve to the intended Opus 4.6/Vertex profile.

The original feature checkout now has a documentation-only human-review-guide
fix for runtime/dependencies/separate plugin setup; its diff check passes and
the archive-based plugin recipe validates without inference. These edits are
not committed/pushed. Actual test workspace/plugin and CI executable source
remain at 6ed858b. The two previously known default bootstrap fixes remain
separate from the tested deployment adapter.

## Resume commands and receipts

All scripts are private temporary controllers and have no automatic inference
retry loop. Local stages: `.venv/bin/python /tmp/sme-flow-local.py <stage>`.
The current refinement uses `--attempt installed-plugin`. Check it afterward
with `.venv/bin/python /tmp/sme-flow-check-local.py --attempt installed-plugin`,
then read the generated sections to judge actual compliance. Only on success,
run one `review`, verify four local report/provenance files and unchanged Jira,
then one `push`. The CI launcher requires the installed-plugin content check.

Launch native CI once with `.venv/bin/python /tmp/sme-flow-launch-ci.py` after
successful push and live gate/discovery verification. It asserts branch fdc770c1,
normal default JQL selecting RHAIRFE-19 with batch size one, and no conflict.
`ci-launch.json` is exclusive-create; never call it again if a receipt exists.
Observe/archive with `/tmp/sme-flow-observe-ci.py`; it cannot submit/retry work.
After approval, use local `pull-after-ci` and `signoff`, then verify unchanged
normal selection without inference. No new ticket or shared reset is needed.
