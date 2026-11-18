# Plan: Initiatives test scenario and demo on w530 (CC-75)

Status: **Phase 2 rehearsal completed 2026-11-17** (see "Results"). Written
2026-11-15 on p15, branch `cc-75-w530-initiatives`; this is a condensed
public version of the plan and its progress log.

Details that depend on private sources (the mirror's patches and production
configuration) are kept outside this repository.

## Goal

Mirror the Initiative-related pipelines and repos into a breadboard stack on
w530, seeded with fully synthetic Initiatives, so that:

1. it serves as a **test scenario** for the Initiative work (rfe-creator
   Initiative autofix, strat-creator `initiative-strategy`, epic-creator
   decomposition, strat-pipeline `workflow-batch-initiative`). The scenario
   must run without production Jira, without a `staging` branch and without
   GitLab approvals.
2. it also serves as an **end-to-end demo**:
   Outcome → Initiative → autofix review → strategy → Epics.

The scenario reuses and generalises `var/demos/strat-pipeline-replication`
rather than forking it. The fixture is
[`var/demos/initiatives/`](../../var/demos/initiatives/README.md).

## Components

| Component | Source | Role in the scenario | Mirror target |
| --- | --- | --- | --- |
| strat-creator | GitHub `fullsend-ai/strat-creator` (public) | `initiative-strategy` type; #124 adds the `strat-creator-ignore`/`initiative-ignore` exclusions | GitHub emulator (`main`, `pr-124`, `cc75-emulator`) |
| assess-strat | GitHub `opendatahub-io/assess-strat` (public) | Strategy review rubric | GitHub emulator |
| rfe-creator | GitHub `fullsend-ai/rfe-creator` (public) | Initiative autofix (`--type initiative`) | GitHub emulator (`main`, `ci-prod`, `ci-stage`) |
| epic-creator | GitHub `fullsend-ai/epic-creator` (public) | Decomposition into `RHAI` Epics; #40 adds the `rhai-initiative` workload | GitHub emulator (`main`, `pr-40`) |
| strat-pipeline | GitLab `redhat/rhel-ai/agentic-ci/strat-pipeline` (private) | `workflow-batch-initiative` job | GitLab emulator, same path |
| strat-pipeline-data | GitLab (private) | Strategy results repo | GitLab emulator, starts empty |
| strat-dashboard | GitLab (private) | Dashboard; not used on Initiative runs | GitLab emulator |
| rfe-autofixer | GitLab (private) | `autofix-initiative` job | GitLab emulator, same path |
| rfe-autofixer-results | GitLab (private) | Autofix results repo | GitLab emulator, starts empty |
| epic-decomposer | GitLab (private) | Decomposition job | GitLab emulator, same path |

The private code repos are mirrored as history-free snapshots with emulator
adaptations applied as tracked patches kept outside this repository. Their
data repos were not copied; they start empty. Public pins are recorded in the
fixture's manifests.

## Approach

- **Hosts.** w530 runs the stack (`BREADBOARD_DOMAIN=w530.local`). p15
  authors the fixture; w530 runs it from a separate worktree synced from p15.
- **Emulators.** Jira, GitHub and GitLab emulators stand in for production.
  A project-config import adds the Outcome issue type, Release Pending, an
  RHAISTRAT workflow, `Incorporates`/`Depend` link types and the `RHAI`
  project.
- **CI.** The GitLab emulator's Kubernetes-executor runner `glemu-k8s-runner`
  (privileged, emulator CA mounted) runs the mirrored jobs. Each job brings up
  its own Fullsend stack (Fullsend 0.55.0 and an OpenShell gateway, as pinned
  by strat-creator) with podman inside the job pod. The breadboard-deployed
  Fullsend is not used on this path.
- **Schedules.** Created on `main` only and **inactive**; scenarios trigger
  them with "play", so nothing runs on cron unattended. Schedule names:
  `initiative-dry`, `initiative-live-emulator`, `autofix-initiative` and
  `rfe-batch`.
- **CI variables set by our scripts** include `INITIATIVE_STRATEGIES`,
  `INITIATIVE_LIVE`, `STRAT_EXECUTOR`, `STRAT_DRY_RUN`, `FULLSEND_PUBLISH`,
  `BATCH_SIZE`, `AUTOFIX_SCHEDULE`, `AUTOFIX_LIMIT`, `RESULTS_REPO`,
  `CLAUDE_REPO`, `CLAUDE_REPO_BRANCH` and `JIRA_USERNAME`. Credentials are a
  synthetic Jira bot PAT, a GitLab results PAT and a Model Relay key, stored as
  masked variables; `bootstrap_credentials.py` generates them without
  printing them.
- **Model.** Standing rule from the human: **always use Model Relay**; no
  real model keys in CI. A dedicated relay project `cc75-initiatives` routes to
  a Vertex upstream account with an allowlist of `claude-opus-5-5`. Inside the
  sandbox the relay key is an OpenShell provider credential (the agent sees a
  placeholder), and the emulator CA is baked into a per-job sandbox image. This
  reuses the recipe already proven in `var/demos/fullsend-claude-workflow/`.
- **Synthetic seeding and snapshots.** A seeder creates the catalogue top-down
  and takes jira-emulator snapshots (`cc75-pre-seed`, `cc75-baseline`).
  Scenarios and the demo reset by restoring a snapshot.

## Synthetic Initiatives

- **Fully synthetic:** fictional product areas and codenames, fictional people
  (`synth-pm-01`, `synth-eng-03`) and neutral components (`synth-runtime`,
  `synth-ui`). No real text, names or Jira keys. Every summary is prefixed
  `[SYNTH]` and every issue carries `cc75-synthetic`.
- **Deterministic:** `generate_initiatives.py` renders the committed
  `catalogue.yaml` from hand-authored templates (no LLM), so reruns are
  byte-stable.
- **Idempotent:** issues are looked up by a `cc75-fx-<id>` label and created
  top-down (Outcome → Initiative → Epic → Story), because the emulator cannot
  change `parent` later.
- **Range of quality and size:** good (rich goals and requirements, complete
  template, Outcome parent), typical (Stories-only tracker, missing fields, no
  Epics) and poor (punctuation-only summary, cryptic summary, title only), plus
  a strategy-rich Initiative already signed off. Initiatives range from no Epic
  children to a long tail, with children in RHAI, RHOAIENG and AIPCC, and some
  with a legacy `Incorporates` link.
- **Variant labels:** opted in (`initiative-autofix-opt-in`), rubric-pass,
  needs-attention, ignored (`initiative-ignore`/`strat-creator-ignore`), a
  stale `strat-creator-processing` lock, closed-but-labelled, and not opted in.
- **Catalogue:** 79 issues after the I25 exemplar was added (3 Outcomes,
  25 Initiatives, 2 RFEs, Epics and Stories); the first seed had 78.
- **Oracle:** the generator also writes `expected.yaml` from the catalogue,
  not from Jira: the set each discovery query must select, the Initiatives
  epic-creator must skip and why, the expected label transitions and the
  bounds on generated Epic counts.
- **Codenames** that collided with well-known software were renamed (Harbor →
  Brackwater, Heron → Thornbill, Kestrel → Saltmarsh) after the model read
  "Harbor" as the CNCF registry in S6.
- **I25 exemplar** (RHAISTRAT-75028) was written to pass strategy review, for
  the demo.

## Scenarios

"Model?" says whether the scenario spends model tokens.

| ID | Scenario | Model? | Observable acceptance |
| --- | --- | --- | --- |
| S0 | Bootstrap: preflight, topology, credentials, config import, seed, snapshot; run twice | No | Second run creates nothing; issue count, parents, labels, status and link order match the catalogue; `cc75-baseline` exists |
| S1 | Discovery oracle: strat-creator, autofix opt-in and epic-creator skip queries against the emulator | No | Selected sets equal `expected.yaml` |
| S1b | The same through each tool's own discovery code | No | Matches the oracle |
| S2 | CI lint and contracts; gateway and sandbox smoke inside a CI job | No | Lint valid; Initiative job present and gated; the job-owned Fullsend stack starts on the pod runner |
| S3 | Tripwire: `INITIATIVE_STRATEGIES=on` without the dry flags on `main` | No | The pipeline fails closed; no Jira writes |
| S4 | Dry run with nothing selected | No | Pipeline succeeds with no work; no sandbox, no model, no writes |
| S5 | Initiative autofix on opted-in Initiatives | Yes | Only opted-in Initiatives are touched; gate labels applied; summaries unchanged; results in `rfe-autofixer-results` |
| S6 | Strategy dry canary, `BATCH_SIZE=1` | Yes | One oracle-predicted Initiative processed; zero Jira writes |
| S7 | Strategy live on the emulators (`BATCH_SIZE=1`, then 3) | Yes | Strategy and review attached to the Initiative; lock set and released; gate labels match the review; results under `initiative-strategy/` in `strat-pipeline-data` |
| S8 | Decomposition of signed-off Initiatives | Yes | `RHAI` Epics with `parent` = Initiative and `Blocks` between siblings; `epic-creator-auto-decomposed` set; Initiatives with existing Epics or a legacy link skipped; rerun creates nothing |
| S9 | Kill switch and rollback | No | Flag off runs only the old path; snapshot restore returns exactly the baseline |
| S10 | Feature regression: single RFE → Feature | Yes (1 item) | Behaves as before; no `initiative-*` labels on Features or RFEs |

Evidence is written to `var/demos/initiatives/evidence/` as sanitised JSON
(ids, label diffs, oracle comparison).

## Results

### No-model scenarios (2026-11-16)

| Item | Result | Evidence |
| --- | --- | --- |
| Mirror | GitHub emulator mirrors of the public repos; GitLab emulator mirrors of the private repos; re-runs converge | `topology-manifest.json`, `pipeline-manifest.json` |
| S0 | **Pass.** 78 issues seeded; read-back passes; second run converges (0 created) | `evidence/seed-*.json` |
| S1 | **Pass.** All discovery queries match the oracle | `evidence/discovery-*.json` |
| S1b | **Finding:** strat-creator `main` does not exclude `initiative-ignore` or `strat-creator-ignore` and selects two ignored fixture Initiatives; **#124** matches the intended contract exactly. The scenario pins #124; `main` stays mirrored to show the gap | `evidence/tool-discovery-*.json` |
| S2 gateway smoke | **Pass, first run.** The Fullsend 0.55.0 tarball passes its checksum; podman, the gateway and the sandbox come up in the job pod; Claude Code runs in the sandbox; 199 s total | `evidence/smoke-fullsend-gateway-*.json` |
| S3 | **Pass.** Without the dry flags the pipeline fails closed; with them it passes; 0 Jira writes | `evidence/S3-*.json` |
| S4 | **Pass.** Discovery selects nothing; the run is skipped with no sandbox or model; 0 Jira writes | `evidence/S4-20261116T010846Z.json` |
| S9 | **Pass.** Fingerprints of all fixture issues differ from the baseline only on the four S7 Initiatives; restoring the baseline matches exactly | `evidence/S9-20261116T160904Z.json` |

### Model-backed scenarios (2026-11-16; spend approved by the human)

| Item | Result | Spend |
| --- | --- | --- |
| S6 dry canary | **Pass.** Only the oracle's RHAISTRAT-75006 selected; create → refine → review; 109 relay requests, all 200; 0 Jira writes; review REVISE 4/8 | $6.03 (plus about $6 in earlier attempts) |
| S7a, first attempt | **Failed:** attachment written, read-back refused by the sandbox proxy because the emulator returned URLs on its public base URL. Fixed by using the emulator's canonical `https://jira.<domain>` everywhere | $2.84 |
| S7a | **Pass** (pipeline 26, job 54): 75006 got strategy and review attachments, `strat-creator-auto-refined` + `strat-creator-needs-attention`, a comment; lock released; writes only to 75006; snapshot `cc75-after-S7a` | $6.15 |
| S7b | **Pass** (pipeline 27, job 57): `BATCH_SIZE` 3 selected exactly 75009, 75010, 75019 and skipped 75006; all REVISE 4/8 with gate labels; snapshot `cc75-after-S7b` | $17.11 |
| S5 | **Pass** (pipeline 56): 3 opted-in Initiatives (75004, 75006, 75009); writes only to them; summaries unchanged; 75006 revised 6 → 9/10. 75004 and 75009 pass and are also flagged for a human, so the plan's "exactly one label" check was corrected | $6.04 |
| S8 | **Decomposes; both oracle skips fail** (pipeline 65). 75025 → 7 RHAI Epics, correctly linked and labelled. **Duplicate Epics:** 75026 (3 existing Epics) got 5 more and 75027 (legacy `Incorporates` link) got 4. Rerun selects nothing | about $24 including two earlier failed runs |
| S10 | **Pass** (pipeline 67): one synthetic RFE → one RHAISTRAT Feature, `strat-creator-rubric-pass`, no `initiative-*` labels, results only under `RHAISTRAT/` | $6.61 |
| I25 live check | Pipeline 69: review 5/8 REVISE (feasibility, testability and scope 1/2) | $7.40 |
| I25 tightened | Scope narrowed to one runtime, REST only, a defined benchmark. Pipeline 71: **7/8 APPROVE**, `strat-creator-rubric-pass`; snapshot `cc75-demo-75028-approved` | $8.30 |
| I25 end to end | Signed off, then decomposed: **11 RHAI Epics** after one review revision, `epic-creator-auto-decomposed`; Jira restored afterwards | $5.06 |

Spend to this point: about $92 in Fullsend/OTEL estimates.

### Eventual-state rehearsal (2026-11-17; about $20 approved by the human)

The mirror ran the private pipelines at the revisions expected to reach
production, with only `JIRA_USERNAME`, a live run on `main` with
`INITIATIVE_LIVE=on`, and emulator values supplied as project, schedule or
pipeline variables.

| Step | Result | Spend |
| --- | --- | --- |
| Autofix (schedule, limit 3), pipeline 89 | **Success:** 3 Initiatives, 2 pass, 1 rejected; labels applied | $4.01 |
| Live strategy on 75028, pipeline 90 | **Success:** strategy and review attached, `strat-creator-rubric-pass` | $7.53 |
| Decompose, pipeline 92 | 14 Epics, review accepted; **failed** before submit because our run left `RESULTS_REPO` pointing outside the emulator | $5.02 |
| Decompose, pipeline 96 (from snapshot `cc75-rehearsal-end`) | 10 Epics, review 14/14 accepted; **failed** at submit because our run did not point the job at the mirrored epic-creator #40 branch | $5.22 |
| Decompose, pipeline 99 (after the fix; the human said continue) | **Success:** review 11/14 → revise → 14/14; 12 Epics created (RHAI-75044..75055, parent 75028); 75028 labelled `epic-creator-auto-decomposed`; results pushed to the emulator; `JIRA_USERNAME` accepted | $5.47 |

Total $27.25 (about $20 approved; the last $5 after the human said to
continue). Fix (`f8df0d5`): `run_decompose.py` and `demo.py decompose` pass
`CLAUDE_REPO`/`CLAUDE_REPO_BRANCH` (GitHub emulator `pr-40`) and
`RESULTS_REPO` (emulator) as pipeline variables. Snapshots:
`cc75-rehearsal-end` (after strategy and sign-off) and
`cc75-rehearsal5-decomposed` (12 Epics). Jira is back at `cc75-baseline`.

## Findings in public components

- **strat-creator `main`** does not honour the ignore labels in Initiative
  discovery; **#124** fixes it (S1b).
- **epic-creator #40, duplicate Epics.** With the `rhai-initiative` workload,
  `--skip-if-has-epics` checks only `epic-creator-auto-decomposed`, so
  Initiatives with hand-made Epics or a legacy `Incorporates` link get
  duplicates. Confirmed by S8.
- **epic-creator #40, idle run fails.** With nothing to submit,
  `submit.py --workload rhai-initiative --all` exits 1, so a scheduled run
  with no work would go red.
- **Fullsend 0.55.0** allows harness fetches only from `github.com` and
  `raw.githubusercontent.com` with no override, so a stock binary cannot fetch
  a harness from an in-cluster forge, emulator or GitHub Enterprise. Local
  relative sources work and the mirror uses them. Worth raising upstream.
- **strat-creator** builds its results remote from `gitlab.com`; the mirror
  redirects it to the GitLab emulator through an opt-in variable.
- **OpenShell 0.0.112:** inside a Kubernetes pod the gateway takes its
  in-cluster bootstrap and exits unless `KUBERNETES_SERVICE_*` is unset; a
  TLS-terminating Jira provider fails certificate verification, so Jira is an
  opaque tunnel with an extra CA file.
- **Model Relay** requires Claude Code 2.1.280+ for `claude-opus-5-5`; the
  per-job sandbox image uses the Fullsend sandbox image's Claude Code.
- **Emulator gaps:** jira-emulator cannot change `parent` on update and drops
  unknown parents silently (G1), and has no `parent IN (...)` (G2); neither
  blocks the scenario. The GitLab emulator appears to count a failing
  `after_script` against the job, and turns a bare `true` list item into
  `True`.
- **w530** (no AVX2) cannot run x86-64-v3 images; the mirror uses images that
  run on it.

## Human decisions and approvals

- Phase 2 SSH work on w530 approved; sleep disabled on w530 to stop idle
  suspend.
- Pins: strat-creator #124 for Initiative scenarios; epic-creator #40 head
  (already bound to RHAISTRAT, so no rebind was needed).
- Private sources fetched by the human's chosen method and copied to w530; the
  data repos were not copied.
- Relay upstream: Vertex, through the dedicated `cc75-initiatives` project.
- Model spend approved in steps (S5–S8, S10, then about $20 for the rehearsal
  plus $5 more).
- Staging: CC-75 builds no staging branch, staging pipeline or sync MR. The
  only non-main branch is the emulator-only `cc75-live` of strat-pipeline,
  flagged to the human as a candidate to become a variable on `main`.
- VM-based runners deferred: job-owned podman in a pod is also the production
  design.

## Risks

| Risk | Status |
| --- | --- |
| Job-owned Fullsend stack inside a CI pod (podman-in-pod, egress, cold start) | Retired by the S2 gateway smoke |
| Image pull access from w530 | Retired: the job images pull anonymously |
| Upstream moves during the build (#124, #40, rfe-creator `ci-prod`) | Pins recorded in the fixture manifests; refreshing a pin is a deliberate ledger entry |
| Emulator fidelity (G1, G2, variable masking) | Seeder read-back checks, oracle loops and shell fallbacks |
| Synthetic text resembling real content | Hand-authored catalogue, `[SYNTH]` prefix, a lint that rejects real-looking keys and names outside the synthetic roster; human review of `catalogue.yaml` |
| Model spend and long jobs | `BATCH_SIZE=1` canaries, a dedicated relay project, inactive schedules |

## Demo outline (about 25 minutes)

`scripts/demo.py` runs each step through the verified jobs, and
`demo-script.md` follows RHAISTRAT-75028 from strategy to Epics. A full run
costs about $35 of model use when every signed-off Initiative is decomposed.

1. **Reset:** restore `cc75-baseline`; show the Outcomes and the `[SYNTH]`
   Initiatives, one good, one typical and one poor.
2. **Opt-in:** add `initiative-autofix-opt-in` to three Initiatives; the
   opt-in label is the canary boundary.
3. **Autofix review:** play `autofix-initiative`; good Initiatives get
   `initiative-autofix-rubric-pass`, the poor one
   `initiative-needs-attention` with an `[Initiative Creator]` comment.
4. **Tripwire:** a non-dry Initiative run on `main` fails closed; staging is a
   run configuration, not a branch (CC-74).
5. **Dry strategy:** play `initiative-dry` (`BATCH_SIZE=1`); the strategy
   artefact appears in the job with zero Jira changes.
6. **Live on the emulators:** show the strategy and review attachments, the
   gate labels and the `initiative-strategy/` folder in the data repo.
7. **Sign-off and decomposition:** add `strat-creator-human-sign-off` with
   `demo.py signoff`, run `demo.py decompose`, and show the RHAI Epics with
   `Blocks` links and `epic-creator-auto-decomposed`.
8. **Rollback:** turn the flag off and restore the snapshot.

## Main-only rollout patterns exercised (CC-74)

| Pattern | Exercised by |
| --- | --- |
| Default-off flags (`INITIATIVE_STRATEGIES`, `STRAT_EXECUTOR`) | S2, S9 |
| Dry run (`STRAT_DRY_RUN=1`, `FULLSEND_PUBLISH=0`) | S4, S6 |
| A staging schedule on `main` (`initiative-dry`) | S4, S6 |
| Scoped canary (opt-in label, `BATCH_SIZE=1`, `AUTOFIX_LIMIT`) | S5, S6, S7 |
| Emulators as the pre-production test bed | the whole fixture |
| Kill switch and fail-closed tripwire; live cutover rehearsed on the emulators | S3, S7, S9 |
| Oracle and label-diff evidence before widening from 1 to 3 | S6 → S7 |
| Pinned versions bumped deliberately | fixture manifests |
