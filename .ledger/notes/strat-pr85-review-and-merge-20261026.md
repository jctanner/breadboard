# PR #85: October 26 review repairs and upstream merge

## Review inventory

Fetched all pages: 42 reviews, 117 inline comments and 24 regular comments.
The PR head was 95a5c8f; it was no longer draft, CI checks passed on that head,
and GitHub reported a conflict with current upstream main.

Latest reviews:

- [Qodo 5656278242](https://github.com/fullsend-ai/strat-creator/pull/85#pullrequestreview-5656278242).
- [Fullsend 5656403797](https://github.com/fullsend-ai/strat-creator/pull/85#pullrequestreview-5656403797).

## Findings and disposition

| Finding | Result |
| --- | --- |
| 4380387588: partial review-summary write blocks retry | Reproduced with the real publisher/composer and file-size-limited child processes. Write to a unique temporary file, fsync and atomically replace. Matching completed summaries are not rewritten; different existing summaries still refuse. |
| 4380387603: unplanned review produces StopIteration | Reproduced with the real CLI and a valid composition missing from a legacy-compatible create inventory. Require one unique inventory target before mutating progress. Managed freshness may reject corruption earlier; this is controlled-error handling. |
| 4380483679: architecture versions sort as text | CI, local-copy and remote-listing paths now share numeric directory-name ordering. 3.10 beats 3.9 and ea.10 beats ea.2. Preserve the existing suffix convention; do not introduce a separate GA/prerelease policy. Reject non-directory aliases in discovery. |
| 4380483700: inherited DRY_RUN changes publication metadata | Reproduced live results misclassified for both DRY_RUN=0 and =1. Remove only the legacy variable from the extractor child. The validated result alone supplies --dry-run. |
| 4380483695: downstream pending compatibility | Checked JSON exporter and report/dashboard renderers; pending remains explicit and neutral, separate from numeric approval. Added regressions and artifact-convention documentation. Org Pulse's existing tests cover excluding provisional reviews. |
| TLS and sandbox Jira authority | Repeated accepted scope/risk decisions. Preserve the owner's temporary TLS exception and writable/raw-token design; no host-only-writer redesign. |
| Tracking issue/protected-path approval | Repeated process findings. The owner scope comment remains the existing authorization evidence; do not fabricate a tracking issue or reviewer approval. |

## Upstream merge

Upstream main bb4887bc397eee9610ef4170b56a4c7cf8eef295 contains two onboarding
updates. The only conflict was .fullsend/config.yaml. Retained the three
strategy agents and remote-resource prefixes, accepted upstream version 1,
role list, issue-creation targets and generated-workflow updates. A structural
comparison verifies all generic upstream agents/settings survived unchanged.

Local signed-off commits:

- 68b98f27de1aa0c90df854b6a842fcaab7bedfdd: merge upstream main.
- 2ecd758281bf7396b8c439c670d77185c1089da6: review repairs and regressions.
- b8d67c334697dc3297c67b608584f4d4dd600060: four-job CI support, cherry-picked
  from 284389c with provenance and signoff.

The owner explicitly chose to include the CI support in #85. This makes its
merge provide the upstream-main interfaces expected by pipeline MR !18, without
a separate source PR. The original companion branch remains untouched.

## Verification

Scoped red run: 12 failures, three controls pass. Initial test drafting also
assumed a GA/prerelease precedence change; that was removed to preserve existing
behavior. Both red logs/XMLs are retained. New fixes: all 15 direct regressions
pass. Expanded selection: 47 pass, five optional skips.

The first broad run detected a changed diagnostic when release selection now
rejects an empty tree earlier. Confirmed the error in isolation and added both
missing-release and missing-PLATFORM cases, retaining the no-claims assertions.
That interrupted run and before-case log are retained. The complete rerun of
the repairs plus upstream merge passed 1,301 tests with six optional skips in
439.64 seconds.

The combined suite including CI parity passed **1,362 tests with six optional
skips**, 473.58 seconds. Ruff, type descriptors, shell syntax and diff checks
pass. Actual upstream-main consumer registrations
package against one synthetic local source snapshot with all three harnesses,
their companions and commit/hash-bound runtime URLs. No model or external
service call is made by that probe.

Source, complete patch, raw API snapshot, scoped red/green evidence, focused
results, interrupted/before diagnostics and both successful full-suite logs
are sealed under `var/run-data/20261026-strat-pr85-review-and-merge/`: 46 files,
verified hash readback, zero credential findings. The archive records the
committed pre-push state and remains unchanged.

No paid smoke, live Jira write, deployment, PR merge, reviewer reply or thread
resolution. Root ledger changes are separate from component source commits.

## Publication and current PR state

Pushed the three signed-off commits to feat/s1-workflow-hardening. SSH remote
readback and GitHub API confirm head b8d67c334697dc3297c67b608584f4d4dd600060.
GitHub reports mergeable=true against base bb4887b, with mergeable_state=blocked
while checks/approval complete. DCO passed; other new-head checks had not
reported at readback. Do not describe old-head CI as validation of this head.
The component worktree is clean. The PR itself was not merged, and no reviewer
reply, thread resolution, paid smoke, live Jira change or deployment occurred.
The accepted TLS/security exceptions remain as previously decided by the owner.
