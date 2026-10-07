# Bug: Jira issue component ID references are silently ignored

## Evidence

During M5, POST `/rest/api/3/issue` with
`components: [{"id": "1"}]` created `RHAIRFE-1` with an empty component list,
although GET `/rest/api/3/project/RHAIRFE/components` returned component ID 1
named `CLI`. `services/issue_service.py` processes component `name` values and
skips entries that supply only `id` (create and replacement update paths).

## Expected

A reference to an existing project component should attach that component or
return an explicit validation error; it should not silently disappear.

## Workaround and scope

M5's fixture uses `components: [{"name": "CLI"}]`, matching the original
seed fixture, and verifies the returned field. The component checkout is
unchanged. This does not block M5/M6 with that fixture representation.

Related: [M5 Jira preparation](../../tasks/done/fullsend-strategy-seed-rfe.md).
