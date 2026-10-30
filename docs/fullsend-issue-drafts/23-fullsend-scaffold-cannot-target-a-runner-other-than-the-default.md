<!-- Draft for review. Not filed. -->
# scaffold: installed workflows always target the default runner label, so they stay queued on installations without it

**Repository:** fullsend-ai/fullsend
**Parent:** none

---

### What happens

The scaffold renders every `__GH_RUNNER__` placeholder as
`config.DefaultGHRunner` (`ubuntu-24.04`, `internal/config/config.go:170`).
An installation cannot get any other runner label in its workflows.

The pieces needed for another label exist but nothing connects them:

- `RenderOptions.RunnerImage` (`internal/scaffold/render.go:15`) is
  documented as "GitHub Actions runner image; empty = use DefaultGHRunner".
  `resolvedRunner` (line 76) uses it when it is set.
- Both install paths build their options with
  `RenderOptionsForInstall(vendored bool, upstreamRef, upstreamTag string)`
  (line 19). These are `internal/scaffold/installfiles.go:38` and
  `internal/repos/remote_scaffold.go:76`. That constructor never sets
  `RunnerImage`, and no other caller sets it.

The rendered placeholder is the shim's `runs-on` for `stop-fix`
(`templates/shim-per-repo.yaml:73`). It is also the `runner_image` input
that the shim and the `prioritize` thin caller pass to the reusable
workflows (`shim-per-repo.yaml:52`, `.github/workflows/prioritize.yml:45`).
The reusable workflows then use `runs-on: ${{ inputs.runner_image }}` for
every agent job, for example `reusable-dispatch.yml:119`.

When an installation's runners do not carry the `ubuntu-24.04` label, the
jobs wait in the queue indefinitely. No error or warning is reported, and
the run never starts. One example is self-hosted runners with their own
labels. The only workaround is to edit the installed workflows after each
install, and the next install or upgrade overwrites the edit.

### What should happen

An installation whose runners use a label other than the default can get
installed workflows that target its runners. Installations that do not
configure anything keep `ubuntu-24.04`.

### How to reproduce

1. Use an organisation or repository whose only Actions runners are
   self-hosted with labels such as `[self-hosted, linux]`, and no
   `ubuntu-24.04` runner.
2. Install Fullsend into it.
3. Trigger a dispatch, for example by opening an issue.
4. The `fullsend` workflow run's jobs stay `queued` with
   `runs-on: ubuntu-24.04`. They never start and report no error.

Code-level: `RenderOptionsForInstall(false, "", "")` returns options with
`RunnerImage == ""`, so `RenderTemplate("templates/shim-per-repo.yaml", ...)`
always writes `ubuntu-24.04`.

### Context

Found while running Fullsend end to end against a local GitHub API emulator.
The emulator's self-hosted runners do not carry the `ubuntu-24.04` label.

The placeholder and the field were added in #2659 (for #2611). Its PR
description gives "Pass `RunnerImage` in `RenderOptions`" as the override
for scaffold templates. No install path does that today.

Related: #5899, the open discussion about running Fullsend jobs on
self-hosted runners. That arrangement would need this override.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0012-let-an-installation-name-its-runner.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30)
- **Evidence:**
  - The "sits queued indefinitely, no error, no warning" symptom comes from
    the patch header.
  - The code facts come from code read on origin/main: `render.go:11-21`
    and `render.go:76-80`, `config.go:169-170`, the two
    `RenderOptionsForInstall` callers, and the `__GH_RUNNER__` sites in the
    scaffold templates. The `runs-on` lines come from a grep for
    `runner_image` in `.github/workflows/`.
  - The patch header also names `layers/workflows` as a caller. That caller
    does not exist on origin/main (only `installfiles.go` and
    `remote_scaffold.go` call it), so the issue does not mention it.
  - The intent of #2659 comes from its PR body, read through the API. The
    repro labels are illustrative.
- **Duplicate search (section 0012, plus one extra search for
  `runner_image`):** no duplicate.
  - #5899 (open): related, linked. It is a discussion about self-hosted
    runners and does not report this gap.
  - #2659 (closed PR) and #2611 (closed): related, linked as the origin of
    `__GH_RUNNER__` and `RunnerImage`.
  - #7359, #6244, #7281, #8812, #7403 (shim label filters), #7605, #7606,
    #1381, #7988, #8875, #918, #6621, #7680, #6538, #8717: unrelated.
    Those are label filtering for dispatch, not `runs-on` labels.
  - #8865 and #8878 (GitLab runner image tag), #8162, #7196, #6356:
    unrelated.
- **Open questions for the reviewer:**
  - This adds configuration surface (a per-installation runner label).
    Upstream may want an ADR or a design decision on where the setting
    lives before an agent implements it. The issue deliberately says
    nothing about how to configure it. Consider adding the `needs-adr` or
    `design` label, or a line asking for one, when filing.
  - Repro steps 1-4 are inferred from the header's symptom and the code. The
    observed case was the emulator's runners, not a real self-hosted
    github.com organisation.
