# ADR-0012: Explore strategy orchestration through native Fullsend agents

## Status

Accepted POC direction, 2026-10-07. A1 prepares the checkout, A2 implements
the prompts, and A3 resolves runtime integration while wiring the new CI branch.
Reuse the known working Fullsend setup; no standalone compatibility gate.

## Decision

Use a separate strat-creator checkout/branch under
`checkouts.fullsend_agent_led_poc/`. Define strat-single and strat-batch prompt
agents using native Fullsend `agent:` harnesses. Follow rfe-creator/rfe-autofixer's
released binary, job-owned gateway, pre/post and validation pattern. No custom
Fullsend patch. Prompts control progression through existing skills/helpers;
preserve Opus 4.6, Vertex, one runner, owned locks and truthful review outcomes.

Publish the new `.gitlab-ci.yml` on `feat/fullsend-agent-led-poc` in the existing
`gitlab.local/redhat/rhel-ai/agentic-ci/strat-pipeline` project. It consumes the
public fork's `feat/fullsend-agent-led-strategy` branch at a tested commit.
Preserve the existing GitLab branches and shared project variables.

## Consequences

This experiment tests native agent orchestration alongside the completed
script-led POC, with independent checkout, branch, results and evidence.
Deterministic API helpers, validation, publication and outer cleanup remain
necessary. Prompt compliance alone cannot prove phase completion or cleanup.
Strategy creation/refinement requires Jira write permissions that differ from
the reference RFE read-only/dry-submit sandbox contract. Prove resume before
enabling automatic validation retries on write-bearing work.

## Amendment, 2026-10-07: host-side locking and discovery

The host pre-script (CI job container), not the agent, discovers candidates
(`list-rfe-ids.py --jql-default` for batch, `RFE_KEY` for single), takes the
Jira processing locks with `lock_issues.py`, and records the owned keys in
`$FULLSEND_RUN_DIR` before the sandbox exists. The agent receives the
acquired keys as input and never calls `lock` or receives JQL. The outer CI
releases from that record after `fullsend run`.

Why: `lock_issues.py lock --locked-keys-file` truncates the record on each
call, so a repeated agent call strands a held lock with an empty record
(reproduced against the emulator). strat-pipeline avoids this by locking once
from CI before Claude; the reference rfe-autofixer/rfe-creator harness keeps
the agent off coordinated Jira writes entirely. A host-written record also
survives sandbox loss; only loss of the job pod needs Jira reconciliation.
Unlike rfe-autofixer and epic-decomposer, which pass JQL to the skill and
serialize with `resource_group`, discovery stays bounded and deterministic;
the cost is no in-agent wave processing and whole-run locks, as today.

## Amendment, 2026-10-07: one in-run validation retry

After pipeline 2083's mid-batch `end_turn`, the user chose rfe-creator's
pattern: `max_iterations: 2`, where the retry resumes from durable
repository progress (`tmp/strat-progress.yaml`) rather than repeating
completed phases. This replaces "start with one agent attempt". The
remaining risk is a partly finished phase. A per-strategy step can repeat
when the agent stopped after its Jira effect but before its marker; the
skills' verdict-label gates bound this for review.

See [the plan](../plans/fullsend-agent-led-strategy-poc.md).
