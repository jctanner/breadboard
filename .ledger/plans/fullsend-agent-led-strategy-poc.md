# Fullsend agent-led strategy POC

## Outcome

Run strat-creator through native Fullsend Claude agents in Breadboard's
K3s/GitLab/OpenShell setup. Translate strat-pipeline's Bash orchestration into
two first-class prompts: **strat-single** and **strat-batch**. Each agent uses
the existing strategy skills and deterministic Python helpers. Use a pinned,
unmodified published Fullsend release, without the custom entrypoint patch.

This is a separate experiment from the completed
[script-led POC](fullsend-entrypoint-strategy-poc.md), which remains available
with its existing branches, results and evidence.

## Working locations and defaults

| Item | Location / choice |
| --- | --- |
| Fork | `github.com/jctanner-opendatahub-io/strat-creator` |
| Checkout | `checkouts.fullsend_agent_led_poc/jctanner.strat-creator` |
| Feature branch | `feat/fullsend-agent-led-strategy` |
| Upstream | `github.com/opendatahub-io/strat-creator` |
| Base | Rebase and publish fork `origin/main` onto fetched `upstream/main`, then branch |
| Breadboard fixture | `var/demos/fullsend-agent-led-poc/` |
| Local CI | Existing `gitlab.local/redhat/rhel-ai/agentic-ci/strat-pipeline`, new branch `feat/fullsend-agent-led-poc`; same maintained runner |
| Results | Existing `gitlab.local/.../strat-pipeline-data` and strat-dashboard `main`, shared with the script-led POC (user decision at B3.1, 2026-10-07; supersedes "separate results repository") |
| Model/provider | `claude-opus-4-6`, effort high, Vertex with existing authorized Breadboard credentials |

Read the checkout's instructions before edits and locally ignore its parent
directory in Breadboard. Do not copy the old `.fullsend/` wholesale. Carry
useful model, TLS, Git-fetch, redaction and helper fixes with provenance,
without importing script-led orchestration or its Fullsend build job.

## Reference and architecture

Follow rfe-creator's `agent:` + prompt Markdown + pre/post scripts + structured
output validation, and rfe-autofixer's CI-owned gateway and released binary.
Examined references:

- `checkouts.tmp/opendatahub-io/rfe-creator` at `15b924c`.
- `checkouts.tmp/gitlab_rhel_agentic_ci/rfe-autofixer` at `28bccc8`.
  Its Fullsend job installs **0.43.0**, uses
  `quay.io/aipcc/agentic-ci/openshell:0.3.46`, and supervisor
  `quay.io/opendatahub/odh-openshell-supervisor:v0.0.112-rhaiv.0`.
- That job imports a pinned rfe-creator harness, which differs from the latest
  local checkout. A2 records the prompt/harness reference followed; A3 pins
  the runtime used by the new CI workflow.

Reuse that working release/image combination when wiring the new pipeline.
If integration reveals a missing required capability, choose a compatible
published release and explain the version change.
Do not patch Fullsend or substitute the prior feature binary. Prefer supported
provider declarations and verify changed Vertex/local-policy settings during
CI integration instead of copying deprecated profile overrides. No standalone
infrastructure smoke test is required before prompt implementation.

CI installs released Fullsend, prepares credentials, and starts its own
Podman/OpenShell gateway. The new GitLab branch contains the replacement
`.gitlab-ci.yml`, following rfe-autofixer's native agent invocation pattern.
It fetches and pins `github.com/jctanner-opendatahub-io/strat-creator` from
`feat/fullsend-agent-led-strategy`, then runs `fullsend run strat-single` or
`fullsend run strat-batch` using the same pinned public checkout for target
repository and `.fullsend` configuration. Native Fullsend launches Claude
with its normal hooks. Prompts direct the phase sequence; exact API/file
operations remain in existing helpers. Pre/post scripts handle preparation,
validated output handoff and final publication; an outer CI cleanup path
protects owned-lock release when agent or post-script execution fails.

Keep GitLab `main` and `feat/fullsend-strategy-poc` unchanged. GitLab project
variables are shared across branches: preserve existing values and use
distinct POC variables or job overrides where this pathway differs. The new
workflow must not redirect the completed POC's source or results targets.

The reference RFE sandbox forbids final Jira submission. Strategy creation
already clones/links Jira issues, so its read-only Jira profile cannot be copied
literally. Allow the local Jira writes required by existing skills/helpers,
retain deterministic publication, and preserve refinement push before review.
Document this necessary difference from rfe-autofixer.

## Prompt contract

- **Locking and discovery (amended 2026-10-07, ADR-0012):** the host
  pre-script discovers candidates, acquires locks and records owned keys
  before the sandbox starts; agents receive acquired keys, never JQL, and
  never lock or unlock.
- **strat-single:** read the acquired RFE key, and run create, refine,
  deterministic Jira push and review. Follow existing skill instructions rather than
  reimplementing their internal logic.
- **strat-batch:** the pre-script runs native JQL discovery and processed-work
  exclusion with size/offset and optional exact candidate bound, then locks;
  the agent creates for the acquired set, refine all new strategies, push refinements, then review all.
  This implements `batch-discover`; curated `batch-selected` is deferred.
- Both operate headlessly under the authorized workflow, preserve attention/
  human-sign-off gates, recognize recorded owned locks, and exclude old result
  artifacts. Empty/blocked work emits a skipped result without model work.
- Persist progress and RFE-to-STRAT mappings with existing state helpers.
  Retries must reconcile Jira/artifacts and resume, not blindly repeat create.
  Start with one agent attempt until safe native validation resume is proven.
- Emit `agent-result.json`: action, mode, run ID, input/acquired/skipped keys,
  strategy mappings, completed phases, artifact paths, publication readiness
  and errors. A host validator checks actual artifacts/state; valid JSON alone
  cannot establish completion. Host scripts execute trusted source code,
  treating downloaded agent output as data.
- Missing required architecture context fails or records incomplete review;
  never convert a skipped check into approval. Genuine revise outcomes are
  successful workflow execution requiring human follow-up.

## Milestones

1. **A1 — Checkout, remotes, synchronized main, feature branch.** Create the
   checkout in the requested folder, set the correct fork `origin` and canonical
   `upstream`, fetch both, rebase fork main onto upstream main and publish the
   updated `origin/main`. Verify ancestry/remote SHA, then create and switch to
   `feat/fullsend-agent-led-strategy` from that main. Record original and final
   SHAs and required checks. Repository setup only.
   [Task](../tasks/done/agent-led-strategy-foundation.md).
2. **A2 — Prompts, harnesses and validators; commit/push.** Implement both
   agents and supporting deterministic boundaries. Exercise no-work, partial
   locks, missing context, failure and resume using focused fixtures. Run
   component-required checks and push the fork branch.
   [Task](../tasks/done/agent-led-strategy-prompts.md).
3. **A3 — GitLab branch and one fresh single-RFE run.** Create and publish
   `feat/fullsend-agent-led-poc` in the existing local `strat-pipeline` project
   with the new `.gitlab-ci.yml`. Resolve release/provider/pre/post integration
   as part of wiring this workflow. Run native strat-single and verify real
   4.6 inference, Jira effects,
   validated output, publication/readback, redaction and cleanup.
   [Task](../tasks/done/agent-led-strategy-single-ci.md).
4. **A4 — Scheduled batch (amended 2026-10-07).** Event-trigger dispatch
   and polling are out of scope by user decision: neither reference pipeline
   uses Fullsend `trigger:` routing or Jira polling. Batch runs from a GitLab
   pipeline schedule, as in strat-pipeline and rfe-autofixer; single stays
   a manual or API pipeline. The original A4 text follows for the record.
   **Was: Batch and event selection.** Extend the same GitLab branch and
   process two fresh RFEs with strat-batch.
   Prove native event triggers select and dispatch the correct agent with the
   correct inputs; direct CLI selection alone is not event evidence. Compare
   outputs/failure recovery with the script-led baseline.
   [Task](../tasks/done/agent-led-strategy-batch-events.md).

### Follow-up milestones (added 2026-10-08)

A1–A4 close the POC. These carry its open items forward. Each keeps the
same branches, pins and shared targets, and stops at breakpoints.

5. **A5 — Publication and dashboard without manual recovery.** Remove the
   two recoveries every run needed. Fix Org Pulse so a valid new ingest
   clears a stale flag on a recreated Jira key, without the manual
   `releases:jira-sync`
   ([bug](../bugs/open/org-pulse-ingest-recreated-jira-keys-stay-stale.md)).
   Fix the GitLab emulator so a downstream bridge waits for its upstream
   jobs as in real GitLab, and add strat-pipeline's `build-dashboard`
   trigger job to the agent-led CI, so the native trigger replaces the hand
   rebuild
   ([bug](../bugs/open/gitlab-emulator-downstream-trigger-runs-before-upstream.md)).
   Then publish the missing RHAIRFE-11 / RHAISTRAT-11 run from its
   retained artifacts, without new model work.
   [Task](../tasks/pending/agent-led-strategy-publication-recovery.md).
6. **A6 — Recovery paths proven in CI.** Show the in-run validation retry
   (iteration 2 resumes from progress markers and repeats no Jira effects)
   in a real pipeline, and close
   [the end_turn bug](../bugs/open/agent-led-batch-ends-turn-after-skill-report.md).
   Run the partial- and blocked-lock cases in CI with a temporary Jira
   label write, removed afterwards. How iteration 1 is made to fail is a
   breakpoint decision, checked against rfe-creator first.
   [Task](../tasks/pending/agent-led-strategy-recovery-ci.md).
7. **A7 — Runner job pod cleanup.** Find why Kubernetes-executor job pods
   stay in `Error` after the job finishes, fix it in the runner deployment,
   prove a new job's pod is removed, then delete the retained evidence pods
   ([bug](../bugs/open/gitlab-runner-job-pods-left-in-error.md)).
   [Task](../tasks/pending/gitlab-runner-job-pod-cleanup.md).

## Open choices and constraints

No question blocks planning. Defaults above carry forward the user's existing
model, Vertex, one-runner and job-owned-gateway requirements. Reuse the known
working runtime; A3 handles integration differences encountered in the new CI
workflow. A4 selects and tests the existing event producer/schema for single/batch
requests. Use supported
native `trigger:` routing; do not invent a new dispatcher or claim manual CI
invocation proves event dispatch. Initial runs are manually initiated; leave
unattended recurring schedules disabled.

Prompt instructions cannot guarantee cleanup after termination. Prove durable
owned-lock recording and trusted outer cleanup; hard runner loss requires
reconciliation before retry. Do not automatically replay partial Jira effects.

Known DNS, GitLab cancellation and review-schema issues remain separate.
The Org Pulse stale-key and eager-bridge issues moved into A5 (2026-10-08). Apply documented recovery where needed and disclose
its limits. This plan does not reset service data, change the completed POC,
or prepare an upstream PR. Planning starts no checkout, CI job or model run.

## Status

Implementation plan, 2026-10-07. A1 done (fork main = upstream `cc1ba8c`; branch created). A2 done (branch `508ea33`; host-side locking per ADR-0012 amendment; Fullsend 0.43.0 kept). A3 done (fork `a2b888a`, GitLab branch head `242608b`; pipeline 2078 success; results shared with the script-led POC by decision). A4 done (fork `9350c89`, GitLab branch head `6e3ab46`; batch 2084, recovery 2086; event dispatch withdrawn). Standalone smoke milestone removed. A5–A7 added 2026-10-08 for the open items; all pending.
