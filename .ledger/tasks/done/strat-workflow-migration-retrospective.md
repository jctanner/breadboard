# Draft the strategy Workflow migration retrospective

Owner requested a document explaining the migration from Bash-orchestrated
Claude batches to dynamic workflows, including implementation effort,
JavaScript maintenance, resilience, and observed agent self-modification.

- [x] Review migration plans, decisions, hardening records, bugs, validation,
  usage accounting, runtime investigations, and active PR93 follow-up.
- [x] Verify the official dynamic workflows terminology and distinguish fixed
  JavaScript scheduling from an agent editing source and relaunching.
- [x] Measure merged PR85 scope from Git, with tests/docs/bundled copies included
  explicitly rather than claiming a pure resilience-code count.
- [x] Write a linked retrospective in the ledger and verify local references
  and whitespace.

Draft: [Migrating Bash orchestration to Claude dynamic workflows](../../notes/strat-workflow-migration-lessons.md).

The draft covers handoff delivery, scope, state, composition, completion,
recovery, freshness, hook performance, source protection, Fullsend integration,
real GitLab qualification, rollout, and dated token accounting. PR93 review
repairs remain active; the retrospective does not claim they are qualified.
AISDLC-52 is the project tracking ticket, verified through Jira during the
preceding conversation. The owner's human-edit attribution is distinguished
from the narrower evidence supplied by the archived Jira changelog.

No component source, runtime settings, Jira records, or external documents
were changed. No model job or paid validation was launched.

## Editorial revision after owner review

Moved the conclusion to the opening and the observed three-execution incident
to the first substantive section. Grouped effort/status/version limits for
decision makers and implementation/validation guidance for engineers. Moved
Jira actor-attribution qualification into a footnote so the main text focuses
on valid freshness refusal and excessive batch impact.

Added an explicit version boundary: cited runtime investigations cover 2.1.296,
with no recorded revalidation on 2.1.311 or later. Dojo's 2.1.311 one-agent smoke
does not qualify those fault behaviors. Linked the documented JavaScript
learning work. Documentation checks only; no runtime revalidation was launched.

## External review clarification

Reframed B1 around control of the already running Bash outer loop: edits do not
hot-reload its parsed loop, while the observed primary Claude session could
edit and relaunch a Workflow within one job. Neither source immutability nor
hot-patching an existing Workflow VM is inferred. B2 now cites the handoff
diagnosis directly and separates its 2/12 result from the self-edit incident.
M1 distinguishes three successful single-RFE runs per design from one completed
three-RFE batch per design and removes the ambiguous matched-cost claim.
Updated a PR93 task link after that task moved to done. Documentation only.
