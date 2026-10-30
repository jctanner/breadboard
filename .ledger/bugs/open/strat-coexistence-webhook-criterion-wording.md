# Generated coexistence criterion overstates webhook isolation

## Observed output

Scheduled job 17591617217 published RHAISTRAT-2636 at data repository commit
b78befbc4f366fb30ace9bd46ae5c00075ed3651. Its strategy, lines 86 and 173,
says no MutatingWebhookConfiguration or ValidatingWebhookConfiguration from
any component should match workspaces.kubeflow.org. The same technical
approach lists Workspace-specific validating webhooks and expects each
generation's webhooks to target its own kind.

As written, the universal prohibition also forbids the Workspace validating
webhooks that the document describes. The intended criterion should prohibit
cross-generation matching, while allowing each generation's own webhooks.
Conversion-webhook verification also needs to distinguish CRD conversion
configuration from admission webhook configurations.

## Scope

This is a concrete generated-content consistency finding. File schema,
provenance and publication checks pass; they do not establish the truth or
logical consistency of prose. The numeric gate approved the strategy 7/8;
feasibility, testability and scope reviewers requested revisions for other
reasons, with their reports retained. The approval policy is intentional and
is not being changed by this finding.

No Jira description, artifact or source code was edited. No new paid model
review was launched. A literal comparison found this exact overbroad clause
absent from the saved original, including after markup normalization; that
does not establish that all earlier versions were free of a similar problem.

Evidence: archived run's
data-repository/RHAISTRAT/run-gitlab-job-17591617217/strat-tasks/RHAISTRAT-2636.md,
lines 86/173, under var/run-data/20261029-real-gitlab-evening-workflow-batch/.
[Qualification](../../tasks/done/strat-evening-workflow-qualification-20261029.md).
