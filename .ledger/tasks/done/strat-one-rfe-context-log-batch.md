# Task: Start a one-RFE batch with latest entrypoint logging

## Goal

User requests a new batch job processing only one RFE.

## Preflight

Previous batch2065 succeeded; native discovery returned no eligible RFEs.
Seeded one fresh fixture RHAIRFE-8, unique marker
fullsend-entrypoint-poc-one-rfe-context-20261007. Native discovery size1/offset0
returns exactly8; no processed issues replayed or service data reset.

## Configuration

Batch discovery (not single-rfe mode), size1, offset0, expected key RHAIRFE-8.
Source43a6457 includes startup banner, workspace trust, per-invocation stderr
and visible initial architecture fetch. Fullsend bdedebeaf / Vertex Opus4.6.

## Acceptance

- [x] Exactly one clean eligible RFE selected.
- [x] Pipeline2067 created; batch4021 activated, pending on build4020.

## Status

Done: requested job started. Runtime outcome remains pending.

## Run

Pipeline2067, CI commit794d7f42cf4ce055917dda01155b7446adb3ba81.
Build4020 running; batch4021 pending, dashboard bridge4022 completed eagerly
(known emulator behavior). No diagnostic/single-rfe job selected.
