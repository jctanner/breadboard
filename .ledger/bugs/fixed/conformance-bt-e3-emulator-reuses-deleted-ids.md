# Bug: GitHub emulator reuses the ids of deleted rows (BT-E3)

## Summary

The GitHub emulator gives a new row the id of the most recently deleted one.
Its models declare `primary_key=True, autoincrement=True`, and on SQLite
SQLAlchemy does not emit the `AUTOINCREMENT` keyword for that (it needs
`sqlite_autoincrement=True` on the table). SQLite then allocates
`max(rowid) + 1`, so deleting the newest rows frees their ids for reuse.
GitHub never reuses an id.

Found in BT-B3 (`.ledger/plans/fullsend-behaviour-tests-plan.md`). The
behaviour suite deletes every slot repository when it releases the slot,
which takes that repository's workflow runs and jobs with it.

## Reproduction

1. `make bt-run FEATURES=features/triage/triage.feature` (vendored). Its
   triage run is workflow run 1962, with jobs 8510 onwards, in
   `halfsend/test-repo-01`.
2. The suite releases the slot and deletes `halfsend/test-repo-01`.
3. `make bt-run FEATURES=features/triage/triage.feature FULLSEND_REF=main`.
   The new repository's triage run is again workflow run 1962, with jobs
   8510 onwards. The logs differ (only the first says "Using vendored
   binary"), so these are two different runs under one id.

## Expected

Ids are never reused, as on GitHub: a run, job, repository, issue or
artifact keeps its id after deletion and no later row receives it.

## Actual

The ids of deleted rows are handed out again. This applies to every
emulator table, since all of them share the declaration.

## Impact

Medium. T1 passes, because each scenario looks its run up afresh. But any
client that caches by id, or holds an id across a delete, can attach to a
different object. The behaviour suite creates and deletes repositories on
every lease, and a concurrent run (B4, concurrency 4) widens the window: a
run id still held by one scenario can be reused by another. Results are
also confusing to read, because two runs' artifacts share a directory name
(`debug-triage-run-1962`).

## Related Tasks

- `.ledger/plans/fullsend-behaviour-tests-plan.md` (BT-B3; fix before BT-B4
  raises concurrency)
- Fix belongs in `checkouts/github-emulator` (filed and fixed there, like
  BT-E1 and BT-E2)

## Resolution

Fixed 2026-11-07 in github-emulator `b987b79` ("Never hand out the id of a
deleted row"); the emulator's record is
`docs/bugs/fixed/deleted-rows-ids-are-handed-out-again.md`.

- **Models.** Every model table is declared `sqlite_autoincrement`
  (`app/models/__init__.py`).
- **Migration 0016.** It rebuilds each existing table that lacked
  `AUTOINCREMENT`, as 0011 did for `repositories`.

Deployed with `make host-rebuild-github`. The live database went from 0015
to 0016 at startup. Every table except `gists` (string ids) is
`AUTOINCREMENT`, and `PRAGMA integrity_check` is `ok`. Before deploying, a
backup was taken to `/data/github_emulator.pre-0016.db` in the emulator
volume. A copy of that database upgraded with identical reflected schema
and row counts.

Live check, with two consecutive `make bt-run
FEATURES=features/triage/triage.feature`:

- run 1 got workflow run 1962 and jobs 8510 onwards. 1962 had been deleted
  before the migration, above the highest id left (1956), so it could not
  be protected; the record says so.
- run 2, after run 1's slot repository was deleted, got run 1971 and jobs
  8600 onwards. Before the fix it would have taken the deleted ids again.
