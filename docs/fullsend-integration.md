# Fullsend Integration

Fullsend is Breadboard's agentic software-engineering execution path. Breadboard
provides the isolated GitHub emulator, Actions scheduler and runners, local
token mint, OpenShell gateway, sandbox controller, telemetry services, and
operations dashboard. Fullsend provides the workflow shim, role-specific agent
workflows, configuration, and CLI.

The current integrated path is GitHub-first. The
`fullsend-dev/triage-target` repository carries the `.fullsend/` configuration
and Fullsend workflow shim. Jira and GitLab are available to the broader
Breadboard platform, but they do not directly trigger Fullsend agent runs in
the current deployment.

At a glance — who provides what, and the path an event takes:

```mermaid
graph LR
    event(["Issue · PR · comment · review"]) --> forge

    subgraph breadboard["Breadboard provides"]
        forge["GitHub emulator<br/>repos · issues · PRs · Actions"]
        runners["Actions runners"]
        mint["Local token mint"]
        shell["OpenShell gateway<br/>sandbox controller"]
    end

    subgraph fullsend["Fullsend provides"]
        shim["Workflow shim<br/>.github/workflows/fullsend.yaml"]
        dispatch["Reusable dispatch<br/>selects the stage"]
        harness["Agent harnesses<br/>triage · review · code"]
    end

    forge -->|"matches trigger"| shim
    shim --> dispatch
    dispatch -->|"queues a job"| runners
    runners -->|"OIDC assertion"| mint
    runners -->|"creates a sandbox"| shell
    shell --> agent["Agent sandbox<br/>loads a harness, calls a model"]
    harness -.->|"fetched at run time"| agent
    mint -.->|"role-scoped credential"| agent
    agent -->|"labels · comments · reviews · branches · PRs"| forge
```

The dashed edges are what the agent is *given*; the solid path is control
flow. The loop closes at the forge: everything an agent produces arrives back
as ordinary GitHub activity, which is why the dashboard can be a pure observer.

## Services

The integration uses these deployed components:

| Component | Responsibility |
|-----------|----------------|
| GitHub emulator | Stores repositories, issues, pull requests, workflow definitions, workflow runs, and job state; evaluates Actions event triggers. |
| GitHub Actions runners | Poll for queued jobs, execute workflow steps, and report logs and conclusions back to the emulator. Two tiers: a site-scoped agent runner (label `fullsend`) that serves every Fullsend job in every repository, and an enterprise-scoped hosted stand-in (`ubuntu-24.04`, `ubuntu-latest`) for generic CI. Onboarding a repository needs no runner deployment. |
| Fullsend Mint | Exchanges a development OIDC assertion for a role- and repository-scoped GitHub installation token. |
| OpenShell gateway | Creates and manages constrained agent sandboxes. |
| Sandbox controller | Runs the sandbox workload and exposes pod state and events to the operations dashboard. |
| Fullsend runner image | Contains the Fullsend binary, OpenShell client, Git tooling, and local runner integration. |
| Fullsend Dashboard | Reads GitHub Actions and Kubernetes state for operational visibility. It does not receive source events or dispatch agent work. |
| MLflow and Observatory | Receive optional agent traces, CI artifacts, and verification data when telemetry is configured. |

See [fullsend-services.mmd](architecture/diagrams/fullsend-services.mmd) for
the service relationship map.

## Event and token flow

Issue, pull request, issue-comment, and pull-request-review activity enters the
GitHub emulator. Its Actions event matcher starts the checked-in `fullsend`
workflow, which forwards the event payload to the reusable dispatch workflow.
The dispatch workflow selects the agent stage and queues a job. The local
runner polls and claims that job; the Fullsend dashboard is only an observer.

Inside the job, the Fullsend composite action requests an OIDC assertion and
posts it to the local mint with the requested role and repository scope. The
mint returns a short-lived token used to check out the target repository and
perform the permitted GitHub operations. The runner then starts the agent
through OpenShell.

The GitHub emulator is the OIDC issuer: an ephemeral RS256 key pair with a
JWKS at `https://github.local/.well-known/jwks.json`, issuing assertions whose
claims are derived from the job that presents its request token. The
development mint verifies those assertions against that issuer and refuses
any repository the assertion was not issued for, then signs a JWT as the
role's GitHub App and answers with a one-hour installation token the emulator
mints for that repository at the requested permission level.
This preserves the workflow contract without an external GitHub or cloud
control plane. What that mint trusts, what it covers, and what it does not
check is written up in [fullsend-mint-trust.md](fullsend-mint-trust.md).

See [fullsend-event-flow.mmd](architecture/diagrams/fullsend-event-flow.mmd)
for the sequence diagram.

## Agent sandbox

The runner supplies the event payload, checked-out workspace, scoped GitHub
token, and model credentials. OpenShell creates the sandbox through the cluster
sandbox controller, mounts the workspace, injects its proxy CA, and applies the
role's filesystem and network policy before the agent starts.

The policy is Fullsend's own. Every harness names upstream's
`policies/base.yaml` unmodified: system and image paths read-only, only
`/sandbox`, `/tmp`, and `/dev/null` writable, the process as the `sandbox`
user. Network access comes from the provider profiles each stage lists, not
from a policy written here: triage runs with `fullsend-vertex-ai` and
`fullsend-github-ro` only, and the write-capable `fullsend-github-code`
profile is named by the code and fix harnesses alone, so a read-only stage
cannot inherit it. The one local change to those profiles is the emulator's
host added beside the public ones (`github.local`, read-only, on the
read-only profile); the conformance script refuses to run if the installed
profiles have drifted from the mirrored source. The earlier hand-written
policy, `deploy/fullsend/policies/github-emulator-readonly.yaml`, survives
only in the legacy direct-token smoke and is not on the conformance path.
A green run's sandbox log reports `denied_action_count=0` in every activity
summary; run 1746 is the reference. The runner retains status and result
files in the shared job volume for the dashboard.

See [fullsend-agent-sandbox.mmd](architecture/diagrams/fullsend-agent-sandbox.mmd)
for the sandbox boundary and data paths.

The source deployment definitions are in `deploy/k8s/23*.yaml`,
`deploy/k8s/24-fullsend-mint-dev.yaml`,
`deploy/k8s/25-fullsend-direct-token-smoke.yaml`, and
`deploy/k8s/26-fullsend-dashboard.yaml`. The build and bootstrap scripts are
under `deploy/scripts/05h-*`, `deploy/scripts/05i-*`, `deploy/scripts/05j-*`,
`deploy/scripts/17-*`, `deploy/scripts/18-*`, and `deploy/scripts/22-seed-fullsend.sh`.
Fullsend's own patches, policies, and seed scripts live under
`deploy/fullsend/`; named legacy compatibility smokes (`19-run-fullsend-direct-token-smoke.sh`,
`20-run-fullsend-vertex-smoke.sh`, `21-run-fullsend-result-smoke.sh`) are
separate from this deployed path and are not run by `deploy-all.sh`.
