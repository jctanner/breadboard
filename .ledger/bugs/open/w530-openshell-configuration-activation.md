# Test-host OpenShell effective configuration activation fails

## Status

Open; integration qualification of PR #10 is blocked. No merge approval.

## Reproduction

The dedicated Fedora 44 test host runs the complete stack with a custom .local
subdomain. Fullsend conformance passes Mint, checkout and setup but fails while
activating the sandbox's effective configuration. Public status reports
ConfigurationInvalid and a generic configuration activation error. An independent
sandbox without attached providers reproduces the same failure.

## Evidence and limits

All application deployments are Available. Cluster, public-CA certificate chains
and custom-domain DNS validation pass. The public OpenShell runtime capability
probe passes on this CPU/kernel in both isolated Podman and hardened K3s without
weakening SELinux, seccomp or host-wide controls. This does not identify the
activation failure. The examined failed run produced no behaviour-result or agent-result artifact.

Runtime diagnostic log inspection awaits explicit approval after automatic review
rejected exports due possible credential/session material. Continue with metadata
until that approval arrives. Do not bypass by exporting the same logs through an
alternate API. Real model inference is not qualified.
