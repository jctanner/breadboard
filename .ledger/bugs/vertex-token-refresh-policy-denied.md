# The sandbox policy denies Claude Code's Vertex token refresh

## Status: Open — blocks B5 (the first real-model run)

## Investigation: stale gateway profile (2026-09-22)

The installed `fullsend-vertex-ai` profile is **not** the profile in the agents
repository. Read-only export from the running gateway returned resource version
1, display name `Fullsend Vertex AI`, and these binary rules:

```yaml
binaries:
  - /usr/bin/node
  - /usr/local/bin/node
  - /usr/local/lib/node_modules/@anthropic-ai/claude-code/**
```

The actual Claude executable is under `/usr/lib/node_modules/`, not
`/usr/local/lib/node_modules/`. Neither that executable nor its logged ancestors
matches the installed rules. The expected `**/claude.exe` rule is absent.
The source profile instead says `Fullsend Inference` and contains the four
glob rules described below. Therefore the original premise that those rules
were active in the gateway was not established by inspecting the source file.

### Why the old profile survives import

`internal/sandbox/sandbox.go:211`, `ImportProfile`, in Fullsend:

1. Checks a local hash cache keyed only by profile ID.
2. Attempts to delete the gateway profile, discarding its error/output.
3. Imports the source file.
4. Treats any import output containing `already exists` as success and writes
   the **new source file's hash** to the cache without comparing gateway content.

`ImportProfileVerified` clears the cache first but then only checks profile
existence. It does not check that the content matches.

OpenShell v0.0.110 rejects deletion when a sandbox uses the profile. A read-only
query confirmed the retained `agent-review-ca597` sandbox still attaches
`vertex-ai`, whose type is `fullsend-vertex-ai`. Gateway logs at
2026-09-22 12:21:28 and 12:40:47 UTC show `DeleteProviderProfile` returning gRPC
status 9 (`FAILED_PRECONDITION`), followed immediately by
`ImportProviderProfiles`. The source deletion guard and existing reference
explain why delete-and-reimport cannot replace this shared profile. The log
lines do not expose the profile ID or import diagnostics individually; the
installed profile export and retained provider reference provide that context.

### Policy selection and glob checks

The retained run-1283 sandbox artifact confirms the original denials. Rego's
`deny_reason` generates that binary-mismatch text only when an endpoint policy
exists but its binary check fails. `policy:-` means no complete endpoint-plus-
binary match, not that the provider was unattached. The separate `claude_code`
policy need not match a Google endpoint.

An offline gobwas/glob v0.2.3 control with `/` as delimiter produced:

```text
**/claude.exe                                       -> true
/usr/local/lib/node_modules/@anthropic-ai/claude-code/** -> false
```

Both were evaluated against the exact `/usr/lib/.../claude.exe` path. This is
a standalone glob control, not a test of the deployed Regorus engine. No
engine-level glob defect is needed to explain the denial: the desired glob
never appears in the installed profile.

### Fix direction and verification

Reconcile the gateway profile with the intended source using a supported
profile update, checking effects on existing consumers. Fix Fullsend's import
logic to propagate deletion failures and compare existing profile content
before accepting an `already exists` response or caching success. Existence
alone is insufficient on a shared gateway. Do not delete the unrelated review
sandboxes merely to make import succeed, or broaden the binary allowlist as
a substitute for fixing synchronization.

After reconciliation, export the profile to verify its binary rules, then run
the real-model scenario and verify allowed OAuth/inference requests. Retain the
dummy regression check separately. No live profile, provider, sandbox, or
deployment was changed during this investigation, and no model call was made.
The old run's logs were read from the retained artifact, not recreated.

The rest of this report is the original evidence and hypotheses; its claim
that the desired binary glob was active is superseded by the installed-profile
export above.

## Summary

With `runtime: claude` and `model: haiku`, the agent reaches the sandbox, starts
Claude Code, and then cannot obtain a Google access token:

```text
  💬 API Error: Could not refresh access token: policy_denied
  ✗ API Error: Could not refresh access token: policy_denied
  ! Agent exited with code 1
...
Error: validation failed after 2 iteration(s)
```

`policy_denied` is OpenShell's wording, not Google's. The sandbox's own policy
engine refused the connection.

Everything before the model call works: routing, authorization, OIDC, the mint,
credential scoping, sandbox creation, the pre-flight reaching the forge, the
repository copy. The dummy runtime passes all ten behaviour assertions on the
same stack. Only the model call fails.

Reproduced twice: run 1279 (issue 92) and run 1283 (issue 93).

## The evidence is downloadable now

This is the first bug in this series where the sandbox logs survive the run.
Do not re-derive them from a live sandbox.

```bash
A=https://github.local/api/v3/repos/fullsend-dev/triage-target
H="Authorization: token ghp_admin_default_token"

# The artifact from run 1283.
curl -sk "$A/actions/artifacts/2" -H "$H"        # index of files and sizes
curl -sk "$A/actions/artifacts/2/zip" -H "$H" -o evidence.zip

# Or one file at a time, without unpacking:
curl -sk "$A/actions/artifacts/2/files/fs-tri-f0709ad9dd21/logs/openshell-sandbox.log" -H "$H"
```

The bundle holds `openshell-sandbox.log` (75 KB), `openshell-gateway.log`,
both iterations' transcripts, `metrics.json` and `run-telemetry.jsonl`.

## What is established

Each of these was read from the run's own logs or from the sandbox image.

- **Every model call was refused; none succeeded.** 31 `DENIED` lines across two
  Claude processes (pids 550 and 683, one per iteration), all to
  `oauth2.googleapis.com:443`. Zero `ALLOWED` lines mention claude at all.
- **No policy matched.** Every denial carries `policy:-`. The reason text is
  `binary '/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe' not
  allowed in policy '_provider_vertex_ai'`, with
  `ancestors: [/usr/bin/dash -> /opt/openshell/bin/openshell-sandbox]` and a
  `SYMLINK HINT:` that OpenShell's own formatter truncates to `...`.
- **The host is allowed.** `profiles/fullsend-vertex-ai.yaml` permits
  `*.googleapis.com:443`, which covers `oauth2.googleapis.com`. The refusal is
  about the binary, not the endpoint.
- **The binary is listed too.** The same profile's allowlist is `**/claude`,
  `**/claude.exe`, `**/pi`, `**/node`.
- **Globs work in general.** `fullsend-github-ro.yaml` uses `**/gh` and matches
  `/usr/bin/gh` in this same sandbox — that is how the forge pre-flight passes.
- **OpenShell renames the binary itself.** At sandbox startup it canonicalises
  policy binary paths through the container filesystem:

  ```text
  Resolved policy binary symlink via container filesystem:
    original=/usr/local/bin/claude
    resolved=/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe
  ```

  and the same for `/usr/bin/codex` → `codex.js`, `/usr/bin/copilot` →
  `npm-loader.js`, `.venv/bin/python` → `python3.14`. So the `.exe` path in the
  denial is OpenShell's canonical name for the inode. Nothing invokes Claude by
  that name.
- **`.exe` is a real Linux binary.** It begins `\177ELF`, 64-bit. The name is an
  artifact of single-file compiled packaging, which is why upstream's profile
  lists both spellings.
- **Four names, one inode.** `/usr/bin/claude`, `/usr/local/bin/claude`,
  `.../claude-code/bin/claude.exe` and
  `.../claude-code-linux-x64/claude` are all inode `86949524`, 214687216 bytes.

## Explicitly ruled out, so it is not chased again

- **Missing provider credentials.** `openshell provider get vertex-ai` reports
  `Credential keys: <none>`, against `GH_TOKEN` for `github-ro`. That difference
  is *correct*, not the bug: the triage harness copies the credentials into the
  sandbox itself —

  ```yaml
  host_files:
    - src: ${GOOGLE_APPLICATION_CREDENTIALS}  ->  /tmp/.gcp-credentials.json
    - src: ${GCP_OIDC_TOKEN_FILE}             ->  /sandbox/workspace/.gcp-oidc-token
  ```

  so the vertex provider is pure network policy and Claude Code is meant to
  refresh its own token. An hour was spent on this; it is a dead end.
- **The model alias.** `haiku` resolves correctly:
  `→ Agent: claude-haiku-4-5@20251001`. Note this happens in Claude Code, not
  Fullsend — the claude runtime passes `--model 'haiku'` through verbatim and
  only applies repo-configured `models.aliases`, of which there are none.
- **The `.exe` name being a packaging mistake.** It is a real ELF binary and
  upstream expects it.

## What is NOT established

- **Why `**/claude.exe` does not match the path OpenShell resolved.** The rego
  (`openshell-supervisor-network/data/sandbox-policy.rego`) has an exact-path
  rule that skips globbing when the entry has no `*`, and a glob rule doing
  `glob.match(b.path, ["/"], p)` over `exec.path` plus ancestors, where `**`
  should cross `/`. By inspection it ought to match. It does not.
- **Whether the relevant policy is even attached.** `policy:-` on every denial
  says none matched. The startup log also mentions a separate `claude_code` L7
  policy with its own endpoints (`claude_code.endpoints[0]` appears in a
  validation warning). The question may be "why was no policy attached to this
  process" rather than "why did this glob fail". **This is the strongest lead.**

## A probe that did not work, so it is not repeated

Two disposable sandboxes were created from `fullsend-sandbox-local:k3s` with
`--provider vertex-ai`, staging copies of `node` at `/tmp/p/claude.exe`,
`/tmp/p/claude` (hardlinked to it), `/tmp/p/a/b/c/claude.exe` and
`/tmp/q/notallowed`, then attempting a TCP connect to
`oauth2.googleapis.com:443` from each.

**All four returned `EAI_AGAIN` — including the control.** DNS does not resolve
in a hand-made sandbox, so no network policy decision was recorded for any of
them and the glob question went untested. The real agent sandbox resolves DNS
fine, so the harness does setup the bare `sandbox create` does not: the run log
shows `Enabling providers v2`, `Importing profile: fullsend-vertex-ai`, then
`Ensuring provider: vertex-ai`. Reproducing that sequence is the prerequisite
for any further probing. Tried both with and without `--no-auto-providers`;
same result. Both sandboxes were deleted.

## Suggested next steps

Roughly by information gained per unit of effort.

1. **Find out why no policy attached.** `policy:-` is the loudest signal in the
   log and it has not been explained. Read how OpenShell decides which policy
   governs a process, and whether the `claude_code` L7 policy should have
   claimed this traffic instead of `_provider_vertex_ai`.
2. **Test the glob directly**, outside the sandbox. The rule is
   `glob.match("**/claude.exe", ["/"], "/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe")`.
   That is a five-line OPA or gobwas/glob check and settles the question this
   probe could not.
3. **If the glob is the cause**, the narrow local fix is an exact path in the
   profile — the rego's exact-path rule bypasses globbing entirely. Treat that
   as a workaround and report the glob failure upstream, because any deployment
   with Claude Code at that path has a policy that silently does not apply.
4. **Rule the version skew in or out.** The gateway and supervisor run 0.0.110
   while the CLI is built at Fullsend's pinned 0.0.116 revision. Version skew
   has already caused two bugs in this chain (`--detach`, and the sandbox image
   pull policy).

## An unrelated finding worth recording

The sandbox image carries **two different Claude Code builds**:

| path | inode | size | links |
| --- | --- | --- | --- |
| `/usr/bin/claude` and its three aliases | 86949524 | 214687216 | 2 |
| `/root/.local/bin/claude` | 86938577 | 240420560 | 1 |

Which one runs depends on `PATH`. That is not this bug — the denial names the
first — but it is worth resolving before anyone reasons about Claude Code's
version inside the sandbox.

## Context

- This is G42 in
  [`.ledger/plans/fullsend-integration-conformance-plan.md`](../plans/fullsend-integration-conformance-plan.md).
  It blocks B5, the breakpoint that asks whether the agent's output is useful.
- Switching back to the scripted path is two deletions:
  `FULLSEND_RUNTIME` and `FULLSEND_MODEL` repository variables on
  `fullsend-dev/triage-target`. The config file still says `runtime: dummy`, so
  removing the variables restores the ten conformance assertions.
- Those assertions only run under the dummy runtime. Whatever fixes this, keep
  a dummy run as a standing regression check — the real runtime retires that
  guard silently.
- Local deviations live in `deploy/fullsend/patches/` across three lists. The
  agents-mirror list already carries one provider-profile patch
  (`agents/0003`), which is the precedent for a profile change if one is needed.
