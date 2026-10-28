# Breadboard's local Markovd CLI wrapper points at the wrong Go module

Reported and fixed 2026-10-16.

`./bin/markovd-cli help` exited 1 with "cannot find main module". Its local
wrapper ran `go run <breadboard>/cmd/markovd-cli`, but the CLI source belongs to
the separate `checkouts/markovd` repository. The compiled checkout binary's
`help` command already worked; no component source change was needed.

The wrapper now executes `<breadboard>/checkouts/markovd/bin/markovd-cli`,
forwarding all arguments without changing the working directory. This preserves
root `.markovd-cli-config.toml` discovery. If the binary is missing, the wrapper
prints the exact checkout build command and exits 1. Both wrapper and binary
remain ignored local files, consistent with the existing `bin/` policy.

Verification: Bash syntax check; `help`, `--help`, and no-argument usage all
exit 0 and show usage with an unreachable server configured, proving help
does not require a service connection. Absolute-path invocation from another
working directory also succeeds. `git diff --check` passes.
