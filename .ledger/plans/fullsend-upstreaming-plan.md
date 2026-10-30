# Fullsend upstreaming plan

Get the upstream-bound patches Breadboard carries into `fullsend-ai/fullsend`
and `fullsend-ai/agents`, so the conformance path stops depending on a private
patch set that has to be rebased forever.

Started 2026-09-24, out of the closed
[Fullsend integration conformance plan](fullsend-integration-conformance-plan.md).
That plan found the defects; this one lands the fixes. It is deliberately a
separate plan because the gates are different: conformance was answerable by
running things locally, and this is answerable only by other people agreeing.

## Why now

Thirteen of the sixteen patch files are real defects that affect any GitHub
Enterprise install, not local accommodations. Every one of them was found by running
Fullsend's own code against a forge that is not github.com, which is a
configuration upstream supports and evidently does not test. Each patch header
already says "Written to be sent upstream as-is."

Two facts set the clock. The checkouts are pinned at 2026-09-16 and upstream is
merging in the #7300s — **eight days stale on a fast-moving project**. And two
earlier patches were dropped because upstream fixed the same ground natively,
which means the window in which a patch is still the best available answer is
not indefinite. Carrying them costs a rebase every time the checkout moves;
landing them costs a review cycle once.

## Approach, revised 2026-10-30: issues for upstream's agents

**Decision (owner, 2026-10-30): file issues, not pull requests, and let
upstream's own agents write the fixes.** `fullsend-ai/fullsend` runs Fullsend on
itself (`.fullsend/config.yaml`: triage, code, review panel, fix), so a
well-evidenced issue is the input that system is built for. The patches here
become evidence and a private reference, not submissions.

How an issue is written follows upstream's own
[`filing-issues`](../../checkouts/fullsend-ai/fullsend/skills/filing-issues/SKILL.md)
skill:

- **Problem, not solution.** What happens, what should happen, how to
  reproduce, and context. No patch in the body and no prescribed fix. Where the
  defect lives (file and function) is an observation and goes in as context;
  how to change it is the code agent's call.
- **Search first** for duplicates across `fullsend-ai/fullsend` and
  `fullsend-ai/agents`, in all states.
- **Every draft is approved by the owner before it is filed.** Filing is
  outward-facing and the skill requires it.
- **One problem per issue.** Related issues (the host-assumption cluster) hang
  off one parent through the sub-issues API rather than one issue listing nine
  defects.
- **Few at a time.** Start with one or two and see how triage and the code
  agent handle them before filing more; volume reads as automation regardless
  of merit.

What Breadboard adds is verification: when an agent opens a PR for one of these
issues, run it through this stack's conformance path (a non-github.com forge,
which upstream does not test) and report the result on the PR. When a fix
merges, the matching local patch is dropped at the next rebase.

The owner is already vouched and holds the triage role (U1, U2), so the vouch
sections below are kept as history only. "What upstream requires of each PR"
and "The grouping question" applied to PRs Breadboard would have opened; they
now describe what upstream's agents will do, not work for this plan.

## The hard gate: this cannot start with an agent

*Superseded: the owner is vouched (U2), and the approach is issues (above).*

`CONTRIBUTING.md` in both repos operates a **vouch system**, and it is aimed
directly at work like this:

> AI tools make it trivial to generate plausible-looking but low-quality
> contributions, so we require first-time contributors to be vouched by a
> maintainer before submitting pull requests. […] Write in your own words — do
> not have an AI generate the request. Requests that read like LLM output will
> be denied.
>
> **If you are not vouched, any pull request you open will be automatically
> closed.**

So step one is a Vouch Request discussion on `fullsend-ai/fullsend`, written by
a human, in their own words, and **not drafted, edited or "tidied up" by an
agent**. That is not a formality to route around; it is the project's stated
defence against exactly the kind of contribution this plan produces, and
attempting to launder AI prose through it would be both dishonest and, on their
own account, likely to fail.

What an agent can legitimately do beforehand: assemble the facts a human needs
to write that request from — which patches, what each fixes, how each was
found, what evidence exists. That material is in
[`docs/fullsend-compatibility-profile.md`](../../docs/fullsend-compatibility-profile.md)
and in the conformance plan's per-gap entries.

**Nothing downstream of this gate can be attempted until a maintainer comments
`/vouch`.** Org members and collaborators with write access bypass the check, so
if this work is done under an account that already has write access to the org,
this section is moot — establish that first, because it changes the whole shape
of the plan.

## What the vouch request needs to cover

A checklist of **facts and topics**, not draft sentences, and deliberately so.
The project's rule is "write in your own words — do not have an AI generate the
request", and a request assembled from pre-written prose would pass the letter
of that while defeating its point. Working from factual notes is not the same as
having the text written; these bullets are notes. The prose has to be the
submitter's.

Where each fact can be checked is given so nothing has to be taken on trust.

**Context — who is asking and why they were in the code at all**

- Breadboard runs Fullsend as a first-class service in a local K3s stack with
  emulated GitHub, GitLab and Jira forges — not a toy harness or a read-through
  of the source.
- The configuration exercised is enterprise-shaped: the forge is not
  `github.com`. That is a configuration Fullsend supports and, on this
  evidence, does not test.

**What was actually run** — evidence in
[`fullsend-integration-conformance-plan.md`](fullsend-integration-conformance-plan.md),
closing entry

- Real GitHub events through Fullsend's own `fullsend.yaml` shim and
  `reusable-dispatch.yml`, a mint verifying real OIDC claims, an OpenShell
  sandbox, a real agent against Vertex, and results written back to the forge.
- Three stages end to end: triage (labels and comments), review (a
  `CHANGES_REQUESTED` review with inline comments), code (a pushed branch, an
  opened pull request, an assignee).
- Nothing reimplemented and no compatibility shim between Fullsend and the
  forge; missing forge behaviour was added to the emulator instead.

**The recurring defect class** — the main thing worth reporting

- `github.com` assumed where the configured host belongs, in three separate
  layers: the Go client, the composite action YAML, and the agents shell ops
  libraries.
- Worth naming that it had already been fixed in *one* of six ops libraries
  upstream and never carried across — this is not a single oversight.
- Worth naming the security-relevant instance: `forge_set_push_remote` built
  `x-access-token:TOKEN@github.com/...`, so on an enterprise install a minted
  push token goes to github.com.

**Standalone defects**

- A provider profile import reporting success when it replaced nothing, leaving
  a gateway serving a stale policy while every run logged importing it.
- The sandbox not receiving `GH_HOST`/`GH_ENTERPRISE_TOKEN`, so `gh` inside the
  sandbox addresses github.com and authenticates as whatever the environment
  already held rather than as the minted role.
- The scaffold hardcoding a hosted runner label, so a scaffolded repository's
  first dispatch sits queued with nothing reporting why.

**What makes the submission credible**

- Fourteen upstream-bound fixes; nine of the twelve Go and action patches
  carry tests. The exceptions are 0003 and 0004, which are action YAML and
  have no Go test, and 0005, which still needs one. One agents patch ships a
  test suite modelled on the project's existing GitLab host-mismatch test.
- Each patch header records what was observed, how, and why the fix is shaped
  as it is — see `deploy/fullsend/patches/`.
- Three earlier patches were dropped because upstream fixed the same ground
  natively (0010 most recently, by #7973), and the set has been rebased onto
  v0.52.0; upstream movement is being tracked rather than ignored.

**What would *not* be submitted, and why** — probably the strongest single
signal

- Two local-only substitutions stay local: `github.local` in the two GitHub
  provider profiles, and the CA-bearing sandbox images. Both are artefacts of
  running against an emulator on a cluster address, both are marked
  `NOT FOR UPSTREAM` in their own headers, and both are documented in
  [`docs/fullsend-compatibility-profile.md`](../../docs/fullsend-compatibility-profile.md).
- Knowing which changes do not belong upstream is what separates someone who
  understands the codebase from someone generating plausible patches.

**The ask**

- Permission to open pull requests.
- Intent to group by repository and layer rather than filing thirteen PRs for
  one root cause — and willingness to split them if a maintainer prefers.

**If a patch is included in an issue body before vouching** — see
"Bug reports as a parallel path" below

- State that the patch is offered for inclusion under the project's licence,
  and that the submitter will sign off on it as a commit if that is preferable.
  Their DCO policy exempts autonomous agent commits because no human is present
  to certify; code lifted from an issue into an agent commit has a human origin
  and no sign-off, and saying so up front removes the ambiguity.

## Bug reports as a parallel path

*Superseded in part by the revised approach above: issues are now the main
path, and they describe the problem without the patch, as upstream's
`filing-issues` skill asks. The three report-only observations at the end of
this section still stand and are good early issues.*

The vouch system gates pull requests, not issues. Filing well-evidenced bug
reports needs no vouch, is useful to upstream immediately, and their
`CONTRIBUTING.md` documents a split queue — a "contributor issue search" that
excludes issues reserved for agents, filtered by bot author and by
`label:ready-to-code`. An issue their triage classifies as a bug may therefore
be picked up and fixed by their own code agent.

Include the patch and the reasoning in the issue body. Withholding a fix in
order to have their agent reproduce it would be using them, and the reasoning is
the part a bug report otherwise loses — several of these fixes are non-obvious
in ways a symptom description does not convey.

Two constraints: start with two or three of the best-evidenced defects rather
than thirteen, since volume reads as automation regardless of merit; and for the
patches that carry tests, a real pull request remains materially better once
vouched, because an issue gets no CI, no coverage report and no line-level
review.

Three observations belong in this queue as reports rather than patches,
because each is a prompt or policy question upstream should decide, and a
patch would presume the answer. They are listed with their evidence in
`.ledger/tasks/pending/open-items-after-runner-consolidation.md` under
"Upstream improvements to record, not build here":

- the dispatch re-triages on every `issues.edited` without reading `changes`,
  against its own ADR 0002;
- the triage agent's duplicate rule (open issues only) against the forge
  skill's `--state all` listing;
- `agents/triage.md` names `ISSUE_URL` as an input without saying it is an
  environment variable, and haiku sometimes asks for it instead of reading
  it, making no tool call and failing validation. Three occurrences here,
  each with the harness side proven; a one-sentence prompt change.

The third is the best first report of the three: it has the cleanest
evidence (two identical runs that differ only in the model's first action),
the smallest fix, and it is the kind of thing a maintainer running on a
smaller model would hit themselves.

## What goes, and what never does

As of the v0.52.0 rebase (2026-10-30): thirteen active patch files in
`deploy/fullsend/patches/` and five in `deploy/fullsend/patches/agents/`.
Fourteen are upstream-bound, four are local-only and must never be submitted,
and three are retired. One further local substitution is an image, not a
patch: the CA-bearing OpenShell supervisor (see "Never submitted").

The three lists are not interchangeable and the build scripts say so: Go source
patches are applied before the binary is compiled, mirror patches to files a
workflow reads at run time, agents patches to the agents mirror at seed time. A
patch in the wrong list does nothing, and does it silently.

### Upstream-bound — `fullsend-ai/fullsend`, Go source

| patch | fixes | tests |
| --- | --- | --- |
| 0005 | resolve the agents repo and status comments against the configured host | **none** |
| 0006 | allow a forge reachable only privately | yes |
| 0007 | parse enterprise raw-content URLs | yes |
| 0008 | scope the minted token on forges that are not github.com | yes |
| 0009 | load the harness environment for dummy behaviour ops | yes |
| 0011 | address the configured forge in `github setup` and `github set` (upstream moved the other subcommands onto the configured host) | yes |
| 0012 | let an installation name the runner its workflows target | yes |
| 0013 | allow the configured forge in the default remote-resource allowlist | yes |
| 0014 | address the configured forge in the three remaining GitHub clients (status reconciliation, token-scope check, eval-measure manifest) | yes |
| 0015 | resolve the agents repo against the configured host in `fullsend dispatch --route` and `fullsend lint`, and in the offline-cache scan and dispatch label | yes |

### Upstream-bound — `fullsend-ai/fullsend`, action YAML

Patches 0003 and 0004 (honour `GITHUB_API_URL`/`GITHUB_SERVER_URL`; skip local
sandbox host setup when a gateway is configured). Composite-action YAML, so the
Go coverage gate does not apply — but neither does a Go test, which makes the
reasoning in the PR body the only evidence a reviewer gets.

### Upstream-bound — `fullsend-ai/agents`

| patch | fixes | tests |
| --- | --- | --- |
| 0001 | accept an issue URL on the configured GitHub host (triage library) | none |
| 0005 | the same host assumption in the review, code and fix libraries | yes |

### Never submitted

Four patches, each marked as local in its own name or header, and one image.
All exist because this stack's forge is an emulator on a cluster address with a
private CA. They are described in the compatibility profile and stay there.

- Agents 0002 (`GH_HOST` into the sandbox, and `GH_ENTERPRISE_TOKEN` as a
  provider placeholder). It replaced an upstream-bound patch that passed the
  real minted token through `env.sandbox`, which upstream #1407 now forbids;
  local by decision, 2026-10-29.
- Agents 0003 (`github.local` in the `fullsend-github-code` profile).
- Agents 0004 (CA-bearing local sandbox images).
- Go 0016 (`github.local` in the read-only profile, which v0.52.0 embeds in
  the fullsend binary, and the `GH_ENTERPRISE_TOKEN` placeholder on it). This
  is the half of agents 0003 that moved with the profile.
- The `openshell-supervisor-local` image: OpenShell 0.1.x runs the supervisor
  in its own image, so the internal CA has to be added there too.

### Retired

- Go 0002 (insecure dev mint URL), retired 2026-09-24 when the mint moved to
  internal TLS, per decision 3 of the conformance plan.
- Go 0010 (do not report success for a profile import that replaced nothing),
  retired 2026-10-29: upstream #7973 verifies the gateway's exported profile
  before treating "already exists" as success.
- The old agents 0002 (real forge token through `env.sandbox`), replaced by
  the local-only agents 0002 above.

None is a candidate.

## What upstream requires of each PR

*Now context only: these are the gates upstream's agent PRs pass. Useful for
judging an agent PR during verification, not work for this plan.*

Gathered from `CONTRIBUTING.md` and `COMMITS.md` rather than assumed:

- **DCO sign-off** (`git commit -s`). Human-driven agent sessions sign off — the
  human directing the session certifies personhood and legal authority. The
  autonomous-agent exemption does not apply here: these are not agent commits
  made by the fullsend bot identity.
- **Conventional Commits**, and the forbidden type+scope table is enforced by a
  gitlint rule: `fix(ci)`, `feat(ci)`, `fix(e2e)` and `feat(e2e)` are rejected in
  favour of `ci(<subsystem>)`. Our patch subjects already use `fix(<area>)`
  shapes and should be re-checked against the table rather than trusted.
- **`make lint` before pushing**, and for Go changes **`make go-test`**.
- **Coverage, the sharpest gate: 80% patch coverage on changed lines (5%
  tolerance) and no more than a 1% drop in project coverage.** Nine of the ten
  upstream-bound Go patches carry tests; **0005 does not**, and the two
  action-YAML patches cannot. Writing tests for 0005 is real work that has to happen before it can
  be submitted, not a formality at the end.
- **Focused PRs** — one problem area or decision per PR.
- **CODEOWNERS approval** before merge.
- **Rework means a new PR**, not a force-push, when the approach changes rather
  than the details.
- An ADR if a patch encodes a decision rather than a fix. None obviously does,
  but 0012 (`FULLSEND_RUNNER_IMAGE`) introduces a configuration seam and may
  attract that question; if it does, ADR first and implementation second.

## The grouping question, decided up front

*Revised for issues: one problem per issue, the host-assumption ones as
sub-issues of one parent. The grouping by layer below still describes how the
fixes would naturally split.*

Nine of the fourteen upstream-bound patches are one problem wearing different hats: *github.com
is assumed where the configured host should be used*. Go 0005, 0007, 0008, 0011,
0013, 0014, 0015 and agents 0001, 0005 all fix instances of it. 0014 was found
last (2026-09-29) and is the strongest single argument for the cluster: 0005
had already moved the run's own status comment onto the configured host, and
the post-job step that reconciles an orphaned one was still built with the bare
constructor, so a hard-killed run's "Started" comment could never be
finalized. 0015 was found in the v0.52.0 rebase: `fullsend dispatch --route` and
`fullsend lint` arrived upstream after 0005 and repeated the bare constructor.
A grep for `gh.New(` after the cluster lands should find only the
constructor itself, `newGitHubLiveClient`, and three callers off the
conformance path that this plan leaves alone (`agent.go` for URL agents,
`inference_openai.go`, `mint_setup.go`); say so in the PR body, because it
is the check a reviewer can repeat.

"Focused PRs — one problem area per PR" pulls two ways here. Submitting seven
separate PRs for one root cause invites seven reviews of the same argument.
Submitting one PR per repository per layer — the Go client, the action YAML, the
agents shell libraries — gives a reviewer one coherent story each time and
matches how the code is actually organised.

**Decision:** group by repository and layer, not by patch file. Expect roughly
five PRs, and say in each body that it is one facet of a single host assumption,
linking the others. Revisit if a maintainer asks for them split.

## Sequencing

Revised 2026-10-30 for the issues approach. Ordered so the cheapest possible
failure comes first.

1. **Standing.** Done: vouched, triage role.
2. **Refresh and measure.** Done for v0.52.0 (U3). Repeat before filing each
   batch, so an issue never reports something upstream has already fixed.
3. **First issue.** The `ISSUE_URL` prompt ambiguity in `agents/triage.md`
   (from "Bug reports as a parallel path"): cleanest evidence, smallest fix,
   and it exercises triage and the code agent on the agents repository. File
   0007 (enterprise raw-content URLs) alongside it or right after, as the
   first host-assumption defect: self-contained, no design argument.
4. **Watch one issue through**: triage outcome, whether the code agent picks
   it up, the PR it opens, review. Verify the PR on this stack and comment
   with the result.
5. **The host-assumption cluster**: a parent issue, then the remaining
   defects (0005, 0008, 0011, 0013, 0014, 0015, agents 0001 and 0005) as
   sub-issues, a few at a time.
6. **The rest**, each on its own merits: 0006, 0009, the action-YAML pair
   0003/0004, and 0012, which adds configuration surface and may draw an ADR
   first (upstream has its agents merge ADRs separately from implementation).
7. **The other two report-only observations** from "Bug reports as a
   parallel path".
8. **Drop each local patch** at the next rebase after its fix merges.

### Superseded PR sequencing (before 2026-10-30)

1. **Establish account standing.** Does the submitting account already have write
   access to `fullsend-ai`? If yes, the vouch gate does not apply and everything
   below starts immediately. Done 2026-10-30: already vouched, triage role.
2. **File two or three bug reports** with patches and reasoning inline. No vouch
   needed for these, they are useful to upstream on their own, and they become
   the concrete evidence the vouch request cites.
3. **Vouch request** (human, own words, from the checklist above) if the gate
   applies. Not needed: already vouched (U2).
4. **Refresh the checkouts and measure the damage.** Done 2026-10-30, against
   v0.52.0: [rebase report](../tasks/current/fullsend-v052-patch-rebase.md).
   One patch dropped as fixed upstream (0010), one added (0015), agents 0002
   made local-only, and conformance passes on the result (run 1816). Repeat
   before each submission; upstream moves quickly.
5. **One probe PR.** Patch 0007 — parse enterprise raw-content URLs — is
   self-contained, carries a test, and is an obvious correctness bug with no
   design argument attached. (The original probe, 0010, was fixed upstream.)
   It belongs to the host cluster but stands alone, so it can be submitted by
   itself and cited by the cluster PRs. Land it first to learn the actual
   review cycle, CI behaviour and coverage reporting before the harder ones
   are exposed.
6. **The host-assumption cluster**, grouped as decided above.
7. **The remainder** — 0006, 0009, 0012 — each on its own merits.
8. **Write tests for 0005** before it goes anywhere.

## Breakpoints

Hard stops. Each produces something a human can look at, and each gets an
explicit go or pivot before the next begins.

- **U1. Standing established.** A one-line answer: the account has write access,
  or it needs a vouch. Everything else is shaped by this.
  **Answered 2026-10-30:** the submitting account is already vouched and holds
  the triage role on `fullsend-ai` (the owner is building a case for
  maintainer). Triage is not write access, but the vouch is what the gate
  checks.
- **U2. Vouch granted** (or established as unnecessary). Nothing may be opened
  before this. **Met 2026-10-30:** already vouched; no request needed.
- **U3. Rebase report.** The patch set applied to current `main`, with a table of
  applies-clean / needs-rework / now-unnecessary. Runnable: the conformance
  stack still passes on the rebased patches.
  Report against v0.52.0 (2026-10-29):
  [Fullsend v0.52.0 patch rebase](../tasks/current/fullsend-v052-patch-rebase.md).
  Conformance passes on the rebased set (run 1816). Reached 2026-10-30;
  awaiting go or pivot.
- **U4. First issue through upstream's agents.** One issue filed, triaged, and
  either fixed by an agent PR that merges or answered by a maintainer. The
  agent PR is verified on this stack and the result posted on it. Proves the
  process, not the fix.
  **Trial filed 2026-10-30:** [fullsend#8952](https://github.com/fullsend-ai/fullsend/issues/8952)
  (minted token not used by `gh` off github.com; local patch 0008), chosen
  over the `ISSUE_URL` prompt issue because its sibling #8530 went through
  upstream's agents publicly (labelled `security`) and it verifies cleanly
  here: drop 0008 and rerun conformance. Drafts for the rest:
  `docs/fullsend-issue-drafts/`.
  Same day: upstream triage labelled it `bug`/`ready-to-code`; the code agent
  opened [PR #8955](https://github.com/fullsend-ai/fullsend/pull/8955)
  (`bc3e038`); review raised one finding (runner-secret refusal list), the fix
  agent pushed `6c9c1ce`, review approved. Verified here with 0008 skipped
  (`FULLSEND_SKIP_PATCHES` in 05i, branch `verify/8955` in the checkout):
  conformance runs 1821 (first commit) and 1826 (both) passed, all labels and
  comments by `fullsend-triage[bot]`. Result posted on the PR. Waiting on a
  human approval to merge; then drop 0008 at the next rebase.
  17:19 UTC: waynesun09 reviewed `6c9c1ce` (comment, two medium findings, both
  documentation: the runner-secret refusal of `GH_ENTERPRISE_TOKEN` is an
  unrecorded breaking change in the PR body and `BREAKING CHANGE` trailer, and
  `harness-reference.md`'s refused-names list omits it). Not ours to act on:
  `/fs-fix` needs write permission (ADR 0054 `is_authorized`), and the
  owner's triage role does not have it. Re-verify only if the fix changes
  code.
- **U5. Host-assumption cluster resolved**: each sub-issue fixed, declined
  with a reason recorded here, or obsoleted by upstream.
- **U6. Every upstream-bound defect has a terminal state**: fixed upstream and
  the local patch dropped, declined with reason, or obsoleted. The
  compatibility profile shrinks to the local-only substitutions (four patches
  and the CA-bearing images), and `05i-build-fullsend.sh` stops applying what
  landed.

## Risks

- **An agent's fix may differ from ours**, or miss part of the defect (the
  host-assumption cluster has nine facets). That is acceptable: verify the
  agent PR on this stack and say precisely what still fails; keep the local
  patch until the upstream fix covers the case.
- **Mutation commands need write access.** `/fs-fix`, `/fs-retro` and
  `/fs-prioritize` require write permission (upstream ADR 0054); the owner's
  triage role can file, label, comment and use `/fs-triage`, so review
  follow-ups on agent PRs are the maintainers' to trigger.
- **Triage may not route an issue to the code agent** (needs-info, or not
  labelled ready-to-code). Answer what triage asks; the owner's triage role
  can apply labels where that is the honest classification.

- **AI provenance is the live one.** These patches were written in agent
  sessions. The project says so plainly about its own concerns, and a PR that
  reads as generated will get a colder review regardless of whether the fix is
  right. The mitigation is not to disguise it: each patch header already
  explains what was observed, how, and why the fix is shaped as it is, and that
  reasoning is the strongest thing these submissions have. A human sign-off is
  required anyway by the DCO.
- **Upstream may fix things first.** Already happened twice. That is a good
  outcome — it costs us a patch and buys the same behaviour — but it means delay
  has a price and the rebase report (U3) should be redone if this plan stalls.
- **Coverage on 0005 may be awkward.** It touches agents-repo resolution and
  status-comment clients; if the seam is hard to test, the honest options are to
  refactor for testability as part of the PR or to submit it last with the
  difficulty stated.
- **A maintainer may reject the premise** of a patch rather than its
  implementation — most plausibly 0012, which adds configuration surface. A
  rejection with a reason is a valid terminal state; the local patch then moves
  from "upstream-bound" to "local-only" in the compatibility profile, which is a
  documentation change, not a defeat.

## Out of scope

- The four local-only patches and the CA-bearing images. They never go
  upstream.
- Emulator work. `jctanner/github-emulator` is ours; its five fixes from
  2026-09-23 are already committed there.
- The four unrun harnesses (`fix`, `prioritize`, `retro`, `scribe`). If running
  them turns up more upstream-bound defects, they join this plan's inventory —
  but exercising them is conformance work, not upstreaming work.
