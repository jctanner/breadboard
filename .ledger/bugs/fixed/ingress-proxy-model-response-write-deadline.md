# Bug: Host ingress proxy cuts long model responses at 120 seconds

## Reproduction

The authorized SME local-refinement test uses native Claude 2.1.296 and the
managed Opus 4.6 relay client through the host ingress proxy. Long API responses
repeatedly end near 120 seconds; Claude logs ECONNRESET and partial-response
recovery, then exhausts native retries. The artifact and Jira remain unchanged.

The Go proxy configures WriteTimeout=120s on both HTTP and HTTPS servers. That
is an absolute response deadline, not a streaming idle timeout. Its shared
upstream transport also has a 120s response-header deadline. Dedicated model
inference routes need to let relay/provider timeouts and client cancellation
govern long responses, while ordinary console routes retain their defaults.

## Evidence

Local refinement: 2026-10-19 13:57:54–14:35:58 UTC, candidate 6ed858b. Relay rows
for sme-local-refine-20261019 show HTTP 200, upstream vertex-strat-evals,
completion=cancelled near 120–121 seconds. Claude ends with ECONNRESET after
ten streaming retries and a nonstream fallback. No new paid run was launched.

Private evidence is staged under /tmp/strat-sme-flow-20261019 and copied under
var/run-data/fullsend-claude-workflow/sme-loop-20261019. The first archive's
verification honestly fails on copied absolute latest symlinks; preserve it
and create a separate link-as-metadata capture.

## Impact and repair

This blocked local SME qualification. A delayed mock upstream reproduced all
eight original HTTP/HTTPS streaming/nonstream cases as failures. The repair
clears the absolute frontend response deadline and upstream header deadline
only for relay-api.local and the internal model-relay service hostname.
Other console/service routes retain their deadlines. Upstream cancellation
still follows a disconnected client.

Go race tests pass for HTTP, HTTPS and negotiated HTTP/2, delayed nonstream
responses, console deadline preservation and client cancellation. Deployed
with make host-rebuild-ingress-proxy; both ready replicas run image
6f9972561763118fcc031f81ea92a5a6661ae731309d01979712b68ae1329b89.

The explicit SME continuation on the same source/model started 17:00:30 UTC.
Its 17:01:39 API request completed around 17:04:16 with tool_use and 7,027
output tokens, beyond the old 120s cap. Inference vhost and backend routing are
confirmed in the deployed proxy logs. This qualifies the transport repair;
SME content/refinement/review/CI acceptance remains a separate task.

The original failed attempt is preserved. The replacement link-as-metadata
capture at local-refine-failed-links-recorded-20261019T163135.528241Z passes
both initial and independent checksum verification. Old ingress replica logs
were not captured before rollout; do not claim those logs were recovered.
