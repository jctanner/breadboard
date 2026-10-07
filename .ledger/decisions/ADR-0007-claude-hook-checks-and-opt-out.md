# ADR-0007: Complete M3 with hook checks, then add an explicit opt-out

## Status

Accepted by user direction on 2026-10-05.

## Decision

Complete M3 using option 2 from the
[conflict analysis](../notes/m3-claude-hook-conflict-analysis.md), with the
review revisions: trusted expected hashes, checks before supported launches,
and an independent outer-runner check before accepting results or publishing.
Keep hooks enabled and require real hook execution and defined tamper tests.
Do not require read-only hook installation to complete M3.

Immediately afterward, add `security.sandbox_hooks.enabled`, default true,
as a separate follow-up. False skips Fullsend's hooks without disabling
host scanning, runtime provisioning, plugins, or OpenShell policy. Keep the
setting outside `entrypoint` and consistent across supported execution paths.

## Limits and consequences

Writable files may change during execution. Checks detect differences present
when checked; they cannot prove continuous integrity, detect every temporary
change, or undo external writes. An in-sandbox helper is not a trusted boundary
against a child with the same write permissions. Immutable installation is a
separate investigation, not a promised property of M3.

The old bootstrap conflict remains useful evidence, but no longer blocks the
chosen implementation path. The revised checks and repository test gates
still need to pass. The hooks switch must not substitute for that evidence.
Reconcile this scoped interpretation with the final upstream ADR before PR.
