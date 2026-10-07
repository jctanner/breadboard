# ADR-0011: Verify local strategy service TLS in clients

## Status

Accepted for M6 POC, 2026-10-06; extends ADR-0010.

## Evidence and decision

Pipeline 2031/job 3938 used the actual public feature checkout and policy.
The restored Jira bot identity and public GitHub API passed, while allowed
GitLab and Org Pulse HTTPS requests were reset. Collected supervisor logs
show allowed Python executable/endpoint checks followed by NET:FAIL.

Apply the previously proven Jira private-CA solution to `gitlab.local:443`
and `orgpulse.local:443`: opaque TLS tunnels with client certificate and
hostname verification using the mounted local CA. Verify trusted access and
wrong-CA rejection in a fresh sandbox before real strategy execution.

## Consequences

OpenShell retains endpoint/port/executable-lineage enforcement for these
local services. It does not inspect their HTTP methods or inject credentials
in opaque tunnels. The workflow supplies credentials directly to its existing
clients. Public GitHub read-only HTTP inspection is unchanged. Supervisor
upstream private-CA trust and restoration of local HTTP inspection remain a
future capability, not a prerequisite for this POC.
