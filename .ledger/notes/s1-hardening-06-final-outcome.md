# S1 repair 6: final completion checks

2026-10-14. [Plan](../plans/strat-workflow-s1-hardening.md).

## Source and behavior

Local emulator `opendatahub-io/strat-creator`, branch `eval/s1-hardening`,
candidate **`4c32d21bb2687bda032e4e609ea68853f3fe24dc`**. Published after the
final full suite passed. Historical benchmark refs are unchanged.

Test-only follow-up **`b6a228d300cc560978453cc310fbb10d45498f90`** is also published
on that branch. It updates the opt-in headless test's first-tool expectation for
the new completion preflight. The implementation is unchanged; another offline
full suite passed 941 tests with seven opt-in checks skipped. No additional
model run was launched.

The original last step could return `action: failed` normally and treated an
absent output checker as exit zero. The new step calls the deterministic
`strat_pipeline_state.py result` validator. It checks the expected RFE inventory,
one strategy per RFE, expected skips, completion marks, actual refined strategy
bodies, required review/source files, current-run composition provenance and
numeric decision consistency. It writes the result and `tmp/strat-completion.json`,
with input/progress/artifact hashes and a hash of the exact saved result.

The final structured result must carry that receipt's run ID, identity and
hash. A loaded plugin hook verifies the match against current files. A failed,
null or mismatched final result fails the Workflow. The trusted host validator
independently checks the receipt from its own code, reads downloaded files as
data and retains its Jira readback checks. There is no fallback success when
`fullsend-check-output` is unavailable.

Numeric scores remain the sole approval gate. A correctly completed review
recommending revise or reject is successful pipeline work, with its attention
flag retained. Specialist recommendations remain informational.

`completion-status` checks saved completion without calling skills. If a
reporting retry has an empty output directory, `result` restores the same
validated output and receipt when the current files still verify. It leaves
progress unchanged. Missing handoff warnings are reconciled with saved work;
they cannot promote missing work and do not invalidate already verified work.
The three primary prompts and host feedback use this recovery path first.

## Runtime and reporting are separate

`strat_pipeline_outcome.py inspect` reads native terminal state and its matched
journal, requiring this receipt in the completed Workflow result and a paired
started/result agent record. It checks the business record independently.
CLI exit zero cannot override a killed/failed/missing runtime, null result or
absent/truncated completion journal. It records work, runtime and CLI/reporting
status separately. A verified completed Workflow followed by a nonzero reporting
exit becomes `completed_with_reporting_error`, with `retry_work: false`.

The Claude binary's CLI exit behavior is unchanged. Its successful controller
result can still accompany a failed Workflow; the application check rejects
that combination. Likewise, reporting can fail after real work completes;
that failure must not erase the saved work or trigger rerunning it.

## Offline and native checks

Final component suite: **941 passed, seven opt-in live checks skipped**, 180.30s.
Lint, Python/shell checks and diff checks pass. The first full suite exposed an
older positive skip fixture that edited its result without updating saved
input/progress and validation. That fixture now produces a fresh receipt. A
subsequent canonical-result hash check has its own negative test and final full
suite. All test logs are retained; these are not additional model trials.

Fault fixtures cover missing refinement/push/review, bad inventory/skips, malformed
progress, changed artifacts, mismatched run/provenance/decision, forged completion,
changed result hashes, missing/truncated journals and cancelled/failed runtime.
Node executes the actual Workflow source, including null/invalid final outcomes.
Trusted-host tests reject a missing receipt despite otherwise matching files/Jira,
and verify reporting recovery without changing progress or the receipt.

Three real Claude Code **2.1.296** controls used a loopback API stub and no
provider credentials or inference. Exact fixture sources/settings are retained;
the early success/reporting captures precede the final canonical hash tightening,
and the final trusted verifier accepts their unchanged records too.

| Native control | Stub requests | CLI exit | Workflow | Application result |
| --- | ---: | ---: | --- | --- |
| Valid completed work | 6 | 0 | completed | Completed; invented receipt hash denied before valid return |
| Error injected only after terminal completion | 7 | 1 | completed | Work complete; reporting failed/unconfirmed; no work retry |
| One required role report removed despite saved success marks | 6 | 0 | failed | Incomplete/unverified; rejected despite CLI success |

For both completed controls, an empty output followed by `result --failed workflow`
restored the same receipt and output, with identical progress bytes. Independent
capture checks pass for the two completed controls; deliberately removing the
receiving helper receipt or changing native state to killed fails those checks.

## Single GLM validation

Job **`script-run-all-glm-5-3-1014-160206-564759`**, created 16:02:06 UTC,
completed 16:03:03 UTC: **57 seconds**. Source is the candidate above. One
focused test, no whole-job retry and no Haiku/Opus inference.

Two authored strategies were already refined, pushed in dry-run mode and
composed/reviewed before Claude started. The fixture extracts the actual final
step and schema from the production Workflow, overriding only its test effort
to medium. This tests final validation and receipt delivery; it does not test
strategy creation, fresh scoring, reviewer quality or the full pipeline.
The saved outcomes are STRAT-9601 approve/false and STRAT-9602 revise/true.
No Jira reset/write, publication or reviewer rerun occurred.

The independent verifier passes: one actual final helper command, its receipt
in the receiving request, matching structured output, an allowed completion
hook, both required outcomes and the exact receipt in native completed state
and journal. CLI exit zero; no errors; `retry_work: false`.

All **five request/response pairs** used exact hosted request ID
`rits/zai-org/glm-5-3`. Primary/helper aliases and the fixture step are configured
for medium effort; configuration does not establish upstream effort semantics.
Claude Code 2.1.296 binary SHA-256:
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`.

Captured usage: **21,250 input**, **56,832 cache-read input**, **0 cache creation**
and **1,873 output** tokens; reported categories total **79,955**. This is captured
usage, not a claim about GLM billing/category semantics. No dollar figure is inferred.

## Archives and status

Live evidence is complete, final and independently checksum-verified under:

`var/run-data/strat-workflow-hardening/06-final-outcome/script-run-all-glm-5-3-1014-160206-564759/20261014T161339639339Z/`

The live archive has **16 sources, 243 files, 1,192,646,410 bytes**, including
**11 browsable API files and 140 strace files**, native transcripts/state/journal,
candidate source and available MLflow/Jira/service/relay/system evidence.
It verifies with `complete=true`, `final=true`, `errors=[]`; its reset-guard receipt
is published. Manifest SHA-256:
`24cd1afad1548d4b22317b35875cb5f26b24bd6e95c1e06963122a76ff68e5da`.

Controls, exact source, all test logs (including earlier failed/changed checks),
launch metadata and independent verification have a separate verified capture:

`var/run-data/strat-workflow-hardening/06-final-outcome/controls/20261014T162745626178Z/`

**667 files, 9,566,070 bytes**, no symlinks. Manifest SHA-256:
`86c19fb4fedd5fe0a984f7be2652f3ff4a56f7408b0171545f1fbc096ef170ec`.
Neither finalized archive was modified after verification. Shared-service
snapshots cover the collection interval; they are not an atomic system snapshot.

The test-only follow-up, its full-suite log and final independent verification
have a separate checksum-verified supplement (six files, 113,379 bytes):

`var/run-data/strat-workflow-hardening/06-final-outcome/verification/20261014T164831905256Z/`

Manifest SHA-256:
`f02a1fc53856dce3101fe09f1c62bd8930cafd061a0fb3696bf5a326c6f388f1`.

Item 6's focused repair is done on the local hardening branch. The repair is validated;
production Fullsend/OpenShell execution, full batches and content accuracy remain
separate qualification. Fullsend's existing entrypoint is unchanged. Its host
validation checks business completion; native observation additionally requires
exported native state/journal, and no Fullsend export contract is assumed here.
General crash/replay idempotency, stale source/journal invalidation and deadline/
quota policy remain items 7–9. No subsequent item was started.
