import * as fs from "node:fs";
import * as path from "node:path";
import type { CustomToolFactory } from "@oh-my-pi/pi-coding-agent";

type BridgePayload = {
	action: string;
	args?: Record<string, unknown>;
	endpoint?: string;
};

function envPath(name: string): string {
	return String(process.env[name] ?? "").trim();
}

function findRepoRoot(): string {
	const configured = envPath("SHUHENG_REPO") || envPath("GA_TUI_REPO") || envPath("GA_TUI_ROOT");
	if (configured) return path.resolve(configured);

	let current = import.meta.dir;
	for (let i = 0; i < 8; i += 1) {
		if (fs.existsSync(path.join(current, "src", "ga_tui", "agent_bridge.py"))) {
			return current;
		}
		const parent = path.dirname(current);
		if (parent === current) break;
		current = parent;
	}
	return path.resolve(import.meta.dir, "../../..");
}

function pythonPathWithRepo(repoRoot: string): string {
	const src = path.join(repoRoot, "src");
	const existing = envPath("PYTHONPATH");
	return existing ? `${src}:${existing}` : src;
}

function bridgeCommand(payload: BridgePayload): { command: string; args: string[]; cwd: string } {
	const repoRoot = findRepoRoot();
	const python = envPath("GA_TUI_BRIDGE_PYTHON") || "python3";
	return {
		command: "env",
		args: [
			`PYTHONPATH=${pythonPathWithRepo(repoRoot)}`,
			python,
			"-m",
			"ga_tui.agent_bridge",
			"call",
			JSON.stringify(payload),
		],
		cwd: repoRoot,
	};
}

function parseBridgeJson(stdout: string): Record<string, unknown> {
	const line = stdout
		.split(/\r?\n/)
		.map(item => item.trim())
		.filter(Boolean)
		.at(-1);
	if (!line) {
		throw new Error("Shuheng bridge returned empty stdout.");
	}
	const parsed = JSON.parse(line);
	if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
		throw new Error("Shuheng bridge returned non-object JSON.");
	}
	return parsed as Record<string, unknown>;
}

function renderBridgeResult(result: Record<string, unknown>): string {
	return JSON.stringify(result, null, 2);
}

async function callBridge(pi: Parameters<CustomToolFactory>[0], payload: BridgePayload, signal?: AbortSignal) {
	const command = bridgeCommand(payload);
	const result = await pi.exec(command.command, command.args, {
		cwd: command.cwd,
		timeout: 30000,
		signal,
	});
	const parsed = parseBridgeJson(result.stdout);
	if (result.code !== 0 && parsed.status !== "error") {
		throw new Error(result.stderr || `Shuheng bridge exited with code ${result.code}`);
	}
	return parsed;
}

const factory: CustomToolFactory = pi => {
	const z = pi.zod;

	return [
		{
			name: "ga_tui_context_get",
			label: "Shuheng Context",
			description:
				"Read a Shuheng-managed context pack for the current project or a target subagent. This is read-only and returns an artifact ref plus bounded context JSON.",
			parameters: z.object({
				target: z.string().optional().describe("Optional Shuheng subagent id or unique name."),
				objective: z.string().describe("Objective that the context pack should support."),
				task_id: z.string().optional().describe("Optional task id for context-pack provenance."),
				parent_task_id: z.string().optional().describe("Optional parent task id."),
			}),

			async execute(_toolCallId, params, _onUpdate, _ctx, signal) {
				const result = await callBridge(
					pi,
					{
						action: "memory_context_get",
						args: {
							target: params.target ?? "",
							objective: params.objective,
							task_id: params.task_id ?? "",
							parent_task_id: params.parent_task_id ?? "",
						},
					},
					signal,
				);
				return {
					content: [{ type: "text", text: renderBridgeResult(result) }],
					details: result,
				};
			},
		},
		{
			name: "ga_tui_memory_candidate_submit",
			label: "Shuheng Memory Candidate",
			description:
				"Submit a durable memory candidate to Shuheng. This never writes long-term memory directly; Shuheng validates it and queues human approval.",
			parameters: z.object({
				target: z.string().describe("Target Shuheng persistent subagent id or unique name."),
				statement: z.string().describe("Durable, verified memory candidate statement."),
				evidence_ref: z.string().optional().describe("Optional artifact/runtime evidence reference."),
				task_id: z.string().optional().describe("Optional related Shuheng task id."),
			}),

			async execute(_toolCallId, params, _onUpdate, _ctx, signal) {
				const result = await callBridge(
					pi,
					{
						action: "memory_candidate_submit",
						args: {
							target: params.target,
							statement: params.statement,
							evidence_ref: params.evidence_ref ?? "runtime://provider/ohmypi/plugin",
							task_id: params.task_id ?? "",
						},
					},
					signal,
				);
				return {
					content: [{ type: "text", text: renderBridgeResult(result) }],
					details: result,
				};
			},
		},
	];
};

export default factory;
