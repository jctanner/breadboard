# Dummy runtime checks `GH_HOST` without loading the sandbox environment

## Status: Fixed and verified (run 1259)

Run 1259, issue 89: `✓ Agent exited with code 0`. All ten behaviour
assertions pass, including `GH_HOST` and the restored `GH_ENTERPRISE_TOKEN`,
with the label applied and both comments posted by `fullsend-triage[bot]`.

One intermediate run was needed. With `GH_HOST` fixed, run 1253 failed on the
next assertion down: `read_file` resolves paths against the *target repository*
while `write_fixture`, `assert_file` and `assert_json` resolve against the
*workspace*, so `read_file output/agent-result.json` had never been able to
pass. That was a defect in the conformance script, not in this fix, and it was
invisible for exactly the reason recorded above — an earlier assertion always
failed first and the headline names only the first failure. The script now
exercises both bases deliberately, one operation each.

The Triage job still reports `failure`, on the composite action's final
`actions/upload-artifact` step, which this runner refuses rather than faking.
That is a separate gap and is tracked in the plan.

## Fix applied (2026-09-21)

`deploy/fullsend/patches/0009-load-the-harness-environment-for-behaviour-ops.patch`,
on the Go build list in `deploy/scripts/05i-build-fullsend.sh`. Upstream-bound.

Behaviour operations that run a command on the scenario's behalf now source the
harness environment file first — `read_file`, `url_get`, `checkout_branch`,
`assert_env`, `assert_file`, `assert_json`. `write_fixture`'s mkdir and upload
stay independent, per the fix direction above.

A missing or unreadable file fails with that as the stated reason rather than
being tolerated, so this cannot degrade back into an assertion that passes
against an environment nobody loaded. The file path is overridable on
`DummyRuntime` alongside `ExecFn`/`UploadFn`/`WriteResultsFn`, which is what
the three existing real-host-shell checkout tests needed; they were passing
only because nothing sourced anything.

Two tests added: one asserting every command-running op sources the file, one
asserting the missing-file case is reported as itself. `internal/runtime` and
`internal/cli` both pass, and all six patches apply in sequence and build.

The conformance behaviour script was corrected in the same pass
(`deploy/fullsend/seed/seed-behaviour-script.py`): its docstring had recorded
the wrong lesson from the earlier `GH_ENTERPRISE_TOKEN` failure — that the
sandbox does not set that variable — when the real cause was this defect. That
assertion is restored, because on a non-github.com host it is the variable gh
actually reads and therefore the one that proves which identity an agent acts
as. The docstring now also warns that the headline names only the first failed
operation, which is how this went unnoticed.

Not yet verified against a live run. Judge it on `behaviour-results.json`, not
on the headline or the post-script's comment.


## Investigation findings (2026-09-21)

The original report below confuses a value written to the sandbox's `.env`
file with a value exported into every sandbox exec process. The error does
**not** establish that Fullsend expanded `GH_HOST` to an empty string.

`internal/runtime/dummy.go`, `executeBehaviourOp`, constructs `assert_env` as:

```sh
v=$(printenv -- 'GH_HOST'); test -n "$v"
```

`DummyRuntime.execFn()` returns `sandbox.Exec`, which launches a fresh
`openshell sandbox exec ... -- sh -c <command>`. Neither layer sources
`/sandbox/workspace/.env`. In contrast, the GitHub preflight explicitly sources
that file, and the Claude runtime launch does too. The harness's `env.sandbox`
values are exports in that file, not process-global configuration for future
OpenShell exec sessions.

### Live control experiment

Created disposable sandbox `debug-g40-20260921` using the affected run's image,
`fullsend-sandbox-local:k3s`, without providers or workflow dispatch. Uploaded
a non-secret `/sandbox/workspace/.env` containing `GH_HOST=github.local`, an
example issue URL, and `FULLSEND_FORGE=github`. Ran the exact assertion before
and after sourcing the file, then checked a separate exec:

```text
unsourced assertion exit=1 GH_HOST=[UNSET]
sourced assertion exit=0 GH_HOST=[github.local]
next exec GH_HOST=[UNSET]
```

This reproduces the dummy assertion failure even with a correct, non-empty
environment file. The temporary sandbox was deleted after the experiment.
No runner, harness, image, or workflow changes were made.

### Evidence and limits

- Job 2565 confirms runtime `dummy`, image `fullsend-sandbox-local:k3s`, a
  successful GitHub preflight, then the failing `assert_env GH_HOST` operation.
- Overlay resolution does precede validation/expansion: `Compose` calls
  `ResolveOverlays` before returning. Validation establishes that the host
  variable is **set**, but does not establish that it is empty. The original
  deduction also depended on treating the later dummy failure as proof of an
  empty `.env` value, which is invalid.
- No reserved-key warning means the key was not skipped; it does not prove
  what value was written.
- The original sandbox `fs-tri-ad36e32ea272` has been deleted; querying its
  logs now returns `sandbox not found`. Its original `.env` contents were not
  recovered, so an additional upstream value problem is not conclusively
  excluded. The reproduced runtime defect alone is sufficient to fail this
  assertion regardless of a correctly delivered file value.
- The pod-level runner environment has no `GH_HOST`, but this is not the
  composite step environment: `_run_step` injects it separately.
- `setup-agent-env.sh` comes from the scaffold copied by
  `.github/workflows/reusable-triage.yml`, specifically
  `internal/scaffold/fullsend-repo/.github/scripts/setup-agent-env.sh`.
  It strips role prefixes from environment names and writes them to
  `GITHUB_ENV`; a `TRIAGE_GH_HOST` could override `GH_HOST`. Such an override
  was not observed in this investigation.
- The dummy behaviour loop continues after failed operations and reports only
  the first error in its headline. It can still write `agent-result.json`
  from a fixture and pass schema validation. Thus a post-script comment is
  not evidence that every assertion passed. Provider configuration also
  supplies `GH_TOKEN` independently, so its assertion passing does not prove
  `.env` was sourced.

### Fix direction

Load the harness environment when executing dummy behaviour operations, with
explicit error handling, so they receive the same environment as real runtime
launches. At minimum `assert_env` must source `.env` before checking values;
consider consistent handling for the other behaviour operations that depend
on PATH or credentials. Keep low-level upload/bootstrap execs independent of
`.env`, since those create the file in the first place. Moving values from
`env.sandbox` to a host-file fragment does not fix an unsourced environment.

Verify with an integration test that sets a variable only in `.env` and runs
the real assertion shell, then rerun the conformance workflow and inspect all
entries in `behaviour-results.json`, not just the first-error headline or
schema-validation outcome. No implementation fix was applied during this
investigation. The original report below is retained as history and its
empty-expansion claim is superseded by these findings.

## Summary

The Fullsend triage agent now gets all the way into a real sandbox, with a real
minted credential, and then fails its first meaningful assertion:

```
→ Iteration 1 of 2
  • Running agent

  ! Dummy runtime: assert_env GH_HOST unset or empty:
::notice::Agent completed (0s)

  ! Agent exited with code 1
```

`GH_HOST` is what tells `gh` inside the sandbox to address this stack's forge
rather than github.com. Without it every call an agent makes leaves the
appliance. The conformance behaviour script asserts it deliberately
(`deploy/fullsend/seed/seed-behaviour-script.py`), which is why the run stops
here instead of producing plausible-looking garbage.

This has never worked. It fails identically in run 1236 (job 2505) and run 1247
(job 2565). It is **not** caused by the credential-scoping fix in G39 — that
landed between those two runs and changed nothing here.

## Why it looked like it was working

Worth reading before you start, because it is the reason this went unnoticed.

Fullsend runs the post-script whether or not the agent exited non-zero. The
post-script reads the agent's result file, applies the label and posts the
triage comment. So a run whose agent failed still produces a labelled issue
with a sensible comment on it, and the terminal status comment still says
`✅ Success`. I read that as a completed agent run twice. The only place the
failure is visible is the job log and the run's own `conclusion: failure`.

If you are judging whether this is fixed, judge it on the absence of
`assert_env GH_HOST` in the job log, not on the issue.

## What is established

Each of these was read from the running system or the source, not assumed.

- **`env.sandbox` is delivered to the sandbox.** `buildSandboxEnvLines`
  (`internal/cli/run.go:2863`) is appended at `run.go:3061`, *after* the line
  that sources `.env.d/*.env`, and the comment there states env.sandbox wins on
  collision. So the mechanism patch `agents/0002` uses is the right one.
- **The value was exported as an empty string, not skipped.**
  `buildSandboxEnvLines` skips a key only when it is not a POSIX identifier or
  is in `reservedSandboxKeys`, and both paths print `WARNING:` to stderr. No
  such warning appears in the job log.
- **The harness actually in use carries the lines.** Run 1247 logged
  `Base: https://github.local/fullsend-ai/agents/raw/e99461f31abb1d5537380aa6e7640de2170a7b7e/harness/triage.yaml (fetched)`,
  and fetching that exact URL shows `GH_HOST: "${GH_HOST}"` and
  `GH_ENTERPRISE_TOKEN: "${GH_ENTERPRISE_TOKEN}"` in the GitHub overlay's
  `env.sandbox`. The patch is applied and the run is using it.
- **Expansion is plain `os.Getenv`.** The expander at `run.go:927` returns
  `os.Getenv(key)` for everything except `FULLSEND_DIR` and the OIDC deny list;
  `GH_HOST` is in neither. `h.Env.Sandbox` is expanded at `run.go:965`.
- **Minting completes before expansion.** `mintAgentToken` is called at
  `run.go:911`, the expander is defined at `run.go:927`. So a variable the mint
  sets is visible to expansion — this is how `GH_TOKEN` gets in.
- **Nothing in the live path assigns `GH_HOST`.** Searched the mirrored
  `action.yml` actually checked out by the run (fullsend@`0cee1da2`, fetched
  and confirmed 200/26 KB, not a 404), every patch under
  `deploy/fullsend/patches/`, and the target repo's four workflows. The only
  references are reads, in patches `0008` and `agents/0002`.

## The one strong deduction, and how to check it

`ValidateRunnerEnvWith` (`internal/harness/harness.go:707`) is called at
`run.go:951`, before expansion, and it explicitly checks every `${VAR}`
reference in `h.Env.Sandbox`. Its lookup is `os.LookupEnv`, and its documented
rule is that **an empty value passes and only a truly unset variable fails**.

The run did not fail validation. If overlays were already merged into `h.Env`
by that point, that means:

> `GH_HOST` is set in the Fullsend process, to the empty string.

That would rule out "the variable never reached the step" and point instead at
something assigning it empty.

**Check the premise before relying on it.** The deduction holds only if
overlay resolution happens before `run.go:951`. It appears to: `ResolveOverlays`
runs inside harness composition (`internal/harness/compose.go:278`), and the
log prints `✓ Harness loaded` long before sandbox setup. Confirm that rather
than inherit it from me — I have twice in this chain inferred a cause from
evidence that fit more than one story.

## What is NOT ruled out

Stated explicitly because an earlier bug document in this series carried a
"ruled out" table that was wrong, and cost time.

- I have **not** confirmed that the runner's `GH_HOST` reaches the composite
  action's inner step. `_run_step` in
  `checkouts/github-emulator/src/runners/emulator/runner.py:807` sets it
  unconditionally from `_emulator_host()` (line 105), which returns
  `urlparse(EMULATOR_URL).hostname or "github.local"` and cannot return empty.
  `_composite_step` (~line 1205) routes inner steps back through `_run_step`,
  so it *should* be set. I never observed it.
- Two greps I ran early returned nothing because the raw URL **404'd**, not
  because the content was absent — `.github/scripts/setup-agent-env.sh` at both
  the fullsend mirror path and the target repo path. Step 7 "Setup agent
  environment" runs that script, succeeds, and prints nothing. Where that file
  comes from, and whether it writes `GITHUB_ENV`, is genuinely unknown. Note
  that `runtime_env` (accumulated `GITHUB_ENV` writes) is applied at
  `runner.py:838`, *after* the base block that sets `GH_HOST` — so a
  `GH_HOST=` written there would win. **This is the most promising untested
  lead.**
- I have not checked whether any `${{ vars.X }}` / `${{ secrets.X }}` in the
  calling step's `env:` block renders to an empty assignment that collides.

## The probe that settles it in one run

Do this before theorising further. It distinguishes "unset in the step",
"set-but-empty in the step" and "set correctly but lost inside Fullsend",
which is the split everything else depends on.

Add a temporary mirror patch printing the value from inside the composite
action's own run step — the same process that invokes `fullsend run`:

```bash
echo "PROBE GH_HOST=[${GH_HOST-UNSET}] len=${#GH_HOST}"
```

`${GH_HOST-UNSET}` (one dash) distinguishes unset from empty; `${#GH_HOST}`
catches whitespace. Put it at the top of the `run:` block of the `id: run`
step in `action.yml` (~line 426 of the upstream file, the one that ends in
`fullsend run "${AGENT}"`).

Mirror patches for `action.yml` go in `MIRROR_PATCHES` in
`deploy/fullsend/seed/seed-upstream-fullsend.py` — **not** the Go build list in
`deploy/scripts/05i-build-fullsend.sh`. A patch in the wrong list does nothing
and does it silently. Re-seed with `./deploy/scripts/22-seed-fullsend.sh`; no
image rebuild is needed for a mirror-only change.

## How to reproduce

The stack must be running.

```bash
curl -sk -X POST "https://github.local/api/v3/repos/fullsend-dev/triage-target/issues" \
  -H "Authorization: token ghp_admin_default_token" \
  -H "Content-Type: application/json" \
  -d '{"title":"gh-host repro","body":"The README does not explain what this repository is for."}'
```

Then find the run and read the Triage job. **Pick the run named `fullsend`,
not the one named `M8 Fullsend role and event fixture`** — both fire on the
same `issues` event and the M8 one is always cancelled. Selecting on
`event == "issues"` alone gets you the wrong run; that mistake cost a cycle.

```bash
curl -sk "https://github.local/api/v3/repos/fullsend-dev/triage-target/actions/runs?per_page=8" \
  -H "Authorization: token ghp_admin_default_token" \
  | python3 -c 'import sys,json
for r in json.load(sys.stdin)["workflow_runs"]:
    print(r["id"], r["name"], r["event"], r["status"], r["conclusion"])'
```

Then the Triage job's log; the failure is a few minutes in, in step 8.

## If the fix turns out to be in the harness

If the probe shows `GH_HOST` is correct on the host and lost inside Fullsend,
the fix is Fullsend's. If it shows the runner never exported it to that step,
the fix is ours in `runner.py`.

There is also a third possibility worth holding in mind: that `env.sandbox` is
simply the wrong vehicle for a host-derived value, and these two variables
belong in the `host_files` env file instead —
`env/github/triage.env` in the agents repo, which today contains only:

```sh
export ISSUE_URL="${GITHUB_ISSUE_URL}"
export GH_TOKEN=${GH_TOKEN}
```

That file is expanded on the host and copied in, and it is the proven path for
the two variables that *do* arrive. Note that the two variables that arrive
have other explanations too — `FULLSEND_FORGE` comes from the harness forge
section, not `env.sandbox` — so nothing currently observed actually witnesses
`env.sandbox` expansion working end to end. That is worth establishing in the
same probe.

If the answer is the env file, `agents/0002` needs rewriting and its upstream
framing changes with it.

## Context

- This is G40 in
  [`.ledger/plans/fullsend-integration-conformance-plan.md`](../plans/fullsend-integration-conformance-plan.md),
  which carries the full chain. The 2026-09-21 entry "the identity fix
  verified, and a gap it uncovered" is this bug's origin.
- Local deviations live in `deploy/fullsend/patches/` across three lists: Go
  source before compilation, the Fullsend mirror, and the agents mirror. Each
  patch header says which list it belongs to and whether it is upstream-bound.
- Do not re-do G37 (sandbox had no `GH_HOST`/allowlist entry at all) or G39
  (ambient admin token outranking the minted one). Both are fixed and verified;
  G39's evidence is that the triage comment on issue 87 comes from
  `fullsend-triage[bot]` rather than `admin`.
- The sandbox itself is healthy: the pre-flight connectivity check passes and
  the proxy reset recorded in
  [`sandbox-proxy-resets-local-forge.md`](sandbox-proxy-resets-local-forge.md)
  no longer reproduces, because the sandbox image now bakes in the internal CA.
