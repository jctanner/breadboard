<!-- Draft for review. Not filed. -->
# ops libraries: review, code, fix and other GitHub stages assume github.com URLs

**Repository:** fullsend-ai/agents
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

On a GitHub host other than github.com, the review stage stops in its
pre-script, before the agent runs:

```
ERROR: PR_URL does not match expected GitHub pattern: https://<host>/<owner>/<repo>/pull/107
```

The GitHub ops libraries under `scripts/lib/` write `https://github.com`
into URL validation, URL parsing and the push remote. That causes three
separate faults:

1. **Validation** matches `^https://github\.com/...` by name, so a valid
   URL on the configured host is rejected.
2. **Parsing** strips the literal `https://github.com/` with `sed`. On
   another host nothing is stripped, so the repository becomes
   `https://<host>/<owner>/<repo>`.
3. **Push remote:** `forge_set_push_remote` in the code and fix libraries
   sets `origin` to `https://x-access-token:<token>@github.com/<repo>.git`.
   By inspection, on another host this sends the push token to github.com.

A related effect of (1): the host is not taken from the run, so with
`GITHUB_SERVER_URL` set to another host, a `github.com` URL still passes
validation.

The same libraries already use `${GITHUB_SERVER_URL:-https://github.com}`
for their run links (`forge_get_workflow_run_url`,
`github-code-ops.lib.sh:349`, `github-fix-ops.lib.sh:154`).

Sites on `main`:

| Library | Line | Function | Fault |
| --- | --- | --- | --- |
| `github-review-ops.lib.sh` | 22 | `forge_validate_pr_url` | validation |
| `github-review-ops.lib.sh` | 29 | `forge_parse_pr_url` | parsing |
| `github-code-ops.lib.sh` | 29 | `forge_validate_issue_url` | validation |
| `github-code-ops.lib.sh` | 37 | `forge_parse_issue_url` | parsing |
| `github-code-ops.lib.sh` | 43 | `forge_extract_repo_from_url` | parsing |
| `github-code-ops.lib.sh` | 241 | `forge_set_push_remote` | push remote |
| `github-fix-ops.lib.sh` | 37 | `forge_validate_pr_url` | validation |
| `github-fix-ops.lib.sh` | 45 | `forge_parse_pr_url` | parsing |
| `github-fix-ops.lib.sh` | 106 | `forge_set_push_remote` | push remote |
| `github-prioritize-ops.lib.sh` | 27 | `forge_validate_issue_url` | validation |
| `github-prioritize-ops.lib.sh` | 34 | `forge_parse_issue_url` | parsing |
| `github-retro-ops.lib.sh` | 22 | `forge_validate_originating_url` | validation |
| `github-retro-ops.lib.sh` | 30 | `forge_parse_originating_url` | parsing |
| `github-scribe-ops.lib.sh` | 107 | `forge_issue_url_base` | builds a `https://github.com/<repo>/issues` link |

These are reached from `pre-review`/`post-review`, `pre-code`/`post-code`
(`pre-code.src.sh:66` and `:71` use the validation and
`forge_extract_repo_from_url`), `pre-fix`/`post-fix`,
`pre-prioritize`/`post-prioritize`, `pre-retro`/`post-retro`, and
`post-scribe.src.sh:546`. The bundled `scripts/*.sh` files carry copies.

### What should happen

Each GitHub stage accepts an issue or PR URL on the GitHub host the run is
executing against, parses the repository as `<owner>/<repo>`, pushes to and
links to that host, and rejects URLs on a different host. Behaviour on
github.com is unchanged.

### How to reproduce

From a checkout of `main` (`_gha_sanitize` is stubbed because these
libraries expect a caller to define it):

```bash
export GITHUB_SERVER_URL=https://ghe.example.com
bash -c '_gha_sanitize(){ printf %s "$1"; }
  source scripts/lib/github-review-ops.lib.sh
  PR_URL=https://ghe.example.com/acme/widgets/pull/107 forge_validate_pr_url; echo "rc=$?"
  PR_URL=https://github.com/acme/widgets/pull/107 forge_validate_pr_url; echo "rc=$?"'

bash -c 'source scripts/lib/github-code-ops.lib.sh
  g=$(mktemp -d); git -C "$g" init -q; git -C "$g" remote add origin x
  REPO_FULL_NAME=acme/widgets
  (cd "$g" && forge_set_push_remote TOKEN && git remote get-url origin)'
```

Output:

```
ERROR: PR_URL does not match expected GitHub pattern: https://ghe.example.com/acme/widgets/pull/107
rc=1
rc=0
https://x-access-token:TOKEN@github.com/acme/widgets.git
```

The same calls against `github-fix-ops.lib.sh`, `github-prioritize-ops.lib.sh`,
`github-retro-ops.lib.sh` and `github-scribe-ops.lib.sh` give the
corresponding results.

### Context

Found while running Fullsend against a local GitHub API emulator on a
private hostname. That is not a GitHub Enterprise Server, but by inspection
these paths behave the same way on any host other than github.com,
including GHES.

Only the review stage was observed failing in a run. The code and fix sites
were found by reading the code, and the prioritize, retro and scribe sites
by inspection only; those stages were not run on another host. The
function-level output above was produced directly from the libraries on
`main`.

The triage library has the same validation and parsing problem; that is
tracked separately. On the GitLab side, a hard-coded host allowlist was
reported and fixed in #920 / #921.

---

## Draft notes (not part of the issue)

- **Parent lives in fullsend-ai/fullsend.** File it there first; attach this
  issue as a cross-repository sub-issue.
- **Local patch:** `deploy/fullsend/patches/agents/0005-address-the-configured-github-host-in-the-remaining-ops-libraries.patch`
  (covers review, code and fix only).
- **Checked against:** fullsend-ai/agents@8f819a9 (origin/main, 2026-10-30).
  Found with `git grep -n 'https://github.com' origin/main -- scripts/lib/`
  plus the escaped `github\.com` regexes.
- **Evidence:**
  - Review error text and "where a review run stops, before the agent does
    anything": patch 0005 header. Header also says it was "Exercised locally
    on the review stage only; the code and fix stages have not been run".
  - The three faults and the github.com-URL-still-accepted effect: patch
    0005 header; I confirmed each at function level against `git archive
    origin/main scripts` (output above is verbatim; `ghe.example.com` is a
    placeholder). I also confirmed `forge_validate_pr_url` in fix-ops,
    prioritize/retro validation failures, and `forge_issue_url_base`
    returning `https://github.com/acme/widgets/issues`.
  - "Sends the push token to github.com" is marked by inspection: the
    remote URL was confirmed, no push was executed.
  - Not included: other `https://github.com` hits in `scripts/lib/` that
    already use `${GITHUB_SERVER_URL:-https://github.com}`
    (`gitlab-code-ops:561`, `gitlab-fix-ops:223`,
    `post-failure-report:229`, `github-scribe-ops:118`), and
    `gitleaks-install.lib.sh:113`, which downloads gitleaks from
    github.com releases. That one is a tool download rather than a forge
    URL; the reviewer may want it mentioned.
  - `forge_extract_repo_from_url` (code-ops:43) is covered by our patch.
    It returns the whole URL unchanged for another host, so the
    `pre-code.src.sh:74` repo-match check would also trip. That follows
    from reading the code, not from a run.
- **Duplicate search (section `a0005`):** no duplicate.
  - agents#813 / #815 / #872 (closed PRs): made code, review and fix
    multi-forge. These introduced the GitHub/GitLab library split; related
    history, not linked.
  - agents#920 / #921 (closed, from section `a0001`): GitLab host allowlist.
    Related, linked in Context.
  - agents#1675 (closed PR, signed commits via API): touches code-ops,
    unrelated to host.
  - agents#981, #1665, #1191, fullsend#6603, #6947: unrelated.
- **Open questions for the reviewer:**
  - Split the push-token case (fault 3) into its own issue? It is the only
    one with a credential-exposure angle, and it is the one an agent might
    otherwise leave until last.
  - Keep prioritize/retro/scribe in this issue, given they were never run?
    They are listed as inspection-only.
