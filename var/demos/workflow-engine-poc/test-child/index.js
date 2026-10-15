/**
 * test-child — scripted child provider for the workflow-engine POC.
 *
 * Registers provider "test-child" with model "echo": a fully deterministic,
 * zero-inference classifier. Given a prompt "CLASSIFY <item>" it replies
 * with JSON {"item": "...", "bucket": "..."} where the bucket is a stable
 * hash of the item text. Used as the Layer 1-3 child so the whole stack
 * runs offline and byte-deterministically.
 */

import { createAssistantMessageEventStream } from "@earendil-works/pi-ai/compat";

const BUCKETS = ["alpha", "beta", "gamma"];

function classify(item) {
	let h = 0;
	for (const ch of item) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
	return BUCKETS[h % BUCKETS.length];
}

function lastUserText(messages) {
	for (let i = messages.length - 1; i >= 0; i--) {
		const m = messages[i];
		if (m.role !== "user") continue;
		if (typeof m.content === "string") return m.content;
		if (Array.isArray(m.content)) {
			return m.content.filter((b) => b && b.type === "text").map((b) => b.text).join("\n");
		}
		return "";
	}
	return "";
}

function zeroUsage() {
	return {
		input: 0,
		output: 0,
		cacheRead: 0,
		cacheWrite: 0,
		totalTokens: 0,
		cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
	};
}

function assistant(content, stopReason, extra) {
	return {
		role: "assistant",
		content,
		api: "test-child-stream",
		provider: "test-child",
		model: "echo",
		usage: zeroUsage(),
		stopReason,
		timestamp: Date.now(),
		...extra,
	};
}

export default function (pi) {
	pi.registerProvider("test-child", {
		// baseUrl is required by the registration form but never contacted.
		baseUrl: "http://127.0.0.1:9",
		api: "test-child-stream",
		// Placeholder credential: streamSimple performs no HTTP, so no real key exists.
		apiKey: "local-no-inference",
		models: [
			{
				id: "echo",
				name: "Echo (scripted, no inference)",
				reasoning: false,
				input: ["text"],
				cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
				contextWindow: 100000,
				maxTokens: 4096,
			},
		],
		streamSimple(model, context) {
			const stream = createAssistantMessageEventStream();
			const text = lastUserText(context.messages);
			const match = /^CLASSIFY\s+([^\n]+)/.exec(text.trim());
			if (!match) {
				const error = assistant([], "error", { errorMessage: `test-child: prompt must be "CLASSIFY <item>", got: ${JSON.stringify(text.slice(0, 80))}` });
				stream.push({ type: "error", reason: "error", error });
				stream.end();
				return stream;
			}
			const item = match[1].trim();
			const out = JSON.stringify({ item, bucket: classify(item) });
			const final = assistant([{ type: "text", text: out }], "stop");
			stream.push({ type: "start", partial: assistant([], "pending") });
			stream.push({ type: "text_start", contentIndex: 0, partial: assistant([{ type: "text", text: "" }], "pending") });
			stream.push({ type: "text_delta", contentIndex: 0, delta: out, partial: assistant([{ type: "text", text: out }], "pending") });
			stream.push({ type: "text_end", contentIndex: 0, content: out, partial: final });
			stream.push({ type: "done", reason: "stop", message: final });
			stream.end();
			return stream;
		},
	});
}
