# M5: Reset local Jira and seed one strategy RFE

## Goal

After [M4](../done/strat-creator-entrypoint-poc.md),
[M4.1](../done/strat-creator-rfe-autofixer-images.md), and
[M4.2 sandbox Jira access](../done/fullsend-sandbox-jira-connectivity.md), prepare a repeatable local input
for the Fullsend strategy pipeline. Reset the Jira emulator only and seed one
RFE selected from the existing `var/` fixtures.

## Acceptance criteria

- [x] Require M4.2's successful sandbox Jira check before resetting Jira.
- [x] Inspect the fixture and current emulator reset behavior before running it.
  Use the Jira-only reset pattern in
  `var/demos/dashboard-strat-arch-context-test/workflows/reset-jira.yaml`;
  do not invoke a stack-wide reset.
- [x] Reset `jira.local`, then verify required projects, issue types, and
  service credentials. Recreate the CI bot/token if reset removed them.
- [x] Adapt `var/demos/strat-pipeline-replication/scripts/seed_single_rfe.py`
  or the captured RFE under `var/demos/dashboard-strat-arch-context-test/files/`.
  Match the feature branch's eligibility labels/gates rather than blindly
  reusing a historical strategy version label.
- [x] Confirm the seeded RFE is readable and eligible for `single-rfe`, with
  no stale lock or completed-strategy markers. Target its explicit issue key
  so unrelated built-in seed issues are not processed.
- [x] Record the issue key, fixture source, required labels, and repeatable
  reset/seed commands without credentials. Provide these inputs to M6.

## Status

Done, 2026-10-06. Jira-only reset, bot credential restoration, seed and repeat verification passed.

## Outcome and evidence

Seeded [RHAIRFE-1](https://jira.local/browse/RHAIRFE-1):
**Add rhai-cli diagnose subcommand for RHOAI deployment health checks**.
The final corrected reset-and-seed command completed with `reset_performed:
true`, `created: true`, `eligible: true`. Its non-resetting repeat returned
`created: false`, the same key, and an RHAIRFE count of one. No model or
strategy execution was started.

| Check | Result |
| --- | --- |
| Jira reset | Only POST `https://jira.local/api/admin/reset`; tables recreated and built-in seed reloaded |
| Required projects/types | RHAIRFE Feature Request; RHAISTRAT Feature and Initiative verified |
| Source content | Imported unchanged from `var/demos/strat-pipeline-replication/scripts/seed_single_rfe.py` |
| Strategy source | `feat/fullsend-strategy-entrypoint` at `bd20534f5b904ae7808d167ad3cde671e17d5ab1` |
| Release label | `strat-creator-3.5`, selected from actual `jql.required_labels` |
| Quality label | `rfe-creator-autofix-rubric-pass`, selected from actual `jql.quality_labels` |
| Other labels | `fullsend-entrypoint-poc-m5`, `rfe-creator-feasibility-pass` |
| Fields | Feature Request; New; priority Major; component CLI; full original description |
| Eligibility | Actual `build_jql_from_config` discovery query selects the key; no excluded status or blocking/skip labels |
| Stale work | No processing/attention/human-sign-off markers, strategy links, or attachments |
| Readability | Strategy `jira_utils.get_issue` succeeds using the bot and verified certificate/hostname trust |
| Idempotence | Reuses one marker-matched issue; rejects duplicates or processing markers |

The quality/feasibility labels are fixture inputs, not claims that upstream
RFE agents ran during M5. M6 must target `RFE_KEY=RHAIRFE-1` explicitly.

## Credentials and reset behavior

The reset removes custom users, PATs, issues, and links and recreates admin
with its default credential data. The fixture restored dedicated identity
`aipcc-agentic-jira-bot` with a random password and PAT. Values live only in
Kubernetes secret `ai-pipeline/fullsend-strategy-jira`; no raw values were
printed or written to source. Secret keys:

- `JIRA_SERVER`: `https://jira.local`.
- `JIRA_USER`: bot identity.
- `JIRA_TOKEN`: generated **password**, for the strategy client's Basic auth.
- `JIRA_BEARER_TOKEN`: real bot PAT, for a Bearer Authorization header.

A valid Bearer PAT resolves to the bot; an invalid Bearer resolves to fallback
admin, proving the restored PAT is recognized. Basic `/myself` resolves to
the intended bot and the Python issue read succeeds. The emulator still uses
permissive Basic auth, so Basic password validation is unavailable. The
credential secret is retained for M6; M6 provisions GitLab variables from it
in memory and rechecks the bot from its actual sandbox. Do not put the PAT
in the Basic-password variable. GitLab, the maintained runner, and other
services were not reset or changed.

## Reproduction and checks

See `var/demos/fullsend-entrypoint-poc/jira-seed/README.md`. Set
`JIRA_ADMIN_USER`, `JIRA_ADMIN_TOKEN`, and `JIRA_CA_FILE` through the existing
local environment/secret management, then:

```bash
python3 var/demos/fullsend-entrypoint-poc/jira-seed/prepare.py --reset-jira
python3 var/demos/fullsend-entrypoint-poc/jira-seed/prepare.py
```

The fixture uses trusted HTTPS, checks local-only URL scope, reads the current
branch config/guards, preserves source RFE content, and reports sanitized
metadata. Live reset/seed, read/eligibility checks, and repeat passed. Python
parse, CLI help, whitespace checks, and `git diff --check` passed. No component
checkout was changed, so its feature SHA remains unchanged.

The initial preflight needed an explicit JQL and positive page size. The first
seed then exposed the emulator's silent ID-only component omission. The final
fixture uses component `name: CLI` (as the source fixture does), verifies the
returned field, and passed a fresh complete reset/seed run. That emulator
[bug](../../bugs/open/jira-emulator-component-id-ref-ignored.md) is documented
and remains open; its workaround does not block M6.

## Independent review — 2026-10-06

Reviewed the reset/seed implementation and handoff, then used read-only live
requests with the retained bot credentials and runner CA. Confirmed one
RHAIRFE issue, RHAIRFE-1, matching the branch's actual discovery JQL; required
projects/types, New status, Major priority, CLI component, expected labels,
and no blocking labels, links, or attachments. Basic and valid Bearer identify
the bot; invalid Bearer does not. The actual strategy Python client can read
the issue with verified TLS. Independently compared the complete returned ADF
description with the source fixture's converted content: exact match.

M5 is accepted for M6. One nonblocking
[description-verification gap](../../bugs/open/m5-seed-adf-content-check.md)
remains in the reusable script: its equality check skips ADF responses.
CLI help and Python parsing passed. This review did not rerun the reset/seed
command or mutate Jira; reset execution and repeat-run behavior are supported
by the implementation and the original completion evidence. Post-reset bot
access from the actual sandbox remains M6's check.
