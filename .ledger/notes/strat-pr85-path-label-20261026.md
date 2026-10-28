# PR #85: publication paths, Jira labels and paragraph wrapping

Owner approved exactly three new findings from review 5658796463 on a0158d9.
Repeated Org Pulse TLS, general Jira authority, remote allowlist, pending-reviewer
and process comments retain their prior disposition. No model, live Jira,
deployment, cutover, public reply or merge is part of this work.

## Implementation

- **4382320349, directory symlinks.** Resolve the chosen results checkout root,
  then reject symlinks and escaping paths below that root before reading saved
  publication state or any planned copy. Validate every destination against
  the run directory before writing the publication journal; recheck its path
  immediately before the atomic replacement. Source artifact roots also reject
  symlinks. Preserve the intentional current symlink, hash checks, genuine
  conflict refusal and interrupted-copy recovery. This changes identified-run
  publication, the path used by the Workflow post-script. It does not claim
  protection against hostile concurrent filesystem replacement or redesign the
  accepted sandbox/Jira authority model.
- **4382320355, malformed labels.** One validator requires a list of strings.
  Missing, null, string, object and mixed-type values stop with a controlled
  error before effect intent, publication or freshness capture. STRAT gates,
  RFE ownership and RFE/STRAT freshness use the same rule. Empty lists remain
  valid; the existing current-run needs-attention recovery exception is intact.
- **4382320374, paragraph wrap.** Reflow the CLAUDE.md freshness paragraph to
  match its surrounding margin; retain the exact instructions.

## Evidence

Pre-fix focused reproduction: **19 failed, one control passed** (16.98s).
Tests clone actual local Git repositories containing tracked directory symlinks
at four destination depths, both existing and dangling targets. Inspection of
the retained red workspaces found four outside strategy files, recording their
sizes and hashes in strat-pr85-path-label-red-escaped-files.json. They are fake
test artifacts inside /tmp. The new regression verifies no outside file change,
source cleanup or publication journal on refusal. A source-directory symlink
also fails before reading/copying it.

Malformed-response tests wrap real local Jira helper calls before and after
target binding. They assert no mutation or pending intent, unchanged progress,
and refusal of both direct human snapshot and create provenance capture.

Focused suite: **148 passed** in 122.48 seconds, including existing verdict
recovery, lost acknowledgement, atomic-copy process-death and genuine-conflict
controls. Final full offline suite: **1,413 passed, six optional skips** in
545.67 seconds, with the model-calling smoke disabled. Ruff, type descriptor
validation and git diff --check pass. A word-for-word comparison confirmed the
CLAUDE.md edit changes only wrapping.

Signed-off commit: 0d608244f57f831e66c30c8ba4b2890ec5f2cb56. Six source files
and the staged patch passed the local-credential/pattern scan before commit
(zero findings). Component worktree is clean. No model calls or live Jira writes.

Evidence destination:
var/run-data/20261026-strat-pr85-path-label/.

Nineteen files sealed before push with zero credential findings, manifest and
byte readback verified. Pushed 0d60824 without force; Git and the GitHub API
confirm the exact head. PR #85 remains ready/non-draft and conflict-free;
DCO passed, other new-head CI checks pending at publication time. Separate
verified publication receipt:
var/run-data/20261026-strat-pr85-path-label-publication/.
