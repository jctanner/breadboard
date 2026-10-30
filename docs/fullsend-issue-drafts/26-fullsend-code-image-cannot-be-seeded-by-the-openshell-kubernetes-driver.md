<!-- Draft for review. Not filed. -->
# images: fullsend-code sandboxes never become Ready on OpenShell's Kubernetes driver because /sandbox/.cache/gopls is unreadable

**Repository:** fullsend-ai/fullsend
**Parent:** none

---

### What happens

With OpenShell 0.1.4 (the version pinned in `.github/scripts/openshell-version.sh`)
and its Kubernetes compute driver, a sandbox created from the `fullsend-code`
image never reaches `Ready`. The pod's `workspace-init` init container exits 1:

```
Error:   × Permission denied (os error 13)
```

`workspace-init` runs `/.openshell/runtime/openshell-sandbox seed-workspace`,
which copies the image's `/sandbox` into the workspace volume. It runs as the
workload identity (uid/gid 10001, `runAsNonRoot`, read-only root filesystem).
The `fullsend-code` image contains a directory that identity cannot read:

```
$ podman run --rm --entrypoint sh \
    ghcr.io/fullsend-ai/fullsend-code@sha256:7a020876eeab07d788d03d4313d24198332d7cbd7ec8dce809d53656e86296c6 \
    -c 'stat -c "%a %u:%g %n" /sandbox/.cache/gopls; find /sandbox ! -perm -o=r'
700 998:998 /sandbox/.cache/gopls
/sandbox/.cache/gopls
/sandbox/.cache/gopls/ba894286
```

The directory comes from `images/code/Containerfile:156`, which runs
`go install … gopls && gopls version` as the image's `sandbox` user (uid 998);
`gopls version` creates its cache at `~/.cache/gopls` with mode 0700.

`fullsend run` keeps waiting for the sandbox, then kills `openshell sandbox
create` at its ready timeout and retries, so the code stage fails after three
attempts with:

```
Error: creating sandbox: sandbox creation failed after 3 attempts: sandbox create failed: signal: killed (output: Created sandbox: fs-cod-…
  [0.0s] Requesting compute...
  [4.0s] Sandbox allocated
  [4.8s] Image pulled
  [5.6s] Image pulled)
```

Nothing in that output names the init container or the permission error.

The `fullsend-sandbox` image (triage) has no such directory and seeds
normally, so on the same deployment triage succeeds and the code stage it
hands off to does not. The review harness uses the same `fullsend-code`
image, so by inspection review is affected the same way.

### What should happen

A sandbox created from `fullsend-code` on OpenShell's Kubernetes driver, at
the pinned OpenShell version, reaches `Ready` the same way one from
`fullsend-sandbox` does.

### How to reproduce

1. Deploy the OpenShell 0.1.4 gateway with its Kubernetes compute driver
   (Helm chart at that version).
2. Create a sandbox from the code image with the agents repo's
   `policies/base.yaml`:
   ```
   openshell sandbox create --name probe --keep --no-auto-providers --no-tty \
     --from ghcr.io/fullsend-ai/fullsend-code@sha256:7a020876eeab07d788d03d4313d24198332d7cbd7ec8dce809d53656e86296c6 \
     --policy policies/base.yaml --detach -- sleep 600
   ```
3. The sandbox stays in `Provisioning`. The pod's `workspace-init` container
   has exited 1 with `Permission denied (os error 13)`.
4. The same command with the `fullsend-sandbox` image reaches `Ready`.

Making the directory readable in a derived image (and nothing else) lets the
same sandbox reach `Ready`, which isolates the cause to that directory.

### Context

Found while running Fullsend's triage → code flow against a local GitHub API
emulator, on a Kubernetes-hosted OpenShell gateway. Only the Kubernetes
driver was exercised; other compute drivers may seed differently.

Related in OpenShell: NVIDIA/OpenShell#2761 reported image-provided 0700 home
directories becoming unusable after workspace seeding when the seed ran as
root; it is closed, and the fix proposed for it (NVIDIA/OpenShell#3208) was
closed without merging. In 0.1.4 the seed runs as the workload identity
instead, so content the image's own user owns with mode 0700 cannot be read
by the seed at all.

---

## Draft notes (not part of the issue)

- **Local workaround:** `deploy/fullsend-sandbox-local/Containerfile` ends
  with `RUN chmod -R a+rX /sandbox` (2026-10-30). It applies to both local CA
  images (agents patch 0004 points the harnesses at them).
- **Checked against:** fullsend-ai/fullsend@25811c9a8 (origin/main,
  2026-10-30): `images/code/Containerfile:141` `USER sandbox`, `:156`
  `go install … gopls && gopls version`; `.github/scripts/openshell-version.sh:17`
  `OPENSHELL_VERSION=0.1.4`. The digest is the one pinned by the agents repo's
  `harness/code.yaml:21` and `harness/review.yaml:12` (agents@8f819a9).
- **Evidence:**
  - Observed: experiment/testrepo2 #5 on the GitHub emulator, run 1835, job
    7282 (code stage): three create attempts, each killed at the ready
    timeout (gateway log shows ~2m10s between each create and delete,
    17:42:09 → 17:44:19 → 17:46:34 UTC), error text above copied from that job.
  - Reproduced by hand from the runner pod with `fullsend-code-local:k3s` (our
    CA layer on the upstream digest): `workspace-init` exit 1, `Permission
    denied (os error 13)`; pod spec: `runAsUser`/`runAsGroup` 10001,
    `readOnlyRootFilesystem`, `fsGroup` 10001.
  - The upstream digest itself (not our layer) has the `0700 998:998`
    directory: checked with podman above.
  - After the local `chmod -R a+rX /sandbox`, the same probe with
    `--policy policies/base.yaml` reached `Phase: Ready`; inside it the agent
    runs as uid 10001 and the seeded `gopls` dir is owned by 10001.
  - A probe without `--policy` fails differently (supervisor: "Image policy
    is invalid") — irrelevant to Fullsend, which always passes the harness
    policy; not mentioned in the issue.
  - Seed code: `crates/openshell-sandbox/src/main.rs`
    `seed_kubernetes_workspace_at` → `copy_workspace_tree` (OpenShell
    `5a7728c`, v0.1.4).
- **Not run:** the code agent end to end after the workaround (needs
  experiment/testrepo2 #5 re-triggered); OpenShell 0.1.6 (open Renovate PR
  fullsend#8738) — whether a newer seed copes with unreadable content is
  unknown, and is worth checking before filing.
- **Duplicate search (2026-10-30, authenticated):** fullsend/agents for
  `gopls permission sandbox`, `seed-workspace`, `Permission denied os error
  13`, `workspace-init`, `openshell kubernetes driver`: no duplicate.
  Related, not linked: agents/fullsend#2041 (closed, "Sandbox: fix Go module
  cache permissions for markdown-only repos" — different cause), #8738 (open,
  OpenShell v0.1.6 bump). NVIDIA/OpenShell for `seed-workspace permission` and
  `workspace-init Permission denied`: #2761 (closed) and #3208 (closed,
  unmerged), linked in Context.
- **Open questions for the reviewer:**
  - Whether upstream deploys OpenShell's Kubernetes driver anywhere: their
    docs mention it only in ADRs 0028/0036 and an archived roadmap. If not,
    expect "unsupported topology"; the issue is still accurate for anyone who
    does.
  - Whether to also report the missing diagnostic (the `signal: killed`
    output never names `workspace-init`) to OpenShell or Fullsend separately.
