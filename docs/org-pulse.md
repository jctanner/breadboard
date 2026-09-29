# Org Pulse in the Breadboard stack

Org Pulse is the AI Engineering engineering dashboard: Jira, GitHub and
GitLab data joined to a team roster to surface delivery insight. In this
stack it runs at `https://orgpulse.local` in demo mode. This page records how
its two source repositories fit together, how the deployment here differs
from upstream's, and what it would take to make it live.

## Two repositories, one application

| checkout | what it is | what it publishes |
| --- | --- | --- |
| `checkouts/org-pulse-core` | the platform: Vue 3 frontend, Express backend, the module system, the built-in `team-tracker` module, a Python chatbot service, and an OpenShift kustomize base | the npm package `@org-pulse/core` on the public registry, and three images on quay.io: `org-pulse-core-backend`, `org-pulse-core-frontend-builder` (dependencies and source, not yet built) and `org-pulse-core-frontend-runtime` (hardened nginx, no app code) |
| `checkouts/rhai-org-pulse` | the AI Engineering consumer: nine modules (`ai-catalyst`, `ai-impact`, `customer-insights`, `okr-hub`, `product-builds`, `releases`, `system-health`, `upstream-pulse`, `workflow-validation`) and platform customisations, with no platform code of its own | two images, `team-tracker-backend` and `team-tracker-frontend`, each built `FROM` a core image at a pinned tag with the modules copied on top |

The consumer depends on core two ways. For local development it installs
`@org-pulse/core` from npm and `npm run setup` symlinks core's modules and
shared code into the workspace. For deployment its Dockerfiles start from
core's images: the backend adds a few npm libraries and the modules; the
frontend adds the modules to the builder stage, runs the Vite build, and
copies the result into the runtime image. Its kustomize overlay pulls core's
base straight from GitHub at the pinned release and swaps the image names.
The two checkouts are at matching revisions: the consumer pins
`@org-pulse/core ^2.0.84` and core is at v2.0.84.

## How it is built here

`deploy/scripts/05l-build-org-pulse.sh` builds the three core images from the
core checkout and tags them with the exact quay.io names the consumer's
Dockerfiles name, so `FROM quay.io/org-pulse/org-pulse-core-backend:v2.0.84`
resolves to the local build without a pull. It then builds the consumer's
backend and frontend on those, tags them `org-pulse-backend:k3s` and
`org-pulse-frontend:k3s`, and imports them into k3s. The core tag is read
from the core checkout's `package.json`, the same way the consumer's own
Makefile reads it from the installed package; the script warns if the
consumer's pin does not cover the core checkout's version.

The Red Hat hardened base images (`registry.access.redhat.com/hi/nodejs`,
`hi/nginx`) and the UBI Node builder pull without credentials. The backend
build compiles native dependencies and the frontend build runs Vite, so the
first build takes several minutes.

## How it is deployed here

`deploy/k8s/28-org-pulse.yaml`, applied by `26-deploy-org-pulse.sh` and
`make host-deploy-org-pulse`, keeps upstream's three parts as plain manifests
in the `ai-pipeline` namespace:

| part | upstream | here |
| --- | --- | --- |
| frontend | nginx behind an OpenShift OAuth proxy sidecar, config rendered by an init container to inject a proxy secret | nginx alone; the config is a ConfigMap naming the backend Service, proxy secret empty |
| backend | Express on 3001, identity from `X-Forwarded-Email` set by the proxy | the same image; without the header the backend uses the first `ADMIN_EMAILS` entry, upstream's own local-dev fallback, so every caller is `admin@breadboard.local` |
| database | an `ExternalName` Service to a managed MongoDB | a MongoDB pod (the image upstream's compose file uses) with a 2Gi PVC |
| refresh | a 15-minute CronJob calling the admin refresh API | none: demo mode answers every refresh with "skipped" |
| chatbot | a Python service needing an LLM endpoint | left out |

Routing follows every other service: a cert-manager Certificate in
`02-certificates.yaml`, a Traefik Ingress in `08-ingress-https.yaml`, a route
in the Go host proxy, the hostname in its certificate, and a link in the
Breadboard dashboard's navigation. Add `orgpulse.local` to the hosts entry
that carries the other `*.local` names.

`make host-rebuild-org-pulse` rebuilds both layers and restarts the two
deployments; `make host-logs-org-pulse` follows the backend.

## Known gaps

- **MongoDB image.** Upstream's compose file names
  `quay.io/mongodb/mongodb-community-server`. That image's entrypoint refuses
  to start on Linux 6.19 and newer, citing MongoDB 8.0's tcmalloc, offers no
  bypass, and does so on every tag including 7.0. This host runs a newer
  kernel, so the manifest uses the official `docker.io/library/mongo:7.0`,
  which has no such check. Its readiness probe needs a ten-second timeout;
  `mongosh` takes longer than the one-second default to start, and a probe
  that always times out leaves the Service without endpoints.
- **Identity in demo mode.** Role assignments come from the fixtures'
  `roles.json`, not from `ADMIN_EMAILS`, so the default identity has to be
  one of the fixture admins (`demo@example.com`) for the admin pages to open.
- **`workflow-validation` does not load.** The consumer's backend Dockerfile
  installs the module libraries core lacks, and `undici`, which that
  module's OpenSearch client requires, is not among them; the router fails
  with "Cannot find module 'undici'" and the other nine modules mount. This
  is an upstream defect in `rhai-org-pulse`, present in its production image
  too unless core's node_modules happen to carry `undici`; harmless in demo
  mode, where the module would have nothing to query.

## Demo mode, and what live would take

`DEMO_MODE=true` serves fixture data (core's and the consumer's, seeded into
MongoDB at startup), disables refresh and token creation, and never calls
Jira, GitHub, GitLab, LDAP or Google. No credentials are mounted.

Pointing it at the emulators is not a configuration change. Core's Jira
client is Jira Cloud only, REST v3 with email and API token against
`redhat.atlassian.net`, while the Jira emulator speaks Server-style v2. The
GitHub App client names `api.github.com` as a constant. Making Org Pulse
talk to this stack's forges is the same kind of host-assumption work the
Fullsend integration went through, and belongs in its own plan. Pointing it
at real Jira Cloud and GitHub instead needs an Atlassian token and a classic
PAT in a Secret, and egress the cluster's runner pods deliberately do not
have.

Observatory already imports `org-pulse-config.json`, the pipeline registry
that Org Pulse's `system-health` module describes, so the two know about
each other; that is the thread to pull for a live integration.
