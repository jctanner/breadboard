# Bug: run locally, the behaviour harness acts as a person, so dispatch routes differently (BT-H7)

## Summary

In CI the suite acts as a GitHub App: `e2etest.TokenForOrg` mints an
org-wide installation token for the role `e2e` from the mint
(`internal/e2etest/auth.go`, `resolveE2EToken`). Run locally, which is the
path Breadboard's `run.sh` uses, it acts as the user behind `GH_TOKEN`. Here
that is the emulator's `admin`, a site admin and owner of every slot
repository.

Fullsend's dispatch routes on who acted. When the suite opens an issue,
`issues: opened` routes to triage if the author passes
`is_event_actor_authorized … triage` (`reusable-dispatch.yml`, around line
370):

- In CI the author is the e2e App's bot, which is not authorized, so nothing
  runs.
- Here the author is `admin`, who is authorized, so triage starts. The
  scenario never scripted a triage agent, so triage fails ("output/
  agent-result.json not found"), and the scenario's wait on the issue-open
  workflow fails with it.

Found in BT-B4 (`.ledger/plans/fullsend-behaviour-tests-plan.md`).

## Reproduction

`make bt-run FEATURES=features/dispatch/dispatch.feature`. Runs 1975, 1980
and 1997 (2026-11-07) routed `issues: opened` to triage and failed in
Triage.

## Expected

The harness acts as a bot identity, as in CI, so routing matches upstream.

## Actual

It acts as `admin`.

## Impact

At least 3 T2 scenarios fail outright: the issue-label and disabled-harness
scenarios in `dispatch.feature`, and the runtime.forge overlay scenario.
Routing for other events may differ as well.

## Options

1. Give the bb mint the `e2e` role, backed by an "e2e" App installed on the
   pool org with the permissions the suite needs (create and delete
   repositories, contents, issues, pull requests, Actions variables and
   workflows). Then set `GITHUB_ACTIONS=true`-equivalent behaviour for
   `TokenForOrg`. This would need a harness option, because the mint client
   uses Actions OIDC, which the host does not have.
2. Mint an installation token for such an App on the host, from the App's
   private key held by the emulator, and pass it as `GH_TOKEN`. The suite
   keeps one token per org for the whole run (upstream budgets 45 minutes),
   so a run longer than the token's lifetime needs a refresh.

## Related Tasks

- `.ledger/plans/fullsend-behaviour-tests-plan.md` (BT-B4)
