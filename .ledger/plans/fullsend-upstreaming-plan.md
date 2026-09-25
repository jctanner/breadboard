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

## The hard gate: this cannot start with an agent

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

- Thirteen upstream-bound fixes; six of the eight Go patches already carry
  tests, and one agents patch ships a test suite modelled on the project's
  existing GitLab host-mismatch test.
- Each patch header records what was observed, how, and why the fix is shaped
  as it is — see `deploy/fullsend/patches/`.
- Two earlier patches were dropped because upstream fixed the same ground
  natively; upstream movement is being tracked rather than ignored.

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

## What goes, and what never does

Sixteen patch files across three lists: eleven in
`deploy/fullsend/patches/` and five in `deploy/fullsend/patches/agents/`.
Thirteen are upstream-bound, two are local-only and must never be submitted,
one is retired.

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
| 0010 | do not report success for a profile import that replaced nothing | yes |
| 0011 | address the configured forge in the `github` subcommands | yes |
| 0012 | let an installation name the runner its workflows target | yes |

### Upstream-bound — `fullsend-ai/fullsend`, action YAML

Patches 0003 and 0004 (honour `GITHUB_API_URL`/`GITHUB_SERVER_URL`; skip local
sandbox host setup when a gateway is configured). Composite-action YAML, so the
Go coverage gate does not apply — but neither does a Go test, which makes the
reasoning in the PR body the only evidence a reviewer gets.

### Upstream-bound — `fullsend-ai/agents`

| patch | fixes | tests |
| --- | --- | --- |
| 0001 | accept an issue URL on the configured GitHub host (triage library) | none |
| 0002 | pass the forge host into the sandbox — all six GitHub overlays | none |
| 0005 | the same host assumption in the review, code and fix libraries | yes |

### Never submitted

Agents 0003 (`github.local` in the two GitHub profiles) and 0004 (CA-bearing
local images). Both are marked `NOT FOR UPSTREAM` in their own headers and exist
because this stack's forge is an emulator on a cluster address. They are
described in the compatibility profile and stay there.

### Retired

Go 0002 (insecure dev mint URL), retired 2026-09-24 when the mint moved to
internal TLS, per decision 3 of the conformance plan. Not a candidate.

## What upstream requires of each PR

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
  tolerance) and no more than a 1% drop in project coverage.** Six of the eight
  Go patches carry tests; **0005 does not**, and the two action-YAML patches
  cannot. Writing tests for 0005 is real work that has to happen before it can
  be submitted, not a formality at the end.
- **Focused PRs** — one problem area or decision per PR.
- **CODEOWNERS approval** before merge.
- **Rework means a new PR**, not a force-push, when the approach changes rather
  than the details.
- An ADR if a patch encodes a decision rather than a fix. None obviously does,
  but 0012 (`FULLSEND_RUNNER_IMAGE`) introduces a configuration seam and may
  attract that question; if it does, ADR first and implementation second.

## The grouping question, decided up front

Seven of the thirteen upstream-bound patches are one problem wearing different hats: *github.com
is assumed where the configured host should be used*. Go 0005, 0007, 0008, 0011
and agents 0001, 0002, 0005 all fix instances of it.

"Focused PRs — one problem area per PR" pulls two ways here. Submitting seven
separate PRs for one root cause invites seven reviews of the same argument.
Submitting one PR per repository per layer — the Go client, the action YAML, the
agents shell libraries — gives a reviewer one coherent story each time and
matches how the code is actually organised.

**Decision:** group by repository and layer, not by patch file. Expect roughly
five PRs, and say in each body that it is one facet of a single host assumption,
linking the others. Revisit if a maintainer asks for them split.

## Sequencing

Ordered so the cheapest possible failure comes first.

1. **Establish account standing.** Does the submitting account already have write
   access to `fullsend-ai`? If yes, the vouch gate does not apply and everything
   below starts immediately.
2. **File two or three bug reports** with patches and reasoning inline. No vouch
   needed for these, they are useful to upstream on their own, and they become
   the concrete evidence the vouch request cites.
3. **Vouch request** (human, own words, from the checklist above) if the gate
   applies.
4. **Refresh the checkouts and measure the damage.** Fetch both repos, rebase
   the patch set onto current `main`, and record which patches no longer apply,
   which are now unnecessary because upstream fixed them, and which changed
   shape. This is the first place the plan can shrink for free.
5. **One probe PR.** Patch 0010 — "do not report success for a profile import
   that replaced nothing" — is self-contained, carries a test, and is an
   obvious correctness bug with no design argument attached. Land that one
   first to learn the actual review cycle, CI behaviour and coverage reporting
   before the harder ones are exposed.
6. **The host-assumption cluster**, grouped as decided above.
7. **The remainder** — 0006, 0009, 0012 — each on its own merits.
8. **Write tests for 0005** before it goes anywhere.

## Breakpoints

Hard stops. Each produces something a human can look at, and each gets an
explicit go or pivot before the next begins.

- **U1. Standing established.** A one-line answer: the account has write access,
  or it needs a vouch. Everything else is shaped by this.
- **U2. Vouch granted** (or established as unnecessary). Nothing may be opened
  before this.
- **U3. Rebase report.** The patch set applied to current `main`, with a table of
  applies-clean / needs-rework / now-unnecessary. Runnable: the conformance
  stack still passes on the rebased patches.
- **U4. First PR merged.** One patch through the whole pipeline — lint, tests,
  coverage, review, CODEOWNERS approval. Proves the process, not the patch.
- **U5. Host-assumption cluster resolved** — merged, or rejected with a reason
  recorded here.
- **U6. Every upstream-bound patch has a terminal state**: merged, rejected with
  reason, or obsoleted by upstream. The compatibility profile shrinks to the two
  local-only substitutions, and `05i-build-fullsend.sh` stops applying what
  landed.

## Risks

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

- The two local-only agents patches. They never go upstream.
- Emulator work. `jctanner/github-emulator` is ours; its five fixes from
  2026-09-23 are already committed there.
- The four unrun harnesses (`fix`, `prioritize`, `retro`, `scribe`). If running
  them turns up more upstream-bound defects, they join this plan's inventory —
  but exercising them is conformance work, not upstreaming work.
