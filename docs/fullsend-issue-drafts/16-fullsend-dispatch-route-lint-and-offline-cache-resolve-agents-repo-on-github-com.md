<!-- Draft for review. Not filed. -->
# cli: `dispatch --route`, `lint` and the offline cache resolve the agents repo on github.com

**Repository:** fullsend-ai/fullsend
**Parent:** #TBD — 10-fullsend-tracking-github-com-host-assumption.md

---

### What happens

Besides `fullsend run` (tracked in a sibling sub-issue), three other readers
of the `fullsend-ai/agents` fallback assume github.com. All points below are
by inspection of origin/main.

1. **`fullsend dispatch --route`.** `routeBuiltinAgent` builds its fallback
   client with a bare `gh.New("")` (`internal/cli/dispatch_route.go:222`),
   which targets api.github.com regardless of `GITHUB_API_URL`. On another
   host the harness cannot be resolved, so its `role:` is never read. The
   route then requires write access (`dispatch_route.go:228-248`) and skips
   any actor below write with reason `harness unavailable; actor below write`
   (`:266`), including actors the harness role would have admitted. The
   warning it logs, `Could not resolve the <agent> harness, requiring write
   access: <err>`, carries the api.github.com error, so it reads as a
   credential or network failure rather than a wrong host.
2. **`fullsend lint`.** The fallback client is a bare
   `gh.New(composeGitToken)` (`internal/cli/lint.go:98`), so lint resolves
   the agents repo against api.github.com in the same way.
3. **Offline cache scan and route label.** `cachedPinnedAgentsRepoFile`
   (`internal/cli/run.go:7507`, `:7560`) and `routeHarnessLabel`
   (`dispatch_route.go:298-299`) recognise an agents-repo harness only by
   the literal prefix `https://raw.githubusercontent.com/fullsend-ai/agents/`
   (`defaultAgentsRepoURLPrefix`). They match what the online fallback
   fetches today, but on another host neither recognises a harness fetched
   from that host: offline resolution reports `No cached <noun> from
   fullsend-ai/agents`, and the decision log has no `agents@<sha>` label.

`internal/cli` already has `newGitHubLiveClient`
(`internal/cli/github_client.go:137`), which honours `forge.github.url` and
falls back to `GITHUB_API_URL`; these sites do not use it.

### What should happen

On a host other than github.com, `dispatch --route` and `lint` resolve the
agents repo on the configured host, a route with a resolvable harness
applies that harness's role threshold, and the offline scan and route label
recognise harnesses fetched from that host. Behaviour on github.com is
unchanged.

### How to reproduce

Code-level, since these were found by reading rather than from a failing run:

1. Set `GITHUB_API_URL` to a GitHub host other than github.com.
2. Call `routeBuiltinAgent` with `forgeClient: nil` for `triage` on an event
   from an actor with the triage role, with an `agents[].trigger` and no
   `source:`. The harness lookup goes to api.github.com, the route logs
   `Could not resolve the triage harness, requiring write access`, and the
   decision is `skip` with `harness unavailable; actor below write`.
3. `routeHarnessLabel(cfg, "triage", deps)` with
   `deps[0].URL = "https://<host>/fullsend-ai/agents/raw/<sha>/harness/triage.yaml"`
   returns `""`.

### Context

Found while running Fullsend against a local GitHub API emulator; by
inspection this applies to any host other than github.com, including GitHub
Enterprise Server. #8873 (open) concerns which revision the offline scan
chooses; it touches the same function but not the host.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0015-resolve-the-agents-repo-in-dispatch-lint-and-offline-cache.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30).
  `dispatch_route.go:222`, `lint.go:98`, `run.go:7507/7560`,
  `dispatch_route.go:298-299` all unchanged.
- **Evidence:** everything here is code reading. The patch header says it
  was "found while rebasing the patch set onto v0.52.0", not from a failing
  run, and the ledger has no log of the route warning, so the body says "by
  inspection" throughout and the repro is code-level.
- **Patch header claim corrected:** the header says the route's threshold
  "fails closed to write without saying the harness was never found". On
  origin/main that is not accurate: `dispatch_route.go:247` logs `Could not
  resolve the %s harness, requiring write access: %v` and `:266` uses the
  reason `harness unavailable; actor below write` (added in b4a4b94cd /
  44fdffc56, #8726). The body states the true consequence: the role
  threshold is lost and the logged error names api.github.com, not the host.
- **Offline cache point:** on upstream main the offline scan is consistent
  with the online fallback (both use raw.githubusercontent.com); the
  mismatch our patch fixes only exists once the online path addresses
  another host (our 0005). The body frames it as "does not recognise a
  harness fetched from that host", not as an independent upstream failure.
  Repro step 2 checked by reading: agents@8f819a9 `harness/triage.yaml`
  has `role: triage`; `harnessdispatch.RequiredActorRole` maps triage to
  the triage threshold and an empty role to write (`auth.go:83-89`).
  The `<host>/fullsend-ai/agents/raw/<sha>/...` URL in repro step 3 is the
  GHES raw-URL form also used in the ParseRawContentURL sibling; it is an
  illustrative input, not a claim about what upstream builds.
- **Duplicate search (section `0015`):** no duplicate.
  - #8873 (open) / PR #8939 (open), offline agents-revision selection:
    related (same function), linked in Context.
  - agents#1835, agents#1752 (lint scope / CI): unrelated.
  - #7834, #7451, #7907, #5649, #6654, #4100, #792, #2042, agents#1849,
    agents#1749, #8932, agents#1844: unrelated.
- **Open questions for the reviewer:**
  - Whether item 3 is worth keeping in the body at all, given it is only
    visible after the online path is fixed.
