# Reconcile strategy agents with the merged onboarding config

## Goal

After the user merged onboarding PR 86, update our feature branch from upstream
main and extend its committed config, preserving onboarding behavior. Do not
merge an unmerged onboarding feature branch or recreate a separate config.

## Acceptance

- [x] Confirm onboarding merged and bring upstream main into the feature branch.
- [x] Preserve runtime, roles, generic agents, issue targets and notifications.
- [x] Add three strategy registrations and required remote-resource allowlist.
- [x] Correct README/example/ignore guidance and check the real config in tests.
- [x] Run full source tests and native model-free configuration controls.
- [x] Publish the source update and refresh the GitLab consumer's source pin.
- [x] Preserve the consumer's one-file layout and record verification.

No paid strategy runs, Jira writes or production schedule changes are authorized.
Use existing feature branches and signed-off commits; no history rewrite.

## Completed: 2026-10-20

The user's PR 86 merge appears on main as 9c87d8373830a4a7588b42af7845fa61543e7625.
Merged upstream main into the feature branch, then extended its committed
config. No unmerged onboarding branch was incorporated. All six generic agents
and every other original setting compare equal after filtering the three new
strategy registrations and allowlist; both inherited workflow files compare
byte-for-byte. Corrected stale docs/example/ignore guidance and PR 85's body.

Published signed-off source merge 8b2f1e0ae453a67a6518ba989d3816aeba991e1f;
upstream main is its second parent. Lint initially exposed two adjacent imports
in an earlier pull-test change; combined them and full make lint passes, including
type validation. Full make test: 1,118 passed, six optional skips in 279.25s.
Native Fullsend harness/dispatch suite: all twelve cases pass using the real
combined config, including five previously optional event checks. Native locks
resolve strat-single, strat-batch and strat-resume. Evidence is under
`/tmp/strat-onboarding-reconcile-evidence.json` and the native directory recorded
in `/tmp/strat-onboarding-native-path.txt`.

Published signed-off consumer 0825ea430f0c07f5639c323564f1f0db6d6603f3, changing
only the source pin and matching registration URLs. Full pipeline suite:
69 passed in 14.29s. Actual bootstrap against published 8b2f1e0 and native locks
pass; evidence is `/tmp/strat-minimal-consumer-53b9ph6g/result.json`. Previous
85e5cb3 receipt is retained separately under `/tmp/strat-minimal-ci-validation-85e5cb3-result.json`.
Published GitLab CI lint passes without warnings/errors, selecting python-tests
on a default push. Both PR/MR descriptions and remote source heads are verified;
both component checkouts are clean. All test execution was model-free.

Final MR read-back confirms successful GitLab pipeline 2968225182 on 0825ea4,
with no merge conflicts and the expected upstream main target.

[Source PR 85](https://github.com/fullsend-ai/strat-creator/pull/85) and
[pipeline MR 15](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/15)
remain draft for the previously recorded deployment qualifications. The
[registration guidance bug](../../bugs/fixed/strat-creator-onboarding-registration-guidance.md)
is fixed on the published feature branch.
