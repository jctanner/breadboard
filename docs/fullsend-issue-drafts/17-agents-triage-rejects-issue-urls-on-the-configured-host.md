<!-- Draft for review. Not filed. -->
# triage: tracker_validate_issue_url rejects issue URLs on GitHub hosts other than github.com

**Repository:** fullsend-ai/agents
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

On a GitHub host other than github.com, the triage pre- and post-scripts
reject a valid issue URL before the triage agent does anything:

```
ERROR: ISSUE_URL does not match expected pattern: https://<host>/<owner>/<repo>/issues/79
```

Two functions in `scripts/lib/github-triage-ops.lib.sh` name github.com
directly:

- `tracker_validate_issue_url` (line 22) matches `ISSUE_URL` against
  `^https://github\.com/...`, so any other host fails.
- `tracker_parse_issue_url` (line 29) strips the literal
  `https://github.com/` with `sed`. For a URL on another host nothing is
  stripped, and `REPO` is set to `https://<host>/<owner>/<repo>` instead of
  `<owner>/<repo>`.

Both are called from `scripts/pre-triage.src.sh` (lines 27, 29) and
`scripts/post-triage.src.sh` (lines 97, 98), and are bundled into
`scripts/pre-triage.sh` and `scripts/post-triage.sh`.

### What should happen

The triage scripts accept an issue URL on the GitHub host the run is
executing against, and parse `REPO` as `<owner>/<repo>` for it. Behaviour on
github.com is unchanged.

### How to reproduce

From a checkout of `main`:

```bash
GITHUB_SERVER_URL=https://ghe.example.com \
ISSUE_URL=https://ghe.example.com/acme/widgets/issues/79 \
bash -c 'source scripts/lib/github-triage-ops.lib.sh
         tracker_validate_issue_url; echo "rc=$?"
         tracker_parse_issue_url; echo "REPO=$REPO"'
```

Output:

```
ERROR: ISSUE_URL does not match expected pattern: https://ghe.example.com/acme/widgets/issues/79
rc=1
REPO=https://ghe.example.com/acme/widgets
```

### Context

Found while running Fullsend's triage stage against a local GitHub API
emulator on a private hostname. That is not a GitHub Enterprise Server, but
by inspection the same check applies to any host other than github.com,
including GHES.

Other code in this repository already takes the host from
`GITHUB_SERVER_URL`: for example `forge_get_workflow_run_url` in
`scripts/lib/github-code-ops.lib.sh` (line 349), which
`scripts/pre-code-jira.sh` embeds for its run URLs. On the GitLab side, a
hard-coded host allowlist was reported and fixed in #920 / #921.

The same pattern appears in the review, code, fix, prioritize, retro and
scribe libraries; that is tracked separately.

---

## Draft notes (not part of the issue)

- **Parent lives in fullsend-ai/fullsend.** File it there first; attach this
  issue as a cross-repository sub-issue.
- **Local patch:** `deploy/fullsend/patches/agents/0001-accept-a-configured-github-host.patch`
- **Checked against:** fullsend-ai/agents@8f819a9 (origin/main, 2026-10-30).
  Both function bodies are unchanged from what the patch modifies.
- **Evidence:**
  - Error text and "rejected before the triage agent does anything": patch
    0001 header (and the parent draft's symptom list), observed in a triage
    run against the emulator.
  - Line numbers, callers, and the bundled scripts: read from origin/main.
  - The reproduction output: I ran it against `git archive origin/main
    scripts`, verbatim output above. `ghe.example.com` is a placeholder host.
  - The patch header says `scripts/pre-code-jira.sh` "already" uses
    `GITHUB_SERVER_URL` for run URLs. On origin/main the uses are at
    `pre-code-jira.sh:946` and `:1603`, which are bundled copies of
    `github-code-ops.lib.sh:349` and `gitlab-code-ops.lib.sh:561`, not code
    in `pre-code-jira.src.sh`. The issue body cites the source library
    instead.
- **Duplicate search (section `a0001`):** no duplicate.
  - agents#920 / #921 (closed): GitLab host allowlist in
    `forge_validate_issue_url`. Same class of problem on the GitLab side.
    Related, linked in Context.
  - agents#1732 / #1733 (closed): GitLab triage/scribe lose custom HTTPS
    ports. Related, but GitLab and about ports. Not linked.
  - agents#827, #686, #1490, #1125, #1665, #1588, #1739, #327, #1149,
    fullsend#8402: unrelated (they touch the same scripts or messages for
    other reasons).
- **Open questions for the reviewer:**
  - Keep the GitLab #920 link? It is useful precedent, but it could read as
    a suggestion to copy that fix.
