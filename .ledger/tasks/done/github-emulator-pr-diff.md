# Task: Serve aggregate pull-request diffs in the GitHub emulator

## Goal

Support `/ui/{owner}/{repo}/pulls/{number}.diff`, the GitHub-style
`/{owner}/{repo}/pull/{number}.diff` advertised by PR JSON, and the PR API's
`Accept: application/vnd.github.diff` representation.

## Acceptance criteria

- [x] Return raw Git unified diffs with plain-text content type.
- [x] Reuse merge-base comparison and preserve Git diff metadata.
- [x] Respect repository visibility and scoped token permissions on every route.
- [x] Verify empty diffs, missing PRs/refs, and normal JSON responses.
- [x] Run focused regression tests and `git diff --check`.
- [x] Build/deploy using `make host-rebuild-github` and verify PR #2 live.

## Status

Done, 2026-10-14. Implementation lives in the ignored, separate
`checkouts/github-emulator` repository; project work evidence stays here.

## Findings

The UI `.diff` path returns the SPA shell. PR #2's changed-files API already
contains 43 patches (111,137 bytes). The PR API ignores the diff Accept header.
Raw output can share the existing `git diff base...head` invocation without
reconstructing patches from parsed file records.

## Implementation and validation

- Extracted a shared raw comparison helper in `src/app/git/bare_repo.py`;
  the existing changed-files helper parses those same bytes. Git failures
  remain distinguishable from a successful empty diff.
- Added direct web/UI download routes before the SPA mount. Their auth
  dependency invokes the existing gateway with the canonical PR API path,
  preserving browser sessions, private-repository visibility, Actions job
  permissions, and installation-token repository selections/permissions.
- PR GET accepts `application/vnd.github.diff` and
  `application/vnd.github.v3.diff`; normal JSON responses retain their response
  model. Responses include `Vary: Accept`.
- Merge saves current pre-merge base/head SHAs for diff downloads after merge
  and head-branch deletion. Missing Git data returns 404 rather than an empty
  success response.
- Focused regression command:
  `.venv/bin/pytest tests/test_pull_diff.py tests/test_pulls_api.py tests/test_frontend_app.py tests/test_raw_content.py tests/test_installation_token_permissions.py tests/actions/test_job_permissions.py -q`
  from `checkouts/github-emulator`: **80 passed**, with existing deprecation
  warnings. Initial sandboxed run stalled and was interrupted; unsandboxed
  reruns completed successfully.
- Tests compare downloads against real Git output, including merge-base/net
  changes, renames, deletions, executable modes, binary files, missing final
  newlines, HEAD responses, empty diffs, missing refs/repos/PRs, private access,
  browser sessions, and scoped job/installation tokens.
- `git diff --check` passed in both repositories.

## Deployment evidence

- `make host-rebuild-github` completed successfully; deployment rolled out.
  Pod `github-emulator-7b8c58667f-w92l4` is Running/Ready with image ID
  `sha256:15b67c60e175fa9b910b0041e3cacb35c2815c153e4dc6c94584478765d4dfeb`.
- Live `https://github.local/ui/opendatahub-io/strat-creator/pulls/2.diff`,
  the advertised GitHub-style URL, and both API diff Accept variants return
  HTTP 200 and `text/plain; charset=utf-8`. All four responses are byte-identical:
  111,179 bytes, SHA-256
  `04c5610353cf9515b67bb8096ab956f4a15d2f6a2af8d5985a6dc19b21389941`.
- The aggregate contains 43 file sections, matching every changed-files API
  patch (apart from separator newlines). Default API JSON still reports
  43 changed files, 1,752 additions and 78 deletions. A missing PR diff
  returns HTTP 404 rather than the frontend shell.
- No commit or push performed; unrelated Breadboard working changes preserved.
