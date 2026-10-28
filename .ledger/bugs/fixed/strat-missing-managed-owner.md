# Malformed prepared ownership bypasses write guard

PR #85 comment 4381545501, reproduced on b8d67c3. Prepared live input with a
valid run_id and missing, empty or malformed lock_owner reaches effect reads,
intent and writes; context validates run_id only and the guard skips absent
ownership. Normal host preparation supplies an owner, so this is malformed-input
hardening, not evidence of ordinary managed-run bypass.

Expected: reject before any effect read, intent or mutation; require a valid
owner again in direct guards. Preserve standalone human helpers, including the
explicit standalone persistent journal. Prepared input cannot select that mode.

Evidence: /tmp/strat-pr85-three-concerns-red.log.
Task: [approved review fixes](../../tasks/done/strat-pr85-review-b8d67c3.md).

Fixed in a0158d9: validate prepared run and owner identifiers before side effects;
direct guards also fail closed. Explicit standalone persistent context uses a
private process type that prepared JSON cannot select. Valid owned paths,
foreign-owner refusal and standalone controls pass. Full suite: 1,394 pass,
six skips. Evidence:
var/run-data/20261026-strat-pr85-human-gates-publication-ownership/.
