# Model Relay telemetry rollover: local verification

Initial finding verified 2026-10-13 against relay commit
`0a1ecbc96eade9891f9858b5ff7b78b73b1dc73c`. The fix and subsequent validation are
recorded at the end of this note; baseline observations below describe the old code.

## Finding

The console's totals follow the newest **100 loaded requests**, rather than all
requests in the selected period. Older rows fall out as new requests arrive.
Load more restores older rows, but Refresh replaces them with the newest page.
This reproduces apparent rollover during a batch without deleting stored data.

The JavaScript served by `relay.local/admin/admin.js` matches the inspected
checkout exactly: SHA-256
`361602f247a461e2094bdc2f4cf6f83e113572163b19eb42621bcfd5a60cdfd5`.
Fetching that public static asset required no admin credential or inference call.

## Local experiment

Started the real compiled relay with `SHIM_BACKEND=mock`, loopback listeners,
a temporary SQLite database and generated fixture credentials. Provider settings
were excluded from its environment, and the model executable was `/bin/false`.
The fixed-response mock accepted 150 requests; no Claude process or provider
inference ran. The real console JavaScript executed in Node with a minimal DOM,
empty filters and reads from that isolated relay's real API.

The first 100 requests reported three synthetic output tokens each; the next 50
reported one each. Fixture timestamps were then spread across 298 minutes to
represent nearly five hours of history without waiting. These are synthetic
usage fields, not purchased tokens.

| Action | Requests stored | Output tokens stored | Requests displayed | Output tokens displayed |
| --- | --- | --- | --- | --- |
| Initial 100 requests | 100 | 300 | 100 | 300 |
| Add one request | 101 | 301 | 100 | 298 |
| Reach 150 requests | 150 | 350 | 100 | 200 |
| Load every page | 150 | 350 | 150 | 350 |
| Refresh with no new requests | 150 | 350 | 100 | 200 |

All 150 unique requests and all 350 synthetic output tokens were available
through cursor pagination. They also remained in SQLite after restarting the
local relay. Pending writes, dropped requests/events and storage errors were
all zero before restart. This example rolls over at request 101, independently
of elapsed time; it does not require a timed retention policy.

The summary API returns 200 output tokens for the first page and a continuation
cursor. Its documented contract explicitly says it summarizes a bounded page;
it is not an aggregate endpoint for the entire filtered history.

## Reproduction and checks

These commands reproduce the pre-fix baseline and require that revision's binary
and console source. From the Breadboard root at that baseline:

```bash
cargo build --offline --manifest-path checkouts/model-relay/Cargo.toml
python3 .ledger/notes/assets/model-relay-telemetry-rollover/reproduce.py
```

The script starts and stops its own local relay, removes its temporary state,
and prints sanitized observations. Local socket access must be permitted.
It never connects to the deployed relay or loads personal provider credentials.

- [Reproduction script](assets/model-relay-telemetry-rollover/reproduce.py)
- [Console probe](assets/model-relay-telemetry-rollover/console_probe.js)
- [Recorded observations](assets/model-relay-telemetry-rollover/observed.json)
- [Reporting bug, now fixed](../bugs/fixed/model-relay-telemetry-totals-follow-loaded-page.md)

The four existing Rust telemetry tests passed with
`cargo test --offline telemetry::tests::`. The new JavaScript syntax check,
Python compile check and git diff --check pass. Relay source remains unchanged.
No deployment or paid model call occurred.

## What to change

Compute overview totals over the full selected project/key/time range on the
server, independently of table pagination. Keep the request table paginated,
label the two scopes clearly and test that Refresh preserves full-range totals.
The aggregate implementation must preserve the relay's bounded query execution
and concurrent streaming behavior; merely raising the page limit postpones the
same rollover.

For now, traverse all cursor pages before calculating a run total. In the console,
Load more must reach the end, and another Refresh returns to the first page.
The default From value is the previous 24 hours when the page opens, another
display filter to consider when reviewing older runs.

This verifies a reporting limitation in the deployed console code. It does not
audit every historical production record or requalify the separate high-load
writer-loss issue. The experiment did not mutate deployed telemetry, credentials
or routing.

## Fix and stress validation, 2026-10-13

Implemented and deployed a separate full-filter aggregate endpoint. Console
overview totals now use it while the request table remains cursor-paginated.
The existing bounded summary API keeps its contract. Raw snapshots, indexed
reporting rows and global/minute rollups update atomically; exact partial-minute
boundaries retain the original timestamp semantics. Reads keep their timeout and
bounded worker limits, with a one-second, 64-selection cache.

Testing found and corrected two additional issues before deployment: full-history
aggregate scans exceeded the read budget under load, and the old 1,024-write event
threshold shed intermediate snapshots. Maintained rollups remove the scan; an
8,192-write event threshold absorbs the measured bursts. Request-write limits
remain unchanged.

The final matrix used 100,000 legacy historical rows, one-CPU relay affinity,
128 KiB request content, 32 fixture keys and actual active-stream peaks of 32,
128 and 256. With and without four reporting readers, all 16,640 requests and
1,028 aggregate reads succeeded. Zero requests or usage events were dropped;
all writer queues drained without storage errors. At 256 streams with readers,
aggregate p95 was 48.43 ms (including cache hits) and sampled peak RSS was
122.59 MiB. Independent raw-record totals and restart checks passed.

Two longer 128-client cases crossed minute boundaries. Each retained all 11,520
new requests, all 100,000 historical rows and exactly 195,840 usage events;
another 1,445 reporting reads succeeded. Successful stress traffic totals 39,680
requests and 2,473 aggregate reads. The fixture's historical timestamp/run is
uniform; this is not a high-cardinality history test or a multi-hour production
soak. Memory was measured, not capped. No upstream-provider capacity claim is made.

The required `make host-rebuild-relay` completed after a private consistent
SQLite backup. All 4,859 deployed raw requests, control data and account credential
files were unchanged after rollout. Live aggregate generation totals matched
raw SQLite, integrity checking passed, and served console code matched source.
No paid provider calls or deployed inference occurred. Rust's 37 tests, fmt and
clippy, plus frontend/Python/shell checks and diff checking, passed.

Current acceptance command: `checkouts/model-relay/scripts/test-telemetry.sh`.
Reusable stress tooling and full evidence are in the component:

- [Stress script](../../checkouts/model-relay/tests/stress_telemetry.py)
- [Detailed results](../../checkouts/model-relay/.ledger/notes/telemetry-aggregates-stress-results.md)

These links point into an ignored component checkout. Its own repository records
the implementation; the sanitized summary above stays in Breadboard's ledger.
