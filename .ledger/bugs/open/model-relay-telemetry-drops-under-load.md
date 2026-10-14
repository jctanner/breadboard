# Model Relay drops telemetry records under high request volume

Component: `checkouts/model-relay` (Model Relay, deployed as `model-relay`
in `ai-pipeline`). Found 2026-10-10 during the strat-workflow benchmark
smoke runs ([plan](../../plans/strat-workflow-eval-plan.md)).

## Evidence

- `GET /api/private/v1/health` on 2026-10-10 at about 02:56 UTC reported
  `"dropped_records": 3901` with `"storage_errors": 0`, while
  `/api/private/v1/telemetry/requests` held only 449 records in total, 2026-10-09
  21:33 to 2026-10-10 02:56.
- The drops happened during PR #83 Workflow runs. Those fan out to several
  agents streaming at once (refine, scorer, four reviewers).
- `src/telemetry.rs`:
  - every request record and every streamed usage event goes through
    `enqueue()` onto `mpsc::channel::<Write>(1024)`;
  - `enqueue()` uses `try_send`; when the queue is full the write is
    discarded and only `health.dropped` is incremented;
  - one `telemetry-writer` thread drains the queue with one SQLite
    `execute` per write, each its own commit.

## Impact

- **Agents and inference are not affected.** `try_send` never blocks or
  errors the request path, and every recorded request returned HTTP 200.
- **Telemetry is incomplete under load.** Call counts and token totals from
  the relay are lower bounds. The counter doesn't say whether whole request
  records or only intermediate usage events were lost, so per-run cost from
  the relay can't be trusted for the eval until this is fixed.
- The benchmark plan should take cost from the jobs' API dumps or Claude's
  `result` events until then.

## Suggested fix

1. Batch the writer: drain whatever is queued and write it in one
   transaction, instead of one commit per row.
2. Never drop final request records. Await capacity for `Write::Request`,
   and allow dropping only intermediate `Write::Event` usage updates.
3. Coalesce usage events per request (keep the latest), which cuts the
   write volume.
4. Optionally enlarge the queue, as a backstop only.
5. Report which kind of write was dropped (request vs event) in `/health`.

## Verification to record when fixed

Run a Workflow fan-out (strat-workflow S1 on haiku) and confirm
`dropped_records` stays 0, or counts only events. The relay's request count
for the job should then match the job's API dumps.

## Fix (2026-10-10, deployed)

Committed in `checkouts/model-relay` (`src/telemetry.rs`, `src/admin_ui/admin.js`):

- The writer drains up to 512 queued writes and commits them in one
  transaction. A request's record is rewritten at every streamed usage
  snapshot, so only its latest copy in a batch is written; events are
  coalesced by (request, sequence).
- The queue is unbounded and is limited by count instead. Usage events are
  dropped above 1,024 pending writes. Request records are dropped only above
  65,536.
- `/health` adds `dropped_requests`, `dropped_events`,
  `last_dropped_at_unix_ms` and `last_storage_error_at_unix_ms`.
  `dropped_records` remains, as their sum.
- The console's "Storage needs attention" came from the lifetime
  `dropped_records` counter, which never resets: 21,538 at 18:30 UTC, still
  rising during the smoke re-run. The console now warns only about request
  drops or storage errors in the last 15 minutes.

The console's frozen numbers were a separate bug, also fixed:
`/telemetry/requests` paged oldest first, so the console's first page, and
every stat computed from it, was always the same 100 oldest requests. The
list, summary and export endpoints now accept `order=desc`, and the console
uses it.

Deployed with `make host-rebuild-relay` at 2026-10-10 23:39 UTC, before the
opus smoke run (`markov-run-f2f3b733`), together with
`SHIM_UPSTREAM_TIMEOUT_SECONDS=600` in `deploy/k8s/29-model-relay.yaml`.
Checked after the restart: the pod has the 600 s timeout; `/health` reports
the new fields, all drops 0; `order=desc` returns the newest requests first.
The `checkouts/model-relay` commit (`e80a2af`) is local and not pushed.

Still to verify, as above, once the opus run finishes: drops stay 0 (or
events only), and the relay's request count per job matches its API dumps.
Close the bug then.

## Supplemental local stress validation, 2026-10-13

The separate [full-filter reporting fix](../fixed/model-relay-telemetry-totals-follow-loaded-page.md)
has been implemented and deployed. Its tests reached actual 32, 128 and 256
concurrent synthetic streams on one CPU, with 100,000 historical rows and live
reporting readers. The new rollup writer exposed intermediate-event pressure at
the old 1,024-write threshold. Raising that bounded threshold to 8,192 preserved
all events in the final matrix; the request threshold remains 65,536.

All 39,680 requests across the final matrix and minute-crossing continuations
survived with zero dropped requests/events or storage errors. The continuation
cases independently counted all 195,840 expected SQLite events per case, as well
as raw request IDs and usage. This strengthens current writer evidence without
recovering older missing records or substituting for the historical per-job API
dump reconciliation requested above. No paid inference ran.

[Detailed evidence](../../notes/model-relay-telemetry-rollover.md#fix-and-stress-validation-2026-10-13).
