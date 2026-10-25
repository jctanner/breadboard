# Task: GitHub Emulator to Webhook Sink, End to End

## Goal

Show that a GitHub emulator event, such as an issue being created, reaches a
`webhook-sink` consumer with a valid signature.

## Blocked By

The GitHub emulator never fires repository webhooks: `trigger_webhooks()`
has no callers. See the emulator's ledger,
`checkouts/github-emulator/docs/bugs/open/repository-webhooks-are-never-delivered.md`.

## Acceptance Criteria

- [ ] A repository hook with `events: ["issues"]`, and the default sender
      token (`make host-webhook-sink-tokens`) as its secret, points at
      `http://webhook-sink.ai-pipeline.svc.cluster.local/hooks/github`.
- [ ] Creating an issue returns an `issues`/`opened` event to a consumer
      waiting on `GET /events?source=github&event=issues&wait=30`, with
      `sender.method` set to `hmac`.
- [ ] Creating the issue is not slowed by the delivery.
- [ ] `docs/webhook-sink.md` marks the GitHub emulator as delivering.

## Status

Blocked
