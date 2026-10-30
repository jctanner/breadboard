<!-- Filed 2026-10-30 as https://github.com/fullsend-ai/fullsend/issues/8952 (the issue text is between the two rules). -->
# run: minted agent token is not used by gh on hosts other than github.com

**Repository:** fullsend-ai/fullsend
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md (filed standalone as the trial; attach once the parent exists)

---

### What happens

The same gap #8530 closed for `GITHUB_TOKEN` remains on every GitHub host
other than github.com, where `gh` reads a different pair of variables.

`mintAgentTokenAtLevel` (`internal/cli/run.go:7033`) writes the minted
installation token to every name in `agentTokenEnvVars`
(`run.go:7128-7130`), which is:

```go
var agentTokenEnvVars = []string{"GH_TOKEN", "GITHUB_TOKEN"} // run.go:6822
```

`gh` chooses the variable it reads by host. `gh help environment`:

> `GH_TOKEN`, `GITHUB_TOKEN` (in order of precedence): an authentication
> token that will be used when a command targets either `github.com` or a
> subdomain of `ghe.com`.
>
> `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN` (in order of precedence):
> an authentication token that will be used when a command targets a GitHub
> Enterprise Server host.

So when the run targets any other host, the mint writes to variables `gh`
does not read for that host. Every `gh` call the run makes after the mint
(pre/post scripts, `host_files` expansion, and anything else that inherits
the process environment) keeps using whatever `GH_ENTERPRISE_TOKEN` or
`GITHUB_ENTERPRISE_TOKEN` already held, usually the workflow's own token. If
neither is set, `gh` has no credential for the host.

The mint step reports success either way. Nothing in the log shows that the
calls that follow are not using the minted token.

The same gap is in `syncRunnerEnvTokens` (`run.go:6908`), which refreshes
only `agentTokenEnvVars` (and role-specific names) into `RunnerEnv` after a
remint, and in the cleanup, which restores only those names.

### What should happen

On a host other than github.com, `gh` calls made after a mint authenticate
with the minted token, exactly as they do on github.com. After cleanup, the
variables `gh` reads for that host hold the values they had before the mint.
Behaviour on github.com is unchanged.

### How to reproduce

`gh` behaviour alone (gh 2.92.0, empty config dir):

```console
$ GH_TOKEN=minted-token GH_ENTERPRISE_TOKEN=ambient-token gh auth token --hostname ghe.example.com
ambient-token
$ GH_TOKEN=minted-token gh auth token --hostname ghe.example.com
no oauth token found for ghe.example.com
$ GH_TOKEN=minted-token GH_ENTERPRISE_TOKEN=ambient-token gh auth token --hostname github.com
minted-token
```

In a run:

1. Run an agent with a mint URL configured, on a GitHub host other than
   github.com, from a workflow that exports `GH_ENTERPRISE_TOKEN` (so that
   `gh` works on that host at all).
2. Let the run post a comment with `gh` after the mint (for example from the
   post-script).
3. The comment is authored by the identity behind `GH_ENTERPRISE_TOKEN`, not
   the agent's App bot.

### Context

The point of the mint is that the run acts with a narrowly scoped App token
for its role and level. Off github.com the run keeps acting with the
credential it was launched with, which is typically broader, and with that
credential's identity in the audit trail. The run does not show that this
happened.

Found while running Fullsend against a local GitHub API emulator on a private
hostname: a status comment posted by the CLI as the minted bot identity sat
next to an agent comment posted as the workflow's actor. That is not a GitHub
Enterprise Server, but by inspection the same applies to any host `gh`
treats as GitHub Enterprise Server, which is any host other than github.com
and `*.ghe.com`.

#8530 added `GITHUB_TOKEN` to `agentTokenEnvVars` for the same reason on
github.com. #7231 is the earlier remint/`RunnerEnv` snapshot bug that
`syncRunnerEnvTokens` addresses.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0008-scope-the-minted-token-on-enterprise-forges.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30).
  `agentTokenEnvVars` (#8530, merged in #8534 as 7cffeb4e2) now covers
  `GH_TOKEN` and `GITHUB_TOKEN`; `GH_ENTERPRISE_TOKEN` and
  `GITHUB_ENTERPRISE_TOKEN` appear nowhere in non-test Go on main. The defect
  is still present.
- **Evidence:**
  - gh variable choice: quoted from `gh help environment` (gh 2.92.0); the
    `gh auth token` transcript was run locally with an empty
    `GH_CONFIG_DIR` and dummy values.
  - Observed symptom (bot status comment vs. actor-authored agent comment):
    patch header; also `.ledger/bugs/gh-host-empty-in-sandbox.md` (run 1259
    passes with `GH_ENTERPRISE_TOKEN` asserted).
  - Line numbers (`6822`, `6908`, `7033`, `7128-7130`): read on origin/main.
  - "Inherits the process environment": `inheritedScriptEnv` uses
    `os.Environ()` (`run.go:3362`), and the `syncRunnerEnvTokens` comment
    describes post-scripts reading `os.Environ()`.
- **Duplicate search:** `GH_ENTERPRISE_TOKEN` (0 hits) and
  `mintAgentToken enterprise` (1 hit: #7376, closed PR, steer receipt
  authentication; unrelated). No duplicate. Related, linked in Context:
  #8530 and #7231 (both cited in the code comments on main).
- **Open questions for the reviewer:**
  - The in-run reproduction steps are generalised from the emulator
    observation, not executed on main. Keep them, or keep only the `gh`
    transcript?
  - Whether the sandbox itself (not only the runner-side scripts) receives
    `GH_ENTERPRISE_TOKEN` depends on the agents repo's harness `env.sandbox`;
    on our setup that is a local agents patch. I left the sandbox out of the
    issue for that reason.
