# Prepare the next Opus batch with five Workflow agent slots

Status: done, configuration prepared locally. No paid run launched.

User requested `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS=5` for the next
Opus run. Updated `s1-hardening-opus` to use the schema-fixed component
`f3508786a1e2200731b25dfeda7e01ef772d32ce`, concurrency cap five, one S1
iteration and the existing distinct three-RFE scenario.

The per-test setting flows through Markov run metadata into the submitted job's
actual native environment variable. The wrapper validates a positive integer,
unsets an empty value so other tiers retain their CPU-derived default, and saves
the requested cap in run-summary.json. The benchmark result retains it too.
GLM's source pin and the other historical tier pins remain unchanged. The
completed pair's exact configuration remains available at its recorded
Breadboard source commit and in its immutable archives.

The cap permits up to five outer Workflow agents when ready; this three-ticket
pipeline may have only three ready at once. It does not change forked Skill
scheduling or guarantee five simultaneous requests. A future timing comparison
changes both component source and concurrency, so it cannot isolate concurrency.

Validation: current Markov directory validation and shell syntax pass. All 69
benchmark tests pass, including real offline Markov execution that asserts the
submitted Opus job receives cap five and the schema-fixed source. No network,
Jira reset, provider request or deployed workflow import was used by these
checks. Publish/sync this configuration before the next authorized launch.

Subsequently published/imported as Breadboard `5ed4a28` and used for the user's
separately authorized [single Opus run](s1-hardening-opus-concurrency5.md).
Actual Claude process verifies cap five and f350878. That run failed on upstream
HTTP 429; its complete final archive independently verifies.

[Hardening plan](../../plans/strat-workflow-s1-hardening.md).
