# Confirm merged GitLab rollout remains on legacy

Owner reported MR !18 merged. Read-only verification on 2026-10-27T19:19Z
confirms merge at 19:10:15Z into main, commit
b00078ee43ab7c4a0b6b0d9903eb5c7b60503618 (squash
c5e2b873500a889bd4f78ad13b1e6b7ac0bc01fd). Source head was 200b04b.

Current upstream main is that merge commit. The merged .gitlab-ci.yml SHA-256
matches the locally tested branch byte-for-byte. STRAT_EXECUTOR defaults to
legacy, CLAUDE_BRANCH is stable-1.x, Workflow source remains fullsend-ai/main.
No executor override exists at project scope or active schedule 4222905
(main, 0 */6 * * *). No runtime cutover was enabled by the merge.

GitHub strat-creator PR #85 is still open/unmerged at 364e1ca. Its source
interfaces need to merge before selecting fullsend for a manual Workflow smoke.
Schedule enablement remains a later deliberate setting change.

Raw sanitized receipt: /tmp/strat-pipeline-merge-20261027T191933Z.json.
Only read APIs/configuration and updated ledger notes. No local branch switch,
source edit, CI variable/schedule change, model job or manual pipeline started.
