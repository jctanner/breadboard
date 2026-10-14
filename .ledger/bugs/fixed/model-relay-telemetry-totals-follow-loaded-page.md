# Bug: Model Relay telemetry totals follow loaded pages instead of the selected period

## Summary

The admin console's usage totals cover its loaded request rows. Initial load and
refresh retrieve only the newest 100 matches. New requests displace earlier rows,
and refreshing after Load more discards those older pages from the totals.
Long batch runs can therefore appear to roll over before completion.

## Source evidence

At relay commit `0a1ecbc`, `src/admin_ui/admin.js`:

- `telemetryQuery()` sets `limit=100` and `order=desc`.
- `loadTelemetry(false)` replaces `state.requests` with that page's items.
- `renderTelemetry()` sums only `state.requests`.
- Refresh and Apply filters call `loadTelemetry()` without the append flag.

The list, summary and export APIs are cursor-paginated. `telemetry::summary()`
summarizes a page and labels its scope as bounded. Database request rows are
upserted by request ID; no age- or count-based request deletion was found.

## Expected

The telemetry overview should show totals for the selected project/key/time
range independently of how many table rows are loaded. Table pagination and
overview totals should have explicit separate scopes.

## Verification

Confirmed locally on 2026-10-13 using the real mock relay and real console code.
The deployed JavaScript is byte-identical to the inspected source. At 150 stored
requests and 350 synthetic output tokens, the console displayed 100 requests and
200 tokens. Load more restored 150/350; Refresh with no new traffic returned to
100/200. All records survived a restart. Storage errors and dropped writes were
zero; no paid inference or deployed-data mutation occurred.

[Experiment, reproduction and observations](../../notes/model-relay-telemetry-rollover.md)
are recorded under the
[completed investigation](../../tasks/done/model-relay-telemetry-rollover.md).

## Initial proposed fix

Provide server-side totals across the selected filters independently of request
table pagination, with bounded query execution. Keep full-range summary scope
separate from loaded-row scope and verify Refresh and long-run accumulation.
The existing summary endpoint's bounded-page contract is documented; adding
true aggregates needs an explicit API contract. Raising the page limit alone
does not solve the reporting problem. No fix or deployment was made in this
investigation.

## Fixed and deployed, 2026-10-13

Added `/telemetry/aggregate` for all matching requests while preserving the old
bounded summary/list/export contracts. The console fetches overview totals
independently from table pages and labels both scopes. Indexed reporting rows
and global/minute totals commit with raw records; stream updates replace their
old contributions. Time boundaries remain inclusive and timezone aware. WAL,
bounded readers and the query timeout remain; a short bounded cache reduces
repeated reads.

The real console fixture keeps 150 requests and 450 synthetic output tokens
through Load more and Refresh. Stress tests reached 32, 128 and 256 measured
active streams on one CPU with 100,000 historical rows and reporting readers.
The final matrix and minute-crossing continuations passed for 39,680 requests,
with zero dropped requests/events, storage errors or aggregate failures.

Deployed through `make host-rebuild-relay`. All 4,859 existing requests, control
data and account credential files were preserved. Live aggregates match raw
SQLite totals; served console code matches source. No paid inference occurred.
[Implementation and stress evidence](../../notes/model-relay-telemetry-rollover.md#fix-and-stress-validation-2026-10-13).
