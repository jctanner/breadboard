# Gap: Human review guide does not describe hardened runtime/plugin setup

The unchanged human review guide says install Claude Code and clone the
repository, then run its local slash commands. S1 review now requires the
loaded plugin's capture hooks and pins runtime 2.1.296; the guide does not
explain either requirement. A default current host CLI was 2.1.300.

The SME test also exposed a harness setup mistake: --plugin-dir pointing at
the editable human checkout makes all files below that registered plugin root
sensitive to the native Edit permission check, including local/ artifacts.
This is a loader/permission boundary, not evidence that SME input was ignored.
Do not weaken the native permission check or switch to an unqualified runtime.

Zero-upstream local API probes with actual Claude 2.1.296 establish:

- Inline plugin + artifact below that root: Edit denied, both direct and forked.
- Separate plugin directory + artifact in the working directory: Edit succeeds,
  both direct and forked.

The mock first reads then edits the fixture, and source/API data is explicitly
marked synthetic under the SME campaign's offline-permission-probe directory.
No provider tokens are used. The first probe omitted Read and failed that
precondition; retained results distinguish the corrected probes.

Document the qualified CLI and separate plugin installation/loading for local
human commands, with hooks enabled and project artifacts writable. The actual
SME continuation must use source-identical separate plugin/workspace copies.
Human interactive approval of protected plugin edits is not the intended setup
for ordinary strategy artifacts.

## Local documentation fix

The feature checkout's docs/human-review-guide.md now documents qualified
Claude 2.1.296, uv helper dependencies, a separate committed-source plugin
snapshot, the working checkout as cwd and explicit plugin loading in command
examples. The repo URL follows the fullsend-ai move. No executable source
changes. The actual tested workspace/plugin copies remain clean at 6ed858b.

The documented git archive snapshot recipe passes Claude 2.1.296 plugin
validation and its helper symlinks resolve. The validator warns that a plugin
root CLAUDE.md is not project context; the guide explicitly keeps the source
checkout as cwd, where that project's CLAUDE.md is loaded normally. Generic
marketplace-install advice does not affect the validation verdict.

Component git diff --check passes. At initial test completion this documentation
change was local and unpublished. The user subsequently authorized publication:
signed-off commit `1bcb8f4bab6d03619cd8da672c0b7a103e3bdb1f` now includes the
guide, pull repair and regression tests on `origin/feat/s1-workflow-hardening`.
Remote branch read-back matches and the checkout is clean. Required pre-push
`make test` passes 1,092 tests with six conditional skips; no paid model run.
