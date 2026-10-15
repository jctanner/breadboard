# Schedule the next Opus batch

Status: done. Scheduling, run analysis, recovery archival, independent final
verification and published receipt checks are complete. The pinned evaluation
remains FAIL on the documented architecture-judgment vocabulary mismatch.

Add and deploy one-time and recurring cron scheduling in checkouts/markovd.
Schedule one S1 three-RFE Opus batch at 2026-10-15 00:30 America/New_York
(04:30 UTC), repeats=1, cap=5, candidate f3508786a1e2200731b25dfeda7e01ef772d32ce,
Breadboard 5ed4a28494bcbb0d3fed31cbe985bca16fc49cc0.
Keep final archives and attach an observer to collect this run after completion.
Scheduling tests use harmless workflows and spend no model tokens.

Implementation deployed from `checkouts/markovd`, feature branch
`feat/run-scheduling`, via `make host-rebuild-markovd`. Full Go race suite with
isolated PostgreSQL, frontend build and tests pass. Live one-time/cron dispatch
survives server restart; each dispatched once. Browser creation, edit,
pause/resume, delete and blocked-response loading checks pass.

Queued schedule **6** for **2026-10-15T04:30:00Z**. The imported workflow
and frozen schedule source both equal 5ed4a28494bcbb0d3fed31cbe985bca16fc49cc0.
Payload: tier=s1-hardening-opus, only_tests=S1, variants=opus, repeats=1,
wipe_at_start=false, breadboard_ref=5ed4a28494bcbb0d3fed31cbe985bca16fc49cc0,
workflow_bg_wait_ceiling_ms=17700000, job_timeout=18000. Tier verifies f350878,
batch size three and cap five. Previous final archives independently reverified
before saving this schedule.

Detached observer PID 3302018 follows only the schedule's run ID and archives
before evaluating the result. It never submits or retries a paid run. Runtime
context and eventual captures:
`var/run-data/strat-workflow-hardening/opus-scheduled-20261015-0030/`.
The copied observer/helper, schedule intent/response, preflight/import data,
status and observer log live in `launch-context/` there. Terminal results and
final verification are recorded below.

## Morning result

The schedule fired once at 04:30 UTC. Run `markov-run-dd4a838118bd23d18c693b01`
completed; its Opus job ran 04:30:12–05:06:40 UTC (36m28s). All three strategies
completed, all 12 actual reviewer returns match provenance and final reviews,
and native/receipt/input hashes verify. The pinned benchmark remains red only
because one architecture judgment starts “Mostly sound”; transport content is
present. [Results](../../notes/s1-hardening-scheduled-opus-20261015.md).

The overnight archive hit a 600-second dashboard volume timeout and correctly
published no receipt. Recovery PID 3706531 is collecting a separate capture
with fast lossless gzip and a configurable 2,400-second stream timeout. The
original incomplete capture is retained. No model rerun/reset occurred.
Recovery is complete. Final capture `20261015T111127302464Z` independently
verifies: complete/final, errors=[], 3,599 files / 8,998,503,549 bytes, receipt
published. API dumps, strace, native traces, logs, Jira, MLflow and Observatory
state are included. Both incomplete captures are retained; recovery source
intervals/provenance are explicit. The completion/report audit passes again
against the final capture. No paid rerun occurred.

Closure verifies one schedule occurrence and the live published receipt's
resolved archive path and manifest hash. Directly browsable model-job evidence:
569 API dump files, 2,357 strace files and 295 artifact files. Closure and audit
records are saved in launch-context/campaign-closure.json and
post-run-audit-recovered.json. The original observer's failed result/log remain
intact as historical evidence of the archive timeout.
