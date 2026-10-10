#!/usr/bin/env python3
"""Expand a tier's test list into the ordered list of runs for Markov.

    plan_runs.py --tier smoke --breadboard-ref <sha> [--only S1,S2]
                 [--variants haiku,opus] [--repeats N]

Reads data/tests/<tier>.yaml, data/arms.yaml and data/variants.yaml. Runs
are ordered in rounds: every test and variant once, then again, so arms and
variants alternate (A, B, A, B) instead of running back to back.

Prints one JSON object: {"tier", "breadboard_ref", "runs": [...]}. Each run
carries everything its job needs except the RFE key, which comes from the
seed step.
"""
import argparse
import json
import sys

import yaml

from benchlib import DATA, SHA_LEN


def fill(value, values: dict):
    if isinstance(value, str):
        return value.format(**values)
    if isinstance(value, dict):
        return {k: fill(v, values) for k, v in value.items()}
    if isinstance(value, list):
        return [fill(v, values) for v in value]
    return value


def split(text: str) -> list[str]:
    return [part.strip() for part in (text or "").split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tier", required=True)
    parser.add_argument("--breadboard-ref", required=True)
    parser.add_argument("--breadboard-repo", default="https://github.com/jctanner/breadboard")
    parser.add_argument("--only", default="", help="comma-separated test IDs")
    parser.add_argument("--variants", default="", help="comma-separated variants, replacing each test's own")
    parser.add_argument("--repeats", default="", help="replaces the tier's repeat count")
    args = parser.parse_args()

    if len(args.breadboard_ref) != SHA_LEN:
        raise SystemExit(f"--breadboard-ref must be a full 40-character commit, got {args.breadboard_ref!r}")

    tier = yaml.safe_load((DATA / "tests" / f"{args.tier}.yaml").read_text())
    arms = yaml.safe_load((DATA / "arms.yaml").read_text())["arms"]
    variants = yaml.safe_load((DATA / "variants.yaml").read_text())["variants"]
    repeats = int(args.repeats or tier.get("repeats", 1))

    tests = tier["tests"]
    only = split(args.only)
    if only:
        unknown = set(only) - {t["id"] for t in tests}
        if unknown:
            raise SystemExit(f"unknown tests for tier {args.tier}: {sorted(unknown)}")
        tests = [t for t in tests if t["id"] in only]
    variant_override = split(args.variants)
    for name in variant_override:
        if name not in variants:
            raise SystemExit(f"unknown variant {name!r}; known: {sorted(variants)}")

    runs = []
    for repeat in range(1, repeats + 1):
        for test in tests:
            arm = arms[test["arm"]]
            for variant in variant_override or test["variants"]:
                model = variants[variant]["model"]
                values = {
                    "model": model,
                    "strat_creator_ref": arm["strat_creator_ref"],
                    "breadboard_repo": args.breadboard_repo,
                    "breadboard_ref": args.breadboard_ref,
                }
                runs.append({
                    "id": f"r{repeat}-{test['id']}-{variant}",
                    "tier": args.tier,
                    "test": test["id"],
                    "arm": test["arm"],
                    "variant": variant,
                    "model": model,
                    "repeat": repeat,
                    "scenario": test["scenario"],
                    "strat_creator_ref": arm["strat_creator_ref"],
                    "mlflow_experiment": f"strat-workflow-eval/{args.tier}/{test['id']}/{variant}",
                    "script": fill(arm["script"], values),
                    "extra_env": fill(arm.get("extra_env", {}), values),
                })

    json.dump({"tier": args.tier, "breadboard_ref": args.breadboard_ref, "runs": runs}, sys.stdout)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
