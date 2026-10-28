# Bug: OpenShell relay profile excludes Claude's compiled leaf executable

## Evidence

Pipeline 2099/job 4066 completed host preparation and created a real sandbox.
Fullsend launched Claude 2.1.296 as Opus 4.6 at 02:02:42 UTC. Every API attempt
failed with `ERR_PROXY_TUNNEL`; Fullsend exited after one validation iteration.
Its transcript reports **zero input/output/cache tokens and $0**. The relay
has zero matching requests. Owned ticket claim, evidence capture and gateway
cleanup all completed successfully.

OpenShell's native sandbox log names the actual rejected process:
`/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe`.
The npm launcher runs this compiled binary, whose basename matches neither
`**/claude` nor `**/node`. The model-free Python discovery check exercised
neither this executable identity nor its network access.

## Fix

Add only the exact observed compiled executable path to the local relay
provider's allowlist, retaining its exact host, method/path rules and TLS
inspection. No direct upstream access, credential exposure or policy bypass.
The configuration regression now checks the real leaf executable explicitly.

## Archive

Complete native evidence and independent checksum verification both pass:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2099/20261019T020654.319358Z`.
It contains real raw API attempts and syscall traces, plus native Fullsend,
OpenShell, host-state and shared-service evidence. Pipeline/job failed as
expected; there is no Workflow business result or publication to claim.

Related: [single-RFE smoke](../../tasks/done/fullsend-claude-workflow-opus-single-smoke.md).
