# Initiatives demo on the emulators (about 25 minutes)

The Initiative flow end to end on w530, with no production systems:
rfe-creator autofix → strat-creator Initiative strategy → human sign-off →
epic-creator decomposition. Every step runs the production job that a scenario
verified (S3–S10); nothing is simulated. All data is synthetic (`[SYNTH]`
summaries, `cc75-*` labels, `75001+` keys). Model calls go through Model Relay
(`claude-opus-5-5`).

Run the commands on w530 from `~/breadboard-cc75/var/demos/initiatives`:

```bash
export BREADBOARD_DOMAIN=w530.local BREADBOARD_CA_FILE=~/.cache/cc75/w530-ca.crt PYTHONUNBUFFERED=1
```

Open beside the terminal: the Jira emulator (`https://jira.w530.local`), the
GitLab emulator (`https://gitlab.w530.local`) and the Model Relay console
(`https://relay.w530.local`, project `cc75-initiatives`).

Model steps take 14–24 minutes each, so start them while you talk (the
command returns once the job is playing; `--wait` follows it to the end). The
timings and costs below are from the 2026-11-17 rehearsal on the eventual-state
mirror (`main`, `JIRA_USERNAME`; rehearsals 3 and 5 in the ledger).

| # | Step | Command | Time | Model cost | Verified by |
| --- | --- | --- | --- | --- | --- |
| 0 | Reset | `python3 scripts/demo.py reset` | 1 min | — | S9 |
| 1 | The board | `python3 scripts/demo.py board` | 2 min | — | S0, S1 |
| 2 | Opt-in | `python3 scripts/demo.py optin RHAISTRAT-75005` | 1 min | — | S1 |
| 3 | Autofix | `python3 scripts/demo.py autofix` | 14 min (background) | ~$4 (3 Initiatives) | S5, rehearsal 3 |
| 4 | Tripwire | `python3 scripts/demo.py tripwire` | 2 min | — | S3 |
| 5 | Live strategy | `python3 scripts/demo.py live RHAISTRAT-75028` | 24 min (background) | ~$8 | S7, rehearsal 3 (rubric pass) |
| 6 | Human sign-off | `python3 scripts/demo.py signoff RHAISTRAT-75028` | 1 min | — | S8, demo check |
| 7 | Decomposition | `python3 scripts/demo.py decompose` | 20 min (background) | ~$5.50 per Initiative | S8, rehearsal 5 (12 Epics) |
| 8 | Switch off and roll back | `python3 scripts/demo.py killswitch`, then `reset` | 2 min | — | S9 |

Total model cost is about $18 with 75028 decomposed alone, or about $35 with every
signed-off Initiative decomposed (see step 7). Steps 3, 5 and 7 can run in parallel with
the talk track; start 3 and 5 early.

## Talk track

0. **Reset.** The Jira emulator returns to the `cc75-baseline` snapshot: 3
   Outcomes, 25 Initiatives, their child Epics and 2 RFEs, all synthetic.
1. **The board.** Initiatives span the quality range on purpose: tight ones
   (75004–75006), field gaps, poor and very long ones, ones already signed off,
   and one with hand-made Epics (75026). Point at `initiative-autofix-opt-in`:
   only opted-in Initiatives are ever touched.
2. **Opt-in.** The owner opts one more in. The label is the canary boundary;
   rfe-autofixer and strat-creator both require it.
3. **Autofix.** rfe-autofixer's production schedule-only job, played from an
   inactive schedule, reviews the first opted-in Initiatives. Expect a revised
   Initiative (S5: 75006 went from 6 to 9/10) and `[Initiative Creator]`
   comments. `initiative-needs-attention` can sit next to
   `initiative-autofix-rubric-pass`: the Initiative passed, and a human should
   still look.
4. **Tripwire.** A live Initiative run on strat-pipeline `main` without
   `INITIATIVE_LIVE=on` is refused: its `python-tests` job fails. Rollout
   is flags and run configuration on `main`, not a staging
   branch.
5. **Live strategy.** On strat-pipeline `main` with `INITIATIVE_LIVE=on` (the
   proposed cutover flag: the tripwire stays, and the owners flip one variable to
   go live), strat-creator writes
   the strategy for RHAISTRAT-75028, the Initiative written to pass review.
   `demo.py show RHAISTRAT-75028`: the `-strategy.md` and `-review.md`
   attachments and `strat-creator-rubric-pass`; `demo.py results` for
   `initiative-strategy/` in the data repo. In the check run it scored 7/8
   (APPROVE). Contrast: the archetypes scored 4/8 and an earlier, broader draft
   of 75028 5/8 (REVISE): "every inference request" pulled in runtimes without
   tracing hooks and a gRPC path the ingress does not route. Snapshot
   `cc75-demo-75028-approved` holds this state if the run is skipped.
6. **Human sign-off.** The one manual gate: `demo.py signoff RHAISTRAT-75028`
   adds `strat-creator-human-sign-off`.
7. **Decomposition.** epic-creator #40 (rhai-initiative workload) through
   epic-decomposer creates RHAI Epics under every signed-off Initiative, with
   `Blocks` links and `epic-creator-auto-decomposed`. In rehearsal 5 75028
   became 12 Epics (three spikes, the product decisions, the MLServer patch and
   wheel rebuild, controller injection and admission warning, collector
   ingress, the parallel-worker span, the attribute allowlist, the e2e suite and
   benchmark), after one review/revise round (11/14 -> 14/14);
   `demo.py show RHAISTRAT-75028` lists them. Snapshot
   `cc75-rehearsal5-decomposed` holds that state (`cc75-demo-75028-decomposed`
   is the earlier 11-Epic run). The job YAML is production's; `demo.py`
   passes `CLAUDE_REPO`/`CLAUDE_REPO_BRANCH` (#40, `pr-40` in the GitHub
   emulator) and `RESULTS_REPO` (emulator) as pipeline variables. The fixture's 75025–75027 are
   also signed off, so the run decomposes them too (about $5 each) and shows the
   finding: RHAISTRAT-75026 already had three Epics and gets more (S8: +5),
   because #40 skips only on its own label. To decompose 75028 alone, remove
   `strat-creator-human-sign-off` from 75025–75027 first.
8. **Switch off and roll back.** With `INITIATIVE_STRATEGIES` unset the
   pipeline offers only the RFE batch; `reset` restores the baseline exactly
   (S9 compares every issue).

## If a step fails

Each step is the same job the scenario runners use, with the same evidence
under `evidence/`. A failed model step costs nothing to retry until the agent
starts; check the job trace link the command prints. The scenario runners
(`scripts/run_*.py`) re-check a step with assertions.

## Known differences from production

The mirror adapts the private GitLab projects to the emulators and to w530
(sandbox images its CPU can run, emulator gaps, Model Relay). Those patches
quote private source, so they live outside this repository
(`$CC75_PRIVATE_PATCHES`, default `~/.cache/cc75/private-patches`). In
behaviour:

- `decompose-initiatives` is a proposed epic-decomposer job, and needs
  epic-creator #40.
- Every project carries `JIRA_USERNAME` only, as production will.
- A live Initiative run uses the proposed `INITIATIVE_LIVE=on` flag on `main`;
  production has no live path yet.
