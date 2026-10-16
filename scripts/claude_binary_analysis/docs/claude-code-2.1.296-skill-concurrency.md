# Why four forked Skill calls ran sequentially

Claude Code 2.1.296 serializes Skill calls made by the same agent. Issuing several
calls in one model response does not make their execution overlap. Both exact
binary control flow and three credential-free native controls confirm this.
The same rule applies to plain `claude -p` slash-command execution, with
Workflows disabled.

## The dispatch rule

The generic tool constructor defaults `isConcurrencySafe` to false. The Skill
tool does not override it, including when a Skill uses `context: fork`.
The streaming dispatcher starts an unsafe call only when no other tool is
executing. Its nonstreaming counterpart also groups these calls separately and
runs them serially.

Original descriptive pseudocode:

```text
tool defaults: mayOverlap = false
Skill definition: keeps that default

when deciding whether to start a queued tool:
    if no tool is running: allow
    otherwise: allow only if this tool and all running tools may overlap
```

The outer Workflow agent cap and tool-use concurrency ceiling do not turn a
serial tool into a parallel tool. Forked context provides a separate
conversation; it does not itself promise concurrent execution.
The reason Anthropic selected this default is unverified.

## Native controls, no provider calls

A loopback server supplies every model response. Each of four forked Skills
uses an isolated Read-only agent and receives a one-second delayed response.
The Workflow agent cap is five in both cases.

| Arrangement | Maximum overlapping child requests | Result |
| --- | ---: | --- |
| Plain `claude -p "/concurrency-review"`, Workflows disabled, four Skills together | 1 | Four serialized calls, all return |
| One Workflow agent requests four Skill calls together | 1 | Four serialized calls, all return |
| Four Workflow agents each request one Skill | 4 | Four overlapping calls, all return |

All three Claude processes exit zero. The CLI control additionally verifies
that the authored slash-command prompt reached the receiver. The fixtures have fresh configuration
directories and an explicit environment containing only the loopback endpoint
and a dummy API credential. No personal credentials or real inference are used.
The separate-callers control establishes an available scheduling arrangement, not a
validated change to the strategy pipeline's completion/provenance contracts.

## Connection to the benchmark

The one-ticket Vertex smoke reports Claude Code 2.1.296. Its four reviewer calls
share one API response but their actual child transcripts run sequentially
over 8m49s. The longest child takes 2m50s. This matches the recovered dispatch
rule and the first control. The three-ticket run shows the same serial ordering
within each ticket, while different tickets' review agents overlap.

The archived scripted S2 Opus run, `markov-run-79d3241a`, also requests each
ticket's four reviewer Skills together. Their recorded child response ranges
are ordered feasibility, testability, scope and architecture for all three
tickets. Launch/first/last response hashes were checked against the retained
[S2 provenance](claude-code-2.1.296-workflow-s2-opus-provenance.json).
This concurrency restriction is shared by both designs and predates Workflow
integration. Independent Claude processes or separate Workflow callers can
provide scheduling above an individual agent's serial Skill queue; only the
separate-Workflow-callers arrangement was tested here.

The tested local binary SHA-256 is
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`.
The production executable hash was not independently captured; its version
and matching behavior are recorded. Do not extend the rule to untested releases.

[Exact byte ranges, hashes and verified control outcomes](claude-code-2.1.296-skill-concurrency-evidence.json).
[Benchmark timings](../../../.ledger/notes/s1-fullsend-vertex-opus-smoke-20261015.md).

Reproduce with a new output directory for each execution:

```bash
python3 scripts/claude_binary_analysis/run_skill_concurrency_control.py \
  /home/jtanner/.local/share/claude/versions/2.1.296 \
  tmp/claude-code-binary-analysis/2.1.296/traces/skill-concurrency-repeat \
  --layout same-receiver
```

Use `--layout separate-receivers` with another fresh output directory for the
comparison control. Raw fixtures, transcripts and recovered source stay ignored.
Add `--route cli --layout same-receiver` with a third fresh output directory
to reproduce the plain slash-command case. Its config sets enableWorkflows=false.
