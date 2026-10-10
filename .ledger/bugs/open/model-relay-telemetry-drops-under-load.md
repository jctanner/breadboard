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
