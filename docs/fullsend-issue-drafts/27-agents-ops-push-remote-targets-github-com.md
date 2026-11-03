<!-- Draft for review. Not filed. Split out of 18 per the GLM and DeepSeek
     reviews (CC-1): the push remote is a different fault class (credential-
     bearing URL construction) from 18's validation/parsing faults. -->
# ops libraries: forge_set_push_remote pushes to github.com regardless of the configured host

**Repository:** fullsend-ai/agents
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

`forge_set_push_remote` in the code and fix libraries sets `origin` to
`https://x-access-token:<token>@github.com/<repo>.git`:

- `scripts/lib/github-code-ops.lib.sh:238`
- `scripts/lib/github-fix-ops.lib.sh:103`

On a GitHub host other than github.com, by inspection this sends the push
token to github.com and pushes the fix branch to a repository path on the
public host that the token is not valid for. The push fails; if the token
were valid there, the push would go to the wrong host.

These functions are reached from `post-code` and `pre-fix`/`post-fix`
(`post-code.src.sh:834`, `pre-fix.src.sh:255`). The bundled `scripts/*.sh`
files carry copies.

### What should happen

The push remote is built from the GitHub host the run is executing against,
so the fix branch is pushed to the configured host with the run's
credential. Behaviour on github.com is unchanged.

### How to reproduce

From a checkout of `main`:

```bash
bash -c 'source scripts/lib/github-code-ops.lib.sh
  g=$(mktemp -d); git -C "$g" init -q; git -C "$g" remote add origin x
  REPO_FULL_NAME=acme/widgets
  (cd "$g" && forge_set_push_remote TOKEN && git remote get-url origin)'
```

Output:

```
https://x-access-token:TOKEN@github.com/acme/widgets.git
```

The same call against `github-fix-ops.lib.sh` gives the corresponding
result.

### Context

Found while running Fullsend against a local GitHub API emulator on a
private hostname. That is not a GitHub Enterprise Server, but by inspection
this behaves the same way on any host other than github.com, including
GHES. The URL validation and parsing faults in the same libraries are
tracked in a sibling sub-issue.

---

## Draft notes (not part of the issue)

- **Split from:** 18-agents-ops-libraries-assume-github-com-urls.md, per the
  GLM and DeepSeek pre-filing reviews (2026-11-02): credential-bearing URL
  construction is a different fault class from validation/parsing and is
  independently fixable.
- **Local patches:** agents 0005 (`deploy/fullsend/patches/`), shared with
  draft 18.
- **Checked against:** fullsend-ai/agents@origin/main (2026-11-02):
  `forge_set_push_remote` at `github-code-ops.lib.sh:238` and
  `github-fix-ops.lib.sh:103`.
- **Duplicate search:** covered by draft 18's searches
  (`ops library github.com url`); no hit describes the push remote.
