# GitLab UI trace and artifact downloads ignore browser session

## Summary

Job detail and admin CI Lab linked directly to `/api/v4/projects/.../jobs/...`
trace/artifact endpoints. UI login cookies are scoped to `/ui`, and API
identity requires explicit API credentials. Private project downloads therefore
returned Project Not Found even for a logged-in browser.

## Fix

Changed both frontend surfaces to `/ui/{project}/-/jobs/{id}/trace` and the
existing `/ui/{project}/-/artifacts/{id}/download` route. Added plain-text trace
responses with session identity, Reporter access checks for private projects,
and job/project matching. Nested project routing supports the trace endpoint.
API authentication remains unchanged.

## Evidence

2026-10-06: rebuilt and deployed with `make host-rebuild-gitlab`.
Focused private-project UI test passed; anonymous downloads return 404.
Live nested project 7/job 3993: trace HTTP 200 (3,417,626 bytes), artifact
HTTP 200 (742,464 bytes); anonymous requests to both return 404.
Component and root `git diff --check` passed. Existing checkout documentation
changes were preserved. No pipeline rerun or data reset.
