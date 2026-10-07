# A3: Wire the GitLab branch and run one native strategy

Depends on [A2 prompts](../done/agent-led-strategy-prompts.md).

## Acceptance criteria

- [x] Add fixtures under `var/demos/fullsend-agent-led-poc/`; create and publish
  `feat/fullsend-agent-led-poc` in the existing GitLab project
  `redhat/rhel-ai/agentic-ci/strat-pipeline`. Record its branch base; preserve
  `main` and the completed `feat/fullsend-strategy-poc` branch.
- [x] Add the new `.gitlab-ci.yml` on that branch, following rfe-autofixer.
  Fetch the public strat-creator fork's `feat/fullsend-agent-led-strategy`
  branch and pin the tested commit for its prompts, skills and harness files.
  Use the maintained runner and existing approved credentials, with separate
  results/dashboard targets. Preserve shared project variables; use distinct
  POC variables or job overrides instead of changing the old workflow's pins.
- [x] Invoke released `fullsend run strat-single --fullsend-dir ... --target-repo ...`.
  No compile job, feature binary or custom entrypoint. Retain job-owned gateway
  readiness, CA trust, EXIT redaction and deterministic cleanup.
- [x] Reuse rfe-autofixer's working release/image combination, starting with
  Fullsend 0.43.0, and record version/checksum and image pins. Check native
  hooks, providers, pre/post scripts and result extraction while bringing up
  this workflow. Fix specific integration failures here; do not create a
  separate smoke harness, temporary probe branch or general infrastructure
  validation milestone. Explain any required published-version change.
- [x] Seed one fresh eligible RFE from existing fixtures without reset or
  processed-issue replay; verify identity and bounded inputs before launch.
- [x] Prove actual Vertex Opus 4.6 parent/child inference, create/refine/Jira
  push/context-backed review, validated structured output, released owned lock,
  results commits and sanitized artifacts. Truthful revise is an allowed outcome.
- [x] Verify Org Pulse readback and fresh post-publication dashboard separately;
  record any emulator recovery required. Verify gateway/container/network cleanup.
- [x] Exercise no-work/failure boundaries without more model writes. Retain
  partial effects, incomplete phases and original failure; no blind auto-rerun.
- [x] Run relevant checks and `git diff --check`; commit/push the new CI branch,
  run acceptance jobs explicitly on it, and record branch/source SHAs,
  pipeline/job IDs, issue/result references and remaining differences.

## Inputs from A2

CI sets `STRAT_RUN_ID` (e.g. the job ID) and `STRAT_STATE_DIR`, a host
directory in the job container that is not mounted in the sandbox. It
optionally sets `STRAT_LOCAL_CA_FILE`, `STRAT_PUBLISH_DIR` and
`STRAT_ARCHITECTURE_CONTEXT_PATH`. After `fullsend run`, whatever its exit
status, CI runs `.fullsend/shared/release-locks.sh "$STRAT_STATE_DIR"`. On a
pre-script skip, CI publishes `$STRAT_STATE_DIR/preflight-result.json`.

## Breakpoints

| # | What you get | How to check | Question |
| --- | --- | --- | --- |
| B3.1 | `feat/fullsend-agent-led-poc` published with the new CI; one no-work job (strat-batch with empty discovery, so no Jira writes; no RFE is currently locked): released 0.43.0 installed and checksummed, gateway healthy, pinned fork cloned, pre-script skips (exit 78) with no sandbox or model, `preflight-result.json` artifact, lock release and cleanup logged | Pipeline and job trace in `https://gitlab.local`; artifacts | Is the CI shape right before spending a model run? |
| B3.2 | One fresh RFE through native strat-single on Opus 4.6: STRAT in Jira, validated result, released lock, commit in the new results repo, Org Pulse and fresh dashboard readback, cleanup | Jira issue, results commit, dashboard, job artifacts | Is the output right? |
| B3.3 | No-work and failure boundaries without more model writes (e.g. context failure before lock, bad key), evidence recorded | Pipelines and ledger | Go to A4? |

## Verdict log

| Breakpoint | Verdict | Date | Notes |
| --- | --- | --- | --- |
| B3.1 | Go | 2026-10-07 | (2) Publish to the existing `strat-pipeline-data`, not a new results repository. (3) No separate dashboard target. (4) Use a distinct RFE rather than the repeated `rhai-cli diagnose` template. CI YAML confirmed fine. |
| B3.2 | Go | 2026-10-07 | Attempt 2 (pipeline 2078) accepted; proceed to B3.3. |
| B3.3 | Done; awaiting A4 go | 2026-10-07 | See B3.3 evidence. |

## Design notes

- Vertex: 0.43.0 registers the upstream `vertex-ai` provider with a no-op
  credential (`--credential _NOOP_VERTEX_AI=`, `internal/sandbox/sandbox.go`),
  and the pinned profile injects nothing. Claude refreshes tokens from the
  mounted ADC file via `*.googleapis.com`, as in rfe-creator. The existing
  `authorized_user` ADC should work without the script-led POC's
  `--from-gcloud-adc` shim; B3.2 proves it.
- Release: `fullsend_0.43.0_linux_amd64.tar.gz` sha256
  `e56be72bb2af7210418307e784d65a8ead4ff736540c077f75d258865e595f10`
  (matches the release `checksums.txt`); binary sha256
  `7728f2f3a3bb3fd57a1306f8505e0040a89fc670082695acbc65a72f5243dd14`.

## B3.1 handoff (2026-10-07)

- **Branch:** `feat/fullsend-agent-led-poc` in project 7, created from
  `main` `14d81319af44973d592e4197b14b680684f35813`. Head `7677bfd`;
  first commit `36af250`. `main` and `feat/fullsend-strategy-poc`
  (`4810e17`) are unchanged.
- **Variables:** the shared project variables were checked by name only;
  none were created or changed.
- **Fixtures:** `var/demos/fullsend-agent-led-poc/` (`ci/`, `publish.py`,
  `test_ci.py` with 6 tests). Not yet committed to Breadboard.
- **Pipeline 2075 / job 4036 failed, as an integration finding.** Fullsend
  0.43.0 rejects any harness `${VAR}` that is unset on the host; empty is
  allowed (`internal/harness/harness.go:689`). The unset variable was
  `STRAT_ARCHITECTURE_CONTEXT_PATH`. It failed before the pre-script, so no
  locks were taken and no sandbox started.
  - Fix: `ci/strategy.sh` exports every optional variable, defaulting to
    empty.
  - `test_ci.py` now cross-checks both harnesses' references.
  - Follow-up: the strat-creator README must say optional variables must be
    set, even to empty.
- **Pipeline 2076 / job 4037 succeeded** (strat-batch, no work):
  - fork pinned at `508ea33`;
  - release tarball checksum OK; binary sha256 `7728f2f3…dd14`;
  - OpenShell CLI and gateway `0.0.112-rhaiv.0`; supervisor
    `sha256:48062232…0db2`; sandbox `sha256:259605fe…995a`;
  - gateway healthy;
  - the released binary loaded the harness, passed the validation
    dependency check, and created the `vertex-ai` provider without a shim;
  - the pre-script fetched architecture context `rhoai-3.6-ea.2`;
  - discovery excluded 10 processed RFEs, so the pre-script exited 78 and
    no sandbox or model ran;
  - `preflight-result.json` is a valid skipped result;
  - release-locks found no record;
  - `cleanup_exit=0`, with no containers or job network left; redaction
    changed 0 files. The runner left job 4037's pod in `Error` (exit 137
    after success), the same as job 3924 earlier:
    [bug](../../bugs/open/gitlab-runner-job-pods-left-in-error.md).

Open for B3.2:
- the results project name;
- the dashboard target (strat-dashboard `main` hardcodes
  `strat-pipeline-data`);
- seeding one fresh RFE, a Jira write via
  `var/demos/fullsend-entrypoint-poc/jira-seed/batch.py`.

## B3.2 attempt 1: pipeline 2077 / job 4038 (2026-10-07)

- **Seed:** RHAIRFE-11, *Configurable retention for Data Science Pipelines
  run artifacts*, from `seed_rfe.py --scenario dsp-retention`. Verified
  first: discovery returned exactly RHAIRFE-11; no clones, links or
  attachments.
- **Branch and source:** branch head `8b9e3ab`, fork `508ea33`.
- **Host lock and agent:** the host locked RHAIRFE-11 (`run.json`,
  `gitlab-job-4038`). The agent ran natively for 1103 s and exited 0.
  - Phases recorded in order: create 21:39:41, refine 21:45:36, push
    21:45:43, review 21:56:06.
  - The result claims RHAIRFE-11 -> RHAISTRAT-11, approve, context
    available.
- **Models:** all `claude-opus-4-6`; the parent and 6 subagents, 273
  assistant turns.
- **Jira:** RHAISTRAT-11 is Cloners-linked and pushed, with labels
  `auto-created`, `auto-refined` and `rubric-pass`. The review is attached
  and a comment posted. Score 6/8; prose reviewers 1 approve, 3 revise.
- **Validation failed on a validator bug:**
  [bug](../../bugs/fixed/agent-led-validator-required-unanimous-prose-reviewers.md),
  fixed in fork `a2b888a`. The post-script was skipped, so nothing was
  published.
- **Locks:** release-locks unlocked RHAIRFE-11, and the record was renamed
  `.released`.
- **Cleanup:** no containers, network removed. The `cleanup_exit=1` came
  from the wrapped command's status (`fullsend run` returned 1). The
  gateway now logs `command_exit` and `cleanup_exit` separately.
- **Output scan:** Fullsend's post-agent scan NFKC-normalized fullwidth
  characters and redacted 3 `env_assignment` patterns per file in the
  transcripts. Our redaction changed 0 files.
- **Republished:** CI pinned at `a2b888a`; branch head `242608b`.

A second RFE scenario, `registry-serving-guard` (Model Registry: block
archiving served versions), is ready. It has not been seeded. Another
model run needs an explicit go; no blind rerun.

## B3.2 attempt 2: pipeline 2078 / job 4039, success (2026-10-07)

- **Seed:** RHAIRFE-12, *Block archiving Model Registry versions that are
  still being served*, from `seed_rfe.py --scenario
  registry-serving-guard`. Verified first: discovery returned exactly
  RHAIRFE-12; no clones.
- **Source:** fork `a2b888a`, branch head `242608b`.
- **Host lock:** the host locked RHAIRFE-12 (run `gitlab-job-4039`).
- **Agent:** ran natively for 1152.7 s and exited 0. Phases in order:
  create 22:53:29, refine 22:57:47, push 22:57:53, review 23:10:47.
- **Models:** all `claude-opus-4-6`; the parent and 6 subagents, 275
  assistant turns.
- **Validation:** "completed single result matches run record, artifacts,
  progress and Jira". The Jira readback ran this time.
- **Review:** 8/8 approve; prose reviewers 2 approve, 2 revise
  (informational).
- **Jira:** RHAISTRAT-12 is Cloners-linked to RHAIRFE-12 and pushed, with
  labels `auto-created`, `auto-refined` and `rubric-pass`. The review is
  attached and a comment posted.
- **Locks:** release-locks unlocked RHAIRFE-12, and the record was renamed
  `.released`.
- **Results:** in `strat-pipeline-data`, run commit
  `28c3825a411ad6f694dfddaa53b782dbd3ca5925` (run `20261007-231219`) and
  summary commit `2db3a1bc17c7b059c58eed29d648171197bd1a05`.
  - `RHAISTRAT/current` -> `20261007-231219`.
  - `summary.json` and `summary-production.json` have the run as current:
    single-rfe, not a dry run, RHAISTRAT-12 <- RHAIRFE-12, approve 8/8.
  - Run files: task, review, RFE snapshot, comments, pre-push snapshot,
    report and pipeline-data.
- **Org Pulse:** the bulk push reported 1 created, 799 unchanged and 16
  historical validation errors, but the per-feature GET returned 404 and
  the index lacked the key. This is the known stale-key bug
  ([open bug](../../bugs/open/org-pulse-ingest-recreated-jira-keys-stay-stale.md)).
  - Recovery, as documented: `POST /api/admin/refresh/handler`
    `releases:jira-sync` returned 202. It reads Jira only; no model replay
    and no file edits.
  - Afterwards `GET .../features/RHAISTRAT-12` returned latest run
    `20261007-231219`, sourceRfe RHAIRFE-12, the RFE's title, approve,
    needsAttention false, scores 8/8 and the prose reviewer verdicts.
  - RHAISTRAT-11 reads back an unrelated run `20260929-231800`. That key is
    reused from pre-reset data, and run 4038 was never published.
- **Cleanup:** `command_exit=0`, `cleanup_exit=0`; no containers or job
  network left.
- **Credential scan:** job 4039 artifacts, 31 files, and job 4038, 32 files,
  each checked against 9 credential kinds (ADC refresh token and client
  secret, Jira token and Basic form, results token and Basic form, Org Pulse
  token, Vertex JSON). 0 hits.
- **Redaction:** our redaction changed 0 files.

- **Dashboard:** a fresh strat-dashboard `main` build, pipeline 2079 / pages
  job 4040, ran after publication and succeeded.
  `public/runs/20261007-231219.json` exists, and `public/summary.json` and
  `public/index.html` both contain the run and RHAISTRAT-12.

## B3.3: failure boundaries without model writes (2026-10-07)

Both runs used branch head `242608b` and fork `a2b888a`.

- **Pipeline 2080 / job 4041: context failure before locking.**
  strat-single on RHAIRFE-12 with `STRAT_ARCHITECTURE_CONTEXT_PATH` set
  to a path that doesn't exist. The pre-script reported "architecture
  context fetch failed" and exited 1, so Fullsend reported "Pre-script
  failed". No run record, no sandbox and no lock. release-locks found no
  record. `command_exit=1`, `cleanup_exit=0`.
- **Pipeline 2081 / job 4042: invalid key.** `RFE_KEY=RHAIRFE-x12`. The
  context fetch succeeded, then `prepare_run` rejected the key and exited
  1. Otherwise the same as job 4041: no run record, sandbox or lock;
  `command_exit=1`, `cleanup_exit=0`.
- **Jira:** RHAIRFE-12 has no processing label, and its `updated` is
  unchanged since run 2078's release (23:12:32). No model ran.
- **Credentials:** jobs 4041 and 4042 have 0 hits each (14 files).
- **Already covered elsewhere:**
  - post-lock failure releasing locks: attempt 1, pipeline 2077;
  - the native no-work skip: B3.1, pipeline 2076;
  - blocked-RFE skip: emulator tests. Running it in CI would need a
    temporary Jira label write, so it was not run.

## Remaining differences

- **Results:** published to the existing `strat-pipeline-data` and
  strat-dashboard `main`, shared with the script-led POC by decision.
  `publish.py` has no option to create a separate repository.
- **Org Pulse:** readback needed the documented `releases:jira-sync`
  recovery ([open bug](../../bugs/open/org-pulse-ingest-recreated-jira-keys-stay-stale.md));
  it is not durable.
- **Unpublished run:** RHAIRFE-11 / RHAISTRAT-11 is processed in Jira, but
  its run was never published (validator bug in attempt 1). Org Pulse shows
  an unrelated September run for that reused key.
- **Dashboard:** no downstream bridge; a fresh build was triggered by hand
  after publication, because of the eager-bridge emulator bug.
- **Serialization:** `resource_group: strat-agent-led` serializes this
  branch's jobs only. Coordination with the script-led and `main` jobs is by
  Jira processing labels.
- **Runner pods:** finished job pods are sometimes left in `Error`
  ([open bug](../../bugs/open/gitlab-runner-job-pods-left-in-error.md)).
- **Retries:** one validation iteration; there are no automatic retries.
- **Events:** A4 covers event triggers and batch with a model.

## Status

Done, 2026-10-07. A4 waits for an explicit go.
