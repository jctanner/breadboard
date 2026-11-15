# Service releases and published images

Release versions use UTC CalVer `YYYY.MM.DD`, then `.1`, `.2`, etc. for further
releases that day. Git tags, GitHub release names and image tags are identical
and immutable. Repositories with established schemes retain them: Markov uses
v-prefixed SemVer, and GitLab's existing `2026.06.30` tag is preserved.
Package metadata versions are separate and are not rewritten by this rollout.

The container workflow builds Linux amd64 images once, smoke-tests their
`/healthz` endpoint, then publishes that exact tested image. PRs do not publish.
Main builds update `latest` and `sha-<full SHA>`; release builds publish the
exact CalVer tag without changing `latest`. A GitHub release is created only
after every matrix image publishes; its notes include all image digests.

| Published image | Build context | Smoke port |
| --- | --- | --- |
| ghcr.io/jctanner/breadboard-dashboard | Repository root, pinned OpenShell SDK checkout | 5000 |
| ghcr.io/jctanner/breadboard-fullsend-dashboard | Repository root | 5000 |
| ghcr.io/jctanner/breadboard-golang-reverse-proxy | deploy/golang-reverse-proxy | 80 |

The dashboard SDK source is pinned to OpenShell commit
`b2ea81822bb5263679ed00ff0fbe8c08577abab5`; Actions fetches that public commit
before the build. It does not copy a developer's ignored checkout.

## Deployment and local builds

`deploy/release-images.json` records each selected image's release pin and
its corresponding local build tag. Maintained manifests use the published
CalVer tags and `IfNotPresent`. They include the Jira and GitHub K3s variants
required by the existing TLS/Caddy manifests. No deployment is performed by
the release workflows. Package visibility is a separate human-approved action;
configure image pull authentication for private packages.

Regular deploy scripts use the pins and skip local builds for these images.
`BREADBOARD_IMAGE_SOURCE=local` selects the existing local tags through
`apply-domain-manifests.sh`, retaining domain rendering. Explicit
`make host-rebuild-dashboard`, emulator, proxy, relay and hooksink rebuild
targets select local images automatically. To review either form without
applying it:

```sh
bash deploy/scripts/apply-domain-manifests.sh --render deploy/k8s/20-pipeline-dashboard.yaml
BREADBOARD_IMAGE_SOURCE=local bash deploy/scripts/apply-domain-manifests.sh --render deploy/k8s/20-pipeline-dashboard.yaml
```

Update a release pin by checking the GitHub release and its published digest,
then changing the manifest and `release-images.json` together in a PR. Use
`image:tag@sha256:...` for additional digest pinning. This repository has no
maintained Compose deployment on origin/main.

## Images retained as local or upstream builds

- Pipeline agent: requires the installation's internal CA and unpinned
  architecture/agent source inputs. Publish only after those build inputs and
  CA injection have a separate reproducible contract.
- Claude agent and Fullsend Mint development images: retain local development
  builds; the mint is an integration-only credential exchange service.
- Fullsend runner/sandbox/code and OpenShell supervisor local variants: built
  from third-party integration sources; retain their upstream release schemes
  and local overlays pending owner coordination.
- Org Pulse: layered images in red-hat-data-services repositories, already
  using a CORE_TAG contract; retain that contract and upstream publication.
- Observatory and markovd: repositories outside jctanner; proposals only until
  separately authorized. Markov's existing SemVer release path is preserved.
- Workflow Dojo: optional, outside deploy-all.sh; inventory only here.
- Legacy ai-first-pipeline: generated Dockerfile in a deployment script;
  deferred until it has a maintained reproducible build definition.

A failed publication creates no GitHub release. Inspect Actions and GHCR before
any next action; do not automatically retry or overwrite release images.
Allocate a new CalVer suffix if a release image was partially published.
Changing GHCR package visibility always requires separate human approval.
