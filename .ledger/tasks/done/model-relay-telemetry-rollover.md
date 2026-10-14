# Task: Verify Model Relay telemetry rollover without inference

## Goal

Investigate apparent telemetry rollover during long batch runs using local
synthetic fixtures, with no paid model calls and no deployed data changes.

## Acceptance criteria

- [x] Inspect storage, pagination, summary APIs and console refresh behavior.
- [x] Reproduce the display behavior against the real local relay and console code.
- [x] Distinguish missing stored records from page-limited reporting.
- [x] Record evidence, scope and a proposed fix in the ledger.
- [x] Keep existing credentials, deployments and unrelated work unchanged.

## Status

Done, 2026-10-13. Relay checkout remains clean at
`0a1ecbc96eade9891f9858b5ff7b78b73b1dc73c`.

## Initial finding

The console uses `limit=100&order=desc`, replaces loaded rows on refresh and
calculates all displayed token totals from those rows. Load more appends rows,
but a subsequent refresh returns to the newest page. The summary API also
explicitly summarizes one bounded page. No request retention/deletion mechanism
was found in the storage code.

## Verification

- [Experiment and runnable reproduction](../../notes/model-relay-telemetry-rollover.md)
  use the current compiled binary, isolated mock backend, temporary SQLite and
  fixture credentials. No provider calls or model processes ran.
- At 150 stored requests / 350 synthetic output tokens, the console's first
  page shows 100 / 200. Load more reaches 150 / 350; refreshing without new
  traffic returns to 100 / 200. An accelerated five-hour fixture, full cursor
  pagination and process restart preserve all records and total usage.
- Deployed admin.js matches the tested source byte-for-byte. Read only its public
  static asset; no production credentials or telemetry were fetched or changed.
- Four existing Rust telemetry tests pass. JavaScript syntax, Python compilation,
  local documentation links and git diff --check pass. This investigation does
  not edit the session log; concurrent planning entries are preserved.
- Local socket sandbox restrictions required approval to run the isolated test;
  its child environment contains only mock settings. Temporary processes/state
  are cleaned up. No relay source change, deployment, commit or push.
- Proposed fix is separate server-side aggregate reporting with paginated rows;
  the [reporting bug, now fixed](../../bugs/fixed/model-relay-telemetry-totals-follow-loaded-page.md)
  remains open. The unrelated untracked pi-provider plan is preserved.
