# ADR-0010: Verify local Jira TLS in the strategy client

## Status

Accepted for the Fullsend strategy POC, 2026-10-06.

## Context

M4.2 must reuse M4.1's CI, supervisor, and sandbox images, retain verified
HTTPS, and prove Jira access through the existing Python client. Activating
service permissions in the base policy exposed a second failure: OpenShell
TLS inspection cannot trust the emulator's private CA. Pipeline 2020/job 3917
recorded `TLS relay error: invalid peer certificate: UnknownIssuer`. The same
bridge and sandbox image without inspection reached Jira using the runner CA.

## Decision

Put permission-only local service rules in the applied sandbox base policy,
not an imported but unattached credential provider profile. Match versioned
Python interpreters. Use `tls: skip` only for `jira.local:443`, which selects
an opaque CONNECT tunnel through OpenShell. The existing strategy client
verifies the real Jira certificate and hostname using the mounted runner CA.
There is no hardcoded ClusterIP, permissive global egress, or disabled client
TLS verification. Keep public GitHub endpoints under enforced read-only HTTP
inspection and keep the Vertex credential provider.

## Consequences

OpenShell enforces Jira's endpoint, port, and configured executable lineage
but does not inspect Jira HTTP methods or inject credentials in this tunnel.
Jira had read-write service access; the actual M4.2 fixture only calls GET APIs.
The harness continues to pass Jira credentials to its existing Python client.
Restoring Jira L7 inspection would require configuring the supervisor's
upstream private-CA trust before sandbox startup and proving that path with
the selected images. GitLab/Org Pulse retain their prior inspection settings
and still require M6 validation.

The current Jira emulator defaults to permissive Basic authentication.
`/myself` demonstrates CI identity propagation; invalid Basic passwords are
accepted, so these checks cannot prove password validation. M5/M6 recheck
the auth mode and service identity after reset.

Evidence and fresh-job acceptance are tracked in
[the M4.2 task](../tasks/done/fullsend-sandbox-jira-connectivity.md).
