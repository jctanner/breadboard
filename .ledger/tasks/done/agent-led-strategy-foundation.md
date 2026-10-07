# A1: Prepare and synchronize the strat-creator checkout

Follow the [agent-led POC plan](../../plans/fullsend-agent-led-strategy-poc.md).

## Ordered work and acceptance criteria

1. [x] Create the working checkout at
   `checkouts.fullsend_agent_led_poc/jctanner.strat-creator` from the user's fork.
   Read its instructions and locally ignore the checkout in Breadboard. If a
   checkout already exists, inspect its work before using it.
2. [x] Verify `origin` points to
   `github.com/jctanner-opendatahub-io/strat-creator`; add or correct `upstream`
   to `https://github.com/opendatahub-io/strat-creator.git`. Fetch both remotes.
3. [x] Start local `main` from the fetched `origin/main`, preserve its original
   tip in a local backup reference, and rebase it onto the fetched `upstream/main`.
   Resolve conflicts while preserving intentional fork changes. Run required
   pre-push checks and `git diff --check`, then push the rebased `main` to origin.
   Use a normal push when possible; if existing history was rewritten, use
   `--force-with-lease` against the recorded remote tip, never an unconditional
   force push. If origin advances, fetch/reconcile it before retrying.
4. [x] Verify the published `origin/main` matches local `main` and contains the
   recorded `upstream/main` as an ancestor. Create and switch to
   `feat/fullsend-agent-led-strategy` from that synchronized `main`.
5. [x] Record checkout path, remote URLs, original origin tip, fetched upstream
   tip, rebased/published main SHA, feature branch/base SHA, checks and any
   conflict resolutions. Leave a clean working tree on the new feature branch.

## Scope

Repository preparation only. Prompt files come next in
[A2](agent-led-strategy-prompts.md). The
previous POC's checkouts and feature branches are separate. This task does
not start CI, alter Jira, or run a model.

## Status

Done, 2026-10-07.

## Evidence

- Checkout: `checkouts.fullsend_agent_led_poc/jctanner.strat-creator`, cloned
  into the pre-existing empty directory. Read its `CLAUDE.md` and `Makefile`.
  Ignored locally through Breadboard `.git/info/exclude`
  (`checkouts.fullsend_agent_led_poc/`).
- Remotes: `origin` `git@github.com:jctanner-opendatahub-io/strat-creator.git`;
  `upstream` `https://github.com/opendatahub-io/strat-creator.git`. Both fetched.
- Original `origin/main`: `cc1ba8c` ("fix target version config in
  strat-create (#79)"). Fetched `upstream/main`: `cc1ba8c`. Ahead/behind 0/0.
- Rebase: none needed; fork main already equalled upstream main. No conflicts,
  no backup ref required, nothing pushed. `git ls-remote origin` confirms
  `refs/heads/main` = `cc1ba8cc22eba2a007e94f9a2c8036f8963defaf`, and
  `upstream/main` is an ancestor of `origin/main`.
- Feature branch: `feat/fullsend-agent-led-strategy` created from `main` at
  `cc1ba8c`; local only, not yet pushed (A2 pushes it).
- Baseline checks on that base: `make lint` passed; `make test`
  768 passed, 1 skipped (113 s, Python 3.14 venv via `uv sync`).
  `git diff --check` clean; working tree clean.
