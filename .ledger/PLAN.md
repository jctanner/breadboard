# Project work index

## Migration retrospective

- [Bash to Claude dynamic workflows](notes/strat-workflow-migration-lessons.md):
  draft covering added implementation and validation work, JavaScript/runtime
  semantics, observed source edits and relaunches, recovery/freshness, live
  qualification, and dated effort accounting. [Writing task](tasks/done/strat-workflow-migration-retrospective.md).

## Current milestone

- [Permanent scheduled Workflow cutover](tasks/done/strat-workflow-permanent-schedule-cutover-20261029.md):
  owner authorized permanent fullsend on schedule 4222905; API readback
  verified at 00:34 UTC October 30. Next run midnight New York; six-hour
  cadence, cap ten, upstream main and owner unchanged. Project/manual default
  remains legacy with stable-1.x fallback. No automatic rollback, host timer
  or manually launched run.

- [October 29 scheduled Workflow qualification](tasks/done/strat-evening-workflow-qualification-20261029.md):
  Opus 4.6 batch passed in **48m04s**; four acquired RFEs completed/reviewed,
  all approved by the numeric gate, publication and downstream dashboard pass.
  No input-change deferral occurred, so this live run qualifies the normal
  resume/publication path, not the drift race. Evidence retained; schedule
  restored to inherited legacy before the midnight recurrence.
  Content inspection finds valid metadata and retained SME text, but three
  strategies have reviewer dissent and the coexistence G4 has a concrete
  [wording inconsistency](bugs/open/strat-coexistence-webhook-criterion-wording.md).

- [PR8913 waynesun09 review](tasks/done/fullsend-8913-waynesun-review.md):
  index-based identity and private-protocol labeling fixed; race/lint/replay
  and Opus 5.5 review pass. Signed-off a4c647466 pushed and exact PR head
  verified; replay excerpt/private-protocol caveat refreshed in description.

- [PR8913 review comments](tasks/done/fullsend-8913-review-comments.md):
  sparse hook/agent metadata and run visibility defects reproduced/repaired;
  organization/docs comments addressed. Runtime/CLI-path race, lint and
  replay pass; Opus 5.5 verified the final recovery correction. Signed-off
  8e1fd4028 pushed and verified as PR head. Wider scope retained per owner.

- [Fullsend Opus 5.5 review fixes](tasks/done/fullsend-8908-claude-review-fixes.md):
  actionable findings reproduced and repaired; runtime/CLI-path race, coverage,
  lint and archived replay pass. Opus 5.5 verified final correction with no new
  material finding. Owner-authorized signed-off 7f266ee9f pushed to the fork;
  component checkout clean, no PR created.

- [Evening schedule restored to legacy](tasks/done/restore-strat-schedule-legacy-20261029-evening.md):
  October 29 scheduled pipeline 3006130966 / job 17591617217 passed;
  Workflow job **48m04s**, downstream dashboard pipeline 3006261958 passed.
  Removed only the temporary schedule override at 00:02 UTC October 30;
  inherited legacy verified before midnight New York. Owner/ref/cron/source
  and batch cap ten unchanged; no host automation or extra run launched.

- [Fullsend Workflow event coverage audit](tasks/done/fullsend-8908-workflow-event-coverage-audit.md):
  broader task lifecycle, hook, permission, session, notification and rate-limit
  display implemented; runtime/CLI-path/other-package race checks and staged
  lint pass. Version-bounded event matrix documented; staged, not published.

- [Fullsend #8908 Workflow progress fix](tasks/done/fullsend-8908-workflow-progress.md):
  local branch `fix/8908-claude-workflow-progress`; parser/display regression,
  archived-stream replay, runtime race coverage and staged lint pass. Full
  repository race run hit the CLI 10-minute timeout; the active existing test
  passes on main and patch. Mintcore race suite passes. No commit/publication.

- [PR93 push recovery and publication validation](tasks/done/strat-pr93-push-and-publication-boundaries.md):
  four reports reproduced and repaired, plus Claude's follow-up corrections.
  39 new cases; 154 focused checks and lint/schema pass. Final Opus 5.5 review
  found no material defects; only a recorded import-format blank line changed
  afterward. Full **1,605 pass/six skips**; archive verified 108 files plus
  manifest, 34-file source/evidence credential scan zero. Signed-off **6334546**
  pushed and verified as PR93's exact head; checkout clean. DCO/lint/Unicode
  passed; latest review marks all four findings resolved, with no new code
  findings. All CI green; nine addressed bot conversations resolved, zero
  unresolved threads. Owner merged PR93 into upstream main as **e8f3e5b** at
  2026-10-29 17:09 UTC; merged head 6334546 confirmed. Merge receipt verified
  five files plus manifest. Delivery/thread receipts also retained.
  [Scheduled qualification](tasks/done/strat-evening-workflow-qualification-20261029.md)
  subsequently passed for four RFEs; no live drift race occurred.

- [PR93 creation and recorder boundaries](tasks/done/strat-pr93-create-and-review-boundaries.md):
  both new medium findings reproduced at 17a684f; initial repairs pass 95 focused
  cases. Opus 5.5 confirmed both and found two related boundaries, now repaired
  with 30 new cases. Final Opus 5.5 verification found no material defects; full
  **1,566 pass/six skips**, lint/schema clean. Archive verified 89 files plus
  manifest; 32-file source/receipt credential scan zero. Signed-off **e9bcdc3**
  pushed and verified as PR93's exact head, source byte-identical and checkout
  clean. All CI passed. Latest Fullsend review marks the two repaired findings
  resolved but reports a new push-recording race plus three low items;
  [refresh](bugs/open/strat-batch-freshness-failure-isolation.md). Publication
  archive verified 16 files plus manifest. No merge, smoke or schedule change.

- [PR93 independent proof and late human-gate repairs](tasks/done/strat-pr93-host-proof-and-human-gate.md):
  both concerns and reproduced verification follow-ups fixed locally; 33 new
  cases, full 1,536 pass/six skips, lint/type/schema clean. Opus 5.5 verified
  the corrections; four review calls estimated $6. Archive verified 96 files
  plus manifest; full 31-file PR credential scan zero. Signed-off **17a684f**
  pushed and verified as PR93's exact head; clean checkout, DCO passed, CI/review
  started. [Publication](tasks/done/strat-pr93-host-proof-publication.md): 12-file
  receipt archive verified. No live smoke or schedule change. Parser/layout
  limits and actor/journal assumptions remain tracked separately.

- [PR93 independent local Claude review](tasks/done/strat-pr93-local-claude-review.md):
  one Opus 4.6/high review of 13a4f71, 14m16s, CLI token estimate $2.84.
  No high/medium findings. Conditional Jira display-name compatibility gap
  tracked; conservative unavailable-history behavior retained. Four offline
  checks confirmed both observations. Source unchanged; archive verified 20
  files plus manifest with zero credential findings. No live smoke/cutover.

- [PR93 review findings reproduced and repaired](tasks/done/strat-pr93-review-followup.md):
  signed-off 13a4f71 pushed to existing PR93, exact remote head/files verified,
  clean and mergeable. Push-label race, create/skip/pending accounting, missing
  create receipt, reasons/reporting/CLI fixed. Reverts require host-pinned Jira
  history proof; unprovable cases remain fail-closed. Forty added cases; full
  1,503 pass/six skips, lint/types and Python 3.11/3.12 CI green. Automated review
  in progress; protected-path approval is separate. Archive verified 27 files
  plus manifest, full 28-file PR credential scan zero. No paid run or cutover.

- [Batch freshness isolation PR #93](tasks/done/strat-batch-freshness-isolation.md):
  signed-off 6ad16b5 pushed on feat/isolate-stale-batch-tickets; upstream PR
  verifies main base/exact head, 25 files, mergeable. Ticket edits defer their
  RFE; host verifies partial completion/publication and retains deferred recovery.
  Shared/unverifiable failures stay fatal but can produce failed receipts.
  Nineteen added fault/control-flow cases; full 1,463 pass/six skips, lint/types
  clean. DCO/lint/Unicode CI pass; Python CI/review in progress. Archive verified
  25 files plus manifest; credential scans zero. No paid run or schedule change.

- [Post-fix live batch failed on real input drift](tasks/done/strat-placeholder-repair-live-batch-20261028.md):
  pipeline 2996960969 / job 17523658071, 47m12s, Opus 4.6/main b75e838.
  All six strategies refined/pushed before RHAIRFE-3785's description changed;
  batch-wide freshness blocked all review completions and result finalization.
  [Failure-isolation follow-up](bugs/open/strat-batch-freshness-failure-isolation.md).
  StructuredOutput errors were missing-checkpoint hook rejections, with no
  independent malformed-schema error found. All locks released, host publication
  skipped, schedule still legacy. Native estimated $34.11/26.55M tokens including
  cache. Archive verified 118 files plus manifest, zero configured-secret
  findings. No Jira reset, source patch, model retry or schedule re-enable.

- [SME placeholder fix merged](tasks/done/strat-freshness-empty-placeholder-fix.md):
  PR92 merged Oct 28 00:38Z, main b75e838. Both implementation/test blobs match
  tested 0b69019; [source bug fixed](bugs/fixed/strat-freshness-empty-sme-placeholder-format.md).
  Real schedule still inherits legacy; next due midnight New York. No paid
  requalification or schedule switch performed merely because the PR merged.

- [Scheduled execution restored to legacy](tasks/done/restore-strat-schedule-legacy-20261027.md):
  owner-approved rollback verified at 22:56:10Z. Schedule 4222905 inherits legacy;
  jtanner1 ownership, batch ten and cadence unchanged. Next due midnight New
  York. Failed run/artifacts and partial Jira work preserved; no paid retry.
  [Narrow source repair PR #92](tasks/done/strat-freshness-empty-placeholder-fix.md)
  merged: tested signed-off 0b69019 on fork fix/empty-sme-placeholder-freshness.
  Required full suite 1,444 pass/six skips, full lint/schema pass. DCO/remote
  lint/Unicode/Python 3.11/3.12 all pass. Qodo reports no issues; Fullsend's sole
  changes-requested finding is protected scripts path needing a linked issue
  and human approval, not a code defect. GitHub mergeable/clean. No source
  change or public response made to the review. Schedule stays legacy.

- [Real Workflow schedule enabled](tasks/done/enable-real-strat-workflow-schedule-20261027.md):
  schedule 4222905 now fullsend; ownership transfer to jtanner1 separately
  approved and verified. Batch ten, six-hour cadence and legacy project default
  unchanged. Next due 22:00Z / 6 PM New York Oct 27; no manual pipeline launched.
  Before/after receipts archived. [First scheduled batch qualification](tasks/done/first-scheduled-strat-workflow-batch-20261027.md)
  failed: pipeline 2996590097 / job 17520981396. Own empty SME placeholder's
  punctuation variation tripped literal freshness comparison; reproduced
  offline. All locks released, host publication skipped, partial Jira artifacts
  retained. [Freshness bug](bugs/fixed/strat-freshness-empty-sme-placeholder-format.md).
  Owner-approved rollback completed; no paid retry. Failed archive verified
  65 files plus manifest, rollback archive seven; configured-secret scans zero.

- [Post-merge single-ticket smoke passed](tasks/done/strat-postmerge-single-smoke-20261027.md):
  upstream main/Opus 4.6, one model iteration, 28m 37s; RHAISTRAT-3074 scored
  7/8 approve with testability revise preserved. Jira bytes/comments, 14 sealed
  publication files, dashboard output and cleanup verified. Org Pulse upload
  reports one new record plus 18 aggregate warnings; local per-feature GET
  unavailable due internal DNS. Evidence archived; no source patch or model
  retry. Schedule remained legacy during the smoke; later enablement is above.

- [Org Pulse aggregate review-schema warnings](bugs/open/org-pulse-aggregate-review-schema-warnings.md):
  eighteen aggregate entries rejected by existing schema, examples are older
  STRATs. Separate data compatibility follow-up; current run contract unchanged.

- [Both rollout PRs merged](tasks/done/strat-creator-pr85-merged.md):
  source #85 merged Oct 27 from tested 364e1ca. Upstream main b295fe9 contains
  ten verified matching CI/harness/Workflow interfaces. GitLab !18 already
  merged; legacy/stable-1.x still selected, project/schedule settings unchanged.
  Next step is an explicitly authorized manual single-ticket fullsend smoke;
  no job launched and no scheduled cutover performed.

- [GitLab MR !18 merge confirmed](tasks/done/strat-pipeline-mr18-merged.md):
  merged to main as b00078e on Oct 27. CI bytes match the tested branch;
  legacy/stable-1.x remains default and project/active schedule have no override.
  No executor setting changed or job launched. Strat-creator #85 still open;
  its merge precedes an explicitly authorized Workflow smoke and later enablement.

- [Restore legacy cleanup coverage](tasks/done/strat-pipeline-legacy-cleanup-tests.md):
  Federico's omission fixed by restoring original upstream tests unchanged.
  Fourteen cleanup regressions/full 148 tests pass; runtime/CI untouched.
  Signed-off 200b04b pushed/read back, clean; no cleanup-file deletion remains
  in MR diff. Credential scans zero; ten-file archive and receipt verified.
  MR test-count description updated, no thread reply/resolution. New CI pending.

- [PR #85 review after 364e1ca](tasks/done/strat-pr85-review-364e1ca.md):
  new bot round resolves acquisition race and reports no new code defect.
  Remaining comments repeat accepted/deferred/process/compatibility concerns;
  in-repo pending handling is acknowledged. Required CI all green, conflict-free,
  still changes requested. Read-only status check; no new patch round started.

- [Preserve stable pipelines and opt into Workflow](tasks/done/strat-pipeline-opt-in-workflow.md):
  MR !18 now keeps four legacy jobs on stable-1.x and adds workflow-* jobs on
  main. STRAT_EXECUTOR defaults to legacy; fullsend opts into Workflow.
  134 tests, 50 shell checks, preserved job-body comparison, packaging and GitLab
  lint pass. Project/active schedule have no override; settings unchanged.
  Signed-off e8f3959 pushed/read back, MR title/body updated, GitLab MR pipeline
  2992428660 passed. Credential scans zero; 20-file archive and separate receipt
  verified. No model job, manual pipeline, deployed cutover or merge.

- [PR #85 acquisition and reviewer-contract fixes](tasks/done/strat-pr85-review-0d60824.md):
  human gates rechecked after acquisition and before owned writes; candidate
  records preserved for cleanup. Reviewer descriptor matches runtime; numeric
  policy unchanged. Red: 19 fail/two controls; focused 172 pass; single final
  full suite 1,434 pass/six optional skips. Signed-off 364e1ca pushed/read back,
  conflict-free and component clean. Credential scans zero, 17-file archive and
  separate publication receipt verified. DCO passed, remaining CI pending.
  Bounded audit complete; other comments retain accepted/deferred scope.
  Required CI subsequently passed on this head.

- [PR #85 review on a0158d9 fixed](tasks/done/strat-pr85-review-a0158d9.md):
  publication ancestor symlinks and malformed Jira labels rejected; paragraph
  reflowed without instruction changes. Red: 19 fail/one control; focused:
  148 pass; full offline: 1,413 pass/six optional skips. Signed-off 0d60824
  pushed/read back, conflict-free and component clean. Credential scans zero;
  19-file archive plus separate publication receipt verified. DCO passed,
  remaining remote CI subsequently passed. Accepted/deferred scope unchanged.

- [PR #85 three approved review fixes](tasks/done/strat-pr85-review-b8d67c3.md):
  late human gates, interrupted artifact copies and missing managed ownership
  fixed. Full offline suite: 1,394 pass, six optional skips; 129 focused cases
  and 11 shared-fixture/readback checks pass. Signed-off a0158d9 pushed/read back,
  conflict-free and component clean. Credential scan zero findings; 25-file
  evidence archive plus separate publication receipt verified. New-head remote
  CI all green on subsequent read-back. Missing-CI-source hardening deferred;
  accepted scope preserved.

- [PR #85 October 26 review and merge](tasks/done/strat-pr85-review-and-merge-20261026.md):
  four new defects fixed; upstream conflict resolved and approved four-job CI
  support folded into #85. Combined suite: 1,362 pass, six optional skips.
  Forty-six-file archive verified, no credentials. Signed-off head b8d67c3
  pushed/read back; GitHub confirms conflict-free and component clean. DCO
  passed; other remote checks pending. Accepted TLS/security scope preserved.

- [Strategy pipeline Workflow cutover](tasks/done/strat-pipeline-workflow-cutover.md):
  all four job types migrate on separate local consumer/source branches.
  Config discovery and explicit STRAT reprocess retain their distinct semantics.
  Full suites pass: 63 consumer and 1,343 source tests (six optional skips).
  GitLab CI lint/package checks pass; 30-file archive verified, no credentials.
  Signed-off source 284389c and consumer correction c514513 pushed; consumer now
  targets fullsend-ai/strat-creator main for after the source merge. Remote SHAs
  verified and both components clean. Owner-created consumer MR !18 exists.
  No model run or deployed cutover was launched.

- [Strategy pipeline team ownership](tasks/done/strat-pipeline-team-codeowners.md):
  rebased main onto upstream fe9ca62; new chore/expand-team-codeowners branch adds
  all five missing reference owners to both rules. Membership/scope/diff checks
  pass; signed-off 9550f93 pushed to the fork and remote SHA verified.

- [GitHub REST response counters](tasks/done/github-emulator-comment-counters.md):
  comment/review-comment counts now read real rows; PR Git stats are consistent
  across REST responses. All 762 tests pass; deployed and live probe passed,
  including decrement checks, then its temporary repository was deleted.
  [Separate GraphQL stat gap](bugs/open/github-emulator-graphql-pr-diff-stat-placeholders.md)
  is tracked for follow-up.

- [GitHub branch registration](tasks/done/github-emulator-branch-registration.md):
  shared user/org initialization registers the initial Git SHA; forks and contents
  writes also record branches. Added matching-refs. All 757 tests pass; deployed
  and verified the live org probe against Git and all four REST endpoints, then deleted it.

- [GitHub PR review visibility](tasks/done/github-emulator-pr-review-visibility.md):
  submitted reviews and inline comments now appear in conversation and file diffs.
  Seven focused frontend tests, production build, lint and diff checks pass;
  deployed and browser-verified review 70 and comments 20/21 on experiment PR #2.

- [Fix optional-context recovery](tasks/done/strat-import-optional-context-fix.md):
  reproduced stale-file case now refuses ambiguous leftovers before publication;
  stronger completion contract rejects pre-fix records while preserving later
  local reviews and the documented empty-comment placeholder. All 65 focused
  and 1,282 full-suite checks pass (six optional skips); lint/types/diff pass.
  Seventeen-file archive verified, zero credential findings. Three tested files
  published as signed-off 95a5c8f; exact PR head verified and component clean.
  No model calls, live action, deployment or merge.

- [Stale optional review reproduced](tasks/done/strat-import-stale-optional-reproduction.md):
  actual managed preparation/live freshness plus SIGKILL and retry confirms stale
  prior review survives outside completion inventory. Clean control passes;
  31-file archive verified, no credentials found. Reproduction used unchanged
  component code; the subsequent repair is linked above. No model/live action.

- [Review after fbbbc6e](tasks/pending/strat-pr85-review-fbbbc6e.md):
  latest CI passes and reviewer marks both import fixes resolved. One new
  optional-context recovery defect is now repaired locally above. Org Pulse
  exception and two documentation requests are repeated. CI refers to fbbbc6e.

- [Prepared import recovery repairs](tasks/done/strat-pr85-import-recovery-fixes.md):
  missing overflow attachments and incomplete context retries reproduced on
  0707b5b. Repair stages downloads, preserves existing refined task text and
  records completion after publication. All 90 focused and 1,275 full-suite
  checks pass (six optional skips); lint/types/diff pass. Sixteen-file archive
  verified with zero credential findings. Four tested component files published
  as signed-off fbbbc6e; exact PR head verified and component clean. No paid
  smoke, live mutation, deployment or merge. Org Pulse exception retained.

- [Three actionable PR review repairs](tasks/done/strat-pr85-three-review-fixes.md):
  Jira review readback, title delimiter parsing and recovery pathname redaction
  reproduced and repaired locally. All 27 focused checks and 1,261 full-suite
  tests pass (six optional skips); lint/types/diff pass. Eighteen-file archive
  verified, zero credential findings. Org Pulse exception retained. Eight
  tested component files published as signed-off 0707b5b; exact PR head verified
  and component clean. No model calls or live writes.

- [New review on73c454b awaiting triage](tasks/pending/strat-pr85-review-73c454b.md):
  remote CI passed on the published base. Its three actionable findings are
  now published above; compatibility/documentation findings remain in
  the queue. Preserve owner-approved scope and TLS exception. No new paid smoke.

- [New automated PR #85 findings handled](tasks/done/strat-pr85-post327-review-followup.md):
  one attachment-history bug reproduced and repaired; 1,238 tests
  pass/six optional skips, lint/types/diff pass. Thirteen-file archive verified.
  TLS exception retained; process metadata documented without fabricated
  approval. Three component files published as signed-off73c454b; exact PR head
  verified, component clean, remote CI passes. No paid smoke.

- [Scoped PR #85 fixes implemented](tasks/done/strat-pr85-scoped-review-fixes.md):
  all seven bounded changes done locally; 1,230 tests pass/six optional skips,
  lint/types/shell/diff pass. Thirty-seven-file archive verified, no configured
  secrets found. Workflow and Jira publication architecture retained. Changes
  published as signed-off 32700ec; PR head verified and component clean.
  No paid run, live replay, deployment or cutover.

- [Stoyan security review assessed](tasks/done/strat-pr85-stoyan-security-review.md):
  fetched 131 entries; core writable-guards/Jira-token boundary finding valid.
  Offline fake-write reproduction passes; 31-file evidence archive verified.
  [Assessment and rfe-autofixer comparison](notes/strat-pr85-stoyan-security-review-20261022.md):
  user wants incremental scope against the reference pipeline. Shared writable
  workspace/GCP risks confirmed; reference Fullsend Jira profile is read-only.
  Host-only writer remains an unapproved option, not an implementation task.
  Owner scope comment posted/read-back verified; seven bounded repairs now
  implemented locally as linked above. No model run or cutover.

- [Complete downstream publication](tasks/blocked/strat-downstream-publication-recovery.md):
  Org Pulse replay/readback passes: one feature, 8/8 and dissent preserved.
  Dashboard fix passes with native CI_JOB_TOKEN, no secret override; HTML/JSON
  verified. [MR !7](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-dashboard/-/merge_requests/7)
  awaits required approval before main merge. No model run or executor cutover.

- [Temporary Org Pulse TLS exception](tasks/done/strat-org-pulse-temporary-tls-bypass.md):
  signed-off 85e8307 pushed/API verified. User-requested legacy TLS behavior
  is restored only in the Org Pulse exporter; local HTTPS, 1,190 tests/six skips
  and lint pass. Permanent CA follow-up remains; no model/export retry/cutover.

- [Fresh real GitLab single-ticket smoke](tasks/done/real-gitlab-fresh-single-smoke-after-review.md):
  Opus 4.6 job 17366396650 passes in 27m: live Jira review, strict validation,
  data-repo publication and owned cleanup verified; 62-file archive sealed.
  Downstream delivery incomplete: [Org Pulse TLS trust](bugs/open/strat-fullsend-org-pulse-ca-trust.md)
  and [dashboard Git authentication](bugs/open/strat-dashboard-data-repo-auth-smoke.md)
  fail despite green parent. Estimated $5.26/3.02M tokens. No cutover.

- [Address new strat-creator PR #85 comments](tasks/done/strat-pr85-new-review-fixes-20261021.md):
  signed-off b3c10ec pushed, current technical findings repaired; 1,189 tests/
  six skips, lint and native bootstrap/locks pass. Fifteen-file evidence archive
  verified. Maintainer approval/additional security review remain; no cutover.

- [Recover live publication without models](tasks/done/strat-live-publication-idempotence-recovery.md):
  PASS on RHAISTRAT-3027: existing comment/upload verified, one missing-label
  PUT, second publication zero writes; original review/dissent unchanged.
  Zero model calls/tokens; 89-file archive verified. Real CI/sandbox smoke remains.

- [Fix live Jira media/publication completion](tasks/done/strat-live-review-media-and-publication-guards.md):
  signed-off 02dd13b pushed to existing PR #85. Specific media egress,
  credential-safe redirects and verified live publication before completion;
  1,158 tests/six skips, lint and native bootstrap/dependency checks pass.
  No repeat paid run; real OpenShell live qualification remains pending.

- [Follow the strategy source branch](tasks/done/strat-pipeline-follow-source-branch.md):
  source 630fcca pushed to PR #85; consumer caaf92e in new MR !16 follows
  feat/s1-workflow-hardening with one consistent snapshot per job. Source 1,142
  tests/six skips and 79 pipeline tests pass; native locks and six CI graphs
  pass. MR !16 merged as fe9ca62; main CI 2972994099 passes. New manual
  Fullsend smoke jobs follow the branch, currently 85e8307. Legacy schedule
  unchanged; no production cutover.

- [Live real-GitLab strategy canary](tasks/done/real-gitlab-strategy-single-live-canary.md):
  failed pipeline 2972360596/job 17351822419 after 27m25s. Created/refined
  RHAISTRAT-3027, scores 8/8, but attachment reconciliation hits
  [blocked media egress](bugs/fixed/strat-fullsend-jira-attachment-media-egress.md).
  Reviewer [substitutes dry-run in live mode](bugs/fixed/strat-live-review-dry-run-fallback-completes.md);
  final host validation catches the missing verdict label and skips publication.
  Archive/cleanup verified; no model retry or production schedule change.

- [Strategy pipeline MR !15 ready for review](tasks/done/strat-pipeline-mr15-ready-for-review.md):
  Draft removed on `d27a314`; passing CI and conflict/discussion checks verified.
  Description now includes the real smoke and separates publication from the
  CI archive follow-up. Reviewer approval and production rollout remain separate.

- [Real GitLab strategy smoke](tasks/done/real-gitlab-strategy-single-smoke.md):
  PASS pipeline 2969118303/job 17329828389 on the real agentic-ci runner,
  Podman/OpenShell/direct Vertex. One Opus 4.6 dry-run, 24m58s job/15m45s agent,
  one strategy/four assessments, 8/8 approve, strict validation passes. Fixture,
  gateway and temporary credential cleanup verified; schedule unchanged.
  Live Jira writes/publication remain untested here. Credential preflight/docs
  [fixed](bugs/fixed/strat-fullsend-gitlab-role-preflight.md): existing results
  token explicitly supplies Analyst, signed-off `d27a314` pushed to MR !15,
  74 offline tests pass. [Task](tasks/done/strat-fullsend-reuse-results-credential.md).
  Remaining follow-up:
  [standalone business-artifact export](bugs/open/strat-fullsend-ci-business-artifact-export.md).

- [Real Jira smoke-test RFE](tasks/done/create-real-jira-strategy-smoke-rfe.md):
  created and read-back verified
  [RHAIRFE-3739](https://redhat.atlassian.net/browse/RHAIRFE-3739), workbench
  session timing. Release/quality qualifications and Target Version remain
  unset, outside strategy discovery; no job launched.

- [Org Pulse compatibility PR](tasks/done/org-pulse-architecture-skip-pr.md):
  [upstream #1789](https://github.com/red-hat-data-services/rhai-org-pulse/pull/1789)
  merged into main as 7ba9353e on 2026-10-21; API merge/head verified.
  Architecture-skipped assessments are accepted, pending remains rejected.
  [Review follow-up](tasks/done/org-pulse-pr1789-review-followup.md): bot reports
  no functional issues; formatting nit fixed/pushed as 80746a8a, with 6,382 tests
  and lint passing. Deployed production version/live ingestion remain unverified.

- [Repair the new PR 85 findings](tasks/done/strat-creator-pr85-fullsend-review-repairs.md):
  local dry-run, dashboard and reviewer-state fixes plus review cleanup pass
  1,136 source tests and 6,382 companion Org Pulse tests. Lint and local HTTP
  contract checks pass. Published signed-off source 080700e, companion 84f08dca
  and GitLab pin 6f996e2; 69 pipeline tests, actual bootstrap/native locks and
  GitLab MR CI pass. Consumer deployment and maintainer approval remain separate.

- [Triage the new PR 85 Fullsend review](tasks/done/strat-creator-pr85-fullsend-review-triage.md):
  fourteen distinct findings on 8b2f1e0. Seven model-free reproduction/control
  checks confirm a fresh-ticket dry-run failure, a dashboard directory mismatch
  and an Org Pulse reviewer-state mismatch. Repair those before deployment
  qualification; retain ownership/recovery safeguards. [Full dispositions](notes/strat-creator-pr85-fullsend-review-20261020.md).

- [Reconcile merged onboarding](tasks/done/strat-creator-reconcile-onboarding.md):
  published source 8b2f1e0 from upstream main 9c87d83 and consumer 0825ea4.
  Original onboarding settings/workflows preserved; three strategy agents
  registered and guidance corrected. Full lint, 1,118 source tests, twelve
  native config/dispatch checks, three locks and 69 pipeline tests pass.

- [Minimize the Fullsend consumer](tasks/done/strat-pipeline-minimal-fullsend-consumer.md):
  published source 85e5cb3 and consumer d123c19. Pipeline keeps one registration
  file; final MR diff is five files with only config.yaml added. Source 1,118
  tests, pipeline 69 tests, native bootstrap/locks and six CI graphs pass.

- [Real GitLab Fullsend pipeline branch](tasks/done/strat-pipeline-gitlab-fullsend.md):
  local feat/fullsend-strategy-workflow from upstream 3995ac1, direct Vertex,
  live architecture-context and manual single/batch jobs. 87 tests, native
  Fullsend locks, current-context fetch and GitLab CI compiler checks pass.
  Existing production jobs preserved. Latest signed-off d123c19 in
  [upstream draft MR !15](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/15)
  targeting main. Real-runner smoke pending; no inference launched.

- [Validate the local SME to Fullsend CI loop](tasks/done/strat-sme-local-to-fullsend-validation.md):
  completed with findings. Local human flow and CI 2102/4071 pass, same strategy,
  four reports, Opus 4.6, 29m06s. Post-CI pull exposes duplicated local body;
  repaired helper passes live model-free refresh and 1,092 suite checks (five
  conditional skips). Human sign-off/latest-content read-back and zero-model
  repeat pass. All 35 issues preserved; final and CI archives independently
  verify. Pull/guide fixes published as signed-off 1bcb8f4; full pre-push suite
  passes 1,092 tests with six conditional skips. [Results](notes/strat-sme-local-fullsend-validation-20261019.md).

- [Audit the designed SME revision flow](tasks/done/strat-sme-revision-flow-audit.md):
  existing pull/edit/refine/review/push resubmission verified against current
  main and GitLab; historical two-edit demo completed, 36 model-free checks
  pass. S1 preserves the human flow; new-runtime SME loop remains unqualified.
  [Contract and coverage limits](notes/strat-sme-revision-flow-20261019.md).

- [Single-RFE Opus Workflow smoke through Fullsend](tasks/done/fullsend-claude-workflow-opus-single-smoke.md):
  PASS 2100/4068 in 26m05s; RHAIRFE-19 → RHAISTRAT-16, approve, four role
  reports, native completion/validation/publication, clean claims and gateway.
  Downstream dashboard 2101 passes. Source 6ed858b unchanged, adapter fdc770c1;
  Opus 4.6 / high / cap ten through managed Vertex relay profile. Archive and
  separate verification pass: 5,535 files / 910.12 MB, real API/syscall evidence.
  Setup fixes pass 19 local checks; earlier zero-usage failures/gaps preserved.
  [Two portable fixes still belong in the feature branch](bugs/open/strat-creator-default-fullsend-portability.md).

- [Copy Fullsend POC for Claude Workflow and relay](tasks/done/fullsend-claude-workflow-relay-copy.md):
  isolated `feat/fullsend-claude-workflow` published, baselines preserved;
  Opus 4.6 / high / cap ten selected by user, managed Opus-only relay secret.
  Fifteen local checks pass; real model-free sandbox qualification passes
  2095/4059, including secrets, TLS, blocked egress, runtime and syscall capture.
  All four diagnostics archived/verified. First actual Opus Workflow smoke
  remains next; no inference or Jira mutation performed during setup.

- [Inspect GitLab Fullsend branch reuse](tasks/done/inspect-gitlab-strategy-workflow-base.md):
  both POC branches remain green (script 2073, agent-led 2090); runner ready,
  schedules empty. Recommend copying agent-led 89c879b for the current Workflow,
  with source/runtime/config/env/local-policy/archive adaptations before smoke.
  [Live findings](notes/gitlab-strategy-fullsend-workflow-base-20261018.md).

- [Explain 5.5 revision decisions](tasks/done/strat-opus55-revision-analysis.md):
  all 20 reports and 81 score vectors reconcile. Four approval flips mostly
  reflect real readiness gaps; queue scope is debatable. Both extra calls are
  a separate prose-verdict capture/retry defect. [Findings](notes/strat-opus55-revision-analysis-20261018.md);
  separate 35-file evidence archive verifies, zero new provider calls.

- [Judge saved refined strategies, Opus 4.6 versus 5.5](tasks/done/strat-content-opus46-vs55.md):
  fixed-rubric assistant pass preferred 5.5 in all eight pairs, with material
  residual gaps. Unchanged controls also score lower under 5.5's pipeline.
  [Content findings](notes/strat-content-opus46-vs55-20261018.md); separate
  evidence verifies (708 files / 15.43 MB), no new provider inference.

- [Repair scope-judgment checker](tasks/done/strat-review-scope-subject-checker.md):
  published d3a8a8f / role-assessment-v3; all 81 imported files match. Opus 5.5
  replay now 40/40, only one scope pair changes; historical failures still fail.
  112 checks pass, two optional skips; separate evidence archive verifies.
  Zero inference; revision-rate follow-up is recorded above.

- [Mixed-state ten-ticket Opus 5.5 repeat](tasks/done/s1-pr85-mixed-ten-opus55.md):
  one run authorized, same candidate/fixture/high effort/cap ten; separate model
  tier published at 0b89021, 107 offline checks pass (two optional skips), all
  81 imported files match. Vertex inventory updated, exact model probe HTTP 200;
  markov-run-296d9e2e completed in 25m18s, ten paths/repeat pass, forty reports
  independently delivered/preserved. Benchmark FAIL solely on a scope wording
  false negative; two additional testability calls. 37.26M tokens / $42.80 list
  equivalent. [Analysis](notes/s1-opus55-mixed-ten-20261018.md); final archive
  independently verified (13,930 files / 18.85 GB), receipts published and all
  791 captured generations joined to successful intended Vertex routing.

- [Workflow migration conclusion](plans/strat-workflow-s1-hardening.md#2026-10-18-migration-verdict-and-why-the-testing-mattered):
  functional qualification, testing rationale/avoidable expense and inferred
  production consequences recorded. Fullsend deployment, content-quality,
  source protection and distributed ownership limits remain explicit.

- [Cumulative strategy benchmark token audit](notes/strat-workflow-total-token-usage-20261018.md):
  478.9M exact recoverable reported tokens, about 488.9M including the rounded
  first smoke; 301.4M belongs to S1 hardening. Duplicate captures and mock
  responses excluded; development-chat tokens and unreported usage excluded.
  With GLM free, standard API equivalent is about $485 ($481–$487);
  hardening contributes $345.51. This is not reconciled invoice spend.

- [Latest S1 mixed ten-ticket Opus batch](tasks/done/s1-pr85-mixed-ten-opus.md):
  one run authorized, ten acquired RFEs (4 fresh / 4 refine / 2 review-only),
  eight distinct controls, cap ten and model-free repeat. Published 9232633;
  106 offline checks pass (two optional skips), all 81 imported files match.
  Archive/routing preflight passes. Submitted markov-run-bfc0b766 at 13:30
  New York; observer 878799 attached. Actual Breadboard guard verifies ten
  acquisitions, 4/4/2 split and two prior pushes. Clean 6ed858b, all Opus aliases,
  cap ten, qualified image and successful Vertex requests confirmed. PASS in
  30m07s job time: 10/10 tickets, 40/40 reports, controls/cleanup and zero-model
  repeat all pass. Terminal archive complete, independently checksum-verified
  and receipted at 18:19 UTC; no paid retry.

- [Repair reviewer checker formats](tasks/done/strat-review-checker-format-compatibility.md):
  role-assessment-v2 accepts the unchanged latest 40/40 and mixed-state 36/36
  reports; genuine error/lost-handoff controls still fail. 104 tests pass,
  one optional skip. Historical results/bytes preserved, evidence verified;
  no model calls. Checker published in 9232633 with the mixed-batch setup.

- [Ten-ticket Opus completion-hook retest](tasks/done/strat-creator-completion-fixed-ten-opus.md):
  markov-run-0b098f6e completes natively on 6ed858b: ten strategies, forty
  delivered/preserved reports; final guard passes first try in 2.526s traced.
  Workflow 36m41s / job 38m26s, 33.21M tokens, $55.27 Opus list equivalent.
  Pinned benchmark FAIL is solely two known format false negatives; no lost
  handoff found. Archive independently verified: 11,033 files / 17.09 GB,
  receipts published. [Analysis](notes/s1-completion-fixed-opus-ten-rfe-20261018.md).

- [Optimize the final completion hook](tasks/done/strat-completion-hook-performance.md):
  full-size traced replay improves 20.423s to 2.465s and passes the unchanged
  ten-second cutoff. 140 focused checks and eight traced tampering cases pass;
  both required suites 1,089 passed. Published 6ed858b to PR 85. Profiling
  archive independently verified: 10,093 entries / 852.39 MB; original run
  archive unchanged and verified, profiling pods removed. No model calls.

- [Ten fresh RFEs through repaired S1](tasks/done/strat-creator-pr85-distinct-ten-opus.md):
  markov-run-0e40b64c FAIL in 37m21s. Ten separate strategies and forty role
  reports complete; business validation passes and all claims released.
  [Final completion hook](bugs/fixed/strat-completion-hook-ten-ticket-timeout.md)
  times out on five receipt returns; refinement checkpoint passes first try.
  31.99M accounted Opus tokens, no recorded API/rate errors. Archive complete
  and independently verified: 10,951 entries / 16.59 GB, receipts published.

- [One-RFE Opus test after checkpoint repair](tasks/done/strat-creator-checkpoint-fixed-opus-one-rfe.md):
  markov-run-f5a9eb0a PASS in 26m38s on 2a4b7c9. One strategy, all four
  role reports, approve 7/8; checkpoint passed first attempt, claims released.
  117 Opus requests / 4.90M accounted tokens, no recorded API/rate errors.
  Final archive independently verified: 1,742 entries, no capture errors;
  receipts published.

- [Profile/fix refinement checkpoint timeouts](tasks/done/strat-refine-checkpoint-performance.md):
  published 2a4b7c9 to PR 85. Full-size traced hook: 10.731s to 1.921s;
  unchanged ten-second cutoff passes. Both suites: 1,080 passed. Full evidence
  independently verified, 4,372 entries / 504.79 MB; no model calls or paid retest.

- [PR 85 one-ticket Opus integration test](tasks/done/strat-creator-pr85-reviewed-opus-one-rfe.md):
  markov-run-64a6b4f4 failed in 15m46s after create/refine succeeded. The
  [refinement checkpoint hook](bugs/fixed/strat-refine-checkpoint-hook-timeout.md)
  timed out on all five structured-output attempts; no scoring/reviews started.
  Locks released; Opus identity verified, no recorded API/rate-limit errors.
  Final archive independently verified, 1,228 files, receipts published. No retry.

- [PR 85 remediation](tasks/done/strat-creator-pr85-remediation.md): pushed fixes f941955, 21 original threads addressed, native/default checks passed; no paid inference.
- [PR 85 historical DCO](tasks/done/strat-creator-pr85-historical-dco.md): completed at 18cdf46; DCO passes, author/date/tree identity preserved, old history backed up.

- [Mixed-state S1 batch](plans/strat-workflow-mixed-state-batch.md):
  29-record fixture implemented; real local-emulator preparation, reimport and
  repeat checks pass without inference. Ten candidates produce nine acquired
  (four fresh, three refine, two review-only) and one deferred. Source a75c72b
  pushed/synced; GLM run markov-run-eaf92e4d failed and was stopped on request.
  Nine reviews recorded; review-only import/status contract and oversized
  checker argument exposed. All nine claims released; final archive independently
  verified, 17,077 files / 23.30 GB. [GLM result](tasks/done/s1-mixed-state-glm.md).
  [Repair and one authorized Opus pass](tasks/done/s1-mixed-state-repair-opus.md):
  f5691f7 published; 1,041 component tests pass, 96 benchmark checks plus nine
  local-emulator tests. Opus markov-run-5d3327ed completed all nine tickets and the model-free repeat
  in 45m14s job time. All 36 reports delivered; pinned eval rejects three for
  format. Final archive independently verified, 11,940 files / 22.34 GB.
  [Audit](notes/s1-mixed-state-opus-20261016.md).

- [Accept repeated agreeing reviewer recommendations](tasks/done/strat-review-agreeing-recommendations.md):
  published as fbc335b in the Fullsend fork and aligned in the benchmark; report
  bytes/hashes preserved, invalid/conflicting verdicts rejected. Full suite:
  1,033 passed / seven skipped; 79 benchmark tests pass; both failed reports
  replay unchanged. Mixed-state tier pins the fix; historical pins stay intact.

- [Ten-ticket S1 Opus run at cap ten](tasks/done/s1-ten-ticket-opus-c10.md):
  markov-run-fbc62d49 failed after 51m24s: 10 strategies created/refined/pushed,
  40 role reports delivered, 38 captured, eight final reviews published.
  Duplicate identical recommendations blocked two captures. Completion guard
  caught partial work; all ten claims released. Archive independently verified:
  10,935 files / 20.47 GB, receipt published. No rerun.
  [Audit](notes/s1-fullsend-opus-ten-rfe-20261015.md).
- [Repeated identical recommendation capture fix](bugs/fixed/strat-review-duplicate-recommendation-capture.md):
  published parser and aligned checker accept agreeing repeats and reject
  conflicts; originals and historical FAIL preserved.
- [Stopped ten-ticket GLM run](tasks/done/s1-ten-ticket-glm-c10.md):
  markov-run-d72c2f57 cancelled. Retained API dumps, syscall traces and workflow
  stream archived and verified: 894 files / 6.12 GB, receipt published.
  Deleted pod-local/native data loss is disclosed.

- [Ten-ticket S1 batch and concurrency ten](tasks/done/strat-workflow-ten-ticket-config.md):
  both current hardening tiers updated, ten distinct RFE fixtures ready (three
  newly added), 75 tests pass. Source 0359a9a pushed and synced to Markovd;
  all 64 imported files match and read-only seed validation passes. No model
  run or Jira reset. Reviewer dispatch remains deferred and unchanged.

- [One-ticket Fullsend S1 / Vertex Opus smoke](tasks/done/s1-fullsend-vertex-opus-smoke.md):
  `markov-run-d7043ace` completed in 27m54s, approve 7/8; all four reports
  delivered and preserved. All 108 Opus responses match successful real Vertex
  records, 3.74M tokens. Strict evaluation rejects feasibility section formatting;
  no missing handoff. Final archive independently verified: 1,612 files / 6.36 GB,
  complete/final, no archive errors, receipt published.
  [Audit](notes/s1-fullsend-vertex-opus-smoke-20261015.md).

- [Use the Fullsend S1 source in Markov](tasks/done/strat-workflow-fullsend-source.md):
  PR #85 / `feat/s1-workflow-hardening` pinned at `6a05210` for both hardening
  tiers. Breadboard `5493469` pushed and synced into Markovd; 72 offline checks,
  cluster clone and read-only seed validation pass. No model job launched.

- [Model Relay Vertex upstream](tasks/done/model-relay-vertex-upstream.md):
  implemented and deployed; 43 tests and browser checks pass. Google OAuth
  verified, built-in default routes through the new Vertex account and GLM
  retains its EnMaaS override. Key ignored/private; no model inference spent.

- [Port S1 hardening onto the Fullsend fork](tasks/done/strat-creator-fullsend-s1-port.md):
  local feature branch `feat/s1-workflow-hardening` in the user's
  jctanner-fullsend-ai checkout, tip 6a05210. Exact PR #83 commits precede all
  twelve local follow-ups; newer main changes remain intact. Full tests:
  1,005 passed, seven skipped; type validation and diff checks pass. No paid run.

- [Failed dashboard job durations](bugs/fixed/dashboard-failed-job-duration.md):
  fixed and deployed; all four failed jobs keep stable durations across live
  refreshes, detail duration agrees, and 10 regression tests pass.

- [Markovd scheduling and overnight Opus batch](tasks/done/markovd-scheduled-opus-run.md):
  one-time and recurring cron scheduling is implemented and deployed. Schedule #6
  launched one S1 three-RFE Opus batch at 2026-10-15 00:30 America/New_York.
  The job completed in 36m28s; all 12 reports reached their parents and were
  preserved verbatim. The pinned benchmark rejects “Mostly sound” wording in
  one assessment, rather than a missing return. Final archive independently
  verifies 3,599 files / 9.00 GB, receipt published. Both incomplete captures
  are retained; no model rerun or reset was needed for recovery.
  [Results and audit](notes/s1-hardening-scheduled-opus-20261015.md).

- [Disable Org Pulse scheduled refresh](tasks/done/disable-org-pulse-scheduled-refresh.md):
  CronJob suspended live and in the deployment manifest; YAML validation and
  live readback pass, with no active refresh jobs.

- [GitHub emulator aggregate PR diffs](tasks/done/github-emulator-pr-diff.md):
  implemented and deployed with `make host-rebuild-github`; 80 focused tests
  pass, and PR #2 returns identical 43-file diffs through web/UI/API routes.

- [Native Workflow production hardening](plans/strat-workflow-s1-hardening.md):
  [Three-RFE GLM then conditional Opus validation](tasks/done/s1-hardening-three-rfe-glm-opus.md)
  is complete: GLM passed in 2h13m26s, Opus failed after about 73 minutes;
  both final archives independently verify. The [duration diagnosis](notes/s1-hardening-three-rfe-glm-live-duration.md)
  found a [scorer-path integration bug](bugs/fixed/strat-workflow-scorer-path-outside-composition-scope.md).
  Opus exposed Anthropic schema rejection, then its primary
  [edited source and freshness and relaunched](bugs/open/s1-primary-edits-source-and-freshness-after-failure.md).
  Host validation refused the changed baseline; final output does not qualify
  the original pin. The [schema repair](tasks/done/s1-hardening-anthropic-schema-compatibility.md)
  is pushed at f350878: 1,005 tests and a zero-provider native control pass.
  Source/baseline protection remains open; no new paid batch yet.
  [Next Opus configuration](tasks/done/strat-workflow-next-opus-concurrency.md)
  is prepared at schema-fixed f350878 with an explicit outer agent cap of five;
  69 offline benchmark checks pass. The user has now authorized
  [one Opus launch with cap five](tasks/done/s1-hardening-opus-concurrency5.md);
  `markov-run-f286ae61` failed after 23m19s on upstream Anthropic OAuth HTTP 429
  during reviews and result reporting. Exact source/cap/model/high effort were
  verified in the actual process; the schema rejection did not recur. Its final
  archive independently verifies: 2,898 files, 5.60 GB, no errors. No additional
  iteration was scheduled at archive closure. The user has since authorized the
  single overnight run in schedule #6 above.
  S1 is the selected path after custom entrypoints were rejected. Eight focused
  repairs and one rejected proposal; [reviewer delivery](tasks/done/s1-hardening-01-reviewer-delivery.md)
  is verified in one focused GLM run (4/4 reports).
  [Reviewer scope](tasks/done/s1-hardening-02-reviewer-scope.md) is verified for
  three targets (12/12 GLM reports); final frozen-source parity passes native controls.
  [Refine receipts](tasks/done/s1-hardening-03-refine-receipts.md) is verified
  offline/native and in one GLM two-ticket fixture.
  [Review composition](tasks/done/s1-hardening-04-review-composition.md) preserves
  8/8 authored reports in one GLM case; numeric scores remain the sole gate;
  [Delivery gate](tasks/done/s1-hardening-05-delivery-gate.md) rejects non-assessments
  and preserves historical results; real-capture replays pass with zero inference;
  [Final outcome](tasks/done/s1-hardening-06-outcome.md) verifies saved completion
  and separates reporting failure; three native controls and one GLM fixture pass;
  [Restart recovery](tasks/done/s1-hardening-07-recovery.md) reconciles Jira writes,
  owner-bound cleanup and one immutable publication per run; isolated fault
  controls and 966 component tests pass with zero inference;
  [Freshness](tasks/done/s1-hardening-08-freshness.md) checks inputs and provenance
  before reuse/publication; 990 component tests and three native controls pass
  with zero inference. [Item 9](tasks/done/s1-hardening-09-limits.md) is closed
  as rejected, not a bug; no repair remains pending in the original list.
  Deployment/full-batch/content qualification and cross-host fencing remain separate.
  Iterative live tests use GLM, one execution per case/revision;
  Haiku/Opus requires explicit approval and necessity.

- [Model Relay telemetry rollover investigation](tasks/done/model-relay-telemetry-rollover.md):
  fixed and deployed; overview totals cover all matching requests. Actual
  32/128/256-stream stress and minute-crossing continuations passed, with zero
  dropped requests/events or paid calls; all 4,859 deployed requests preserved
  ([evidence](notes/model-relay-telemetry-rollover.md),
  [fixed reporting bug](bugs/fixed/model-relay-telemetry-totals-follow-loaded-page.md)).

- [Claude Workflows and scripted pipelines](../var/benchmarks/strat-workflow/analysis.md):
  the single maintained report covering execution layers, production-scale test
  budgets/confidence, the production recommendation, and architecture-context's
  entrypoint requirements
  ([rewrite task](tasks/done/claude-workflow-human-report.md),
  [consolidation](tasks/done/claude-workflow-report-consolidation.md),
  [next pipeline](tasks/done/claude-workflow-entrypoint-next-pipeline.md)).
  [Testing overview chart](tasks/done/strat-workflow-testing-overview-chart.md)
  separates costs, recorded/forecast time and hypothetical failure-rate bounds, with
  portable PNG/SVG exports.
  [Benchmark workflow overview](../var/benchmarks/strat-workflow/README.md#workflow-overview)
  diagrams setup, job alternatives, checks and host archival
  ([task](tasks/done/strat-workflow-readme-diagram.md)).
  [Hardening evidence](../scripts/claude_binary_analysis/docs/claude-code-2.1.296-benchmark-hardening.md)
  verifies the installed-version reproduction and complete selected-report delivery;
  [hardening task](tasks/done/claude-workflow-report-hardening.md) records its checks.
  [matched-concurrency retest](plans/strat-workflow-matched-concurrency-retest.md)
  is pre-registered, awaiting paid-run authorization.
- [Independent strategy-content evaluation](notes/strat-workflow-content-eval-harness-assessment.md):
  inspected agent-eval-harness; separate judge models/budgets and artifact adapter
  proposed. No paid judging or benchmark integration has run
  ([assessment task](tasks/done/strat-workflow-content-eval-framework.md)).
- [Fix invalid ANTHROPIC_LOG job setting](tasks/done/fix-anthropic-log-directory-warning.md):
  deployed; both launchers corrected, 18 tests and mock capture check pass.
- [Claude Workflow production-gap investigation](notes/claude-workflow-production-gaps-handoff.md):
  complete. Specialist result delivery and review provenance diagnosed (priorities 1–2),
  and recovery, cancellation, budgets, retries and replay consistency verified as
  twenty-three operational controls
  ([task](tasks/done/claude-workflow-operations-controls.md)).
- [Claude Code auto-mode analysis](tasks/done/claude-code-auto-mode-analysis.md):
  complete. Two-stage Sonnet permission classifier, 140k-char rule prompt,
  severity verdicts, default-on, billed ancillary calls; five verified controls.
- [One S2 Opus batch after rate-limit reset](tasks/done/strat-workflow-tier2-s2-opus-rate-limit-retry.md):
  PASS in 88.7 min; three reviews, 12 substantive specialist returns; scope drift
  persists. Final archive independently verified and receipts published.
- [One GLM single-RFE pass each of S1/S2](tasks/done/strat-workflow-glm-single-passes.md):
  complete: both smoke passes/archives verified; S1 reviewer loss and S2
  same-model non-stream fallback recorded.

- **Deployed (optional service):** [Workflow Dojo](plans/workflow-dojo-plan.md):
  LeetCode-style trainer for Claude workflow scripts at `dojo.local`, with a live
  Claude shell on a Model Relay key; real Workflow runs verified 2026-10-26.

- **Proposed (awaiting review):** [Testing the strat-creator Claude Workflow](plans/strat-workflow-eval-plan.md).
  Smoke and full tiers for PR #83's Workflow, run as dashboard jobs through
  Model Relay (haiku-5-5 to wire up, opus-4-6 for results), with per-test
  Jira seeding and MLflow experiments.
  [First tier 2 three-RFE smoke preparation complete](tasks/done/strat-workflow-tier2-three-rfe-smoke.md):
  distinct fixtures, native batch entrypoints, one Haiku S1 run before
  analysis and a separately authorized S2 run; preserve tier 1.
  [First S1 tier 2 pass](tasks/current/strat-workflow-tier2-s1-first-pass.md):
  publication and one S1 launch authorized 2026-10-11; analyze before S2.
  [Per-run evidence archives](tasks/done/strat-workflow-run-data-archives.md):
  preserve complete system/run data in `var/run-data` before the next reset.
  S1 failed: [completed refine rejected by return mismatch](bugs/open/strat-workflow-refine-return-mismatch.md);
  [reviewer prose lost](bugs/open/strat-workflow-reviewer-output-loss.md).
  [Specialist review scope drift](bugs/open/strat-workflow-specialist-review-scope.md):
  individual-target testability calls return assessments of the full batch.
  [Single S1 Opus batch](tasks/current/strat-workflow-tier2-s1-opus-pass.md):
  authorized 2026-10-11, three RFEs, one run, archive then analyze.
  [Relay managed-account timeout fix](tasks/done/model-relay-managed-account-timeout.md):
  honor the configured deadline, distinguish stream timeouts, validate and redeploy.
  [Single S1 Opus repeat after the relay fix](tasks/done/strat-workflow-tier2-s1-opus-relay-fixed-repeat.md):
  completed/archived in 51.2 min; relay fix confirmed, reviewer-return gate still fails.
  [Single S2 Opus batch on the repaired relay](tasks/done/strat-workflow-tier2-s2-opus-pass.md):
  archived/analyzed; stopped at 55.7 min on account HTTP 429, one published review.
  [Reviewer return gate false positives](bugs/fixed/strat-workflow-review-return-gate-accepts-status.md):
  working-tree checker repaired; original results preserved beside new replays.
- **New, divergent POC:** [Native Fullsend strategy agents](plans/fullsend-agent-led-strategy-poc.md).
  Checkout `checkouts.fullsend_agent_led_poc/jctanner.strat-creator`, branch
  `feat/fullsend-agent-led-strategy`; strat-single/strat-batch prompts on
  released, unmodified Fullsend. Prior script-led POC remains complete.
  CI will live on `feat/fullsend-agent-led-poc` in the existing local GitLab
  `redhat/rhel-ai/agentic-ci/strat-pipeline` project.
  [A1 done](tasks/done/agent-led-strategy-foundation.md): fork main = upstream
  `cc1ba8c`, branch created, baseline 768 passed/1 skipped.
  [A2 done](tasks/done/agent-led-strategy-prompts.md): fork branch
  `508ea33`; host-side discovery/locking, strat-single + strat-batch,
  830 passed/1 skipped.
  [A3 done](tasks/done/agent-led-strategy-single-ci.md): GitLab branch
  `feat/fullsend-agent-led-poc`; pipeline 2078 ran RHAIRFE-12 -> RHAISTRAT-12
  on Opus 4.6, validated and published (`28c3825`); failure paths 2080/2081.
  [A4 done](tasks/done/agent-led-strategy-batch-events.md): fork `9350c89`
  (retry with resume), GitLab head `6e3ab46`; scheduled batch 2084
  (RHAIRFE-15/16, revise 5/8 and approve 6/8) and recovery 2086 (RHAISTRAT-14,
  approve 8/8) published; event dispatch withdrawn by decision.
  Pending follow-ups (awaiting go):
  [A5 publication and dashboard without manual recovery](tasks/pending/agent-led-strategy-publication-recovery.md),
  [A6 recovery paths in CI](tasks/pending/agent-led-strategy-recovery-ci.md),
  [A7 runner job pod cleanup](tasks/pending/gitlab-runner-job-pod-cleanup.md).
  Reuse the working Fullsend setup; no separate infrastructure smoke milestone.
  [Decision](decisions/ADR-0012-native-fullsend-strategy-agent-poc.md).
- **M8 complete — [Batch strategy CI and pipeline cleanup](tasks/done/fullsend-strategy-batch-ci.md).**
  Pushed efcf946; 520 unit / 784 full tests passed (1 skipped).
  Batch 2053/3993 processed RHAIRFE-2/RHAIRFE-3 into RHAISTRAT-2/3 on actual
  Opus 4.6; both reviews approve 8/8. Results, Org Pulse (after standard Jira
  sync recovery), fresh dashboard 2055/3996, redaction and cleanup verified.
  Normal pipelines contain no diagnostics; no test work/schedules remain.
  batch-selected is deferred. [Org Pulse stale-key follow-up](bugs/open/org-pulse-ingest-recreated-jira-keys-stay-stale.md)
  remains open alongside the existing DNS/emulator/coverage/hook follow-ups.
- **Pre-M8 complete:** [Pin strategy to claude-opus-4-6](tasks/done/fullsend-strategy-pin-opus-4-6.md).
  Pushed strat-creator 68614f6; create/refine/review regression passed.
  Vertex smoke 2047/3981 reports actual claude-opus-4-6, provider vertex,
  one turn, clean artifacts and cleanup. Historical M6 remains a 4.8 run.
  The subsequent M8 work is tracked above.
- **M4.1 complete:** [Reuse rfe-autofixer images](tasks/done/strat-creator-rfe-autofixer-images.md).
  Pushed SHA `602766cdd96ca857e433385d2c6a2b30f27e5d4f`; GitLab pipeline
  2011, jobs 3898/3899 passed. M4.2 subsequently fixed and proved sandbox
  Jira access below.
- **M4 complete:** [Prepare, commit, and push strat-creator's
  `feat/fullsend-strategy-entrypoint` branch](tasks/done/strat-creator-entrypoint-poc.md).
  Remote SHA `97562dbee8cf2aa792de01160890a6dcfda61cde`; unit tests (509) and
  full suite (773 passed, 1 skipped) passed. The live workflow subsequently passed in M6.
- **M4.2 complete:** [Sandbox Jira connectivity](tasks/done/fullsend-sandbox-jira-connectivity.md).
  Pushed `bd20534f5b904ae7808d167ad3cde671e17d5ab1`; fresh pipelines
  2022/2023 passed. Temporary runner/credentials/branches removed.
- **M5 complete:** [Jira reset and seed](tasks/done/fullsend-strategy-seed-rfe.md).
  `RHAIRFE-1` is eligible; restored bot credentials are in
  `ai-pipeline/fullsend-strategy-jira`. Repeat and strategy Python read passed.
- **M6 complete:** [Real Vertex strategy workflow](tasks/done/fullsend-strategy-poc-integration.md).
  Pipeline 2037/job 3955 created RHAISTRAT-1 from RHAIRFE-1; publication,
  artifact redaction, cancellation, SIGKILL and fresh recovery passed.
  Review recommends revision (5/8, needs-attention).

- **M3 accepted for the POC:** [Fullsend entrypoint implementation](tasks/done/fullsend-entrypoint-feature.md).
  Functional review fixes passed. The user deferred coverage thresholds under
  [ADR-0008](decisions/ADR-0008-defer-poc-coverage-gate.md); the measured 72.73%
  remains below the floor. [Coverage follow-up](tasks/pending/fullsend-entrypoint-patch-coverage.md)
  is due before upstream PR preparation and does not block integration work.
- **M7 complete:** [Maintained runner consolidation](tasks/done/consolidate-gitlab-runner-capabilities.md).
  Capability matrix 2042 passed, including two concurrent OpenShell jobs.
  Runner-only reset, duplicate cleanup, repeat deployment and emulator restart
  leave one registration/ready manager. Post-restart ordinary CI 3976 passed.
  Full wipe control flow was checked with mocked kubectl; service PVCs were preserved.
- **M1–M7 POC delivery milestones complete.** The pre-M8 exact model gate
  is also complete. M8 adds batch delivery; other follow-ups are listed below.
- [Sandbox hooks switch](tasks/pending/fullsend-sandbox-hooks-switch.md)
  remains a separate follow-up, required before configuring an explicit opt-out.
- [Immutable hook installation](tasks/pending/fullsend-immutable-hook-installation.md)
  is a separate investigation and does not gate M3.

- **M1/M2 gates complete:** [Podman inside k3s evidence](notes/podman-in-k3s-m1-evidence.md)
  and [OpenShell Podman gateway evidence](notes/openshell-podman-gateway-m2-evidence.md).
- [Fullsend entrypoint and strategy POC plan](plans/fullsend-entrypoint-strategy-poc.md)
- [M3 Fullsend entrypoint implementation](tasks/done/fullsend-entrypoint-feature.md).
  Scope: Claude only, preserving current strat-pipeline behavior.
- [Strat-creator harness](tasks/done/strat-creator-entrypoint-poc.md)
- [Breadboard integration and validation](tasks/done/fullsend-strategy-poc-integration.md)
- [Final single-runner consolidation](tasks/done/consolidate-gitlab-runner-capabilities.md)
- [One GitLab runner requirement](decisions/ADR-0005-single-gitlab-runner.md)
- [Claude-only POC scope](decisions/ADR-0006-claude-strategy-poc-scope.md)
- [Job-owned OpenShell gateway decision](decisions/ADR-0004-fullsend-ci-owned-docker-gateway.md)

Other existing work remains under `plans/`, `tasks/`, `bugs/`, and `decisions/`.

- [Subagent skill isolation investigation](tasks/done/claude-subagent-skill-isolation-analysis.md):
  completed 2026-10-11; code proof and ten controls confirm child-discovered
  skills reach the primary as availability metadata through the host registry.
  [Report](../scripts/claude_binary_analysis/docs/claude-code-2.1.296-subagent-skill-isolation-analysis.md)
  distinguishes metadata sharing from full instruction loading.

- [Claude Code workflow binary analysis](tasks/done/claude-code-workflow-binary-analysis.md):
  completed 2026-10-11 against official latest 2.1.296; twelve parsed topic
  groups, seventeen evidence-labeled claims, sixteen runtime controls.
  [Report](../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-analysis.md) documents return values,
  failure handling, chained journal resume, scheduling and actual budget wiring.

## Resolved integration bugs

- [Qualified architecture judgments](bugs/fixed/strat-review-gate-mostly-sound-false-negative.md)
  and [numbered reviewer findings](bugs/fixed/strat-review-gate-numbered-findings-false-negative.md):
  checker v2, real-channel replay and negative controls verified without inference.
- [Consistent repeated role judgments](bugs/fixed/strat-review-gate-repeated-judgment-false-negative.md):
  existing handling confirmed by mixed-state replay; stale open status corrected.
- [Dashboard state archive timeout](bugs/fixed/strat-archive-dashboard-state-timeout.md):
  fast Python-compatible gzip, configurable timeout, 16 focused tests and final
  live recovery verification pass.
- [Sandbox Jira connectivity](bugs/fixed/fullsend-sandbox-jira-connectivity.md) — fixed and verified by M4.2.
- [Jira TLS passthrough decision](decisions/ADR-0010-jira-sandbox-tls-passthrough.md).

## Open integration bugs

- [PR 85 review triage](notes/strat-creator-pr85-review-triage.md): scorer-path workarounds and two timed-out guards found inside the successful mixed Opus run; schema/no-runtime-evidence claims distinguished from valid remaining defects.
- [StructuredOutput hook timeouts](bugs/fixed/strat-structured-output-hooks-timeout-fail-open.md).
- [Scorer shell preflight unavailable](bugs/fixed/strat-scorer-recovery-preflight-has-no-shell.md).
- [Review-only round-trip fingerprint](bugs/fixed/strat-review-only-roundtrip-fingerprint.md).

- [Reviewer Skill serialization](bugs/open/strat-reviewer-skills-serialized.md):
  deferred by the user; about six minutes of ideal single-ticket savings does
  not currently justify the concurrency, provenance and recovery changes.
- [Jira processing labels are not atomic leases](bugs/open/strat-jira-label-locks-not-atomic.md).
  Owner-bound recovery/cleanup detects conflicts; cross-host fencing remains a
  separate production qualification requirement.

- [ANTHROPIC_LOG directory warning fixed](bugs/fixed/anthropic-log-directory-warning.md).
  Deferred cleanup; API capture verified working during S2.
- [Model Relay drops telemetry records under load](bugs/open/model-relay-telemetry-drops-under-load.md).
- [Model Relay cuts off upstream calls at 120 seconds](bugs/fixed/model-relay-120s-upstream-timeout.md)
  Inference is unaffected; relay call and token totals are lower bounds until fixed.

- [Jira component ID references silently ignored](bugs/open/jira-emulator-component-id-ref-ignored.md).
  M5 uses verified component names; does not block M6.

- [Deferred Vertex service-account bootstrap capability](bugs/open/fullsend-vertex-service-account-bootstrap.md).

- **M6 credential override:** use Vertex with existing Breadboard credentials;
  dedicated service-account credentials are no longer required for this POC.

- [Downstream bridge scheduling difference](bugs/open/gitlab-emulator-downstream-trigger-runs-before-upstream.md).
- [Local service TLS verification](decisions/ADR-0011-local-strategy-services-tls-passthrough.md).

- [Fixed owned-lock interpretation](bugs/fixed/fullsend-strategy-child-misreads-owned-lock.md).
- [Fixed retained artifact credential redaction](bugs/fixed/fullsend-strategy-artifact-credential-redaction.md).
- [Canceled-job classification difference](bugs/open/gitlab-emulator-canceled-job-status-overwritten.md).

- [Intermittent nested Podman DNS startup](bugs/open/nested-podman-aardvark-dns-startup-intermittent.md).
  Fresh concurrent checks passed; the earlier failure remains unexplained.
- [Emulator skips after_script on failure](bugs/open/gitlab-emulator-after-script-skipped-on-script-failure.md).
  EXIT sanitizer mitigates artifact exposure; intentional failure 2044/3975 verified.
- [Maintained GitLab runner operations](../docs/deployment/gitlab-runner.md).

## Batch logging verification

- [Fresh two-RFE batch after CI progress fix](tasks/done/fullsend-ci-progress-batch-test.md).

- [Results clone HTTP/2 error](bugs/open/fullsend-results-clone-http2-stream-error.md): first attempt failed before writes; retry recovered.
- [Skipped architecture verdict becomes approve](bugs/open/strategy-review-skipped-architecture-recorded-as-approve.md).
- [Fixed long-running active job warning](bugs/fixed/gitlab-long-active-job-marked-stale.md).

- [Remove unused Claude assessment directory permission](tasks/done/fullsend-strategy-unused-directory-warning.md): complete; source 78bc04c, 789 full tests passed (1 skipped), both CI pins published.

- [Two-issue settings/log verification](tasks/current/fullsend-settings-log-batch-test.md): attempt failed at results clone (emulator OOM); retry awaits user decision.

- [Strategy entrypoint startup banner](tasks/done/strat-entrypoint-start-banner.md): complete; 774cf10 pushed, 790 tests passed, both CI pins published.

- [Runner trace offset mismatch and emulator OOM](bugs/fixed/gitlab-runner-trace-range-mismatch-stalls-terminal-status.md): fixed and deployed; 4011 recovered as failed (results clone killed by emulator OOM).

- [Historical Claude stderr replay](bugs/fixed/strategy-ci-replays-historical-claude-stderr.md): fixed in3343f23; trust configured and per-invocation stderr retained.

- [CI trust and stderr isolation](tasks/done/strat-ci-trust-and-stderr.md): complete;3343f23 pushed,792 tests passed, both future CI pins published.

- [Use Fullsend's built-in Vertex provider](tasks/pending/strat-use-builtin-vertex-provider.md): verify credential refresh parity and remove the deprecated reserved profile import.

- [Bash injection scanner false positives](tasks/pending/fullsend-bash-injection-scan-false-positives.md): refine environment-enumeration matching; eight ordinary Bash expressions currently trigger warnings.

- [Webhook sink service](tasks/done/webhook-sink-service.md): deployed as hooksink at `hooksink.local` (`checkouts/hooksink`; renamed from webhook-sink on 2026-10-26). Jira emulator delivery is verified end to end with a long-poll consumer and signatures. Decision: [ADR-0013](decisions/ADR-0013-webhook-sink-in-rust.md). [GitHub end to end](tasks/done/webhook-sink-github-emulator-e2e.md) is done: the emulator now delivers repository webhooks.

- [Visible initial architecture fetch](tasks/done/strat-entrypoint-visible-context-fetch.md): complete;43a6457 pushed,795 tests passed, both CI pins published.

- [One-RFE batch with setup logs](tasks/done/strat-one-rfe-context-log-batch.md): started2067/4021 for fresh8, batch size1, latest entrypoint source.

- [Sandbox policy denies architecture-context Git fetch](bugs/fixed/fullsend-sandbox-architecture-context-git-fetch-denied.md): L7 `read-only` preset denied `POST git-upload-pack`; fixed in strat-creator3fd1563, pins published; live2070/4027 fetch and policy denials verified.

- [Verify sandbox architecture fetch policy](tasks/done/verify-sandbox-architecture-fetch-policy.md): complete;2070/4027 passed live fetch/denials/cleanup,5 fixture checks passed.

- [One-RFE batch after verified policy](tasks/done/strat-one-rfe-verified-policy-batch-start.md): started2071/4029 for freshRHAIRFE-9, size1, verified source3fd1563.

- [Repeat one-RFE batch](tasks/done/strat-one-rfe-policy-repeat-batch-start.md): started2073/4033 for freshRHAIRFE-10, size1, verified policy.

- [Other Claude subagent information channels](tasks/done/claude-subagent-shared-information-analysis.md): complete; six new controls, file-change injection, host/model distinction and dormant nested-memory flag documented.

- [Claude skill variable expansion](tasks/done/claude-skill-variable-expansion-analysis.md): complete; full prompt-placeholder catalog, field/stage differences, nine controls and forty-one exact symbols documented.
