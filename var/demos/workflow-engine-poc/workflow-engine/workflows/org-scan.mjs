/**
 * org-scan.mjs — clone an org's architecture context, then one scan agent
 * per checkout. The drop-in proof: a second workflow module, authored in
 * the Claude-Workflows shape, needing no provider or extension changes.
 *
 * Guards carried from the campaign findings:
 *  - cardinality cross-check: the clone agent's own reported count must
 *    agree with its list (an omitting agent must also falsify the count);
 *  - per-repo reality check: each scan result must name the repo it was
 *    asked about;
 *  - every agent result is schema-validated and journaled by the host.
 */

import fs from "node:fs";
import path from "node:path";

export const meta = {
	name: "org-scan",
	description: "Clone an org's architecture context and summarize each checkout",
};

const Clone = {
	type: "object",
	properties: {
		root: { type: "string" },
		repo_count: { type: "integer", minimum: 1 },
		repos: {
			type: "array",
			items: {
				type: "object",
				properties: { name: { type: "string" }, path: { type: "string" } },
				required: ["name", "path"],
				additionalProperties: false,
			},
		},
	},
	required: ["root", "repo_count", "repos"],
	additionalProperties: false,
};

const Scan = {
	type: "object",
	properties: {
		repo: { type: "string" },
		summary: { type: "string" },
		concerns: { type: "array", items: { type: "string" } },
	},
	required: ["repo", "summary"],
	additionalProperties: false,
};

export default async function run(wf, input) {
	const org = input.org;
	if (!org || typeof org !== "string" || !org.trim()) {
		throw new Error("org-scan: input.org is required");
	}

	// Phase 1 — discovery: one agent runs the context fetch and reports the
	// checkout folders (schema-validated; paths are the agent's report).
	const clone = await wf.agent(
		`CLONE ${org}\nRun fetch-architecture-context.sh for the org and return every checkout folder it created; copy paths verbatim from the tool output.`,
		{ label: "org-clone", schema: Clone },
	);

	// Cardinality cross-check: the list and the reported count must agree.
	if (clone.repos.length !== clone.repo_count) {
		throw new Error(`org-scan: clone lists ${clone.repos.length} repos but reports count ${clone.repo_count} — refusing to fan out over a disagreeing manifest`);
	}

	// Phase 2 — fan-out: one scan agent per checkout, bounded concurrency.
	const scans = await wf.parallel(
		clone.repos.map((repo) => () =>
			wf.agent(
				`SCAN ${repo.name} at ${repo.path}\nRead the checkout and produce an architecture summary with any concerns.`,
				{ label: `scan:${repo.name}`, schema: Scan, cwd: path.resolve(clone.root, repo.name.replace(/^.*\//, "")) },
			),
		),
		{ concurrency: 2 },
	);

	// Per-repo reality check: each scan must be about the repo it was given.
	for (let i = 0; i < clone.repos.length; i++) {
		if (scans[i].repo !== clone.repos[i].name) {
			throw new Error(`org-scan: scan ${i} is about ${JSON.stringify(scans[i].repo)}, expected ${JSON.stringify(clone.repos[i].name)}`);
		}
	}

	// Phase 3 — completeness + artifact.
	fs.mkdirSync(path.join(wf.runDir, "results"), { recursive: true });
	for (const scan of scans) {
		fs.writeFileSync(path.join(wf.runDir, "results", `${scan.repo}.json`), JSON.stringify(scan) + "\n");
	}
	const artifact = {
		org,
		root: clone.root,
		scanned: scans.length,
		expected: clone.repos.length,
		complete: scans.length === clone.repos.length,
		repos: clone.repos.map((r) => r.name),
		scans,
		summary: `${scans.length}/${clone.repos.length} repos scanned`,
	};
	fs.writeFileSync(path.join(wf.runDir, "artifact.json"), JSON.stringify(artifact, null, "\t") + "\n");
	if (!artifact.complete) {
		throw new Error(`org-scan: incomplete — ${scans.length}/${clone.repos.length} repos scanned`);
	}
	return artifact;
}
