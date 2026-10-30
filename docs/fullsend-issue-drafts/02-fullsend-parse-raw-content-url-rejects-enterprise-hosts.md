<!-- Draft for review. Not filed. -->
# forge: ParseRawContentURL rejects raw-content URLs on GitHub Enterprise hosts

**Repository:** fullsend-ai/fullsend
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

`forge.ParseRawContentURL` (`internal/forge/url.go:184`) accepts only one
host. Line 196 refuses everything else:

```go
if u.Hostname() != "raw.githubusercontent.com" {
	return nil, fmt.Errorf("not a raw.githubusercontent.com URL: %s", u.Hostname())
}
```

A GitHub host other than github.com has no `raw.githubusercontent.com`. So
any raw-content URL on such a host fails to parse, and every caller that
needs the parse fails with it:

- `fetchBaseSkillDir` (`internal/harness/compose.go:1979`) returns
  `base <field>: parsing raw URL for skill directory fetch: not a raw.githubusercontent.com URL: <host>`,
  so a URL-based harness whose skills live on the configured host cannot
  load them.
- The script-directory probe (`compose.go:1793`) treats the URL as
  unparseable and falls back to a single-file fetch, so companion files next
  to a pre/post script are not fetched.
- `parseAgentSourceURL` (`internal/cli/agent.go:861`) and the lock path
  (`internal/cli/lock.go:1211`) cannot parse an agent source on that host.

When the parse succeeds it always labels the result `Forge: "github"`
(line 232), which `CloneURL` (line 243) turns into `github.com`. By
inspection, a parse that accepted an enterprise URL but kept that label would
clone the directory from github.com instead of the configured host.

### What should happen

A raw-content URL on the configured GitHub host parses into the same owner,
repo, ref and path as the equivalent `raw.githubusercontent.com` URL, and the
result identifies that host, so a directory fetch built from it (`CloneURL`)
clones from the configured host rather than github.com.

The URL shape differs. github.com serves raw content from a separate
hostname; a GitHub Enterprise Server host serves it from the host itself,
with a literal `raw` segment after the repository:

```
https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path...}
https://{host}/{owner}/{repo}/raw/{ref}/{path...}
```

The second form is the one `recognizedManifestSourcePath`
(`internal/repos/managed_config.go:78`) already documents for github.com.

Behaviour for `raw.githubusercontent.com` URLs, including the error message
for other hosts, is unchanged.

### How to reproduce

Code-level, on `main`:

```go
info, err := forge.ParseRawContentURL(
	"https://raw.githubusercontent.com/fullsend-ai/agents/main/skills/x/SKILL.md")
// info = {Forge:github Owner:fullsend-ai Repo:agents Path:skills/x/SKILL.md Ref:main}, err = nil

info, err = forge.ParseRawContentURL(
	"https://ghe.example.com/fullsend-ai/agents/raw/main/skills/x/SKILL.md")
// info = nil, err = "not a raw.githubusercontent.com URL: ghe.example.com"
```

### Context

Found while running Fullsend against a local GitHub API emulator on a private
hostname, where a harness sourcing skills from that host failed with the
error above. That is not a GitHub Enterprise Server, but by inspection the
check at `url.go:196` applies to any host other than github.com, including
GHES.

The directory-level fetches that depend on this parse were added in #2707
(skills) and #5688 (pre/post scripts).

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0007-parse-enterprise-raw-content-urls.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30).
  Line numbers re-read on that SHA: check at `url.go:196`, `Forge: "github"`
  at 232, `CloneURL` at 243, callers at `compose.go:1793/1829/1979/2172`,
  `agent.go:861`, `lock.go:1211`.
- **Evidence:**
  - Error text and the "not our ref" clone consequence: patch header. The
    clone consequence is stated in the issue as "by inspection", because on
    main the parse fails before the clone is attempted.
  - Code-level reproduction: run on a detached worktree of origin/main
    (`go test` with a throwaway test calling `ParseRawContentURL`); outputs
    quoted verbatim.
  - Caller error wrapping (`parsing raw URL for skill directory fetch: ...`):
    read from `compose.go:1979-1981`.
  - URL shape `{host}/{owner}/{repo}/raw/{ref}/{path}`: patch header, plus the
    same form documented upstream in `managed_config.go:78` for github.com.
    No GitHub docs link cited.
  - The patch header says the URL is "one this CLI built for that forge". On
    main the CLI still builds only `raw.githubusercontent.com` URLs (the
    agents-repo prefix is hardcoded, `run.go:145`); that is a sibling child
    of the parent. So the reproduction uses a user-configured harness URL
    instead of claiming the CLI builds it.
- **Duplicate search:** `ParseRawContentURL` (7 hits, all closed PRs) and
  `raw.githubusercontent.com enterprise` (0 hits). No duplicate.
  - #2707, #5688: related (introduced the directory fetches that call the
    parser); linked in Context.
  - #5978, #5875, #2770, #2736, #2626: unrelated (other harness/URL work
    that touches the same code).
- **Open questions for the reviewer:**
  - GHES with subdomain isolation enabled may also serve raw content from a
    `raw.<host>` subdomain. I did not verify that, so the issue names only
    the `/raw/` path form. Add the subdomain form if you know it applies.
  - No end-to-end reproduction on main: a harness `base` on a non-github.com
    host is refused earlier by `fetch.DefaultPolicy`'s domain allowlist
    (`fetch.go:104`, `fetch: domain not in allowlist`) before this parse is
    reached. That gate is a separate host-assumption problem, so the issue
    relies on the code-level reproduction only.
