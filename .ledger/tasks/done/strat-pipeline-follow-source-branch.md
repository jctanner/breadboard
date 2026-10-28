# Follow a strat-creator branch between runs

## Goal

The user requested following a branch rather than maintaining a fixed source
commit in the GitLab pipeline. Default to the existing
feat/s1-workflow-hardening branch in the user's strat-creator fork, while
preserving one immutable source snapshot throughout each individual job.

## Acceptance criteria

- [x] Pipeline configuration selects the branch without stored commit/hash updates.
- [x] Bootstrap resolves that branch once and exports the observed source commit.
- [x] Private Fullsend registrations, hooks, validators and target use that snapshot.
- [x] New jobs follow branch advances; prepared jobs retain their previous snapshot.
- [x] Reject mismatched registrations/source and invalid branch input.
- [x] Update documentation and pass source/pipeline offline checks and native locks.
- [x] Publish source helper changes to existing PR #85 and a new pipeline feature MR.

## Scope

Source changes stay on the existing strat-creator feature branch. Consumer
branch feat/fullsend-follow-source-branch starts from merged upstream main
38efbce. Keep only config.yaml in the consumer's .fullsend directory.
No paid run, production schedule change or automatic merge. The attachment
egress and live-review fallback bugs remain separate follow-ups.

## Completed: 2026-10-21

Published signed-off source `630fccab1471d32dc41cc2912986975977996b07` to
existing [PR #85](https://github.com/fullsend-ai/strat-creator/pull/85), head
verified through GitHub. It accepts branch registrations and binds the private
runtime config to the already fetched snapshot and actual harness digests.
Existing explicit commit/hash consumers remain supported. The target checkout,
hooks and validators continue using the resolved snapshot. Source receipts
include branch, observed commit and harness hashes.

Published signed-off consumer `caaf92eb7031de2e1512034220d0c31ce3513d1d` on
feat/fullsend-follow-source-branch, from merged upstream main 38efbce, and opened
[MR !16](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/16).
Remote read-back verifies source/target, single expected commit, no conflicts,
ready for review and awaiting approval. MR CI 2972921135 was running at final
read-back. No merge is requested, so production main retains its old source
selection until MR !16 lands.

Consumer configuration now sets STRAT_CREATOR_BRANCH=feat/s1-workflow-hardening,
with matching unhashed branch URLs in its one .fullsend/config.yaml. Bootstrap
validates the branch, fetches refs/heads/<branch> once, detaches at FETCH_HEAD
and exports its observed SHA internally. That SHA is provenance for this job,
not a maintained consumer setting. No source commit/hash update is required
for subsequent fixes on the same branch.

## Validation

- Source full make test: 1,142 passed, six optional skips, 285.23 seconds.
- Source make lint: Ruff/type validation pass. An initial sandbox cache-lock
  restriction was rerun with approved cache access; a test line length was fixed.
- Pipeline suite: 79 passed, including actual local Git branch movement across
  two bootstraps, snapshot retention and invalid branch rejection.
- Source focused tests: 32 passed, including branch advances before runtime
  packaging/target checkout, registration mismatch and preserved consumer config.
- Actual published-source CI bootstrap and native Fullsend 0.47.1 single/batch
  locks pass, resolving three dependencies per agent and invoking no model.
  Receipt: /tmp/strat-minimal-consumer-r_n9c8yd/result.json and associated logs.
- Six GitLab CI compiler scenarios pass without warnings/errors. Scheduled
  jobs remain the legacy batch/dashboard; manual and publication graphs match
  their previous gates.
- Root/component diff checks pass and both component worktrees are clean.
  Credential comparisons find no real secret values. The scanner's private-key
  marker is the unchanged explicit SYNTHETIC-KEY-CONTENT fixture in an existing
  test; parent/current blob and added-line checks confirm no key was introduced.

No model run, Jira mutation, schedule change or merge. The two live-canary
functional bugs remain open and require separate repair/testing.

## Merge verified: 2026-10-21

After the user reported the merge, read-only GitLab checks confirm MR !16
merged at 16:45:16Z as fe9ca62abc9de57c66cb8ec9b5953fa1bd164fc9. Upstream
main is that commit and push CI 2972994099 passes. Both main's CI variables
and single/batch registration URLs follow feat/s1-workflow-hardening in the
user's strat-creator fork, without a maintained source SHA. PR #85 currently
points to 02dd13b, containing the media/publication fixes.

The six-hour legacy schedule is unchanged and the new Fullsend jobs remain
manual for web/API pipelines. No pipeline was launched. Next qualification
is a new live single-ticket canary; the earlier failed canary is unchanged.
Read-back receipt: /tmp/strat-mr16-postmerge-status.json.
