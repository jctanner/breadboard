# Bug: GitLab runner leaves finished job pods in Error

## Summary

After a Kubernetes-executor job finishes, its pod in the `gitlab-runner`
namespace stays behind with both containers terminated by SIGKILL (exit
137) instead of being deleted.

## Evidence

- `runner-emulator--project-7-concurrent-0-sp053hcn`: job 4037
  (strat-batch, pipeline 2076, agent-led POC). The job **succeeded**;
  `build` and `helper` exited 137 afterwards; created 2026-10-07T21:22:28Z.
- `runner-xmvfkupbt-project-7-concurrent-0-iidmyxc6`: job 3924
  (`build-fullsend-feature`, script-led POC), same symptom, about 31 hours
  older.

## Expected

The runner deletes the job pod after uploading artifacts.

## Actual

The pod object remains in `Error`. Job status and artifacts in GitLab are
unaffected.

## Impact

Low. The pods are clutter, and a reader can mistake them for failed jobs.
Cleanup checks for the agent-led POC must treat job pods separately from
the job's own gateway, container and network cleanup, which is verified
inside the job (`cleanup_exit=0`).

## Notes

Not investigated. Both pods were left in place as evidence. Likely in the
runner's pod-deletion path, or a grace-period or finalizer interaction in
K3s.

## Related Tasks

- tasks/done/agent-led-strategy-single-ci.md

## Update (2026-10-07, later)

Job 4037's pod was gone by the time pipeline 2079 ran, about 1h50m
later. The dashboard job pod for pipeline 2079 was terminating normally.
Only job 3924's pod (33 hours old) remains, so 4037's was a delayed cleanup
rather than a permanent leak. Impact is lower than first recorded; a
reaper delay or a missed deletion for one older pod is still unexplained.
