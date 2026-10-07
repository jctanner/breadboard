# M3 follow-up: Add an explicit Fullsend sandbox hooks switch

## Goal

After [M3](../done/fullsend-entrypoint-feature.md), add
`security.sandbox_hooks.enabled` in the Fullsend feature branch. This belongs
under the existing security configuration, not in `entrypoint`.
See [ADR-0007](../../decisions/ADR-0007-claude-hook-checks-and-opt-out.md).

```yaml
entrypoint:
  command: [scripts/strategy-entrypoint.sh]
security:
  sandbox_hooks:
    enabled: false
```

## Acceptance criteria

- [ ] Omitted or true preserves existing per-hook defaults and switches.
- [ ] False skips Fullsend hook scripts, settings, hook-only environment,
  hook activation arguments, and checks for deliberately omitted hooks.
  Retain any independent launcher/entrypoint integrity checks.
- [ ] Keep runtime provisioning, credentials, models, plugins, host scanning,
  and OpenShell policy working. Do not disable project/plugin hooks.
- [ ] Apply the switch consistently to existing agent-led runtimes and the
  supported Claude entrypoint path; this does not add Codex/Pi entrypoint support.
- [ ] Define and test inheritance using existing security composition rules.
  `security.enabled: false` remains the broader override; nested true cannot
  re-enable hooks beneath it. Reject invalid flag types.
- [ ] Test both defaults and explicit opt-out, including a real Claude
  entrypoint with no Fullsend hook uploads or activation. Confirm the
  hooks-enabled M3 checks still pass and unrelated scanning remains enabled.
- [ ] Document the setting and report effective hook status in run output.
  Meet Fullsend's relevant functional test and lint requirements; coverage
  thresholds are deferred to pre-PR preparation under
  [ADR-0008](../../decisions/ADR-0008-defer-poc-coverage-gate.md).

## Status

Pending and ready to start; M3 is accepted for POC progression. The flag is proposed and does not
exist yet. It is not a substitute for completing M3 with hooks enabled.
The strategy harness can explicitly opt out when this follow-up is complete;
record that choice and its effect when integrating the POC.
