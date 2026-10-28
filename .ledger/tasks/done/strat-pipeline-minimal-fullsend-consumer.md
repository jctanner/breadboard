# Minimize the strategy pipeline's Fullsend files

## Goal

Follow rfe-autofixer's consumer layout: keep only `.fullsend/config.yaml` in
the pipeline's `.fullsend` directory and keep reusable strategy/runtime
implementation with strat-creator. Reduce additional pipeline files where
practical without losing the existing validation and cleanup behavior.

## Acceptance

- [x] Verify direct remote harness resolution with pinned Fullsend 0.47.1.
- [x] Move reusable integration code/settings/tests into strat-creator.
- [x] Pipeline keeps agent registration and GitLab/operator configuration.
- [x] Preserve direct Vertex, current architecture HEAD, manual execution,
  one validation iteration, owned cleanup and redacted artifacts.
- [x] Run relevant model-free checks and record any deployment limitations.
- [x] Update the existing feature branches/MR after full required checks.

## Constraints

No paid inference or production writes. Use existing feature branches and
retain the legacy jobs/schedule. Read component instructions before editing.
The user's goal is fewer source files in the pipeline, not removal of guards.

## Completed: 2026-10-20

Pipeline final diff is five files instead of fifteen. Only `.fullsend/config.yaml`
is new; jobs, guide and CI contracts use existing files. Six reusable integration
files and their helper/failure tests moved into strat-creator. Both feature
branches are committed/pushed, with clean component checkouts:

- Strat-creator signed-off 85e5cb3 in [PR 85](https://github.com/fullsend-ai/strat-creator/pull/85).
- Pipeline signed-off d123c19 in [MR 15](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/15).

GitLab MR pipeline 2967970795 succeeds on d123c19 (model-free tests).
Remote read-back confirms both expected feature heads and the draft MR target.

Native Fullsend 0.47.1 initially fails a registration-only lock because the
plugin directory is missing locally. Shared setup now materializes verified
companions in private runtime state and keeps the remote registrations unchanged.
The actual GitLab bootstrap against published 85e5cb3 passes, and native locks
both agents with three remote dependencies each. Consumer source still contains
only config.yaml. Evidence: `/tmp/strat-minimal-ci-validation-85e5cb3-result.json` and
its referenced isolated directory/logs. The temporary driver initially repeated
a dict keyword; corrected before the successful integration check.

Pipeline full suite: 69 passed; after source-pin updates, all 30 CI configuration
checks pass. Strat-creator full suite: 1,118 passed, six optional skips in 281.96s.
Ruff, shell syntax and diff checks pass. Six GitLab compiler graph variants
pass without warnings/errors, including unchanged scheduled behavior.
Local credential/private-key comparisons find no leaked values.

No model calls or production writes. Real runner/image/OpenShell/Vertex smoke
and reviewed upstream source selection remain qualification gates; both PRs
remain draft. [Implementation/evidence](../../plans/strat-pipeline-gitlab-fullsend.md).
