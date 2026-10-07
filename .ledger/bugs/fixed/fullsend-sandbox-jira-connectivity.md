# Bug: Jira access fails inside the Fullsend sandbox

## Summary

M4.1 reported a DNS hang for `jira.local` inside the sandbox and a timeout
when pinning a request to Jira's Kubernetes ClusterIP. The runner itself
resolved the name and received trusted HTTPS status 200. That initial report
did not establish whether DNS, routing,
OpenShell policy, or another layer is responsible.

## Evidence and impact

See [M4.1's recorded checks](../../tasks/done/strat-creator-rfe-autofixer-images.md),
GitLab pipeline 2011, jobs 3898/3899. Reproduce with that shared image set
and the strategy sandbox policy. A working runner connection does not prove
the sandbox can execute the strategy's Jira operations.

Expected: the strategy's Python HTTP client can call the local Jira API
from inside the sandbox using `https://jira.local` and verified TLS.

This blocked the strategy integration run. The fix and fresh-job verification
were completed by [M4.2](../../tasks/done/fullsend-sandbox-jira-connectivity.md).

## Resolution

Fixed, 2026-10-06, in strat-creator
`bd20534f5b904ae7808d167ad3cde671e17d5ab1` (pushed).

The imported service profile was unattached, so its network permissions were
inactive; its Python pattern also missed the actual versioned interpreter.
Move service permissions into the applied base policy and match `**/python3*`.
Once OPA allowed Jira, structured logs showed supervisor TLS inspection
rejecting its private CA with `UnknownIssuer`. Jira-only TLS passthrough now
lets the existing Python client verify the server certificate and hostname
using the runner CA, while endpoint/port/executable policy remains enforced.
Jira HTTP inspection is absent; public GitHub keeps read-only inspection.

Pipelines 2022 and 2023, smoke jobs 3921 and 3923, independently passed Jira
server information and intended CI identity, rejection without the local CA,
allowed GitHub HTTPS, blocked endpoint, output transfer, and cleanup. The
emulator is permissive for Basic passwords; identity propagation is proven,
password validation is unavailable and documented. Direct child DNS fails
immediately, not a hang; HTTP CONNECT resolves upstream. The same Podman
bridge resolves and reaches Jira, so routing was not the root cause.

See the completed M4.2 task for pins, sanitized evidence, tests, and cleanup.
