# Follow-up: Investigate immutable Fullsend hook installation

## Goal

Find a supported way to install hooks and their launcher before making them
non-writable by Claude. This is separate from M3's checks at launch and
completion and does not gate the strategy POC.

## Acceptance criteria

- [ ] Evaluate files baked into a pinned image, a separate bootstrap user,
  or a documented OpenShell file-injection mechanism before policy enforcement.
- [ ] Cover hook scripts, generated settings, launcher, and relevant environment;
  check writable parent directories and the agent's ability to change permissions.
- [ ] Prove attempted modification during a live Claude run is refused.
- [ ] Record version coupling and maintenance implications; rerun M2 checks
  for any replacement OpenShell version. Do not assume image packaging is
  unsuitable upstream without reviewing it with maintainers.

## Status

Pending investigation. See [ADR-0007](../../decisions/ADR-0007-claude-hook-checks-and-opt-out.md).
