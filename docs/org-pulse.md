# Org Pulse in the Breadboard stack

Org Pulse is the AI Engineering engineering dashboard: Jira, GitHub and
GitLab data joined to a team roster to surface delivery insight. In this
stack it runs at `https://orgpulse.local`, pointed at the Jira, GitHub and
GitLab emulators. This page records how its two source repositories fit
together, how the deployment here differs from upstream's, which patches
make the emulators reachable, and what demo mode is for.

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
| backend | Express on 3001, identity from `X-Forwarded-Email` set by the proxy | the same image; without the header the backend uses the first `ADMIN_EMAILS` entry, upstream's own local-dev fallback, so every caller is `admin@breadboard.local`, which the role store is seeded with as admin |
| database | an `ExternalName` Service to a managed MongoDB | a MongoDB pod (the image upstream's compose file uses) with a 2Gi PVC |
| refresh | a 15-minute CronJob calling the admin refresh API | the same CronJob, addressed to the backend Service, without the proxy secret |
| chatbot | a Python service needing an LLM endpoint | left out |

Routing follows every other service: a cert-manager Certificate in
`02-certificates.yaml`, a Traefik Ingress in `08-ingress-https.yaml`, a route
in the Go host proxy, the hostname in its certificate, and a link in the
Breadboard dashboard's navigation. Add `orgpulse.local` to the hosts entry
that carries the other `*.local` names.

`make host-rebuild-org-pulse` rebuilds both layers and restarts the two
deployments; `make host-logs-org-pulse` follows the backend.

## Live mode: the emulators as the forges

The images are built from two feature branches on the forks, one per
repository, which make every forge host configurable and change nothing
when the variables are unset:

| branch | what it does |
| --- | --- |
| org-pulse-core `feature/configurable-github-api-url` | `shared/server/github-host` reads `GITHUB_API_URL` as the REST base and derives the GraphQL endpoint by the enterprise convention (`/api/v3` to `/api/graphql`); the App token exchange, the contributions fetch and the two roster-sync username helpers use it |
| rhai-org-pulse `feature/configurable-forge-hosts` | the six module defaults follow `GITHUB_API_URL`, `GITHUB_SERVER_URL` (which host a pull-request link belongs to), `JIRA_HOST` and `GITLAB_BASE_URL`; the package-onboarding project gains its own base-URL module secret |

The manifest sets those to the emulators' in-cluster names, hands Node the
cluster CA through `NODE_EXTRA_CA_CERTS` (the variable the backend image
already uses for a private CA, so verification stays on rather than being
switched off), and mounts the emulators' development credentials: any
basic-auth pair for the Jira emulator in its permissive mode, and the GitHub
emulator's seeded admin token. GitLab instances are configured in Org
Pulse's own Settings UI, so only the default host is set.

On the emulator side, the Jira emulator already rewrites Jira Cloud's
`/rest/api/3/` to its routes and serves `/search/jql` with cursor
pagination, and the GitHub emulator gained `user.contributionsCollection`,
the one GraphQL shape team-tracker needs (github-emulator
`docs/tasks/done/graphql-user-contributions-collection.md`).

Verified from inside the backend on 2026-09-29: Node's fetch reaches the
Jira emulator's v3 search (17 issues), the GitHub emulator's REST API as
`admin`, and its GraphQL contributions calendar, all over TLS against the
cluster CA. A full refresh then ran all 27 handlers. What they reported is
the work that remains, none of it transport:

- **The roster is empty.** Org Pulse computes everything relative to its
  roster, and the sources it knows are Red Hat LDAP and a Google Sheet, so
  the team-tracker metrics, GitHub and GitLab handlers fail on a null
  organisation until people and teams are seeded through the team-structure
  API.
- **The Jira emulator's JQL parser rejects relative dates** such as
  `resolutiondate >= -26w`, which the releases module's velocity query uses.
  That is a Jira emulator addition.
- **Module configuration.** The releases handlers want a target-version JQL
  fragment or product shortnames in their settings, and two want a Google
  service-account key; those are Settings-UI and credential matters, not
  code.

Seeding the roster and teaching the emulator relative dates are the next
pieces.

## Demo mode

`DEMO_MODE=true` in the ConfigMap serves the shipped fixtures (core's and
the consumer's, seeded into MongoDB at startup), disables refresh and token
creation, and never calls a forge. Demo roles come from the fixtures'
`roles.json`, not from `ADMIN_EMAILS`, so in demo mode the default identity
has to be one of the fixture admins (`demo@example.com`) for the admin
pages to open. It is the quickest way to see the modules with data in them.

## Known gaps

- **MongoDB image.** Upstream's compose file names
  `quay.io/mongodb/mongodb-community-server`. That image's entrypoint refuses
  to start on Linux 6.19 and newer, citing MongoDB 8.0's tcmalloc, offers no
  bypass, and does so on every tag including 7.0. This host runs a newer
  kernel, so the manifest uses the official `docker.io/library/mongo:7.0`,
  which has no such check. Its readiness probe needs a ten-second timeout;
  `mongosh` takes longer than the one-second default to start, and a probe
  that always times out leaves the Service without endpoints.
- **`workflow-validation` does not load.** The consumer's backend Dockerfile
  installs the module libraries core lacks, and `undici`, which that
  module's OpenSearch client requires, is not among them; the router fails
  with "Cannot find module 'undici'" and the other nine modules mount. This
  is an upstream defect in `rhai-org-pulse`, present in its production image
  too unless core's node_modules happen to carry `undici`.

Observatory already imports `org-pulse-config.json`, the pipeline registry
that Org Pulse's `system-health` module describes, so the two know about
each other; that is the thread to pull for a live integration.
