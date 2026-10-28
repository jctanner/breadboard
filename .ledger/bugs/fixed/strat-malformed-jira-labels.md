# Malformed Jira label responses are not validated

PR #85 comment 4382320355, reproduced on a0158d9 at real helper boundaries
around the local Jira emulator. Replace the requested STRAT labels field with
missing, null, a string, a mixed-type list or an object. Missing/string/object
values can become an empty gate set; null and mixed lists can produce incidental
TypeErrors. Both mutation checks and snapshot capture need a controlled refusal.

Expected: require a present list of strings before gate/ownership checks or
freshness capture. Stop before a pending intent or Jira mutation and preserve
progress. Normal Jira lists, including empty lists, remain valid.

Evidence: /tmp/strat-pr85-path-label-red.log.
Task: [review fixes](../../tasks/done/strat-pr85-review-a0158d9.md).

Fixed in 0d60824. The shared list-of-strings validator protects STRAT gates,
RFE ownership and RFE/STRAT freshness. Ten malformed-response cases before
and after binding preserve remote state/progress and refuse snapshot capture.
Normal empty/ordinary labels and own-verdict recovery remain valid. Full
offline suite: 1,413 pass, six skips. Evidence:
var/run-data/20261026-strat-pr85-path-label/.
