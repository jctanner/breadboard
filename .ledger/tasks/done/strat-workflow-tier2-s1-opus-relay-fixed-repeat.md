# Single S1 Opus batch after the managed-account relay fix

## Authorization

2026-10-11: user proposed another S1 batch after requesting the relay fix.
Run exactly one repeat of the same tier 2 three-RFE S1 Opus workload,
keeping S1/S2 designs, fixture content and benchmark harness unchanged.
Archive the new run; no S2 or further repeat is authorized.

## Acceptance criteria

- [x] Previous S1 Opus archive passes host verification; live reset guard
      recognizes both completed Haiku and Opus runs.
- [x] No active pipeline jobs or Markov runs; fixed relay build is healthy.
- [x] Launch one S1 Opus batch and verify seed, model, design pin and wait budget.
- [x] Start one detached collector and retain relay source/deployment provenance.
- [x] Verify final archive and analyze the relay's effective streaming deadline,
      retries, reviewer handoffs, runtime, usage and primary context.
- [x] Record results; stop before any S2 or additional repeat.

## Preflight

Previous run `markov-run-7845a7f1` archive:
`var/run-data/strat-workflow/markov-run-7845a7f1/20261011T162230677725Z`.
Host checksums verify; live reset guard has no pending archives.
Relay build fingerprint:
`84bb7c79a09bfcb0c29dd7edd517605bfcf293994d95a9dbe4818a0fdc40b8c0`.
All private storage health counters zero. Harness remains pinned to
`2615e72e79704874620be092af2ae5fffc76b8e9`, S1 to `1bd7f17`,
Opus 4.6, repeats=1, only_tests=S1, wait=5,400,000 ms, wipe_at_start=false.

## Live run

One POST submitted **2026-10-11 17:04:21.986 UTC / 13:04:21 EDT**:
`markov-run-c5ba3904` (database ID 568), source `2615e72e`.
Seed `script-seed-scenario-all-claude-haiku-5-5-1011-170425-10f2cf`
completed; both archive guards and seed checks passed before S1.
S1 job `script-run-workflow-all-claude-opus-4-6-1011-170435-3f61ed`
created 17:04:35 UTC, running, model `claude-opus-4-6`.
Actual Kubernetes job fields verified: BATCH_SIZE=3,
BATCH_EXPECTED_KEYS=RHAIRFE-1 RHAIRFE-2 RHAIRFE-3,
STRAT_CREATOR_REF=`1bd7f1718c7ed10f2900691c0e9eaea2b8e48e43`,
STRAT_BG_WAIT_CEILING_MS=5400000, experiment
`strat-workflow-eval/tier2-opus/S1/opus`.

One detached archive collector, host PID **2460265**, started 17:06:25 UTC
with `--wait 8100`; escalated host inspection confirms it is active.
Log/process metadata under `var/run-data/strat-workflow/markov-run-c5ba3904/`.
`launch-context/` preserves the exact uncommitted relay source, working-tree
patch and deployed build/account/configuration context; its three files
(135,333 bytes) verify against their own SHA256 manifest. The collector
creates a separate timestamped final runtime capture with browsable API
dumps and strace, verifies it and publishes receipts. No second collector,
S2 or additional run was started.

Analyze whether managed-account streams can finish beyond 120 s, any new
timeout_error events, retry/concurrency costs, final reviewer returns and
primary context growth. The existing reviewer handoff bug is unchanged and
may still cause the evaluation gate to fail even if the relay fix works.

## Completed

S1 completed **17:55:45 UTC / 13:55:45 EDT**, wall **3070 s / 51.2 min**;
Markov completed 17:55:49.922 UTC. All runner exits zero. Three strategies
have APPROVE reviews: 7/8, 8/8, 6/8; all other evaluation checks pass.
Evaluation FAIL only on reviewer_outputs_returned: 10/12 empty Skill
completion markers; two substantive testability results both cover all
three strategies despite individual-target launches. Scope drift recorded
as a separate open bug; no S1 change or further model run.

Relay verification: 335 complete requests, zero failures; all 283 streaming
generations match S1 response dumps. Seven complete streams exceed 120 s,
range 124.211–170.314 s, all seven matched to S1. Deployed build ID matches
the repaired source. No timeout/stream failure or rate-limit evidence.
Runtime is 20.6 min / 28.7% below the pre-fix pass; two nondeterministic
trials do not quantify a guaranteed improvement. Reviews took 15.2, 19.0
and 16.3 min, with the same two-worker pipeline. Usage: 283 calls, 216778
output, 11038816 cache-read, 1696541 cache-write tokens.

Primary model: six calls identified by outer stream assistant IDs joined
to relay records. Input context 24103 → 24762 before waiting, then 25584,
25827, 26192, 26887 after completion. No primary model call/polling during
17:05:02.590–17:55:16.548 UTC. Last generated answer adds 161 output
tokens; 26887 is the last measured input context, not aggregate usage.

Final archive verified, receipts published:
`var/run-data/strat-workflow/markov-run-c5ba3904/20261011T175615927646Z/`.
Manifest final=true, complete=true, zero errors; 20 sources, 2715 files,
1267550579 bytes, including 566 API dumps and 1710 strace files for S1.
Capture interval 17:56:15.928–18:00:46.133 UTC. Separate verified
launch-context source snapshot remains alongside the capture. Collector
returned ok=true, problems=[], receipts_published=true. No S2 or repeat.
