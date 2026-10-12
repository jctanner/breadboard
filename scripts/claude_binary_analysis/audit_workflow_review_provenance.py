#!/usr/bin/env python3
"""Read immutable run API pairs and map specialist findings to receiving requests.

No archive is modified. Text matching records observed delivery and overlap;
it does not equate paraphrase differences with fabricated review content.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from run_plugin_experiments import sha256, write_json
from run_subagent_skill_experiments import strings

ROLES = ("feasibility", "testability", "scope", "architecture")


def user_texts(request: dict) -> list[str]:
    return [b.get("text", "") for m in request.get("messages", []) if m.get("role") == "user" for b in (m.get("content", []) if isinstance(m.get("content"), list) else [{"type": "text", "text": m["content"]}]) if b.get("type") == "text"]


def content(response: dict) -> list[dict]:
    return response.get("content", response.get("message", {}).get("content", []))


def tool_results(request: dict) -> list[dict]:
    return [b for m in request.get("messages", []) for b in (m.get("content", []) if isinstance(m.get("content"), list) else []) if b.get("type") == "tool_result"]


def fragments(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9_.:/-]+", text.lower())
    # Longer verbatim fragments are evidence of transmission/overlap, not a
    # semantic test of whether a legitimate summary incorporated a concern.
    return list(dict.fromkeys(" ".join(words[i:i + 12]) for i in range(0, max(0, len(words) - 11), 6)))


def normalize(text: str) -> str:
    text = re.sub(r'(?m)^\s*\d+\t', '', text)
    return " ".join(re.findall(r"[A-Za-z0-9_.:/-]+", text.lower()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    job = args.job
    api = job / "api-dumps"
    index = [json.loads(line) for line in (api / "index.jsonl").read_text().splitlines()]
    records = [{"index": row, "request": json.loads((api / row["request_file"]).read_text()), "response": json.loads((api / row["response_file"]).read_text())} for row in index]
    records.sort(key=lambda r: r["index"]["timestamp"])
    starts = {}
    for f in (job / "artifacts").rglob("*.jsonl"):
        # Only structured execution events, not unrelated telemetry content.
        if f.name != "stream.jsonl": continue
        for line in f.read_text().splitlines():
            try: event = json.loads(line)
            except ValueError: continue
            if event.get("subtype") == "task_started" and event.get("tool_use_id"):
                starts[event["tool_use_id"]] = event
    launches = {}
    for r in records:
        for b in content(r["response"]):
            if b.get("type") != "tool_use" or b.get("name") != "Skill": continue
            name = b.get("input", {}).get("skill", "")
            role = next((role for role in ROLES if name.endswith(f"strategy-{role}-review")), None)
            if role is None: continue
            targets = re.findall(r"\bRHAISTRAT-\d+\b", b.get("input", {}).get("args", ""))
            launches[b["id"]] = {"launch": r, "block": b, "role": role, "target": targets[0] if len(set(targets)) == 1 else None}
    review_paths = {}
    observed_tools = {b['id']: (r['index'], b) for r in records for b in content(r['response']) if b.get('type') == 'tool_use'}
    for p in (job / "artifacts").rglob("RHAISTRAT-*-review.md"):
        review_paths.setdefault(p.name.split("-review")[0], p)
    rows = []
    for id, launch in launches.items():
        source, target, role = launch["launch"], launch["target"], launch["role"]
        receiving = [r for r in records if any(b.get("tool_use_id") == id for b in tool_results(r["request"]))]
        first = receiving[0] if receiving else None
        returned = next((b for b in tool_results(first["request"]) if b.get("tool_use_id") == id), None) if first else None
        returned_text = "\n".join(v for _, v in strings(returned.get("content"))) if returned else ""
        prompt = starts.get(id, {}).get("prompt")
        child = []
        for r in records:
            if r["index"]["query_source"] != "agent:custom": continue
            if r["index"]["timestamp"] < source["index"]["timestamp"]: continue
            if first and r["index"]["timestamp"] > first["index"]["timestamp"]: continue
            for body in user_texts(r["request"]):
                if prompt and prompt.strip() in body:
                    child.append(r); break
                if not prompt and "Base directory for this skill:" in body and f"/strategy-{role}-review" in body.splitlines()[0] and target and re.search(rf"\b{re.escape(target)}\b", body):
                    child.append(r); break
        # Compaction can remove the skill body. Continue through unique tool
        # IDs or exact compact-summary payloads, rather than chronology alone.
        join_steps = []
        for _ in range(4):
            child_ids = {b['id'] for r in child for b in content(r['response']) if b.get('type') == 'tool_use'}
            summaries = []
            for r in records:
                if r['index']['query_source'] != 'compact': continue
                if any(prompt and prompt.strip() in body for body in user_texts(r['request'])) or any(b.get('tool_use_id') in child_ids for b in tool_results(r['request'])):
                    summaries.extend(b['text'] for b in content(r['response']) if b.get('type') == 'text' and len(b.get('text', '')) > 100)
            added = []
            for r in records:
                if r in child or r['index']['query_source'] != 'agent:custom': continue
                if r['index']['timestamp'] < source['index']['timestamp'] or (first and r['index']['timestamp'] > first['index']['timestamp']): continue
                method = 'unique tool result ID' if any(b.get('tool_use_id') in child_ids for b in tool_results(r['request'])) else 'exact compact summary' if any(summary in body for summary in summaries for body in user_texts(r['request'])) else None
                if method:
                    added.append(r); join_steps.append({'request_file': r['index']['request_file'], 'method': method})
            if not added: break
            child.extend(added); child.sort(key=lambda r: r['index']['timestamp'])
        prose = [(r, b.get('text', '')) for r in child for b in content(r['response']) if b.get('type') == 'text']
        assessments = [(r, t) for r, t in prose if len(t) > 700 and re.search(r"recommendation|assessment|review", t, re.I)]
        assessment_source, assessment = assessments[-1] if assessments else (None, "")
        child_calls = [(r, b) for r in child for b in content(r["response"]) if b.get("type") == "tool_use"]
        last = child[-1] if child else None
        last_types = [b["type"] + (":" + b.get("name", "") if b["type"] == "tool_use" else "") for b in content(last["response"])] if last else []
        all_parent_text = "\n".join(v for r in receiving for m in r['request'].get('messages', []) if m['role'] == 'user' for _, v in strings(m.get('content')))
        parent_norm = normalize(all_parent_text)
        assessment_fragments = fragments(assessment)
        delivered_fragments = [f for f in assessment_fragments if f in parent_norm]
        # Exclude the expected Skill return to identify alternate result paths.
        alternate = []
        seen = set()
        for r in receiving:
            for b in tool_results(r["request"]):
                other = b.get("tool_use_id")
                if other == id or other in seen: continue
                seen.add(other)
                text = "\n".join(v for _, v in strings(b.get("content")))
                hits = [f for f in assessment_fragments if f in normalize(text)]
                full_body = bool(assessment and normalize(assessment) in normalize(text))
                origin = observed_tools.get(other)
                path = origin[1].get('input', {}).get('file_path', '') if origin else ''
                command = origin[1].get('input', {}).get('command', '') if origin else ''
                transcript_recovery = path == '/tmp/reviewer-prose.txt' or ('subagents' in command and '.jsonl' in command)
                partial_body = bool(transcript_recovery and assessment_fragments and len(hits) / len(assessment_fragments) > .5)
                paths = re.findall(r"(?:/[^\s<>\"']+)?(?:artifacts|local)/strat-reviews/[^\s<>\"']+", text)
                if hits or paths:
                    alternate.append({"tool_use_id": other, "request_file": r["index"]["request_file"], "matching_fragment_count": len(hits), "full_assessment_body_observed": full_body, "partial_transcript_assessment_observed": partial_body, "source_path": path, "source_is_explicit_transcript_recovery": transcript_recovery, "sample_fragments": hits[:4], "review_paths": paths[:8]})
        writes = [{"name": b["name"], "file_path": b.get("input", {}).get('file_path'), "input_sha256": hashlib.sha256(json.dumps(b.get('input'),sort_keys=True).encode()).hexdigest(), "request_file": r["index"]["request_file"]} for r, b in child_calls if b["name"] in ("Write", "Edit")]
        final_path = review_paths.get(target)
        final_text = final_path.read_text() if final_path else ""
        final_norm = normalize(final_text)
        overlap = [f for f in assessment_fragments if f in final_norm]
        match = re.search(rf'(?im)^##? {role}[^\n]*\n', final_text)
        section = ''
        if match:
            end = re.search(r'(?m)^## ', final_text[match.end():])
            section = final_text[match.end():match.end() + end.start()] if end else final_text[match.end():]
        section_fragments = fragments(section)
        section_sources = []
        seen_sources = set()
        for r in receiving:
            for b in tool_results(r['request']):
                tid = b.get('tool_use_id')
                if tid in seen_sources: continue
                seen_sources.add(tid)
                incoming = normalize('\n'.join(v for _, v in strings(b.get('content'))))
                hits = [f for f in section_fragments if f in incoming]
                if len(hits) < 3: continue
                origin = observed_tools.get(tid)
                section_sources.append({'tool_use_id': tid, 'receiving_request_file': r['index']['request_file'], 'source_tool_index': origin[0] if origin else None, 'source_tool_name': origin[1]['name'] if origin else None, 'source_path': origin[1].get('input', {}).get('file_path') if origin else None, 'source_input_sha256': hashlib.sha256(json.dumps(origin[1].get('input'),sort_keys=True).encode()).hexdigest() if origin else None, 'matching_section_fragments': len(hits), 'total_section_fragments': len(section_fragments), 'fraction': len(hits) / len(section_fragments) if section_fragments else 0, 'sample_fragments': hits[:3], 'source_precedes_specialist_launch': origin[0]['timestamp'] < source['index']['timestamp'] if origin else None})
        substantive_return = bool(assessment and len(returned_text) > 700 and "Skill execution completed" not in returned_text)
        status = "delivered" if substantive_return else "unresolved because evidence is missing" if not assessment or first is None else "not observed"
        if not substantive_return and any(a['full_assessment_body_observed'] or a['partial_transcript_assessment_observed'] for a in alternate): status = 'delivered via another route'
        schemas = [t.get("input_schema") for r in child[:1] for t in r["request"].get("tools", []) if t["name"] == "StructuredOutput"]
        bodies = [t for r in child[:1] for t in user_texts(r["request"]) if "Base directory for this skill:" in t]
        target_lines = [line for t in bodies for line in t.splitlines() if target and re.search(rf"\b{re.escape(target)}\b", line)]
        rows.append({"tool_use_id": id, "role": role, "target": target, "launch_index": source["index"], "launch_input": launch["block"]["input"], "fork_agent_id": starts.get(id, {}).get("task_id"), "child_join_method": "exact task_started prompt in API request" if prompt else "role/expanded target/window; no task-start prompt available", "child_request_count": len(child), "first_child_index": child[0]["index"] if child else None, "assessment_source_index": assessment_source["index"] if assessment_source else None, "assessment_chars": len(assessment), "assessment_sha256": hashlib.sha256(assessment.encode()).hexdigest() if assessment else None, "last_child_index": last["index"] if last else None, "last_child_response_types": last_types, "child_structured_calls": sum(b["name"] == "StructuredOutput" for _, b in child_calls), "effective_child_schema": schemas[0] if schemas else None, "expanded_target_lines": target_lines, "first_receiving_index": first["index"] if first else None, "expected_return_chars": len(returned_text), "expected_return_preview": returned_text[:240], "delivery_status": status, "parent_matching_fragments": len(delivered_fragments), "alternate_delivery_candidates": alternate, "child_explicit_file_writes": writes, "published_review": str(final_path) if final_path else None, "published_review_sha256": sha256(final_path) if final_path else None, "published_section_present": bool(re.search(role, final_text, re.I)), "published_matching_fragments": len(overlap), "published_overlap_samples": overlap[:6], "incorporation_status": "unresolved: section/lexical overlap does not establish semantic fidelity"})
        rows[-1]['child_continuation_joins'] = join_steps
        rows[-1]['published_role_section_sources'] = sorted(section_sources, key=lambda s: s['fraction'], reverse=True)
    evidence_files = {str(api / "index.jsonl"), str(job / "artifacts/eval-result.json")}
    for r in records:
        if r['index']['query_source'].endswith(':strat-scorer'):
            for field in ('request_file','response_file'): evidence_files.add(str(api / r['index'][field]))
    for row in rows:
        for key in ("launch_index", "first_child_index", "assessment_source_index", "last_child_index", "first_receiving_index"):
            if row[key]:
                for field in ("request_file", "response_file"): evidence_files.add(str(api / row[key][field]))
        if row["published_review"]: evidence_files.add(row["published_review"])
        for item in row['published_role_section_sources']:
            evidence_files.add(str(api / item['receiving_request_file']))
            if item['source_tool_index']:
                for field in ('request_file', 'response_file'): evidence_files.add(str(api / item['source_tool_index'][field]))
        for item in row['child_continuation_joins']: evidence_files.add(str(api / item['request_file']))
    evidence = [{"path": p, "sha256": sha256(Path(p))} for p in sorted(evidence_files)]
    write_json(args.output, {"schema_version": 1, "job": str(job), "runner_sha256": sha256(Path(__file__)), "api_pair_count": len(records), "evidence": evidence, "calls": rows, "summary": dict(Counter(row["delivery_status"] for row in rows)), "limitations": ["Alternate paths are lexical candidates, not proof of semantic delivery", "A complete-looking section does not establish fidelity or fabrication", "Missing task-start prompts weaken joins outside the S1 stream archive"]})
    print(json.dumps({"calls": len(rows), "summary": dict(Counter(row["delivery_status"] for row in rows)), "output": str(args.output)}))


if __name__ == "__main__": main()
