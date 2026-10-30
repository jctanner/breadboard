<!-- Draft for review. Not filed. -->
# action: agent and CLI install actions call github.com for releases and clones

**Repository:** fullsend-ai/fullsend
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

On a GitHub host other than github.com, the Fullsend agent action fails
before `fullsend run` starts:

```
::error::Unexpected HTTP 401 checking release <version>; cannot proceed
```

The agent action (`action.yml`) and the CLI install action
(`.github/actions/install-fullsend-cli/action.yml`) name github.com in seven
places, regardless of the host the job runs on:

| File | Line | Request |
| --- | --- | --- |
| `action.yml` | 152 | `GET https://api.github.com/repos/fullsend-ai/fullsend/releases/latest` |
| `action.yml` | 167 | `GET https://api.github.com/repos/fullsend-ai/fullsend/git/tags/<sha>` |
| `action.yml` | 185 | `GET https://api.github.com/repos/fullsend-ai/fullsend/tags?...` |
| `action.yml` | 217 | `GET https://api.github.com/repos/fullsend-ai/fullsend/releases/tags/<version>` |
| `action.yml` | 297 | release asset download from `https://github.com/fullsend-ai/fullsend/releases/download/...` |
| `action.yml` | 353 | source-build remote `https://x-access-token:<token>@github.com/fullsend-ai/fullsend.git` |
| `.github/actions/install-fullsend-cli/action.yml` | 182 | source-build remote `https://x-access-token:<token>@github.com/<workflow_repository>.git` |

Each REST call sends `Authorization: Bearer ${GH_TOKEN}`, where `GH_TOKEN`
is the `github_token` input (default `github.token`). That token belongs to
the job's own host, so github.com rejects it. The release check at line 217
uses `curl -w "%{http_code}"`, and any status other than 200 or 404 reaches
the error at line 229 shown above. By inspection, the clone remotes at lines
353 and 182 also present the job token to github.com, and the source build
fetches from github.com rather than from the job's host.

### What should happen

When the action runs on a GitHub host other than github.com, its release
lookups, asset download and source clones go to the host the job is running
against, and the job token is only sent to that host. Behaviour on
github.com is unchanged.

### How to reproduce

1. On a GitHub host other than github.com, run a workflow that uses the
   Fullsend agent action with no vendored binary and `version` set to a
   release tag.
2. The "Detect install method" step requests
   `https://api.github.com/repos/fullsend-ai/fullsend/releases/tags/<version>`
   with the job's token, gets 401, and the step fails with the error above.

The same request can be made directly: a token that github.com does not
recognise gets HTTP 401 for that URL.

### Context

Found while running Fullsend against a local GitHub API emulator on a
private hostname. That is not a GitHub Enterprise Server, but by inspection
these paths behave the same way on any host other than github.com,
including GHES.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0003-honor-github-api-and-server-url.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main,
  2026-10-30). All seven literals present at the lines in the table.
- **Evidence:**
  - The seven sites and the `Unexpected HTTP 401 checking release ...;
    cannot proceed` symptom: patch 0003 header, observed against the
    emulator. Line numbers and the exact `::error::` text (line 229) read
    from origin/main.
  - Only the release check at line 217 was observed failing. The other six
    are by inspection (stated as such for the clone remotes). The
    `latest` lookup (line 152) uses `curl -fsSL`, so a 401 there would fail
    differently; I did not describe that failure because I did not observe
    it.
  - I left out the patch header's claim that "every other host the action
    talks to is taken from the standard Actions variables": `action.yml`
    and the install action contain no `GITHUB_API_URL` or
    `GITHUB_SERVER_URL` reference on origin/main, so I could not check it
    by grep. The other traffic presumably goes through `gh`.
  - The direct-request line in "How to reproduce" was checked on
    2026-10-30: a `curl` to `api.github.com/.../releases/latest` with a
    bogus bearer token returned 401.
  - Not checked: `gh release download ... -R "${WORKFLOW_REPOSITORY}"` at
    install action line 160 has no literal host. Its host depends on `gh`'s
    environment.
- **Duplicate search (section `0003`):** no duplicate.
  - fullsend#2277 (closed PR, mint cross-org WIF): unrelated.
  - agents#807 (closed, code agent multi-forge), fullsend#529 (closed, run
    links on start): unrelated.
  - From `host-cluster`: fullsend#5792 (closed PR, moved logic from
    action.yml to the composite action) and #5357 (closed PR, resolve CLI
    version from the reusable workflow ref) touch this code but not the
    host. Related history, not linked.
- **Open questions for the reviewer:**
  - On GHES the action itself may come from github.com through GitHub
    Connect while the job token belongs to the appliance. In that setup
    there may be no `fullsend-ai/fullsend` repository or release on the
    appliance. "What should happen" says "the host the job is running
    against". That matches our setup, where the emulator serves a mirror of
    fullsend-ai/fullsend, but upstream may want to choose. Consider
    softening it to "a host and credential that match" if this looks too
    prescriptive.
