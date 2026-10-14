#!/usr/bin/env python3
"""Verify one archived focused refinement handoff recovery, not strategy quality."""
import argparse
import json
from pathlib import Path
import re

import yaml

from verify_reviewer_delivery import MODEL, objects

KEYS = ["STRAT-9401", "STRAT-9402"]


def verify(root):
    artifacts = root / "artifacts"
    requests = [json.loads(p.read_text()) for p in (root / "api-dumps").glob("*.request.json")]
    responses = [json.loads(p.read_text()) for p in (root / "api-dumps").glob("*.response.json")]
    errors, calls, bound_schemas = [], {}, set()
    models = sorted({request.get("model", "") for request in requests})
    if models != [MODEL] or not responses:
        errors.append("missing captures or unexpected model")
    for request in requests:
        for tool in request.get("tools", []):
            if tool.get("name") == "StructuredOutput":
                choices = tool.get("input_schema", {}).get("properties", {}).get("recorded", {}).get("enum", [])
                if len(choices) == 2 and choices[-1] == "none" and choices[0] in KEYS:
                    bound_schemas.add(choices[0])
    if bound_schemas != set(KEYS):
        errors.append("target-bound refinement schemas not observed")
    for document in requests + responses:
        for block in objects(document.get("messages", document.get("content", []))):
            if block.get("type") == "tool_use":
                calls[block["id"]] = block
    for key in KEYS:
        skills = [call for call in calls.values() if call.get("name") == "Skill"
                  and call.get("input", {}).get("skill", "").split(":")[-1] == "strategy-refine"
                  and call["input"].get("args", "").split()[:1] == [key]]
        apply = [call for call in calls.values() if call.get("name") == "Bash"
                 and re.search(r"fixture.py\s+apply\s+" + re.escape(key) + r"\b", call.get("input", {}).get("command", ""))]
        marks = [call for call in calls.values() if call.get("name") == "Bash"
                 and re.search(r"strat_pipeline_state.py\s+mark\s+refine\s+" + re.escape(key) + r"\b",
                               call.get("input", {}).get("command", ""))]
        if len(skills) != 1 or len(apply) != 1 or len(marks) != 1:
            errors.append(f"{key}: expected one Skill, fixture action and completion mark")
    progress = json.loads((artifacts / "fixture-state/strat-progress.json").read_text())
    data = json.loads((artifacts / "fixture-state/strat-input.json").read_text())
    if progress.get("run_id") != data.get("run_id") or set(progress.get("refine", {})) != set(KEYS):
        errors.append("saved completion does not match this run and its two targets")
    for key in KEYS:
        path = artifacts / "fixture-strategies" / (key + ".md")
        metadata = yaml.safe_load(path.read_text().split("---", 2)[1])
        if (metadata.get("strat_id") != key or metadata.get("source_rfe") != key.replace("STRAT", "RHAIRFE")
                or metadata.get("status") != "Refined" or metadata.get("refine_count") != 1):
            errors.append(key + ": saved artifact identity/status/invocation count is wrong")
    events = [json.loads(line) for line in (artifacts / "fixture-state/refine-checkpoints/events.jsonl").read_text().splitlines()]
    snapshots = [event for event in events if event.get("allowed") and (event.get("result") or {}).get("kind") == "checkpoint"]
    if not any(event["result"]["verified"]["refined"] == KEYS and not event["result"]["verified"]["rejected"] for event in snapshots):
        errors.append("no actual persisted-state checkpoint accepted by the hook")
    result = None
    for path in (artifacts / "native-projects").rglob("workflows/wf_*.json"):
        state = json.loads(path.read_text())
        if state.get("state", state.get("status")) == "completed":
            result = state.get("result")
    fault = {"key": KEYS[1], "receipt": {"recorded": json.dumps({"recorded": KEYS[1]}, separators=(",", ":"))}}
    if (not isinstance(result, dict) or result.get("ready") != KEYS or result.get("failed") != []
            or result.get("injected") != [fault]):
        errors.append("injected malformed receipt did not recover to the correct ready set")
    if (artifacts / "claude-exit.txt").read_text().strip() != "0":
        errors.append("CLI did not exit successfully")
    return {"passed": not errors, "errors": errors, "models": models,
            "requests": len(requests), "responses": len(responses), "workflow_result": result,
            "saved_refined": sorted(progress.get("refine", {})), "hook_events": len(events),
            "bound_receipt_schemas": sorted(bound_schemas),
            "claim": "focused GLM carried actual validated state and recovered one injected handoff fault without repeating fixture work; content generation and full pipeline are separate"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.job)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
