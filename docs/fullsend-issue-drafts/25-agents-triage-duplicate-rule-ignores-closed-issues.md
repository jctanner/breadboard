<!-- Draft for review. Not filed. -->
# triage: duplicate rule counts only open issues, but the triage tooling also shows closed issues

**Repository:** fullsend-ai/agents
**Parent:** none

---

### What happens

The triage agent's definition and the commands it is given disagree about whether closed issues count as duplicates.

- `agents/triage.md` step 2b (line 41) says to "search open issues and pull/merge requests for related work". The `duplicate` action (line 284) is defined as "the same problem as an existing open issue".
- The same agent is told to fetch referenced issues "including **closed** ones" (line 90).
- `skills/github-forge/SKILL.md` line 26 lists `gh issue list --repo OWNER/REPO --state all --json number,title,state --limit 100`. The comment above it scopes that command to verifying finished children of a tracking issue.
- The `issue-labels` skill that triage loads (`skills/issue-labels/github/SKILL.md` line 57) lists `gh issue list --repo OWNER/REPO --state all --json number,title,labels --limit 50`.

So the model sees closed issues in the same run in which it is told that only open issues can be duplicates.

Observed outcome: a repository received a series of issues with an identical body, and each earlier copy was closed before the next was opened. A triage run (claude-haiku-4-5) labelled one of them `duplicate` and cited the previous, closed copy by number. The triage runs immediately before and after it, on issues with the same body, answered `sufficient`.

### What should happen

The definition of a duplicate and the issues the agent is shown are consistent, so that the same input gives the same action from run to run. Whether a closed issue can be a duplicate target (agents#367 argues triage should search closed issues to catch already-fixed bugs) is for maintainers to decide. Today the rule says no and the tooling feeds the model closed issues anyway.

### How to reproduce

1. Open an issue, then close it.
2. Open a new issue with the same title and body.
3. Run triage on the new issue several times.
4. Some runs return `duplicate` with `duplicate_of` set to the closed issue; others return `sufficient`.

### Context

Found while running Fullsend against a local GitHub API emulator. Related: agents#367 (triage should search closed issues and merged PRs), agents#899 (mutual-duplicate closures).

---

## Draft notes (not part of the issue)

- **Local patch:** none: report-only
- **Checked against:** fullsend-ai/agents@8f819a9 (origin/main, 2026-10-30). The relevant files have not changed between our checkout (f4acd03) and origin/main.
- **Evidence:**
  - The observed outcome: `.ledger/tasks/pending/open-items-after-runner-consolidation.md` line 39 (conformance run 1743, haiku, duplicate of a closed issue with an identical body; neighbouring runs `sufficient`).
  - The scenario shape (one issue text reused; the reset closes earlier copies; the earlier copy was cited by number): `.ledger/plans/fullsend-integration-conformance-plan.md` around lines 4126-4133.
  - All line references come from my own reading of origin/main.
- **Correction to the ledger framing:** the ledger says the forge skills list issues with `--state all`. On origin/main, the duplicate-search commands in `github-forge` (lines 20 and 23) use `--state open`. `--state all` appears only for tracking-issue children (line 26, with a comment saying so) and in the `issue-labels` label-convention research (line 57, run in a sub-agent that returns a summary). Triage's own line 90 also says to fetch closed referenced issues. The inconsistency is real but narrower than "the skills list all issues", and the body is worded to match that.
- **Duplicate search:** (`obs-dup`) no duplicate.
  - agents#367 (open): related, and linked in Context. It asks for closed issues to be searched; this issue reports that the rule and the tooling disagree today.
  - agents#899, and its PR agents#1487 (mutual-duplicate tie-breaker): related, linked.
  - agents#1496, #494, #1633, fullsend#2184, #576, #6765, #6704: unrelated.
  - fullsend#5653 (e2e triage test issues left open): unrelated, but the same "repeated synthetic issue" setting.
- **Open questions for the reviewer:**
  - I do not have the run 1743 transcript, so I cannot say which command showed the model the closed copy. The emulator's issue search honours `state:` but ignores `is:` qualifiers (`checkouts/github-emulator/src/app/services/search_service.py`, around lines 161-181). If `gh issue list --state open --search ...` reaches the emulator as `is:open`, the emulator would have returned closed issues where github.com would not. In that case part of this observation is emulator behaviour, not upstream's. Worth checking the run transcript before filing.
  - The reproduction is inferred from one observed run. I have not rerun it.
- **Reviewer check on the emulator question (added in review):** running `gh`
  against the emulator from the host failed before any search ("malformed
  version" from `/meta`), so the query `gh issue list --state open --search`
  sends could not be captured. From reading gh's source, `--state open` is
  sent as a `state:open` qualifier, which the emulator honours, not
  `is:open`; if so, the closed-issue match was not emulator behaviour. This is
  from memory of gh's source, not verified; confirm from the run 1743
  transcript before filing.
