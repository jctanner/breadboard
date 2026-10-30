<!-- Draft for review. Not filed. -->
# dispatch: every issues.edited event re-runs triage, not only title or body edits

**Repository:** fullsend-ai/fullsend
**Parent:** none

---

### What happens

The dispatch routes every `issues` `edited` event to triage. It does not check which field the edit changed.

- `.github/workflows/reusable-dispatch.yml` lines 359-362: when `EVENT_ACTION` is `edited`, `STAGE="triage"` is set after only the actor-authorization check. The event's `changes` object is never read.
- `internal/harnessdispatch/input/ghaevent.go` lines 147-148 map `edited` to `TransitionEdited` and record nothing about which fields changed.
- `internal/cli/dispatch_route.go` lines 83-94 (`triageRouteAccepts`) accept `TransitionEdited` unconditionally for a work item.
- By inspection, the default CEL trigger in fullsend-ai/agents `harness/triage.yaml` (lines 37-40) matches `transition.kind in ["opened", "edited"]`. Because the normalized event does not record which fields changed, a trigger cannot tell a title or body edit from any other edit.

The shim the scaffold installs subscribes to `issues: types: [opened, edited, labeled]` (`internal/scaffold/fullsend-repo/templates/shim-per-repo.yaml` line 21, and the repository's own `.github/workflows/fullsend.yaml` line 23). As a result, each `edited` delivery from an authorized actor starts a full triage run, and triage begins by removing prior triage labels (ADR 0002, "When a triage run starts").

### What should happen

ADR 0002 (`docs/ADRs/0002-initial-fullsend-design.md`, status Accepted, line 128) lists the triage triggers as:

> 2. **Issue `title` or `body` edited** (`issues` **`edited`** when `title` or `body` changed).

An `edited` event re-triggers triage only when its `changes` include `title` or `body`. Any other edit does not start a triage run.

### How to reproduce

1. In a repository onboarded to Fullsend, deliver an `issues` `edited` event from an authorized actor whose `changes` object contains neither `title` nor `body`.
2. The route step selects `STAGE=triage` and a triage run starts.

By inspection of the code paths above, this is a code-level reproduction. It was not separately observed for an edit that changed neither field.

### Context

Found while running Fullsend against a local GitHub API emulator.

---

## Draft notes (not part of the issue)

- **Local patch:** none: report-only
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30); agents trigger cited at fullsend-ai/agents@8f819a9.
- **Evidence:**
  - The observation itself: `.ledger/tasks/pending/open-items-after-runner-consolidation.md` line 40 (one line, no run number).
  - Everything else is from my own code reading at the SHAs above: the ADR quote and status, the bash route, `ghaevent.go`, `triageRouteAccepts`, the shim `types`, and the agents CEL trigger.
  - I searched `changes` in `reusable-dispatch.yml`, `fullsend.yaml`, `internal/harnessdispatch`, `internal/normevent` and `dispatch_route.go`. Upstream does not filter on `changes` anywhere on these paths, so the defect is present.
- **Duplicate search:** (`obs-edited`) no duplicate.
  - fullsend#1688 (is_authorized on dispatch paths), #5244 (triage role for observation stages), #279 (initial triage agent), agents#686: unrelated. They touch the same routing block but not the `changes` question.
  - The query "retriage on edit ADR 0002" returned no hits.
- **Open questions for the reviewer:**
  - The ledger gives no concrete run or edit type. Do we have an example to cite (for example a label-free metadata edit, or an edit made by a bot)? If not, the reproduction stays code-level, as written.
  - "Every edit" is not quite "every": the bash path skips actors that fail `is_event_actor_authorized`, and the CEL trigger requires `actor.kind == "human"`. I described this as "from an authorized actor".
  - The ADR's other edits besides title and body: GitHub's `issues.edited` `changes` can carry only `title` and `body`. Label, assignee and milestone changes have their own actions. If the reviewer confirms that, the practical scope is narrower than "any edit". The visible remaining cases would be edits where `changes` is empty, or where a field is rewritten to the same value. I could not confirm this from upstream code, so the body does not claim it. Consider whether the issue is still worth filing in that light.
