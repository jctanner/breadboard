# ADR-0013: Webhook Sink in Rust with SQLite

## Status

Accepted

## Context

The emulators send webhooks, but the stack has nowhere to receive them. We
need a sink that keeps deliveries durably and lets consumers pull new events
with a cursor. See [the task](../tasks/done/webhook-sink-service.md).

These options were considered:

| Option | Why not chosen |
| --- | --- |
| Off-the-shelf inboxes (webhook.site, smee, Convoy) | They are built for inspection or forwarding, not for polling as a queue. |
| A broker behind an adapter (NATS JetStream, Redis Streams) | It works, but adds a second service and client libraries for every consumer. |
| Kubernetes event routing (Argo Events, Knative) | Heavy, and overlaps with markovd. |
| A small purpose-built service | Chosen. |

Several languages were considered for the service:

- **Python (FastAPI):** matches the emulators, but costs an image of about
  150 MB or more and 60–100 MB of memory.
- **Go:** matches `deploy/golang-reverse-proxy/` and has a footprint close
  to Rust's.
- **Rust:** the smallest footprint, chosen at the project owner's
  preference.

## Decision

Implement the sink as a standalone Rust service:

- built with `axum` and `tokio`;
- storing events in SQLite in WAL mode, on a PVC;
- running as one replica;
- shipped as a static binary on a minimal image.

Storage sits behind a trait, so that the backend can change without
changing the HTTP API.

Move to Postgres or NATS JetStream only when one of these is needed:

- more than one replica, for availability;
- several consumers that each need server-side acks, redelivery, or dead
  lettering;
- durability beyond one PVC.

Event volume alone, including real GitHub traffic later, is not a reason to
move.

## Consequences

**Positive:**

- The image is expected to be about 5–15 MB, with an idle memory footprint
  of a few MB.
- Startup is close to instant.
- Consumers need only HTTP, with no broker client library.

**Negative:**

- This adds a third implementation language to the stack.
- Cold `cargo` builds are slow; the Containerfile must cache dependency
  layers.
- SQLite's single writer limits the sink to one replica until the backend
  changes.
