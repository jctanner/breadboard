# Bug: Sandbox policy denies architecture-context Git fetch

## Summary

Inside the Fullsend strategy sandbox, `scripts/fetch-architecture-context.sh`
listed the architecture versions through the GitHub API, then failed to clone
`opendatahub-io/architecture-context`:

```text
error: RPC failed; HTTP 403 curl 22 The requested URL returned error: 403
fatal: expected flush after ref listing
Architecture context fetch exit status: 128
```

Strategy agents then ran without architecture context (pipeline 2067/job 4021,
RHAIRFE-8, 2026-10-07 12:22:19Z).

## Root cause (evidence-backed)

The 403 came from OpenShell's L7 policy inside the sandbox, not from GitHub,
a proxy or credentials. `policies/strategy.yaml` gave `github.com:443`
`protocol: rest, access: read-only`. That preset expands to `GET`, `HEAD`
and `OPTIONS` on `**` (`openshell-supervisor-network/src/l7/mod.rs`). Git
smart HTTP clone sends `GET .../info/refs?service=git-upload-pack` and then
`POST .../git-upload-pack` (protocol v2 `ls-refs`, then `fetch`). The POST
was denied, and Git reports that as "expected flush after ref listing".

The sandbox's own decision log (`/var/log/openshell.2026-10-07.log` in sandbox
container `228cbd075b8a`, job 4021) shows each attempt:

```text
12:22:19.248Z HTTP:GET  ALLOWED GET  api.github.com:443/repos/opendatahub-io/architecture-context/contents/architecture
12:22:19.580Z NET:OPEN  ALLOWED /usr/lib/git-core/git-remote-http -> github.com:443
12:22:19.687Z HTTP:GET  ALLOWED GET  github.com:443/opendatahub-io/architecture-context/info/refs
12:22:19.783Z HTTP:POST DENIED  POST github.com:443/opendatahub-io/architecture-context/git-upload-pack
              [policy:local_services engine:l7] reason=... not permitted by policy
```

The same GET-allowed, POST-denied pattern repeats at 12:24:24Z and 12:27:33Z
(later fetches by the strategy skills). The job-owned gateway log has no
github.com entries; enforcement happens in the sandbox supervisor.

Comparison probes, temporary directories only, same command:

| Where | Result |
| --- | --- |
| Host (git 2.55.0) | `GET info/refs` 200, `POST git-upload-pack` 200 ×2, anonymous; HEAD `4df4a8a8`, newest `rhoai-3.6-ea.2` |
| Runner build container (git 2.52.0, job 4021 pod, `/tmp`) | clone succeeds, HEAD `4df4a8a8` |
| Sandbox | GET allowed, POST denied by L7 policy (above) |

The repository is public and needs no authentication or redirects. TLS
verification held throughout: the clone got through the TLS handshake, and
the API call and `info/refs` succeeded.

Upstream OpenShell documents the same issue and fix. Its default GitHub
provider (`providers/github.yaml`, issue #1769) replaces the preset with
explicit rules that add `POST /**/git-upload-pack`.

The earlier 403 in batch 2057/job 4000 (RHAISTRAT-4/5) has the same signature
under the same policy. It was very likely the same cause, but that sandbox's
log no longer exists.

## Fix

Strat-creator `3fd1563ede66c6f3080606d36b7341ef4deb07e7` (pushed to
`feat/fullsend-strategy-entrypoint`) replaces the `github.com` preset with
explicit rules: `GET`, `HEAD` and `OPTIONS` on `**`, and
`POST /opendatahub-io/architecture-context/git-upload-pack`. It is narrower
than upstream's `/**/git-upload-pack`, because the only Git fetch from
github.com inside the sandbox is this script. The Fullsend build and the
results clone run outside the sandbox or against gitlab.local. Push
(`git-receive-pack`), other repositories' Git fetches, and any other POST
remain denied. The api/raw/codeload endpoints, TLS handling, local services,
binaries, Fullsend hooks, Vertex profile and the `claude-opus-4-6` pin are
unchanged.

`test_service_permissions_are_in_applied_policy` pins the exact rule set and
the fetch URL.

Both Breadboard CI fixtures now pin `3fd1563`:
`var/demos/fullsend-entrypoint-poc/strategy-ci/gitlab-ci.yml` and
`runner-validation/gitlab-ci.yml`. A new no-model diagnostic,
`runner-validation/publish.py --diagnostic architecture-fetch`, runs the real
fetch in the sandbox under the pinned policy and image. It checks
LATEST_VERSION, the sparse paths, the filter, and that document and overlay
files exist. It also checks that receive-pack and another repository's
upload-pack get 403.

## Checks

- Strat-creator `make test`: 795 passed, 1 skipped (112.76s).
  `git diff --check` clean.
- Strategy-ci fixture tests: 4 passed. CI YAML parses. Diagnostic
  `bash -n` and `py_compile` pass. Breadboard `git diff --check` clean.

## Status

Fixed and verified inside the sandbox (2026-10-07). Normal branch pin published
at8c7f6a2988e2f1b0ea9a541cfca0b6544e8e65cf; diagnostic branch final commit
0964954537811fa8bfd0c39d8467e3780c40590e. Both use3fd1563; native main preserved.
Existing local admin bootstrap was used without transcript credential searches.

Pipeline2070/build4026 and architecture-fetch4027 passed. Real fetch exit0 in
3.7s, HEAD4df4a8a8cad23798dc9d7816707c1632ff939112, newest rhoai-3.6-ea.2,
shallow/blob:none, exact sparse paths selected version+overlays.1025 document
files and36 overlay files have content. Supervisor records ALLOWED context
upload-pack and DENIED receive-pack/other-repo upload-pack, both denial probes403.
Source artifact confirms3fd1563 and hooks enabled; no model transcripts.
Cleanup exit0, no containers/job network, job pod gone.27 artifact entries have
zero managed credential hits. Five fixture regressions, syntax/diff checks pass.

First diagnostic2069/4025 fetched successfully in4.4s but failed its version
assertion: Git cone mode retains early-access -> rhoai-3.6-ea.2 symlink, which
is_dir() counted as a second version. Repository tree at fetched commit confirms
mode120000/target. Diagnostic now reports aliases and counts actual directories;
offline regression still rejects an actual extra version. No policy widening
was needed. No strategy/model work or historical-review edits were performed.

## Limitations

- RHAISTRAT-8 (job 4021) and RHAISTRAT-4/5 (job 4000) were reviewed without
  architecture context. This fix does not validate those reviews; see
  [skipped architecture review recorded as approve](../open/strategy-review-skipped-architecture-recorded-as-approve.md).
- If the fetch URL changes (for example to add `.git` or move to another
  repository), the POST rule must change too; the regression test asserts both.

## Related

- [Visible initial architecture fetch](../../tasks/done/strat-entrypoint-visible-context-fetch.md)
- [Fullsend entrypoint and strategy POC plan](../../plans/fullsend-entrypoint-strategy-poc.md)

## Pin follow-up (2026-10-07 15:10Z)

The strat-creator branch head is now `02ad362`, a docs-only pipeline diagram
commit on top of `3fd1563`. The GitLab branches were published with
`3fd1563`, and `source.sh` requires pin == branch head, so they must be
republished before the next strategy or diagnostic run. Both local CI
fixtures now pin `02ad362`. A further docs-only diagram revision, `78ab3f1`
(architecture-context source, results clone, policy summary), is committed
locally. GitHub returned Internal Server Error on three pushes (request
A96E:224301:19E410:1F65DD:6AC660DE). Once it is pushed, bump both pins again.
