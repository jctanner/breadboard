<!-- Draft for review. Not filed. -->
# Several code paths address github.com instead of the configured GitHub host

**Repository:** fullsend-ai/fullsend
**Parent:** none (this is the parent; the sub-issues are listed below)

---

### What happens

Fullsend supports GitHub hosts other than github.com: `forge.github.url` in
`repos.yaml` names the instance (#5712), and `newGitHubLiveClient` in
`internal/cli` builds an API client from it, falling back to `GITHUB_API_URL`.
Several code paths in this repository and in `fullsend-ai/agents` still
address github.com by name. On any other host they either reach the public
API with a credential that is not valid there, or refuse a URL that belongs
to the configured host before any work starts. Typical symptoms:

```
! Could not resolve fullsend-ai/agents@main: 401 Bad credentials
Error: resolving agent "triage": no config and agents-repo fallback unavailable
ERROR: ISSUE_URL does not match expected pattern: https://<host>/<owner>/<repo>/issues/79
Error: resolving agent "triage": remote resource not allowed
```

Each sub-issue below is one place where this happens. They share a cause, but
each fails independently and can be fixed and verified on its own.

### What should happen

When a run, a CLI command or an agent script is configured for a GitHub host
other than github.com, every request it makes to the forge and every URL it
validates or builds uses that host. Behaviour on github.com is unchanged.

### Context

Found while running Fullsend end to end against a local GitHub API emulator
on a private hostname. That is not a GitHub Enterprise Server, but by
inspection each of these paths behaves the same way on any host other than
github.com, including GHES.

The repository already has the pieces: `forge.github.url` (#5712),
`newGitHubLiveClient`, and the centralised CLI client construction from
#7090. The remaining sites are the ones that bypass them, for example the
bare `gh.New(...)` calls in `internal/cli`, and the literal
`https://github.com` and `raw.githubusercontent.com` matches elsewhere.

Sub-issues:

- [ ] action: agent and CLI install actions call github.com for releases and clones
- [ ] run: agents-repo fallback and the run's status comment address github.com on other GitHub hosts
- [ ] forge: ParseRawContentURL rejects raw-content URLs on GitHub Enterprise hosts
- [ ] run: minted agent token is not used by gh on hosts other than github.com
- [ ] cli: `fullsend github setup` and `github set` address api.github.com on other GitHub hosts
- [ ] config: default allowed_remote_resources refuses fullsend-ai repositories on the configured GitHub host
- [ ] cli: token-scope check, `reconcile-status` and `eval-measure` address api.github.com on other GitHub hosts
- [ ] cli: `dispatch --route`, `lint` and the offline cache resolve the agents repo on github.com
- [ ] (`fullsend-ai/agents`) triage: tracker_validate_issue_url rejects issue URLs on GitHub hosts other than github.com
- [ ] (`fullsend-ai/agents`) ops libraries: review, code, fix and other GitHub stages assume github.com URLs

---

## Draft notes (not part of the issue)

- **Local patches:** the whole host cluster: Go 0003, 0005, 0007, 0008, 0011,
  0013, 0014, 0015 and agents 0001, 0005 (`deploy/fullsend/patches/`).
- **Checked against:** fullsend-ai/fullsend@e82eda3ec and
  fullsend-ai/agents@8f819a9 (origin/main, 2026-10-30). The bare `gh.New`
  callers and literal `https://github.com` matches are still present there.
- **Filing:** file this parent first, then each child, then attach the
  children with the sub-issues REST API as `skills/filing-issues/SKILL.md`
  describes. Replace the checklist titles with the filed issue numbers.
  Children in `fullsend-ai/agents` can be sub-issues across repositories.
- **Duplicate search:** `enterprise github.com hardcoded` and `GHES support`
  found no umbrella issue. Related, linked in Context: #5712 (closed,
  `forge.github.url`), #7090 / PR #7200 (closed, centralised CLI GitHub
  client authentication). Also related, not linked: #6787 (open, WIF for
  self-managed forges behind a private issuer).
- **Open questions for the reviewer:**
  - Whether to file the parent at all, or only the children with
    cross-links. The plan chose a parent to avoid one review of the same
    argument per child.
  - The plan's "few at a time" rule: file the parent with only the first one
    or two children, and add the rest later?
