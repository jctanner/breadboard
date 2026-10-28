# Bug: Pinned-context fetch runs before the combined CA is exported

Pipeline 2098/job 4064 stopped on public GitHub certificate verification in
the new pinned-snapshot bootstrap. The runner inherited its local-only
`GIT_SSL_CAINFO`; `source.sh` builds the correct combined public/local bundle
but runs as a child process. The adapter had exported that bundle only after
the newly added context fetch.

Move the three CA exports before all network bootstrap operations. Do not
disable TLS verification. A model-free shell regression deliberately supplies
the wrong inherited CA, intercepts the first network command, and verifies
all three CA variables already point to the combined bundle.

No sandbox, ticket lock or model call occurred. Artifacts survived the fixed
redactor. Complete capture and separate verification both pass:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2098/20261019T015557.703731Z`.

Related: [single-RFE integration smoke](../../tasks/done/fullsend-claude-workflow-opus-single-smoke.md).
