#!/usr/bin/env python3
"""Combine the runs' eval-results into one summary table.

    summarize.py < eval-results.json

Reads a JSON list of eval-results on stdin (objects, or the JSON text
check_run.py printed) (the workflow sends them with script_exec stdin, which has no size
limit, unlike an argument). Prints a Markdown
summary: one row per run, then one per test and variant with the pass count,
median wall time and mean tokens. Ends with one JSON line of totals.
"""
import json
from statistics import mean, median
import sys


def minutes(seconds) -> str:
    return "–" if seconds is None else f"{seconds / 60:.1f}"


def thousands(value) -> str:
    if value is None:
        return "–"
    return f"{value / 1e6:.2f}M" if value >= 1e6 else f"{value / 1000:.0f}k"


def main(argv: list[str]) -> int:
    results = [r if isinstance(r, dict) else json.loads(r) for r in json.load(sys.stdin) if r]
    results.sort(key=lambda r: (r["repeat"], r["test"], r["variant"]))

    print("## Runs\n")
    print("| Run | Test | Arm | Variant | Pass | Failed checks | Verdict | Minutes | Calls | Output | Cache read | Cache write | 429s | Job |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in results:
        u = r.get("usage", {})
        verdict = f"{r['verdict']} {r['score']}" if r.get("verdict") else "–"
        print(f"| {r['run']} | {r['test']} | {r['arm']} | {r['variant']} | {'yes' if r['pass'] else 'NO'} "
              f"| {', '.join(r.get('failed_checks', [])) or '–'} | {verdict} | {minutes(r.get('wall_seconds'))} "
              f"| {u.get('calls', '–')} | {thousands(u.get('output'))} | {thousands(u.get('cache_read'))} "
              f"| {thousands(u.get('cache_write'))} | {u.get('rate_limited', '–')} | {r['job']} |")

    groups: dict[tuple, list] = {}
    for r in results:
        groups.setdefault((r["test"], r["arm"], r["variant"]), []).append(r)
    print("\n## By test\n")
    print("| Test | Arm | Variant | Passed | Median minutes | Mean output | Mean cache read | Mean cache write |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for (test, arm, variant), rows in sorted(groups.items()):
        walls = [r["wall_seconds"] for r in rows if r.get("wall_seconds") is not None]
        usage = [r.get("usage", {}) for r in rows]

        def avg(key):
            values = [u[key] for u in usage if key in u]
            return mean(values) if values else None
        print(f"| {test} | {arm} | {variant} | {sum(r['pass'] for r in rows)}/{len(rows)} "
              f"| {minutes(median(walls)) if walls else '–'} | {thousands(avg('output'))} "
              f"| {thousands(avg('cache_read'))} | {thousands(avg('cache_write'))} |")

    totals = {"runs": len(results), "passed": sum(r["pass"] for r in results)}
    totals["all_passed"] = totals["runs"] > 0 and totals["passed"] == totals["runs"]
    print()
    print(json.dumps(totals))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
