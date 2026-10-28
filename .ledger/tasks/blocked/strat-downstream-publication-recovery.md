# Complete Org Pulse and dashboard delivery without another model run

## Authorization

The user authorized both remaining tasks: retry Org Pulse publication from
saved results using the temporary TLS exception, and repair the dashboard's
data-repository credential then rebuild it. A subsequent interruption happened
before tools or mutations; this resumed turn begins with inspection. No model
run, Jira edit, production executor cutover or schedule change is included.

## Acceptance

- [x] Inspect current upstream state and credential metadata without exposing secrets.
- [x] Reuse verified saved RHAISTRAT-3038 content, avoiding stale aggregate replay.
- [x] Publish and read back Org Pulse numeric approval and specialist dissent.
- [x] Diagnose dashboard Git authentication and test the permanent credential fix.
- [x] Run only downstream builds and verify generated HTML and JSON artifacts.
- [x] Archive receipts/traces/artifacts and record remaining limits.
- [ ] Land the dashboard fix on main after required MR approval.

## Baseline

Source 85e8307 implements the user-approved temporary certificate exception;
1,190 tests/six skips and lint pass. Original strategy smoke 2974269929/
17366396650 passed business validation and Jira/data-repo publication, but
Org Pulse failed TLS and dashboard 2974334519/17366831288 failed data-repo
authentication. Preserve that original failed-downstream record. Use a new
archive: var/run-data/20261022-strat-downstream-publication-recovery/.

## Inspection and launches

The interruption preceded remote work. New preflight confirms source 85e8307.
Current main data summary omits RHAISTRAT-3038 after subsequent legacy scheduled
runs; its immutable publication seal still matches the saved run exactly.
Original artifacts/payload verify. Replay selects this one strategy only and
checks its expected payload hash, rather than reposting an old 1,031-entry
aggregate over newer data.

The local host cannot resolve the internal Org Pulse endpoint. The real CI
runner can reach it, so created an isolated API-only recovery branch/job with
no model jobs. Pipeline 2976666017 on strat-pipeline, branch
smoke/downstream-org-pulse-recovery-20261022, commit b71602c. It checks the
sealed files, uses the current versioned exporter, publishes once and reads
back the numeric gate and dissent. Saved intent prevents blind relaunch.

jtanner1 has Developer (30) on strat-dashboard; project/group variable APIs
return 403. The pipeline's existing RESULTS_PUSH_TOKEN successfully reads the
data repository, but does not grant dashboard administration. Asked the user
for Maintainer access or maintainer-side replacement of DATA_REPO_TOKEN. The
user asked what was wrong with it; explained that Git authentication is
rejected, while precise missing/expiry/scope cause remains undetermined.

In parallel, launched only dashboard recovery pipeline 2976679109, isolated
branch smoke/strat-downstream-recovery-20261022 at 32d4431. It tests the original
credential without exposing values, applies a temporary known-working override,
and uses the hardened reader from feat/s1-workflow-hardening. Current main's
reader can omit identified directories. Neither existing main branch, permanent
project variable nor legacy schedule was edited. Permanent credential repair
still needs the requested access or maintainer action. No model call/Jira write.

## Recovery checks passed; permanent dashboard fix under validation

Org Pulse pipeline 2976666017/job 17383298312 passes in about 43 seconds.
Before GET 404, one POST creates one feature with no validation errors, after
GET 200. Numeric 8/8 approval, feasibility revise and other approve verdicts,
source RFE and original run identity match the sealed saved payload. No model
call, direct Jira write or aggregate-wide replay.

Dashboard pipeline 2976679109/job 17383395165 succeeds with the temporary
credential. CI diagnostic confirms the existing DATA_REPO_TOKEN is present,
different from the replacement, and fails actual Git read; the replacement
passes. Its HTML includes the smoke but copied summary JSON is stale because
legacy scheduled readers omit identified runs. Added local summary regeneration
and reran only Pages: pipeline 2976847572/job 17384767676 passes. HTML, run JSON
and summary JSON all include RHAISTRAT-3038/run-gitlab-job-17366396650.

The same runner also proves CI_JOB_TOKEN can read the data repository. This
avoids needing a static replacement or project-variable admin access. Prepared
a production-ready one-file dashboard feature branch using process-scoped Git
auth with CI_JOB_TOKEN (no secret URL/config), regenerating summary JSON with
the same reader as HTML, exposing CREATOR_BRANCH defaulting to main, and
allowing API builds. It retains existing defaults/Pages content; no main merge
or executor cutover. Validate this exact branch without any credential override
before opening a merge request. Remote AGENTS.md and CLAUDE.md are absent.

## Exact fix validated; awaiting required approval

[Dashboard MR !7](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-dashboard/-/merge_requests/7)
is open/ready, branch fix/ci-job-token-dashboard-summary, commit
6a9085d57f903646a122e0420ae092426872115f. One file changes. The exact branch
passes [pipeline 2976991608](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-dashboard/-/pipelines/2976991608),
Pages job 17385905560, with no credential override. Clone authenticates using
only its native CI_JOB_TOKEN. HTML, individual run JSON and regenerated summary
JSON contain the smoke strategy/run, score eight and feasibility dissent.
CI lint, YAML and embedded-Python compile checks pass. No static secret needs
replacement to adopt this solution.

MR API reports merge_status=can_be_merged but detailed_merge_status=not_approved.
Main is protected. Required review approval is pending; no merge or bypass was
attempted. The task is blocked only on landing that permanent dashboard fix.
The user need not grant project-variable administration for this job-token
approach. Source/branch defaults remain upstream main; the opt-in smoke
selects the hardened fork/branch explicitly. Default identified-run support
also depends on landing strat-creator PR #85. No strategy executor cutover.

All three diagnostic/final dashboard builds and the one scoped Org Pulse replay
are retained separately. No extra Org Pulse POST occurred while reading or
archiving evidence. The final dashboard build/pipeline succeeds and its GitLab
Pages artifacts are verified. Live browser/Pages URL readback is not claimed:
Pages management metadata returns 403 with this Developer account.

Legacy schedule 4222905 is unchanged, current main/data-repo settings and Jira
work untouched. No production cutover or model inference; extra model token
spend is zero. Original smoke and temporary-TLS archives remain unchanged.

Final archive verification completed: **72 files plus SHA-256 manifest**, ZIP
CRC checks and 1,326 contained-file credential scans pass, zero configured-secret
findings. verification.json records Org Pulse recovery, exact dashboard build
proof, unchanged schedule and pending main merge. Root diff check passes.
