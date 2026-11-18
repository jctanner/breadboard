# Initiatives scenario fixture (CC-75)

A resettable breadboard scenario for the Initiative flow (rfe-creator autofix
→ strat-creator `initiative-strategy` → epic-creator decomposition), seeded
with **fully synthetic** Initiatives. Plan:
[`.ledger/plans/cc75-w530-initiatives-scenario-plan.md`](../../../.ledger/plans/cc75-w530-initiatives-scenario-plan.md).

All data is fictional. Summaries start with `[SYNTH]`, and every issue carries
`cc75-synthetic` plus `cc75-fx-<id>`. Keys are in the `<PROJECT>-75001+` block.

## Environment

Run from this directory on the stack host:

```bash
export BREADBOARD_DOMAIN=w530.local            # the full ingress domain
kubectl get configmap internal-ca-cert -n ai-pipeline -o jsonpath='{.data.ca\.crt}' \
  > ~/.cache/cc75/w530-ca.crt
export BREADBOARD_CA_FILE=~/.cache/cc75/w530-ca.crt
```

Jira and GitLab use the emulators' development defaults (`admin:admin`).
`mirror_github.py` needs the GitHub emulator's development admin token in
`GITHUB_API_TOKEN`; it is defined in `deploy/k8s/10-github-emulator.yaml`.

## Steps

| Step | Command | Scenario |
| --- | --- | --- |
| Render catalogue (deterministic; lint for synthetic-only content) | `python3 scripts/generate_initiatives.py` (`--check` in CI) | — |
| Seed Jira: config import, issue import, read-back, `cc75-baseline` snapshot | `python3 scripts/seed_initiatives.py` | S0 |
| Discovery queries vs oracle | `python3 scripts/check_discovery.py` | S1 |
| strat-creator's own discovery JQL, per mirrored ref | `python3 scripts/check_tool_discovery.py` | S1b |
| Mirror public repos into the GitHub emulator | `python3 scripts/mirror_github.py` | — |
| Job-owned Fullsend/OpenShell gateway smoke in GitLab CI, no model | `python3 scripts/run_smoke.py fullsend-gateway` | S2 (part) |

To reset Jira, restore the `cc75-baseline` snapshot
(`POST /api/admin/snapshots/<name>/restore`). Do not use `/api/admin/reset`,
which drops the imported project configuration.

## Files

- `catalogue.yaml`: the 24 Initiatives, 3 Outcomes and 2 RFEs (fictional).
- `generated/issues.json` and `expected.yaml`: rendered from the catalogue;
  do not edit by hand.
- `source-manifest.json`: public upstreams and refs. Private GitLab sources
  are listed but still pending.
- `topology-manifest.json`: mirrored paths and commits (no credentials).
- `patches/strat-creator/`: emulator patches for the public strat-creator.
  The patches for the private GitLab projects quote private source, so they
  live outside this repository, in `$CC75_PRIVATE_PATCHES` (default
  `~/.cache/cc75/private-patches`).
- `smoke/`: CI smoke projects pushed to the GitLab emulator as `cc75/<name>`.
- `recording/`: records the demo as a captioned, narrated video; see
  [`recording/README.md`](recording/README.md).
- `evidence/`: sanitised run summaries. Full CI traces stay on the host under
  `~/.cache/cc75/traces/`.
