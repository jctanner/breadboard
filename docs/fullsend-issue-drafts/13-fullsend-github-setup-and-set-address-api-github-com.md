<!-- Draft for review. Not filed. -->
# cli: `fullsend github setup` and `github set` address api.github.com on other GitHub hosts

**Repository:** fullsend-ai/fullsend
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

`fullsend github setup <owner/repo>` and `fullsend github set <owner/repo>
<key> <value>` build their API client with a bare `gh.New(token)`
(`internal/cli/github.go:150` and `:1165`). That client targets
api.github.com regardless of `GITHUB_API_URL`. Pointed at another GitHub
host, with a token for that host, both commands reach the public API and are
refused with `401 Bad credentials` before doing any work.

The sibling `fullsend github foreign allow|list|revoke` commands
(`internal/cli/foreign.go:64`, `:142`, `:295`) build theirs with
`newGitHubLiveClient`, which honours `forge.github.url` and falls back to
`GITHUB_API_URL`, so they reach the configured host.

### What should happen

`github setup` and `github set` address the same host as the other
`fullsend github` subcommands when one other than github.com is configured.
Behaviour on github.com is unchanged.

### How to reproduce

1. Export `GITHUB_API_URL` for a GitHub host other than github.com and a
   `GH_TOKEN` valid for that host.
2. Run `fullsend github set <owner/repo> FULLSEND_GCP_REGION us-east5`
   for a repository on that host.
3. The command fails with `401 Bad credentials` from api.github.com.
   `fullsend github foreign list` with the same environment reaches the
   configured host.

### Context

Found while running Fullsend against a local GitHub API emulator; by
inspection this applies to any host other than github.com, including GitHub
Enterprise Server.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0011-address-the-configured-forge-in-the-github-commands.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30).
  `github.go:150` (setup) and `github.go:1165` (set) still call bare `gh.New`.
- **Evidence:** "401 Bad credentials from the public API while pointed at a
  private one" is from the patch header (observed). The foreign.go contrast
  and line numbers are from reading origin/main. The repro's specific
  `github set FULLSEND_GCP_REGION` invocation and the `foreign list`
  comparison are a constructed minimal form, not the logged invocation; the
  header does not say which subcommand produced the 401.
- **Not stated:** the patch header says "every other command in the package
  already builds its client through newGitHubLiveClient". That is not true
  on origin/main: bare `gh.New` remains in `agent.go:896`,
  `inference_openai.go:748` and `mint_setup.go:414` (plus the sites in the
  sibling sub-issues). I named only the foreign commands as the contrast.
- **Duplicate search (section `0011`):** no duplicate.
  - #5713 / #5712 (closed, forge URL fields in repos.yaml), #7200 / #7090
    (closed, centralised CLI client auth): related, already linked from the
    parent.
  - #5617 / #5616 (closed, forge-aware repos tool), #6242 (closed,
    `--forge`/`--base-url` on post-review), #6067 (closed, afterFunc),
    #6395 (closed, per-repo uninstall): related background, not linked.
  - #8886, #8717, #4727, #260, #2269, #7527, #918, #7451, #3965, #7456:
    unrelated.
- **Open questions for the reviewer:**
  - Should `agent.go:896`, `inference_openai.go:748` and `mint_setup.go:414`
    be added (here or as another child)? We have no observation for them, so
    they would be by-inspection only.
