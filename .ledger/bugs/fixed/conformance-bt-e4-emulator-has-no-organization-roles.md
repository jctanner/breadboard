# Bug: GitHub emulator has no organization roles (BT-E4)

## Summary

Fullsend's behaviour suite gives its human test actors access through
organization roles. The write actor (`TEST_ACTOR_WRITE_PAT`) holds the
predefined all-repository *write* role in the pool org, and the triage actor
(`TEST_ACTOR_TRIAGE_PAT`) holds all-repository *triage*. Grants per
repository are avoided on purpose: every slot repository is deleted and
recreated per lease, which would drop collaborator grants and leave pending
invitations (fullsend #7777; `pkg/behaviourtest/drivers/install/actor_grants.go`,
`hack/setup-new-e2e-org.sh`).

The emulator has no organization roles. `GET /orgs/{org}/organization-roles`
returns 404, and repository permission ignores organization membership
entirely:

- `GET /repos/{o}/{r}/collaborators/{u}/permission`
  (`api/collaborators.py`) answers only for the owner, a direct collaborator
  or an App installation;
- `can_write_contents` (`services/repository_access.py`) does the same.

Fullsend authorizes most dispatch paths with `has_repo_permission`, which
calls that endpoint, so an org member with an all-repository role reads as
having no access.

Found in BT-B4 (`.ledger/plans/fullsend-behaviour-tests-plan.md`).

## Reproduction

1. `GET https://github.local/api/v3/orgs/halfsend/organization-roles` → 404.
2. Add a user to an org with `PUT /orgs/{org}/memberships/{user}`, then ask
   for their permission on any org repository that does not list them as a
   collaborator → 404 (no access).

## Expected

As on GitHub:

- `GET /orgs/{org}/organization-roles` lists the predefined all-repository
  roles (read, triage, write, maintain, admin) with their ids;
- `PUT` and `DELETE /orgs/{org}/organization-roles/users/{username}/{role_id}`
  assign and remove one;
- `GET /orgs/{org}/organization-roles/{role_id}/users` lists who holds it;
- a member's effective permission on every org repository, including ones
  created later, is the highest of their collaborator permission and their
  all-repository role. That applies to the permission endpoint, to content
  writes and to triage-level actions (labels, assignees).

## Actual

The routes do not exist, and org membership confers no repository permission
beyond read access to private repositories.

## Impact

High for BT-B4. About 14 of the ~31 runnable T2 scenarios use the write or
triage actor: owners-auth (6), fix-authorization (2), the
retro/review/triage-prioritize CEL routes (5) and one in dispatch. They
cannot be set up the upstream way. T3 (platform actor and bot authorization)
depends on it too.

## Related Tasks

- `.ledger/plans/fullsend-behaviour-tests-plan.md` (BT-B4, BT-S4)
- Fix belongs in `checkouts/github-emulator`, like BT-E1–E3; then a bb seed
  for the actors (users, PATs, membership, roles) beside `make bt-seed`.

## Resolution

Fixed 2026-11-07 in github-emulator `e330ef0` ("Emulate organization roles");
the emulator's record is `docs/bugs/fixed/organization-roles-are-not-emulated.md`.

- **Organization roles.** The predefined all-repository roles are served
  under `/orgs/{org}/organization-roles` (migration 0017).
- **Effective permission.** A member's permission on every repository of
  the organization, including ones created later, is the highest of their
  collaborator permission and their role. Organization owners have admin.
- **Permission endpoint.** It now answers in GitHub's vocabulary, which is
  what Fullsend's dispatch reads. It used to return `push` and `pull`, which
  Fullsend read as no access.

Deployed with `make host-rebuild-github`: the live database went from 0016
to 0017, and `integrity_check` is ok. A backup was taken to
`/data/github_emulator.pre-0017.db`.

`make bt-seed` now creates the suite's actors
(`deploy/fullsend/seed/seed-behaviour-pool.py`). Their tokens go to the
gitignored `deploy/fullsend/behaviour/.env.actors` (0600), which `run.sh`
exports. On a repository created after seeding:

| Actor | Access | `permission` / `role_name` |
| --- | --- | --- |
| `bt-write-actor` | member with `all_repo_write` | `write` / `write` |
| `bt-triage-actor` | member with `all_repo_triage` | `read` / `triage` |
| `bt-outsider` | not a member | 404 |

A reseed keeps the existing tokens.
