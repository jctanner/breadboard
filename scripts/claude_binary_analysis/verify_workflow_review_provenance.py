#!/usr/bin/env python3
"""Verify compact archive observations against original API pairs and hashes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_plugin_experiments import sha256
from run_subagent_skill_experiments import strings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docs", type=Path)
    args = parser.parse_args()
    total = 0
    for name, expected in {"s1-opus": {"not observed": 10, "delivered": 2}, "s2-opus": {"delivered": 12}, "s1-glm": {"delivered via another route": 4}, "s2-glm": {"delivered": 4}}.items():
        j = json.loads((args.docs / f"claude-code-2.1.296-workflow-{name}-provenance.json").read_text())
        assert j["summary"] == expected, (name, j["summary"])
        for evidence in j["evidence"]: assert sha256(Path(evidence["path"])) == evidence["sha256"]
        api = Path(j['job']) / 'api-dumps'
        ids = set()
        for call in j['calls']:
            assert call['tool_use_id'] not in ids; ids.add(call['tool_use_id'])
            assert call['child_request_count'] and call['assessment_chars'] > 700
            assert call['expanded_target_lines']
            launch = json.loads((api / call['launch_index']['response_file']).read_text())
            assert any(b.get('id') == call['tool_use_id'] and b.get('name') == 'Skill' for b in launch['content'])
            receiving = json.loads((api / call['first_receiving_index']['request_file']).read_text())
            results = [b for m in receiving['messages'] for b in (m['content'] if isinstance(m['content'],list) else []) if b.get('tool_use_id') == call['tool_use_id']]
            assert len(results) == 1 and not results[0].get('is_error')
            last = call['last_child_response_types']
            if name.startswith('s1'):
                parent = json.loads((api / call['launch_index']['request_file']).read_text())
                parent_schema = next(t['input_schema'] for t in parent['tools'] if t['name'] == 'StructuredOutput')
                assert parent_schema == call['effective_child_schema']
                if call['delivery_status'] != 'delivered':
                    assert 'tool_use:StructuredOutput' in last
                    assert 'Skill execution completed' in json.dumps(results[0])
            else:
                assert call['effective_child_schema'] is None and call['child_structured_calls'] == 0
            if name == 's1-opus' and call['delivery_status'] == 'delivered':
                assert call['role'] == 'testability' and call['target'] in ('RHAISTRAT-1','RHAISTRAT-2')
                assert 'tool_use:StructuredOutput' not in last
            if name == 's1-glm':
                assert any(a['full_assessment_body_observed'] or a['partial_transcript_assessment_observed'] for a in call['alternate_delivery_candidates'])
            assert call['published_review'] and call['published_section_present']
        total += len(j['calls'])
    assert total == 32
    print('Verified 32 archived specialist calls and referenced source hashes')


if __name__ == '__main__': main()
