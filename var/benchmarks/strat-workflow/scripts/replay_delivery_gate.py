#!/usr/bin/env python3
"""Recompute only assessment delivery from immutable archived API channels.

Original evaluation/pass and gate values are preserved alongside the new gate.
This reads no services, invokes no model and does not re-grade the pipeline.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

from check_run import REVIEWER_SKILLS, reviewer_returns


def digest(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def replay(root, strategies=None):
    root = root.resolve()
    evaluation_path = root / "artifacts/eval-result.json"
    original = json.loads(evaluation_path.read_text()) if evaluation_path.is_file() else None
    expected = strategies if strategies is not None else (original or {}).get("strategies")
    if not isinstance(expected, list) or not expected or len(set(expected)) != len(expected):
        raise ValueError("need distinct expected strategies from the evaluation or --strategies; launches do not define completeness")
    paths = sorted(path for path in (root / "api-dumps").iterdir()
                   if path.name.endswith((".request.json", ".response.json")))
    if not paths:
        raise ValueError("missing captured API requests/responses")
    inputs = {str(path.relative_to(root)): digest(path) for path in paths}
    bodies = [json.loads(path.read_text()) for path in paths]
    if evaluation_path.is_file():
        inputs[str(evaluation_path.relative_to(root))] = digest(evaluation_path)
    original_gate = (original or {}).get("checks", {}).get("reviewer_outputs_returned")
    recomputed = reviewer_returns(bodies, expected)
    comparisons = []
    original_detail = (original_gate or {}).get("detail", {})
    original_pairs = original_detail.get("by_strategy", {}) if isinstance(original_detail, dict) else {}
    for key in expected:
        for role in REVIEWER_SKILLS.values():
            before = original_pairs.get(key, {}).get(role, {}).get("returned")
            after = recomputed["detail"]["by_strategy"][key][role]["returned"]
            comparisons.append({"strategy": key, "role": role, "original_returned": before,
                                "recomputed_returned": after, "changed": before != after if before is not None else None})
    # Ensure the evidence has not changed while being read.
    if any(digest(root / name) != identity for name, identity in inputs.items()):
        raise ValueError("input capture changed during replay")
    return {"schema_version": 1, "job_directory": str(root), "expected_strategies": expected,
            "expectation_source": "explicit strategies" if strategies is not None else "archived evaluation",
            "original_job": (original or {}).get("job"), "original_pass": (original or {}).get("pass"),
            "original_failed_checks": (original or {}).get("failed_checks"), "original_gate": original_gate,
            "recomputed_gate": recomputed, "pairs": comparisons, "inputs": inputs,
            "limits": "Delivery replay only; original evaluation unchanged. Scope, incorporation and technical accuracy are not re-graded."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("--strategies", nargs="+", help="independent expected keys when no archived evaluation exists")
    parser.add_argument("--output", type=Path, required=True, help="new result file outside the original capture")
    args = parser.parse_args(argv)
    try:
        root, output = args.job.resolve(), args.output.resolve()
        protected = root
        for ancestor in [root, *root.parents]:
            if (ancestor / "manifest.json").is_file():
                protected = ancestor
                break
        if output.is_relative_to(protected):
            raise ValueError("output must be outside the original job/capture")
        result = replay(root, args.strategies)
        with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
            stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"recomputed_ok": result["recomputed_gate"]["ok"],
                          "expected": len(result["pairs"]),
                          "delivered": sum(pair["recomputed_returned"] for pair in result["pairs"]),
                          "changed_pairs": sum(pair["changed"] is True for pair in result["pairs"]),
                          "original_pass": result["original_pass"], "output": str(output)}))
        return 0 if result["recomputed_gate"]["ok"] else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Invalid delivery replay: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
