# readonly_repo fails on OpenShell's Kubernetes driver: the .git chown needs root

Found 2026-11-08 in the behaviour-test T2 run (BT-B4), in two review
scenarios: `fix-authorization.feature` (only the registered review bot's
changes-requested review starts fix) and `fork-bash-routing.feature`. Both
failed with:

```
chown: changing ownership of '/sandbox/workspace/target-repo/.git/...': Operation not permitted
Error: read-only repo enforcement failed: exit code 1
```

## Cause

`fullsend run` step 8c, `internal/cli/run.go` (line 2527 at upstream
`5c41e937c`), runs inside the sandbox:

```
find <repo> -path '*/.git' -prune -o -not -type l -exec chmod a-w {} + &&
  chown -R sandbox:sandbox <repo>/.git && chmod -R u+w <repo>/.git
```

The chown assumes the exec user is root. Two facts on bb's stack rule that
out:

- OpenShell 0.1.4's Kubernetes driver runs the agent container as uid/gid
  10001, with `runAsNonRoot`, `capabilities.drop: [ALL]` and
  `allowPrivilegeEscalation: false`. This was read from a live sandbox pod's
  spec.
- In `ghcr.io/fullsend-ai/fullsend-sandbox:latest`, `sandbox` is uid 998.

In the failing runs, the `chmod a-w` on the working tree succeeded. It sits
before the chown in the `&&` chain, and `chmod` requires ownership, so the
exec user owns the uploaded tree.

A probe pod with the same security context reproduced it: `id` reports 10001,
`chown -R sandbox:sandbox` exits 1 with EPERM, and `chmod -R u+w` succeeds.
Upstream CI uses the Docker driver, which execs as root, so the problem does
not show there. Every `readonly_repo: true` harness fails. Of the agents
repo's harnesses, only `review.yaml` sets it.

## Local workaround

`deploy/fullsend/patches/0022-chown-the-readonly-repo-git-dir-only-as-root.patch`
is in the 05i build list. It runs the chown only when `id -u` is 0, because a
non-root exec user already owns what it extracted. The command moves into
`readonlyRepoCommand`, which has two tests: the non-root path, and the guard.

Verification:

- Old command as non-root: exits 1. New command: succeeds, and leaves the
  working tree read-only and `.git` writable.
- `go build ./...` and `go vet ./internal/cli/` pass.
- The new tests and the `TestForceRemoveAll*` tests pass.
- Not yet deployed or run end to end.

The workaround does not fix one limitation. As non-root owner, the agent can
`chmod` the tree back, so on this driver read-only is advisory.

## Upstream

No duplicate was found on 2026-11-08. Searches: readonly_repo, chown sandbox,
"read-only repo enforcement", kubernetes driver non-root. Related issues:

- fullsend#9048 (open, ours): another Kubernetes-driver/uid mismatch.
- fullsend#7927: another readonly_repo gap.

Not filed. The upstream filing workflow belongs to the other session. Show
the draft to the owner first.

### Draft issue (fullsend-ai/fullsend)

**Title:** `readonly_repo` harnesses fail on OpenShell's Kubernetes driver: the `.git` chown needs root

### What happens

With OpenShell 0.1.4 (the version pinned in
`.github/scripts/openshell-version.sh`) and its Kubernetes compute driver,
every harness with `readonly_repo: true` fails before the agent starts.
`review` is one of them. `fullsend run` makes the target repo read-only
(`internal/cli/run.go`, step 8c) with:

```
find <repo> -path '*/.git' -prune -o -not -type l -exec chmod a-w {} + &&
  chown -R sandbox:sandbox <repo>/.git && chmod -R u+w <repo>/.git
```

The chown fails on every entry in `.git`, and the run stops:

```
chown: changing ownership of '/sandbox/workspace/target-repo/.git/HEAD': Operation not permitted
...
Error: read-only repo enforcement failed: exit code 1
```

The Kubernetes driver runs the sandbox's agent container as uid/gid 10001,
with `runAsNonRoot: true`, `capabilities.drop: [ALL]` and
`allowPrivilegeEscalation: false`. In `fullsend-sandbox`, the image's
`sandbox` user is uid 998. A process with that identity cannot change
ownership to another uid:

```
$ id
uid=10001 gid=10001 groups=10001
$ getent passwd sandbox
sandbox:x:998:998::/sandbox:/bin/bash
$ chown -R sandbox:sandbox /tmp/t/.git; echo $?
chown: changing ownership of '/tmp/t/.git': Operation not permitted
1
```

On the Docker driver, `openshell sandbox exec` runs as root, so the chown
succeeds there and the problem does not appear.

### What should happen

A `readonly_repo` harness runs on the Kubernetes driver too. Its working tree
is read-only to the agent, and `.git` stays writable to it.

### How to reproduce

1. Deploy OpenShell 0.1.4 with the Kubernetes compute driver.
2. Run a harness with `readonly_repo: true` (for example `review`) against a
   pull request, using the `fullsend-sandbox` image.
3. The run fails at "Make the target repo read-only" with the error above.

The chown can also be checked without OpenShell. Run the image as uid 10001
with all capabilities dropped, then try `chown -R sandbox:sandbox` on a
directory that uid created.

### Context

Found running Fullsend's behaviour suite against a Kubernetes-hosted stack.
The two review scenarios in `fix-authorization.feature` and
`fork-bash-routing.feature` fail this way. Here, the exec user already owns
the files it uploaded, so `chmod a-w` and `chmod u+w` both work; only the
chown fails.

One consequence goes beyond the failure. When the agent runs as the owner of
the tree, `chmod a-w` alone does not stop it from writing: the owner can
`chmod` the files back. So on this driver, read-only cannot rest on file
modes alone.

Related: #9048, the same driver/uid mismatch, seen in the `fullsend-code`
image; #7927, another `readonly_repo` gap.
