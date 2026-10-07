# Task: Consolidate GitLab CI capabilities into one runner

## Goal

Deliver one maintained runner for `gitlab.local` with ordinary CI, native
strategy, nested Podman, and job-owned OpenShell capabilities. Follow step 7
of the [POC plan](../../plans/fullsend-entrypoint-strategy-poc.md).
Depends on the Podman and OpenShell validation results.

## Acceptance criteria

- [x] Fold validated settings into the authoritative runner deployment script/manifests.
- [x] Preserve required tags and untagged-job behavior; document job-image requirements.
- [x] Validate ordinary CI, native strategy CI, Podman, and OpenShell on the same runner.
- [x] Confirm concurrent jobs have separate runtime storage and gateway state.
- [x] Remove temporary runner registrations, deployments, and secrets after draining work.
- [x] Deployment and emulator reset leave exactly one runner registration/deployment.
- [x] Record job assignment evidence and maintenance/rollback instructions.

## Status

Complete on 2026-10-06. Authoritative configuration, registration convergence,
capability matrix, concurrent isolation, repeat deployment and live runner-only
registration reset passed. Reset scope and remaining reliability limitations
are recorded below; M6 issue/results evidence was preserved.

## Implementation and validation — 2026-10-06

Authoritative runner deployment now carries privileged=true, concurrent=4,
job-local emptyDirs at /var/lib/containers and /run/containers, verified local
CA, Recreate manager strategy, existing tags and run_untagged=false. New
registration/lifecycle helpers pause and drain assigned work, refuse busy
reset/reconciliation, reuse the maintained token and remove duplicate
registrations and obsolete experiment resources. Deployment and clean-all
share these helpers. Fixture --enable-runner delegates to deployment.

Live registration-only reset via clean-all --gitlab-runner-only emptied the
emulator runner registry, invalidated stale configuration, and recreated
exactly one registration/manager. Service data was preserved. A deliberately
added paused duplicate (ID 2) was removed by redeployment, keeping maintained
ID 1. Both tags remain; untagged jobs remain ineligible. The full clean-all
PVC-wipe control flow passed a mocked-kubectl check (drain before empty DB,
then reconcile/resume one runner). **The live test did not wipe every service
PVC**; its reset scope was the actual emulator runner registrations.

Capability matrix **2042**, source branch feat/fullsend-runner-validation
commit `499d3a41bc766b4b6b0cb4d84440241c9ef7dfd2`:

| Job | Result | Evidence |
| --- | --- | --- |
| 3967 build-fullsend-feature | success | Pinned public strategy fork and Fullsend feature build |
| 3968 ordinary-ci | success | Alpine job, k8s-incluster tag, artifact upload |
| 3969 native-strategy-readonly | success | Real UBI native setup, Claude 2.1.292, restored bot, processed RHAIRFE-1 excluded |
| 3970 nested-podman | success | Inner exit/output, exit 37 propagation, DNS/HTTPS, cleanup |
| 3971 openshell-a | success | Feature Fullsend sandbox, four services, wrong-CA rejection, cleanup |
| 3972 openshell-b | success | Same checks while the other gateway was running |

All six traces identify glemu-k8s-runner; job API aliases description as
gitlab-runner, while CI_RUNNER_DESCRIPTION is not injected. The native probe
performed no model calls or Jira/results writes; real Vertex phase execution
and publication remain separately proven by M6. Native main is unchanged at
`14d81319af44973d592e4197b14b680684f35813`.

Concurrent runtime proof:

- 3971 pod runner-emulator--project-7-concurrent-1-g0q6x4wl; gateway/network
  strat-3971 / openshell-strat-3971; sandbox fs-con-9d7a9866d775.
- 3972 pod runner-emulator--project-7-concurrent-0-c84thdxb; gateway/network
  strat-3972 / openshell-strat-3972; sandbox fs-con-4084f34ceec8.
- Distinct pod UIDs, certificate fingerprints and job state directories, each
  with its own database and one sandbox visible to its engine. Both pods had
  independent container storage/run emptyDirs and no hostPath. Both cleanup
  exits were 0, with zero containers and no job network after cleanup.

Negative eligibility **2043**: tagged ordinary 3973 passed, untagged 3974
remained pending without a runner; canceled only that probe after recording.
Failure-artifact **2044/3975** preserved intentional exit 37 and sanitized
the synthetic fixture to [REDACTED]. The same EXIT sanitizer was published
to the M6 CI branch at `08b93ad5edfcf7dabffe5e42f801821823ea6c03`; no model
job was started. Exact-value credential scans across ten retained job archives
found zero known managed secrets. Final validation branch fixture commit
`fba5547f7c68d49f721cb4517bbbf902e9bf9eb3` includes that failure guard.

Local registration checks passed token reuse, duplicate removal, refusal to
reset active work, drain timeout leaving the runner paused, and empty-registry
recovery. Bash syntax and rendered TOML checks passed. Maintenance, image
requirements, shared privilege boundary and rollback are documented in
`docs/deployment/gitlab-runner.md`; reproduction fixture is
`var/demos/fullsend-entrypoint-poc/runner-validation/`.

## Findings and remaining differences

Pipeline 2041's native check failed only at a logging line referencing an
uninjected variable; corrected fixture passed in 2042. Its OpenShell job
3966 separately failed DNS (SSRF denial on resolution failure), and Podman
reported an aardvark-dns startup error during removal. Outer cleanup left no
containers/network and preserved failure. Fresh concurrent 3971/3972 passed;
root cause is **not fixed** and remains an [open reliability bug](../../bugs/open/nested-podman-aardvark-dns-startup-intermittent.md).

The emulator skips appended after_script on script failure. An EXIT sanitizer
mitigates artifact exposure and is live-tested; the underlying emulator
[behavior remains open](../../bugs/open/gitlab-emulator-after-script-skipped-on-script-failure.md).
Earlier bridge scheduling, canceled status, permissive Jira Basic auth,
service-account bootstrap and deferred M3 coverage retain their recorded
status. M7 does not turn the review's revise/5-of-8 outcome into approval.

## Final state

Emulator rollout/restart completed; repeat authoritative deployment reused
maintained registration **ID 1**. One manager is ready, Recreate, concurrent=4,
privileged=true, tags k8s-incluster/aipcc-small-x86_64, run_untagged=false,
with both per-job emptyDir mounts and no obsolete experiment resources.
The final post-restart ordinary/untagged check is recorded below.

Final post-restart pipeline **2045**: ordinary CI **3976** passed; untagged
**3977** remained pending with no runner and was canceled after observation.
Final validation branch commit `ec2f2ce362f482ad93da7ea2f18d441fddede10c`.
The final inspection confirmed exactly one registration, one ready manager
and no temporary runner config/credential resources. Python/YAML/Bash syntax,
registration checks, full-reset mocked control flow and git diff --check passed.
