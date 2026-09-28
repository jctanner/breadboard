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

- **Issue edits trigger triage.** *Resolved on the emulator side 2026-09-27.* Upstream's intent is documented (Fullsend ADR 0002: triage on `issues.edited` "when title or body changed"; the triage doc and ADR 0054 repeat it; commit 1e67a2e3 added `edited` to the per-repo shim deliberately, with a parity test). The over-triggering here was the emulator's: it sent one `edited` for any update, milestone and assignee included, and no `changes` object. It now sends GitHub's events per change (`edited` only for title or body, with `changes`; `assigned`/`unassigned`; `milestoned`/`demilestoned`; nothing for a no-op) - github-emulator, tests in `tests/actions/test_event_triggers.py`; live: an assignee change started no run, a body edit started one. What remains is upstream's own gap: the dispatch does not read `changes`, so an issue-type change on GitHub still re-triages. A dispatch patch honouring ADR 0002 would be an upstream contribution, not done.
- **`TRIAGE_AUTO_CODE` on for the conformance path.** *Done 2026-09-27:* off on the conformance target through the per-repository harness override Fullsend ADR 0080 names - `.fullsend/triage.yaml` composed on the mirror's `harness/triage.yaml`, pinned by commit and content hash, referenced from `config.yaml`'s `agents` list. Written by `seed-triage-auto-code-off.py`, which the seed script runs, so a reset restores it. Configuration, not a substitution; recorded in the plan's glossary.
- **The onboarding button and the two local seeders.** *Resolved 2026-09-27, both seeders retired.* The vendored binary gave way to the release on the mirror. The allowlist gap was fixed at its source: patch 0013 makes `DefaultAllowedRemoteResources` derive the configured forge's two prefixes from `GITHUB_SERVER_URL`, so the CLI scaffolds them at `admin install` time and merges them into an existing config at run time; the button needs no extra step. Verified by onboarding a throwaway repository through the dashboard endpoint: its scaffold PR's `config.yaml` listed `https://github.local/fullsend-ai/{fullsend,agents}/` with no seeder run; conformance run 1738 green on the rebuilt CLI. The button now performs the whole onboarding the CLI owns; what stays local per repository is the App installation, bot collaborators and the runtime variables, none of which is a seeder.

## Conformance plan items open before today

- `fullsend-github-code` in the profile-staleness precondition.
- The seeder triggering the agents mirror's CI on every push.
- Track F2: the CLI rejects a non-HTTPS `--mint-url` at install time.
- The narrowest sandbox policy that passes; who may start onboarding and how it gets its App credential. (Work package 3 is closed: the mint trust write-up on 2026-09-27 and the per-run `identity.json` on 2026-09-28.)
- Scenario question from run 1743: repeated conformance issues can be triaged as duplicates of the closed earlier copies. *Decided 2026-09-28: accept it; not a Breadboard fix.* The cause is upstream: in `fullsend-ai/agents`, `agents/triage.md` defines a duplicate as an existing *open* issue, while the `github-forge` and `issue-labels` skills it is told to use list issues with `--state all`, so the model is shown closed issues and then told they do not count. The conformance check keeps asserting only that a label was applied.

## Upstream improvements to record, not build here

- `fullsend-ai/agents`: reconcile the duplicate rule (open issues only, `agents/triage.md` step 2b) with the forge skills' `gh issue list --state all` commands. Evidence: Breadboard conformance run 1743 on the emulator, haiku, `duplicate` of a closed issue with an identical body; the runs either side answered `sufficient`.
- `fullsend-ai/fullsend`: the dispatch routes every `issues.edited` to triage without reading `changes`; ADR 0002 says title or body only.
- `fullsend-ai/fullsend`: patch 0003 (the install action's hardcoded github.com clone) and patch 0013 (forge-derived default `allowed_remote_resources`), both written to be sent as-is.
 All at their checkboxes in `fullsend-integration-conformance-plan.md`. (MLflow and Observatory telemetry was taken out of the plan on 2026-09-27.)

## Harness-dispatch CLI install (found 2026-09-27, G48–G51 in the conformance plan)

- [x] G48 `actions/cache` shim on the agent runner (github-emulator 6547571).
- [x] G49 composite conditions see `inputs.*`; G50 `runner.*` left to the runner (github-emulator e02ee86).
- [x] G51 release path: emulator release assets (github-emulator 215183a) and `seed-fullsend-release.py` on the mirror; run 1727 green.
- [x] G52 step conditions imply `success()` (github-emulator 215183a).
- [x] Retired `seed-vendored-binary.py` (2026-09-27): the binary is removed from the target and the agent action installs from release v0.0.1.
- [x] Pushed: github-emulator through 215183a, breadboard through 0d465ea.
