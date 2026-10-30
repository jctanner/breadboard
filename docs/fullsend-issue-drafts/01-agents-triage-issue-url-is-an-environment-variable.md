<!-- Draft for review. Not filed. -->
# triage: agent definition does not say ISSUE_URL is an environment variable, so the model sometimes asks for it

**Repository:** fullsend-ai/agents
**Parent:** none

---

### What happens

`agents/triage.md` (lines 15-17) lists its inputs as:

```
- `ISSUE_URL` — the HTML URL of the issue.
```

It never says where that value comes from. The harness sets it as an environment variable in the sandbox shell (`harness/triage.yaml`, `env.sandbox`, lines 101, 122 and 149), but the agent is not told so.

With claude-haiku-4-5, the triage agent occasionally reads the Inputs list, decides `ISSUE_URL` is missing from "the user's message", asks for it, and ends without a tool call. No `agent-result.json` is written and the run fails output validation. The transcript of a passing run with identical harness content, skills and prompt differs only in that the model chose to run `echo $ISSUE_URL` (in another case `env | grep ISSUE_URL`) before doing anything else.

This is a low-rate flake: of 32 consecutive issue-triggered triage runs on one repository, 27 passed and none of the 4 failures was this. It was seen three times in total: twice on triage and once on review. For the review occurrence, a scripted check inside the same harness, with no model involved, confirmed that every input variable was set.

By inspection, `agents/review.md` describes its inputs the same way (lines 25-37: `PR_URL`, `REPO_FULL_NAME`, `FULLSEND_OUTPUT_DIR` are "set by the harness" but not called environment variables). In the review occurrence the agent made no tool call and asked to be told the PR URL, the repository and the output directory. `agents/fix.md` does name its inputs as environment variables (for example `TRIGGER_SOURCE`, line 61).

### What should happen

The agent reads its documented inputs from its environment and starts work. It does not ask the user for values the harness has already provided.

### How to reproduce

1. Run the triage agent with `FULLSEND_MODEL=haiku` (claude-haiku-4-5) on an issue-opened event, repeatedly.
2. Occasionally a run ends within about ten seconds with exit 0 and no tool calls. The final message asks for the issue URL, and validation reports that `agent-result.json` is missing.
3. Check the sandbox environment for that run: `ISSUE_URL` is set.

### Context

Found while running Fullsend against a local GitHub API emulator. Larger models (Opus, Sonnet) were not seen to do this. Each failed run cost about $0.03, but the issue received no triage decision until someone re-ran it.

---

## Draft notes (not part of the issue)

- **Local patch:** none: report-only
- **Checked against:** fullsend-ai/agents@8f819a9 (origin/main, 2026-10-30)
- **Evidence:**
  - Behaviour, the 27/32 rate, the three occurrences (review run 1456, triage runs 1581 and 1801), the `echo $ISSUE_URL` comparison with passing run 1751, and the claim that the harness is not at fault: `.ledger/tasks/pending/open-items-after-runner-consolidation.md` line 41.
  - The `env | grep ISSUE_URL` difference (run 1581 compared with passing run 1553), "user's message", "exit 0 in ten seconds", $0.03, and the dummy-runtime probe (run 1459, eight review inputs all present): `.ledger/notes/fullsend-stage-matrix.md`, "What the dummy runtime settled" section, around lines 202-245.
  - Model id claude-haiku-4-5 (`FULLSEND_MODEL=haiku`): stage matrix lines 43-44.
  - Inputs wording, the `env.sandbox` lines, and the review and fix wording come from my own reading of origin/main (`agents/triage.md`, `agents/review.md`, `agents/fix.md`, `harness/triage.yaml`). `agents/code.md` has no Inputs section and does not mention `ISSUE_URL`.
  - The probe was run for review (1456). The ledger says the harness side of 1581 was "proven by a deterministic probe both times", but the probe I could find (run 1459) asserted only the review inputs. Step 3 of the reproduction leans on that ledger claim. In review, the body's "confirmed" sentence was narrowed to the review probe, which is the one with evidence.
- **Duplicate search:** (`obs-issue-url`) no duplicate found.
  - fullsend#6611, #6769, #8700, #8695, #8922: work-item URL plumbing (FULLSEND_WORK_ITEM_URL). Unrelated.
  - agents#1665 (skill env var reachability test): related in spirit, since it tests that env vars reach skills, but it is a closed PR and not about the prompt. Unrelated.
  - agents#998, #827, #1843, #1167, #686, #1739, fullsend#8699, #7966, #8002: unrelated.
- **Open questions for the reviewer:**
  - Should this cover review as well (retitle to "triage, review: ...")? I kept triage as the subject and mentioned review as found by inspection, plus the one occurrence.
  - Run 1801 was on `experiment/testrepo2`, not on the conformance target. The 27/32 figure covers the conformance target only.
