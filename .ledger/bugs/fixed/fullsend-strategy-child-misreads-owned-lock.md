# Strategy child misreads the CI entrypoint's owned Jira lock

## Reproduction

Pipeline 2033/job 3943 locked RHAIRFE-1, then launched strategy-create.
Claude successfully used Vertex and read Jira, passed the configured gates,
found no cloned STRAT, then asked for confirmation because it interpreted
`strat-creator-processing` as another run's lock. The child returned without
creating an artifact. The entrypoint failed and unlocked its owned key.

## Fix / validation

Fork `24a3babeaaf24526b3108094a2169c326e1952b4` explains the automated user
write authorization and owned-lock context to each child only when the
recorded lock file exactly matches the configured RFE key. Normal gate and
duplicate-strategy checks are retained. 512 unit / 776 full tests passed
(1 skipped), and the change is pushed. End-to-end retry is pending; keep this
bug open until the child proceeds correctly through the real workflow.

## End-to-end resolution

Pipeline 2037/job 3955 completed real create, refine, review and publication
for RHAIRFE-1/RHAISTRAT-1 with the corrected ownership prompt. The RFE lock
was released; the review was attached. The bug is fixed for this POC.
