# Claude Bun binary analysis tools

These tools recover evidence-scoped plugin and workflow control flow from a
Bun standalone executable. [Reverse-engineering insights](docs/README.md)
contains the maintained reports, pseudocode, and compact evidence records.
Generated binaries, payloads, formatted segments,
and traces belong only under the ignored `tmp/claude-code-binary-analysis/`
tree. Do not commit them.

## Reproduce the 2.1.214 baseline

Run from the repository root with explicit inputs:

```bash
root=tmp/claude-code-binary-analysis/2.1.214
binary=/home/jtanner/.local/share/claude/versions/2.1.214

scripts/claude_binary_analysis/inspect_binary.sh \
  "$binary" "$root" deleteme/claude-code
scripts/claude_binary_analysis/extract_bun_section.sh "$root"
scripts/claude_binary_analysis/index_payload.py \
  "$root/payload/bun-section.bin" "$root/payload"
scripts/claude_binary_analysis/build_source_anchors.py \
  deleteme/claude-code "$root/anchors/source-anchors.json"
scripts/claude_binary_analysis/match_anchors.py \
  "$root/payload/bun-section.bin" \
  "$root/anchors/source-anchors.json" \
  "$root/payload/representations.json" \
  "$root/anchors/bundle-hits.json" \
  "$root/anchors/correspondences.json" \
  --binary-manifest "$root/manifest/binary.json"
```

`inspect_binary.sh` makes the version workspace immutable by recorded binary
hash. `extract_bun_section.sh` verifies the ELF section size and refuses a
different existing payload. `carve_segment.py` records exact source offsets
and hashes in a JSON sidecar. Format only deliberately carved small segments:

```bash
scripts/claude_binary_analysis/carve_segment.py \
  "$root/payload/bun-section.bin" "$root/segments/raw/topic.js" \
  --start OFFSET --end OFFSET --topic topic
scripts/claude_binary_analysis/format_segment.sh \
  "$root/segments/raw/topic.js" "$root/segments/formatted/topic.js" \
  tmp/claude-code-binary-analysis/tooling/node_modules/.bin/prettier
```

The formatter must report exactly Prettier 3.6.2. `compare_segments.py`
normalizes identifiers, strings, and numbers for a coarse structural diff; it
does not establish semantic equivalence by itself.

## Runtime controls

The [S1 hardening follow-up](docs/claude-code-2.1.296-workflow-hardening-controls.md)
records actual configured-agent delivery, reviewer scope hooks, asynchronous
assignment transcript timing, target-bound refinement schemas and
StructuredOutput checkpoint hooks and delivered-report composition.
Final completion controls check saved validation receipts and distinguish native
failure from a reporting error after completed work. `run_outcome_control.py`
uses a loopback stub, with optional `--business-fault` or `--reporting-fault`;
it makes zero provider calls.
`run_reviewer_scope_control.py`, `run_refine_receipt_control.py` and
`run_review_composition_control.py` test candidate repository code against the
native binary with a loopback API and zero provider calls.

The [subagent skill isolation investigation](docs/claude-code-2.1.296-subagent-skill-isolation-analysis.md)
uses `run_subagent_skill_experiments.py BINARY OUTPUT --case CASE` to isolate
nested-checkout discovery from a child's returned answer. Cases include
Explore/general-purpose/Workflow Read, no read, Bash-only, gitignored checkout,
disabled project settings, direct child skill reads/invocations, and explicit
primary invocation. `verify_subagent_skill_controls.py TRACES OUTPUT.json`
checks the ten retained `subagent-skill-*-v1` cases and fixture hashes.

The experiment runner creates a fresh `CLAUDE_CONFIG_DIR`, local fixture
marketplaces, deterministic fixed-date Git commits covering every marketplace
and plugin fixture, and a loopback-only Anthropic response server. It inherits
no credential, retains only fixture/command-bearing request strings, and
requires Claude Code to parse each mock SSE response to a successful result:

```bash
scripts/claude_binary_analysis/run_plugin_experiments.py \
  --strace "$binary" "$root/traces/local-manifest-state-strace-v1"
```

The output directory is immutable. Use a new name for every rerun. Binding the
loopback server and using `strace` may require local sandbox approval.
`experiment.json` and `collision-matrix.json` record fixture commit/tree IDs;
`results.json` summarizes every command and selected marker. Each command
directory retains argv, debug/stdout/stderr output, raw strace, and extracted
`execve` records.

## Tests and commit checks

`check_specialist_delivery.py MANIFEST --api-dir JOB/api-dumps` checks expected
strategy/role/tool IDs against actual receiving tool results. The manifest declares
hashed reference reports or authored fragments; acknowledgements, partial reports,
errors and identity mismatches fail. Alternatively use `--channels FILE.json`
with an `observations` array for controlled fixtures. Exit 0 means every declared
report was delivered, 1 means contract failure, and 2 means invalid input.
See [the evidence and limits](docs/claude-code-2.1.296-benchmark-hardening.md).

```bash
BUN_BIN=/path/to/pinned/bun \
  python3 -m unittest discover -s scripts/claude_binary_analysis/tests -v
python3 scripts/claude_binary_analysis/validate_claims.py \
  scripts/claude_binary_analysis/docs/claude-code-2.1.214-plugin-claims.json --check-paths
python3 scripts/claude_binary_analysis/check_commit_safety.py
```

The Bun fixture test was verified with public Bun 1.3.14. The analyzed target
identifies itself as Bun 1.4.0, which was not a public Bun release when this
baseline was produced. The safety check rejects staged raw analysis paths,
NUL-containing files, analysis deliverables over 1 MiB, and common token
shapes.

## A later Claude version

The workflow investigation for 2.1.296 is recorded in
[the workflow report](docs/claude-code-2.1.296-workflow-analysis.md), with a claim ledger,
parsed symbol catalog, and 16 verified runtime controls beside it.

This release uses multiple ES modules. The old `index_payload.py` heuristic's
`primary_application` is only an anchor-rich module; its CommonJS wording
must not be read as proof of a single application bundle. Follow explicit
import/export bindings into other modules, including modules shorter than
the long-run threshold. Carve each module with `carve_segment.py`, then parse
it without execution to obtain function byte ranges and hashes:

```bash
node scripts/claude_binary_analysis/index_js_module.mjs \
  "$root/segments/raw/module-OFFSET.js" \
  "$root/anchors/module-OFFSET-symbols.json" \
  tmp/claude-code-binary-analysis/tooling/node_modules/prettier/plugins/babel.mjs
```

`run_workflow_experiments.py BINARY OUTPUT --input INPUT.json` runs an
unmodified release against a deterministic loopback API. The input file
contains a Workflow tool call's JSON arguments; omitting it probes tool
availability. Every output directory must be new. Optional controls include
`--settings`, `--named-fixtures valid|invalid-project`, `--text-only-agents`,
and `--resume-controls`. The latter expects two sequential agent prompts
ending in `WORKFLOW_FIXTURE_AGENT first` and `WORKFLOW_FIXTURE_AGENT second`,
with `label:"first"`, to replay, relabel, then change the second prompt.
Recorded `command.json` and mock responses preserve fixture inputs.

The sixteen baseline cases can be checked with:

```bash
python3 scripts/claude_binary_analysis/verify_workflow_controls.py \
  tmp/claude-code-binary-analysis/2.1.296/traces /tmp/workflow-controls.json
PRETTIER_BABEL_PLUGIN="$PWD/tmp/claude-code-binary-analysis/tooling/node_modules/prettier/plugins/babel.mjs" \
  python3 -m unittest discover -s scripts/claude_binary_analysis/tests -v
```

The verifier reads persisted workflow states and actual API captures: a zero
CLI exit status alone does not establish that a background workflow succeeded.

`run_workflow_operations_experiments.py BINARY OUTPUT --case CASE` probes the
operational boundaries with the same mock-only approach: crash boundaries,
journal truncation, competing resumptions, task stop, SIGTERM, the print
background-wait ceiling, concurrency overrides (including nested workflows),
budget gates, injected 429/500/broken-stream faults and stall recovery.
`run_workflow_network_fault_experiments.py BINARY OUTPUT --case CASE
[--max-retries N]` adds the network-fault taxonomy: persistent rate limits,
connection resets with no HTTP response, spend-limit 429s and 529 overload,
with per-request timing so retry backoff is measurable.
`run_workflow_fanout_experiments.py BINARY OUTPUT` runs a result-driven
fan-out control: one agent's structured list feeds a for-loop of per-item
agent calls with result-derived prompts, verifying dynamic chaining. Its
crash cases capture only the crash boundary; `run_workflow_crash_resume_experiments.py
BINARY OUTPUT --case crash-during-agent|crash-before-result|crash-after-result`
re-runs them with a fresh-process resume derived from the surviving journal.
Every output directory must be new; supervisor signals are bounded and sent
only to fixture-owned processes.

```bash
python3 scripts/claude_binary_analysis/verify_workflow_operations_controls.py \
  tmp/claude-code-binary-analysis/2.1.296/traces /tmp/workflow-operations-controls.json
```

The verifier checks journals, workflow states, fixture side-effect counters,
late writes, injected faults and terminal results across the operations cases
and the crash-resume completions.

`run_auto_mode_experiments.py BINARY OUTPUT --case allow|block|default-mode-control`
probes the auto-mode permission classifier with the same mock-only approach.
The main conversation requests a Bash call writing outside the working
directory (so it is not skipped by the acceptEdits rule); classifier requests
are detected by their stop sequences and prompt markers and answered with a
configured `<severity>` verdict. Captures retain full request bodies,
including the classifier's system prompt and transcript packaging.

```bash
python3 scripts/claude_binary_analysis/verify_auto_mode_controls.py \
  tmp/claude-code-binary-analysis/2.1.296/traces /tmp/auto-mode-controls.json
```

The verifier checks request roles and stages, classifier model and budgets,
the system-prompt inventory (rule counts, severity boundary), fixture effects,
denial messages and the debug-log skip/default-on evidence.

`run_subagent_skill_experiments.py BINARY OUTPUT --case CASE` uses the same
mock-only approach for skill discovery and other subagent information channels.
Successful new runs retain a copy of the exact runner. Cases include
`memory-read`, `memory-propagate`, `file-edit`, `file-edit-unread`,
`file-edit-parent-write` and `bash-output`, alongside the earlier skill cases.
The memory-propagate case sets coordinator environment variables as a control;
the shipped typed flag object does not enable instruction propagation.

```bash
python3 scripts/claude_binary_analysis/verify_subagent_skill_controls.py \
  tmp/claude-code-binary-analysis/2.1.296/traces /tmp/skill-controls.json
python3 scripts/claude_binary_analysis/verify_subagent_information_controls.py \
  tmp/claude-code-binary-analysis/2.1.296/traces /tmp/information-controls.json
```

The verifiers select retained run revisions and check actual child tools,
primary request markers and side effects. They separate the primary's model
messages from child events exposed by the SDK stream.

`run_skill_variable_experiments.py BINARY OUTPUT --case CASE` invokes authored
local/plugin skills against a local API stub. Its cases cover arguments,
directories, session/effort, options and harmless bundled-script preprocessing.
Retained runs snapshot the runner and record fixture/config provenance. Verify
the selected nine controls with:

```bash
python3 scripts/claude_binary_analysis/verify_skill_variable_controls.py \
  tmp/claude-code-binary-analysis/2.1.296/traces /tmp/skill-variable-controls.json
```

Choose a new version directory, run the same inspection/index/anchor commands,
compare `representations.json` and anchor multiplicity, and re-carve only
changed neighborhoods. Carry a claim forward only when its exact bundle
fingerprint and runtime preconditions still match. Never reuse or overwrite a
workspace whose manifest has a different binary hash.
