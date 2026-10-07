# Task: Print a clear strategy entrypoint startup banner

## Goal

Make the Fullsend-to-script handoff visible using the user's three-line banner.

## Implementation

Print the banner immediately after shell options, before argument validation
and setup. Static text only. Regression invokes the real entrypoint with no
arguments and checks stdout is exactly the banner before the usage error.

## Acceptance

- [x] Banner added and Bash syntax / component diff check passed.
- [x] Full suite: 790 passed, 1 skipped (112.90 seconds).
- [x] Source 774cf104041575d222305175405eadcb34f17636 pushed; both CI pins published.

## Status

Done. Running batch 2061 uses its existing source pin and will not gain the
banner retroactively.

## Publication

Normal CI branch commit 8e16b4a9233bfb8acdff59e3a6907d8d5ebf86a9;
diagnostic branch commit 6ad05e4488901e36f9537ca3a95ccea732d6b59f.
Both published without creating a pipeline; native main preserved. Component
working tree clean, root/component diff checks passed. No live run of the new
banner was started; real entrypoint regression verifies first-output behavior.
