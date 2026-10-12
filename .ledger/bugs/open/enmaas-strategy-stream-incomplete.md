# Bug investigation: Incomplete/cancelled EnMaaS stream during GLM review

## Evidence

Single authorized S2 run `markov-run-428f237a`, job
`script-strategy-entrypoint-all-glm-5-3-1011-233753-27ed46`, completes and
passes the single-RFE smoke checks. Its stream path is not uniformly clean:

- Relay `16e8d603-1e7d-44ee-8774-6e21a87a9fc7`: HTTP 200,
  `incomplete_upstream_stream`, 48381 ms, starts 2026-10-11 23:55:12.463 UTC.
- Relay `06e2b7fa-ed2f-4eb9-bbf6-3ef0eaa7edad`: HTTP 200,
  cancelled after 323979 ms, starts 23:58:29.875 UTC. This is not evidence
  of a configured 600-second relay timeout; do not infer cancellation cause.
- Streaming request `42606e7c-77da-4ea7-84d0-3c479a3dcf9b.request.json`
  and non-streaming request `929c9558-d65b-412b-a509-22bd209e965b.request.json`
  have identical messages and every field except `stream`.
- The non-stream response `3ac9d502-e5b5-4b25-87c0-97a1cb99d9e9.response.json`
  is indexed at 2026-10-12 00:04:37.094 UTC: model echoes exact hosted ID,
  stop_reason=tool_use, 3584 output tokens. All calls remain on GLM/EnMaaS.

## Impact and limits

The client recovers inside the existing benchmark attempt; no new iteration
was submitted. API response-only error counters report zero despite incomplete
relay streams and unpaired requests. Use relay completion/usage status and
request-response pairing alongside HTTP status and the smoke result.

Root cause is unresolved: distinguish actual upstream truncation, relay SSE
observation/parsing and client cancellation/fallback behavior using retained
evidence. Do not attribute this to the old 120-second timeout or account HTTP
429. S1's GLM run had no relay stream errors. No mid-run provider/design changes.

Final archive: `var/run-data/strat-workflow/markov-run-428f237a/`; original
API indexes, strace, service logs and relay records are retained for follow-up.
