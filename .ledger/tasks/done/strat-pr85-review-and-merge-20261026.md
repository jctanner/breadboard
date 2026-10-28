# Task: Address the October 26 PR #85 review and upstream merge conflict

## Goal

Return to feat/s1-workflow-hardening, assess and address new automated review
findings, and resolve the owner-reported conflict with current upstream main.

## Starting state

PR #85 head/local branch: 95a5c8f. Checkout was clean on the separate
feat/fullsend-ci-cutover branch (284389c); switched back without mixing its
four-job support changes into this PR. API fetched 42 reviews, 117 inline
comments and 24 conversation comments. Only open PR from this fork is #85.
It is now ready for review, with current head CI green, but reports merge conflicts.

## New findings

- 4380387588: direct review-summary write can leave a partial file blocking retries.
- 4380387603: missing create-inventory key uses next() without a default.
- 4380483679: lexicographic architecture-release ordering chooses 3.9 over 3.10.
- 4380483700: inherited DRY_RUN overrides validated publication metadata.
- 4380483695: repeated pending-verdict downstream compatibility check.
- 4380483687: Jira sandbox authority is a known owner-accepted scope decision.
- TLS, tracking issue and protected-path approval findings repeat prior rounds.

## Acceptance criteria

- [x] Fetch latest complete review/comment inventory and select the correct PR branch.
- [x] Verify and address concrete new defects with model-free regressions.
- [x] Resolve upstream main conflicts while retaining current fixes and upstream behavior.
- [x] Check pending-verdict consumers and preserve owner-approved security decisions.
- [x] Run full offline suite, relevant lint/checks and record evidence.
- [x] Include the owner-approved four-job CI support in PR #85.

## Constraints

No paid smoke or live Jira mutation. Preserve numeric-only approval gate,
temporary Org Pulse TLS exception and accepted sandbox trust scope.
Do not post review replies, resolve remote threads or fabricate tracking issues.
The owner subsequently confirmed the CI support must be included in PR #85.
Integrate commit 284389c into this branch after the merge/review repairs;
the separate branch itself need not be changed. Run the combined full suite.

## Local findings and progress

Fetched upstream main bb4887b. Two onboarding commits changed only the config
and two generated GitHub workflows. The single conflict is the config header:
retained the three strategy agents/remote prefixes and explanatory preservation
comments while accepting upstream version 1, fix role, issue-creation targets
and workflow updates. No unmerged index entries remain; merge is not yet committed.

All four code findings reproduced. Scoped baseline: 12 failures, three controls
pass. Initial tests also considered a GA/prerelease ordering policy change;
that was removed to preserve the existing suffix convention. Initial and final
red evidence are separate. All 15 targeted new cases now pass, including
actual process interruption, CLI execution and extractor child behavior.

Added downstream compatibility checks: JSON retains pending separately from
numeric recommendation; report/dashboard render pending neutrally. Existing
Org Pulse tests cover exclusion of provisional reviews. Documented this contract
in CLAUDE.md. No changes to the numeric gate or the accepted TLS exception.

Full offline suite and socket-enabled focused checks are running. Ruff,
type descriptors, shell syntax and diff checks pass. Initial focused selection
inside the sandbox failed only because existing Org Pulse tests bind sockets;
repeated outside the sandbox.

The first broad run caught a changed diagnostic for an empty architecture tree:
release selection now refuses earlier, still before any claim. Verified the
failure in isolation. Updated that existing test to cover both missing-release
and missing-PLATFORM rejection, then restarted the full suite. No production
behavior was relaxed to satisfy the test. Interrupted/before logs are retained.

Owner decision: fold the previously published 15-file four-job support commit
into #85, so its merge alone provides the upstream main interfaces expected by
the consumer MR !18. Patch application check succeeds against the current repairs.

The complete pre-parity suite passed: 1,301 tests, six optional skips, 439.64s.
Recorded merge 68b98f2 and review fixes 2ecd758 separately, then cherry-picked
the approved CI support with signoff/provenance as b8d67c3. No conflicts; component
clean. Combined full suite passes 1,362 tests with six optional skips (473.58s).
Actual consumer packaging passes. Forty-six-file source/review/regression
archive sealed under var/run-data/20261026-strat-pr85-review-and-merge/;
hash readback passes and credential findings are zero.
See [assessment](../../notes/strat-pr85-review-and-merge-20261026.md).

## Publication

Pushed all three signed-off commits to the existing PR branch. SSH remote
readback and GitHub API verify head b8d67c334697dc3297c67b608584f4d4dd600060.
GitHub reports mergeable=true against bb4887b: conflict resolved. Component
worktree is clean. DCO passed; other new-head checks had not yet reported.
No PR merge, paid smoke, live Jira write, deployment, reviewer reply or remote
thread resolution. Existing accepted TLS/security scope is unchanged. The
archive remains sealed with its historical pre-push metadata.
