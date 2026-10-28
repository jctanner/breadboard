# Plan: Workflow Dojo (optional service)

## Context

Workflow Dojo is a LeetCode-style page for learning to create, run and debug
Claude Code workflow scripts (the Workflow tool's `agent`/`parallel`/`pipeline`
JavaScript). Its source is the separate component repository
[jctanner/claude-workflow-dojo](https://github.com/jctanner/claude-workflow-dojo),
checked out locally at `checkouts/workflow-dojo/`.
Maintained integration docs: `docs/workflow-dojo.md`.

Decisions:

- **Free simulated judge.** The judge is a deterministic in-browser simulator
  (virtual clock, mocked agents, concurrency cap). Barrier and sequential-await
  mistakes show up as Time Limit Exceeded.
- **Live shell.** The live Claude shell reuses context-inspector's
  server-owned PTY design: one shared session with detachable WebSocket views.
  Inside the pod, Claude runs directly in the PTY rather than through
  Podman/MITM.
- **User-supplied relay key.** Inference goes through Model Relay using a key
  the user created for the dojo (2026-10-26) and stored with
  `workflow-dojo-relay-key.py --stdin`. A key the script issued during setup was
  revoked.

## Stages

1. **Local trainer: done 2026-10-26.**
   - Built: the simulator, judge, 12 problems, playground and reference page.
   - Evidence: `npm test`; Playwright walkthrough.
2. **K8s service with live Claude: done 2026-10-26.**
   - Built:
     - the FastAPI server, `dojo/`;
     - the image (`Containerfile`, Claude Code 2.1.311);
     - `deploy/k8s/31-workflow-dojo.yaml`, `05n-build-workflow-dojo.sh`,
       `28-deploy-workflow-dojo.sh` and `workflow-dojo-relay-key.py`;
     - the `dojo.local` proxy route and certificate SAN;
     - a proxy change that clears deadlines on WebSocket upgrades;
     - the `host-deploy-dojo`, `host-rebuild-dojo`, `host-dojo-relay-key` and
       `host-logs-dojo` targets.
     It is not in `deploy-all.sh`.
   - Evidence:
     - server unittest, with `cat` as the shell;
     - a live probe through `dojo.local`: the TUI opens with no prompts,
       answers 6*7 → 42, and the WebSocket stays open after 140s idle;
     - the real Workflow tool ran `hello-workflow` (1 agent, about 27s);
     - the browser "Run for real" flow completed through a port-forward.
     - Bug found and fixed: the seeded `CLAUDE.md` initially led a subagent to
       `node`-run the script; it now tells subagents to answer directly.
   - Pending the user: add `dojo.local` to `/etc/hosts`.
3. **Tier 0, JavaScript for Python developers: done 2026-10-26.**
   - Why: the user (a Python developer) kept losing time to JavaScript habits
     rather than to orchestration concepts.
   - Built: eight plain-script problems (0.1–0.8) on arrow returns, sort,
     template strings, nullish values, spread, positional callbacks, objects
     and `await`; a Python equivalent on each; and a JS↔Python table on the
     Reference page.
   - Workflow problems keep their numbers, #1–12.
   - Expanded the same day to 19 problems, after reviewing the user's #6
     transcript. Added: truthiness, `const`/`let`, `split` limits,
     `some`/`every`/`find`/`in`, loops, counting into objects, block and
     callback scope, nested callbacks (the #6 shape), JSON/printing/identity,
     `try`/`catch`, and `.then()`.
   - The #6 review also found that "Ask Claude" is too stingy with examples.
     Proposed fixes: an adaptive tutor prompt, an "Explain in Python" button,
     and splitting #6 into two steps.
   - Evidence: `npm test`; checked in the browser.
   - Breakpoint: waiting for the user's review.
4. **Tier 2, production patterns: done 2026-10-27.**
   - Source: generalized from
     `checkouts.tmp/jctanner-fullsend-ai/strat-creator/workflows/strat-pipeline.js`,
     the workflow the user will support in production. The lessons use generic
     items (`T-n`), at the user's request.
   - Built: nine atomic lessons (2.1–2.9), plus Tier 0 Sets/Maps and
     regex/`throw`/`||` defaults.
   - Simulator fidelity: `const`, `pattern`, `minLength`,
     `additionalProperties: false` and `uniqueItems`; root
     `oneOf`/`anyOf`/`allOf` rejected like the real API 400; tests that
     expect a throw.
   - Evidence: `npm test`.
4b. **Readability and accounts: done 2026-10-27.**
   - Why: the user found the task hard to pick out of each description, and
     lost their progress when they used the dojo from a second machine.
   - Built: a Goal box on every problem (one sentence plus the first test's
     `args` → expected result); *Speaking JavaScript* page references on Tier
     0; user accounts with per-user server-side progress and per-user Claude
     sessions/workspaces (cap 4); an admin Users page and an Account page; a
     bootstrap `admin`/`admin` Secret (`workflow-dojo-admin-secret.sh`).
   - Evidence: `npm test`; server unittest (login required, forged cookie
     refused, per-user progress, last-admin guard, session isolation over the
     WebSocket); a browser check of login, the one-time `localStorage` upload,
     and an editor change saved to the server.
4c. **Migration recovery lessons: done 2026-10-28.**
   - Source: `.ledger/notes/strat-workflow-migration-lessons.md`, at the
     user's request.
   - Built: Tier 2 problems 2.10–2.13: `p-stale-reuse` (a freshness key must
     cover input and instructions), `p-intent-first` (record intent, read back
     instead of retrying, reconcile pending intents), `p-defer-stale` (defer a
     stale item; throw only when the checker fails for every item) and
     `p-real-completion` (complete/incomplete/unknown from an inventory; a
     failed report doesn't rerun work).
   - Evidence: `npm test`, plus partly fixed variants of each solution, which
     the judge rejects on the intended test.
   - Not simulated: StructuredOutput loss through nested Skills and the agent
     editing its own coordinator. Those suit the journal-based drills below.
5. **Proposed: a support track (pending a go).** Predict-the-run problems, a
   failure-mode catalog, incident drills built from real `journal.jsonl`
   artifacts, and resume/caching drills.
6. **Later options (pending a decision).**
   - More problems: judge panel, completeness critic, worktree isolation,
     resume and journal reading.
   - Per-user sessions and auth if more than one person uses the dojo.
   - Surface `/workflows` and journal output in the dojo UI.
