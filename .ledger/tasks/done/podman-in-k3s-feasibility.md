# M1: Run Podman inside k3s

## Goal

Prove nested Podman works on this cluster before starting any other
[Fullsend strategy POC implementation](../../plans/fullsend-entrypoint-strategy-poc.md).
No OpenShell, agent calls, or strategy processing in this milestone.

## Work

Use a disposable pod with rfe-autofixer's job image, recording its resolved
digest, and reproduce its VFS/storage setup. Try current runner-equivalent
permissions first. If changes are necessary, isolate them in a test pod and
dedicated test runner/tag; record capabilities, privilege settings, storage,
and network requirements. Do not change cluster-wide security settings or
mount the host's Docker/Podman socket to make the test pass.

Keep reproducible manifests and scripts under
`var/demos/fullsend-entrypoint-poc/podman-smoke/`. Keep raw logs/runtime state
ignored; record a non-secret evidence summary in the ledger. Once the direct
pod test works, run the same checks through GitLab's Kubernetes executor.

## Acceptance criteria

- [x] Pull and run an inner container; verify both success and nonzero exit propagation.
- [x] Write a file through a workspace bind mount and read it from the outer job.
- [x] Verify DNS and outbound HTTPS from the inner container.
- [x] Remove inner containers and disposable storage, including after a failed test.
- [x] Repeat successfully from a fresh pod without reused runtime state.
- [x] Pass the same smoke test in a real GitLab Kubernetes-executor job.
- [x] Record image/version, configuration, commands, job ID, and pass/failure evidence.

## Gate

All criteria must pass before OpenShell integration, Fullsend implementation,
or strat-creator migration starts. A Podman version/info check is insufficient.
On failure, record the blocker and revisit runner choice; do not proceed on
an assumption that the nested runtime will work later. Passing does not yet
prove that OpenShell or its Docker driver works.

## Status

Complete. See [M1 evidence](../../notes/podman-in-k3s-m1-evidence.md).
