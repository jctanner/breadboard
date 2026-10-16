# Project work index

## Current milestone

- [PR 85 remediation](tasks/done/strat-creator-pr85-remediation.md): pushed fixes f941955, 21 original threads addressed, native/default checks passed; no paid inference.
- [PR 85 historical DCO](tasks/pending/strat-creator-pr85-historical-dco.md): 15 older unsigned commits; history/author certification requires a separate decision.

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

- [Consistent repeated role judgment rejected](bugs/open/strat-review-gate-repeated-judgment-false-negative.md).

- [Qualified architecture judgment rejected by the benchmark](bugs/open/strat-review-gate-mostly-sound-false-negative.md).
- [Delivered numbered feasibility findings rejected by the benchmark](bugs/open/strat-review-gate-numbered-findings-false-negative.md).
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

- [Visible initial architecture fetch](tasks/done/strat-entrypoint-visible-context-fetch.md): complete;43a6457 pushed,795 tests passed, both CI pins published.

- [One-RFE batch with setup logs](tasks/done/strat-one-rfe-context-log-batch.md): started2067/4021 for fresh8, batch size1, latest entrypoint source.

- [Sandbox policy denies architecture-context Git fetch](bugs/fixed/fullsend-sandbox-architecture-context-git-fetch-denied.md): L7 `read-only` preset denied `POST git-upload-pack`; fixed in strat-creator3fd1563, pins published; live2070/4027 fetch and policy denials verified.

- [Verify sandbox architecture fetch policy](tasks/done/verify-sandbox-architecture-fetch-policy.md): complete;2070/4027 passed live fetch/denials/cleanup,5 fixture checks passed.

- [One-RFE batch after verified policy](tasks/done/strat-one-rfe-verified-policy-batch-start.md): started2071/4029 for freshRHAIRFE-9, size1, verified source3fd1563.

- [Repeat one-RFE batch](tasks/done/strat-one-rfe-policy-repeat-batch-start.md): started2073/4033 for freshRHAIRFE-10, size1, verified policy.

- [Other Claude subagent information channels](tasks/done/claude-subagent-shared-information-analysis.md): complete; six new controls, file-change injection, host/model distinction and dormant nested-memory flag documented.

- [Claude skill variable expansion](tasks/done/claude-skill-variable-expansion-analysis.md): complete; full prompt-placeholder catalog, field/stage differences, nine controls and forty-one exact symbols documented.
