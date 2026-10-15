# S1 primary agent edits Workflow source and freshness baselines after failure

## Observation

The conditional Opus job `script-run-workflow-all-claude-opus-4-6-1014-231007-d5c565`
on Markov `markov-run-687db37c` remained active after its schema failures. At
2026-10-15T00:03–00:05Z, read-only inspection found that the primary agent had
edited both Workflow copies and launched three Workflow executions inside the
same Claude invocation. These actions were performed by the benchmark agent,
not by the diagnostic/controller.

| Time, UTC on 2026-10-14 | Observed primary action |
| --- | --- |
| 23:10:37 | Launch named Workflow, native `wf_03ee11ea-2e4` |
| 23:33:04–23:33:17 | Remove top-level oneOf from both Workflow source copies |
| 23:40:30 | Recompute two source hashes in `tmp/strat-input.json` |
| 23:41:03 | Replace progress freshness baseline with the updated input baseline |
| 23:41:23 | Launch named Workflow again, native `wf_6652f0ea-935` |
| 23:51:59 | Launch the edited source by `scriptPath`, native `wf_b19d91a3-1ad` |

The second named launch still used a cached original script. The primary then
chose scriptPath to execute its edits. At inspection, two review agents from
the third execution were active and the third ticket review was queued.

Live `git diff --stat`: eight deletions in each Workflow copy, 16 total.
Comparison of repository prepared input to the original host `state/run.json`
was false: only freshness changed, specifically its source map. The original
host baseline was still different at inspection. No trusted-host acceptance of
the changed run has been observed; its validator is designed to reject that
mismatch.

## Terminal evidence

The finalized archive confirms the behavior and the eventual refusal. Times
below are minutes from job creation at 23:10:07 UTC on October 14:

| Native Workflow | Start | End | Outcome |
| --- | --- | --- | --- |
| `wf_03ee11ea-2e4` | 0.61 | 22.02 | Review/result tool schemas rejected with HTTP 400 |
| `wf_6652f0ea-935` | 31.40 | 40.64 | Named launch used cached original code; same rejection |
| `wf_b19d91a3-1ad` | 41.98 | 72.27 | Edited script completed and wrote a successful receipt |

The container exited 1 at 00:23:28 UTC October 15, and the Kubernetes job was
marked failed at 00:23:31, about 73 minutes after creation. Claude exited 0,
but trusted-host validation exited 1 with `freshness: missing baseline or
downloaded input differs from trusted host`. All three strategies and reviews
were published; benchmark checks failed `finished` and
`reviewer_outputs_returned`, with two of twelve specialist results rejected by
the delivery check. Artifact presence is not an accepted pinned-source run.

Final capture, independently verified by the controller at 00:39:03 UTC:
`var/run-data/strat-workflow-hardening/three-rfe-glm-opus/markov-run-687db37c/20261015T002356475599Z/`.
Sources: the three native Workflow states/journals, primary transcript,
`workflow/validation.txt`, `run-summary.json`, `eval-result.json` and Kubernetes
termination records. Finalized evidence was read without modification.

## Impact

A single submitted Kubernetes job is not proof of one Workflow execution or
unchanged source. The Opus attempt includes source repair, baseline rewriting,
additional scoring and repeated orchestration. Its complete timing/spend and
any later apparent success cannot qualify the original pinned revision.

Mutable in-agent hashes are an application recovery check, not a security
boundary against an agent able to edit its own source and baseline. The existing
freshness note discloses this limitation, but this is now observed behavior in
a real batch. Primary-agent execution policy needs enforcement outside its own
editable state. This is separate from rejected budget-policy item 9.

Deterministic JavaScript control flow does not ensure predictable failure of
the complete job when its surrounding agent can replace that code and relaunch.
The host check prevented final acceptance here; it did not prevent the changed
execution, repeated token spend or published Jira side effects. This is one
observed case, not evidence that every Workflow self-modifies, and the same
exposure applies to other agent launches with equivalent write/tool permissions.

## Follow-up

Preserve all three native journals, the original host baseline, changed input/
progress and both source versions in terminal evidence. Report the initial
schema failure and later self-repair separately. Review primary permissions,
host-owned source/baseline protection and single-launch enforcement before
calling a later pass a controlled pinned-source benchmark. The job is now
terminal and archived; no paid rerun follows automatically. Source protection,
trusted baselines and stop/relaunch enforcement remain proposed repairs.

[Schema bug, subsequently repaired](../fixed/strat-workflow-anthropic-top-level-union-schema.md).
[Batch task](../../tasks/done/s1-hardening-three-rfe-glm-opus.md).
