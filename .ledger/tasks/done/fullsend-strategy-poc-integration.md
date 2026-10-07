# M6: Recreate strat-pipeline in local GitLab and run the seeded RFE

Follow steps 4 through 6 of the
[POC plan](../../plans/fullsend-entrypoint-strategy-poc.md).
Hard dependency satisfied: [M1 Podman in k3s](../done/podman-in-k3s-feasibility.md) passed.
The [M2 stock OpenShell gateway check](../done/openshell-podman-gateway-m2.md)
also passed, selecting Podman. The full strategy POC depends on both feature
branches. Follow the plan's rebased rfe-autofixer reference for TLS,
credentials, and output handoff. Use the shared image set validated by
[M4.1](../done/strat-creator-rfe-autofixer-images.md); M2's original image evidence
does not establish compatibility of that replacement.

## Acceptance criteria

- [x] Require the [pushed M4 branch](../done/strat-creator-entrypoint-poc.md),
  its [M4.1 image pivot](../done/strat-creator-rfe-autofixer-images.md),
  [M4.2 sandbox Jira connectivity](../done/fullsend-sandbox-jira-connectivity.md), and
  [M5 seeded RFE](../done/fullsend-strategy-seed-rfe.md).
- [x] Recreate/adapt the `strat-pipeline` project and CI workflow in
  `gitlab.local`, retaining relevant manual rules, resource groups, artifacts,
  results publication, and downstream dashboard behavior.
- [x] Fetch `https://github.com/jctanner-opendatahub-io/strat-creator.git`
  at `feat/fullsend-strategy-entrypoint` for both Fullsend files and skills.
  Use that same checkout as `--target-repo` and its `.fullsend` as
  `--fullsend-dir`; record the resolved commit in each run. Do not substitute
  public upstream `main` or a GitHub-emulator mirror for this source.
- [x] Build/use Fullsend from its feature commit with entrypoint support;
  add the hooks-switch commit if the harness selects the explicit opt-out.
- [x] Confirm M1 passed with recorded evidence before starting this task.
- [x] Select Podman based on M2 evidence.
- [x] Initial acceptance scope: one seeded RFE through `single-rfe`.
- [x] Prove a CI job can bootstrap its own OpenShell gateway and stock sandbox.
- [x] Prove job/gateway/sandbox connectivity and TLS to local services.
- [x] Verify per-job isolation, artifact collection, and cleanup on failure/cancellation.
- [x] Run without a central OpenShell gateway connection.
- [x] Trigger `single-rfe` for M5's issue key and verify real Claude create,
  refine, review, lock release, expected Jira updates, results commit, logs,
  and artifacts. Verify Org Pulse publication separately from job success.
- [x] Complete additional job types if selected and record failure recovery.
- [x] Record reproducible evidence and remaining production differences.
- [x] Hand durable deployment/reset consolidation to [M7](../done/consolidate-gitlab-runner-capabilities.md);
  M6 used the maintained runner without adding a temporary registration.
  M7 was pending at this handoff and subsequently completed; see its task.

## Status

Complete on 2026-10-06. Third of the three delivery milestones agreed on 2026-10-05.
Earlier progress entries below are historical; final acceptance supersedes them.
Record project/pipeline/job URLs, fork branch and resolved SHA, Fullsend/image
versions, Jira issue key, and result references. Reuse the existing platform
runner with proven Podman/OpenShell capabilities; each job owns its gateway.
The final single-runner deployment/reset regression remains M7.

## M4.1 handoff

The shared-image branch is pushed at
`602766cdd96ca857e433385d2c6a2b30f27e5d4f`; pipeline 2011, jobs 3898/3899
passed the image/gateway smoke. M4.2 owns the sandbox Jira fix: M4.1 reported
a DNS hang and a timeout to the ClusterIP, despite successful runner-side
access. Require M4.2's proof and recheck authenticated sandbox Jira access
after M5's reset, before any strategy run.
Recheck GitLab/GitHub/Org Pulse from the sandbox as already required.
Use the existing Breadboard Vertex credentials under the user override
recorded below; the earlier dedicated-service-account requirement is superseded.

## M4.2 handoff

The fork now resolves to pushed SHA
`bd20534f5b904ae7808d167ad3cde671e17d5ab1`. Fresh CI pipelines 2022/2023
proved Jira GET APIs through the actual strategy Python path and applied
sandbox policy, certificate/hostname checks, rejection without the local CA,
public allowed/blocked egress, output handoff, and cleanup. Service permissions
are in the base policy; Jira alone uses an opaque TLS tunnel with client CA
verification. Public GitHub remains under enforced read-only HTTP inspection.
M4.2 corrected the earlier routing hypothesis; supervisor private-CA trust
was the remaining failure after policy attachment was corrected.

The emulator accepts any Basic password in its current permissive mode.
The probe proved intended identity propagation, not password validation.
Recheck identity, auth mode, and trust after M5 resets Jira. GitLab/Org Pulse
retain inspection rules and still require this milestone's verification.
The reusable read-only check is under
`var/demos/fullsend-entrypoint-poc/jira-connectivity/`.

## M5 handoff

Jira-only reset and seed are complete. Use `RFE_KEY=RHAIRFE-1`:
**Add rhai-cli diagnose subcommand for RHOAI deployment health checks**,
status New, priority Major, type Feature Request, component CLI. Its marker is
`fullsend-entrypoint-poc-m5`; current config gates pass with
`strat-creator-3.5` and `rfe-creator-autofix-rubric-pass`. There are no strategy
links, attachments, locks, or processed-work markers. The source fixture's
full content is preserved, and the branch's discovery JQL and actual Python
issue read passed. Repeatable recipe:
`var/demos/fullsend-entrypoint-poc/jira-seed/README.md`.

The new dedicated CI identity is `aipcc-agentic-jira-bot`, restored after
reset. Provision `JIRA_SERVER`, `JIRA_USER`, and Basic-password `JIRA_TOKEN`
from `ai-pipeline/fullsend-strategy-jira` without printing its data. That secret
also holds `JIRA_BEARER_TOKEN` for actual Bearer PAT consumers; it is distinct
from the password. Valid/invalid Bearer identity checks passed. Basic auth is
still permissive; recheck the new bot and CA trust inside the actual sandbox
before running skills. M4.2's original smoke used deployed admin credentials,
so it does not establish this bot's post-reset sandbox access. No M6 workflow
or strategy/model run was started in M5.

## M6 implementation progress (2026-10-06)

- Added the reproducible `var/demos/fullsend-entrypoint-poc/strategy-ci/`
  publisher, pinned public-fork checkout, separate feature-binary build,
  manual single-RFE entrypoint job, read-only sandbox connectivity gate,
  30-day always-collected artifacts, and downstream dashboard trigger.
- Live project resolves to ID **7**; results project ID **8**, dashboard ID **9**.
  Existing native main is `14d81319af44973d592e4197b14b680684f35813` and is
  preserved. First POC branch publication was
  `0c44c45c9d36ad476ab256079fc046624cdfe062`; subsequent publication includes
  the connectivity gate and build prerequisite correction.
- Exactly one existing runner registration was found. Enabled privileged
  Podman and two per-job emptyDirs on its current ConfigMap and restarted
  the existing manager. No additional runner was registered. Authoritative
  deployment/reset persistence and convergence are still M7.
- M5 bot Basic credentials are provisioned directly from its Kubernetes
  secret without printing values. Existing `RHAISTRAT_GITLAB_TOKEN` and
  `RHAISTRAT_ORG_PULSE_TOKEN` are reused under harness-compatible names.
- Credential metadata inspection found `authorized_user` both in
  `ai-pipeline/gcp-credentials` and project `RHAISTRAT_VERTEX_ADC`. Neither
  is the dedicated Vertex service account required by this plan. Asked the
  user for its location or a permitted service-account impersonation target.
  No real model job is authorized with those broad user credentials by the
  current plan. The strategy job explicitly rejects that credential type.
- Shell syntax, Python compile checks, and `git diff --check` passed.
  Live sandbox connectivity, phase execution, publication, cancellation,
  timeout, and recovery evidence remain outstanding. M6 is not complete.

- First read-only pipeline **2026**: build **3927** succeeded; connectivity
  **3928** failed before sandbox creation because maintained runner
  `GIT_SSL_CAINFO` contains only the local CA and replaces public roots.
  Corrected checkout setup to combine system roots with the mounted local
  CA, retaining certificate verification. No seeded issue was changed.

## User credential override — 2026-10-06

The user explicitly requires **Vertex using the existing Breadboard secret**,
following rfe-autofixer's working path. See the overriding requirement in
[the plan](../../plans/fullsend-entrypoint-strategy-poc.md). The previous
service-account requirement and authorized-user rejection are superseded.
Use `ai-pipeline/gcp-credentials` with `pipeline-secrets` Vertex settings;
no additional credential is required. The missing dedicated service account
is no longer a blocker. Service-account bootstrap remains a deferred
capability, unrelated to acceptance of this authorized Vertex POC path.

## Continued M6 validation

Pipeline **2031**, build **3937** passed on `glemu-k8s-runner`; connectivity
**3938** reached the actual sandbox and passed restored bot identity/public
GitHub, but GitLab/Org Pulse were reset under inspection. Failed-run
artifacts were collected, containers list was empty and job network removed;
`cleanup_exit=1` retained the execution failure. Extend ADR-0010 to these
local services under ADR-0011 and recheck trusted access/wrong-CA rejection.
The read-only gate is now in a preceding validation stage.

Pushed fork **a3d399d100ed8dc6d683afe75fcfafdbaf8c311e** after unit
**512 passed** and full **776 passed, 1 skipped**. Local service TLS tunnels
retain client verification; the results Git authentication header is now
scoped to its repository URL so public architecture-context fetches do not
receive the results credential. Native results/dashboard projects and
masked downstream data credential exist. CI now pins the updated fork.

Fresh pipeline **2033** / connectivity **3942** passed all four services,
restored bot identity, certificate/hostname checks, local wrong-CA rejection,
output extraction, empty containers, removed network, and `cleanup_exit=0`.
Sandbox `fs-con-60ec169dd67f`, source `a3d399d`, binary checksum remains
`5fa82795ce58458c69498f551a1d4880bcb67bd8002e592fd07617def4f01aee`.
Real job **3943** for `RHAIRFE-1` was manually played after that success.
Lifecycle cancellation job **3947**, pipeline **2035**, is also running.

First real strategy job **3943** proved Vertex inference (Claude
`claude-opus-4-8`, allowed `aiplatform.googleapis.com` traffic), trusted Git
results clone, and owned RFE lock/unlock. The child asked for confirmation
because it interpreted its own processing label as another job's lock;
no strategy was created. The entrypoint correctly failed, unlocked Jira,
collected the transcript, and left no Podman containers/network.
Pushed **24a3babeaaf24526b3108094a2169c326e1952b4** after 512 unit and
776 full tests (1 skipped): child prompts now explain verified owned-lock
context and the user's authorization for workflow writes, preserving gates.

Lifecycle job **3947** reached its five-minute agent deadline while holding;
timeout failure retained artifacts, deleted its sandbox, and removed engine
containers/network. This proves timeout cleanup, not cancellation. Corrected
lifecycle readiness to stderr for live visibility, and defaulted normal
probes to zero hold. Credential/user override was functional throughout.

Retry pipeline **2037** / build **3952** and connectivity **3954** passed
with fork `24a3bab`. Played real single-RFE **3955** and separate lifecycle
**3953**. The lifecycle test now emits readiness on stderr for live cancel.
Older pipeline 2036's pinned-revision guard rejected the moved branch, so
its unplayed lifecycle job is not acceptance evidence; the current pipeline
uses one consistent tested source revision for all jobs.

## Real workflow acceptance

Pipeline **2037**, real **single-rfe 3955** succeeded with hooks enabled.
Created/linked **RHAISTRAT-1**, refined its description, attached the 13,388-byte
review, unlocked **RHAIRFE-1**, and committed run **20261006-165222**:
`c3d7f039ebba8ae392d57be9e3c8b600229b8030`; summary commit
`05b2a813232d2b3446f30ff17fba6520d7c9215d`. Review outcome is **revise**,
score **5/8**, `strat-creator-needs-attention`; this is preserved for human
follow-up, not rewritten as a rubric pass. Org Pulse independently returns
the matching key/source RFE and fresh review timestamp. Refreshed dashboard
pipeline **2039/pages 3958** passed; HTML and summary contain RHAISTRAT-1
and include `public/runs/20261006-165222.json`.

Real job cleanup exit 0, empty Podman containers, no job network, three
child transcripts and native workflow outputs were collected. Security
findings recorded nine actual pre-tool hook blocks; hooks were not disabled.
The initial archive's one Jira password occurrence in the native transcript
was sanitized in place and the downloaded archive rechecked (52 entries,
zero credential hits). Automatic artifact redaction is now in CI and passed
live synthetic-fixture validation in **2040/3960**.

Cancellation **3953** acknowledged `canceled` at sandbox readiness, and its
pod disappeared while real job 3955 completed successfully. The emulator
subsequently overwrote its status as failed/unknown_failure; preserve that
classification difference. A retry was hard-killed at verified readiness:
pod `runner-xmvfkupbt-project-7-concurrent-1-p70irqnn`, UID
`d19ea7e0-f9ff-4126-8df4-3e57c3912d88`. Its independent Podman storage/run
emptyDirs and absence of hostPath were recorded; pod removal was verified.
The retry settled as `runner_system_failure`. A fresh 3960 retry is now
checking recovery after that deletion; no strategy/model rerun is needed.

### Explicit SIGKILL check

A stronger repeat sent **SIGKILL** through the job's own Podman socket to its
single ready sandbox container `83c3123bc1cc`, then force-disposed only the
verified lifecycle pod `runner-xmvfkupbt-project-7-concurrent-0-kenhzcr0`
(UID `a3c59a23-11c0-49b7-9d20-08310f4981c9`). This prevents sandbox traps
from running. Recorded independent storage/run emptyDirs, no hostPath, pod
removal, and **no matching live pod in kubelet runtime stats**. A final fresh
3960 retry follows this SIGKILL; earlier successful retries proved recovery
after ordinary pod destruction.

## Final acceptance and M7 handoff — 2026-10-06

The final recovery retry **pipeline 2040 / connectivity 3960** started after
the explicit SIGKILL at **2026-10-06T18:58:39.791531Z**, in fresh pod
`runner-xmvfkupbt-project-7-concurrent-0-lvgb6hpj`. All four service probes,
artifact collection and live redaction fixture passed; the downloaded archive
had zero known credential hits across 27 entries. Cleanup exited 0 with
zero Podman containers and the job network removed. Together with real job
3955, failure 3943, timeout 3947, cancellation and SIGKILL 3953, this closes
M6 lifecycle and recovery acceptance. No additional model job types were selected.

Final reproducible source references:

- Fixture: `var/demos/fullsend-entrypoint-poc/strategy-ci/README.md` and its
  publisher, CI, source, connectivity, strategy, and artifact-redaction scripts.
- Local GitLab project 7, `redhat/rhel-ai/agentic-ci/strat-pipeline`, branch
  `feat/fullsend-strategy-poc`, CI commit
  `33f897fa9543262429e211560ed49327b20acfee`. Native main remains
  `14d81319af44973d592e4197b14b680684f35813`.
- Public strat-creator fork feature SHA
  `24a3babeaaf24526b3108094a2169c326e1952b4`: **512 unit passed;
  776 full passed, 1 skipped**, committed and pushed.
- Fullsend feature SHA `8f628aec6d113181914e2a2307fce17488e2c4b4`;
  hooks remained enabled. Existing Breadboard credentials powered real Vertex inference.

Remaining differences are documented as open emulator bridge-scheduling and
cancellation-status bugs. A fresh dashboard build proved publication despite
the eager bridge. Jira Basic mode proves bot identity propagation, not password
validation. The Vertex service-account bootstrap is deferred under the user
override. M7 must persist the live single-runner privileges/storage configuration
in deployment inventory and prove reset regression. M3 coverage and separate
hook follow-ups retain their existing deferred status. RHAISTRAT-1 requires
human revision (5/8); that review outcome is not an infrastructure blocker.
