# SME human review and Fullsend CI validation, 2026-10-19

## Result

The connected SME flow works, with a real repeated-pull defect repaired locally.
The original candidate must not be called a clean end-to-end pass: its post-CI
human pull duplicated the existing local document. The fix passes focused and
live model-free verification; full-suite results and final archive are recorded
in the completion receipt below. No second paid CI run was submitted.

RHAIRFE-19 still maps to the same RHAISTRAT-16. The final strategy is approved,
human-signed-off and has no DRAFT prefix. All 35 issues remain present, control
issues and source business content are unchanged, and the source claim is
released. A final read-back proves the signed-off generated body is the latest
CI revision and the entire SME section is preserved. Normal host preparation
does not select this strategy again and performs zero inference or Jira writes.

## What ran

The source was strat-creator feature branch 6ed858b, compared earlier with main
b396172. Human commands used an isolated editable checkout and separate
source-identical plugin, qualified Claude 2.1.296, Opus 4.6/high and the frozen
rhoai-3.6-ea.2 architecture snapshot 7d61f097. The host default CLI was unchanged.

| Stage | Outcome |
| --- | --- |
| Actual `/strategy-pull` | 31s; local workspace, no Jira writes |
| Human edit | Added SME direction to the existing strategy; Business Need unchanged |
| Actual local `/strategy-refine` | 9m41s productive attempt; human sections byte-identical |
| Actual local `/strategy-review` | 12m10s; four captured reports, 8/8 approve; testability dissents |
| Actual `/strategy-push` | 23s; publishes SME input and removes the old approval gate |
| Normal CI batch 2102 / job 4071 | PASS, 29m06s; same strategy imported, refined, published and reviewed |
| Human post-CI pull | Native success, but independent check FAIL: two copies of the local body |
| Repaired Python pull helper | PASS against live ticket, no inference/writes; one current document |
| Actual `/strategy-signoff` | Shows summary, waits for confirmation, then publishes and signs off |
| Unchanged selection check | Exit 78, zero acquisitions, zero inference, unchanged Jira |

The sign-off confirmation continued the same ordinary CLI session. It did not
resume/replay a native Workflow. This tests synthetic-ticket sign-off mechanics;
it is not human endorsement of the generated strategy's engineering quality.

The CI path was GitLab emulator, Kubernetes GitLab Runner, job-owned Podman,
Fullsend 0.47.1, OpenShell 0.0.112-rhaiv.0, native Claude Workflow and managed
model-relay/Vertex. Adapter branch fdc770c1 remained unchanged. Default JQL
discovered the reopened ticket at batch size one; BATCH_EXPECTED_KEYS only
asserted discovery. No manual reprocess bypass, fixture label clearing or
special SME-sync instruction was supplied to CI.

Independent archive checks verify the completion receipt, all input/report/
scorer/composed-review hashes, four distinct role agents and correct caller/run
attribution. All 128 CI relay requests are real, resolved to Opus 4.6 on
vertex-strat-evals and completed HTTP 200 without recorded errors. The capture
contains 211 API files and 2,019 syscall files. Dashboard pipeline 2103 passes.

## Repeated-pull defect

`pull_strategy.py` used the body-preserving frontmatter writer and then appended
the new body. A fresh CI workspace passes; refreshing an existing human file
retains the stale strategy before the new one. Later section extraction could
select that stale first strategy and republish it at sign-off.

Three model-free regression cases fail before repair: unchanged repeated pulls
in human and pipeline modes, plus an interrupted replacement. The fix writes
validated frontmatter and the new body to a fresh sibling file, then replaces
the destination. The old file survives a failed write. All 26 pull integration
tests pass after repair. The general frontmatter helper's contract is unchanged.

The failed native result and duplicated file are preserved. The repaired helper
was called directly against the same live ticket and followed by the documented
history operations, with no additional model call or full CI rerun. Its patch
and before/after files are retained. Sign-off then republishes exactly the
latest CI body, verified by ADF canonicalization, not just a marker search.

At test completion the repair and human guide changes were local and uncommitted
in the feature checkout. Publication is recorded below. Executable source
during the paid CI run remained 6ed858b.
Required `make test-unit` passes 1,092 checks. Five conditional Fullsend
comment-dispatch checks skip because fullsend was not on that test process's
PATH; the actual released Fullsend CI execution passed separately.

## Other findings and limits

- The first local refinement failed after 38m04s of native transport recovery.
  The host ingress proxy's absolute 120s write deadline cut streaming responses
  despite HTTP 200. Mock HTTP/HTTPS/HTTP2 tests reproduced it. The dedicated
  inference-host deadline repair passes race tests and is deployed on both
  proxy replicas. Real responses now complete beyond 120s.
- An 11-minute stopped continuation exposed a test setup mistake: loading the
  editable checkout as the plugin root protects its local artifacts as plugin
  assets. A separate source-identical plugin fixes the setup. Four corrected
  native mock probes establish this without provider calls. Mock evidence is
  marked synthetic and excluded from usage qualification.
- Forked local Skills can return outer success/exit 0 after a provider error or
  interrupted work. Independent error/artifact checks are required. This CLI
  defect remains open; no binary patch or runtime-pin relaxation was applied.
- The guide now documents the runtime pin, helper dependencies and separate
  plugin installation. Publication is pending. The two previously recorded
  default Fullsend bootstrap issues remain separate from the tested adapter.
- One sign-off checker initially compared expanded link objects. Jira embeds
  the linked strategy's current title there, so removing DRAFT looked like an
  RFE content change. Only that embedded title changed. The corrected check
  compares relationship identities separately and keeps source fields strict;
  the original false-negative receipt is preserved.

The main SME design corrections are incorporated: generic PVC PATCH route as
new work, no custom expansionState backend field, client-side interpretation
of incomplete evidence, same-UID lost-response reconciliation and restart
consent. Requested acceptance-test coverage is less explicit than the narrative.
The invented 5–30 second polling target and inherited quota arithmetic error
remain. Testability spots the unsupported target; the scorer still awards 2/2.
It calls 40Gi usage plus a 10Gi expansion delta over a 50Gi quota an exceedance.

CI preserves feasibility/testability revision recommendations while scoring
8/8 and approving under the user's numeric-only policy. This is evidence that
SME content reaches the right stages and dissent survives, not proof that an
approved strategy has no errors. No new paid LLM judge was used.

## Evidence

Private campaign root:
`var/run-data/fullsend-claude-workflow/sme-loop-20261019/`.

CI capture:
`ci/gitlab-pipeline-2102/20261019T182633.397919Z`.
Collection and separate checksum verification both pass. Final human-stage
capture also includes failed/stopped attempts, native sessions, hooks, API
bodies, syscall traces, exact source/patches, architecture, Jira exports and
shared-service snapshots. Earlier symlink-verification failure is preserved;
later archives record copied links as metadata.

Shared databases are individually consistent snapshots, not one global
transaction. Local Claude did not export remote OTLP; retaining MLflow state
does not imply a local trace exists. Old ingress replica logs before rollout
were not captured and are unavailable. Later replica logs are retained.

## Completion receipt

Final human-stage capture:
`final-human-ci-loop-20261019T183447.696185Z`, 5,545 manifest entries.
Collection completes without errors and separate checksum verification passes.
It includes the original failed post-CI pull, repaired helper/source patch,
full required-suite log, sign-off read-back and zero-inference repeat receipts.
The CI capture above also passes separate verification. Root and component
`git diff --check` pass. No commits or pushes were performed for this task.

## Subsequent publication

At the user's request, committed and pushed the pull repair, its three
regression cases and human review guide as signed-off commit
`1bcb8f4bab6d03619cd8da672c0b7a103e3bdb1f` on
`jctanner-fullsend-ai/strat-creator:feat/s1-workflow-hardening`.
Required full `make test` passes 1,092 tests with six conditional skips: five
Fullsend dispatch checks without its CLI on the test PATH, and the opt-in paid
Workflow smoke. Remote read-back matches; the component checkout is clean.
Only the three reviewed source/test/guide files were committed. No new model
run or changes to historical benchmark captures.
