# Task: Fetch architecture context visibly before agents start

## Goal

Expose architecture fetch stdout/stderr and exit status in CI without relying on
an agent's summary of a failed fetch.

## Implementation

Entrypoint runs native fetch from project root before telemetry/locks/Claude,
with a180-second timeout. Tee combined stdout/stderr directly to console and
output/architecture-context-fetch.log; retain exit code separately. Fetch
failure remains optional as in current skills, while log-storage failure is fatal.
Native curl now reports HTTP failures and propagates their status before JSON
parsing, with connect/request timeouts. Skills may still retry their native fetch.
This improves evidence; it does not claim to fix the403 or skipped-review schema.

## Acceptance

- [x] Real entrypoint regressions cover output/artifacts and optional failure.
- [x] Full suite, Bash syntax and diff checks pass.
- [x] Source/pins published without a new model job.

## Status

Done. Existing job4017 untouched.

## Verification and publication

Source43a6457f599062427f6c0283babb32d231e0dee4 pushed. Final full suite795
passed/1 skipped (112.97s); Bash syntax and root/component diff checks passed.
Regression verifies combined stdout/stderr artifacts and statuses0/22, continued
workflow on optional failure, and native curl403 exits22 without a JSON traceback.
Native fetch now uses set -eo pipefail to propagate Git failures as well.
Normal CI commit86e6cbde4a2cd8bd2126f0d5d28f1f710bbde1c2; diagnostic commit
8a193a11528e2775c532e1f60bb8bfbf2a8586aa. Both publish-only; native main unchanged.
No new diagnostic/model/batch execution; remote403 cause still unverified.
Skills can perform later fetch attempts under their existing instructions.

## Live evidence: pipeline2067/job4021 (2026-10-07)

Initial fetch now exposes the failure directly: at12:22:19Z it reached Git
clone of .context/architecture-context, then HTTP403/RPC failure and "expected
flush after ref listing". Exit128 retained and optional-context warning printed.
The GitHub API architecture listing succeeded sufficiently to reach clone;
the failing operation is Git transport, not initial API discovery. Exact source
of403 (upstream or sandbox policy/gateway) remains unverified. Job still running.
Trace had zero workspace-trust warnings at inspection.

## Root cause found (2026-10-07)

The 403 is OpenShell's sandbox L7 policy. `github.com` had the `read-only`
preset (GET/HEAD/OPTIONS), which denied Git's `POST git-upload-pack`. The
sandbox decision log from job 4021 shows it. Fixed in strat-creator `3fd1563`;
see [bug](../../bugs/fixed/fullsend-sandbox-architecture-context-git-fetch-denied.md).
Job 4021 finished `success` (1044 s) without architecture context.
