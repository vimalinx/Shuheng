# Shuheng Pi-native Sidecar

This integration is a narrow JSONL stdio process boundary around the pinned
upstream Pi Coding Agent SDK. It runs one task at a time and exposes four input
commands: `describe`, `health`, `run`, and `abort`.

The `run` command receives a frozen `shuheng.agent_build.v1` record, an explicit
workspace and runtime directory, and the effective Tool names granted by the
Shuheng control plane. The sidecar disables implicit Extensions, context files,
Prompt templates, Themes, and global/project Skill discovery. It constructs the
session only from the Build's system prompt, inline Skills, inline Prompt
templates, and explicitly listed custom Tool modules.

Shuheng starts a fresh sidecar process for every assignment. Frozen resources
are materialized in a mode-`0700` operating-system temporary directory, removed
before the terminal event, and never reused by another Build. This prevents
module caches, global mutations, listeners, and SDK state from crossing runs.

Custom Tool records use this shape:

```json
{
  "name": "project_lookup",
  "path": "tools/project_lookup.mjs",
  "content_base64": "<frozen AgentBuild bytes>",
  "sha256": "<hex>",
  "export_name": "default"
}
```

The exported value must be a Pi `ToolDefinition`, an array containing the named
definition, or a function returning either form. A module is imported only when
its name is also present in the effective Tool allowlist, and its SHA-256 digest
is checked before the frozen bytes are materialized inside the isolated runtime
directory and imported. Mutable Agent Project source paths are never reopened at
run time.

The executable grant is a local-code trust decision, not an OS syscall sandbox.
The MVP strips unrelated host credentials and exposes no implicit Pi/OMP
resources, but an authorized Tool still runs as Node code within its one-run
sidecar process. Only grant Tool source you trust.

Set `SHUHENG_PI_NATIVE_MOCK=1` for deterministic protocol tests that do not load
the SDK, contact a model provider, or use network access.

For live local use, install the pinned dependency beside this file with
`npm install --omit=dev` (or the equivalent Bun command). Shuheng passes its
configured default model, endpoint, headers, and API key only in the transient
runtime payload; the key is installed into Pi's in-memory auth storage and is
not copied to the task ledger, Run Manifest, trace, or Agent Project files.

If Shuheng has no model configuration, the narrow environment fallback is
`SHUHENG_PI_NATIVE_MODEL_PROVIDER`, `SHUHENG_PI_NATIVE_MODEL`, optional
`SHUHENG_PI_NATIVE_BASE_URL`, `SHUHENG_PI_NATIVE_API`, and
`SHUHENG_PI_NATIVE_API_KEY`.
