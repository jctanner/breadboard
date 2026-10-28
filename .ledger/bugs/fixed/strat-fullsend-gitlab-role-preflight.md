# Fullsend GitLab trial omits required Analyst credential from preflight/docs

## Evidence

Real agentic-ci pipeline 2969118303, job 17328210051, on 2026-10-20 reached
Fullsend 0.47.1 after Jira/Vertex credential checks, sandbox image build and
gateway start. It failed with:

```text
GitLab role credential is not provisioned: role "analyst": secret FULLSEND_GITLAB_ANALYST_TOKEN
```

The exact release's `internal/cli/gitlab_role.go`, `internal/gitlabroles/`
and `docs/contributing/gitlab-role-credentials.md` require the registered
per-role credential in GitLab CI. Shared/user-token fallback is intentionally
unsupported. Triage routes to Analyst. This failure precedes model execution;
there are no strategy reports, transcripts or host run manifest in the archive.

The job ran 20:08:25–20:15:58 UTC, mostly environment preparation. Both
input-validation and all 69 repository tests had passed. Gateway/fixture
cleanup succeeded, and RHAIRFE-3739's two neutral labels were restored.

## Gap and follow-up

The consumer README omits this required secret; reusable setup checks it only
when Fullsend resolves credentials after the image/gateway preparation.
Document provisioned `FULLSEND_GITLAB_ANALYST_TOKEN` and fail before expensive
preparation when it is absent. Keep the intended registered role; do not
silently substitute the operator's personal token or weaken Fullsend routing.

## Immediate smoke mitigation

Created a temporary Developer/API project access token, expires 2026-10-21,
as a masked, hidden, protected project variable. The personal API token
remains outside the job. GitLab returns opaque hidden-variable read-back;
verify metadata and the new token ID rather than comparing the unreadable
value. Revoke the temporary token and remove its variable after the smoke.

[Execution task](../../tasks/done/real-gitlab-strategy-single-smoke.md)
contains the exact source, CI fixture and archive references. This bug remains
open for a maintained preflight/documentation fix; a provisioned test secret
alone does not repair that omission.

The authorized retry passed with one real model iteration. The temporary
credential was then revoked and its CI variable removed; cleanup receipts
are archived. A maintained deployment still needs a provisioned role secret.

## Comparison with gitlab.local

The local Workflow smoke used the same released Fullsend 0.47.1 and already
received the Analyst credential. Archived pipeline 2100/job 4068 trace line 89
at 2026-10-19T02:13:35 UTC explicitly records:

```text
GitLab identity role=analyst kind=builtin source=role secret=FULLSEND_GITLAB_ANALYST_TOKEN
```

Evidence:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2100/20261019T023624.716768Z/gitlab/jobs/4068/trace.log`.
The launcher does not substitute a different token or disable GitLab routing.
The local credential was already supplied, so its absence was not exercised.
The real GitLab project had neither the Analyst variable nor a project access
token before this smoke. This is a missed deployment prerequisite in the
real-GitLab adaptation/docs, not a new Fullsend-version requirement or evidence
that the earlier local tests failed.

## Reference rfe-autofixer comparison

Read the real GitLab project's current main on 2026-10-20, commit
`efc285d7b3f69a8aac668e03adb81fdb0026b536` (project 80884610).
`autofix-rfe-stage-dry-fullsend` still downloads Fullsend **0.43.0** at CI
line 194. The CI definition has no per-role secret references. The exact
0.43.0 runtime source predates the mandatory registered-role selection used
in 0.47.1; it documents the older generic GitLab-token setup instead.

Therefore its current pin does not hit this specific newer startup check.
An upgrade to 0.47.1 needs the matching role credential provisioned; group
secret presence was not audited. The ten Fullsend jobs in the latest 100
job records were all manual/unstarted, so this inspection does not establish
recent runtime success or failure. No autofixer job was launched or changed.

The reference's CI layout was reused while the strategy path deliberately
uses newer Fullsend. Matching that layout did not establish credential parity
across those releases.

## Presence versus validity: correction

Further inspection of the exact 0.47.1 implementation shows the startup
selection check verifies only nonempty, whitespace-trimmed presence.
`internal/gitlabroles/route.go:125` (`Selection.Token`) returns any nonempty
string without format validation or an authentication request.
`applyGitLabRoleSelection` exports it as GITLAB_TOKEN and clears PUSH_TOKEN
for Analyst. Therefore the earlier categorical statement that startup
requires a *valid* credential was too strong: an invalid nonempty string
passes this selection check.

Actual GitLab requests would authenticate with that string and be rejected.
Failure handling is operation-specific: run.go's status notifier warns on
setup/post failures, while required forge work can fail. In this launcher,
status notifications are conditional on explicit status repository/issue
inputs, and the strategy's actual work targets Jira. It is plausible that a
nonempty placeholder remains unused for this workload. The complete run with
an invalid value has **not** been tested; no placeholder has been installed
or another model run launched. Do not turn a source-level presence check
into a claim that a live token is operationally necessary for Jira-only work.

## Fixed: explicitly reuse the results credential

On 2026-10-20 the user chose to reuse the existing `RESULTS_PUSH_TOKEN`
rather than provision a separate credential, accepting a later permissions
fix if required in production. Consumer commit `d27a314`, pushed to MR !15's
existing feature branch, explicitly exports it as
`FULLSEND_GITLAB_ANALYST_TOKEN` in the first CI setup block. The check rejects
missing/empty/whitespace-only values before bootstrap, and shell tracing is
disabled before assignment. The registered Analyst selection remains intact;
the operator's personal management credential is not substituted.

README documents that the token is required even with publication disabled,
that its actual data-repository write permissions accompany it, and that
pull/push access does not prove GitLab API access to the pipeline project.
The full pipeline suite passes 74 tests, including model-free child-process
inheritance/redaction and missing-value checks. No further inference or live
authentication test was run. Production use of this mapping remains pending
deployment; the preflight/documentation omission itself is fixed.
[Implementation task](../../tasks/done/strat-fullsend-reuse-results-credential.md).
