# Task: Register branches created by repository APIs

## Status

Done.

## Confirmed before changes

The user create route records the SHA from bare_repo.create_initial_commit in a
Branch row. The org route delegates to repo_service.create_repo, whose separate
initial-commit implementation writes Git but never adds a Branch row.
Live experiment/branch-probe: ls-remote found main, branches returned [], branch
lookup returned 404, exact Git ref returned 200, matching-refs returned 404.
Probe deleted with 204. Seeded token read from pod environment, never logged.

## Scope

Share initial commit/branch registration between user and org creation. Audit
forks, contents writes, templates, imports, transports, GraphQL and Git Data APIs.
Add matching-refs and tests for user/org default branches plus discovered gaps.
Preserve unrelated pre-existing diff-download edits.

## Implementation and audit

- User and org creation call repo_service.initialize_repository, which invokes
  the canonical bare Git initial-commit writer and records its SHA in Branch.
  The older git_service initial-commit implementation delegates to that writer.
- branch_service records new or existing branch heads without replacing protection.
  Forks register heads read from the actual clone (including packed refs), and
  contents writes register/update the branch after update-ref.
- Added matching-refs with literal prefix matching over actual Git refs.
- Imports and HTTP/SSH pushes already reconcile disk branches. Git ref mutations
  and PR merges/auto-merges already register Branch records. Git commit-object
  creation creates no branch ref, so no Branch record is appropriate there.
- GraphQL repository creation only initializes an empty bare repo. No template
  generation endpoint exists; is_template is metadata on normal repo creation.
- Six regression tests pass outside the sandbox (4 user/org/default-branch cases,
  a multi-branch fork, and first/subsequent contents commits). Tests compare REST
  SHAs to git rev-parse and assert all four requested branch/ref endpoints.
- Python compile and diff checks pass. Full suite passed: 757 tests in 296.52s (including all six new regression tests).

Deployment completed via make host-rebuild-github. First post-rollout probe
refused to create anything while the API briefly returned 502 during startup.

## Live verification after deployment

experiment/branch-probe created with auto_init=true. Git ls-remote advertised
main at 184c9d317be6d29102435a7fe747ed66325cebfd. All four requested endpoints
returned 200 and that same SHA: branches, branches/main, git/ref/heads/main,
and git/matching-refs/heads. Script asserted agreement and deleted the probe
with HTTP 204 in its finally block. Token was read from the pod environment;
no token value appeared in code, arguments or output. No existing repositories
were backfilled or otherwise altered by the probe.

Validation: 757/757 full-suite tests pass; Python compile checks, component and
Breadboard git diff --check pass. Changes remain local/uncommitted; unrelated
pre-existing diff-download work is preserved.
