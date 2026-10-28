# Task: Webhook Sink Service

## Goal

Add a small, resettable webhook sink, `webhook-sink.local`, written in Rust.
It accepts webhook deliveries from the emulators and keeps them durably.
Consumers pull new events with a cursor, instead of each one running its
own HTTP receiver.

## Context

The GitHub emulator sends GitHub-style webhooks:

- the headers are `X-GitHub-Event`, `X-GitHub-Delivery`, and
  `X-Hub-Signature-256` when the hook has a secret;
- `src/app/services/webhook_service.py` makes the delivery;
- it records each attempt as a `WebhookDelivery` row.

The Jira emulator has webhook models too. Nothing in `deploy/k8s/` receives
these deliveries, so hooks have nowhere to point.

The GitHub emulator delivers inline, with a 30-second `httpx` timeout, while
handling the triggering request. A slow receiver therefore slows the
emulator's API, so the sink must answer quickly.

Real GitHub webhooks are an expected later source, but are out of scope
here. Design choices that keep that step cheap are part of this task; see
"Later: real GitHub".

The choice of Rust, and the conditions for outgrowing SQLite, are in
[ADR-0013](../../decisions/ADR-0013-webhook-sink-in-rust.md).

## Design

**Stack:**

- `axum` on `tokio`;
- SQLite through `sqlx` or `rusqlite`, in WAL mode, on a PVC;
- `hmac` and `sha2` for signature checks;
- a static musl binary on a `scratch` or distroless image.

**Storage:** one `events` table.

| Column | Notes |
| --- | --- |
| `seq` | Integer primary key, autoincrement. This is the consumer cursor. |
| `channel` | The path segment the event was posted to. |
| `source` | `github`, `gitlab`, `jira` or `generic`, derived from the headers. |
| `delivery_id` | `X-GitHub-Delivery` or an equivalent. Unique per channel when present. |
| `event` | `X-GitHub-Event`, `X-Gitlab-Event`, or the Jira `webhookEvent`. |
| `received_at` | UTC timestamp. |
| `headers` | JSON object, exactly as received. |
| `body` | Raw bytes, exactly as received, never re-encoded. |
| `signature_valid` | Nullable boolean; null when the channel has no secret. |

Keep storage behind a small trait, so that a Postgres or NATS JetStream
backend can replace SQLite later without changing the HTTP surface.

**HTTP surface:**

| Method and path | Behavior |
| --- | --- |
| `POST /hooks/{channel}` | Verify the signature if the channel has a secret, insert, commit, wake waiters, then return `202`. Return `401` on a bad signature for a channel with a secret, and `413` when the body exceeds the cap (default 25 MB, GitHub's maximum). A duplicate `delivery_id` returns `200` without inserting. |
| `GET /events?channel=&after=<seq>&limit=&wait=<s>` | Return events with `seq > after` in ascending order, plus `next_after`. When there are none and `wait` is set (capped at, say, 60 s), wait for an insert on that channel before answering. |
| `GET /events/{seq}` | Return one event, with the raw body available, for example `?raw=1` returning the original content type. |
| `DELETE /events[?channel=]` | Reset, for demos and test runs. |
| `GET /channels` | List channels with their counts and latest `seq`. |
| `GET /healthz` | Liveness and readiness. |

**Long-poll:** keep one `tokio::sync::Notify` (or a `watch` channel) per
channel.

- Query first.
- If nothing is newer than `after`, wait on the notifier until `wait`
  expires, then query again.

Consumers keep their own cursor. Server-side consumer groups and acks are
out of scope.

**Configuration:**

- Channel secrets come from a Kubernetes Secret, mounted or passed as
  environment variables, never a ConfigMap.
- Retention is a maximum age and/or maximum row count, enforced by a
  background task.
- The listen address and database path come from the environment.

## Deployment

- **Code location:** a separate project at `checkouts/hooksink`.
  It has its own git repository, like the emulators, and is ignored by
  Breadboard.
  - Give it its own `AGENTS.md`, `PLAN.md` and ledger.
  - Breadboard keeps only the deployment wiring.
  - The project is branded hooksink. Its remote is
    `git@github.com:jctanner/hooksink.git`, and
    `deploy/scripts/00-clone-component-repos.sh` clones it to
    `checkouts/hooksink`. (Renamed from `checkouts/webhook-sink-service` on
    2026-10-26.)
  - Kubernetes resources and hostnames were `webhook-sink` until
    2026-10-26; see "Renamed to hooksink" below.
- **Image:** a multi-stage Containerfile that caches dependency builds
  (for example with `cargo-chef`), so a source-only change rebuilds in
  seconds.
- **Manifest:** `deploy/k8s/31-webhook-sink.yaml`, holding:
  - a Deployment with one replica, because SQLite has a single writer;
  - a Service;
  - the PVC;
  - the secret reference;
  - probes.
- **Routing:** add `webhook-sink.local` in each of these places:
  - `deploy/k8s/02-certificates.yaml`
  - `deploy/k8s/08-ingress-https.yaml`
  - `deploy/golang-reverse-proxy/deployment.yaml`
  - `deploy/k8s/22-fullsend-networking.yaml`, if sandboxes need to reach it
- **Rebuild target:** `make host-rebuild-webhook-sink`, which builds,
  imports, applies the manifest, then restarts, so that it also works on a
  first deploy.
- **Full deploy:** add the sink to `deploy/scripts/deploy-all.sh` and the
  `CLAUDE.md` service tables.
- **In-cluster URL:** emulator hooks use
  `http://webhook-sink.ai-pipeline.svc.cluster.local/hooks/<channel>`.

## Acceptance Criteria

- [x] The service builds as a static binary: a 2.23 MB `scratch` image, with
      about 1 MB of RSS when idle.
- [x] Tests cover these cases, as 10 unit tests and 14 HTTP tests:
  - [x] a valid signature;
  - [x] a bad signature;
  - [x] a channel without a secret;
  - [x] a duplicate delivery ID;
  - [x] cursor paging;
  - [x] a long-poll wake;
  - [x] a long-poll timeout;
  - [x] the body cap;
  - [x] retention trimming;
  - [x] reset.
- [x] Bodies are stored byte for byte. A test re-verifies a stored event's
      signature from its stored headers and raw body.
- [x] Deployed through `make host-rebuild-webhook-sink` with no prior
      manifest applied.
- [ ] **Not met; moved to a blocked follow-up.** End to end: a GitHub
      emulator repo hook records an `issues` event after an issue is
      created. The emulator never fires hooks; see
      [the follow-up](webhook-sink-github-emulator-e2e.md). Its
      delivery code, called directly, does reach the sink with a valid
      signature.
- [x] End to end: a long-poll consumer started before the event receives it
      without re-polling. Shown with the Jira emulator.
- [x] A Jira emulator webhook delivery is recorded under its own channel.
- [x] The sink answers in milliseconds. The emulator's `deliver_webhook`
      measured 0.11 s, including creating its HTTP client.
- [x] `docs/webhook-sink.md` exists and is linked from `docs/README.md`.

## As Built

These differ from the design above:

- **Raw bodies** are served at `GET /events/{seq}/raw`, not `?raw=1`.
- **Channel secrets** are files in a mounted optional Secret,
  `webhook-sink-secrets`, one key per channel, reread on every delivery.
- **Long-poll** uses one global `watch` channel instead of one per
  channel; waiters query again for their own channel.
- **Header redaction:** the `X-Gitlab-Token`, `Authorization` and `Cookie`
  values are stored as `[redacted]`, because GitLab's token is the channel
  secret itself.
- **Optional API token:** `WEBHOOK_SINK_API_TOKEN` guards the consumer
  endpoints, but not `/hooks` or `/healthz`.
- **Deploy script numbers:** the build script is `05n`, and the deploy
  script is `28-deploy-webhook-sink.sh`.
- **Port:** the Service listens on port 80.
- **Routing:**
  - The host proxy terminates TLS and forwards plain HTTP to the sink, as
    it does for Model Relay.
  - The changes are a route in `deploy/golang-reverse-proxy/main.go`, a
    name on the proxy certificate, and a CoreDNS rewrite.
  - No Traefik ingress or separate certificate was added.
- **Jira emulator:** `deploy/k8s/12-jira-emulator.yaml` now sets
  `WEBHOOK_ALLOW_INSECURE_HTTP=true`. Without it, the emulator rejects
  `http://` webhook URLs. Its `WEBHOOK_ALLOW_PRIVATE_NETWORKS` setting is
  defined but never read.
- **Clone script:** clones `git@github.com:jctanner/hooksink.git` to
  `checkouts/hooksink` (added 2026-10-26, once the remote existed).

## Later: real GitHub (out of scope)

The design above covers, from the start:

- raw storage;
- delivery ID dedupe;
- store-then-respond;
- cursor semantics that map onto JetStream sequence numbers;
- secrets in a Secret.

Receiving from real GitHub then adds:

- **Ingress:** a public endpoint or tunnel with TLS, such as cloudflared or
  ngrok, or a hosted edge buffer such as Hookdeck.
- **Hardening:**
  - mandatory signatures on every public channel;
  - optionally, an allowlist of the hook ranges from `api.github.com/meta`;
  - rate limiting.
- **A reconcile job:** GitHub expects a 2xx within 10 seconds and does not
  redeliver failures automatically. The job lists recent deliveries through
  the GitHub API and redelivers the ones that failed.

Move to Postgres or JetStream only under the conditions in ADR-0013.

## Files Likely Involved

- `checkouts/hooksink/` (new project; its own repository)
- `deploy/scripts/00-clone-component-repos.sh`
- `deploy/k8s/31-webhook-sink.yaml` (new)
- `deploy/k8s/02-certificates.yaml`
- `deploy/k8s/08-ingress-https.yaml`
- `deploy/golang-reverse-proxy/deployment.yaml`
- `deploy/scripts/deploy-all.sh`
- `Makefile`
- `CLAUDE.md`
- `docs/README.md`

## Status

Done, except the GitHub end-to-end criterion, which is blocked on the GitHub emulator.

## Validation

All of this was done on 2026-10-25, on the host k3s cluster (p15.lab.net).

**Build checks:**

- `cargo test` passes all 24 tests: 10 unit and 14 HTTP.
- The image build runs `cargo fmt --check`, `cargo clippy --all-targets
  -D warnings` and the tests, and fails on any of them.

**Bug found and fixed during a local smoke test:** a duplicate delivery
consumed an AUTOINCREMENT value, so `seq` went from 1 to 3. The store now
checks for the delivery first, and a unit test asserts there is no gap.

**Jira end to end:**

- An admin webhook for `jira:issue_created`, with a secret, pointed at
  `/hooks/jira-e2e`. A consumer was already waiting with `wait=20`.
- Creating `TEST-1` returned the event after 1.33 s. It had `source=jira`,
  the Atlassian delivery ID, and `signature_valid: true`.
- The HMAC re-verified from `/events/1/raw`.

**GitHub delivery code:**

- `deliver_webhook()` was run inside the emulator pod against a hook on
  `/hooks/github-e2e` with a secret.
- The sink answered 202 with `seq` 2. The event had `source=github`,
  `event=issues`, and `signature_valid: true`.

**Host access:**

- After `make host-rebuild-ingress-proxy`,
  `https://webhook-sink.local/channels` answered through the proxy.
- `github.local`, `dashboard.local` and `relay.local` still answered.

**Pod usage:** `kubectl top` showed about 1m CPU and under 1 MiB of
memory.

**Test data left in place:**

| Where | What |
| --- | --- |
| GitHub emulator | Repository `admin/webhook-e2e-*` and its hook |
| Jira emulator | Issue `TEST-1` and the `sink-e2e-*` webhook |
| `webhook-sink-secrets` | Keys `github-e2e` and `jira-e2e` |
| Sink | Two events |

## Follow-up: tokens and admin console (2026-10-25)

The design above has been superseded by
`checkouts/hooksink/docs/decisions/ADR-0002-sender-tokens-are-signing-secrets.md`.

**What changed:**

- Every delivery needs a sender token. A sender token's value is the
  webhook signing secret: the sink identifies the token by its HMAC.
  `X-Gitlab-Token`, Bearer, and `?token=` are accepted for senders that
  cannot sign.
- Every read needs a consumer token, given as a Bearer token.
- Per-channel secrets and `WEBHOOK_SINK_API_TOKEN` are gone.
- An admin console and API, like Model Relay's, run on a separate admin
  listener at `webhook-sink-admin.local`. They issue, rotate and revoke
  tokens, and browse and reset events. Consumers can no longer reset
  events.
- Default sender and consumer tokens, plus the admin key, live in the
  Secret `webhook-sink-tokens`. The deploy script creates it, and
  `make host-webhook-sink-tokens` prints the values.
- Bucketing is by query-time filters, `channel`, `source`, `event` and
  `sender`, not stored topics, as the user chose.

**Evidence:** recorded in
`checkouts/hooksink/docs/tasks/done/admin-console-and-tokens.md`.

- Jira delivered TEST-2, signed with the default sender token. A consumer
  long-polling with a filter, using the default consumer token, received
  it after 1.64 s.
- The GitHub emulator's delivery code was accepted the same way.
- The console was exercised in headless Chrome, including at phone width.

**Test data:**

- The `webhook-sink-secrets` Secret, created for the earlier test, was
  deleted.
- The Jira `sink-e2e-*` webhook was replaced by `webhook-sink-jira-*`,
  whose secret is the default sender token, on channel `jira`.
- The GitHub test hook now posts to channel `github` with the default
  sender token.
- The console check issued two `ui-check` sender tokens and revoked both.

## Follow-up: admin key and insecure reveal mode (2026-10-25)

**Admin key:** it defaults to `admin`, as Model Relay's does. The default
sender and consumer tokens stay random. On the existing cluster, only
`admin-key` in `webhook-sink-tokens` was changed, so existing tokens and
hooks were unaffected. Verified: `admin` gets 200, and the old random key
gets 401.

**Insecure reveal mode:** the manifest sets
`WEBHOOK_SINK_INSECURE_REVEAL_TOKENS=true`, so the console can show and
copy token values; see the project's ADR-0003. In headless Chrome on the
cluster:

- the revealed default consumer value matched the Secret's;
- the copied default sender value matched the Secret's.

## Follow-up: host and repository filters (2026-10-25)

Consumers can filter with `host=` and `repo=`. A `repo` value ending in
`*` matches by prefix, such as `org/*`. The sink reads both from each
payload when it stores the event, and older events were backfilled once.
See `checkouts/hooksink/docs/tasks/done/host-and-repo-filters.md`.

After deploying, these filters were checked through
`https://webhook-sink.local`:

| Filter | Result |
| --- | --- |
| `host=github.local` | the four GitHub emulator events |
| `repo=admin/*` | the four GitHub emulator events |
| `host=jira.local&repo=TEST` | the two Jira events |
| `host=github.com` | nothing |

## Renamed to hooksink (2026-10-26)

The project is branded hooksink, and Breadboard now uses that name
throughout:

- Checkout `checkouts/hooksink`, cloned from
  `git@github.com:jctanner/hooksink.git`.
- Deployment, services, PVC and Secret: `hooksink`, `hooksink-admin`,
  `hooksink-data`, `hooksink-tokens`; image `hooksink:latest`.
- Hostnames `hooksink.local` and `hooksink-admin.local` (proxy routes,
  certificate names, the CoreDNS rewrite file and `/etc/hosts`).
- Files `deploy/k8s/31-hooksink.yaml`, `deploy/scripts/05n-build-hooksink.sh`,
  `deploy/scripts/28-deploy-hooksink.sh`, `docs/hooksink.md`; Make targets
  `host-rebuild-hooksink`, `host-logs-hooksink`, `host-hooksink-tokens`;
  override variables `HOOKSINK_DIR`, `HOOKSINK_ADMIN_KEY`,
  `HOOKSINK_DEFAULT_SENDER_TOKEN`, `HOOKSINK_DEFAULT_CONSUMER_TOKEN`.
- The program's environment variables were renamed in hooksink itself from
  `WEBHOOK_SINK_*` to `HOOKSINK_*`, and the manifest follows. The
  `whs_`/`whc_` token prefixes are unchanged.
- The hooksink package, binary and console are named hooksink too, and the
  redeployed pod logs `hooksink listening`; `GET /` reports
  `"service": "hooksink"`.

Migration on p15: the old pod was scaled to zero, `events.sqlite` copied into
`hooksink-data`, and the Secret's values copied into `hooksink-tokens`, so
events and issued tokens carried over. The three GitHub repository hooks and
the Jira webhook were repointed to
`http://hooksink.ai-pipeline.svc.cluster.local/hooks/<channel>` with their
secrets kept; a signed GitHub ping was accepted (202). The old resources and
image were then deleted.
