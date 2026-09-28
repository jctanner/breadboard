# Open items after the runner consolidation (2026-09-27)

Everything left open at the end of the runner consolidation plan, in one
place, so nothing depends on a chat transcript. Each item names where its
detail lives. The emulator bugs are being fixed in this task; the rest are
decisions or separate work.

## Emulator bugs (fixed 2026-09-27, github-emulator; deployed and conformance-checked below)

| item | detail | status |
| --- | --- | --- |
| Rerun leaves dependent jobs waiting forever | github-emulator `docs/bugs/fixed/rerun-leaves-dependent-jobs-waiting.md` | fixed: rerun rebuilds the run through detection and materialization |
| Restart mid-claim strands the job; cancel does not stop the runner | `docs/bugs/open/restart-mid-claim-strands-the-job.md` (defect 1 closed; the OOM half stays open) | fixed: unacknowledged claims requeue after 120 s; a cancelled job answers 409 and runner.py kills the step |
| Push processed after its pull request opens fires `synchronize` | `docs/bugs/fixed/push-processed-after-pull-request-opens.md` | fixed: synchronize only for a head that moved |
| Stale runner registrations accumulate | `docs/bugs/fixed/stale-actions-runner-registrations-accumulate.md` | fixed: same name in the same scope reuses the row, re-keys it and takes its jobs back |
| G45 job tokens are not repository-bound | conformance plan, "Runner consolidation findings" | fixed: a job token's writes are refused outside its own repository at the auth chokepoint |
| G46 `job_workflow_ref` reports the caller | same | fixed: the called workflow's owner/repo/path@ref is recorded on the job (migration 0009) and the OIDC token reports it |

## Emulator, open with an instrument armed

- **OOM kills, four so far, cause unidentified.** `docs/bugs/open/restart-mid-claim-strands-the-job.md`, defect 2, has every replay and its result. The memory watchdog counts completed requests per endpoint between reports; the next crossing of 512 MiB names the hot endpoint. Raising the 1536Mi limit is a stopgap on offer, not a fix.

## Fullsend-side behaviour, decisions rather than bugs

- **Issue edits trigger triage.** The shim listens to `issues: edited` and the router sends them to triage; thirty edits on 2026-09-27 cost $0.92 in haiku triages. Decide whether to drop `edited` from the shim for this stack or accept it as upstream's intent.
- **`TRIAGE_AUTO_CODE` on for the conformance path.** *Done 2026-09-27:* off on the conformance target through the per-repository harness override Fullsend ADR 0080 names - `.fullsend/triage.yaml` composed on the mirror's `harness/triage.yaml`, pinned by commit and content hash, referenced from `config.yaml`'s `agents` list. Written by `seed-triage-auto-code-off.py`, which the seed script runs, so a reset restores it. Configuration, not a substitution; recorded in the plan's glossary.
- **The onboarding button and the two local seeders.** The button covers what the CLI owns; the agents-mirror allowlist still runs by hand per repository (`seed-config-allowlist.py`, taking `FULLSEND_SEED_ORG`/`REPO`; the vendored-binary seeder is retired, the release on the mirror serves every repository). Decide whether the button runs them (runner consolidation plan, phase 2 status).

## Conformance plan items open before today

- `fullsend-github-code` in the profile-staleness precondition.
- The seeder triggering the agents mirror's CI on every push.
- Track F2: the CLI rejects a non-HTTPS `--mint-url` at install time.
- The mint trust write-up; recording actor, repo, role, workflow, mint exchange and downstream; the narrowest sandbox policy that passes; Fullsend traces and artifacts to MLflow and Observatory; who may start onboarding and how it gets its App credential. All at their checkboxes in `fullsend-integration-conformance-plan.md`.

## Harness-dispatch CLI install (found 2026-09-27, G48–G51 in the conformance plan)

- [x] G48 `actions/cache` shim on the agent runner (github-emulator 6547571).
- [x] G49 composite conditions see `inputs.*`; G50 `runner.*` left to the runner (github-emulator e02ee86).
- [x] G51 release path: emulator release assets (github-emulator 215183a) and `seed-fullsend-release.py` on the mirror; run 1727 green.
- [x] G52 step conditions imply `success()` (github-emulator 215183a).
- [x] Retired `seed-vendored-binary.py` (2026-09-27): the binary is removed from the target and the agent action installs from release v0.0.1.
- [ ] Push github-emulator (6547571, e02ee86, 215183a) and breadboard.
