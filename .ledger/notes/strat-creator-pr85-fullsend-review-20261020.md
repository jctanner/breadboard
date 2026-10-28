# PR 85: Fullsend review triage, October 20

Assessed source `8b2f1e0ae453a67a6518ba989d3816aeba991e1f`, the same
head reviewed by Fullsend. The new review contains **14 distinct findings**:
nine inline comments, four documentation findings in a fallback review, and
one protected-path finding in the summary. Status/risk comments and repeated
summary text are not additional findings. The full paginated export contains
91 historical and current entries, saved to
`/tmp/strat-creator-pr85-fullsend-review-current.txt`.

[Review summary](https://github.com/fullsend-ai/strat-creator/pull/85#issuecomment-6294590490)
and [fallback documentation findings](https://github.com/fullsend-ai/strat-creator/pull/85#pullrequestreview-5587439411).

## Repair priority

1. **Fresh-ticket dry runs fail.** Actual host preparation selects an eligible
   fresh RFE with `dry_run=true` and live input freshness. A local `STRAT-7001`
   task with `jira_key=null` then causes `record-create` to request that
   nonexistent strategy from Jira: HTTP 404, no saved create progress. This
   blocks the default real-GitLab dry-run smoke. The existing host dry-run test
   checks preparation and absence of a lock, not creation through completion.
   Repair strategy identity handling across create, push and verification;
   keep live RFE freshness and real strategy/SME readbacks. Do not globally
   turn off live checks for dry runs.
2. **The dashboard drops identified runs.** The publisher produces
   `RHAISTRAT/run-<run_id>` with a `strat-publication-v1` manifest.
   `extract-pipeline-data.py:301` supports this layout, but
   `generate-dashboard.py:605` accepts only timestamp names. A real publisher
   fixture is omitted; an identical timestamp-named copy is included. The
   GitLab dashboard job invokes this generator. Keep stable run identities
   and the rule that retrying an old publication cannot move `current` over
   a newer run. Share the discovery contract and sort by recorded time.
3. **Org Pulse rejects new reviewer states.** `build_features` passes reviewer
   values unchanged. Against the checked-out Org Pulse validator, a valid
   control is accepted, all four `pending` variants are rejected, and
   architecture `skipped` is rejected. Null is rejected too, so the suggested
   null mapping is not a repair. `pending` is provisional and should not
   escape a completed review; `skipped` is an allowed final architecture
   result when context is unavailable. Define the consumer contract without
   inventing approval or altering the numeric gate. The publisher logs
   validation warnings but exits zero by design; this is non-blocking loss of
   telemetry, not a silent strategy-processing failure. Live production Org
   Pulse deployment behavior was not exercised.

## Disposition of every finding

| Finding / comment | Disposition | Action |
| --- | --- | --- |
| High: dry-run freshness, `4326850662` | Confirmed functional defect | Priority 1 above; full lifecycle regression with a fresh local strategy. |
| High: protected paths, summary only | Maintainer/process requirement | Fullsend policy requires a linked issue and scope rationale, then human approval. A successful benchmark does not satisfy this policy. No issue or approval was fabricated. |
| Medium: recovery label-gate difference, `4326850675` | Intentional exception; clarify shared guidance | Recovery verifies and republishes an already composed current-run review after interrupted publication. It does not create or refine new work. Preserve normal label gates; document this exception in CLAUDE.md rather than broadening all three skills. |
| Medium: reviewer schema, `4326850682` | Confirmed consumer mismatch | Priority 3 above; distinguish provisional pending from a final architecture skip. |
| Medium: publication layout, `4326850689` | Confirmed consumer defect | Priority 2 above. The layout is already documented/versioned; the missing dashboard reader update is real. |
| Low: repeated Step 7, `4326850697` | Accept | Renumber publication and final advice. |
| Low: relative publisher path, `4326850708` | Accept | Use the skill-directory helper path in both recovery and publication examples for portable skill use. |
| Low: README test-unit description, `f_46156e333c4fea42` | Accept | It now runs all offline checks, including emulator integration/E2E coverage. |
| Low: README smoke target, `f_a44d6300ba05a7bd` | Accept | Document the separate explicit model-calling target. |
| Low: README missing strat-reviewer, `f_63b1242e529b6565` | Accept | Update the implementation table and agent tree. |
| Low: CLAUDE testing guidance, `f_7223f241ac56047a` | Accept | Explain offline coverage and optional paid smoke accurately; retain full-suite-before-push requirement. |
| Low: lock CLI errors, `4326850715` | Accept diagnostics/docs; keep owner protection | An unowned unlock correctly leaves the owned claim intact, but emits a traceback. Catch expected errors and document owner/record arguments. |
| Low: managed config marker, `4326850724` | Do not reverse onboarding reconciliation | Maintainer corrected the installer-ownership premise; committed config is the supported registration point. Checked-out Fullsend setup preserves existing config on ordinary reruns and has explicit preservation tests. Keep registration tests; qualify any claim about a different installer version. |
| Low: write retries/clone marker, `4326850731` | Intentional safety behavior; clarify contract | Reads retry; uncertain writes reconcile instead of blindly repeating. Owner checks are already a no-op outside a pipeline/effects context. Known discovery gates match explicit labels and ignore the clone marker; arbitrary external filters remain outside this audit. |

The four fallback finding IDs above belong to review `5587439411`. Inline
comments belong to changes-requested review `5587439682`; none are outdated
relative to the assessed head.

## Local evidence and limits

Seven model-free checks pass in the final probe run. These are **reproduction
and safety-control checks**, not evidence that the reported bugs are fixed:

- Fresh eligible RFE, real pre-script, live isolated Jira, dry-run create
  recording fails with the synthetic key's 404 before progress is saved.
- Actual producer-to-Org-Pulse-validator payload: approve control passes;
  four pending variants and architecture skipped fail validation.
- Actual identified-run publisher output is omitted by the dashboard;
  identical content under a timestamp directory is included.
- Unowned CLI unlock retains processing/owner labels but leaks a traceback.
- Standalone side-effect context and owner check need no pipeline owner and
  make no owner-validation Jira calls.
- Existing read-versus-write retry regression passes.
- Existing interrupted review-publication recovery test passes; recovery
  preserves content, numeric verdict and dissent, with one comment/attachment.

Reproduction file: `/tmp/test_pr85_review_probes.py`; JUnit receipt:
`/tmp/pr85-review-probes-20261020.xml`. Command, from the source checkout:

```bash
uv run pytest /tmp/test_pr85_review_probes.py \
  tests/test_side_effect_recovery.py::test_http_read_retries_are_distinct_from_write_reconciliation \
  tests/test_side_effect_recovery.py::test_completed_review_recovers_publication_without_regeneration \
  -q -s --tb=short --disable-warnings \
  --junitxml=/tmp/pr85-review-probes-20261020.xml
```

Consumer inspected: `checkouts/rhai-org-pulse` at `718ffa29799afcbb8f7a09e4427baa2b31dfad19`,
`modules/ai-impact/server/features/validation.js:111` and bulk route at line 157.
Dashboard wrapper: `checkouts.tmp/gitlab_rhel_agentic_ci/strat-dashboard` at
`0bb887f7766d10df26f25cae14c66422d6e546e4`, `.gitlab-ci.yml`; it clones the
creator and invokes `scripts/generate-dashboard.py`, and its JSON-copy loop
does not itself require timestamp names. Neither external deployment was
modified or called.

Fullsend review policy is explicit in the checked-out agents repo,
`skills/pr-review/SKILL.md`, Protected paths: absent a linked issue, the bot
must request changes; sufficient context still requires human approval.
Onboarding premise was corrected in
[the maintainer's comment](https://github.com/fullsend-ai/strat-creator/pull/85#issuecomment-6220196013).
Checked-out Fullsend `a734637c` has the complementary implementation in
`internal/cli/github.go:318` and preservation regressions beginning at
`internal/cli/github_test.go:1657`; those are source evidence, not a test of
every deployed installer version.

No source/component changes, PR replies, thread resolutions or new paid model
runs were made during this triage. Earlier passing processing batches do not
cover these fresh dry-run and downstream reporting cases. Repair the first
issue before using the default dry-run smoke as deployment evidence.

## Authorized repairs, October 20

The user authorized the repairs after triage. Local source changes on
`feat/s1-workflow-hardening` now address the actionable code/documentation:

- Freshness distinguishes a real `RHAISTRAT-*` identity from a local dry-run
  `STRAT-*` task. Only an actual dry run with null Jira identity gets the
  local exception. Real identities and paths are checked; live RFE changes
  and existing-strategy SME edits still fail closed. The fresh-ticket test
  uses actual host preparation and completes create/refine/push-skipped/
  composition/publication/result plus trusted host validation.
- Dashboard and summary share `discover_runs()`. Both read legacy timestamp
  directories and manifest-identified runs, normalize explicit time offsets,
  sort history by generation time, and reject invalid identified metadata.
  Neither stable publication identity nor current-pointer recovery changed.
- Completed Org Pulse export warns and excludes provisional pending reviews;
  all original artifacts remain. Final architecture skips and specialist
  dissent are preserved, with unchanged numeric recommendation. A matching
  consumer fixture documents the contract on both sides.
- Duplicate skill step numbers and relative publisher paths are corrected.
  README/CLAUDE describe the offline suite, opt-in model smoke and reviewer
  agent. CLAUDE explains the review-only recovery exception, read retry versus
  write reconciliation, standalone ownership and clone-marker semantics.
  Owned-lock CLI errors now return status 2 and a clear message, preserving
  the claim and record; owner/record flags are documented.

The Org Pulse API repair is isolated in
`checkouts.tmp/rhai-org-pulse-review-contract`, branch
`fix/strategy-reviewer-state-contract`, based on freshly fetched upstream main
`3a56474079b862605d310c2ebc96b72a478953b5`. It permits `skipped` only for
architecture, rejects provisional pending everywhere, and preserves numeric
verdict and dissent through actual bulk validation/forwarding. Data-format
docs, an example fixture, unit/route tests and an isolated HTTP integration
test accompany the change. The original Org Pulse checkout remains clean on
its existing feature branch. No deployment was changed.

Source full `make test`: **1,136 passed, six optional skips**, 315.05s. Full
`make lint` passes Ruff and type descriptor validation. New dry-run, live-SME,
local-identity rejection, mixed-layout/timezone, metadata rejection, pending
export and ownership-error regressions are included. Consumer focused tests:
**67 passed**; isolated HTTP integration: **one passed**. Consumer full lint
passes. Actual Python producer output passes the repaired Node validator,
with equal producer/consumer fixtures; the unchanged older validator still
rejects it. Evidence: `/tmp/pr85-org-pulse-contract-receipt.json` and
`/tmp/pr85-fullsend-review-repairs-source-tests.log`.

The first full consumer suite ran inside the sandbox: 6,330 passed, 52 failed
and eleven skipped, with 52 `listen EPERM` errors from local HTTP servers.
That is an execution-permission failure, not a reproduced application
regression. With local listening permitted, the full suite passes:
**6,382 passed, eleven skipped**, all 344 files, in 69.07s. Receipt:
`/tmp/pr85-fullsend-review-repairs-org-pulse-tests-permitted.log`.
The standalone HTTP integration passed in 1.4s and does not require a browser
or deployed service. All three working trees pass `git diff --check`.

After the user authorized commit/push, published signed-off source `080700e`
to PR 85, companion Org Pulse `84f08dca` to the fork's separate feature branch,
and GitLab consumer `6f996e2` to MR 15. Its source pin and both remote
registrations now use the repaired source; verified harness hashes are
unchanged. Pipeline's full 69 tests, actual published-source CI bootstrap and
native Fullsend locks pass. Bootstrap receipt:
`/tmp/strat-minimal-consumer-fq3wka_i/result.json`. MR pipeline 2968770749 is
successful on 6f996e2. All remote heads verified and worktrees clean; staged
credential checks pass for 23 changed files. The Org Pulse companion still
must land/deploy before its older API accepts architecture skips, and the
actual real-runner smoke remains unqualified.
No paid benchmark, PR response, thread resolution or tracking issue was created.
Fullsend's protected-path issue/rationale and human approval requirement
remains a maintainer action; successful tests cannot grant that approval.
