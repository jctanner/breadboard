<!-- Draft for review. Not filed. -->
# cli: token-scope check, `reconcile-status` and `eval-measure` address api.github.com on other GitHub hosts

**Repository:** fullsend-ai/fullsend
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

Three clients in a run's job ignore `GITHUB_API_URL` and go to
api.github.com. On another GitHub host each fails on every run:

| Site | Code (origin/main) | Observed |
| --- | --- | --- |
| Token-scope check in `fullsend run` | `internal/cli/run.go:1357` passes the literal `"https://api.github.com"` to `fetchTokenScope` | `! Token scope check: fetching token scope: listing installation repositories: Get "https://api.github.com/installation/repositories?per_page=100": dial tcp 140.82.112.5:443: connect: connection refused` |
| `fullsend eval-measure` manifest lookup in `fullsend-ai/agents` | `internal/cli/evalmeasure.go:257` returns a bare `gh.New(token)` | `! Could not resolve fullsend-ai/agents@main: get ref fullsend-ai/agents@heads/main: ... Get "https://api.github.com/...": dial tcp ...: connect: connection refused` |
| `fullsend reconcile-status` | `internal/cli/reconcilestatus.go:21-23`, `reconcileNewForgeClient` returns a bare `gh.New(token)` | `Error: listing comments: list issue comments page 1: ... Get "https://api.github.com/...": dial tcp ...: connect: connection refused`, then `::warning::Could not reconcile orphaned status comment` (`action.yml:660`) |

The first two are warnings. The third matters: `reconcile-status` is the
post-job step that finalizes a status comment left in the "Started" state
when the `fullsend` process died before posting its completion. On another
host it never reaches the forge, so by inspection a cancelled or hard-killed
run keeps its "Started" comment.

`internal/cli` already has `newGitHubLiveClient`
(`internal/cli/github_client.go:137`), which honours `forge.github.url` and
falls back to `GITHUB_API_URL`; these three sites do not use it or the
variable.

### What should happen

On a host other than github.com, the token-scope check, the eval-measure
manifest lookup and the orphaned-status reconciliation reach the configured
host. Behaviour on github.com is unchanged.

### How to reproduce

1. Run a Fullsend workflow against a GitHub host other than github.com, so
   `GITHUB_API_URL` names that host.
2. The `fullsend run` log shows the token-scope warning above, and the
   eval-measure step logs the agents-ref warning.
3. Cancel a run after its "Started" status comment is posted. The post-job
   step logs `Could not reconcile orphaned status comment` and the comment
   stays "Started".

Code-level: with `GITHUB_API_URL=https://ghes.example.com/api/v3`,
`reconcileNewForgeClient("t")` and the client from
`evalMeasureFetchContext` both report `BaseURL()` `https://api.github.com`,
the default in `gh.New` (`internal/forge/github/github.go:169`).

### Context

Found while running Fullsend against a local GitHub API emulator; by
inspection this applies to any host other than github.com, including GitHub
Enterprise Server. "connection refused" is specific to an environment
without egress to github.com; with egress the requests reach the public API
with a token not issued there. The run's own completion comment and its
agents-repo fallback are tracked in a sibling sub-issue.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0014-address-the-configured-forge-in-the-remaining-clients.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30).
  All three sites unchanged: `run.go:1357`, `evalmeasure.go:257`,
  `reconcilestatus.go:22`. `tokenscope.go` has no host logic; it uses the
  `baseURL` it is given.
- **Evidence:** all four log lines are from the patch header (observed in
  our cluster, which blocks egress, hence "connection refused"). The header
  lists the agents-ref warning without naming its source; I attributed it to
  eval-measure because the header names eval-measure as the third client and
  our run.go fallback was already patched (0005). On unpatched upstream the
  run's own fallback emits the same message form. "Started comment stays
  forever" is from the header's reasoning plus reading `action.yml:635-661`;
  the reproduce step 3 is by inspection, not a logged reproduction - flagged
  in the body as "by inspection".
  The code-level repro is by inspection: `gh.New` sets
  `baseURL: "https://api.github.com"` (`internal/forge/github/github.go:169`)
  and `LiveClient.BaseURL()` exists (`:181`); not executed.
- **Duplicate search (section `0014`):** no duplicate.
  - #6036 (closed PR, added eval measurements): origin of the eval-measure
    site, unrelated as a defect.
  - #895, #6703, #8769, agents#1689, #213, #7450, #7461, #8756: unrelated.
- **Open questions for the reviewer:**
  - The table is long for a GitHub issue body; acceptable, or split to a
    list?
