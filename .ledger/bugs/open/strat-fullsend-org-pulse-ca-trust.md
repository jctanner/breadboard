# Fullsend host cannot verify the Org Pulse TLS certificate chain

## Evidence

Real GitLab smoke pipeline 2974269929, Opus job 17366396650, source b3c10ec.
At 2026-10-22 00:18:07Z the host exporter prepares 1,031 aggregate features
in 42 batches. Every batch fails with CERTIFICATE_VERIFY_FAILED:
"self-signed certificate in certificate chain". Zero created/updated/unchanged.

At the failing revision, the export used normal TLS verification and expected the CI
system trust store or SSL_CERT_FILE to contain the appropriate CA. The error
proves the presented chain is untrusted in this process; it does not establish
which missing CA or server-side chain correction is required. The initial
recommendation to retain verification was superseded by the owner's explicit
temporary exception below.

## Why this appears in the new integration

The request runs in Fullsend's host post-script inside the outer GitLab job
container, after agent sandbox cleanup. It does not run in the OpenShell
agent sandbox. The trace starts sandbox cleanup at 00:16:56Z, starts the host
post-script at 00:17:42Z and reports Org Pulse TLS failures at 00:18:07Z.

The legacy consumer's ci-scripts/push-to-org-pulse.py explicitly sets
ctx.check_hostname=False and ctx.verify_mode=ssl.CERT_NONE (lines 104-106).
The new shared exporter uses ssl.create_default_context() without disabling
either check. Legacy success therefore did not prove a valid trusted chain:
it bypassed certificate verification. The current failure exposes that trust
gap; the exact missing CA or service chain still needs inspection.

## Temporary exception authorized

The user explicitly requested disabling verification for now after discussing
the tradeoff. The earlier recommendation against bypassing it no longer blocks
this scoped change. Restore the legacy context only in the Org Pulse exporter:
check_hostname=False then CERT_NONE. Document the exception and leave permanent
corporate CA trust as follow-up. A local HTTPS test with an untrusted certificate
reproduces the old failure and passes after the change. No live export/model
retry is included in this authorization.

[Implementation task](../../tasks/done/strat-org-pulse-temporary-tls-bypass.md):
signed-off 85e8307 pushed/API verified. Eight local exporter tests, 1,190 full
tests/six skips and lint pass. The certificate exception is implemented;
permanent corporate CA trust remains unresolved. No live export was retried.

### Scoped delivery recovery verified: 2026-10-22

The user subsequently authorized retrying saved results. Real CI export-only
pipeline 2976666017/job 17383298312 runs the 85e8307 exporter against one sealed
saved strategy, not the old whole aggregate. Before GET is 404; one POST
creates one feature without validation errors; after GET is 200. The saved
run identity, numeric 8/8 approval and feasibility revise dissent match.
Delivery is recovered under the user-approved TLS exception. No model/Jira
write or repeated POST. Keep permanent CA trust as a future issue.
[Evidence](../../tasks/blocked/strat-downstream-publication-recovery.md).

## Impact and follow-up

Strategy generation, live Jira publication and data-repository publication
pass. Org Pulse export is non-blocking, so a green job alone does not prove
ingestion; the later export-only recovery above independently verified delivery.
Permanent CA trust remains a future task. The owner reaffirmed that the existing
certificate/hostname bypass is accepted for now and is not a prerequisite for
the next smoke test. Saved pipeline outputs can be reused without another model
run. No new retry was performed during this clarification.

Evidence: var/run-data/20261021-real-gitlab-fresh-single-opus46-postreview/
job-17366396650-fullsend-single-rfe/trace.log.
