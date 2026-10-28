# GitLab Fullsend branches available for Workflow qualification

Read-only live inspection of private project 7,
`redhat/rhel-ai/agentic-ci/strat-pipeline`, on 2026-10-18. Both relevant POC
branches still exist. No branch publication, CI run, Jira change or model call.

| Branch | Current head | Latest pipeline | Outcome |
| --- | --- | --- | --- |
| `feat/fullsend-strategy-poc` | `4810e1703d59b21d4c92bba584169d0fa6ae5041` | 2073, 2026-10-07 | Success: feature build 4032 and batch-discover 4033; strategy job 20m41s. |
| `feat/fullsend-agent-led-poc` | `89c879b69366cb2a9b21068f0781c7277b8f04e8` | 2090, 2026-10-08 | Success: strat-single 4053, 29m10s; build-dashboard 4054 triggered after completion. |

Also present: `feat/fullsend-runner-validation`, `demo/fullsend-rhaistrat`
and preserved `main` at `14d81319af44973d592e4197b14b680684f35813`.
Project pipeline schedules currently return an empty list. GitLab deployment
in ai-pipeline and the maintained runner deployment in gitlab-runner each
report 1 desired / 1 ready / 1 available. This is service readiness, not a new
sandbox execution test.

## What was functional

The script-led POC ran actual create/refine/push/review through a job-owned
OpenShell gateway, using a custom Fullsend entrypoint feature build. Its
single- and two-RFE batch acceptance, owned lock cleanup, results publication
and artifact handling are documented in the completed M6/M8 tasks. Latest
branch CI still pins the old public fork's `feat/fullsend-strategy-entrypoint`
at `3fd1563ede66c6f3080606d36b7341ef4deb07e7`.

The agent-led POC uses released Fullsend 0.43.0, with host preparation,
validation, publication and cleanup around a native model-driven agent. It
passed a scheduled two-ticket batch (2084/4045) and recovery (2086/4047).
Its latest single-ticket run, 2090/4053, created/refined/reviewed RHAISTRAT-17,
published results, recovered the Org Pulse stale key automatically and rebuilt
the dashboard after publication. The current CI pins old source `9350c89` on
`feat/fullsend-agent-led-strategy`; it does not load PR 85's Workflow.

Historical success does not claim the new candidate works in Fullsend.
The hardened Workflow's recent tests ran in Breadboard/Markov Kubernetes jobs,
outside the complete Fullsend/OpenShell path.

## Recommended reuse

Create a separate branch, for example `feat/fullsend-claude-workflow`, from
`feat/fullsend-agent-led-poc`. Preserve both green baselines and main. Reuse
the maintained runner, job-owned gateway, credential handling, redaction,
results/dashboard publication and cleanup. Adapt the launch to the candidate's
existing `strat-single` / `strat-batch` harnesses, which already instruct the
primary agent to invoke the shipped Workflow plugin.

Required integration changes before a model run:

1. Pin `https://github.com/jctanner-fullsend-ai/strat-creator.git`, branch
   `feat/s1-workflow-hardening`, at the tested full candidate SHA
   `6ed858b2294a29457153a90f187a801022c21e8b` (or a deliberately chosen newer
   published repair). Old source references alone cannot exercise the new code.
2. Update the old Fullsend 0.43.0 launch/setup for the current harness contract.
   The new harness pins the Fullsend 0.47.1 sandbox image by digest and requires
   Claude Code 2.1.296. Keep the runtime check and existing one-iteration policy.
3. Generate/register agent configuration through the installer/fleet path.
   The current source deliberately omits installer-managed `.fullsend/config.yaml`.
4. Supply all current runner variables, including full-SHA `STRAT_CREATOR_REF`,
   `STRAT_DRY_RUN` and `STRAT_PREVIOUS_PROGRESS` (empty where appropriate).
   The old CI only sets STRAT_CREATOR_SHA and its older optional-variable set.
   Carry the chosen model and concurrency through explicitly.
5. Adapt the production-Jira-only sandbox policy for the local Jira emulator
   and current local CA while retaining certificate verification and the
   existing boundary. Retain host-side architecture fetch and publication.
6. Include raw API/syscall/native evidence in the run archive, with the
   established private var/run-data retention and redaction. CI's old always-
   collected artifacts alone do not prove the newer complete capture contract.
7. Validate configuration, plugin/hook loading, interpreter/dependencies,
   source pins and sandbox connectivity without inference, then perform the
   separately authorized single-ticket integration smoke.

The rejected custom-entrypoint patch is unnecessary for the new agent-led
Workflow path. The original script-led branch remains useful as historical
comparison/recovery evidence.

## Inspection details

Live branch/pipeline/job lists and both raw CI definitions were read via
authenticated GitLab GETs. Anonymous access returns 404 for this private
project; that initial response did not mean it was missing. Current CA came
from ConfigMap `ai-pipeline/internal-ca-cert` (`ca.crt`); the older checked-in
deployment-image CA was insufficient. No token was minted or credential value
printed. Raw read responses are in ignored temporary files under /tmp.

Related evidence:
- [Script-led real acceptance](../tasks/done/fullsend-strategy-poc-integration.md).
- [Script-led batching](../tasks/done/fullsend-strategy-batch-ci.md).
- [Agent-led batch/recovery](../tasks/done/agent-led-strategy-batch-events.md).
- [Agent-led latest publication run](../tasks/current/agent-led-strategy-publication-recovery.md).
- [Current S1 hardening and qualification limits](../plans/strat-workflow-s1-hardening.md).
