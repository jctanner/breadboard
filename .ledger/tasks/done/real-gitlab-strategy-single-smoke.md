# Real GitLab single-ticket strategy smoke

## Goal

Run one Opus 4.6 dry-run for RHAIRFE-3739 using the reviewed fork commit,
through the real agentic-ci GitLab runner, Podman, OpenShell and Fullsend,
using direct Vertex credentials. The user confirmed use of the upstream
project because the personal fork has no runners or secrets.

## Acceptance

- [x] Verify remote branch, runner and required GitLab secret access without
  printing or copying credentials unnecessarily.
- [x] Coordinate production discovery and check competing runs before making
  the synthetic ticket eligible.
- [x] Run tests/input checks, then start exactly one single-ticket dry-run
  with publication disabled.
- [x] Archive job metadata, logs and artifacts under `var/run-data/` and
  inspect the strategy, four review reports, business validation and cleanup.
- [x] Remove temporary eligibility labels and restore any schedules we pause.

User authorized this sequence after reviewing its steps. No live Jira strategy
creation or downstream publication is included. Preserve uncertain API writes
for reconciliation rather than retrying blindly.

## Execution

- Reviewed consumer commit: `6f996e2e424c5238af0520c8b5235e5ea8c95e6a`;
  source remains `080700e4b1b23eea9f2ffc30a32684f806dd9472`.
- Created exact-commit upstream branch
  `smoke/fullsend-single-rhairfe-3739-20261020`. Protected only this branch
  (maintainer push, no merge, no force push), allowing protected CI variables
  without copying them or changing main.
- [Pipeline 2969078190](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/pipelines/2969078190),
  API source, explicit single/RHAIRFE-3739/dry-run=1/publish=0.
- Runner `48079670`, tag `aipcc-small-x86_64`, online. Both input validation
  and all 69 repository tests pass on this actual runner.
- Inherited group-variable metadata returns 403; actual credential presence
  remains to be verified by job preflight before model invocation.
- Archive: `var/run-data/20261020-real-gitlab-strat-single-opus46-smoke/`.
  Preflight, exact branch/protection, pipeline variables/receipt and CI traces
  saved. No raw credential values in the task or console.

### Production coordination adjustment

The attempt to pause schedule 4222905 returned HTTP 403. Read-back confirms it
remains active and the synthetic ticket remains unqualified. No ownership
takeover or change to production main was attempted.

Instead, signed-off smoke-only commit
`f5dfb0e32cf73d4cf9cd70bca7f91c12e3dd5072` adds a small fixture helper and
job qualification/cleanup on the temporary upstream branch. Source and the
fork/MR are unchanged. The single job owns the existing `strat-batch` resource
group before qualifying this exact ticket. Its after-script removes only its
three labels (two qualifiers and a job owner marker) before releasing the
resource group. Script timeout leaves room for after-script cleanup.

The helper checks required credential presence before any ticket mutation;
labels are never set by the workstation. Four model-free contract checks cover
missing credentials, an uncertain committed Jira write without retry,
preservation of concurrent labels and idempotent cleanup. All 69 repository
tests, compilation, credential scan and GitLab CI lint pass. First pipeline
2969078190 was canceled with its model job never started. A replacement checks
the temporary wrapper before the sole authorized model attempt.

Replacement [pipeline 2969118303](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/pipelines/2969118303)
passes both input validation and repository tests on the agentic-ci runner.
Played [job 17328210051](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/jobs/17328210051)
once on 2026-10-20. Initially waiting for the shared resource group;
credential preflight, model execution and result checks remain pending.

### First real-runner attempt and environment repair

Job 17328210051 ran 20:08:25–20:15:58 UTC and failed before host run/model
execution: Fullsend 0.47.1 requires `FULLSEND_GITLAB_ANALYST_TOKEN` for GitLab
runtime routing, despite this agent doing its strategy work in Jira. The exact
release's source/docs confirm the requirement; no shared/user-token fallback.
Jira, direct Vertex, live context fetch, sandbox build and gateway setup passed.
All 17 archived paths include source/context receipts and independent gateway
and fixture cleanup confirmations. RHAIRFE-3739 reverted to its neutral labels.
No strategy/model transcript exists from this setup failure.

Created temporary project-scoped Developer/API token 28638973, expires
2026-10-21, as a masked/hidden/protected variable. The raw token exists only
in GitLab's secret store; the personal management token was not passed to CI.
Hidden-variable read-back is opaque, so verified protected metadata and our
new token ID instead of comparing the unreadable value.

Retried only the failed job, now
[17329828389](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/jobs/17329828389),
which started at 20:41:56 UTC and passed Jira/Vertex/fixture checks. The source,
model, iteration count and dry-run/publication settings are unchanged.
The monitor archives results, verifies cleanup and revokes/removes the temporary
credential on terminal status. Revocation remains pending while the job runs.

[Maintained preflight/documentation gap](../../bugs/fixed/strat-fullsend-gitlab-role-preflight.md)
is recorded separately; provisioning this one test secret does not fix it.

### Active model execution

At 20:49:45 UTC the host pre-script selected exactly RHAIRFE-3739:create.
Sandbox bootstrap/scans passed; Claude Code 2.1.296 / Opus 4.6 started at
20:50:15 UTC and launched `strat-pipeline:strat-pipeline` at 20:50:22.
Regular Fullsend heartbeats continue with no reported error. This is the
first actual model attempt; final outcome is not yet known.

The active controller is `/tmp/strat-real-smoke.py watch`, unified exec session
`15760`. It polls the latest job, refreshes the archived trace, then downloads
all attempt logs/artifacts and verifies fixture/schedule restoration before
revoking token 28638973 and removing its temporary CI variable. Receipts are
under the archive root. Inspect `watch-finished.json`, `status.json`,
`temporary-analyst-revoked.json` and the final artifacts before declaring success.
The watcher explicitly leaves content/result review for the next inspection.

Static audit also identified a possible artifact coverage gap: post-script
handoff/results are assembled under private `.fullsend-state/.../publish`,
while CI uploads `fullsend-output/`. Native outputs/transcripts are retained,
but check whether standalone strategy/review documents are in the final ZIP;
do not claim full document archival without inspecting it.

## Final result: functional smoke passed, with operational follow-ups

Pipeline 2969118303 and job 17329828389 succeeded. The job ran
20:41:56–21:06:55 UTC: **24m58s** total. Actual agent execution was
**15m45s**; setup before the agent was about **8m17s**. Exactly one model
iteration ran with Opus 4.6/high, source 080700e and Claude 2.1.296 on the real
agentic-ci runner, Podman, OpenShell and direct Vertex.

The host run and structured result agree on one fresh input, RHAIRFE-3739,
and one local dry-run strategy, STRAT-3739. All create/refine/push/review phases
are recorded; the push is intentionally a dry-run. No skips or business
errors. Numeric score **8/8**, approve, needs_attention=false. The trusted host
checker prints `PASS: result matches the run record, progress, artifacts and
scores`; native post-script handoff completed. This is stronger evidence than
the green job alone.

Reviewed the actual refinement edit, four specialist assessment transcripts
(feasibility, testability, scope, architecture) and numeric scorer output.
The feasibility assessment questions the frontend/component choice while the
architecture assessment and scorer support it. Approval follows the user's
numeric-only gate; this smoke does not independently adjudicate that content
disagreement. Three HIGH Tirith findings record blocked commands (nested
command analysis and a Python pipeline); they did not stop completion.

Model-reported cost is **$5.836762**, not an invoice. Metrics record input 152,
cache creation 472,496, cache read 3,767,504 and output 39,966 tokens: 4,280,118
combined. Reasoning is separately reported as 9,944 and not added again.
`per_model_usage.requests=0` contradicts the confirmed inference activity and
cannot be used to count requests here. One iteration is recorded.

The final ZIP passes its integrity check: 40 files, 4,788,023 uncompressed bytes.
It includes transcripts, debug/security/gateway logs and native result/metrics,
but **no standalone strategy/review documents**. The private post-script
handoff was not uploaded. Saved six clearly labeled transcript excerpts and
`review/verification.json`; these are not canonical final-file snapshots.
[Required business-artifact export fix](../../bugs/open/strat-fullsend-ci-business-artifact-export.md).

Independent final receipts confirm both run/release exits zero, gateway
command/cleanup exits zero, the ticket's two neutral labels restored, Target
Version unset and no linked STRAT. Schedule 4222905 remains enabled with its
original cron/ref/timezone. Temporary token 28638973 is revoked and its CI
variable removed. Watcher session 15760 completed normally.

This validates the real runner integration **in dry-run mode**. Live Jira
strategy writes, publication, Org Pulse and the downstream dashboard remain
outside this test. Maintained role-secret preflight/docs and business-output
export remain separate tracked follow-ups; no further paid run was launched.
