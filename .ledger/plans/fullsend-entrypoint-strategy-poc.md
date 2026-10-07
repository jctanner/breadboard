# Fullsend entrypoint and strategy pipeline POC

Implement the Claude entrypoint path from ADR 127 in the user's Fullsend fork
and demonstrate it with a script-driven strategy harness in the user's
strat-creator fork. Reuse the
existing strategy orchestration instead of asking an agent to control it.
M1, M2, and M3 are complete for POC progression. The user deferred the
coverage threshold under [ADR-0008](../decisions/ADR-0008-defer-poc-coverage-gate.md)
to focus on the full workflow. Functional review fixes passed; the measured
72.73% coverage is not a passing result. Track that work in the
[pre-PR coverage task](../tasks/pending/fullsend-entrypoint-patch-coverage.md).
M4, M4.1, M4.2, M5, M6, M7, and M8 are complete. The hooks switch remains a
separate follow-up before using an explicit opt-out. Single-runner consolidation
is implemented and validated; remaining reliability/emulator differences are
recorded in the final M7 findings below.

## Pre-M8 gate: pin Claude Opus 4.6

**Complete — 2026-10-06.** The strategy POC now pins **`claude-opus-4-6`**
as requested by the user. Strat-creator feature commit
`68614f656df6598e1429cac125d634802c07e0f1` is pushed and consumed by both CI
fixtures. Create/refine/review wrapper regressions passed; 513 unit tests and
777 full tests passed (1 skipped). Alias/subagent settings are pinned and
conflicting ambient model/fallback overrides cleared.

Non-mutating Vertex smoke **2047/3981** passed through the actual Fullsend
helper: assistant response model and result modelUsage/canonicalModel report
**claude-opus-4-6**, provider **vertex**, one turn, nonzero token usage.
Claude Code v2.1.260 supports forced subagent selection. Hooks, effort high,
existing credentials and images are preserved. Zero credential matches in
artifacts; cleanup exit 0 and no containers/job network remain. Initial smoke
2046/3979 failed before inference due to prompt argument parsing; passing the
prompt through stdin fixed it.

The processed seed was not rerun; results and historical M6 evidence remain
unchanged (**M6 actually used claude-opus-4-8**). The intermittent DNS issue
remains open. This closed the pre-M8 gate; subsequent M8 execution is recorded below.
[Implementation and evidence](../tasks/done/fullsend-strategy-pin-opus-4-6.md).

## M8: batch strategy CI and pipeline cleanup

Add batch processing to the Fullsend `.gitlab-ci.yml` and prove it with at
least two fresh RFEs on `claude-opus-4-6`. Use the user-approved job name
`batch-discover`, preserving native `batch-jql` discovery, limits,
processed-work filtering, batch serialization, and owned-lock cleanup.
The curated-list variant is named `batch-selected` (formerly `batch-config`)
and remains outside M8's initial implementation scope. Extend the single-RFE
harness to handle the native batch phase order and publication while retaining
single-RFE behavior. Apply the new name consistently to CI dependencies,
publisher commands, tests, and documentation; preserve historical references.

Remove `lifecycle-check`, `model-smoke`, and `sandbox-connectivity` from the
normal pipeline. Keep reusable diagnostics in a separately invoked validation
configuration and retain real-job preflight, cleanup, and redaction. Update
publisher commands and dashboard dependencies for the simplified job graph.
Do not reset Jira or reuse the already processed M6 seed. The DNS reliability
bug remains an open follow-up, not M8's primary scope.

[M8 task and acceptance criteria](../tasks/done/fullsend-strategy-batch-ci.md).
**Complete — 2026-10-06.** Pushed strat-creator source efcf946; tests 520 unit,
784 full passed (1 skipped), plus 2 CI graph regressions. Normal CI at
fa8b966a58f5dd251a613b15b3deb4da1e5edf1b supports single-rfe and
batch-discover with matching bridges; diagnostics live in opt-in validation.
Batch 2053/3993 processed RHAIRFE-2/RHAIRFE-3 into RHAISTRAT-2/RHAISTRAT-3,
with actual Opus 4.6 across 355 assistant records in 17 transcripts. Both
reviews recommend approve, 8/8; both refinements/reviews reached Jira and
owned locks were released. Results run 20261006-223446, commits 73af1d2
and 54945d1. Fresh dashboard 2055/3996 includes both strategies and run data.

Org Pulse stored both reviews but reset-era stale flags initially hid them.
Standard releases:jira-sync recovery made per-feature reads confirm both
source RFEs, run ID and scores. [Ingest/refresh reliability remains open](../bugs/open/org-pulse-ingest-recreated-jira-keys-stay-stale.md).
No model replay or Jira reset was needed; M6 issue hashes and review outcome
remain unchanged. Artifact credential scan had zero hits; cleanup exit 0 with
no containers/job network. No-model controls 2052/3991 and published job graph
checks passed. One maintained runner, no schedules, all test jobs terminal.
The DNS bug remains open; batch-selected/reprocess-strat remain deferred.


## Delivery milestones

The user's three delivery milestones continue after M3; M4.1 and M4.2 add
the image pivot and sandbox Jira connectivity before Jira preparation:

1. **M4 — Prepare and publish the strat-creator branch.** Create
   `feat/fullsend-strategy-entrypoint` in the user's fork. Add the copied Bash
   and Python helpers, Fullsend entrypoint/harness/config, required dependencies,
   and CI launcher/cleanup files. Preserve strat-pipeline's behavior and route
   Claude calls through `fullsend-claude`. Test, commit, and push to
   `github.com/jctanner-opendatahub-io/strat-creator`; record the remote SHA.
   [Task](../tasks/done/strat-creator-entrypoint-poc.md).
   **M4 is complete** at `97562dbee8cf2aa792de01160890a6dcfda61cde`.

   **M4.1 — Reuse rfe-autofixer's images.** Replace the custom CI and sandbox
   Containerfiles with the reference job image and Fullsend sandbox image,
   using the matching supervisor. Keep our feature-branch Fullsend binary.
   Verify dependencies and gateway/sandbox compatibility, update docs/tests,
   then commit and push the existing branch. **M4.1 is complete** at the
   successful local GitLab smoke pipeline 2011 (jobs 3898/3899), pushed at
   commit `602766cdd96ca857e433385d2c6a2b30f27e5d4f`; see the
   [completed task](../tasks/done/strat-creator-rfe-autofixer-images.md).
   M4.1 reported sandbox DNS/ClusterIP failures. M4.2's bounded probes
   corrected that diagnosis: raw child DNS fails immediately, HTTP resolves
   through the OpenShell proxy, and the same Podman bridge reaches Jira.
   The actual defects were unattached service permissions and supervisor
   upstream private-CA trust; see M4.2 evidence.
   [Decision](../decisions/ADR-0009-reuse-rfe-autofixer-images.md).

   **M4.2 — Fix sandbox access to Jira.** Diagnose DNS, routing, policy, and
   TLS using the M4.1 images. Prove a read-only Jira API request through the
   strategy's Python HTTP path inside the real sandbox, then repeat in a
   fresh CI job with network restrictions and cleanup still working. Record
   the fix and evidence before M5. No Jira reset or strategy run is needed.
   **M4.2 is complete** at pushed strat-creator SHA
   `bd20534f5b904ae7808d167ad3cde671e17d5ab1`. Fresh pipelines 2022/2023
   (build/smoke jobs 3920/3921 and 3922/3923) passed the strategy Python
   Jira API, client TLS verification including rejection without the local
   CA, intended CI identity, allowed GitHub and blocked public endpoint,
   output transfer, and cleanup. Service permissions now live in the applied
   base policy, with a versioned Python match. Structured diagnostic logs
   proved supervisor upstream `UnknownIssuer`; Jira-only TLS passthrough
   preserves client certificate/hostname verification and endpoint policy
   but omits Jira HTTP inspection. Public GitHub remains read-only.
   The emulator is permissive for Basic passwords, so identity propagation
   is proven and password validation is unavailable. All temporary resources
   were removed, and only the maintained GitLab runner remains. Tests: 512
   unit tests; full suite 776 passed, one skipped. No Jira reset or strategy
   run occurred. M5/M6 must recheck identity/auth mode after reset and validate
   the other services and real writes.
   [Task](../tasks/done/fullsend-sandbox-jira-connectivity.md),
   [decision](../decisions/ADR-0010-jira-sandbox-tls-passthrough.md),
   [fixed bug](../bugs/fixed/fullsend-sandbox-jira-connectivity.md).
2. **M5 — Reset Jira and seed one RFE.** Reset only `jira.local`, adapt an
   existing `var/` fixture, and verify its labels, required fields, credentials,
   and readiness for a strategy run. Record the issue key and repeatable seed
   commands. **M5 is complete**, 2026-10-06: Jira alone was reset;
   `RHAIRFE-1` is New, Feature Request, priority Major, component CLI, and
   eligible under pushed strat-creator `bd20534f5b904ae7808d167ad3cde671e17d5ab1`.
   Its unchanged source content is the existing `rhai-cli diagnose` fixture.
   Actual config supplies `strat-creator-3.5` and
   `rfe-creator-autofix-rubric-pass`; it has no locks, strategy links, or
   attachments. Reset/seed and the idempotent repeat passed, as did a read
   with the strategy Python client over trusted HTTPS. Dedicated CI bot
   credentials were restored in `ai-pipeline/fullsend-strategy-jira`:
   `JIRA_TOKEN` is its Basic password; `JIRA_BEARER_TOKEN` is its separately
   validated PAT. Basic auth remains permissive. The reusable recipe is
   `var/demos/fullsend-entrypoint-poc/jira-seed/README.md`; M6 targets
   **`RFE_KEY=RHAIRFE-1`** and rechecks the new bot in the real sandbox.
   An emulator component-ID omission is documented; the verified fixture
   uses component names. Other services were not reset and no strategy ran.
   [Task](../tasks/done/fullsend-strategy-seed-rfe.md).
3. **M6 — Recreate the GitLab workflow and run it.** Rebuild the local
   `strat-pipeline` CI workflow in `gitlab.local`. Fetch Fullsend files and
   skills from `github.com/jctanner-opendatahub-io/strat-creator` at
   `feat/fullsend-strategy-entrypoint`, using that same checkout as the sandbox
   repository. Use the Fullsend feature build and a job-owned Podman/OpenShell
   gateway. Process M5's issue through `single-rfe` and verify strategy output,
   Jira effects, lock release, results publication, and collected artifacts.
   Record the resolved source SHA and job evidence.
   [Task](../tasks/done/fullsend-strategy-poc-integration.md).

The initial acceptance run is one RFE. Additional job types can follow after
that works. The public GitHub fork is the requested source for the skills and
Fullsend files; `gitlab.local` owns the CI workflow. Local endpoints and secret
values belong in emulator CI configuration, not committed credentials.

The hooks-switch work need not block preparing M4's branch, but the flag must
exist before a harness uses it. M7 still validates that the final platform
maintains one GitLab runner with all required capabilities.

## Required final runner setup

End with **one maintained GitLab runner registration and deployment serving
`gitlab.local`**, capable of running ordinary CI, native strat-pipeline jobs,
and jobs that use nested Podman and their own OpenShell gateway. Extend the
existing Kubernetes runner with the validated configuration. A temporary
test runner is an experiment, not an additional permanent service.

One runner can execute concurrent jobs and use different job images. Podman
and OpenShell tooling belong in the appropriate job images; the runner must
provide the permissions, storage, networking, and trust those jobs need.
Each Fullsend job still owns its gateway and sandbox; runner consolidation
does not introduce a shared gateway. Any executor replacement must preserve
this single-runner outcome. See
[ADR-0005](../decisions/ADR-0005-single-gitlab-runner.md).

## M1 complete and gate cleared

**M1 passed on 2026-10-05 UTC.** See
[the completed M1 task](../tasks/done/podman-in-k3s-feasibility.md) and
[its evidence](../notes/podman-in-k3s-m1-evidence.md). Podman 5.8.2 passed in
three fresh pods and GitLab pipelines `1980`/`1981`, jobs `3846`/`3847`.
The passing configuration used the agentic-ci Podman image, VFS storage,
privileged job containers, and inner `--network=host --cgroups=disabled`.
Here `host` means the outer pod's network namespace, not the k3s node's.
Ordinary runner-equivalent permissions failed on TUN, cgroup, and mount access.

The recorded checks cover inner execution and exit status, writable workspace
mounts, DNS/outbound HTTPS, cleanup, and repeatability through the Kubernetes
executor. Test pods and the dedicated runner were removed afterward; M1 did
not permanently enable privileged jobs on the existing strategy runner.

**The M1 gate is cleared.** OpenShell integration and feature implementation
may proceed. M1 included no OpenShell, model calls, or strategy processing;
it does not prove sandbox policy enforcement or OpenShell compatibility.

## Repository boundaries

| Repository | Proposed feature branch | Responsibility |
| --- | --- | --- |
| `checkouts.fullsend_prototype/jctanner.fullsend` | `feat/entrypoint-harness` | General Fullsend feature, tests, and user documentation |
| `checkouts.fullsend_prototype/jctanner.strat-creator` | `feat/fullsend-strategy-entrypoint` | Copied CI helpers, entrypoint, harness, policy, and POC tests |
| Breadboard | Current planning work | Ledger and any required local emulator/deployment fixtures |

Both forks were clean on `main` when inspected: Fullsend `7a2622076` and
strat-creator `cc1ba8c`. The Fullsend branch was created from `7a2622076`;
the strat-creator branch remains pending. Read each repository's instructions before editing. Keep
these nested repositories out of Breadboard commits; the new
`checkouts.fullsend_prototype/` directory currently appears untracked in
Breadboard and needs a local ignore or an appropriate tracked ignore rule.

Use `checkouts.fullsend_prototype/0127-custom-runtimes.md` as the design input.
Although its local status says Accepted, the user says upstream acceptance
and merge are still pending. After M1, build and test on the fork branch; reconcile
with the merged ADR before preparing the eventual upstream PR. Do not open
that PR as part of this planning task.

## Confirmed gateway requirement

Each CI job must bootstrap its own OpenShell gateway, collect outputs, and
tear down that gateway and its sandboxes when finished. There is no central
gateway for this POC. The initial requirement named the Docker compute
provider; the user subsequently identified rfe-autofixer's Podman setup as
the model and required Podman-in-k3s as the first gate. M2 passed with the
Podman provider and selects it for the remaining POC. Docker-driver
compatibility remains untested. The temporary runner needed `privileged =
true`; because the final Kubernetes runner is shared, M7 must validate the
effect on ordinary jobs before this setting is incorporated. See
[ADR-0004](../decisions/ADR-0004-fullsend-ci-owned-docker-gateway.md) and
[M2 evidence](../notes/openshell-podman-gateway-m2-evidence.md).

The existing Kubernetes runner successfully ran the native strategy scripts,
but its configuration supplies neither a Docker daemon nor Docker-in-Docker.
That earlier success does not establish support for this new execution path.
The inspected Fullsend `action.yml` also bootstraps a local **Podman** gateway.
It and rfe-autofixer are references for the post-M1 OpenShell work.

## Rebased rfe-autofixer reference

Reviewed rfe-autofixer at `28bccc8` (integration commit `8bc7d14`). Its new
`autofix-rfe-stage-dry-fullsend` job confirms the job-owned Podman/gateway
approach. It runs Fullsend 0.43.0 with CI image `openshell:0.3.46` and custom
supervisor `v0.0.112-rhaiv.0`. This is a manual, allowed-to-fail job; no run
evidence was reviewed. It does not replace M1/M2 evidence or reopen those gates.

The imported [rfe-creator harness](https://github.com/opendatahub-io/rfe-creator/blob/fae245e778384a0fc823c1df6a71bd2b38489882/.fullsend/rfe-creator/rfe-creator.yaml)
uses `agent:`, a task prompt, and validation retries. M3's script-controlled
`entrypoint` and supported Claude child launches are still required. Reuse
the following integration patterns in steps 3–5:

- Generate gateway certificates and register the local HTTPS gateway. Check
  certificate names, client authentication, and sandbox callbacks in k3s;
  certificate generation alone is not the credential-bearing run gate.
- Review its Jira/Vertex providers and profiles, `providers_v2_enabled`, and
  GCP credential-file delivery against the selected OpenShell version. Its
  Jira profile targets production with read-only access; our strategy POC
  needs explicit local endpoints and the intended write permissions. The
  sample copies a GCP key into the sandbox; do not assume credentials remain
  outside it or adopt that exposure without reviewing the needed access.
- Its host pre-script prepares dependencies/context; its post-script copies
  downloaded `tmp/` and `artifacts/` back into the target checkout before CI
  publishes results. Define and test our equivalent output handoff and
  completion checks; preserve strat-pipeline's own gates and publication.

M4.1 now selects rfe-autofixer's image set under ADR-0009; repeat the relevant
M2 checks before accepting it. Build Fullsend from our feature commit rather
than downloading 0.43.0. Use
readiness checks and explicit cleanup instead of copying the job's fixed
sleeps. Do not copy its agent validation retry loop into a workflow that may
repeat external writes. The single-runner outcome and Claude-only scope stay
unchanged.

## Confirmed runtime scope and fidelity

**Claude only for this POC.** Defer Codex/Pi agentless bootstrap, child launch,
and new entrypoint telemetry adapters. Keep their existing agent-led behavior
unchanged. Explicitly reject unsupported entrypoint runtime/parser selections;
do not silently fall back to Claude. Plain entrypoints with no runtime remain
part of the common launch contract. This is a scoped implementation of ADR
127, not completion of its full multi-runtime design. See
[ADR-0006](../decisions/ADR-0006-claude-strategy-poc-scope.md).

Replicate the current strat-pipeline as closely as the sandbox permits:
preserve deterministic step order, prompts/model settings, gates, locking,
batch behavior, exit handling, artifact formats, and publication semantics.
Copy the existing helpers and make focused adaptations for sandbox paths,
dependencies, credentials, and Fullsend's supported Claude launch. Record
each difference from the source and why it is necessary; avoid unrelated
workflow redesign. Changes needed to preserve correct cancellation or error
handling must be explicit and tested.

## Scope and remaining choices

The user confirmed the next sequence: publish the branch, reset/seed local
Jira, then run the local GitLab workflow against that branch. Initial acceptance
is `single-rfe` with one seeded issue. Additional strategy job types are later
work; their full rollout is not a prerequisite to this first run.

Use local Jira/GitHub/GitLab/Org Pulse services and the existing Vertex setup,
with the public GitHub fork as the explicit exception for source checkout.
Podman is selected based on M1/M2. Real production issue/result service access
is outside the POC. Preserve the final single-runner requirement.

## Implementation sequence

**M2 complete: prove OpenShell separately.** The disposable GitLab CI job
bootstrapped its own Podman API and gateway, created a stock sandbox, executed
a command, exported an artifact, verified allowed/blocked network traffic,
and tore down its job-owned resources. It matched CLI/gateway/supervisor at
OpenShell 0.0.116 and recorded the sandbox/supervisor digests. It used
job-local storage and no host engine socket or central gateway. See
[M2 evidence](../notes/openshell-podman-gateway-m2-evidence.md). M2 needed no
model calls or strategy code; the provider/runner privilege tradeoff is now
recorded for the remaining POC and final runner consolidation.

Use M2's fixture as the comparison for M4.1's replacement-image tests; its
recorded versions remain the historical passing baseline.
It passed with a separate bridge and normal cgroups, without M1's inner
host-network or disabled-cgroups settings. Before credential-bearing runs,
address the smoke gateway's unauthenticated HTTP configuration and validate
local service connectivity, concurrent jobs, and failure/cancellation cleanup.

M2 selected OpenShell's Podman driver because the sandbox policy checks,
supervisor callback, artifact transfer, and cleanup all passed. The remaining
runner work must handle the validated privilege setting under the required
single-runner arrangement. Docker compatibility remains untested.

### M3: Complete for the POC; coverage deferred

Implement the general feature in `checkouts.fullsend_prototype/jctanner.fullsend`
on `feat/entrypoint-harness`, following
[the M3 task](../tasks/done/fullsend-entrypoint-feature.md). Both environment
gates have passed. This milestone covers implementation steps 1 and 2 below
and the Fullsend tests from step 5. Runtime scope is confirmed as Claude only.

The implementation and docs are on the fork branch. The implementing agent
reported that real Claude execution proved a configured hook ran and blocked its canary Bash command. Four
OpenShell tamper cases (changed, deleted, replaced, and unexpected directory
entry) were rejected by the outer runner before result acceptance, with
sandbox cleanup verified. A separate no-runtime OpenShell run verified argv,
event/support-file delivery, task input, output collection, and cleanup.
Race-enabled `make go-test` passed across both default and GitHub-tagged Go
tests (83.9% total statement coverage); the CLI package passed at 80.4% after
the added scan tests. Staged `uvx pre-commit run` passed, including gofmt,
go vet, and documentation checks. Function-level patch-coverage inspection
was above the 80% target for the new entrypoint scan, launch, and integrity
functions. Review corrections pin effective hook defaults, preserve bounded
failure diagnostics before sandbox cleanup, and update the user reference.
The corrected affected-package profile estimates changed executable-line
coverage at 150/200 (75.0%) for the correction commit only. Independent
re-review measured 480/660 (72.73%) for the full M3 feature; the floor is not met and is deferred under ADR-0008. The dedicated
[review record](../bugs/open/fullsend-m3-review-gaps.md) lists all four
dispositions and evidence.
The test target needed a temporary `gh` executable that exits with
no token because legacy fixtures otherwise wait indefinitely on host
`gh auth token`; it was kept under `/tmp` and not added to the fork.

The exact implementation and evidence are in the
[M3 task](../tasks/done/fullsend-entrypoint-feature.md). The check
detects changes present at checkpoints; a writable helper can be bypassed,
temporary changes restored before checks can escape detection, and external
writes cannot be undone. These limits do not substitute for an immutable hook
installation.

This detects modifications present at checkpoints, not every temporary change
or bypass of a writable helper; it cannot undo external writes. Keep hooks
enabled for M3's proof. Immutable installation is a
[separate follow-up](../tasks/pending/fullsend-immutable-hook-installation.md).

### M3 follow-up: Sandbox hooks switch

Then implement [the hooks switch task](../tasks/pending/fullsend-sandbox-hooks-switch.md):
`security.sandbox_hooks.enabled`, default true. False skips Fullsend's hook
uploads and activation, while retaining runtime setup, host scanning, plugins,
and OpenShell restrictions. This setting belongs outside `entrypoint` and
applies consistently to existing agent-led runtimes and Claude entrypoints.
It does not substitute for M3's hooks-enabled verification. The strategy POC
can select an explicit opt-out afterward and record that difference.

**M4 complete:** the strat-creator branch is pushed at
`97562dbee8cf2aa792de01160890a6dcfda61cde`; its unit suite passed (509 tests)
and its full suite passed (773 passed, 1 skipped). The task records the copied
helper provenance and source adaptations. M4.1 supersedes the custom image
choice with rfe-autofixer images. The original Containerfiles and gateway
launcher are committed but have not been built or exercised in the live stack;
M6 covers that integration. See the [M4 task](../tasks/done/strat-creator-entrypoint-poc.md).

M5 seeds the issue; M6 runs the real strategy workflow. Runner consolidation
remains required. Reconcile with the merged upstream ADR before PR.

The numbered items below are implementation steps, not milestone numbers.

1. **Define the launch contract before wiring the pipeline.** Add the ADR's
   `entrypoint` mapping to the harness, mutually exclusive with `agent`.
   Implement whole-mapping replacement through inheritance, strict validation,
   and single-pass argument substitution from `env.sandbox`. Reject paths
   escaping the Fullsend directory, including symlinks, and preserve argv
   boundaries without shell evaluation. Keep `runtime` in `config.yaml`;
   entrypoint mode with no explicit runtime must skip runtime bootstrap.

   Specify delivery, executable permissions/shebang, repository working
   directory, task/event inputs, environment, and output collection. Use the
   existing repository upload and output paths where possible. Test supporting
   file delivery explicitly. Run once by default; permit validation retries
   only as specified in the ADR. A nonzero exit, timeout, or launch failure
   must not replay external writes. Cancellation must terminate descendants.

2. **Separate Claude setup from agent launch.** Introduce agentless Claude
   bootstrap and a documented child invocation helper. Reuse Claude's
   settings, hooks, plugin loading, model/effort selection, and
   integrity checks; preserve trusted verification data outside child control.
   Do not implement this by merely exporting a config directory or invoking
   the bare Claude binary. Preserve existing agent-led behavior.

   Support `stream_format: none|claude` independently of runtime provisioning
   for this scoped implementation; document the deferred ADR parser values.
   For this multi-call POC use `none`: retain child transcripts
   and telemetry as artifacts without claiming aggregate Fullsend metrics.
   Runtime-free SDK scripts receive no automatic provider credentials.

3. **Copy and adapt the pipeline into strat-creator.** Start from
   `checkouts.tmp/gitlab_rhel_agentic_ci/strat-pipeline` at a recorded commit.
   Put the copied `ci-scripts/` helpers under `.fullsend/scripts/ci/`, preserving
   provenance and applicable license notices. Include the Python dependencies
   used for stream handling, OTEL collection/summary, results pushing, and Org
   Pulse upload; copying Bash alone is insufficient. Keep the source checkout
   unchanged and record each adaptation.

   Add `.fullsend/scripts/strategy-entrypoint.sh`,
   `.fullsend/harness/strategy.yaml`, `.fullsend/config.yaml`, and a scoped
   policy/profile. Extract the actual create/refine/review sequencing from
   `.gitlab-ci.yml`, including lock acquisition, skip/no-work behavior, and
   unlock cleanup. Accept an explicit mode and issue/config inputs through
   the declared argument/environment contract. Start with `single-rfe`.

   Use the checked-out strat-creator feature branch as the sandbox workspace;
   do not clone public `main` over it. Replace `/tmp/claude-workdir`,
   `CI_PROJECT_DIR`, and `/root/.tokens` assumptions with explicit workspace,
   output, and credential paths. Replace direct Claude invocation in
   `run-claude.sh` with Fullsend's supported helper. Review its early-success
   marker and process-kill handling so cancellation cannot become success.

   Fullsend runs as the sandbox user: package installation, `useradd`, and
   copying a GCP key from `setup-claude-ci.sh` cannot simply run unchanged.
   Use rfe-autofixer's Fullsend sandbox image and verify the required
   dependencies there, per M4.1. Use Fullsend's runtime/provider setup;
   document any actual missing dependency before proposing an image extension.
   Record the difference from the original UBI9 CI image. Preserve artifact
   names and reporting behavior.

4. **Connect the local services and launcher.** Test `.local` resolution and
   trusted HTTPS from the CI job, gateway, and sandbox, plus network permissions for the
   actual Python/Git/Claude processes. Provide Jira, results-repository, Org
   Pulse, and Vertex access through explicit secret inputs and supported
   credential delivery/refresh. Keep local endpoints and secrets out of
   upstream Fullsend defaults. Identify architecture-context dependencies and
   mirror them or explicitly configure their permitted source.

   Add CI setup/cleanup scripts to strat-creator for the job-owned gateway.
   Give each job separate names, state, certificates, provider credentials,
   and network resources; wait for readiness before invoking Fullsend. Use a
   version-correct foreground/service launch suitable for CI rather than
   assuming systemd exists inside the job container. Map local service names
   through a reachable Breadboard ingress and retain CA trust across every
   nested layer; host entries in the outer pod do not automatically propagate.
   Verify GitLab identity/role credentials separately from the GitHub mint;
   a local gateway does not supply forge credentials. Build the CLI
   from the Fullsend feature commit and supply that binary to the shared CI
   image; do not use a stale installed binary or release without entrypoint support.
   Keep CI responsible for schedules, manual rules, resource groups, artifact
   upload, and the downstream dashboard trigger; it invokes one harness per
   job. The entrypoint sequences children inside that one sandbox.

   Collect Fullsend output and gateway logs before teardown. Handle success,
   failure, cancellation, and timeout with traps plus CI cleanup; account for
   hard job termination where neither can run. With job-scoped container
   storage, pod deletion must remove that temporary storage and processes.
   With a persistent container host, use job labels and bounded stale-resource cleanup. Never prune
   unrelated containers, networks, or volumes. Verify concurrent CI jobs do
   not share state or delete one another's resources.

5. **Verify the feature and POC separately.** Fullsend tests must cover schema,
   inheritance, argument/path validation, explicit/no runtime resolution,
   parser selection, exit/retry behavior, cancellation, and existing agent-led
   regression paths. For Claude, exercise real child hook execution,
   applicable tamper rejection, and selected model propagation; uploaded
   files alone are not proof. Follow `make go-test`, staged `make lint`, and
   the repository's patch coverage target of 80% (75% enforced floor),
   deferred until pre-PR preparation under ADR-0008.

   In strat-creator, use deterministic test doubles to verify call order,
   failure propagation, owned-lock cleanup, no-work cases, and publication.
   Run `make test-unit` for executable changes and the full `make test` before
   pushing. Then run one seeded RFE with a real model: require create, refine,
   review, unlock, expected Jira updates, a results commit, and collected
   logs/artifacts. Verify Org Pulse publication separately: its original
   helper treats upload failure as non-blocking. Test graceful cancellation
   and document recovery for a destroyed sandbox where traps cannot run.

6. **Complete the agreed scope and prepare the handoff.** If selected, exercise
   reprocess-strat, a small config batch, scheduled JQL batch, concurrent lock
   contention, and the dashboard trigger. Record Codex/Pi entrypoint support
   as deferred; it does not gate this Claude POC. Record feature/source/image commits,
   sandbox and CI IDs, Jira keys, result commits, remaining differences, and
   exact reproduction commands without credentials. Review against the final
   merged ADR before preparing the Fullsend PR; follow its commit/DCO rules.

7. **Consolidate into the platform runner.** Fold the proven Podman/OpenShell
   requirements into `deploy/scripts/15-deploy-gitlab-runner.sh` and
   `deploy/k8s/21-gitlab-runner.yaml` as needed. Include the concrete job
   privilege/security settings from validation; do not assume tags alone
   select different security settings within one runner. Preserve required
   project tags and untagged-job behavior, and use per-job storage and gateway
   state so concurrent jobs do not interfere.

   Make deployment and `clean-all.sh` reset handling converge on one runner
   registration instead of creating duplicates. Drain active test work, move
   fixture jobs to the main runner's tags, and remove temporary registrations,
   deployments, and secrets. On that same runner, validate ordinary CI,
   native strategy CI, nested Podman, and job-owned OpenShell execution,
   including concurrent jobs. Repeat deployment/reset checks and verify
   exactly one registration remains, with job traces proving assignment.
   Document job-image requirements and update/rollback commands.

## Completion criteria

The agreed POC reproduces the current strategy orchestration through the new
Fullsend entrypoint, using supported Claude child launches inside one
policy-constrained sandbox, with necessary source differences documented.
M1 must pass before later implementation begins. Every CI job creates and
cleans up its own OpenShell gateway using the agreed container provider;
validation must succeed without any central OpenShell gateway connection.
Evidence proves the intended external effects and failure behavior. The
Fullsend branch contains reusable product changes; the strat-creator branch
contains the workflow. Run `git diff --check` in every changed repository.
Existing native strategy CI remains available for comparison and rollback.
Completion also requires the single platform runner to pass the capability
checks above and survive deployment/reset without duplicate registrations.

### M6 implementation started — 2026-10-06

See [completed M6 task](../tasks/done/fullsend-strategy-poc-integration.md)
for implementation and evidence. The manual Fullsend CI branch preserves
native main, uses the pinned public fork for harness and skills, and collects
artifacts plus a separate connectivity gate. The existing single runner now
has live Podman privileges and job-local storage; M7 owns durable deployment
and reset consolidation. The user has authorized the existing Breadboard Vertex credentials under
the override below; a dedicated service account does not gate this POC.
This was the initial launch state; final acceptance below closes M6.

### User override: Vertex with existing Breadboard credentials — 2026-10-06

**Overriding requirement from the user:** use Google Cloud Vertex AI for
M6, following the working rfe-autofixer authentication path and using
Breadboard's existing Vertex secret and project settings. This supersedes
M4.1/M6 handoff language requiring a dedicated Vertex-only service account
or prohibiting the existing authorized-user credentials for the real POC.
Do not require a new credential or service account to proceed.

Application Default Credentials (ADC) describe Google authentication to
Vertex; they are not an alternative inference service. Use
`ai-pipeline/gcp-credentials` (`credentials.json`, currently
`type=authorized_user`) with Vertex project/region settings from
`ai-pipeline/pipeline-secrets`. Keep credential values in secrets or masked
CI variables and private job-local files. Preserve the existing supported
refresh path, verify real Vertex inference, and record run evidence.
The service-account bootstrap gap is deferred and does not block M6.
All other M6 acceptance criteria remain in effect.

### M6 trusted services and real-run launch — 2026-10-06

Fork `a3d399d100ed8dc6d683afe75fcfafdbaf8c311e` passed 512 unit and
776 full tests (1 skipped) and is pushed. Pipeline 2033/build 3941 and
sandbox connectivity 3942 passed: restored Jira bot identity, GitLab,
Org Pulse, and public GitHub HTTPS; wrong-CA rejection for local services;
artifact extraction; cleanup exit 0 with empty Podman containers and removed
job network. Local service tunnels follow ADR-0011; public GitHub inspection
is retained. Fullsend remains feature SHA `8f628aec6d113181914e2a2307fce17488e2c4b4`.

Real `single-rfe` job 3943 is running for `RHAIRFE-1` with the user-approved
Breadboard Vertex credentials and hooks enabled. Separate lifecycle job 3947
in pipeline 2035 tests cancellation without running model skills.
The emulator eagerly dispatched downstream pipeline 2034 before strategy;
recorded [bridge scheduling bug](../bugs/open/gitlab-emulator-downstream-trigger-runs-before-upstream.md).
A fresh dashboard build after publication is required as POC recovery.

### M6 complete — 2026-10-06

The real Vertex workflow **2037 / single-rfe 3955** processed **RHAIRFE-1 →
RHAISTRAT-1**, created/refined/reviewed the strategy, released the RFE lock,
attached the review, committed results and separately verified Org Pulse.
Run `20261006-165222`, results commit `c3d7f039ebba8ae392d57be9e3c8b600229b8030`,
summary commit `05b2a813232d2b3446f30ff17fba6520d7c9215d`. Review recommends
**revise, 5/8, needs-attention**; human revision remains necessary. Fresh
dashboard **2039 / pages 3958** published matching HTML, summary and run data.

The final public fork SHA is `24a3babeaaf24526b3108094a2169c326e1952b4`
(512 unit passed; 776 full passed, 1 skipped; pushed). Hooks stayed enabled
and recorded nine pre-tool blocks. The owned-lock prompt issue and one native
transcript credential occurrence were fixed; the retained archive was sanitized
and automatic CI redaction independently passed a live synthetic fixture.

Failure, five-minute timeout, cancellation, explicit sandbox SIGKILL and
pod disposal were checked. Kubelet runtime stats confirmed disposal; fresh
post-SIGKILL recovery **2040 / connectivity 3960** passed service access,
redaction, artifacts and cleanup (exit 0, no containers or job network).
The emulator's eager downstream scheduling and overwritten canceled status
remain documented differences, with fresh dashboard publication verified.

See the [completed M6 task](../tasks/done/fullsend-strategy-poc-integration.md)
for source pins, job evidence, findings and remaining differences. The existing
single runner was reused. M7 was pending at this M6 handoff; the subsequent
completion section below records its durable deployment/reset validation. The overriding
Vertex requirement above was fulfilled using existing Breadboard credentials.

### M7 complete — 2026-10-06

Authoritative deployment now maintains one registration and one Recreate runner
manager: concurrent=4, privileged=true, existing tags and run_untagged=false,
with separate job emptyDirs at /var/lib/containers and /run/containers.
Deployment pauses/drains work, reuses the maintained registration token and
removes duplicates/experiment resources. clean-all shares that lifecycle;
its new --gitlab-runner-only option resets registrations without erasing M6
issues/results. The fixture runner switch delegates to authoritative deployment.

Capability pipeline **2042** passed build 3967, ordinary 3968, native read-only
strategy 3969, nested Podman 3970 and simultaneous OpenShell **3971/3972**.
Distinct pods, certificates, gateway databases/state directories and networks
proved independent engines; both cleanup exits were 0 with no containers or
job networks left. Native setup installed Claude and verified restored Jira
bot access and processed-seed exclusion; it did not repeat model calls or writes.

Live runner-registration reset, removal of a deliberately paused duplicate,
repeat deployment and emulator restart converge on **one registration ID 1
and one ready manager**, with no temporary runner resources. Final ordinary
**2045/3976** passed; untagged 3977 stayed unassigned and was canceled.
Full clean-all PVC-wipe control flow was checked with mocked kubectl; the live
reset cleared actual runner registrations and preserved service PVC contents.

Failure job **2044/3975** retained exit 37 and uploaded a redacted synthetic
fixture. An EXIT sanitizer now protects strategy/M7 artifacts because the
emulator skips appended after_script after errors. Updated strategy CI commit
`08b93ad5edfcf7dabffe5e42f801821823ea6c03`; no extra model job ran. Final
validation fixture commit `ec2f2ce362f482ad93da7ea2f18d441fddede10c`.
Python/YAML/Bash syntax, registration reuse/busy-reset checks, mocked full-reset
flow, artifact credential scans and git diff --check passed.

An earlier concurrent sandbox suffered DNS/SSRF denials and an aardvark-dns
startup error; cleanup succeeded, and fresh concurrent jobs passed. Its
[root cause remains open](../bugs/open/nested-podman-aardvark-dns-startup-intermittent.md).
The underlying [after_script semantics](../bugs/open/gitlab-emulator-after-script-skipped-on-script-failure.md)
also remain open, with the sanitizer mitigation verified. These findings are
not represented as causal fixes. Existing M3 coverage, hook follow-ups, Vertex
service-account bootstrap and emulator differences retain their recorded status.

See [completed M7](../tasks/done/consolidate-gitlab-runner-capabilities.md) for
job/source evidence and reset scope, and
[runner maintenance/rollback](../../docs/deployment/gitlab-runner.md).
The POC now meets its single-maintained-runner delivery requirement.

## Post-M8: CI progress logging fix (2026-10-06)

Missing Claude stdout had two causes: Fullsend's `stream_format: none` retained
stdout only in an artifact, and our renderer expected partial events while the
helper emits completed assistant messages. Fullsend `bdedebeaf` now forwards
stdout and retains it; strat-creator `7244097` renders completed messages and
avoids partial-stream duplication. Both source commits are pushed; caller pins
updated and normal emulator CI branch published at `456a7865`. Live output is
credential-masked before reaching the runner; exact Vertex Opus 4.6 pin retained.

Verification: 787 strategy tests passed / 1 skipped; repository-wide Fullsend
`make go-test` passed (race, all build variants), vet and staged lint passed.
Affected runtime package coverage 90.6%; RunEntrypoint 82.5%, changed forwarding
expression covered. Four caller tests passed, including a 100,000-character
line with credential masking. Replayed all 17 job 3993 transcripts: 355 assistant
records rendered into 97,108 bytes. Historical job traces are not rewritten.
Optional live diagnostic 2056 was canceled during a very slow GitHub source
fetch, before sandbox execution. Live forwarding is verified by runtime
regression; no completed new sandbox run is claimed. See
[fixed logging gap](../bugs/fixed/fullsend-entrypoint-claude-ci-progress-missing.md).


## Logging batch test and active-job warning (2026-10-06)

User-authorized fresh pair RHAIRFE-4/5 completed as RHAISTRAT-4/5 in pipeline
2057/job4000, source 7244097 / Fullsend bdedebeaf. First attempt failed at results
clone HTTP/2 before locks/inference; bounded retry succeeded. Actual 367 model
records in 17 transcripts all Opus 4.6. Live Claude stdout visible; 31/31 long
plain lines intact after ANSI removal. Trace/artifact credential scans clean;
owned locks, containers and network cleaned; earlier six issue hashes preserved.

Numeric recommendations: approve 8/8 and approve 6/8. The latter has three prose
revise verdicts, which native skill explicitly treats as informational. Both
architecture-context fetches returned 403; skipped prose architecture verdicts
were coerced to approve by schema constraints. This is an open evidence bug,
not proof that architecture-context review succeeded.

Results run 20261007-021455: f9057265 / summary 42551cbb; direct Org Pulse
reads verified after existing standard Jira-sync recovery. Fresh dashboard
2059/4003 contains both new keys and run JSON after retrying a clone interrupted
during emulator rollout. Successful batch duration 33m48s; build 8m57s. Most
model time was repeated per-strategy scoring/prose checks; Git fetch, first
failure and retry added total elapsed time. Five-hour timeout is retained.

Fixed user's stale/pending warning: diagnostics now consider latest job/trace
activity instead of a 30-minute lifetime threshold, and the UI does not label
running-job warnings pending. Two related regressions passed; deployed after
batch completion, browser trace and artifact routes verified. No live test job
or schedule remains. [Complete receipt](../tasks/done/fullsend-ci-progress-batch-test.md).

### Claude unused-directory warning follow-up (2026-10-06)

Job 4000 repeatedly reported an untrusted-workspace warning for the checked-in
`permissions.additionalDirectories` entry `/tmp/strat-assess`. That permission
supports local evaluation and is not used by strategy CI. The entrypoint now
prepares its disposable project's settings before launching Claude, removing
only that directory while preserving other settings and Fullsend hooks. It does
not mark the project trusted in Claude's separate `.claude.json` state.
Malformed JSON fails startup; absent settings are allowed. See the
[work receipt](../tasks/done/fullsend-strategy-unused-directory-warning.md)
for tests and publication. No processed RFEs are replayed for this fix.

### Visible entrypoint handoff (2026-10-06)

The entrypoint now prints the user's three-line `STRAT CREATOR ENTRYPOINT
SCRIPT` banner as its first output, before argument validation or setup.
This distinguishes Fullsend's `Running agent` message from script execution.
Already-running job 4011 retains its earlier immutable source pin. See the
[banner receipt](../tasks/done/strat-entrypoint-start-banner.md).

### Trace upload stall and emulator OOM (2026-10-07)

Batch 2061/4011 appeared stuck at the results clone. The emulator was
OOM-killed (512Mi) while serving `strat-pipeline-data.git`; the clone failed
and the job exited 1 before Claude ran. Emulator trace defects (no overlap
retry, `Range` reporting the last index rather than the size, lossy decoded
storage) then pinned the runner in a 416 loop, so the failed status never
arrived. The emulator now stores trace bytes verbatim, follows GitLab's
append-at-offset semantics and caps `pack.threads`. The runner recovered 4011
on its own (checksum-verified); a controlled job across a mid-job redeploy
completed with a full trace and failed status. Memory headroom remains a
follow-up. [Bug receipt](../bugs/fixed/gitlab-runner-trace-range-mismatch-stalls-terminal-status.md).

### Workspace trust and stderr isolation (2026-10-07)

Job4017 confirmed the earlier directory removal worked, but its19 project allow
rules still lacked trust. Historical stderr from results HEAD (13 allow and13
additional-directory warnings) was repeatedly printed by the wrapper; the
live file had only4 new allow warnings at inspection. Warning counts in the
job trace therefore did not count current invocations accurately.

The authorized follow-up merges project trust into CLAUDE_CONFIG_DIR/.claude.json
atomically, preserves config, and leaves Fullsend hooks/model controls intact.
Each invocation retains its own stderr artifact and prints it once; historical
working stderr is cleared after results clone. Running4017 is not altered.
[Implementation receipt](../tasks/done/strat-ci-trust-and-stderr.md).

### Entry-controlled architecture context setup (2026-10-07)

The entrypoint now invokes the native architecture fetch before starting Claude,
teeing combined stdout/stderr into the runner trace and a retained output log,
with a180-second timeout and separate exit-code artifact. Native curl HTTP
errors are reported directly; failed commands propagate instead of leaving a
misleading ready marker. Context remains optional under existing skills; this
is diagnostic visibility, not a403 resolution or a skipped-review schema fix.
[Receipt](../tasks/done/strat-entrypoint-visible-context-fetch.md).

## Architecture-context Git fetch denied by sandbox policy (2026-10-07)

Job 4021's fetch 403 came from OpenShell's L7 policy, not GitHub. The
`read-only` preset on `github.com` denied `POST git-upload-pack`. Strat-creator
`3fd1563` allows only that POST for `opendatahub-io/architecture-context`;
push stays denied. Both CI pins now point at `3fd1563`, and a no-model
`architecture-fetch` diagnostic has been added. Publishing and the live
diagnostic await GitLab admin credentials. The skipped-architecture schema
bug remains open. See
[bug](../bugs/fixed/fullsend-sandbox-architecture-context-git-fetch-denied.md).

### Live sandbox fetch policy verification (2026-10-07)

Published3fd1563 normal and validation pins using existing local admin bootstrap.
No-model diagnostic2070/4027 passed: fetch3.7s, newest rhoai-3.6-ea.2,
1025 document files and36 overlays, shallow/blob:none, exact sparse paths.
Supervisor confirms context upload-pack allowed, push/other-repo POST denied.
First diagnostic fetched successfully but its assertion counted a symlink alias;
corrected and offline-regression checked,5 fixture tests passed. Cleanup0, no
containers/job network/pod or transcripts; artifact credential scan clean.
Prior reviews remain unvalidated by this fix. See completed verification task
and fixed fullsend-sandbox-architecture-context-git-fetch-denied bug.
