# OpenShell blocks Jira attachment verification after an upload

## Evidence: 2026-10-21

Real GitLab live canary pipeline 2972360596/job 17351822419, merged main
38efbce and strategy source 080700e, created/refined RHAISTRAT-3027 from
RHAIRFE-3739. Review scores are 8/8, with testability dissent preserved.
The publisher posted its comment and uploaded the review, then failed while
reading the uploaded bytes to reconcile the attachment side effect.

At 14:38:20Z the reviewer transcript reports `Tunnel connection failed:
403 Forbidden` in `jira_utils.download_attachment`, called by the readback
inside `add_attachment`. The OpenShell sandbox log explicitly states:

```text
endpoint api.media.atlassian.com:443 is not allowed by any policy
```

The versioned policy allows only redhat.atlassian.net for Python Jira work.
The attachment's URL on that host redirects to api.media.atlassian.com.
A separate host-side GET verified HTTP 303 followed by HTTP 200 and downloaded
the exact bytes of the retained review. Jira credentials were supplied only
to redhat.atlassian.net, not the media redirect. Attachment SHA256:
8980ce1906e611bc109cc032aeeeadce719a6e99f84d13bb1e8b53ff500f2aee.

## Impact and fix direction

The upload committed, but its side-effect record remains pending. The
publisher stops before the numeric-verdict label. Permit the specific
required media endpoint for the Python Jira client, or provide a verified
same-host download path. Preserve strict host/port/binary restrictions and
ensure redirect handling does not forward Jira credentials to other hosts.
Do not bypass attachment reconciliation or repeat the committed upload.

The dry-run smoke did not exercise this live attachment readback. The reused
results/Analyst token passed startup; this failure is in Jira sandbox egress.
At diagnosis, no code fix or further model run had been made.

Evidence archive: var/run-data/20261021-real-gitlab-strat-single-opus46-live/,
including native ZIP/transcripts/OpenShell logs, failure recovery files,
Jira snapshots, the downloaded review and verification.json.
[Execution task](../../tasks/done/real-gitlab-strategy-single-live-canary.md).

## Resolution: 2026-10-21

Signed-off commit 02dd13b in strat-creator PR #85 permits only the additional
api.media.atlassian.com:443 endpoint under the existing Python-only Jira
policy. Attachment downloads follow bounded redirects, verify TLS, reject
HTTPS downgrades and send Jira credentials only to the exact Jira origin.
Reconciliation still compares exact uploaded bytes before completing an
uncertain upload; it does not blindly repeat the mutation.

Local HTTP redirect tests cover same-origin authentication, cross-origin
credential stripping, exact bytes, unsafe URLs and bounded redirects. The
repaired downloader also fetched the existing canary attachment read-only
and matched its archived SHA256. Full suite: 1,158 passed, six optional skips;
lint/type checks pass. The policy still needs qualification in a new real
OpenShell live run; no additional inference or Jira write was performed.
