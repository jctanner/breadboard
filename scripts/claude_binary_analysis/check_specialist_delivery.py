#!/usr/bin/env python3
"""Check expected reports in receiving tool results, without reading transcripts.

The manifest names each strategy/role/tool ID and either a hashed reference
report or required authored fragments. Matching proves delivery of that text,
not correct review scope, faithful final incorporation, or technical truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[A-Za-z0-9_.:/-]+", text.lower()))


def result_text(content) -> str:
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text = "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    else:
        raise ValueError("result content must be text or text blocks")
    return re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S).strip()


def validate_manifest(manifest: dict, directory: Path) -> list[dict]:
    expected = manifest.get("expected")
    if manifest.get("schema_version") != 1 or not isinstance(expected, list) or not expected:
        raise ValueError("manifest needs schema_version 1 and a nonempty expected list")
    pairs, ids, entries = set(), set(), []
    for row in expected:
        for key in ("strategy", "role", "tool_use_id"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"manifest entry needs {key}")
        pair = (row["strategy"], row["role"])
        if pair in pairs or row["tool_use_id"] in ids:
            raise ValueError("duplicate expected strategy/role or tool ID")
        pairs.add(pair)
        ids.add(row["tool_use_id"])
        reference, fragments = row.get("expected_report"), row.get("required_fragments")
        if (reference is None) == (fragments is None):
            raise ValueError("each entry needs exactly one reference report or fragment list")
        if reference is not None:
            path = (directory / reference["file"]).resolve()
            if not path.is_relative_to(directory.resolve()):
                raise ValueError("reference report must stay inside the manifest directory")
            raw = path.read_bytes()
            if digest(raw) != reference.get("sha256"):
                raise ValueError("reference report hash mismatch")
            fragments = [raw.decode()]
        if not isinstance(fragments, list) or not fragments or any(
            not isinstance(f, str) or not normalize(f) for f in fragments
        ):
            raise ValueError("delivery assertions need nonempty text fragments")
        entries.append({**row, "assertions": [normalize(f) for f in fragments]})
    return entries


def check_delivery(manifest: dict, observations: list[dict], directory: Path) -> dict:
    expected = validate_manifest(manifest, directory)
    by_id = {}
    for observation in observations:
        if not isinstance(observation.get("tool_use_id"), str):
            raise ValueError("observation needs tool_use_id")
        by_id.setdefault(observation["tool_use_id"], []).append(observation)
    rows = []
    for entry in expected:
        matches = by_id.get(entry["tool_use_id"], [])
        # Repeated conversation history is not another delivery or another trial.
        unique = {json.dumps({k: o.get(k) for k in
                  ("strategy", "role", "content", "is_error")}, sort_keys=True) for o in matches}
        reason, body, present = "missing result", "", []
        if len(unique) > 1:
            reason = "conflicting results for one tool ID"
        elif matches:
            observation = matches[0]
            body = result_text(observation.get("content"))
            present = [fragment in normalize(body) for fragment in entry["assertions"]]
            if observation.get("strategy") != entry["strategy"] or observation.get("role") != entry["role"]:
                reason = "launch identity mismatch"
            elif observation.get("is_error"):
                reason = "error result"
            elif not all(present):
                reason = "expected report text absent"
            else:
                reason = "expected report text delivered"
        rows.append({"strategy": entry["strategy"], "role": entry["role"],
                     "tool_use_id": entry["tool_use_id"],
                     "delivered": reason == "expected report text delivered", "reason": reason,
                     "report_chars": len(body), "result_sha256": digest(body.encode()) if body else None,
                     "assertions_present": present,
                     "evidence": [o["evidence"] for o in matches if "evidence" in o]})
    unexpected = sorted(set(by_id) - {row["tool_use_id"] for row in expected})
    delivered = sum(row["delivered"] for row in rows)
    return {"schema_version": 1, "ok": delivered == len(rows) and not unexpected,
            "expected": len(rows), "delivered": delivered,
            "unexpected_result_ids": unexpected, "pairs": rows,
            "limits": "Checks receiving-channel text against declared references; does not grade scope, incorporation, or accuracy."}


def read_api_channels(api: Path, manifest: dict) -> list[dict]:
    """Join actual Skill launches and receiving results through paired API files."""
    api = api.resolve()
    def load(name):
        path = (api / name).resolve()
        if not path.is_relative_to(api):
            raise ValueError("API index path escapes its directory")
        raw = path.read_bytes()
        return json.loads(raw), {"file": name, "sha256": digest(raw)}
    index = [json.loads(line) for line in (api / "index.jsonl").read_text().splitlines() if line]
    expected_by_id = {row["tool_use_id"]: row for row in manifest["expected"]}
    accepted_skills = {row.get("skill", f"strategy-{row['role']}-review")
                       for row in manifest["expected"]}
    accepted_skills.update(f"strategy-{role}-review" for role in
                           ("feasibility", "testability", "scope", "architecture"))
    launches, requests = {}, []
    for pair in index:
        response, _ = load(pair["response_file"])
        request, evidence = load(pair["request_file"])
        requests.append((request, evidence))
        for block in response.get("content", []):
            if block.get("type") != "tool_use" or block.get("name") != "Skill":
                continue
            args = block.get("input") or {}
            skill = args.get("skill", "").split(":")[-1]
            if skill not in accepted_skills:
                continue
            entry = expected_by_id.get(block["id"])
            target = str(args.get("args", "")).strip()
            keys = sorted(set(re.findall(r"\bRHAISTRAT-\d+\b", target)))
            strategy = keys[0] if len(keys) == 1 else target if not keys else None
            role = skill.removeprefix("strategy-").removesuffix("-review")
            if entry and skill == entry.get("skill", f"strategy-{entry['role']}-review"):
                role = entry["role"]
            launch = {"strategy": strategy, "role": role}
            if block["id"] in launches and launches[block["id"]] != launch:
                raise ValueError("conflicting Skill launches for one tool ID")
            launches[block["id"]] = launch
    observations = []
    for request, evidence in requests:
        for message in request.get("messages", []):
            if message.get("role") != "user" or not isinstance(message.get("content"), list):
                continue
            for block in message["content"]:
                tool_id = block.get("tool_use_id")
                if block.get("type") == "tool_result" and tool_id in launches:
                    observations.append({**launches[tool_id], "tool_use_id": tool_id,
                                         "content": block.get("content"),
                                         "is_error": bool(block.get("is_error")), "evidence": evidence})
    # Retain an unexpected launch even when no result arrived.
    observed = {row["tool_use_id"] for row in observations}
    for tool_id in set(launches) - set(expected_by_id) - observed:
        observations.append({**launches[tool_id], "tool_use_id": tool_id, "content": ""})
    return observations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("manifest", type=Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--api-dir", type=Path, help="paired API index and request/response files")
    source.add_argument("--channels", type=Path, help="JSON with observations from receiving results")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text())
        validate_manifest(manifest, args.manifest.parent)
        observations = read_api_channels(args.api_dir, manifest) if args.api_dir else json.loads(args.channels.read_text())["observations"]
        result = check_delivery(manifest, observations, args.manifest.parent)
        result["manifest_sha256"] = digest(args.manifest.read_bytes())
        if args.output:
            with args.output.open("x") as output:
                output.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"ok": result["ok"], "expected": result["expected"],
                          "delivered": result["delivered"], "unexpected_result_ids": result["unexpected_result_ids"]}))
        return 0 if result["ok"] else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Invalid delivery-check input: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
