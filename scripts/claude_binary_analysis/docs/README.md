# Claude Code reverse-engineering insights

This directory holds maintained findings, reconstructed pseudocode, and
compact provenance/evidence records from Claude Code binary analysis.
Each investigation is pinned to an exact binary version and hash; findings
must be revalidated before being applied to a different release.

## Investigations

| Target | Findings | Reconstructed control flow |
| --- | --- | --- |
| 2.1.296 production gaps, priorities 1–2 | [Nested specialist return diagnosis](claude-code-2.1.296-workflow-specialist-handoff.md), twenty-one controls and a configured-agent workaround; [real-run provenance](claude-code-2.1.296-workflow-review-provenance.md), thirty-two archived calls | Exact return-path pseudocode in the handoff report |
| 2.1.296 skill variables | [All prompt placeholders, resolution sources and expansion stages](claude-code-2.1.296-skill-variable-expansion.md), with nine controls and frontmatter/hook distinctions | Ordered pipeline pseudocode in the report |
| 2.1.296 other subagent channels | [Files, reporting, traces, shared state and dormant nested-instruction propagation](claude-code-2.1.296-subagent-information-sharing.md), with six additional controls | Exact symbols and channel explanations in the report |
| 2.1.296 subagent isolation | [Child skill discovery reaches the primary context](claude-code-2.1.296-subagent-skill-isolation-analysis.md), with code proof, metadata/body distinction, and ten controls | [Skill discovery pseudocode](claude-code-2.1.296-subagent-skill-isolation-pseudocode.md) |
| 2.1.296 workflows | [Workflow system](claude-code-2.1.296-workflow-analysis.md), including JavaScript capabilities, execution limits, scheduling, returns, failures, and resume | [Workflow pseudocode](claude-code-2.1.296-workflow-pseudocode.md) |
| 2.1.296 workflow operations | [Recovery, cancellation, deadlines, budgets, concurrency, retries and replay](claude-code-2.1.296-workflow-operations.md), with crash-resume controls | Outcomes inline; see the report's evidence section |
| 2.1.214 plugins | [Plugin and skill pipeline](claude-code-2.1.214-plugin-analysis.md), including settings order, discovery, component ownership, and name collisions | [Plugin pseudocode](claude-code-2.1.214-plugin-pseudocode.md) |

[Plugin skill discovery guide](claude-code-plugin-skill-discovery.md) provides
layout and invocation examples backed by the 2.1.214 investigation.

## Evidence records

For **2.1.296 production handoff and provenance**:

- [Exact return-path symbols](claude-code-2.1.296-workflow-handoff-symbols.json)
- [Runtime and archive claims](claude-code-2.1.296-workflow-handoff-claims.json)
- [Twenty-one verified handoff controls](claude-code-2.1.296-workflow-handoff-controls.json)
- [S1 Opus provenance](claude-code-2.1.296-workflow-s1-opus-provenance.json)
- [S2 Opus provenance](claude-code-2.1.296-workflow-s2-opus-provenance.json)
- [S1 GLM provenance](claude-code-2.1.296-workflow-s1-glm-provenance.json)
- [S2 GLM provenance](claude-code-2.1.296-workflow-s2-glm-provenance.json)

For **2.1.296 skill variable expansion**:

- [Exact symbols](claude-code-2.1.296-skill-variable-symbols.json)
- [Evidence-labeled claims](claude-code-2.1.296-skill-variable-claims.json)
- [Nine verified runtime controls](claude-code-2.1.296-skill-variable-controls.json)

For **2.1.296 other subagent information channels**:

- [Exact symbols](claude-code-2.1.296-subagent-information-symbols.json)
- [Evidence-labeled claims](claude-code-2.1.296-subagent-information-claims.json)
- [Six verified runtime controls](claude-code-2.1.296-subagent-information-controls.json)

For **2.1.296 subagent skill isolation**:

- [Exact symbols and source correspondence](claude-code-2.1.296-subagent-skill-isolation-correspondences.json)
- [Evidence-labeled claims](claude-code-2.1.296-subagent-skill-isolation-claims.json)
- [Ten verified runtime controls](claude-code-2.1.296-subagent-skill-isolation-controls.json)

For **2.1.296 workflows**:

- [Binary manifest](claude-code-2.1.296-workflow-binary-manifest.json)
- [Parsed symbol correspondences](claude-code-2.1.296-workflow-correspondences.json)
- [Evidence-labeled claims](claude-code-2.1.296-workflow-claims.json)
- [Sixteen verified runtime controls](claude-code-2.1.296-workflow-controls.json)
- [Additional JavaScript capability probe](claude-code-2.1.296-workflow-language-probe.json)

For **2.1.296 workflow operations** (recovery, cancellation, limits, retries,
replay):

- [Twenty-three verified operations controls](claude-code-2.1.296-workflow-operations-controls.json),
  including the three crash-resume completions

For **2.1.214 plugins**:

- [Binary manifest](claude-code-2.1.214-binary-manifest.json)
- [Source anchor catalog](claude-code-2.1.214-plugin-anchor-catalog.json)
- [Bundle correspondences](claude-code-2.1.214-plugin-correspondences.json)
- [Evidence-labeled claims](claude-code-2.1.214-plugin-claims.json)

## Method and storage

Use [the tooling README](../README.md) for extraction, indexing, isolated
experiments, claim validation, and reproduction commands. Evidence precedence
is controlled runtime behavior, exact target-binary control flow, then older
source correspondence. Reports distinguish runtime-confirmed behavior from
static findings and explicitly untested branches.

Raw binaries, extracted sections, recovered source segments, fixtures and
runtime logs stay under the ignored repository-root
`tmp/claude-code-binary-analysis/<version>/` tree. Keep project plans, task
records and session history in [the ledger](../../../.ledger/PLAN.md).
