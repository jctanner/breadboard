# Fullsend upstream issue drafts

Drafts of issues for `fullsend-ai/fullsend` and `fullsend-ai/agents`.

**Filed 2026-11-02 (CC-1):** every draft except 24, after a two-model
pre-filing review (GLM + DeepSeek, see `cc-1-filing/reviews/`) and a fresh
duplicate search and line-citation check against current `main`
(`cc-1-filing/preflight-report.md`). 18 drafts became issues; 27 was split
out of 18 during review; 24 is held (see its row). The parent of the
host-assumption cluster is
[fullsend#9036](https://github.com/fullsend-ai/fullsend/issues/9036), with
all children attached as sub-issues. Filed numbers are in the table below
and in `cc-1-filing/filed-issues.json`.

They follow the approach in the
[upstreaming plan](../../.ledger/plans/fullsend-upstreaming-plan.md) (revised
2026-10-30): file problem-only issues and let upstream's own agents write the
fixes. Each draft is written the way upstream's
`skills/filing-issues/SKILL.md` asks — what happens, what should happen, how to
reproduce, context — with no patch and no prescribed fix.

Each file has two parts:

- **The issue**: the title and everything between the two `---` rules. That is
  what gets filed.
- **Draft notes**: below the second rule, for review only — the local patch it
  corresponds to, the upstream commit it was checked against, where each fact
  came from, the duplicate-search verdict, and open questions.

## Filing order

Few at a time, so the first ones show how upstream's triage and code agents
handle them before more go in.

| order | file | repository | parent |
| --- | --- | --- | --- |
| **filed** | [12](12-fullsend-minted-token-is-not-used-by-gh-off-github-com.md) — **[fullsend#8952](https://github.com/fullsend-ai/fullsend/issues/8952)** minted token not used by `gh` off github.com, the trial: the remaining half of #8530, which upstream's agents fixed | fullsend | 10 (attached 2026-11-02) |
| filed | [02](02-fullsend-parse-raw-content-url-rejects-enterprise-hosts.md) — **[fullsend#9037](https://github.com/fullsend-ai/fullsend/issues/9037)** `ParseRawContentURL` rejects enterprise raw-content URLs | fullsend | 10 |
| filed | [10](10-fullsend-tracking-github-com-host-assumption.md) — **[fullsend#9036](https://github.com/fullsend-ai/fullsend/issues/9036)** Several code paths address github.com instead of the configured host | fullsend | — (parent) |
| filed | [01](01-agents-triage-issue-url-is-an-environment-variable.md) — **[agents#1864](https://github.com/fullsend-ai/agents/issues/1864)** `ISSUE_URL` is not described as an environment variable | agents | none |
| filed | [11](11-fullsend-agents-repo-fallback-and-status-comment-use-api-github-com.md) — **[fullsend#9038](https://github.com/fullsend-ai/fullsend/issues/9038)** agents-repo fallback and status comment | fullsend | 10 |
| filed | [13](13-fullsend-github-setup-and-set-address-api-github-com.md) — **[fullsend#9039](https://github.com/fullsend-ai/fullsend/issues/9039)** `github setup` / `github set` | fullsend | 10 |
| filed | [14](14-fullsend-default-allowed-remote-resources-refuses-the-configured-host.md) — **[fullsend#9040](https://github.com/fullsend-ai/fullsend/issues/9040)** default `allowed_remote_resources` | fullsend | 10 |
| filed | [15](15-fullsend-token-scope-status-reconcile-and-eval-measure-use-api-github-com.md) — **[fullsend#9041](https://github.com/fullsend-ai/fullsend/issues/9041)** token-scope, status reconcile, eval-measure | fullsend | 10 |
| filed | [16](16-fullsend-dispatch-route-lint-and-offline-cache-resolve-agents-repo-on-github-com.md) — **[fullsend#9042](https://github.com/fullsend-ai/fullsend/issues/9042)** `dispatch --route`, `lint`, offline cache | fullsend | 10 |
| filed | [17](17-agents-triage-rejects-issue-urls-on-the-configured-host.md) — **[agents#1865](https://github.com/fullsend-ai/agents/issues/1865)** triage rejects issue URLs on the configured host | agents | 10 |
| filed | [18](18-agents-ops-libraries-assume-github-com-urls.md) — **[agents#1866](https://github.com/fullsend-ai/agents/issues/1866)** ops libraries assume github.com URLs | agents | 10 |
| filed | [19](19-fullsend-agent-and-install-actions-call-github-com.md) — **[fullsend#9043](https://github.com/fullsend-ai/fullsend/issues/9043)** agent and install actions call github.com | fullsend | 10 |
| filed | [20](20-fullsend-agent-action-sets-up-a-local-sandbox-host-when-a-gateway-is-configured.md) — **[fullsend#9044](https://github.com/fullsend-ai/fullsend/issues/9044)** local sandbox setup despite a remote gateway | fullsend | none |
| filed | [21](21-fullsend-fetcher-refuses-a-forge-on-a-private-network.md) — **[fullsend#9045](https://github.com/fullsend-ai/fullsend/issues/9045)** fetcher refuses a forge on a private network | fullsend | none |
| filed | [22](22-fullsend-dummy-runtime-behaviour-ops-cannot-see-the-harness-environment.md) — **[fullsend#9046](https://github.com/fullsend-ai/fullsend/issues/9046)** dummy-runtime behaviour ops miss the harness env | fullsend | none |
| filed | [23](23-fullsend-scaffold-cannot-target-a-runner-other-than-the-default.md) — **[fullsend#9047](https://github.com/fullsend-ai/fullsend/issues/9047)** scaffold cannot target another runner | fullsend | none |
| held | [24](24-fullsend-dispatch-retriages-on-every-issue-edit.md) dispatch re-triages on every issue edit | fullsend | none |
| filed | [25](25-agents-triage-duplicate-rule-ignores-closed-issues.md) — **[agents#1867](https://github.com/fullsend-ai/agents/issues/1867)** duplicate rule vs `--state all` | agents | none |
| filed | [26](26-fullsend-code-image-cannot-be-seeded-by-the-openshell-kubernetes-driver.md) — **[fullsend#9048](https://github.com/fullsend-ai/fullsend/issues/9048)** `fullsend-code` sandboxes never Ready on OpenShell's Kubernetes driver (`/sandbox/.cache/gopls` 0700) | fullsend | none |
| filed | [27](27-agents-ops-push-remote-targets-github-com.md) `forge_set_push_remote` pushes to github.com regardless of the configured host — split out of 18 during review | agents | 10 |

**24 is held, not filed:** both review models concluded the premise may be
vacuous on github.com (GitHub's `issues.edited` carries only `title`/`body`
changes, which is what ADR 0002 routes to triage). File only with an
observed `edited` delivery whose `changes` carried neither, or an owner
decision to reframe.

## Before filing each one

- Re-run the duplicate search; upstream moves quickly.
- Re-check the cited lines against current `main`.
- File with the owner's account. For a sub-issue, attach it to the parent with
  the sub-issues API (see upstream's `filing-issues` skill), then update the
  parent's checklist with the issue number.
- Record the issue URL in the upstreaming plan.
