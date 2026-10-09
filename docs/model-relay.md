# Model Relay

Model Relay (`checkouts/model-relay`) is a Rust gateway that accepts Vertex
`rawPredict`/`streamRawPredict` and Anthropic Messages requests from Claude
Code clients, forwards them to a project's upstream account, and records usage
in SQLite. Its own README is the reference for the relay itself; this page
covers how Breadboard runs it.

## Endpoints

| Name | Backend | Purpose |
| --- | --- | --- |
| `https://relay.local` | `model-relay-admin:8081` | Admin console (`/admin/`) and `/api/private/v1/*` |
| `https://relay-api.local` | `model-relay:8080` | Inference: Vertex routes, `/v1/messages`, `/health` |
| `http://model-relay.ai-pipeline.svc.cluster.local:8080` | `model-relay:8080` | In-cluster inference |
| `http://model-relay.ai-pipeline.svc.cluster.local:8082/v1/token` | `model-relay:8082` | In-cluster Google token exchange for `external_account` clients |

Both names route through the host proxy and resolve in-cluster through the
CoreDNS rewrites in `deploy/k8s/22-fullsend-networking.yaml`. Add them to the
host's `/etc/hosts` next to the other `*.local` names.

## Deployment

| File | Role |
| --- | --- |
| `deploy/scripts/05m-build-model-relay.sh` | Builds the checkout's `Dockerfile` (fmt, tests, clippy, release) and imports `model-relay:latest` into k3s |
| `deploy/scripts/27-deploy-model-relay.sh` | Creates the admin key Secret once, applies certificate, manifest and ingress |
| `deploy/k8s/29-model-relay.yaml` | ConfigMap, PVC, two Services and the Deployment |

```bash
make host-deploy-relay      # first deployment
make host-rebuild-relay     # rebuild image, import into k3s, restart
make host-relay-admin-key   # print the admin console key
make host-logs-relay
```

The Deployment runs one replica with the `Recreate` strategy: SQLite and the
managed OAuth credentials under `/data` (PVC `model-relay-data`) have a single
owner, and the relay refuses to start if another process holds the volume.

## Dashboard jobs

Jobs submitted from `https://dashboard.local/jobs` reach Vertex through the
relay. Three settings on the dashboard Deployment turn this on; remove them to
send jobs straight to Google again:

| Dashboard setting | Effect on each job pod |
| --- | --- |
| `PIPELINE_MODEL_RELAY_URL` | Set as `ANTHROPIC_VERTEX_BASE_URL` (ends in `/v1`) |
| `PIPELINE_MODEL_RELAY_PROJECT` | Replaces `ANTHROPIC_VERTEX_PROJECT_ID` and sets `GOOGLE_CLOUD_PROJECT` |
| `PIPELINE_GCP_CREDENTIALS_SECRET` | Secret mounted at `/home/pipelineagent/.config/gcloud` instead of `gcp-credentials` |

The `gcp-credentials-relay` Secret holds `credentials.json`, an
`external_account` ADC configuration whose token URL is the relay's port 8082,
and `workload-key`, an exchange-only key issued to client `breadboard-cluster`
in project `vertex-shim-local`. The credential file names the key by absolute
path, so it works only where the Secret is mounted at that path.
`GOOGLE_CLOUD_PROJECT` is required: without it, Google's auth library resolves
the project through Cloud Resource Manager, which rejects the relay's token
before any model call. Other consumers of `gcp-credentials` still use Google
directly; the original Secret is also kept as `gcp-credentials-google-adc`.

Port 8082 is opened by `SHIM_MOCK_ADC_KEY_ID`, which deliberately names no
registry key, so the keyless metadata token endpoint on that port issues
nothing; only workload-key exchange works.

## Configuration

- `SHIM_BACKEND=mock`: the bootstrap `default` profile is a simulator. Connect
  an upstream account under **Upstream accounts** in the console and assign
  projects to it; the account login runs inside the pod and needs only a
  pasted authorization code.
- `/config/keys.json` is `{ "keys": [] }` and `/config/models.json` is `{}`;
  projects, client keys and model grants are managed in the console and
  persist in SQLite.
- The admin key lives in the `model-relay-admin` Secret, created by the
  deploy script. It defaults to `admin` for local development; set
  `MODEL_RELAY_ADMIN_KEY` before the first deploy to use another value, or
  delete the Secret and redeploy to change it.
- The relay needs egress to Anthropic's login, token and inference endpoints
  for real upstream accounts.
