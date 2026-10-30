<!-- Draft for review. Not filed. -->
# runtime: dummy-runtime behaviour operations do not see the harness environment from .env

**Repository:** fullsend-ai/fullsend
**Parent:** none

---

### What happens

`assert_env` reports a variable as unset when the harness has delivered it
to the sandbox correctly:

```
! Dummy runtime: assert_env GH_HOST unset or empty:
! Agent exited with code 1
```

The harness environment is not process state in the sandbox. `bootstrapEnv`
(`internal/cli/run.go:3204`) writes it to `/sandbox/.env` once, during
setup. `harnessEnvLines` (line 3633) adds the `.env.d/*.env` files that
`host_files` contributes and the `env.sandbox` exports. The real runtimes
read this file before they run anything:

- `buildRunCommandWithDigests` (`internal/runtime/claude.go:806`) reads it
  through `claudeGuardedEnv`, which calls `envDataLoad`
  (`internal/runtime/claude_integrity.go:163`), for the Claude launch.
- `checkSandboxGitHubConnectivity` (`internal/cli/preflight_github.go:77`)
  reads it through `agentruntime.EnvDataLoad` (line 82) for the GitHub
  pre-flight.

Every sandbox-side behaviour operation in `internal/runtime/dummy.go` runs
through `sandbox.Exec`. Each call is a new `sh -c` (`internal/sandbox/sandbox.go:1540`)
and does not inherit anything from an earlier call. None of these
operations reads `.env`. As a result, a scripted scenario runs with an
environment that no real runtime sees.

By inspection of `origin/main`, this affects the following operations:

- `assert_env` (line 386) and `assert_not_jwt` (line 403) read the named
  variable with `printenv`. A variable that only `env.sandbox` or a
  `host_files` env file delivers is reported as unset.
- `http_probe` (`httpProbeCommand`, line 764) reads its `header_env`
  variable from `process.env` in `node`.
- `url_get` (`curl`), `assert_json` (`jq`), `read_file` and `assert_file`
  (`test -r`), and the in-sandbox part of `checkout_branch` (`git fetch` from
  the uploaded bundle, then `git commit`) run with the sandbox's base `PATH`.
  They also run without any variable that `.env` sets.

`checkout_branch` no longer needs a forge credential in the sandbox. Since
#8773 its `ls-remote` and `fetch` run on the runner. Its remaining sandbox
command uses only local git.

Variables that reach the sandbox's process environment by another route are
visible. An example is the OpenShell provider placeholder
`INFERENCE_GATEWAY_API_KEY`, which `e2e/behaviour/features/runtime/inference-gateway.feature`
asserts with `assert_env`. As a result, the gap affects only variables that
are delivered through `.env`.

### What should happen

A behaviour operation that runs a command for the scenario sees the same
harness environment that a real runtime launch sees: `.env`, the
`.env.d` files and the `env.sandbox` values. An `assert_env` on a variable
that the harness delivers passes, and an `assert_env` on a variable that the
harness does not deliver fails. If the harness environment file is missing
or cannot be read, the run reports that error. The run does not continue
silently.

### How to reproduce

1. Use a harness with `runtime: dummy` that sets a variable only through
   `env.sandbox`, for example `GH_HOST: example.com`.
2. Add a behaviour script with one operation, `assert_env GH_HOST`.
3. Run the harness with `fullsend run`.
4. The operation fails with `assert_env GH_HOST unset or empty`. In the same
   sandbox, `sh -c 'printenv GH_HOST'` prints nothing. After the harness
   environment from `/sandbox/.env` is loaded, the variable is set.

### Context

Found while running Fullsend end to end against a local GitHub API emulator.
The failure was reproduced in a live sandbox. The same assertion fails when
`.env` is not loaded and passes when it is loaded. A variable set in one
`exec` is not visible to the next `exec`.

Related: #8341. It records `assert_env` rows in the dispatch behaviour
scenarios that never passed and attributes them to variables not passed
through `env.sandbox`. By inspection, a variable passed through
`env.sandbox` is also not visible to these operations. The cause above is
therefore a second reason those rows would fail.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0009-load-the-harness-environment-for-behaviour-ops.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30)
- **Evidence:**
  - The error text, the live-sandbox diagnosis and the statement that the
    real runtimes load the file all come from the patch header.
  - The code paths come from code read on origin/main:
    - `dummy.go`: operation switch at lines 314-470, `executeCheckoutBranch`,
      and `httpProbeCommand` at line 764;
    - `sandbox.go:1540`;
    - `claude.go:794/806`;
    - `preflight_github.go:77-82`;
    - `run.go:3204` and `run.go:3633`.
  - Upstream now loads `.env` as data through `envDataLoad`/`EnvDataLoad`
    (#8498, #8574) instead of sourcing it. The issue therefore says "reads"
    and "loads", not "sources".
  - `INFERENCE_GATEWAY_API_KEY` is a provider credential:
    `run_gateway_egress.go:41`, set through the run-scoped provider. That
    explains why upstream's own `assert_env` scenarios on it pass.
  - The `GH_HOST` value in repro step 1 is an illustration. The header does
    not say how `GH_HOST` was delivered in the observed run.
- **Current state versus the patch:** since #8773 (`1124b035c`) and #8787
  (`6d68183a4`), `checkout_branch`'s remote access runs on the runner. The
  issue therefore makes no credential claim about it. All sandbox-side
  operations still run without `.env`. `write_fixture`'s mkdir and upload
  are omitted from the list, because the patch also leaves them
  independent.
- **Duplicate search (section 0009):** no duplicate.
  - #8341 (open): related, linked in Context. It covers the same `assert_env`
    symptom but gives a different cause.
  - #5987 and #5992: related to behaviour coverage, not to this cause.
    Unrelated.
  - #8300, #8306, #8280, #3820, #8932, #8809, #8521, #8228, #8824, #6875,
    #8149, #8801: unrelated.
- **Open questions for the reviewer:**
  - Should this be linked from #8341 as a comment instead of filed
    separately? The two overlap in symptom, but #8341 asks a product
    question and this issue is a runtime defect.
  - Repro step 4's "after loading, it is set" is phrased without naming a
    mechanism, so that it does not prescribe the fix.
