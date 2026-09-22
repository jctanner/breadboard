# GitHub emulator #12: organization PR metadata uses creator namespace

## Status

Fixed in the local component checkout on 2026-09-22; not deployed or committed.

## Cause

`checkouts/github-emulator/src/app/api/pulls.py` derived repository namespaces
from `Repository.owner`, which records the creator for organization-owned
repositories. Serialization, create-time branch normalization, and read-time
resolved labels all used that login instead of `Repository.organization`.

## Change

Added shared owner/namespace helpers within the PR API module, following the
organization-first behavior of repository serialization. Applied them to PR
URLs, labels, branch normalization, and serialized head/base owner objects.
Eager-load both base and head repository organizations in `_pr_query` so the
serializer remains compatible with its `raiseload` policy. Resolved head labels
use the head repository's namespace when a separate head repository exists.
The PR author's identity remains the creating user.

## Validation

`tests/test_pulls_api.py`: **20 passed** (existing deprecation warnings).
New parameterized coverage exercises organization-owned PR create/get/list/
update, plain and namespace-qualified branch inputs, SHA resolution, imported
qualified refs, URLs, labels, and internal owner serialization. Existing
user-owned PR cases also pass. `git diff --check` passed in both repositories.

Existing unrelated runner changes in the component checkout were preserved.
No live issues, PRs, or deployment resources were modified.
