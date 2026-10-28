# Strategy onboarding guidance follows a superseded review comment

## Finding: 2026-10-20

PR 85 at 85e5cb3 removes/ignores `.fullsend/config.yaml` and instructs deployments
to regenerate it from an external fleet. That follows the reviewer's initial
[comment](https://github.com/fullsend-ai/strat-creator/pull/85#issuecomment-6219344774),
but his later [correction](https://github.com/fullsend-ai/strat-creator/pull/85#issuecomment-6220196013)
says this repository will not be reinstalled and the committed onboarding config
should be retained, combining its runtime/roles/generic agents/status settings
with the three strategy sources and allowed remote resources.

Onboarding PR 86 at 03305e0 adds that config and two workflows. Native Git
merge-tree of the current heads succeeds, with zero overlapping changed paths.
The merged tree preserves the onboarding config and all three strategy
harnesses, but the config registers only code/fix/prioritize/review/retro/triage.
Strategy registrations and the allowlist are absent.

## Follow-up

Align `.fullsend/README.md`, `fleet-entry.example.yaml` and the ignore guidance
with the corrected onboarding contract. Coordinate/prepare the combined
committed repository config preserving the onboarding settings and adding
strat-single, strat-batch, strat-resume and the required resource allowlist.
Do not infer a registered strategy deployment from a conflict-free Git merge.

The GitLab pipeline consumer has its own single/batch registrations and does
not rely on this repository onboarding config. No component or remote changes
were made during this assessment; no model calls or actual merge performed.

Related: [GitLab integration plan](../../plans/strat-pipeline-gitlab-fullsend.md).

## Resolution: 2026-10-20

After the user merged PR 86, fetched upstream main 9c87d83 and merged that main
commit into our feature branch. Published signed-off merge commit 8b2f1e0 in
PR 85. Its config extends the inherited file with three strategy registrations
and the resource allowlist. YAML comparison verifies every original runtime,
role, generic-agent, issue-target and notification setting is preserved; both
onboarding workflow files are byte-identical to upstream.

README, example fragment, ignore guidance and PR body now follow the corrected
committed-config contract. The harness tests read that actual combined config.
Full lint/type checks pass (including a prior pull-test import formatting fix),
the full suite passes 1,118 tests with six optional skips, and native Fullsend
passes all twelve harness/dispatch cases plus locks for all three strategies.

The GitLab consumer now references 8b2f1e0 through signed-off 0825ea4 in MR 15;
it still maintains only one Fullsend registration file. Its 69 tests, real
bootstrap/native locks and published CI lint pass. No paid strategy run or
production Jira write was launched. Both component checkouts are clean.
