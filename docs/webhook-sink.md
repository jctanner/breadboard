# Webhook Sink

The webhook sink (`checkouts/webhook-sink-service`) is a small Rust service.
It stores webhook deliveries from the emulators, and consumers read them back
by cursor and filters, optionally long-polling for new ones. Every delivery
needs a sender token, and every read a consumer token. An admin console
issues and revokes those tokens.

The project's README is the reference for the API; this page covers how
Breadboard runs it.

## Endpoints

| Name | Purpose |
| --- | --- |
| `https://webhook-sink-admin.local/admin/` | Admin console: tokens, events, channel resets |
| `http://webhook-sink.ai-pipeline.svc.cluster.local/hooks/<channel>` | Webhook URL for in-cluster senders |
| `http://webhook-sink.ai-pipeline.svc.cluster.local/events?source=github&after=<seq>&wait=30` | Consumer long-poll, with filters |
| `https://webhook-sink.local` | The public API from the host |

Both `.local` names route through the host proxy. Inside the cluster they
resolve through the CoreDNS rewrites in
`deploy/k8s/22-fullsend-networking.yaml`. On the host, add both to
`/etc/hosts`, next to the other `*.local` names:

```text
192.168.1.115 … webhook-sink.local webhook-sink-admin.local
```

The admin API is served only on the admin listener, so the public name never
exposes token management.

## Tokens

`28-deploy-webhook-sink.sh` creates the Secret `webhook-sink-tokens` once,
when it is missing, with these keys:

| Key | Use |
| --- | --- |
| `admin-key` | Signing in to the console. It defaults to `admin` for local development, as Model Relay's does. |
| `default-sender-token` | Random `whs_…` value: paste it as a hook's secret |
| `default-consumer-token` | Random `whc_…` value: send it as `Authorization: Bearer` when reading events |

To set your own values instead, set `WEBHOOK_SINK_ADMIN_KEY`,
`WEBHOOK_SINK_DEFAULT_SENDER_TOKEN` and `WEBHOOK_SINK_DEFAULT_CONSUMER_TOKEN`
before the first deploy. To print the values:

```bash
make host-webhook-sink-tokens
```

At startup the sink makes the Secret's tokens the defaults. Issue further
tokens for individual senders and consumers in the console. Each value is
shown once; rotate a token if its value is lost.

Breadboard runs the sink in **insecure reveal mode**
(`WEBHOOK_SINK_INSECURE_REVEAL_TOKENS=true` in the manifest). The console's
token views offer **Show** and **Copy** for every active token, so you can
copy a token from the console instead of from the Secret. For a shared
deployment, set it to `false`; the sink then stores consumer tokens as
fingerprints only.

A default token revoked in the console stays revoked. To replace it, put a
new value in the Secret and restart the sink.

## Senders

A sender token is also the webhook signing secret, so hooks authenticate in
the way the sender already supports:

| Emulator | Status | Setup |
| --- | --- | --- |
| Jira | Delivers | `POST /rest/webhooks/1.0/webhook` with `url`, `events`, and `"secret": "<sender token>"`. Jira signs with `X-Hub-Signature`. The deployment sets `WEBHOOK_ALLOW_INSECURE_HTTP=true`, so the emulator accepts the sink's `http://` URL. |
| GitHub | **Does not deliver yet** | Create the hook with `config.secret` set to a sender token. The emulator never fires hooks; see `checkouts/github-emulator/docs/bugs/open/repository-webhooks-are-never-delivered.md`. Its delivery code works when called directly. |
| GitLab | Not implemented | When it delivers, set the hook's secret token to a sender token. The sink accepts `X-Gitlab-Token`. |
| Scripts | — | `Authorization: Bearer <sender token>`, or `?token=` as a last resort. |

## Consumers

```bash
curl -H "Authorization: Bearer $WHC_TOKEN" \
  'http://webhook-sink.ai-pipeline.svc.cluster.local/events?source=jira&event=jira:issue_created&after=0&wait=30'
```

Filter with `channel`, `source`, `event` and `sender`, a sender token ID.
Each takes a comma-separated list. Keep the response's `next_after` as the
next request's `after`.

## Deployment

| File | Role |
| --- | --- |
| `deploy/scripts/05n-build-webhook-sink.sh` | Builds the image, running fmt, clippy and tests, and imports it into k3s |
| `deploy/scripts/28-deploy-webhook-sink.sh` | Creates `webhook-sink-tokens` if missing, applies the manifest, and waits |
| `deploy/k8s/31-webhook-sink.yaml` | The PVC, the services `webhook-sink` (port 80 to 8080) and `webhook-sink-admin` (port 80 to 8081), and a single-replica Deployment |
| `make host-rebuild-webhook-sink` | Build, apply, then restart; also works on a first deploy |
| `make host-webhook-sink-tokens` | Print the admin key and default tokens |
| `make host-logs-webhook-sink` | Follow the logs. Each stored event is logged with its sequence number, channel, source, event, sender token and method. Token values are never logged. |

The sink runs one replica with the `Recreate` strategy, because SQLite
allows only one writer.

## Real GitHub

Receiving webhooks from real GitHub is planned but not set up. It needs a
public endpoint or tunnel for the public listener only, never the admin
listener. A sender token is used as the hook's secret, as with the
emulators. It also needs a reconcile job that redelivers failed deliveries,
since GitHub does not retry them on its own.

See `.ledger/tasks/done/webhook-sink-service.md` and
`.ledger/decisions/ADR-0013-webhook-sink-in-rust.md`.
