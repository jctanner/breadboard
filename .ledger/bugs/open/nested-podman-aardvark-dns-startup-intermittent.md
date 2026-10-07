# Bug: Intermittent nested Podman DNS startup failure

## Summary

During M7 pipeline 2041, OpenShell job 3966 could not resolve any allowed
service hostname. Supervisor logs report `engine:ssrf`, temporary DNS
resolution failure and proxy HTTP 403; policy hash was the same as successful
job 3965. Container removal also reported an aardvark-dns startup error.
The outer harness nevertheless removed all job containers and its network,
retained diagnostics and returned failure (`cleanup_exit=1`).

## Evidence and current status

Distinct pod UIDs, job-specific emptyDirs, gateway certificates/databases,
networks and one sandbox per engine prove independent runtime state. No
hostPath/shared engine was present. A fresh full matrix, pipeline 2042,
passed both concurrent OpenShell jobs 3971/3972, all service/wrong-CA checks,
and cleanup. The failure has not been reproduced or causally fixed.
Both pipelines briefly overlapped while exercising the maintained runner.
Do not attribute it to policy permissions or claim that retry fixed the root cause.

## Follow-up

Capture aardvark process stderr, child DNS configuration, network namespace
IDs and node pressure while reproducing concurrent engine bootstrap. Keep
policy/TLS checks strict; do not treat failed DNS as certificate rejection.
M7's successful concurrency acceptance is recorded separately, with this
remaining reliability limitation disclosed.

## Related task

[M7](../../tasks/done/consolidate-gitlab-runner-capabilities.md).
