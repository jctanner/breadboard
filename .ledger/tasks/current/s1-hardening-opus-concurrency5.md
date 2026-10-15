# One Opus three-RFE batch with five Workflow agent slots

Authorized by the user after the schema repair and concurrency configuration:
launch one S1 batch through markovd using claude-opus-4-6, high effort,
component f3508786a1e2200731b25dfeda7e01ef772d32ce and
CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS=5. No extra iteration or model probe.

## Checks

- [x] Schema-fixed component is pushed; 1,005 component tests and a native
  zero-provider completion control pass.
- [x] All 69 benchmark tests verify the prepared source/concurrency job wiring.
- [ ] Publish the exact benchmark source and sync/import it in markovd.
- [ ] Verify previous final archives before the seed resets Jira.
- [ ] Launch once and verify the actual model job's source, model and cap.
- [ ] Archive and independently verify all terminal evidence, even on failure.
- [ ] Analyze completion, delivery, preserved reports, source integrity and
  observed scheduling; no automatic paid retry.

## Configuration

Tier s1-hardening-opus, only_tests=S1, variants=opus, repeats=1,
wipe_at_start=false. Existing distinct three-RFE scenario. Native timeout
295 minutes, background wait 17,700,000 ms, job wait 18,000 seconds.

The cap permits up to five outer Workflow agents; three tickets may only supply
three ready agents. Forked Skill scheduling is separate. Both source and
concurrency change from the failed Opus run, preventing attribution of timing
differences to concurrency alone. Source/baseline rewrite protection, scorer
path and specialist format/delivery issues remain open; no new fixes are being
silently added to this run.

Evidence root: var/run-data/strat-workflow-hardening/opus-concurrency5/.
The launch intent must be recorded before the sole POST. An uncertain response
requires reconciliation, never a blind second POST. Terminal collection and
verification precede any later reset.

[Prepared configuration](../done/strat-workflow-next-opus-concurrency.md).
[Hardening plan](../../plans/strat-workflow-s1-hardening.md).
