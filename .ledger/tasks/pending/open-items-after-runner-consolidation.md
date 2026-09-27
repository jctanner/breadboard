# Open items after the runner consolidation (2026-09-27)

Everything left open at the end of the runner consolidation plan, in one
place, so nothing depends on a chat transcript. Each item names where its
detail lives. The emulator bugs are being fixed in this task; the rest are
decisions or separate work.

## Emulator bugs (fixing now)

| item | detail | status |
| --- | --- | --- |
| Rerun leaves dependent jobs waiting forever | github-emulator `docs/bugs/open/rerun-leaves-dependent-jobs-waiting.md` | fixing |
| Restart mid-claim strands the job; cancel does not stop the runner | `docs/bugs/open/restart-mid-claim-strands-the-job.md`, defect 1 and the related note | fixing |
| Push processed after its pull request opens fires `synchronize` | `docs/bugs/open/push-processed-after-pull-request-opens.md` | fixing |
| Stale runner registrations accumulate | `docs/bugs/open/stale-actions-runner-registrations-accumulate.md` | fixing |
| G45 job tokens are not repository-bound | conformance plan, "Runner consolidation findings" | fixing |
| G46 `job_workflow_ref` reports the caller | same | fixing |

## Emulator, open with an instrument armed

- **OOM kills, four so far, cause unidentified.** `docs/bugs/open/restart-mid-claim-strands-the-job.md`, defect 2, has every replay and its result. The memory watchdog counts completed requests per endpoint between reports; the next crossing of 512 MiB names the hot endpoint. Raising the 1536Mi limit is a stopgap on offer, not a fix.

## Fullsend-side behaviour, decisions rather than bugs

- **Issue edits trigger triage.** The shim listens to `issues: edited` and the router sends them to triage; thirty edits on 2026-09-27 cost $0.92 in haiku triages. Decide whether to drop `edited` from the shim for this stack or accept it as upstream's intent.
- **`TRIAGE_AUTO_CODE` on for the conformance path.** A green triage labels `ready-to-code` and fires a code stage; conformance runs have had to cancel it by hand. Set it off for the conformance target (conformance plan, open list).
- **The onboarding button and the two local seeders.** The button covers what the CLI owns; the agents-mirror allowlist and the vendored binary still run by hand per repository (`seed-config-allowlist.py`, `seed-vendored-binary.py`, both taking `FULLSEND_SEED_ORG`/`REPO`). Decide whether the button runs them (runner consolidation plan, phase 2 status).

## Conformance plan items open before today

- `fullsend-github-code` in the profile-staleness precondition.
- The seeder triggering the agents mirror's CI on every push.
- Track F2: the CLI rejects a non-HTTPS `--mint-url` at install time.
- The mint trust write-up; recording actor, repo, role, workflow, mint exchange and downstream; the narrowest sandbox policy that passes; Fullsend traces and artifacts to MLflow and Observatory; who may start onboarding and how it gets its App credential. All at their checkboxes in `fullsend-integration-conformance-plan.md`.
