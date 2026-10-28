# Bug: New Fullsend Workflow diagnostic needs OpenShell upload/name compatibility

## Findings

Model-free GitLab pipeline 2092/job 4056 registered all agents and both
credential providers, then rejected a 23-character sandbox name. The pinned
OpenShell release allows at most 19 characters. No Claude invocation.

Pipeline 2093/job 4057 created the shortened-name sandbox, then Python found
a directory at the uploaded script's requested filename. OpenShell's upload
path behavior in a Git checkout is already handled by Fullsend's UploadFile
adapter; the standalone diagnostic initially omitted that compatibility.

## Repair

Use `wf-pre-$CI_JOB_ID` and upload regular files into the existing workspace
directory, invoking their original basenames. An additional diagnostic caught
the external observer creating the workspace as root before SSH upload;
the observer now assigns the workspace to its intended sandbox owner.
All three failed captures are preserved and verified.

## Validation

Pipeline 2095/job 4059 passed the real sandbox probe and artifact/cleanup
checks. All three exit codes are zero. No inference or Jira mutation.

Related [task](../../tasks/done/fullsend-claude-workflow-relay-copy.md).
