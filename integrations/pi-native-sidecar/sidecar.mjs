#!/usr/bin/env node

import { createHash } from "node:crypto";
import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import readline from "node:readline";
import { pathToFileURL } from "node:url";

const PROVIDER_ID = "pi-native";
const PROTOCOL_VERSION = "shuheng.pi_native.sidecar.v1";
const EVENT_SCHEMA = "shuheng.pi_native_event.v1";
const BUILD_SCHEMA = "shuheng.agent_build.v1";
const SDK_PACKAGE = "@earendil-works/pi-coding-agent";
const SDK_VERSION = "0.80.6";
const MOCK_MODE = process.env.SHUHENG_PI_NATIVE_MOCK === "1";
const MAX_STRING_CHARS = 12000;
const MAX_COLLECTION_ITEMS = 100;
const ISOLATION = Object.freeze({
  explicit_resource_loader: true,
  implicit_extensions: false,
  implicit_context_files: false,
  implicit_prompt_templates: false,
  implicit_skills: false,
  implicit_themes: false,
  global_pi_home: false,
  global_omp_home: false,
  in_memory_auth: true,
  in_memory_settings: true,
  in_memory_session: true,
  fresh_process_per_run: true,
  os_syscall_sandbox: false
});

let activeRun = null;
let sdkPromise = null;

function asObject(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function asString(value) {
  return typeof value === "string" ? value : "";
}

function stringList(value) {
  if (!Array.isArray(value)) return [];
  return [...new Set(value.map((item) => asString(item).trim()).filter(Boolean))];
}

function safeSegment(value, fallback) {
  const clean = asString(value).trim().replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  return clean || fallback;
}

function jsonSafe(value, depth = 0, seen = new Set()) {
  if (value === null || value === undefined) return value ?? null;
  if (typeof value === "string") {
    return value.length <= MAX_STRING_CHARS ? value : `${value.slice(0, MAX_STRING_CHARS)}...[truncated]`;
  }
  if (typeof value === "number" || typeof value === "boolean") return value;
  if (typeof value === "bigint") return value.toString();
  if (typeof value !== "object") return String(value);
  if (depth >= 6) return "[max-depth]";
  if (seen.has(value)) return "[circular]";
  seen.add(value);
  if (Array.isArray(value)) {
    const result = value.slice(0, MAX_COLLECTION_ITEMS).map((item) => jsonSafe(item, depth + 1, seen));
    seen.delete(value);
    return result;
  }
  const result = {};
  for (const [key, item] of Object.entries(value).slice(0, MAX_COLLECTION_ITEMS)) {
    result[String(key)] = jsonSafe(item, depth + 1, seen);
  }
  seen.delete(value);
  return result;
}

function writeFrame(frame) {
  process.stdout.write(`${JSON.stringify(jsonSafe(frame))}\n`);
}

function writeResponse(id, command, success, data = {}, error = "") {
  writeFrame({
    schema_version: EVENT_SCHEMA,
    id: asString(id),
    type: "response",
    command,
    success: Boolean(success),
    data,
    error: asString(error)
  });
}

function emitTask(taskId, type, fields = {}) {
  writeFrame({
    schema_version: EVENT_SCHEMA,
    type,
    provider_id: PROVIDER_ID,
    task_id: taskId,
    ...fields
  });
}

function errorText(error) {
  if (error instanceof Error) return `${error.name}: ${error.message}`;
  return String(error || "unknown error");
}

function normalizedDigest(value) {
  return asString(value).trim().toLowerCase().replace(/^sha256:/, "");
}

function decodeFrozenBase64(value, label) {
  const encoded = asString(value).trim();
  if (!encoded || !/^[A-Za-z0-9+/]*={0,2}$/.test(encoded) || encoded.length % 4 !== 0) {
    throw new Error(`${label} has invalid frozen content_base64`);
  }
  const content = Buffer.from(encoded, "base64");
  if (content.toString("base64") !== encoded) {
    throw new Error(`${label} has non-canonical frozen content_base64`);
  }
  return content;
}

function buildToolRecords(build) {
  const builtins = [];
  const custom = [];
  for (const item of Array.isArray(build.builtin_tools) ? build.builtin_tools : []) {
    const name = typeof item === "string" ? item : asString(asObject(item).name);
    if (name.trim()) builtins.push(name.trim());
  }
  for (const item of Array.isArray(build.custom_tools) ? build.custom_tools : []) {
    if (item && typeof item === "object" && !Array.isArray(item)) custom.push(item);
  }
  for (const item of Array.isArray(build.tools) ? build.tools : []) {
    if (typeof item === "string") {
      builtins.push(item);
      continue;
    }
    const record = asObject(item);
    if (!asString(record.name).trim()) continue;
    if (record.kind === "custom" || record.content_base64) custom.push(record);
    else builtins.push(asString(record.name).trim());
  }
  return {
    builtins: [...new Set(builtins)],
    custom
  };
}

function normalizeRun(frame) {
  const taskId = asString(frame.task_id).trim();
  if (!taskId) throw new Error("run.task_id is required");
  const workspaceRoot = path.resolve(asString(frame.workspace_root).trim());
  const agentDir = path.resolve(asString(frame.agent_dir).trim());
  if (!asString(frame.workspace_root).trim()) throw new Error("run.workspace_root is required");
  if (!asString(frame.agent_dir).trim()) throw new Error("run.agent_dir is required");

  const build = asObject(frame.build);
  if (build.schema_version !== BUILD_SCHEMA) {
    throw new Error(`run.build.schema_version must be ${BUILD_SCHEMA}`);
  }
  const buildDigest = asString(build.digest || build.build_digest).trim();
  if (!buildDigest) throw new Error("run.build.digest is required");
  if (!("system_prompt" in build) || typeof build.system_prompt !== "string") {
    throw new Error("run.build.system_prompt must be an explicit string");
  }

  const records = buildToolRecords(build);
  const declared = new Set([...records.builtins, ...records.custom.map((item) => asString(item.name).trim())]);
  const effectiveTools = stringList(frame.effective_tools);
  const undeclared = effectiveTools.filter((name) => !declared.has(name));
  if (undeclared.length > 0) {
    throw new Error(`effective Tool names are absent from the frozen Build: ${undeclared.join(", ")}`);
  }

  return {
    taskId,
    prompt: asString(frame.prompt),
    workspaceRoot,
    agentDir,
    buildDigest,
    build,
    model: asObject(frame.model),
    effectiveTools,
    authorizedCustomTools: records.custom.filter((item) => effectiveTools.includes(asString(item.name).trim())),
    mock: asObject(frame.mock)
  };
}

async function materializeResources(run, sdk) {
  const digestDir = safeSegment(normalizedDigest(run.buildDigest), "build");
  const resourcesRoot = path.join(run.agentDir, "resources", digestDir);
  const skills = [];
  const prompts = [];

  for (const [index, raw] of (Array.isArray(run.build.skills) ? run.build.skills : []).entries()) {
    const item = asObject(raw);
    const name = safeSegment(item.name, `skill-${index + 1}`);
    if (typeof item.content !== "string") throw new Error(`Skill ${name} is missing frozen content`);
    const baseDir = path.join(resourcesRoot, "skills", name);
    const filePath = path.join(baseDir, "SKILL.md");
    await mkdir(baseDir, { recursive: true });
    await writeFile(filePath, item.content, "utf8");
    skills.push({
      name,
      description: asString(item.description),
      filePath,
      baseDir,
      sourceInfo: sdk.createSyntheticSourceInfo(filePath, { source: "sdk" }),
      disableModelInvocation: Boolean(item.disable_model_invocation)
    });
  }

  const rawPrompts = Array.isArray(run.build.prompt_templates) ? run.build.prompt_templates : [];
  for (const [index, raw] of rawPrompts.entries()) {
    const item = asObject(raw);
    const name = safeSegment(item.name, `prompt-${index + 1}`);
    if (typeof item.content !== "string") throw new Error(`Prompt template ${name} is missing frozen content`);
    const baseDir = path.join(resourcesRoot, "prompts");
    const filePath = path.join(baseDir, `${name}.md`);
    await mkdir(baseDir, { recursive: true });
    await writeFile(filePath, item.content, "utf8");
    prompts.push({
      name,
      description: asString(item.description),
      argumentHint: asString(item.argument_hint) || undefined,
      content: item.content,
      sourceInfo: sdk.createSyntheticSourceInfo(filePath, { source: "sdk" }),
      filePath
    });
  }
  return { skills, prompts, resourcesRoot };
}

async function loadCustomTools(run, resourcesRoot) {
  const loaded = [];
  for (const item of run.authorizedCustomTools) {
    const name = asString(item.name).trim();
    const expectedDigest = normalizedDigest(item.sha256 || item.digest || item.source_digest);
    if (!/^[a-f0-9]{64}$/.test(expectedDigest)) {
      throw new Error(`Custom Tool ${name} requires a SHA-256 digest`);
    }
    const content = decodeFrozenBase64(item.content_base64, `Custom Tool ${name}`);
    if (Number.isInteger(item.size) && item.size >= 0 && content.length !== item.size) {
      throw new Error(`Custom Tool ${name} size mismatch`);
    }
    const actualDigest = createHash("sha256").update(content).digest("hex");
    if (actualDigest !== expectedDigest) {
      throw new Error(`Custom Tool ${name} digest mismatch`);
    }
    const logicalPath = asString(item.path).trim();
    const extension = path.extname(logicalPath).toLowerCase();
    if (![".js", ".mjs", ".ts", ".mts"].includes(extension)) {
      throw new Error(`Custom Tool ${name} must use .js, .mjs, .ts, or .mts source`);
    }
    const toolDir = path.join(resourcesRoot, "tools");
    const sourcePath = path.join(toolDir, `${safeSegment(name, "tool")}${extension}`);
    await mkdir(toolDir, { recursive: true });
    await writeFile(sourcePath, content);
    const moduleUrl = pathToFileURL(sourcePath);
    moduleUrl.searchParams.set("shuheng_build", normalizedDigest(run.buildDigest) || run.buildDigest);
    const module = await import(moduleUrl.href);
    const exportName = asString(item.export_name).trim() || "default";
    let candidate = module[exportName];
    if (typeof candidate === "function") {
      candidate = await candidate(Object.freeze({
        build_digest: run.buildDigest,
        tool: Object.freeze({ ...item })
      }));
    }
    const definitions = Array.isArray(candidate) ? candidate : [candidate];
    const definition = definitions.find((entry) => asString(asObject(entry).name).trim() === name);
    if (!definition) throw new Error(`Custom Tool module did not export definition ${name}`);
    loaded.push(definition);
  }
  return loaded;
}

async function loadSdk() {
  if (!sdkPromise) {
    sdkPromise = import(SDK_PACKAGE).then((sdk) => {
      const required = [
        "AuthStorage",
        "DefaultResourceLoader",
        "ModelRegistry",
        "SessionManager",
        "SettingsManager",
        "createAgentSession",
        "createSyntheticSourceInfo"
      ];
      const missing = required.filter((name) => !sdk[name]);
      if (missing.length > 0) throw new Error(`Pi SDK exports missing: ${missing.join(", ")}`);
      return sdk;
    });
  }
  return sdkPromise;
}

function assistantText(message) {
  const record = asObject(message);
  if (record.role !== "assistant") return "";
  if (typeof record.content === "string") return record.content;
  if (!Array.isArray(record.content)) return "";
  return record.content
    .filter((item) => asObject(item).type === "text")
    .map((item) => asString(asObject(item).text))
    .join("");
}

function latestAssistantText(session) {
  const messages = Array.isArray(session.messages) ? session.messages : [];
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const text = assistantText(messages[index]);
    if (text) return text;
  }
  return "";
}

function subscribeToSession(run, session) {
  let streamedText = "";
  const unsubscribe = session.subscribe((event) => {
    if (event.type === "message_update") {
      const update = asObject(event.assistantMessageEvent);
      if (update.type === "text_delta") {
        const delta = asString(update.delta);
        streamedText += delta;
        emitTask(run.taskId, "text_delta", { status: "streaming", delta });
      }
      return;
    }
    if (event.type === "tool_execution_start") {
      emitTask(run.taskId, "tool_started", {
        status: "running",
        tool_call_id: asString(event.toolCallId),
        tool_name: asString(event.toolName),
        payload: { args: jsonSafe(event.args) }
      });
      return;
    }
    if (event.type === "tool_execution_update") {
      emitTask(run.taskId, "tool_updated", {
        status: "running",
        tool_call_id: asString(event.toolCallId),
        tool_name: asString(event.toolName),
        payload: { partial_result: jsonSafe(event.partialResult) }
      });
      return;
    }
    if (event.type === "tool_execution_end") {
      emitTask(run.taskId, "tool_finished", {
        status: event.isError ? "failed" : "completed",
        tool_call_id: asString(event.toolCallId),
        tool_name: asString(event.toolName),
        error: event.isError ? "Pi Tool execution failed" : "",
        payload: { result: jsonSafe(event.result) }
      });
    }
  });
  return {
    unsubscribe,
    text: () => streamedText
  };
}

function positiveInteger(value, fallback) {
  const parsed = Number.parseInt(String(value ?? ""), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function explicitHeaders(value) {
  const result = {};
  for (const [key, item] of Object.entries(asObject(value))) {
    if (typeof item === "string") result[String(key)] = item;
  }
  return result;
}

function configureRunModel(run, authStorage, modelRegistry) {
  const provider = asString(run.model.provider).trim();
  const modelId = asString(run.model.id || run.model.model_id).trim();
  if (!provider || !modelId) throw new Error("run.model.provider and run.model.id are required");

  const apiKey = asString(run.model.api_key).trim();
  if (apiKey) authStorage.setRuntimeApiKey(provider, apiKey);
  const baseUrl = asString(run.model.base_url).trim();
  const api = asString(run.model.api).trim();
  const current = modelRegistry.find(provider, modelId);
  if (!current || baseUrl || api) {
    const config = {
      ...(baseUrl ? { baseUrl } : {}),
      ...(apiKey ? { apiKey } : {}),
      ...(api ? { api } : {}),
      headers: explicitHeaders(run.model.headers),
      authHeader: run.model.auth_header !== false,
      models: [{
        id: modelId,
        name: asString(run.model.name).trim() || modelId,
        ...(api ? { api } : {}),
        ...(baseUrl ? { baseUrl } : {}),
        reasoning: Boolean(run.model.reasoning),
        input: ["text", "image"],
        supportsTools: true,
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: positiveInteger(run.model.context_window, 128000),
        maxTokens: positiveInteger(run.model.max_tokens, 16384),
        headers: explicitHeaders(run.model.headers)
      }]
    };
    modelRegistry.registerProvider(provider, config, "shuheng-agent-project");
  }
  const model = modelRegistry.find(provider, modelId);
  if (!model) throw new Error(`Pi model is unavailable: ${provider}/${modelId}`);
  return model;
}

async function createLiveSession(run) {
  const sdk = await loadSdk();
  await mkdir(run.agentDir, { recursive: true, mode: 0o700 });
  const authStorage = sdk.AuthStorage.inMemory();
  const modelRegistry = sdk.ModelRegistry.inMemory(authStorage);
  const model = configureRunModel(run, authStorage, modelRegistry);

  const settingsManager = sdk.SettingsManager.inMemory({
    compaction: { enabled: false },
    retry: { enabled: false }
  });
  const resources = await materializeResources(run, sdk);
  const customTools = await loadCustomTools(run, resources.resourcesRoot);
  const resourceLoader = new sdk.DefaultResourceLoader({
    cwd: run.workspaceRoot,
    agentDir: run.agentDir,
    settingsManager,
    additionalExtensionPaths: [],
    additionalSkillPaths: [],
    additionalPromptTemplatePaths: [],
    additionalThemePaths: [],
    extensionFactories: [],
    noExtensions: true,
    noSkills: true,
    noPromptTemplates: true,
    noThemes: true,
    noContextFiles: true,
    systemPrompt: run.build.system_prompt,
    appendSystemPrompt: [],
    skillsOverride: () => ({ skills: resources.skills, diagnostics: [] }),
    promptsOverride: () => ({ prompts: resources.prompts, diagnostics: [] }),
    themesOverride: () => ({ themes: [], diagnostics: [] }),
    agentsFilesOverride: () => ({ agentsFiles: [] }),
    systemPromptOverride: () => run.build.system_prompt,
    appendSystemPromptOverride: () => []
  });
  await resourceLoader.reload();

  return sdk.createAgentSession({
    cwd: run.workspaceRoot,
    agentDir: run.agentDir,
    model,
    thinkingLevel: asString(run.model.thinking_level).trim() || "off",
    authStorage,
    modelRegistry,
    resourceLoader,
    noTools: "all",
    tools: run.effectiveTools,
    customTools,
    sessionManager: sdk.SessionManager.inMemory(run.workspaceRoot),
    settingsManager
  });
}

function abortError() {
  const error = new Error("task aborted");
  error.name = "AbortError";
  return error;
}

async function delay(milliseconds, signal) {
  const duration = Math.max(0, Number(milliseconds) || 0);
  if (duration === 0) {
    if (signal.aborted) throw abortError();
    return;
  }
  await new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, duration);
    signal.addEventListener("abort", () => {
      clearTimeout(timer);
      reject(abortError());
    }, { once: true });
  });
}

async function executeMock(run, signal) {
  if (run.mock.fail) throw new Error(asString(run.mock.error) || "deterministic mock failure");
  const response = asString(run.mock.response) || `pi-native mock ${run.taskId}: ${run.prompt}`;
  const chunks = Array.isArray(run.mock.chunks) && run.mock.chunks.length > 0
    ? run.mock.chunks.map((item) => asString(item))
    : [response];
  for (const chunk of chunks) {
    await delay(run.mock.delay_ms, signal);
    if (signal.aborted) throw abortError();
    emitTask(run.taskId, "text_delta", { status: "streaming", delta: chunk });
  }
  return response;
}

async function executeRun(frame) {
  let run;
  try {
    run = normalizeRun(frame);
  } catch (error) {
    const taskId = asString(frame.task_id);
    emitTask(taskId, "task_failed", { status: "failed", error: errorText(error) });
    return;
  }
  const controller = new AbortController();
  activeRun = { taskId: run.taskId, controller, session: null };
  emitTask(run.taskId, "task_started", {
    status: "working",
    payload: {
      build_digest: run.buildDigest,
      effective_tools: run.effectiveTools,
      mode: MOCK_MODE ? "mock" : "live"
    }
  });

  let session = null;
  let subscription = null;
  let terminal = null;
  try {
    if (MOCK_MODE) {
      const text = await executeMock(run, controller.signal);
      if (controller.signal.aborted) throw abortError();
      terminal = { type: "task_completed", fields: { status: "completed", message: text } };
    } else {
      const created = await createLiveSession(run);
      session = created.session;
      if (activeRun?.taskId === run.taskId) activeRun.session = session;
      subscription = subscribeToSession(run, session);
      if (controller.signal.aborted) throw abortError();
      await session.prompt(run.prompt, { expandPromptTemplates: false, source: "rpc" });
      if (controller.signal.aborted) throw abortError();
      const text = latestAssistantText(session) || subscription.text();
      terminal = { type: "task_completed", fields: { status: "completed", message: text } };
    }
  } catch (error) {
    if (controller.signal.aborted || error?.name === "AbortError") {
      terminal = {
        type: "task_aborted",
        fields: { status: "aborted", message: "Pi-native task aborted." }
      };
    } else {
      terminal = { type: "task_failed", fields: { status: "failed", error: errorText(error) } };
    }
  } finally {
    try {
      subscription?.unsubscribe();
    } catch {}
    try {
      session?.dispose();
    } catch {}
    try {
      await rm(run.agentDir, { recursive: true, force: true });
    } catch {}
    if (activeRun?.taskId === run.taskId) activeRun = null;
  }
  emitTask(run.taskId, terminal.type, terminal.fields);
}

async function handleDescribe(frame) {
  writeResponse(frame.id, "describe", true, {
    protocol_version: PROTOCOL_VERSION,
    event_schema: EVENT_SCHEMA,
    provider_id: PROVIDER_ID,
    sdk_package: SDK_PACKAGE,
    sdk_version: SDK_VERSION,
    commands: ["describe", "health", "run", "abort"],
    one_task_at_a_time: true,
    isolation: ISOLATION,
    mode: MOCK_MODE ? "mock" : "live"
  });
}

async function handleHealth(frame) {
  if (MOCK_MODE) {
    writeResponse(frame.id, "health", true, {
      status: "ok",
      mode: "mock",
      sdk_package: SDK_PACKAGE,
      sdk_version: SDK_VERSION
    });
    return;
  }
  try {
    await loadSdk();
    writeResponse(frame.id, "health", true, {
      status: "ok",
      mode: "live",
      sdk_package: SDK_PACKAGE,
      sdk_version: SDK_VERSION
    });
  } catch (error) {
    writeResponse(frame.id, "health", false, {
      status: "unavailable",
      mode: "live",
      sdk_package: SDK_PACKAGE,
      sdk_version: SDK_VERSION
    }, errorText(error));
  }
}

async function handleRun(frame) {
  if (activeRun) {
    emitTask(asString(frame.task_id), "task_failed", {
      status: "failed",
      error: `Pi-native sidecar is already running task ${activeRun.taskId}`
    });
    return;
  }
  void executeRun(frame);
}

async function handleAbort(frame) {
  const requestedTaskId = asString(frame.task_id).trim();
  if (!activeRun || (requestedTaskId && activeRun.taskId !== requestedTaskId)) {
    writeResponse(frame.id, "abort", false, { status: "idle" }, "no matching active task");
    return;
  }
  const current = activeRun;
  current.controller.abort();
  try {
    await current.session?.abort();
  } catch {}
  writeResponse(frame.id, "abort", true, { status: "aborting", task_id: current.taskId });
}

async function handleFrame(frame) {
  const record = asObject(frame);
  const command = asString(record.type).trim();
  if (command === "describe") return handleDescribe(record);
  if (command === "health") return handleHealth(record);
  if (command === "run") return handleRun(record);
  if (command === "abort") return handleAbort(record);
  writeResponse(record.id, command || "unknown", false, {}, `unsupported command: ${command || "<empty>"}`);
}

writeFrame({
  schema_version: EVENT_SCHEMA,
  type: "sidecar_ready",
  provider_id: PROVIDER_ID,
  status: "ready",
  protocol_version: PROTOCOL_VERSION,
  mode: MOCK_MODE ? "mock" : "live"
});

const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
input.on("line", (line) => {
  const text = line.trim();
  if (!text) return;
  let frame;
  try {
    frame = JSON.parse(text);
  } catch (error) {
    writeResponse("", "parse", false, {}, `invalid JSON: ${errorText(error)}`);
    return;
  }
  void handleFrame(frame).catch((error) => {
    writeResponse(asString(asObject(frame).id), asString(asObject(frame).type), false, {}, errorText(error));
  });
});

input.on("close", () => {
  activeRun?.controller.abort();
});

process.on("SIGTERM", () => {
  activeRun?.controller.abort();
  process.exit(0);
});
