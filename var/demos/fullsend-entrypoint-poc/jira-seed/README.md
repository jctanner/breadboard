# M5: Jira-only reset and one eligible strategy RFE

Adapted from `var/demos/strat-pipeline-replication/scripts/seed_single_rfe.py`:
the summary and full problem/outcome/acceptance/user-story/technical description
are imported unchanged. This fixture adds a unique marker, derives release
and quality labels from the selected strat-creator checkout's
`config/pipeline-settings.yaml`, verifies its lock guards and discovery JQL,
and reads the issue using its actual `scripts/jira_utils.py` client.

## Run

Use Python with `httpx` and `PyYAML`, and `kubectl` configured for the local
Breadboard cluster. Supply these through existing credentials/environment:

- `JIRA_ADMIN_USER`, `JIRA_ADMIN_TOKEN`: local emulator admin identity and
  credential (not committed or printed).
- `JIRA_CA_FILE`: local CA PEM trusted by `https://jira.local`; the existing
  `gitlab-runner/gitlab-runner-ca` secret contains the runner's CA.
- `JIRA_SERVER` (optional): defaults to `https://jira.local`. This fixture
  refuses other URLs.

From the Breadboard root:

```bash
python3 var/demos/fullsend-entrypoint-poc/jira-seed/prepare.py --reset-jira
# Repeat verification/seed reuse without another reset:
python3 var/demos/fullsend-entrypoint-poc/jira-seed/prepare.py
```

`--checkout` can select the strategy checkout. Its default is
`checkouts.fullsend_prototype/jctanner.strat-creator`. Record the printed SHA;
M5 used `bd20534f5b904ae7808d167ad3cde671e17d5ab1`.

The reset is only POST `https://jira.local/api/admin/reset`, matching
`var/demos/dashboard-strat-arch-context-test/workflows/reset-jira.yaml`.
It drops/recreates Jira tables and reloads built-in seed data, including admin
and its default PAT. It removes custom users, PATs, issues, and links. The
fixture then verifies RHAIRFE Feature Request and RHAISTRAT Feature/Initiative,
ensures component `CLI`, and restores `aipcc-agentic-jira-bot` with a random
password and PAT. It saves their values through stdin to Kubernetes secret
`ai-pipeline/fullsend-strategy-jira`, never to a repository file or stdout.

## M6 input

The selected RFE is **RHAIRFE-1**, status **New**:

> Add rhai-cli diagnose subcommand for RHOAI deployment health checks

Labels at M5's recorded SHA:

- `fullsend-entrypoint-poc-m5` (unique fixture marker)
- `strat-creator-3.5` (first configured release label)
- `rfe-creator-autofix-rubric-pass` (configured quality label)
- `rfe-creator-feasibility-pass` (retained fixture context)

The labels are acceptance fixture inputs; the script does not run the upstream
RFE rubric/feasibility agents. The issue has priority Major, component CLI,
Feature Request type, no strategy links, and no lock, attention, human-sign-off,
or completed-strategy markers. It matches the branch's discovery JQL. The
repeat reuses its fixture marker and rejects duplicates or processed work.

Set M6's **explicit `RFE_KEY=RHAIRFE-1`**, rather than processing an open batch.
Provision CI variables from the secret in memory; do not print its contents:

| Secret key | CI use |
| --- | --- |
| `JIRA_SERVER` | `https://jira.local` |
| `JIRA_USER` | `aipcc-agentic-jira-bot` |
| `JIRA_TOKEN` | Generated bot **password** for the strategy's Basic HTTP client |
| `JIRA_BEARER_TOKEN` | Bot PAT, exclusively for a Bearer Authorization header |

Do not substitute the PAT for the Basic password. M6 owns GitLab CI variable
provisioning. The secret remains in `ai-pipeline` for that handoff; a runner in
another namespace needs its own credential injection. GitLab and the other
services were not reset, and no strategy/model execution was started.

The emulator remains in permissive Basic auth mode: Basic `/myself` proves
identity propagation, not password validation. A real valid Bearer PAT resolves
to the bot; an invalid Bearer falls back to admin, so the positive/negative
identity check proves the restored PAT is recognized. The strategy Python
read verifies CA and hostname using the runner CA. M6 must still recheck the
new bot identity and HTTPS from its actual sandbox before running skills.

The emulator currently ignores ID-only component references in issue fields.
This fixture uses `name: CLI`, matching the original seed, and verifies the
result. The separate emulator bug is recorded in the ledger.

## M8 fresh batch fixtures

`JIRA_CA_FILE=... python3 var/demos/fullsend-entrypoint-poc/jira-seed/batch.py`
uses existing bot credentials from Kubernetes to seed two distinct diagnose
extensions (JSON support report export; bounded per-check deadlines). It adapts
the existing replication fixture, adds M8 markers and configured eligibility
labels, and never resets Jira or alters the M6 issues. It verifies native
discovery/filtering and prints a size-two exact candidate bound. A repeat after
processing refuses linked/attached fixtures; inspect results before recovery.
