# S1 scorer output is outside the composition helper's accepted scope

## Summary

Observed 2026-10-14 in the real three-RFE GLM batch on hardened S1
`0e7e752702727076818001d3a29208532b40dbab`. The Workflow writes scorer
results under `/tmp/strat-assess/<KEY>/`, then passes that directory to
`strategy-review --scores-from`. `review_composition.begin` requires its scorer
input to pass `review_scope.safe_path`, which restricts it to the repository.
The documented call therefore fails for every ticket.

## Reproduction and actual result

Markov `markov-run-cf0dfe9a`, job
`script-run-workflow-all-glm-5-3-1014-204524-5924cf`:

```text
python3 .../review_composition.py begin RHAISTRAT-2 \
  --scorer-result /tmp/strat-assess/RHAISTRAT-2/RHAISTRAT-2.result.md
Review composition: Path is outside the assigned input scope.
EXIT:2
```

All three review agents encountered this mismatch. GLM diagnosed the helpers
and copied the scorer result byte for byte to `tmp/strat-assess/<KEY>/` inside
the repository, verified equal SHA-256 values, and retried begin successfully.
No tracked source change was observed in the live checkout.

| Strategy | First rejected call, UTC | Successful begin, UTC | Elapsed diagnostic interval |
| --- | --- | --- | --- |
| RHAISTRAT-2 | 21:35:11 | 21:44:37 | 9m26s |
| RHAISTRAT-1 | 21:39:36 | 21:53:15 | 13m39s |
| RHAISTRAT-3 | 22:13:09 | 22:16:11 | 3m02s |

These intervals overlap and must not be added as job wall time. They include
model reasoning, reads and diagnostic commands, not a single slow helper call.

## Expected behavior and impact

The Workflow and helper must agree on the scorer artifact location. A normal
review should not need an agent to debug source, discover a path restriction,
and stage an equivalent input. The current configuration adds time and tokens
and can fail on a model that does not find this workaround. Focused composition
fixtures used in-repository scorer inputs and missed this integration mismatch.

## Proposed repair

Use a per-ticket scorer directory inside the prepared repository, and pass the
same location through scoring and review. Keep the composition path restriction.
Add an integration check using the Workflow's actual path contract.

Open. No live source, configuration or progress was changed during diagnosis;
the user requested inspection without stopping the job. Preserve the current
run's evidence and pin before any later repair or retest.

[Live diagnosis](../../notes/s1-hardening-three-rfe-glm-live-duration.md).
[Batch task](../../tasks/done/s1-hardening-three-rfe-glm-opus.md).

## Mixed Opus recurrence, 2026-10-16

At f5691f7, all nine review callers in markov-run-5d3327ed encountered this
error (twelve rejected begin calls total). All staged score results under the
repository and retried successfully. The operational pass does not dismiss
this defect. [PR triage](../../notes/strat-creator-pr85-review-triage.md).

## Fixed in source, 2026-10-16

strat-creator commit f941955 on feat/s1-workflow-hardening. Scorer and interactive review directories now live under repository tmp/strat-assess; matching Workflow path checks and the actual native composition control pass without staging an outside-repository file.
No paid model batch was rerun for this remediation; historical evidence is unchanged.
