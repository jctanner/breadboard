"""Small response helpers for isolated Anthropic-compatible API fixtures."""
from __future__ import annotations

import json


def respond(handler, request: dict, blocks: list[dict], index: int, *, usage: dict | None = None) -> None:
    usage = usage or {"input_tokens": 10, "output_tokens": 10}
    stop = "tool_use" if any(b["type"] == "tool_use" for b in blocks) else "end_turn"
    result = {"id": f"msg_fixture_{index}", "type": "message", "role": "assistant", "model": request.get("model", "fixture"), "content": blocks, "stop_reason": stop, "stop_sequence": None, "usage": usage}
    if request.get("stream"):
        events = [("message_start", {"type": "message_start", "message": {**result, "content": [], "stop_reason": None, "usage": {"input_tokens": usage["input_tokens"], "output_tokens": 0}}})]
        for i, block in enumerate(blocks):
            start = {**block, "input": {}} if block["type"] == "tool_use" else {"type": "text", "text": ""}
            delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])} if block["type"] == "tool_use" else {"type": "text_delta", "text": block["text"]}
            events.extend([("content_block_start", {"type": "content_block_start", "index": i, "content_block": start}), ("content_block_delta", {"type": "content_block_delta", "index": i, "delta": delta}), ("content_block_stop", {"type": "content_block_stop", "index": i})])
        events.extend([("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None}, "usage": {"output_tokens": usage["output_tokens"]}}), ("message_stop", {"type": "message_stop"})])
        encoded = "".join(f"event: {event}\ndata: {json.dumps(value)}\n\n" for event, value in events).encode()
        mime = "text/event-stream"
    else:
        encoded, mime = json.dumps(result).encode(), "application/json"
    handler.send_response(200)
    handler.send_header("Content-Type", mime)
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)
