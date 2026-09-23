# Fullsend stage matrix — what triage, review and code actually require

Work package 4, first checklist item: collect from the three harnesses the
binaries, entrypoints, providers and credential paths they expect, and record
where this deployment does not yet supply them.

Source: `checkouts/fullsend-ai/agents/harness/{triage,review,code}.yaml` at the
mirrored revision. There are seven harnesses upstream — `fix`, `prioritize`,
`retro` and `scribe` as well — but only these three are in scope for the
conformance plan.

**Status of this document.** The triage column is observed: it has run, and
run 1436's evidence bundle backs every cell. The review and code columns are
*read from the harness files*, not observed. Nothing here claims they work.
That distinction is the whole point of the matrix, and it should stay explicit
until a real run replaces each unobserved cell.

## The matrix

| | triage (observed) | review (unobserved) | code (unobserved) |
| --- | --- | --- | --- |
| agent | `agents/triage.md` | `agents/review.md` | `agents/code.md` |
| role | `triage` | `review` | `coder` |
| slug | `fullsend-ai-triage` | `fullsend-ai-review` | `fullsend-ai-coder` |
| sandbox image | `fullsend-sandbox@sha256:259605…` | `fullsend-code@sha256:623fc7…` | `fullsend-code@sha256:623fc7…` |
| composition | `overlays:` with CEL `when:` | **`forge:` keyed map** | `overlays:` with CEL `when:` |
| providers | vertex-ai, github-ro | vertex-ai, github-ro | vertex-ai, **package-registries**, **gitleaks**, **github-code** |
| profiles | fullsend-vertex-ai, fullsend-github-ro | same | + fullsend-package-registries, fullsend-gitleaks, **fullsend-github-code** |
| skills | github-forge, issue-labels/github | pr-review, code-review, docs-review, pr-risk-assessment, github-forge, issue-labels, pr-review/github | code-implementation, github-forge |
| plugins | none | none | **gopls-lsp** |
| pre script | `pre-triage.sh` | `pre-review.sh` | `pre-code.sh` (jira overlay swaps in `pre-code-jira.sh`) |
| post script | `post-triage.sh` | `post-review.sh` | `post-code.sh` |
| validation | triage-result schema, 2 iterations | review-result schema, 1 iteration | code-result schema, 2 iterations, `feedback_mode: append` |
| timeout | 10 min | 45 min per iteration | 60 min per iteration |
| repo access | read | `readonly_repo: true` | read/write via post script |
| what it writes | issue labels and comments | PR review comments | **pushes a branch and opens a PR** |
| write credential | minted triage token | `REVIEW_TOKEN` | `PUSH_TOKEN` on the runner, never in the sandbox |

## Model selection, and how haiku is applied

The harness files all pin `model: opus`. This deployment does not patch that.
Selection happens at run time through repository Actions variables, observed in
run 1436:

```
FULLSEND_RUNTIME=claude (repository variable)
FULLSEND_MODEL=haiku (repository variable)
→ Agent: claude-haiku-4-5@20251001 (v2.1.260)
```

They are repository-scoped, not stage-scoped, so they already cover review and
code on the same repository with nothing further to set. Run 1436 cost $0.10.
The repository's `.fullsend/config.yaml` says `runtime: dummy`; the variable
overrides it, which is worth knowing before reading that file and concluding no
model runs.

One caveat to carry into the review and code work: haiku is weaker, and the
validation loops are bounded (1 and 2 iterations). A schema failure there will
be ambiguous between a model too weak to produce conforming output and a real
integration defect. Keep the two distinguishable in evidence rather than
reading every failure as the plan's kind of bug.

## Confirmed gaps, verified against the running stack

Checked rather than inferred, on 2026-09-23:

1. **No local `fullsend-code` image.** `k3s ctr images ls` has
   `fullsend-sandbox` and its CA-bearing local variant, and nothing for
   `fullsend-code`. Both review and code use that image. Without a local build
   they pull from ghcr with no internal CA, which is precisely the failure
   agents patch 0004 exists to prevent — every proxied HTTPS call to the forge
   fails its handshake and the agent sees a connection reset.
2. **`gitleaks` and `pre-commit` are missing from the runner.** Checked
   directly in the runner pod: `yq`, `gh`, `jq`, `git` and `python3` are
   present; `gitleaks`, `pre-commit`, `gopls`, `go`, `node` and `npm` are not.
   `post-code.sh` runs on the runner and does a secret scan and a pre-commit
   pass before pushing. This is the same class as G9.
3. **The repository allows only the triage role.** `.fullsend/config.yaml` on
   `fullsend-dev/triage-target` has `roles: [triage]`. The mint itself is
   already configured for `triage`, `scribe`, `coder`, `review`, `fix` and
   `fullsend`, so the mint is not the constraint — the repository config is.
4. **Three profiles the code stage needs are not installed.** The gateway
   serves `fullsend-vertex-ai` and `fullsend-github-ro`. Code additionally
   wants `fullsend-package-registries`, `fullsend-gitleaks` and
   `fullsend-github-code`, and the last of those will need the same
   emulator-host substitution that agents patch 0003 makes to the read-only
   profile.
5. **`fullsend-package-registries` means public egress** to package indexes.
   That collides directly with F4, which is open precisely because the sandbox
   boundary cannot be demonstrated while the pod can reach anything. Deciding
   what the code stage may reach is a boundary decision, not a configuration
   detail, and should be made deliberately.
6. **`review.yaml` composes with `forge:`, not `overlays:`.** Triage and code
   both use `overlays:` with CEL conditions, which this deployment has
   exercised. The `forge:` keyed form is untested here. It may work fine; it
   has simply never run.
7. **The conformance check waits 900 seconds.** Review budgets 45 minutes per
   iteration and code 60. A run that needs longer would currently be reported
   as a timeout by the harness rather than by the thing that actually stalled.

## The auto-code chain, traced: it already works

`triage.yaml` sets `TRIAGE_AUTO_CODE: "on"` with
`TRIAGE_AUTO_CODE_CATEGORIES: "bug,documentation,performance"`. Run 1436
labelled its issue `documentation`, which is on that list, and nothing in the
triage job log mentioned a promotion — the only role it requested was
`triage`. That looked like the next silent failure.

It is not. Promotion is not a dispatch from inside the triage job; it is a
label. `post-triage.sh` applies `ready-to-code`, and the label event starts a
separate run. Tracing run 1436's successors:

| run | event | label | outcome |
| --- | --- | --- | --- |
| 1438 | `issues` labeled | `documentation` | no stage matched — correct, not a routing label |
| 1439 | `issues` labeled | `ready-to-code` | **routed to `code`**, then declined at the role gate |

Run 1439's Route job:

```
Step 3: Determine stage
Routed to stage: code

Step 8: Check role is enabled
::notice::Stage 'code' skipped — role 'coder' not in configured roles
```

Every link holds. The emulator emitted `action: labeled` with a populated
`label.name`; the server rendered the Route step's environment correctly
(`EVENT_NAME=issues`, `EVENT_ACTION=labeled`, `TRIGGERING_LABEL=ready-to-code`,
`EVENT_SENDER_LOGIN=fullsend-triage[bot]`); the router's bot-sender branch
matched and selected `code`; and the role gate refused it because
`.fullsend/config.yaml` lists `roles: [triage]` — saying so in a notice that
names the stage, the role, and the reason.

That is the behaviour this plan keeps asking for and rarely gets: a thing that
does not happen, and says why. Worth recording as a positive result rather
than only cataloguing the failures.

It also changes the shape of the code-stage work. The trigger path is proven;
what is missing is everything downstream of the gate — the role in the
repository config, the local `fullsend-code` image, `gitleaks` and
`pre-commit` on the runner, and the three profiles.

**A caution for the earlier reading.** The first pass at this concluded "no
stage matched" from run *1438*'s log — the `documentation` label, where that
is the right answer — and nearly recorded a defect that did not exist. The
run whose log matters is the one carrying the routing label.
