#!/usr/bin/env python3
"""Verify a focused outcome job using trusted helper code and receiving captures.

The archived fixture repository is data only. Helpers come from the explicit
trusted candidate checkout; original archives are never modified.
"""
import argparse
import importlib
import json
from pathlib import Path
import sys

from verify_reviewer_delivery import MODEL, objects, texts


def verify(job, trusted):
    scripts = trusted.resolve() / "scripts"
    sys.path.insert(0, str(scripts))
    outcome = importlib.import_module("strat_pipeline_outcome")
    if Path(outcome.__file__).resolve() != scripts / "strat_pipeline_outcome.py":
        raise ValueError("completion helper is not from the trusted candidate checkout")
    artifacts = job / "artifacts"
    root = artifacts / "fixture"
    requests = [json.loads(p.read_text()) for p in sorted((job / "api-dumps").glob("*.request.json"))]
    responses = [json.loads(p.read_text()) for p in sorted((job / "api-dumps").glob("*.response.json"))]
    errors = []
    models = sorted({r.get("model", "") for r in requests})
    if models != [MODEL] or not responses:
        errors.append("missing captures or wrong request model")
    receipt = outcome.verify_completion(root, root / "output/agent-result.json")
    summary = outcome.summary(root, receipt)
    matches = []
    for path in (artifacts / "native-projects").rglob("workflows/wf_*.json"):
        state = json.loads(path.read_text())
        if state.get("result") == summary:
            matches.append((path, state))
    if len(matches) != 1:
        raise ValueError("need one native Workflow with the checked completion receipt")
    path, state = matches[0]
    journals = list((artifacts / "native-projects").rglob(f"subagents/workflows/{state['runId']}/journal.jsonl"))
    if len(journals) != 1:
        raise ValueError("need matched native journal")
    cli_exit = int((artifacts / "claude-exit.txt").read_text())
    observed = outcome.observe(root, path, journals[0], cli_exit, root / "output/agent-result.json")
    if not observed["runtime_verified"]:
        errors.extend(observed["errors"])
    calls, results, outputs = {}, {}, {}
    for document in requests + responses:
        for block in objects(document.get("messages", document.get("content", []))):
            if block.get("type") == "tool_use":
                if block.get("name") == "Bash":
                    calls[block["id"]] = block.get("input", {}).get("command", "")
                elif block.get("name") == "StructuredOutput" and block.get("input", {}).get("kind") == "strat-completion":
                    outputs[block["id"]] = block["input"]
                elif block.get("name") in ("Skill", "Agent"):
                    errors.append("fixture reran specialist/generation work")
            elif block.get("type") == "tool_result":
                results[block["tool_use_id"]] = block
    final_commands = [identity for identity, command in calls.items()
                      if "scripts/strat_pipeline_state.py result" in command]
    if len(final_commands) != 1:
        errors.append("expected one final validation command")
    if not any(summary == output for output in outputs.values()):
        errors.append("actual model output does not carry validated receipt")
    if not any(json.dumps(summary, sort_keys=True) == json.dumps(value, sort_keys=True)
               for identity in final_commands
               for value in _json_values(texts(results.get(identity, {}).get("content", "")))):
        errors.append("validated receipt absent from receiving helper tool result")
    hooks = [json.loads(line) for line in (root / "tmp/completion-checkpoints/events.jsonl").read_text().splitlines()]
    if not any(event.get("allowed") and event.get("verified") == summary for event in hooks):
        errors.append("no actual completion-boundary hook approval")
    if len(receipt["result"]["strategies"]) != 2:
        errors.append("missing authored target")
    expected = {"STRAT-9601": ("approve", False), "STRAT-9602": ("revise", True)}
    if {row["strat"]: (row["recommendation"], row["needs_attention"])
            for row in receipt["result"]["strategies"]} != expected:
        errors.append("numeric fixture outcomes disagree")
    return {"passed": not errors, "errors": errors, "request_models": models,
            "requests": len(requests), "responses": len(responses), "final_commands": len(final_commands),
            "observed": observed, "completion_hook_events": len(hooks),
            "claim": "focused final validation of authored saved work; not a full pipeline or content-accuracy trial"}


def _json_values(text):
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
            if isinstance(value, dict):
                yield value
        except ValueError:
            continue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("--trusted-candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.job, args.trusted_candidate)
    if args.output:
        with args.output.open("x") as stream:
            stream.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
