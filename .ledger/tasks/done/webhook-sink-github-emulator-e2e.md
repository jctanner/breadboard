# Task: GitHub Emulator to Webhook Sink, End to End

## Goal

Show that a GitHub emulator event, such as an issue being created, reaches a
`webhook-sink` consumer with a valid signature.

## Was Blocked By

The GitHub emulator never fires repository webhooks: `trigger_webhooks()`
has no callers. See the emulator's ledger,
`checkouts/github-emulator/docs/bugs/open/repository-webhooks-are-never-delivered.md`.

## Acceptance Criteria

- [x] A repository hook with `events: ["issues"]`, and the default sender
      token (`make host-webhook-sink-tokens`) as its secret, points at
      `http://webhook-sink.ai-pipeline.svc.cluster.local/hooks/github`.
- [x] Creating an issue returns an `issues`/`opened` event to a consumer
      waiting on `GET /events?source=github&event=issues&wait=30`, with
      `sender.method` set to `hmac`.
- [x] Creating the issue is not slowed by the delivery.
- [x] `docs/webhook-sink.md` marks the GitHub emulator as delivering.

## Status

Done (2026-10-25).

## Validation

The emulator fix is in
`checkouts/github-emulator/docs/bugs/fixed/repository-webhooks-are-never-delivered.md`.
It was deployed with `make host-rebuild-github`.

A repository hook, with the default sender token as its secret, posted to
`/hooks/github`.

- **Deliveries:** creating an issue delivered `issues`/`opened`; a comment
  delivered `issue_comment`/`created`; a pull request delivered
  `pull_request`/`opened`. The hook's ping arrived too.
- **Attribution:** the sink attributed each delivery to `default-sender`,
  method `hmac`.
- **Consumer:** one long-polling `source=github` received them.
- **Speed:** issue creation took 0.068 s, with delivery in the background.
- **Hook status:** the hook's `last_response` was 202 OK.

The test hook used `/hooks/github`, not the `channel=github` filter this
task first named; the `source=github` filter covers the same check.
