# Public CA unreadable in images built under a protected umask

## Reproduction

Build pipeline-agent with umask 0077. The public ConfigMap certificate enters the
build context as mode 0600; COPY preserves that mode. `pipelineagent` cannot read
`NODE_EXTRA_CA_CERTS`, and OpenSSL directory lookup follows a symlink to the same
unreadable file. The system bundle may remain readable, hiding the problem.

## Fix

Set COPY --chmod=0644 only for the public CA in the pipeline, Fullsend sandbox and
supervisor bundle stages. The generated final supervisor public bundle is also
explicitly mode 0644. Private keys are neither copied nor chmodded. Retain the
protected deployment umask. The final agent image built under umask 0077 passes as `pipelineagent`: Python,
Node 24, Claude, OpenCode, public CA readability, and CLI help with the test Relay
setting. Fullsend image builds remain part of the ongoing deployment qualification.
