# Task: Copy the working Fullsend POC for Workflow qualification

## Goal

Publish a separate `feat/fullsend-claude-workflow` branch on GitLab.local,
copied from the successful agent-led POC, running the pinned PR 85 Workflow
through released Fullsend and OpenShell. Use model-relay and managed client
secrets instead of exposing upstream Google or EnMaaS credentials.

## Acceptance criteria

- [x] Preserve main and both successful POC branches.
- [x] Pin the tested Workflow source, compatible Fullsend and sandbox runtime.
- [x] Register agents, plugins and hooks using the current harness contract.
- [x] Restrict sandbox network access to the local Jira and relay endpoints;
      verify local certificates and keep provider secrets outside agent memory.
- [x] Supply CI inputs and secrets without committing their values.
- [x] Preserve locking, one validation iteration, publication, cleanup and evidence.
- [x] Run meaningful model-free configuration/security tests and publish the branch.
- [x] Record the exact remaining live integration test, without launching inference.

## Authorization and constraints

User authorized the copy pathway and relay/provided-secrets integration.
Base: `feat/fullsend-agent-led-poc` at
`89c879b69366cb2a9b21068f0781c7277b8f04e8`.
Candidate: `jctanner-fullsend-ai/strat-creator` at
`6ed858b2294a29457153a90f187a801022c21e8b`.
No inference is part of this setup task. The user subsequently selected
`claude-opus-4-6` as the default for this exercise, replacing GLM. Use high
effort and pin the primary agent, subagents and all model aliases together.

## Status

Done: copy/setup and model-free qualification. Actual single-RFE Workflow
execution inside Fullsend remains the next test. Previous branch inspection:
[findings](../../notes/gitlab-strategy-fullsend-workflow-base-20261018.md).

## Implementation and checks

- Published isolated GitLab branch at `9f7a97bb758a57b1201889456da6a08f62ad8e6c`;
  all five previous branch heads unchanged. Source pin `6ed858b`, released
  Fullsend 0.47.1 checksum verified; all three agent registrations and local
  profile/plugin resolution pass the actual released CLI.
- Opus 4.6 / high / cap ten replaces the initial GLM default on user request.
  Created a relay-issued Opus-only client credential, masked and scoped to
  the new CI environment. No upstream secret copied, no credential value
  printed. The interrupted GLM provisioning had created nothing.
- Fourteen model-free local checks pass, including code preservation,
  credential references/redaction, exact-host policies, branch isolation,
  actual CLI registration/locking and safe native-artifact extraction.
- Diagnostic pipeline 2092 / job 4056 stopped before any Claude invocation:
  the diagnostic sandbox name exceeded OpenShell's 19-character limit.
  Agent registration and both provider imports/creations passed. Shortened
  diagnostic name for the next revision. Zero inference and no ticket claims.
- Derived image explicitly pins Claude 2.1.296 and the candidate's locked
  Python helper dependencies. Claude's native npm module and launcher remain
  unchanged. Added Node to the relay profile for the npm CLI's executable.
- Diagnostics 2092/4056 and 2093/4057 have complete, verified private captures
  under `var/run-data/fullsend-claude-workflow/gitlab-pipeline-2092` and `2093`.
  The second diagnostic created a sandbox but stopped on the OpenShell upload
  quirk: a file destination became a directory. Upload into the existing
  workspace directory using unchanged basenames for the next revision.
- Fifteen local tests now pass. Capture preserves downloaded symlinks as
  metadata, without following targets. Exact CI source and pinned candidate
  are included in new archives; capture-time helper source is labeled separately.
- Runtime verification stays in the unchanged plugin's SessionStart and
  freshness/pre-launch hooks, inside the actual sandbox. Fullsend's host-side
  validation preflight checks Python dependencies only; the CI host has no
  Claude. Run from the target directory so relative host paths resolve.
- A trusted CI-side observer traces sandbox-user processes through the
  job-owned engine, rather than putting ptrace into the agent launcher. No
  relaxation of OpenShell's seccomp controls. Attachment is sampled and may
  miss initial syscalls. The diagnostic checks for real syscall evidence.
- Revised model-free diagnostic submitted after these fixes. Still no
  inference, Jira mutation or ticket claims.
- Diagnostic 2094/4058 verified external observer attachment but exposed a
  workspace ownership race: the root observer created the workspace before
  SSH upload. Give that workspace to its intended sandbox owner; keep trace
  files operator-owned. Failed capture is complete and checksum-verified at
  `var/run-data/fullsend-claude-workflow/gitlab-pipeline-2094/20261019T011537.029909Z`.
- Existing managed CI key successfully discovers only the selected Opus 4.6
  through the relay. Host `/etc/hosts` lacks `relay-api.local`; provisioning
  uses curl's connect-to mapping to the existing relay.local address while
  retaining inference SNI and certificate validation. Cluster CoreDNS already
  contains the inference alias; no deployment change or TLS bypass.
- Exact-value secret scan: 17 source files, no matches to managed credentials.
  Private CI-variable scratch JSON removed after retaining metadata only.
- Background wait ceiling follows each harness timeout, avoiding the CLI's
  shorter default for a long batch. Automatic CLI updates disabled to preserve
  the qualified runtime. All model aliases remain Opus 4.6.

## Final acceptance

Published GitLab head `7b93d35a3bc718f45ec96b4e8d77461fb81dfc81`.
Pipeline **2095**, job **4059**, passed from 2026-10-19 01:17:27 to 01:22:17
UTC (4m50s), using the real Kubernetes GitLab Runner and job-owned OpenShell.
The source strat-creator checkout remains clean at `6ed858b`.

The probe verified Claude 2.1.296 and helper dependencies, provider placeholders
and absence of host-only keys, authorized Opus 4.6 discovery through the relay,
Jira identity GET, and denied direct Anthropic/Google/relay-admin access.
The inspected HTTPS endpoints work with the local CA baked before startup.
The Jira emulator does not enforce passwords; the result does not claim that
it validated a real Jira password. Five actual syscall files were captured.
Command, capture and cleanup exits are all zero. Fifteen local checks passed,
with the final configuration checks repeated after the last changes.

The passing capture is complete and independently checksum-verified:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2095/20261019T012334.561932Z`.
It contains 115 files / 40,027,440 bytes, including exact CI and candidate
source, native evidence, traces, service databases/logs and relay events.
Manifest SHA-256:
`56fb964dbdfcf1e17c684d31e1ab8c2bb8cf68652f5f30ccf21c9404f57477f3`.
All five previous branch heads remain unchanged; schedules were not created.

No inference or Jira mutation was performed. Next: one distinct eligible RFE
through `strat-single` on this branch with the Opus 4.6 defaults. That test
must verify actual Workflow/plugin business completion, native receipt,
publication/cleanup and raw API-body capture. The model-free diagnostic
qualifies configuration, secrets, TLS and capture plumbing, not those results.
