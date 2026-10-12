# Claude Code 2.1.296: other subagent-to-primary information channels

Investigated 2026-10-11 using the unmodified Linux x64 binary in the
[binary manifest](claude-code-2.1.296-workflow-binary-manifest.json).
This extends the [skill discovery investigation](claude-code-2.1.296-subagent-skill-isolation-analysis.md).

## Findings

Subagents have separate conversations, but also share mutable session state,
workspace files and reporting infrastructure. Several channels carry information
beyond the child's final answer. Distinguish information entering the primary's
**model request** from information visible to the **harness, UI or SDK**.

| Information | Route to the primary or host | Evidence |
| --- | --- | --- |
| Skill names, descriptions and applicability | Child discovery updates shared command availability; the primary receives a skill listing | Ten earlier runtime controls |
| Child-written file text | The primary's changed-file scanner can inject a diff of a tracked file previously written by the primary | New positive runtime control; ordinary Read and unread-file controls are negative |
| Final report, failures and execution metadata | Agent results/notifications carry report text, status, token/tool counts and elapsed time; additional harness notes can accompany the report | Exact code and mock execution events |
| Child conversation and tool inputs/results | A normal background launch supplies a path to the child's full JSONL transcript; verbose stream-json also exposes child messages | Runtime launch receipts and SDK stream |
| Permission decisions | Session permission updates use a shared setter; synchronous agents also share general AppState mutation | Exact code; permission changes not exercised |
| Browser/artifact and file-history state | Shared callbacks/registries; background AppState mutations have a small propagation whitelist | Exact code; automatic context effects not exercised |
| Nested CLAUDE.md / CLAUDE.local.md instructions | An explicit propagation branch exists, but its flag comes from an empty exported object in this build | Exact code and negative controls with both coordinator environment variables set |

Full child tool output is **not automatically copied into the primary's model
conversation** merely because the host streams or stores it. In the Bash
control, the child's output marker appears in its tool result and the SDK child
messages, while remaining absent from all primary model requests. This is a
different boundary from preventing the parent process from observing it.

## File changes: a demonstrated channel with an important restriction

`BDr` runs `ear` when assembling changed-file attachments. `ear` looks at the
current agent's read-state cache, checks disk timestamps and permissions, reads
eligible changed files and computes a diff. The `edited_text_file` serializer
puts that diff into a meta user message for the model. It does not check which
agent made the disk change. The text-snippet budget across a pass is 16,384
characters; after that it can send only a change notice requiring another Read.

The target's scanner skips entries whose **offset or limit is defined**.
Ordinary Read stores an offset (including the default first line), so even an
apparently complete Read does not automatically qualify. Write/Edit state can
qualify because those fields are undefined. This restriction matters when
describing the channel: “the primary previously read the file” is insufficient.

Three runtime controls use a child that reads and writes README.md, then returns
only `CHILD_FIXED_ANSWER_WITHOUT_SKILL_DETAILS`:

- Primary first reads and writes README.md: the child's new text appears in the
  primary's model messages, without a primary reread of README.md.
- Primary only reads README.md: the child's text stays absent, including after
  a subsequent primary Read of an unrelated file.
- Primary has not accessed README.md: the child's text stays absent in the
  captured requests. This control ends after the completion notification.

In all three, the file on disk does change. Shared filesystem state is therefore
broader than automatic diff delivery. Worktree isolation changes which files
are shared; these controls use the default shared checkout.

## Reports, traces and host-visible progress

`VJn` constructs a child result from assistant text, with harness additions for
conditions such as partial results, turn limits, review notices and persisted
tool-result references. `Nl` reserves room for file references when truncating
a large report. `nvt` delivers the result together with task status and usage;
it can also report worktree metadata. These are explicit return/reporting paths,
not silent copying of every tool result.

Normal background launch receipts in these controls identify an `output_file`
and describe it as the full subagent JSONL transcript. The receipt tells the
primary not to Read or tail it because of context size. That instruction is not
a separate filesystem access boundary. The controls record the supplied paths,
but do not direct the primary to read transcripts. Coordinator mode's launch
receipt omits this path in the paired control.

The verbose stream-json output separately contains child assistant/user
messages, tool-call inputs, tool results, task progress and completion usage.
`SA` and `ZOe` implement progress forwarding, with additional options controlling
nested progress. In the Bash control, the host receives the output marker while
the primary model does not. A caller that feeds such events back into a primary
prompt can create an additional application-level channel; this investigation
does not assume that any particular caller does so.

## Shared state: effects that need their own prompt-delivery proof

`SA` calls the context factory `air` with `shareSetAppState: !isAsync`.
Synchronous children can use the parent's AppState setter. Background children
receive a wrapper that only propagates changes to `frameUrls`,
`workshopVerifiedSlugs`, `sidecarHistorySlugs` and `prReviewSlugs`. The wrapper
does not propagate arbitrary child AppState changes.

Other references are shared explicitly: the session, message queue, task and
notification registries, tool state, session environment map, session permission
setter, browser callbacks, artifact registries/read observations, memory-update
queue and attribution callbacks. File-history writes propagate `touch`
operations unless fuller history sharing was requested. Some artifact setters
are disabled for particular agent contexts.

The permission code can apply accepted hook/approval permission updates through
the session setter and persist eligible rules. This is a route for approved
policy changes to outlive the child; it does not establish that a child can
grant itself arbitrary permissions. A shared environment map likewise does
not establish that a normal child shell `export` modifies the parent's shell.
Neither behavior was probed here.

These references establish shared state ownership. They do **not**, by
themselves, prove that every URL, artifact, memory entry, permission decision or
environment value is automatically inserted into the primary's model context.

## Nested instructions: the apparent flag is dormant in this build

`SA` collects paths from child `nested_memory` attachments. Its teardown contains
a `propagateNestedMemory` stage that would enqueue discovered CLAUDE.md and
CLAUDE.local.md paths in the parent's `pendingNestedMemoryTriggers`. It maps
worktree paths back to the main checkout, skips paths already present in the
parent's read-state cache and deduplicates queued paths. `Nyn` consumes that queue
only for the primary, then loads and serializes instruction contents.

However, the teardown gate reads
`Yn.CLAUDE_CODE_COORDINATOR_PROPAGATE_NESTED_MEMORY`. The typed-environment module
constructs `Yn = SPe(kx, null)` with **`kx = {}`**. `SPe` creates environment
getters only for keys present in that input. There is no getter for this flag;
setting the same-named process environment variable does not create one.

Two paired controls advance the primary through a Skill invocation after child
completion. In each, the child receives the nested instruction marker, but the
primary does not. Setting both `CLAUDE_CODE_COORDINATOR_MODE=1` and
`CLAUDE_CODE_COORDINATOR_PROPAGATE_NESTED_MEMORY=1` switches the agent type to
`worker`, yet does not enable instruction propagation. The branch is dormant
under these conditions in this shipped binary. Its presence is evidence of an
implemented design, not runtime proof of an available feature.

## Evidence and reproduction

- [Six verified controls](claude-code-2.1.296-subagent-information-controls.json)
- [Twenty-two exact symbol/property ranges and hashes](claude-code-2.1.296-subagent-information-symbols.json)
- [Evidence-labeled claims](claude-code-2.1.296-subagent-information-claims.json)
- [Probe runner](../run_subagent_skill_experiments.py) and
  [outcome verifier](../verify_subagent_information_controls.py)

The new cases are `memory-read`, `memory-propagate`, `file-edit`,
`file-edit-unread`, `file-edit-parent-write` and `bash-output`. Run the probe with
the pinned binary, a fresh ignored output directory and `--case CASE`. The
verifier selects the recorded successful revisions; earlier attempts remain
ignored evidence and are not treated as passing controls. Each retained run
has a runner snapshot/hash, initial fixture Git commit/tree hashes, scoped API
captures and actual tool results. Mutated fixtures are checked against their
original Git blobs and expected final contents.

No paid inference or real credentials were used. Mock usage values establish
which reporting fields cross the boundary, not real token consumption. These
findings apply to 2.1.296 local in-process agents; other builds, compaction,
remote agents and untested hooks may have different channels.
