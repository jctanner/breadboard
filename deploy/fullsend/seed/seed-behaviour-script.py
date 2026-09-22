#!/usr/bin/env python3
"""Seed the dummy runtime's behaviour script into the target repository.

The conformance path runs `runtime: dummy`, which executes a scripted list of
operations inside the real sandbox instead of calling a model. It hard-fails
without `.fullsend/behaviour/current-scenario.yaml`, so nothing gets past the
agent step until this exists.

What the script asserts is the point of the exercise. Every claim the
conformance run wants to make about the trust boundary is checked here, from
inside the sandbox, by something that cannot succeed by accident:

- the scoped credential arrived, and it is the minted one rather than an
  ambient admin token;

- the run's own identity arrived with it, so the sandbox knows which issue on
  which forge it is working;
- the forge it was told about is this stack's, not github.com;
- the target repository really was copied in; and
- an artifact written inside the sandbox comes back out, through schema
  validation, to the post-script that labels and comments on the issue.

Two constraints shaped it, both discovered by reading the runtime rather than
guessing:

**Every operation runs, and any failure fails the run.** The executor does not
stop at the first error; it records each result and reports failure if any
operation failed. So there is no way to express "this should have been
refused" as an operation. A negative probe would simply fail the run.

Note when reading a failed run that the headline names only the *first* failed
operation. The full set is in `output/behaviour-results.json`, and a run can
still write a valid `agent-result.json` from the fixture below and pass schema
validation with several assertions failing. Judge a run by that file, not by
the headline or by the comment the post-script leaves on the issue.

**`read_file` does not resolve paths the way the other file ops do.** It
resolves relative to the *target repository*; `write_fixture`, `assert_file`
and `assert_json` resolve relative to the sandbox *workspace*, which is the
repository's parent. So `read_file output/agent-result.json` looks for
`target-repo/output/agent-result.json` and fails, while the identical argument
to `assert_file` finds the file. This script got that wrong from the day it was
written and never found out, because an earlier assertion always failed first
and the headline reports only the first failure. The two bases are now
exercised deliberately, one op each, so the distinction stays visible.

**`url_get` shells out to curl, which the sandbox policy blocks on purpose.**
The provider profile's binary allowlist is `gh` and `node`, and its comment
says curl is excluded from every profile so an agent cannot make raw HTTP
calls with the injected token. Using `url_get` here would be asking the policy
to break its own rule. Network reachability is already proven a step earlier,
by the harness's own pre-flight check, which reaches the forge through the
proxy using gh.

So this script asserts what it can prove honestly and leaves the rest to the
parts of the run that already prove it.

This script asserted GH_ENTERPRISE_TOKEN once before, saw it fail, and dropped
it on the reasoning that the sandbox simply does not set that variable. That
reasoning was wrong, and so was dropping it. The assertion failed because
behaviour operations ran without the harness environment loaded at all, which
is also why GH_HOST failed for the entire life of this script. With that fixed
upstream (patch 0009), the variable is delivered and the assertion is
meaningful: on a non-github.com host it is the variable gh actually reads, so
it is the one that proves the minted credential is what an agent would use.

The embedded result is validated against the real schema before anything is
written, because the schema's top-level `required` is not the whole story: an
`allOf` makes further properties mandatory depending on the action chosen, and
finding that out from a failed run costs minutes rather than seconds.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

from emulator import ORG, REPO, api_request


# deploy/fullsend/seed/seed-behaviour-script.py -> parents[3] is the project root.
ROOT = Path(__file__).resolve().parents[3]

SCRIPT_PATH = ".fullsend/behaviour/current-scenario.yaml"

# Must satisfy schemas/triage-result.schema.json, which requires action,
# reasoning and comment, and refuses any property it does not declare.
# "insufficient" is the honest action for an issue nobody assessed, and the
# schema's allOf then requires clarity_scores with all five components. Read
# the conditional branches, not just the top-level "required": choosing an
# action here also chooses which extra properties become mandatory.
TRIAGE_RESULT = {
    "action": "insufficient",
    "clarity_scores": {
        "symptom": 0.0,
        "cause": 0.0,
        "reproduction": 0.0,
        "impact": 0.0,
        "overall": 0.0,
    },
    "reasoning": (
        "Scripted result from the dummy runtime. No model was consulted: this "
        "run exercises the dispatch, credential and sandbox path, not an "
        "agent's judgement."
    ),
    "comment": (
        "This issue was processed by the Breadboard conformance run using "
        "Fullsend's dummy runtime, which follows a fixed script instead of "
        "calling a model.\n\n"
        "The run verified from inside the sandbox that the minted credential "
        "and the issue context arrived, that the forge it was given is this "
        "environment's rather than github.com, and that the target repository "
        "was copied in. This comment and any label alongside it were written "
        "by the post-script using that credential, which is the evidence that "
        "the whole path works.\n\n"
        "Nothing here is an assessment of the issue itself."
    ),
}

BEHAVIOUR_SCRIPT = """# Seeded by deploy/fullsend/seed/seed-behaviour-script.py.
# Not part of Fullsend. This is the scripted scenario the dummy runtime runs
# in place of an agent, and it is what the conformance run actually proves.
#
# Every operation below must succeed: the runtime records each one and fails
# the run if any failed, so there is no way to express a negative assertion
# here. Reachability of the forge, and unreachability of anything else, are
# enforced by the sandbox's provider profile and demonstrated by the harness's
# own pre-flight check, not by this script.
ops:
  - description: The minted credential reached the sandbox
    op: assert_env
    args: GH_TOKEN

  - description: >-
      The credential reached the variable gh actually reads. On any host other
      than github.com gh takes its token from GH_ENTERPRISE_TOKEN and ignores
      GH_TOKEN, so this is the one that decides which identity an agent acts
      as.
    op: assert_env
    args: GH_ENTERPRISE_TOKEN

  - description: >-
      The sandbox was told which forge to use. Without this, gh silently
      addresses github.com no matter where the run is executing.
    op: assert_env
    args: GH_HOST

  - description: The run's own subject reached the sandbox
    op: assert_env
    args: ISSUE_URL

  - description: The forge family was declared, which selects the harness overlay
    op: assert_env
    args: FULLSEND_FORGE

  - description: The target repository was copied into the sandbox
    op: assert_file
    args: target-repo/README.md

  - description: >-
      The same file is readable at the path an agent would use. read_file
      resolves against the target repository rather than the workspace, so
      this asserts the base the agent's own tooling works from.
    op: read_file
    args: README.md

  - description: >-
      Write the agent result. This is the artifact that has to survive schema
      validation and reach the post-script, which labels and comments on the
      issue using the minted credential. If it comes back out, the whole path
      from event to forge write is closed.
    op: write_fixture
    args: output/agent-result.json, fixtures/triage-result.json
    content: |
%(result)s

  - description: >-
      The result came back from inside the sandbox, so a write that silently
      produced nothing cannot pass for success. Workspace-relative, unlike the
      read_file above.
    op: assert_file
    args: output/agent-result.json

  - description: The result is the shape the post-script consumes
    op: assert_json
    args: output/agent-result.json,action
"""


def render() -> str:
    body = json.dumps(TRIAGE_RESULT, indent=2)
    indented = "\n".join("      " + line for line in body.splitlines())
    return BEHAVIOUR_SCRIPT % {"result": indented}


def main() -> None:
    content = render()

    # Fail here rather than seeding a script the runtime will reject.
    import yaml

    parsed = yaml.safe_load(content)
    ops = parsed.get("ops") or []
    if not ops:
        raise RuntimeError("rendered behaviour script has no operations")
    for op in ops:
        if not op.get("op") or not op.get("description"):
            raise RuntimeError(f"operation missing op or description: {op}")
    embedded = next(o for o in ops if o["op"] == "write_fixture")
    result = json.loads(embedded["content"])

    schema_path = (
        ROOT / "checkouts" / "fullsend-ai" / "agents" / "schemas"
        / "triage-result.schema.json"
    )
    if not schema_path.is_file():
        raise RuntimeError(
            f"cannot validate the embedded result: {schema_path} is missing"
        )
    import jsonschema

    try:
        jsonschema.validate(result, json.loads(schema_path.read_text()))
    except jsonschema.ValidationError as exc:
        raise RuntimeError(
            f"the embedded result does not satisfy the triage schema: {exc.message}"
        ) from exc

    encoded = base64.b64encode(content.encode()).decode()
    status, existing = api_request(
        "GET", f"/repos/{ORG}/{REPO}/contents/{SCRIPT_PATH}"
    )
    body = {
        "message": "Seed the dummy runtime behaviour script",
        "content": encoded,
        "branch": "main",
    }
    if status == 200 and isinstance(existing, dict):
        if existing.get("content", "").replace("\n", "") == encoded:
            print(f"behaviour script already current at {ORG}/{REPO}:{SCRIPT_PATH}")
            return
        body["sha"] = existing["sha"]

    status, payload = api_request(
        "PUT", f"/repos/{ORG}/{REPO}/contents/{SCRIPT_PATH}", body
    )
    if status not in (200, 201):
        raise RuntimeError(f"write {SCRIPT_PATH} failed: HTTP {status}: {payload}")
    print(f"seeded {len(ops)} behaviour operations to {ORG}/{REPO}:{SCRIPT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        sys.exit(f"Behaviour script seed failed: {exc}")
