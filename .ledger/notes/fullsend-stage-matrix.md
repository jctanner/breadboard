# Fullsend stage matrix — what triage, review and code actually require

Work package 4, first checklist item: collect from the three harnesses the
binaries, entrypoints, providers and credential paths they expect, and record
where this deployment does not yet supply them.

Source: `checkouts/fullsend-ai/agents/harness/{triage,review,code}.yaml` at the
mirrored revision. There are seven harnesses upstream — `fix`, `prioritize`,
`retro` and `scribe` as well — but only these three are in scope for the
conformance plan.

**Status of this document.** Triage and review are both observed end to end.
Code is still read from the harness file and has not been run. The distinction
is the point of the matrix and should stay explicit until a run replaces each
unobserved cell.

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
2. ~~**`gitleaks` and `pre-commit` are missing from the runner**~~ - **also
   wrong, and for the same reason as 5 below.** They are absent from the image,
   which is what `command -v` in the runner pod showed, but absence is not the
   question: both install themselves. `gitleaks-install.lib.sh` downloads
   8.30.1 and verifies it against a per-platform SHA-256, and
   `precommit-gate.lib.sh` pip-installs `pre-commit==4.5.1` on demand - and
   skips outright, with a message, when the repository has no
   `.pre-commit-config.yaml`, which `triage-target` does not. Nothing needs
   adding to the image. Both installs do depend on the runner reaching
   github.com and PyPI, which it can only because of F4; that dependency is
   worth naming, but it is not the same claim as G9, where `yq` was genuinely
   absent with nothing to install it.
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
5. ~~**`fullsend-package-registries` means public egress**~~ - **wrong, and
   corrected here rather than quietly dropped.** Reading the profile instead
   of its name: it is seven named hosts (`registry.npmjs.org`,
   `registry.yarnpkg.com`, `pypi.org`, `files.pythonhosted.org`,
   `proxy.golang.org`, `sum.golang.org`, `storage.googleapis.com`), each
   read-only and `enforcement: enforce`, with a binary allowlist that excludes
   `curl`. `fullsend-gitleaks` is the same shape over three GitHub release
   hosts. That is the sandbox boundary working as designed, not a hole in it,
   and it does not collide with F4 - which is about the *runner* pod's
   unrestricted egress and stays open on its own terms. There is no trade to
   make and nothing to decide: the profiles import as shipped. The original
   claim was made from the profile's name and category, which is exactly the
   kind of inference this plan keeps warning about.
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


## The review stage, run

Three attempts, each failing honestly - every one reported `failure`, none
reported success while broken.

| run | reached | stopped at |
| --- | --- | --- |
| 1444 | route, mint `review`, profiles, providers | pre-script: `PR_URL does not match expected GitHub pattern` |
| 1450 | sandbox created, bootstrapped, six skills, code copied read-only, both security scans | `gh: Bad credentials (HTTP 401)` from inside the sandbox |
| 1456 | connectivity check, agent ran (haiku, exit 0, $0.03, 10.8s) | no `agent-result.json`; validation failed, post-script correctly skipped |

Two upstream defects, now agents patches 0005 and 0002:

**The PR_URL host assumption.** `github-review-ops.lib.sh` matched and stripped
a literal `https://github.com`. Patch 0001 had already fixed exactly this for
the triage library; three others still carried it, so every stage past triage
failed identically. It was three faults rather than one - validation, parsing,
and `forge_set_push_remote` building `x-access-token:TOKEN@github.com`, which
on an enterprise install sends a minted push token to github.com - plus a
fourth worth stating on its own: with `GITHUB_SERVER_URL` set to an enterprise
host, the old validation still *accepted* a github.com URL, because the host
was written into the pattern rather than derived.

**The sandbox credential.** Patch 0002 had scoped itself to triage and said so
in its own header: "The same overlay shape appears in the other agent harnesses
and would need the same two lines." It came due exactly there. `gh` takes its
host from `GH_HOST` and, off github.com, its credential from
`GH_ENTERPRISE_TOKEN`; the overlay passed neither. All six affected harnesses
now pass both.

Landing that patch exposed a defect in Breadboard's own seeder: it reset its
temp tree to the previous mirror before applying patches, making the mirror a
function of its own last result. A patch that adds a file applied once and then
failed on every later run, and a file deleted upstream would have stayed
mirrored forever. Fixed; verified by seeding three times.

## What the dummy runtime settled, and what it cost to ask

Run 1456's agent made **zero tool calls** and replied asking to be told the PR
URL, the repository and the output directory - values its own agent definition
documents as arriving in the environment. Two explanations fitted: the harness
did not deliver them, or the model did not use them. The artifacts could not
tell them apart; telemetry records the harness URL and no environment.

Rather than buy a stronger model to guess, the question went to the dummy
runtime, which runs scripted operations inside the real sandbox with no model
involved. A temporary scenario asserted the review inputs on run 1459. All
eight passed:

```
GH_TOKEN  GH_ENTERPRISE_TOKEN  GH_HOST
PR_URL  REPO_FULL_NAME  PR_NUMBER
FULLSEND_OUTPUT_DIR  REVIEW_FINDING_SEVERITY_THRESHOLD
```

So the harness delivered everything, and gap 6 from the list above - that
`review.yaml` composes with `forge:` rather than `overlays:` - **closes as a
non-issue**: the `forge:` form merges `host_files` and `env.sandbox` correctly.
The agent had its inputs and did not use them.

That is worth keeping as a method note rather than only a result. The cheap
deterministic probe answered the question the expensive one would only have
guessed at: a passing run on a larger model would have shown the path works
without ever establishing whether haiku had been given its inputs.

The scenario and `FULLSEND_RUNTIME` were restored afterwards, the scenario
verified byte-identical.


## Review, closed end to end

Run 1462 (sonnet) completed the path the three haiku runs could not: a
schema-valid `agent-result.json`, a `risk/moderate` label, a sticky comment,
and a `CHANGES_REQUESTED` review posted as `fullsend-review[bot]`. It found
both planted defects - the mutable default argument and the bare `except:` -
and flagged `scripts/` as a protected path.

It also found a third defect, in the emulator, by being the first client ever
to submit a review *with* inline comments:

**The emulator accepted a review's `comments` array and discarded it.**
`create_review` read `event`, `body` and `commit_id` and never looked at it.
The log said `Attaching 4 inline comment(s) · ✓ Review submitted`, the run went
green, the review carried the right state and body, and every inline finding
was gone. Nothing reported a loss. The only way to see it was to ask the API
for comments the client had been told were attached.

**And the fix for it nearly reintroduced the same shape one layer up.** The
first version required every comment to carry a `line` or `position`.
Fullsend's payload builder omits `line` when it is 0 and sets
`subject_type: "file"` for a whole-file finding, so those would have been
rejected - and `internal/cli/postreview.go` catches a 422 on the review and
resubmits with *no* inline comments at all. One unplaceable finding would have
cost every placed one, and the run would still have reported success. Caught by
reading the client's payload builder before spending another run, not by a
test. `subject_type` is now stored (migration 0008), returned, and used to
decide whether an anchor is required.

Verified in three places, which is worth distinguishing:

| claim | evidence |
| --- | --- |
| the handler stores what it is given | 552 emulator tests, new ones failing against the old handler |
| the deployed image does too, for both comment kinds | live smoke against `github.local` with Fullsend's exact payload |
| Fullsend's post-review path really delivers them | run 1471: 6 attached, **6 retained**, each on the right line |

The `subject_type: "file"` path is covered by the first two and *not* by an
agent run: every finding in run 1471 was line-anchored. Saying "the rerun
passed" would imply more than was shown.

Cost: $2.50 for run 1462, $1.77 for run 1471. The haiku runs were $0.03. The
difference is not diff size - the review harness fans out into sub-agents, and
a first estimate of "well under a dollar" was wrong by roughly threefold.
