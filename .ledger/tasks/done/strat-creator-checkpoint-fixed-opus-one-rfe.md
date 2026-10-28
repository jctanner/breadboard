# One-RFE Opus smoke after the checkpoint performance repair

Authorized 2026-10-16: one RFE, one S1 iteration, `claude-opus-4-6`.
No automatic paid retry or resume.

Candidate: `2a4b7c94b93a2d43bc25fe701e225e5738e226af`, published on PR 85's
`feat/s1-workflow-hardening` branch in `jctanner-fullsend-ai/strat-creator`.
Benchmark source remains the published `440d864797c4dd7e6e31ec639acb751c6ed2308b`;
only the run's tier override changes. Keep historical tiers and archives intact.

Run-only tier `s1-pr85-checkpoint-fixed-opus` selects S1, `smoke-one-rfe`, batch
mode, native integer default size one, concurrency ten, native capture and
stop-on-workflow-failure. No global telemetry wipe. The fixture resets Jira
only after idle, schedule and prior final-archive checks pass.

Use `./bin/markovd-cli` for project sync/import, launch and run status. Read-only
API fallback is limited to exact workflow source metadata (the installed CLI's
typed workflow output omits `source_commit`) and schedules (no CLI command).
The detached observer never starts model work; it collects and independently
verifies terminal evidence and publishes final archive receipts.

Campaign root:
`var/run-data/strat-workflow-hardening/pr85-checkpoint-fixed-vertex-opus-one-rfe-20261016/`.

- [x] Confirm published candidate and deployed Claude Code 2.1.296 without inference.
- [x] Verify the exact one-job/one-RFE Opus request with offline Markov execution.
- [x] Sync/import and verify source, prior archives, idle state and provider readiness.
- [x] Submit once using the CLI and verify the actual process/model/provider.
- [x] Archive terminal evidence and record the independent result.

[Performance fix and profiling](../done/strat-refine-checkpoint-performance.md).
This is Kubernetes/Markov/Breadboard integration, not a Fullsend/OpenShell
deployment test or independent judging of strategy quality.

## Run and result

Submitted once through `./bin/markovd-cli --output json runs create` with
`--workflow main --vars-file`, using repository config and its default mounts.
Run [markov-run-f5a9eb0a](https://markovd.local/runs/markov-run-f5a9eb0a) started
2026-10-17 00:56:07 UTC (2026-10-16 20:56:07 America/New_York).

Model job: `script-run-workflow-all-claude-opus-4-6-1017-005620-09f706`.
The actual process verifies candidate 2a4b7c9, expected fork, batch mode,
one acquired RFE (`RHAIRFE-1`), batch size one, concurrency ten and stop on
native Workflow failure. Primary/subagent/default Haiku/Sonnet/Opus aliases
all resolve to `claude-opus-4-6`; initial source diff is empty. Initial completed
HTTP 200 requests use `vertex-strat-evals` and Google service-account auth.

All 69 imported files match benchmark source 440d864. Three previous model-job
archives passed independent checksum verification before the Jira fixture reset.
The model-free version probe confirms Claude 2.1.296 in image digest
`sha256:2a7c01426967e6a7e1566525057a81b0060026969cb6f2f8430a7e1abfd6115e`;
that temporary probe is removed. The seed job's Haiku name is non-inference
fixture metadata, not a Haiku model request.

Detached archive observer: PID 1877633. Request, exact CLI invocation, imported
source, preflight checks, source/model snapshots, initial relay telemetry,
observer logs and status are saved under the campaign's `launch-context/`.
The model job completed at 2026-10-17 01:22:58 UTC (2026-10-16 21:22:58
America/New_York). Markov subsequently completed its evaluation. The independent
`eval-result.json` reports **PASS**, with no failed checks, and every recorded
pipeline stage exit code is zero.

- Job runtime: 26m38s; native Workflow: 25m24s.
- One acquired RFE, `RHAIRFE-1`, produced one strategy, `RHAISTRAT-1`.
- Create, refine, push, scoring, review and final business validation completed.
- All four assigned role assessments returned, each with one launch and no rerun.
- Numeric score: 7/8, approve; Jira verdict, labels and local records agree.
  Feasibility/testability recommend revision, while scope/architecture approve.
  This is consistent with the user's numeric-score-only approval policy.
- The previously failing refinement checkpoint completed on its first attempt.
  Its agent took 10.454s including inference, shell work and hooks; this is not
  a measurement of the hook alone. No hook timeout is recorded in CLI stderr.
- Final completion receipt validated; all ticket claims released.
- All 117 captured inference requests used Opus 4.6. No recorded API errors or
  rate limits. Accounted tokens: 4,897,354, including 4,080,626 cache-read,
  748,697 cache-write, 146 uncached input and 67,885 output tokens. Reported
  thinking is not added again to this total.

Final archive collection and independent checksum verification completed at
2026-10-17 01:36:19 UTC. The manifest is complete/final, with 1,742 entries
and no capture errors; final receipts are published. It includes job artifacts,
native Workflow state, raw API dumps, syscall traces and system snapshots.
The campaign's `launch-context/result.json` and `archive-verification.json`
record PASS, exact source match, verified archive and receipt publication.
