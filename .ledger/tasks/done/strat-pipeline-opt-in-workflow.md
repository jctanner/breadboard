# Preserve stable jobs and make the Workflow opt-in

Owner requested 2026-10-26: revise the existing GitLab pipeline MR so merging
does not cut over execution. Checkout checkouts.tmp/jtanner1/strat-pipeline,
branch feat/fullsend-workflow-cutover, starting c514513. Upstream main fetched
and unchanged at 9bbac1e; checkout clean. No local AGENTS.md/CLAUDE.md found.

Verified upstream fullsend-ai/strat-creator refs: stable-1.x and tag 1.0.0 both
resolve to bb4887bc397eee9610ef4170b56a4c7cf8eef295. The user's stabel spelling
was a typo; use the actual stable-1.x branch, not a commit pin.

## Implementation

- Preserve the four legacy names, shell/Python bodies, cleanup, timeouts and
  normal selector behavior from upstream main. Pin their clone to stable-1.x
  with a legacy-only CLAUDE_BRANCH variable and existing CLAUDE_REPO.
- Add workflow-batch-jql, workflow-batch-config, workflow-single-rfe and
  workflow-reprocess-strat using the existing Fullsend base and upstream main.
  Existing STRAT_CREATOR_REPO/BRANCH and three remote registrations remain.
- Reuse STRAT_EXECUTOR: legacy default, fullsend opt-in. Mutually exclusive
  family rules; invalid values fail model-free validation. Preserve model-free
  push/MR pipelines, all four operations, shared strat-batch queue and unqueued
  single/reprocess jobs. Do not create two dashboard triggers.
- Existing legacy GCP/Jira credentials remain; Workflow uses the already
  configured direct-Vertex/provided-secrets interface. No model-relay and no
  architecture-context pin. No source/runtime implementation copied into the
  consumer repo.
- Document switching/rollback for future pipelines; keep Workflow prerequisites
  separate from merging this consumer MR. No CI variable/schedule changes or
  model/live Jira run is authorized by this edit.

## Checks

- [x] Test both families, all triggers/selectors, invalid mode, dry publication,
  shared queue, stable branch clone and unchanged Workflow bootstrap.
- [x] Verify preserved legacy scripts against fetched upstream baseline.
- [x] Full consumer suite, shell syntax, diff checks and GitLab CI lint.
- [x] Credential scan, evidence archive, signed-off commit and normal branch push.

Existing MR: https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/18.
Do not launch a pipeline, change project/schedule variables, merge, or post comments.

134 tests pass (14.62s), 50 shell steps parse, original job bodies/defaults/cleanup
match upstream. GitLab lint valid with no warnings/errors. Project and active
six-hour schedule have no executor override; settings untouched. Workflow
registrations package from a local tested-source snapshot; no model/live Jira
run. MR title/description will be updated to the final rollout scope, preserving
the existing author signoff. Details:
[notes/evidence](../../notes/strat-pipeline-opt-in-workflow-20261026.md).

Signed-off e8f3959f03d5df385a9ed2337c0ecd4d54ed4987 pushed normally to the
existing MR !18 branch. Four files; credential scans zero findings. Twenty-file
evidence archive/hash readback verified, with a separate sealed publication
receipt. Git and GitLab read back the exact head, component clean. MR title and
description now describe the opt-in rollout, retaining author signoff. GitLab
trimmed one final newline; read-only verification confirmed all text matches,
without a second metadata mutation. New-head MR pipeline 2992428660 succeeded.
No comment, runtime-variable/schedule change, manual pipeline, model job or merge.
