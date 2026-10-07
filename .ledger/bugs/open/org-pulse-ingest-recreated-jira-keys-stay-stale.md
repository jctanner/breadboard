# Org Pulse ingest retains stale flags on recreated Jira keys

## Summary

M8 strategy batch succeeded and Org Pulse bulk ingest reported two creations,
but AI Impact GET features/RHAISTRAT-2 and /RHAISTRAT-3 returned 404.
Canonical feature files contained the new reviews and run 20261006-223446,
while retaining _stale detectedAt timestamps from 2026-10-06 16:45 (after M5
Jira reset). feature-store rebuildIndex skips stale files.

## Evidence and cause

Batch 2053/3993: 2 created, 790 unchanged, 16 historical entry validation
errors; the new two rows were valid. Canonical files have sourceRfe 2/3 and
runId 20261006-223446. Their retained _stale timestamps hid the new data.
AI Impact ingest forwards to releases and calls refresh-all with handlers=[jira-sync].
The current core refresh-all handler does not honor that selector and uses
cadence unless force is supplied. Releases jira-sync has 12h cadence; its
last successful reset-era sync was too recent, so normal ingest did not
recover the keys immediately. This explains the apparent publication gap;
it was not a missing Vertex/model result.

## Recovery and remaining work

Use the existing admin POST /api/admin/refresh/handler with
handlerId=releases:jira-sync, which ignores cadence and reconciles current
Jira features. This reads Jira and updates Org Pulse only; it does not reset
Jira or repeat model work. M8 invoked that handler after confirming canonical
review data and valid live Jira issues. Verify per-feature GET latest/runId
after completion. Do not expose pod-internal proxy secrets or write data files
manually. Runtime recovery does not fix ingest/refresh scheduling behavior.

A durable follow-up should either reconcile a previously stale key on valid
new ingest or use the correct selected refresh-handler API. Add coverage for
Jira reset/key reuse and immediate readable feature data, preserving genuine
stale detection for absent Jira issues and existing human-review metadata.

## Related work

[M8 batch task](../../tasks/done/fullsend-strategy-batch-ci.md).
