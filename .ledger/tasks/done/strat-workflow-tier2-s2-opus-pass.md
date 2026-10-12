# Single S2 Opus batch on the repaired relay

## Authorization

2026-10-11: user requested the batched single S2 run after analysis of the
relay-fixed S1 pass. Run exactly one S2 tier 2 pass on Opus 4.6, using the
same three distinct RFEs, existing S2 design and benchmark harness. Archive
and analyze this run before any further test. No repeats or design changes.

## Acceptance criteria

- [x] Prior S1 archive checksums verified; live archive guard has no pending runs.
- [x] No active pipeline jobs or Markov runs; repaired relay build healthy.
- [x] Submit one S2 batch; verify seed, actual model and design pin.
- [x] Start one detached final archive collector with launch provenance.
- [x] Verify archive and compare runtime, relay failures, usage and review
      outputs with the repaired-relay S1 pass.
- [x] Record results and stop before further tests.

## Preflight

Harness `2615e72e79704874620be092af2ae5fffc76b8e9`; S2
`0287b838d2bc59a2569cf2dd971aad7ad2d76dad`; tier2-opus, only_tests=S2,
variants=opus, repeats=1, wipe_at_start=false. Native batch discovery,
three RFEs: workbench cull exemption, DSP retention, Feast scheduled
materialization. The seed resets Jira after both archive guards pass.

Relay build ID
`84bb7c79a09bfcb0c29dd7edd517605bfcf293994d95a9dbe4818a0fdc40b8c0`
matches repaired S1. Previous archive
`var/run-data/strat-workflow/markov-run-c5ba3904/20261011T175615927646Z`
passes host verification. Live guard recognizes all three previous
archives; pending=[]; no active jobs or Markov runs.

## Live run

One POST submitted **2026-10-11 18:19:35.819 UTC / 14:19:35 EDT**:
`markov-run-6bcb3c32` (database ID 571), source `2615e72e`.
Seed `script-seed-scenario-all-claude-haiku-5-5-1011-181939-646f1c`
completed and all seed/archive checks passed. S2 job
`script-strategy-entrypoint-all-claude-opus-4-1011-181949-e387e8`
created 18:19:49 UTC, script began 18:19:59 UTC, running.

Verified actual job/model and logs: `claude-opus-4-6` pinned for sessions,
subagents and aliases; exact clone `0287b838d2bc59a2569cf2dd971aad7ad2d76dad`;
batch-discover, BATCH_SIZE=3, BATCH_EXPECTED_KEYS=RHAIRFE-1 RHAIRFE-2
RHAIRFE-3. Native discovery found and locked exactly those three. Architecture
snapshot `7d61f097a9220aeb1280837b66b532177ec558b6`; MLflow experiment
`strat-workflow-eval/tier2-opus/S2/opus`; API bodies, strace and OTel enabled.

One detached collector, host PID **2550958**, started **18:19:56.814 UTC**
with `--wait 8100`; host process inspection confirms it is active.
Root: `var/run-data/strat-workflow/markov-run-6bcb3c32/`.
`launch-context/` preserves relay source, patch and deployment metadata;
three source-context files pass SHA256 verification. Collector waits for
terminal run/jobs, collects a timestamped final archive with browsable API
dumps/strace, verifies it and publishes receipts. Final capture/analysis
pending. No further run launched.

## Final result: attempt analyzed; S2 job and benchmark failed

S2 exits **19:15:33 UTC / 15:15:33 EDT**, code 1. Job wall time from
creation is **3344 s / 55.7 min** (script-only elapsed 3334 s). Markov
finishes its reporting workflow at 19:15:42.682 UTC; its completed status
does not mean the design job or benchmark passed.

Abort: **upstream account HTTP 429**, at 19:15:25.737–25.960 UTC,
`This request would exceed your account's rate limit. Please try again later.`
Relay request `32d8fb77-a78d-404e-bbdb-627f2f56865d`, real managed Claude
OAuth profile `tanner-jc-personal`, upstream request ID present. Claude child
exits 1; script releases all three locks and exits without reviewing
strategy 3. No automatic retry or additional paid run.

All three RFEs have distinct created/refined strategies. RHAISTRAT-1 has
published APPROVE 7/8. RHAISTRAT-2 scorer and specialist work ran, but the
429 occurred before composing/publishing its final review. RHAISTRAT-3
has no dedicated review. Failed checks: finished, steps_done, one_review,
records_agree and reviewer_outputs_returned.

Relay: **235 total records**, 234 complete, one failed (the 429), zero
timeout/stream errors. **187 completed streaming calls**, all joined to
S2 API response IDs, plus the rejected streaming request. Seven successful
streams exceed 120 s, longest **186.484 s**. Build ID matches repaired S1.
Usage: 227 uncached input, 1403324 cache writes (all 5-minute), 8655663
cache reads and 168170 output. Standard API list-price equivalent
**$17.304 spent before abort**, not a complete-batch cost or estimate of
S2 savings versus S1's $21.552 / 51.2 min.

Eight specialist launches for strategies 1/2 return text; seven are
substantive but all cover the whole batch. Target 1 architecture returns
only a 170-character progress message, falsely accepted by the detector.
Updated common scope bug and created a separate reviewer-gate bug. Final
strategy 3 has no launches; no S1/S2 implementation changes.

Final archive independently verified, receipts published:
`var/run-data/strat-workflow/markov-run-6bcb3c32/20261011T191550355513Z/`.
final=true, complete=true, errors=[]; **20 sources, 2457 files,
1382240358 bytes**. Browsable S2 **376 API files and 1774 strace files**.
Capture 19:15:50.356–19:19:56.927 UTC. Collector returned ok=true,
problems=[], receipts_published=true. Original launch-context retained.
