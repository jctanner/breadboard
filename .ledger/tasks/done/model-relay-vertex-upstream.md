# Model Relay Vertex upstream account

Add a managed Vertex provider with project/region and a secret service-account
JSON editor. Forward the built-in Vertex client through the new credential,
preserving existing credentials and telemetry. Component implementation and
verification live in `checkouts/model-relay/.ledger/tasks/done/vertex-upstream-accounts.md`.

Implemented and deployed 2026-10-15 with `make host-rebuild-relay` from Breadboard.
43 Rust tests, fmt, clippy, JS syntax and diff checks pass. Local fixtures cover
both ingress APIs, streaming/counting, OAuth caching for 128 concurrent callers,
rotation, failure and secret privacy. Browser controls pass using deployed UI
assets and synthetic admin responses; no real credential entered those tests.

The user-supplied `strat-creator-evals-key.json` is mode 0600, untracked and
explicitly ignored. Its JSON was imported privately into `vertex-strat-evals`;
Google OAuth authentication succeeded. The real upstream project is
`central-sdlc-ai-eng`, region `global`. The built-in `vertex-shim-local` project
now defaults to this account; its GLM-to-`enmaas-personal` override is retained.
API status and on-volume 0700/0600 permissions were checked after deployment.
All existing upstream accounts remain present; credentials and telemetry were
preserved. Source/ledger files contain no actual key material.

No paid model inference was sent. Prediction IAM permissions, model enablement
and Vertex model quota still require a real inference check. Source branch:
`feat/vertex-upstream-accounts` in the component checkout. Commit `2a50ce6`
was pushed to the matching origin branch; the component worktree is clean.
