# Bug: emulator GraphQL createPullRequest rejects headRepositoryId (BT-E5)

## Summary

The behaviour suite opens a fork pull request with the GraphQL
`createPullRequest` mutation and passes `headRepositoryId`, the fork. That is
how GitHub creates a cross-repository pull request. The emulator's
`CreatePullRequestInput` has no such field and rejects the whole mutation.

Found in BT-B4 (`.ledger/plans/fullsend-behaviour-tests-plan.md`).

## Reproduction

`make bt-run FEATURES=features/dispatch/fork-dispatch.feature`. Every
scenario fails at "creating fork pull request":

```text
create cross-repo pull request: graphql: Variable '$input' has invalid value:
Expected value of type 'CreatePullRequestInput' not to include unknown field
'headRepositoryId'. Did you mean 'repositoryId'?
```

## Expected

As on GitHub: `CreatePullRequestInput.headRepositoryId` names the repository
that holds `headRefName`. The pull request's head is that fork's branch, and
its base is `repositoryId`'s `baseRefName`.

## Actual

The mutation is rejected before it runs.

## Impact

High for T2. All five fork scenarios fail on it: four in
`fork-dispatch.feature` and one in `fork-bash-routing.feature`. They are the
coverage for fork-PR dispatch and the fork kill switch.

## Related Tasks

- `.ledger/plans/fullsend-behaviour-tests-plan.md` (BT-B4)
- Fix belongs in `checkouts/github-emulator`
