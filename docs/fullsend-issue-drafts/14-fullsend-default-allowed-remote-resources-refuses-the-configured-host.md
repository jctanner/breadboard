<!-- Draft for review. Not filed. -->
# config: default allowed_remote_resources refuses fullsend-ai repositories on the configured GitHub host

**Repository:** fullsend-ai/fullsend
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

`config.DefaultAllowedRemoteResources` (`internal/config/config.go:438`)
returns two fixed prefixes, whatever host the run is configured for:

```
https://raw.githubusercontent.com/fullsend-ai/fullsend/
https://raw.githubusercontent.com/fullsend-ai/agents/
```

On a GitHub host other than github.com, `fullsend-ai/agents` and
`fullsend-ai/fullsend` are served from that host, so their raw URLs have the
form `https://<host>/<owner>/<repo>/raw/<ref>/<path>`. Neither default
prefix matches them, and an agent source or harness URL pointing at the
host's copy of either repository is refused by the default allowlist:

```
agents[0] (triage): URL "https://ghe.example.com/fullsend-ai/agents/raw/<sha>/harness/triage.yaml" is not covered by allowed_remote_resources
```

The default is used in several places, so the refusal follows a deployment
around:

- `NewPerRepoConfig` (`config.go:763`) writes it into a newly scaffolded
  config, so a config created on such a host carries only the public
  prefixes.
- `EnsureDefaultAllowedRemoteResources` (`config.go:451`) merges it into an
  existing list at run time (`run.go:403`, `orgconfig.go`, `lock.go:200`).
- It is the fallback allowlist when no config exists (`run.go:556`,
  `lock.go:244`, `dispatch_route.go:208`, `harness/registry.go:34`,
  `harnessdispatch/enumerate.go:51`, `evalmeasure.go:227`).

A deployment on such a host that takes these repositories from the host has
to add the prefixes to `allowed_remote_resources` by hand.

### What should happen

On a host other than github.com, the default allowlist admits
`fullsend-ai/fullsend` and `fullsend-ai/agents` on the configured host the
same way it admits them on github.com today, in every place the default is
used (scaffolded config, run-time merge, and the no-config fallbacks). It
admits nothing else on that host. On github.com the default is unchanged.

### How to reproduce

Code-level, on `main`:

```go
t.Setenv("GITHUB_SERVER_URL", "https://ghe.example.com")
allow := config.EnsureDefaultAllowedRemoteResources(nil)
// [https://raw.githubusercontent.com/fullsend-ai/fullsend/ https://raw.githubusercontent.com/fullsend-ai/agents/]

src := "https://ghe.example.com/fullsend-ai/agents/raw/<40-hex sha>/harness/triage.yaml#sha256=<64 hex>"
err := config.ValidateAgentEntries([]config.AgentEntry{{Name: "triage", Source: src}}, allow)
// agents[0] (triage): URL "https://ghe.example.com/fullsend-ai/agents/raw/<sha>/harness/triage.yaml" is not covered by allowed_remote_resources
```

### Context

Found while running Fullsend against a local GitHub API emulator on a private
hostname, where the first run on a freshly scaffolded config failed until the
host's prefix was added to `allowed_remote_resources` by hand. That is not a
GitHub Enterprise Server, but by inspection the default is the same on any
host other than github.com, including GHES.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0013-allow-the-configured-forge-in-the-default-remote-resources.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30).
  `DefaultAllowedRemoteResources` at `config.go:438-443` still returns only
  the two public prefixes. Callers listed above were found with
  `git grep` on that SHA.
- **Evidence:**
  - Code-level reproduction: run on a detached worktree of origin/main with
    a throwaway test; the default list and the error are quoted verbatim
    (SHA and hash shortened to placeholders in the issue).
  - Scaffold carries the refusal / first run fails until edited by hand:
    patch header.
  - The patch header quotes `Error: resolving agent "triage": remote
    resource not allowed`. That string does not exist anywhere on main or in
    our checkout, so I did not quote it; the issue uses the
    `ValidateAgentEntries` message from main instead.
  - On main the agents-repo fallback still builds
    `raw.githubusercontent.com` URLs (`run.go:145`), so the fallback path
    (`run.go:7426-7428`, `Agents repo fallback skipped ...: URL not in
    allowed_remote_resources`) only hits this once that sibling defect is
    fixed. That is why the reproduction uses a configured agent source.
- **Duplicate search:** `allowed_remote_resources enterprise` (#430 open,
  third-party skill libraries; #2392 closed ADR PR): unrelated.
  `remote resource not allowed` (8 listed hits: agents#240, #8226, #7700,
  #6158, #8331, #8829, #8717, #8815): unrelated. No duplicate.
- **Open questions for the reviewer:**
  - "What should happen" says "admits nothing else on that host". That is
    the patch's scope and seems the right expectation, but it constrains the
    fix slightly; drop it if you want the expectation looser.
