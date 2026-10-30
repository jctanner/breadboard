# Fullsend upstream issue drafts

Drafts of issues for `fullsend-ai/fullsend` and `fullsend-ai/agents`, for review
before anything is filed. Filed so far: 12 as
[fullsend#8952](https://github.com/fullsend-ai/fullsend/issues/8952) (2026-10-30, the trial run).

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
| **filed** | [12](12-fullsend-minted-token-is-not-used-by-gh-off-github-com.md) minted token not used by `gh` off github.com — **[#8952](https://github.com/fullsend-ai/fullsend/issues/8952)**, the trial: the remaining half of #8530, which upstream's agents fixed | fullsend | 10 (attach later) |
| next | [02](02-fullsend-parse-raw-content-url-rejects-enterprise-hosts.md) `ParseRawContentURL` rejects enterprise raw-content URLs | fullsend | 10 |
| next | [10](10-fullsend-tracking-github-com-host-assumption.md) Several code paths address github.com instead of the configured host | fullsend | — (parent) |
| next | [01](01-agents-triage-issue-url-is-an-environment-variable.md) `ISSUE_URL` is not described as an environment variable | agents | none |
| later | [11](11-fullsend-agents-repo-fallback-and-status-comment-use-api-github-com.md) agents-repo fallback and status comment | fullsend | 10 |
| later | [13](13-fullsend-github-setup-and-set-address-api-github-com.md) `github setup` / `github set` | fullsend | 10 |
| later | [14](14-fullsend-default-allowed-remote-resources-refuses-the-configured-host.md) default `allowed_remote_resources` | fullsend | 10 |
| later | [15](15-fullsend-token-scope-status-reconcile-and-eval-measure-use-api-github-com.md) token-scope, status reconcile, eval-measure | fullsend | 10 |
| later | [16](16-fullsend-dispatch-route-lint-and-offline-cache-resolve-agents-repo-on-github-com.md) `dispatch --route`, `lint`, offline cache | fullsend | 10 |
| later | [17](17-agents-triage-rejects-issue-urls-on-the-configured-host.md) triage rejects issue URLs on the configured host | agents | 10 |
| later | [18](18-agents-ops-libraries-assume-github-com-urls.md) ops libraries assume github.com URLs | agents | 10 |
| later | [19](19-fullsend-agent-and-install-actions-call-github-com.md) agent and install actions call github.com | fullsend | 10 |
| later | [20](20-fullsend-agent-action-sets-up-a-local-sandbox-host-when-a-gateway-is-configured.md) local sandbox setup despite a remote gateway | fullsend | none |
| later | [21](21-fullsend-fetcher-refuses-a-forge-on-a-private-network.md) fetcher refuses a forge on a private network | fullsend | none |
| later | [22](22-fullsend-dummy-runtime-behaviour-ops-cannot-see-the-harness-environment.md) dummy-runtime behaviour ops miss the harness env | fullsend | none |
| later | [23](23-fullsend-scaffold-cannot-target-a-runner-other-than-the-default.md) scaffold cannot target another runner | fullsend | none |
| later | [24](24-fullsend-dispatch-retriages-on-every-issue-edit.md) dispatch re-triages on every issue edit | fullsend | none |
| later | [25](25-agents-triage-duplicate-rule-ignores-closed-issues.md) duplicate rule vs `--state all` | agents | none |
| later | [26](26-fullsend-code-image-cannot-be-seeded-by-the-openshell-kubernetes-driver.md) `fullsend-code` sandboxes never Ready on OpenShell's Kubernetes driver (`/sandbox/.cache/gopls` 0700) | fullsend | none |

## Before filing each one

- Re-run the duplicate search; upstream moves quickly.
- Re-check the cited lines against current `main`.
- File with the owner's account. For a sub-issue, attach it to the parent with
  the sub-issues API (see upstream's `filing-issues` skill), then update the
  parent's checklist with the issue number.
- Record the issue URL in the upstreaming plan.
