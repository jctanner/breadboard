# Task: Launch and archive one three-ticket S1 Opus batch

## Authorization

2026-10-11: user said "okay lets do a single S1 batch run w/ claude-opus-4-6".
Publish/sync the needed harness changes and launch exactly one S1 Opus run,
with the existing distinct three-RFE scenario and unchanged S1/S2 pins.
Preserve the completed Haiku evidence before Jira reset. No S2 or repeats.

## Acceptance criteria

- [ ] Publish validated archive guards, separate Opus tier and model checks.
- [ ] Sync/import exact pushed benchmark commit in markovd.
- [ ] Launch one S1 `tier2-opus` run, Opus 4.6, three RFEs, retained evidence.
- [ ] Verify exact seed set, model, design pin and 90-minute wait budget.
- [ ] Arrange a detached collector to save a verified final archive on completion.
- [ ] Record IDs and evidence in the evaluation plan; stop after this run.

## Preflight

No active pipeline jobs or Markov runs. Previous final Haiku archive passes
host checksums; live reset guard recognizes its refreshed receipt at
`/data/breadboard/strat-workflow/markov-run-02336f23/20261011T143354300275Z`.
Runtime estimate: about 50 minutes, planning range 40–60. Runner wait
override 5,400,000 ms; pinned design is unchanged.
All 23 offline tests, Markov validation, compilation, shell syntax and diff
checks passed. Relay preflight: zero dropped records/requests/events,
pending writes and storage errors.
