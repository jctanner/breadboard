<!-- Draft for review. Not filed. -->
# run: agents-repo fallback and the run's status comment address github.com on other GitHub hosts

**Repository:** fullsend-ai/fullsend
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

When `fullsend run` executes against a GitHub host other than github.com
(`GITHUB_API_URL` and `GITHUB_SERVER_URL` name that host), two parts of the
run still go to github.com:

1. **Agents-repo fallback.** An agent with no local definition is resolved
   from `fullsend-ai/agents`. The client for that lookup is a bare
   `gh.New(composeGitToken)` (`internal/cli/run.go:666`), which targets
   api.github.com regardless of `GITHUB_API_URL`. The ref lookup in
   `fetchPinnedAgentsRepoFile` (`run.go:7414`) reaches the public API with
   the configured host's token and is refused, and the run stops:

   ```
   ! Could not resolve fullsend-ai/agents@main: 401 Bad credentials
   Error: resolving agent "triage": no config and agents-repo fallback unavailable
   ```

   Past the ref lookup, the harness URL is built from the fixed prefix
   `https://raw.githubusercontent.com/fullsend-ai/agents/`
   (`defaultAgentsRepoURLPrefix`, `run.go:145`, used at `run.go:7424`), and
   `fetch.DefaultPolicy` allows only `github.com` and
   `raw.githubusercontent.com` (`internal/fetch/fetch.go:104`). By
   inspection, on a host with no `raw.githubusercontent.com` the fallback
   cannot fetch the harness from the configured host even with a working
   ref lookup.

2. **Status comment.** `statusNewForgeClientFn` (`run.go:169-171`) also
   returns a bare `gh.New(token)`, so the comment the run posts about itself
   goes to api.github.com:

   ```
   ! Failed to post completion status: create issue comment on #79: 401 Bad credentials
   ```

Other paths in `internal/cli` already build their client with
`newGitHubLiveClient` (`internal/cli/github_client.go:137`), which honours
`forge.github.url` and falls back to `GITHUB_API_URL`.

### What should happen

On a host other than github.com, the agents-repo ref lookup, the harness
fetch and the status comment all go to the configured host. Behaviour on
github.com is unchanged, including unauthenticated access to the public
agents repository.

### How to reproduce

1. Point a workflow at a GitHub host other than github.com, so
   `GITHUB_API_URL` and `GITHUB_SERVER_URL` name that host and the token is
   valid only there.
2. Leave `agents:` unset in the config so the run uses the agents-repo
   fallback.
3. Run `fullsend run triage` on an issue. The agents ref lookup fails with
   the 401 above and the run exits; the status comment fails the same way.

### Context

Found while running Fullsend against a local GitHub API emulator; by
inspection this applies to any host other than github.com, including GitHub
Enterprise Server. Open PR #7629 would make a non-rate-limit 401/403 from
this ref lookup fatal with a pointer to token settings; on such a host that
message would then point at the token rather than the host. The
`allowed_remote_resources` default and the `dispatch --route` / `lint` copies
of this fallback are tracked in sibling sub-issues.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0005-resolve-agents-repo-against-configured-host.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30).
  `run.go:170` and `run.go:666` still call bare `gh.New`; `run.go:7424` and
  `fetch.go:104` still name only the public hosts.
- **Evidence:** the three error lines are from the patch header (observed).
  Error strings confirmed in code: `run.go:7292` ("no config and agents-repo
  fallback unavailable"), `run.go:1464` ("Failed to post completion status").
  The raw-prefix and fetch-domain points are by inspection; in our
  environment they were masked by the 401 and then fixed in the same patch,
  so the issue labels them "by inspection".
- **Duplicate search (section `0005`):** no duplicate.
  - #7629 (open PR, fail closed on PAT 401/403 in agent-ref resolution):
    related, linked in Context. Touches the same `fetchPinnedAgentsRepoFile`.
  - #8815 (open PR, harness paths relative to harness), #5425 (closed,
    remove scaffold fallback), #7074 (closed, mint status auth): unrelated.
  - agents#401, fullsend#401, agents#71, fullsend#2138, #3207: unrelated
    (keyword noise).
- **Open questions for the reviewer:**
  - The parent lists `allowed_remote_resources` (config default, patch 0013)
    as its own child, but `fetch.DefaultPolicy.AllowedDomains` (in 0005) is
    a separate list. I kept the fetch-domain point here; move it if you
    prefer it with the allowlist child.
  - The raw-URL part overlaps the theme of the `ParseRawContentURL` child
    (the `<host>/<owner>/<repo>/raw/<ref>` convention). I did not state that
    convention in the body, since it edges toward prescribing a fix.
