<!-- Draft for review. Not filed. -->
# fetch: a GitHub host on a private network cannot be fetched from, even when it is the configured forge

**Repository:** fullsend-ai/fullsend
**Parent:** none

---

### What happens

`fetch.FetchURL` (`internal/fetch/fetch.go:136`) resolves the host and
refuses the request if any resolved address is internal or reserved
(`fetch.go:171-178`):

```
fetch: resolved IP is internal/reserved: <host> resolved to <addr>
```

This is a deliberate SSRF defence, and it is the right default. The only way
past it is the unexported `skipIPCheck`, set by `NewTestPolicy` for tests.
Nothing in production can relax it for any host.

The consequence is that a GitHub host on an internal network, such as a
GitHub Enterprise Server reachable only inside a corporate network, cannot
be used as a source for anything Fullsend fetches over HTTP: agent harnesses
(`internal/cli/agent.go:626`, `agent.go:812`), harness bases and their
files (`run.go:525`, `run.go:2306`), `lock`, `lint`, `dispatch --route` and
`eval-measure`. This includes the harnesses a run needs to start, and it
holds even when that host is the forge the run is configured against
(`GITHUB_SERVER_URL`). The deployment's own forge is refused for the same
reason an arbitrary internal service is.

The only workaround is to avoid remote fetches altogether, for example by
committing every harness into the repository as a local-path agent source.

### What should happen

A deployment whose configured forge resolves to a private address can fetch
from that forge. Every other host stays subject to the internal-address check
exactly as today, so this does not become a way to reach arbitrary internal
services. A deployment that does not opt in, and any run on github.com,
behaves as it does now.

### How to reproduce

Code-level, on `main`, using `localhost` to stand in for a host that
resolves to a private address:

```go
p := fetch.DefaultPolicy
p.AllowedDomains = append(p.AllowedDomains, "localhost")
_, err := fetch.FetchURL(ctx, "https://localhost/fullsend-ai/agents/raw/main/harness/triage.yaml", p)
// fetch: resolved IP is internal/reserved: localhost resolved to ::1
```

With the default policy the same call is refused earlier with
`fetch: domain not in allowlist`, because the default allows only
`github.com` and `raw.githubusercontent.com` (`fetch.go:104`). That domain
restriction is a separate problem; this issue is about the address check
that remains once the host is allowed.

### Context

Found while running Fullsend against a local GitHub API emulator on a
private hostname. Once the host was allowed, every harness
fetch failed with
`resolved IP is internal/reserved: <host> resolved to 10.43.17.62`.

That is not a GitHub Enterprise Server, but self-hosted forges on internal
networks are the normal GHES deployment, and by inspection the same check
refuses any of them. Related: #595 (WIF and VPN implications for self-hosted
forges behind firewalls) and #918 (agents cannot load context behind network
boundaries; that issue is about reading third-party context, not the
deployment's own forge). #6628 documents the SSRF-hardened HTTP client this
check belongs to.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0006-allow-a-privately-reachable-forge.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30).
  Check at `fetch.go:171-178`, error var at `fetch.go:116`, `skipIPCheck`
  only set by `NewTestPolicy` (`fetch.go:91-99`). No production way to
  exempt a host exists on main.
- **Evidence:**
  - Observed error with `10.43.17.62`: `.ledger/plans/fullsend-integration-conformance-plan.md`
    (G30). The `<host>` in the issue replaces our `.local` name.
  - "Every fetch fails ... including the agent harnesses": patch header;
    call sites listed in the issue are the `fetch.DefaultPolicy` users found
    with `git grep` on main.
  - Code-level reproduction: run on a detached worktree of origin/main with a
    throwaway test; both errors quoted verbatim.
  - Local-path workaround: ledger G30 and the `agents:` local-path support in
    `config.ValidateAgentEntries`.
  - The PrivateHosts / `FULLSEND_ALLOW_PRIVATE_FORGE` design is deliberately
    left out of the issue, per instructions. "What should happen" states the
    constraint (only the configured forge, opt-in, unchanged elsewhere)
    without the mechanism.
- **Duplicate search:** `internal/reserved resolved IP` (1 hit: #6628,
  closed docs PR for the secure HTTP client; related, linked).
  `private network forge fetch` (101 hits): #918 (open) and #595 (open)
  related, not duplicates, both linked after reading their bodies; #7978,
  #6787, agents#1792, #8226, agents#1610, agents#981 unrelated. No duplicate.
- **Open questions for the reviewer:**
  - "A deployment that does not opt in" implies the relaxation is opt-in.
    That matches the patch and seems right for a security control, but it is
    a requirement, not just a symptom; keep or drop.
  - Git-based directory fetches (sparse checkout) do not go through
    `FetchURL` and are not covered by this check as far as I read; the issue
    names only HTTP fetches.
