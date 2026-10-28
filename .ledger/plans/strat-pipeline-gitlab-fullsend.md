# Real GitLab strategy pipeline with Fullsend

New work authorized 2026-10-26: prepare a separate branch that migrates all four
regular jobs to the Workflow, preserving config-batch and explicit STRAT
reprocessing with companion strat-creator changes. See the
[cutover task](../tasks/done/strat-pipeline-workflow-cutover.md) and
[implementation/validation notes](../notes/strat-pipeline-workflow-cutover-20261026.md).
These local changes have not been deployed; the rollout status below describes
the previously merged manual smoke integration.

## Scope and authorization

Current rollout status: merged GitLab changes enable opt-in smoke testing
only. There has been no production cutover; the original six-hour executor
is unchanged. Source-branch following applies to the manual Fullsend jobs.

The user approved cloning jtanner1/strat-pipeline into checkouts.tmp, creating
a feature branch from current upstream main, and preparing the implementation.
The first change adds manual opt-in Fullsend single/default-JQL batch jobs,
following rfe-autofixer's example. Existing four strategy jobs and the six-hour
production schedule remain available during qualification. The user subsequently
authorized publishing the branch and opening an upstream MR. Paid or
production-mutating execution remains a separate next step.

User constraints: direct Vertex only, using the existing GitLab-provided
credentials and Fullsend/OpenShell configuration. No model-relay dependency.
Each new run fetches current architecture-context and applicable overlays;
record the resolved source as evidence, never configure a fixed context SHA.
The fetched context remains stable within a prepared run. Default Opus 4.6,
high effort, concurrency ten and one validation iteration.

## Repository and prerequisites

- Origin: https://gitlab.com/jtanner1/strat-pipeline.git.
- Upstream: https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline.git.
- Reference job: rfe-autofixer autofix-rfe-stage-dry-fullsend on current main.
- Starting upstream 3995ac1; fork main fd36b15 (behind the namespace move).
- Qualified candidate: strat-creator PR 85 at 1bcb8f4, still draft/unmerged.
  A production merge should select a reviewed upstream source revision.
- Qualified Fullsend 0.47.1 and Claude 2.1.296; retain published image pins.
- Current fork has no available runners listed. Remote execution requires a
  runner and explicitly provided CI variables; the local GitLab auth token
  is for repository operations, not inference or Jira.

## Implementation and validation

1. Clone without persisting credentials; read local instructions; create the
   feature branch from current upstream main.
2. Add manual jobs with explicit opt-in rules, matching the reference outer
   image/Podman/gateway pattern and versioned strat-creator harnesses.
3. Supply portable host dependencies/preflight and current architecture fetch,
   avoiding the default sparse-checkout sibling-alias defect. Preserve native
   sandbox runtime checks and freshness validation.
4. Wire input validation, unique host state, owned cleanup, validated results
   publication, diagnostics/redaction and a deliberate dashboard trigger.
   Prevent old jobs from also running when a Fullsend job is selected.
5. Run model-free configuration, helper and fault-path tests, then document
   variables, runner requirements, test limits and rollout/MR dependencies.

Config-file batch discovery and deliberate reprocessing of already approved
STRATs are not drop-in mappings to the new harness. Retain their existing
jobs for this first opt-in MR; do not silently turn reprocess into gate-skipping
resume. A later default cutover requires explicit parity work.

## Implemented local branch

This section describes the initial implementation. The config-only consumer
follow-up below supersedes its local wrapper/helper layout.

Checkout: checkouts.tmp/jtanner1/strat-pipeline, branch
feat/fullsend-strategy-workflow, based on current upstream 3995ac1. Origin is
the user's HTTPS fork; upstream is the real group project. Authentication used
an in-memory Git header only; remote URLs contain no credentials. There are no
component-local AGENTS/CLAUDE instructions. No commit, push or MR yet.

The branch adds per-repo base-derived harnesses, manual single/batch jobs,
input checks and Python tests before model work. Legacy jobs are excluded only
when the new executor is selected. Jobs default to dry-run and no publication;
real publication explicitly enables the new dashboard trigger. Results are
published once through the versioned host post-script. The gateway follows
the reference image/Podman/OpenShell structure with readiness, unique private
storage, cleanup and redacted diagnostics.

The two portable bootstrap gaps are bridged in this consumer without changing
the tested strat-creator candidate: current context is fetched on the host,
excluding broken sibling aliases, then imported using its local-context
interface; host preflight checks dependencies while sandbox hooks check Claude.
The native Fullsend CLI rejects a direct URL for the consumer validator, so
setup copies validator/schema from the verified source and checks their hashes.
Generated files and dependency caches are ignored. Generic source-default fixes
in PR 85 remain separate follow-up work.

## Validation and limits

- make test: 87 passed, no model calls. Includes current-HEAD changes between
  runs, stable prior snapshots, unsafe/incomplete context, invalid inputs,
  source/hash mismatch, secret/token redaction, real outer-shell failure/cleanup
  and refusal to execute cleanup from an unverified host clone.
- Native Fullsend 0.47.1 lock passes for single/batch, resolving eleven public
  dependencies each, including direct Vertex provider/profile and plugin.
- Actual live context fetch passes against current HEAD 2f3ab4077471bf1670fca16da57e7a48c244d066,
  rhoai-3.6-ea.2 plus overlays. This is observed provenance, not a configured pin.
- GitLab.com CI lint validates the expanded include and default/single/batch
  graphs without errors/warnings. Default dry-run source is push; manual cases
  explicitly override CI_PIPELINE_SOURCE to web only in submitted lint content.
  The initial simulator expectation omitted this and was corrected.
- Lint also exposed an existing null-input dashboard rule; corrected on this
  branch, with [upstream merge pending](../bugs/open/strat-pipeline-null-input-dashboard-trigger.md).
- Shell/Python compile and git diff checks pass. Earlier missing-platform test
  fixture deleted the entire newest Git directory; retaining a component file
  makes that intended invalid-context case meaningful.

Real runner/image build/OpenShell/Vertex execution and publication remain
unqualified on this new branch. The personal fork has no runners listed and
must receive appropriate credentials/runner access before an authorized smoke.
The paid smoke and any subsequent batch are not launched by this task.
The source pin remains dependent on draft PR 85; select reviewed upstream source
before production cutover. Existing scheduled production behavior is preserved.

## Publication: 2026-10-20

The user authorized creating the upstream merge request. Rechecked GitLab.com:
upstream main remains 3995ac1, the source branch did not yet exist remotely,
and no matching open MR existed. The pre-publication suite passes all 87 tests
in 16.05 seconds; shell syntax, Python compilation and staged diff checks pass.
The fifteen staged source files contain no matches for checked local credential
values. Generated state, credential files and dependency caches are excluded.

Created signed-off commit 7402726b79f4715ee4fa5b92d6d6a208a2dd68ef and pushed
origin/feat/fullsend-strategy-workflow. Opened
[upstream draft MR !15](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/15)
from jtanner1/strat-pipeline into redhat/rhel-ai/agentic-ci/strat-pipeline:main.
Read-back confirms the expected source/target projects, branches and commit,
one MR commit and no conflicts. The component checkout is clean.

GitLab CI lint against the published branch, using its real local include,
passes without warnings/errors and selects only python-tests on a default push.
The MR automatically created model-free pipeline 2967607300, initially pending.
No Fullsend/model job or production mutation was launched. The MR remains draft
for the real-runner image/OpenShell/Vertex smoke and the PR 85 source dependency.

## Consumer simplification: 2026-10-20

The user requested the smallest practical pipeline footprint, matching
rfe-autofixer's single `.fullsend/config.yaml`. Implemented and published:

- Source package 85e5cb301726533653feaee560582b307fb15eb7 in PR 85 supplies
  `.fullsend/ci/` launcher, gateway, dependency image, versions, input/context
  preparation and redaction, with tests moved to `test_fullsend_ci.py`.
- Harnesses own concurrency/model/background-wait defaults and host dependency
  preflight; sandbox runtime guards remain. The gateway uses Fullsend's standard
  FULLSEND_SANDBOX_IMAGE override instead of a consumer wrapper.
- Pipeline d123c1955d9ebf1a1374a4d960487731909bc4cc registers remote harnesses
  directly. Existing `.gitlab-ci.yml`, README and CI tests hold the deployment
  configuration and guide. Compared with upstream, only five files change;
  only config.yaml is added. The two wrappers, six CI helper files, separate
  CI include, guide and helper-test file are removed from the consumer.

The published 0.47.1 binary does not fetch every companion for direct agent
registration: a real config-only lock fails on the missing plugin. The shared
setup verifies the source commit and harness hashes, then copies companions
from that clean source into `.fullsend-state/<job>/fullsend`, along with an
unchanged copy of the remote registrations. Generated runtime files are not
maintained in the consumer. The old local generated cache/validator files are
preserved at `/tmp/strat-pipeline-before-minimal/generated-fullsend`; the actual
consumer `.fullsend/` directory now contains only config.yaml.

Validation: 1,118 source tests pass with six optional skips; 69 pipeline tests
pass, with all 30 CI contract checks rechecked after source-pin changes. Native
actual CI bootstrap fetches published 85e5cb3, verifies registrations, prepares
the runtime, and Fullsend locks both agents with three remote dependencies each.
Evidence is `/tmp/strat-minimal-ci-validation-result.json` and referenced logs.
Six GitLab compiler cases (push, MR, single, batch, publication, schedule) pass
without warnings/errors. Lint, syntax, whitespace and credential-value checks
pass. Both components are clean after push; MR 15 description reflects the final
implementation and qualification limits. No paid model call or production write.

Final remote read-back confirms both feature heads; GitLab MR pipeline
2967970795 succeeds on d123c19. The production smoke remains separate.

## Onboarding compatibility check: 2026-10-20

Read all current PR 85 conversation/review/inline comments and fetched onboarding
PR 86. Current heads 85e5cb3 and 03305e0 have merge base b396172. Native
`git merge-tree --write-tree` succeeds with merged tree
8ae5ae86818815d3c17f06a03387989dd973efae and no overlapping changed paths.
The checkout remains clean; this was an object-only trial, not a branch merge.

The original config-file collision is gone because PR 85 no longer adds it.
However, the reviewer's later correction says to retain and extend the committed
onboarding config, rather than omit it and regenerate from a fleet. The merged
config contains only generic agents, not the three strategy agents. Record the
[registration/documentation follow-up](../bugs/fixed/strat-creator-onboarding-registration-guidance.md).
The GitLab consumer's existing registrations are separate and unaffected.

## Merged onboarding reconciled: 2026-10-20

After the user merged PR 86 to main as 9c87d83, merged that upstream main into
the feature branch and published signed-off 8b2f1e0. The combined committed
config preserves onboarding settings and both workflows, adding the three
strategy registrations and allowlist. Documentation, example, ignore guidance,
the real-config tests and PR 85's stale registration paragraph are corrected.

Full source suite passes 1,118 tests with six optional skips in 279.25s. Full
lint/type checks pass after fixing a pre-existing pull-test import-format issue.
Native Fullsend passes twelve actual-config harness/dispatch checks and locks
all three strategy agents. No business Workflow or skill code changed here.

Consumer signed-off 0825ea4 points to source 8b2f1e0 with matching hashes; its
single registration file layout remains. All 69 pipeline tests, actual published
source bootstrap/native locks and published GitLab CI lint pass. The receipt is
`/tmp/strat-minimal-consumer-53b9ph6g/result.json`; prior model-free receipts are
preserved. Source/consumer heads and MR target main are read back remotely.
Both checkouts are clean. No paid strategy run or production Jira mutation.

[Completed reconciliation](../tasks/done/strat-creator-reconcile-onboarding.md).

Final GitLab pipeline 2968225182 succeeds on consumer 0825ea4; MR read-back
confirms no conflicts and upstream main as target.

## Real agentic-ci runner smoke: 2026-10-20

The personal fork has no runners or secrets. With user authorization, copied
the reviewed consumer 6f996e2 to a temporary protected upstream branch, retaining
source 080700e, Opus 4.6/high, one validation iteration and direct Vertex.
No merge is required to use the existing agentic-ci group runner.

Schedule pause returned 403. Production scheduling remains active. A smoke-only
CI fixture commit f5dfb0e on the temporary branch qualifies RHAIRFE-3739 only
while its job owns the same `strat-batch` resource group as production, then
removes only its labels in after-script cleanup. The source/fork MR remains
unchanged. Four fixture contract checks and all 69 pipeline tests pass.

Real runner tests and input checks pass. The first runtime attempt stopped
before model execution because Fullsend 0.47.1 requires its registered GitLab
Analyst token even for this Jira workflow. Jira/Vertex credentials, current
context, sandbox build and gateway setup passed; fixture/gateway cleanup was
independently verified. This is an environment/preflight gap, not a failed
strategy run. [Required secret/documentation follow-up](../bugs/fixed/strat-fullsend-gitlab-role-preflight.md).

A short-lived project-scoped Analyst token is masked, hidden and protected;
the personal management token remains outside CI. Job 17329828389 retries the
zero-model setup failure in pipeline 2969118303. Execution, business validation,
artifact review and temporary-credential revocation remain pending.
[Execution task and archive](../tasks/done/real-gitlab-strategy-single-smoke.md).

### Completed: real runner dry-run passes

Job 17329828389 succeeded in 24m58s, including 15m45s agent runtime and about
8m17s setup. One Opus 4.6 iteration creates/refines/reviews local STRAT-3739
for RHAIRFE-3739, 8/8 approve, zero business errors. Trusted host validation
and post-script handoff pass. Four specialist assessments and the scorer were
inspected from retained transcripts; feasibility/architecture disagree on a
frontend detail, and the configured numeric gate approves. This is a
functional smoke, not independent content-quality adjudication.

Model-reported cost is $5.836762; 4,280,118 tokens including cache operations,
without adding the separate reasoning counter again. The 40-file archive
contains native result, metrics, transcripts and runtime/security logs. The
final strategy/review files remained in a private handoff directory and were
not uploaded. [Business export follow-up](../bugs/open/strat-fullsend-ci-business-artifact-export.md)
and role-secret preflight/docs remain necessary; six transcript excerpts are
saved as excerpts, not represented as canonical final files.

Fixture labels restored, Jira has no linked strategy, gateway cleanup passes,
the temporary Analyst token is revoked/variable removed and the production
schedule remains unchanged. No merge was required. Live Jira strategy writes
and downstream publication remain a separate qualification step.

Local comparison confirms that the earlier successful 2100/4068 run used the
same Fullsend 0.47.1 and logged the selected Analyst role/secret at
02:13:35 UTC on 2026-10-19. The local environment already supplied it; the
real project did not. The missing-secret failure is a deployment prerequisite
omitted from this adaptation's docs/preflight, not a new version requirement.

The real rfe-autofixer reference remains pinned to Fullsend 0.43.0 on main
efc285d (CI line 194), which predates 0.47.1's mandatory role-token selection.
Its latest listed Fullsend jobs are manual/unstarted; no runtime qualification
was inferred or attempted. Reusing its job layout while upgrading Fullsend
required a separate credential-contract check.

Source-level refinement: 0.47.1's role selector checks nonempty presence, not
token validity. An invalid nonempty value passes selection and is exported
as GITLAB_TOKEN. Later GitLab requests would fail; status-comment failures
are warnings. A Jira-only path might never use it, so a live project token
is not yet proven necessary for this workload. A placeholder/full-path test
has not run, and no placeholder was configured. See the role-preflight bug
for exact code references and the correction to earlier advice.

### Reuse the existing results token for Fullsend

The user chose explicit reuse of `RESULTS_PUSH_TOKEN` for the Analyst role,
accepting that GitLab API permissions can be revisited if production needs
them. Published consumer commit `d27a314` to the existing MR !15 branch.
Fullsend CI now disables tracing and exports the token as
`FULLSEND_GITLAB_ANALYST_TOKEN` before dependency/source/gateway setup. A
missing or whitespace-only token fails immediately, including dry runs.
README documents this requirement, the token's existing write permissions
and the unverified API/project access. No additional role secret is required.

All 74 pipeline tests pass; five new shell checks exercise inheritance,
no secret trace output and early rejection with no network or model calls.
The shared strategy source and pins are unchanged. No production run or live
secret change was performed. The preflight/docs bug is fixed in the feature
branch; business-artifact export remains a separate open follow-up.

### MR !15 ready for review

Removed Draft and refreshed the MR description on 2026-10-20. Pre-write checks
confirm expected head d27a314, passing CI pipeline 2969641024, no conflicts and
resolved blocking discussions. Remote read-back confirms `draft=false` and
the updated description; review status is `not_approved`. No merge requested.
The opt-in trial is ready for review with implemented data-repository
publication and the real dry-run evidence stated accurately. Live publication
qualification, the standalone CI archive export and selection of a reviewed
upstream strat-creator revision remain documented follow-ups.

### Merged main and first live canary: 2026-10-21

MR !15 merged as 38efbce; main CI 2972210515 passes. The original six-hour
schedule remains active, and Fullsend is still selected only for manual
web/API pipelines. The source remains the tested fork pin 080700e.

The user authorized one live single-ticket canary for existing RHAIRFE-3739.
Pipeline 2972360596 passed input checks/74 tests, then job 17351822419 ran
once with Opus 4.6/high and publication enabled. It creates/refines linked
RHAISTRAT-3027 and publishes an 8/8 review comment/attachment. The upload's
verification download redirects to api.media.atlassian.com, blocked by the
sandbox's Jira-only policy. The reviewer then reruns publication with --dry-run
and records completion without the live verdict label. The main agent reports
success, but the trusted host validator rejects the missing label and skips
data-repo/Org Pulse publication and the dashboard trigger.

Job fails after 27m25s, agent about 18m37s; model-reported $5.64756225 and
3,112,337 tokens including cache operations. No additional model attempt.
Failure recovery preserves actual business files in the native ZIP; Jira's
uploaded review is independently byte-verified. Fixture/owner/sandbox/gateway
cleanup and unchanged production schedule are verified. Canonical run-path
absence confirms publication did not occur. This is a failed live qualification,
not a successful publication test or a token-authentication failure.

Next implementation work at diagnosis: [allow verified attachment media access](../bugs/fixed/strat-fullsend-jira-attachment-media-egress.md)
and [reject live dry-run substitution/incomplete publication receipts](../bugs/fixed/strat-live-review-dry-run-fallback-completes.md).
Keep the existing final live-readback gate. [Execution/archive evidence](../tasks/done/real-gitlab-strategy-single-live-canary.md).

### Branch-based source selection: 2026-10-21

The user requested avoiding a pipeline MR for every source commit. Source
commit 630fcca in existing PR #85 now accepts branch registrations and creates
private commit/hash registrations from each job's already fetched snapshot.
Legacy commit/hash consumers still work. Source provenance records the branch,
observed commit and actual harness digests.

Consumer caaf92e, new branch feat/fullsend-follow-source-branch from merged
main 38efbce, is published in [MR !16](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/16).
It follows feat/s1-workflow-hardening in the user's fork. The committed
registration URLs have the branch and no maintained hashes. Bootstrap fetches
that branch once per job and exports its observed commit internally; runtime,
source clone, hooks and validators never refresh to a later branch head.
No extra source files are added to the consumer's .fullsend directory.

Full source suite 1,142 passed/six optional skips, pipeline 79 passed, lint/type
checks and diff checks pass. Actual published-source bootstrap and native
Fullsend locks pass for both agents. Six GitLab compiler scenarios pass,
preserving legacy scheduling and manual/publication gates. MR !16 is ready
for review, no conflicts, awaiting approval; its first CI was running on read-back.
The new behavior takes effect after merge, with no paid canary or production
change in this task. Attachment egress and live dry-run fallback remain open.
[Implementation/evidence](../tasks/done/strat-pipeline-follow-source-branch.md).

### Live media/publication fixes in PR #85: 2026-10-21

Published signed-off 02dd13b to the existing feature branch and verified the
PR head. The Python-only Jira policy now allows api.media.atlassian.com:443.
Attachment download authenticates only to the exact Jira origin, follows
bounded redirects and rejects HTTPS downgrades. Existing exact-byte upload
reconciliation remains required so a committed upload is not repeated after
a blocked readback.

A prepared live run cannot substitute --dry-run or silently fall back for
missing credentials. record-review now independently verifies the exact Jira
summary, attached review and expected numeric label before recording live
completion. Missing/conflicting effects fail without completing progress.
Standalone and intentional prepared dry runs still work; numeric-only
approval/dissent are unchanged. No network checks were added to fast hooks.

Local regression tests reproduce partial publication, reject the fallback,
then recover without duplicate comments/uploads. The repaired client reads
the existing cloud attachment with no mutation and matches archived bytes.
Full source suite: 1,158 passed, six optional skips; lint/type checks and
secret/diff checks pass. Actual published-source CI bootstrap and native
Fullsend single/batch locks pass with zero model calls.

Both diagnosed bugs are fixed in source; the original live canary remains
failed, and a new real OpenShell live qualification has not run. MR !16 is
still the consumer rollout step; it was not merged here. No live Jira repair,
paid retry or production schedule change.
[Implementation/evidence](../tasks/done/strat-live-review-media-and-publication-guards.md).

### Branch-following consumer merged: 2026-10-21

User reports MR !16 merged; API read-back confirms merge at 16:45:16Z and
upstream main fe9ca62. Main push CI 2972994099 succeeds. Main's variables and
both agent registrations select the source feature branch without a maintained
SHA; its current head is the tested 02dd13b media/publication fix. Each job
still resolves one immutable snapshot. No new pipeline was launched.

The six-hour production schedule remains on the legacy executor. Fullsend
single/batch jobs remain manual for web/API pipelines. The next qualification
is a live single-ticket canary using the repaired branch; the old canary
remains failed. Read-back receipt: /tmp/strat-mr16-postmerge-status.json.

### Retry readiness and existing strategy: 2026-10-21

Read-only preflight confirms RHAIRFE-3739 is Approved, retains its quality
labels and is outside release scope. Its sole Cloners link is RHAISTRAT-3027,
still New, unresolved, with no final verdict label or processing/owner lock.
The partial run's review attachment remains. Main is fe9ca62, runner online,
no running/pending pipelines, next legacy schedule 22:00Z at this check.

Do not close the strategy merely to retry. The configured discovery and Skill
gates treat a linked Closed/Resolved strategy as completed and skip its RFE;
they do not automatically create a replacement. The current early-state,
unprocessed clone can be imported by a fresh single-ticket run and processed
again with current freshness baselines. This is reuse of existing Jira work,
not native Workflow replay or a fresh-clone test. Temporarily restore only the
RFE's run eligibility and clean it up afterward. A new-clone test would need
a separate synthetic RFE or explicitly reconciled replacement, not closure
alone. No Jira change or model launch performed. Read-back receipt:
/tmp/strat-retry-readiness.json.

### Ticket reuse is not publication-only recovery

The user's idempotence question exposed an important distinction. A fresh
GitLab single-ticket job imports the existing Jira clone, but does not
automatically restore the failed job's workspace, composed review, effects
journal or previous progress. The auto-refined Jira label alone never proves
that saved refinement is reusable. prepare_run.resume_point requires explicit
previous progress with a matching verified push and no recorded review to
select review-only; otherwise it selects refine. Even that reuse requires
unchanged source/instructions, architecture and live inputs. This canary's
source has changed and its old progress incorrectly recorded review complete.

Consequently the proposed ordinary retry would re-refine and re-review the
same clone; it is a duplicate-clone/reprocessing smoke, not proof of
publication-only idempotence. Same-workspace recovery can reconcile an intact
current-run composed review without rescoring or specialist calls. A focused
live publication repair using archived review bytes would be a separate,
explicit operation, preserving evidence and verifying existing effects rather
than pretending old artifacts satisfy the changed Workflow provenance.
No recovery script, Jira repair or paid retry was executed for this question.

### Publication-only idempotence recovery passed: 2026-10-21

The user authorized the focused recovery. At 19:20:19Z the current versioned
publisher completes RHAISTRAT-3027's publication from the exact archived review,
without refinement, scoring or specialist calls. Verified archive hashes,
provenance and all original reports; live strategy/SME content matches the
saved push, and RFE content/comments match after accounting for the original
cleanup's two removed fixture labels. Existing summary and attached review
match exactly. Numeric 8/8 approval and testability dissent remain intact.

Preserved the original failed run, input/progress/freshness and effects. A
standalone artifact export plus a copy of its effects journal reconciles the
pending upload through media readback. Only the missing numeric verdict label
is added: one Jira PUT. A second publisher/verification pass makes zero writes
and leaves Jira snapshots identical. One comment and one attachment remain;
no strategy/RFE content, status, links, fixture eligibility or schedule changes.
Transport audit blocks unexpected/new POSTs and every second-pass mutation.

Zero model calls/tokens. The 89-file archive passes hashes, audit and configured
credential checks at var/run-data/20261021-real-jira-publication-idempotence-recovery/.
This is a successful standalone publication repair/idempotence test, not a
successful GitLab rerun. OpenShell policy, data-repo push and dashboard were
not exercised. A future fresh CI smoke needs another synthetic fixture because
this strategy now carries its final label; do not clear it merely to retest.
[Execution and evidence](../tasks/done/strat-live-publication-idempotence-recovery.md).

### Org Pulse compatibility merged: 2026-10-21

After the user's notification, GitHub API verifies PR #1789 merged at
14:05:03Z into upstream main as 7ba9353e, from expected head 80746a8a.
The compatibility change accepts an architecture assessment marked skipped,
continues rejecting pending assessments and preserves numeric decisions and
specialist dissent. Its source dependency is resolved. Previously completed
checks remain 6,382 passed/eleven skips and full lint; no new code changed.

This merge check does not establish which revision production Org Pulse runs
or prove live ingestion from Fullsend. No deployment, Jira mutation, CI launch
or model call. Receipt: /tmp/org-pulse-pr1789-merge-status.json.

### Follow-up PR #85 findings repaired: 2026-10-21

Fetched/refreshed all 116 review/conversation entries and assessed current
technical findings on 02dd13b, including both cleanup failures sharing one
finding ID. Published signed-off b3c10ec and verified PR #85's remote head.
Fixes cover strict dry-run inputs, stale/partial owned cleanup, reconstruction
of prepared Business Need, sealed skip-only history and skip reasons, concurrent
summary regeneration, empty Org Pulse export and documentation nits. README
links the owner repository's merged consumer contract. Numeric-only approval,
dissent, freshness and uncertain-write safeguards remain intact.

Local regressions reproduce the failures and a real two-publisher Git race.
Full suite: 1,189 passed/six optional skips, 346.81s; focused: 108 passed.
Lint/types, shell syntax, diff and configured-secret checks pass. Actual
published-source bootstrap and native single/batch locks pass. Fifteen-file
archive plus manifest: var/run-data/20261021-strat-pr85-followup-review-fixes/.

Integration remains opt-in smoke testing; no production cutover. No live Jira
mutation or strategy model run. Formal protected-path authorization/human
approval and anticipated additional security feedback remain follow-ups, along
with a fresh real GitLab/OpenShell smoke. No Stoyan security review appears in
the fetched snapshot; no review reply or thread resolution was sent.
[Dispositions](../notes/strat-creator-pr85-review-20261021.md).

### Fresh real GitLab smoke after follow-up review fixes: 2026-10-21/22

The user authorized proceeding without waiting days for additional security
feedback. One fresh synthetic CSV-inventory RFE, RHAIRFE-3748, is processed
by Opus 4.6/high using b3c10ec and merged consumer main fe9ca62. Pipeline
2974269929/job 17366396650 passes in 27m00s; strict final validation and live
Jira publication pass. RHAISTRAT-3038 has one matching review attachment,
one comment and rubric-pass; numeric 8/8 approval preserves feasibility
reviewer's revise dissent. Sealed data publication and both summaries verify
at data-repo commit 5205dca. Owned lock and temporary fixture labels are
released, and the legacy schedule remains unchanged.

Downstream delivery remains incomplete. Org Pulse rejects the TLS chain
for all 42 aggregate batches (zero ingested); dashboard pipeline 2974334519
cannot authenticate its data-repo clone, before dashboard generation. The
export is non-blocking and the trigger does not propagate downstream failure,
so a green parent alone is insufficient. Both failures have open bugs and can
be diagnosed/repaired using saved outputs without another model run.

Metrics estimate 3,024,433 combined tokens and $5.25737975, not invoice cost.
Sixty-two files plus SHA manifest, native ZIP, fourteen publication content
hashes, exact Jira review bytes and configured-secret scan verified. Archive:
var/run-data/20261021-real-gitlab-fresh-single-opus46-postreview/.
[Full result](../tasks/done/real-gitlab-fresh-single-smoke-after-review.md).
This remains opt-in smoke testing, with no production cutover. No further
model run, credential change or downstream retry was performed for analysis.

### Temporary Org Pulse TLS exception approved and published

The user explicitly chose to disable Org Pulse certificate verification for
now after discussing the legacy behavior and trust failure. Signed-off
85e8307 restores that behavior only for the exporter's request-local SSL
context and documents its temporary nature. No global trust change or sandbox
policy change. Full make test: 1,190 passed/six optional skips; local real
HTTPS fixture reproduces rejection before the fix and successful upload after.
Lint/types, diff and three-file configured-secret scan pass. PR #85 remote
head verified; branch-following CI needs no consumer change. Permanent CA
trust remains an open follow-up. No live export retry, model run, dashboard
credential repair or production cutover occurred.
[Task and evidence](../tasks/done/strat-org-pulse-temporary-tls-bypass.md).

### Downstream-only recovery and dashboard fix: 2026-10-22

The user authorized the two remaining tasks. No new strategy/model run.
Local DNS cannot resolve the internal Org Pulse API, so used an isolated
export-only job on the real GitLab runner. Pipeline 2976666017/job 17383298312
verifies the immutable run/seal and replays only RHAISTRAT-3038 with source
85e8307. Before 404, one feature created/no validation errors, after 200.
Original run/source RFE, numeric 8/8 approval and feasibility revise dissent
read back correctly. This confirms actual ingestion, not just TLS connectivity.

Dashboard diagnosis now proves its DATA_REPO_TOKEN is present but fails Git
authentication. A temporary working credential makes the build pass, exposing
stale copied JSON caused by later legacy summary readers omitting identified
runs. Regenerating local summary JSON with the same hardened reader as HTML
fixes the output mismatch. The dashboard's native CI_JOB_TOKEN also passes
Git read, removing the need for a new static secret or variable-admin access.

Ready dashboard MR !7 implements the one-file permanent fix at 6a9085d:
process-scoped job-token Git auth, regenerated summaries, source branch input
(default main) and API builds. Exact pipeline 2976991608/Pages job 17385905560
passes with no credential override. Native artifacts verify the strategy/run
in HTML, individual JSON and aggregate JSON, including dissent. CI lint and
local configuration/embedded-code checks pass. MR approval is required and
pending (not_approved); no merge or main/project-variable change. Default
reader support still follows the merge of strat-creator PR #85; the smoke
selects the hardened fork/branch explicitly. No engine cutover.

Retained all three diagnostic/final dashboard builds, the scoped Org Pulse
replay, payload/seal/readbacks, traces/ZIPs, source/config receipts and
unchanged-schedule proof under
var/run-data/20261022-strat-downstream-publication-recovery/.
No claim of live browser/Pages URL readback; management metadata is forbidden
for the Developer account. Required approval before landing MR !7 is the
remaining action. Extra model tokens/cost: zero.
[Task](../tasks/blocked/strat-downstream-publication-recovery.md).

### Dashboard authentication was already broken before this work

Historical API/job audit confirms the same data-repo authentication rejection
on September 28 (pipeline 2891274781, job 16793120645) and September 29. PR #85
opened October 15 12:37Z; pipeline MR !15 was created October 20. The failure
therefore predates both. All 100 fetched dashboard main pipelines (September
28 through October 22) are failed; sampled old traces establish the matching
authentication cause, without claiming all 100 failures share it or that the
oldest sampled failure was the first. Workflow smoke exposed an existing
credential defect. The new publication format's reader/JSON compatibility
is separate. Twelve-file history archive plus verified manifest:
var/run-data/20261022-strat-dashboard-auth-history/.
