# Design User And Subagent Plugin System

## Goal

Design a Shuheng plugin system that lets users package reusable agent behavior and attach it either globally or to individual subagents, while preserving the governed harness baseline: strong Orchestrator, restricted subagents, single-writer enforcement, approval gates, artifact refs, and auditable state.

## What I Already Know

- User wants users to customize their own agents for different jobs.
- User also wants per-subagent custom plugins, not only global plugins.
- The repo already has per-agent dedicated skills:
  - `SubAgentRuntime.skill_refs`.
  - `/agent skill ...` commands.
  - `agent.create` can include `skills`, `skill`, or `skill_refs`.
  - `agent.skill.update` / `agent.skills.update`.
  - Context packs include `skill_pack.schema_version == "subagent.skill_pack.v1"` only for the target subagent.
- Current dedicated skills resolve local `SKILL.md` or markdown files from skill roots including Shuheng, Codex, OMP, repo, and system skill folders.
- Current spec explicitly says dedicated skills are not a global skill registry UI, not auto-installed third-party skills, and not permission grants.
- Existing policy gates already prove:
  - A custom skill marker appears only in the target agent context.
  - Other subagents do not receive the target-only skill body.
  - Outside paths are not injected.
  - Secret Vault subagent metadata keeps skill refs encrypted with subagent metadata.
  - Dedicated skills do not bypass role policy or approval gates.
- AgentBridge exists as a thin facade for local agent clients and must not become the owner of memory, approval, scheduler, or artifact governance.

## Working Definition

For this feature, a plugin should be a local package that can contribute one or more of:

- Agent templates: reusable agent name/profile/role/default skills/default dashboard/default model hints.
- Dedicated skill packs: prompt/SOP/knowledge files attachable to specific subagents.
- Workflow prompts: reusable task templates that create/delegate work through existing `shuheng-control.v2` / `agenttask.v2` paths.
- Read-only metadata surfaces: summaries for `/plugins`, `/agent info`, Web Console, gateway/A2A cards.

It should not initially mean arbitrary Python/JS execution unless we explicitly choose that as a later, approval-gated phase.

## Recommended MVP Direction

Start with a declarative local plugin registry, no arbitrary plugin code execution.

Decision for planning unless user overrides: MVP uses declarative plugins only. Tool-executing plugins and arbitrary code plugins are later phases because they need a separate permission, approval, sandbox, and audit model.

Suggested plugin package shape:

```text
plugin-id/
  plugin.json
  skills/<skill-id>/SKILL.md
  agents/<agent-template-id>.json
  workflows/<workflow-id>.md
  README.md
```

Suggested manifest skeleton:

```json
{
  "schema_version": "shuheng.plugin.v1",
  "id": "research-pack",
  "name": "Research Pack",
  "version": "0.1.0",
  "description": "Reusable research agents and SOPs.",
  "scopes": ["global", "subagent"],
  "contributes": {
    "skills": [
      {"id": "source-review", "path": "skills/source-review/SKILL.md"}
    ],
    "agent_templates": [
      {
        "id": "evidence-researcher",
        "role": "researcher",
        "profile": "Collect evidence and cite source quality.",
        "skill_refs": ["plugin://research-pack/skills/source-review"]
      }
    ],
    "workflows": [
      {"id": "compare-sources", "path": "workflows/compare-sources.md"}
    ]
  },
  "permissions": {
    "requested_tools": ["read", "web"],
    "write_policy": "none"
  }
}
```

## Requirements Evolving

- Plugins must be installable or discoverable from Shuheng-owned local roots, likely `~/.shuheng/plugins` first.
- Plugins must have stable ids and manifest validation.
- Plugins must expose summaries and contribution lists without injecting all plugin body text globally.
- Per-subagent plugin assignment must be stored on that subagent, similar to `skill_refs`.
- Existing `skill_refs` should remain compatible; plugin-provided skills can resolve to `plugin://<plugin-id>/skills/<skill-id>`.
- Agent templates should create subagents through the existing `create_subagent(...)` / `agent.create` path rather than bypassing role normalization and persistence rules.
- Workflow prompts should run through existing main Orchestrator or subagent task delegation, not as hidden side effects.
- Plugin permissions must be descriptive/declared in MVP and must not override role write policy, policy gates, Secret Vault isolation, or single-writer locks.
- Unresolved, disabled, or invalid plugins must stay visible as metadata but inject no prompt body.
- Plugin registry reads should be cacheable and not perform heavy disk scans on every TUI repaint.

## Open Questions

- Closed: MVP is declarative-only. No plugin code/tool execution in this slice.
- Closed: Plugin-provided skills are represented as normalized `skill_refs` first, using refs like `plugin://research-pack/skills/source-review`; no separate `plugin_refs` field is required for MVP.
- Closed: First user-facing UI is TUI command surface plus registry/query metadata. Web Console can consume the registry later but is not required for MVP.

## Acceptance Criteria Evolving

- [x] A plugin manifest contract is documented in `.trellis/spec/backend/agent-control-protocol.md`.
- [x] A local plugin registry can list valid plugins and validation errors.
- [x] A plugin-provided skill can be attached to exactly one subagent and appears only in that subagent context pack.
- [x] A plugin-provided agent template can create a subagent without bypassing role normalization or approval policy.
- [x] Invalid plugin refs are visible but do not inject content.
- [x] Tests/policy gates cover plugin discovery, manifest validation, per-subagent scoping, no arbitrary outside path injection, and no permission bypass.
- [x] First implementation exposes `/plugins`, `/plugin info <id>`, `/agent plugin add <agent> <plugin-skill-ref>`, `/agent plugin remove <agent> <plugin-skill-ref>`, and `/agent plugin list <agent>` as aliases over the same per-agent skill scoping mechanism.

## Implementation Notes

- Added `src/shuheng/plugins.py` as a pure declarative registry module for local `plugin.json` discovery, manifest validation, stable `plugin://...` refs, metadata formatting, and manifest-declared local path resolution.
- Added `SHUHENG_PLUGINS_DIR = os.path.join(SHUHENG_HOME, "plugins")` plus cached `user_plugin_registry(...)` wrappers in `app.py`.
- Wired plugin skills into existing per-agent `skill_refs`, context packs, and `/agent plugin ...` commands without introducing a separate `plugin_refs` field.
- Added `/plugins`, `/plugin info`, `/plugin template`, and `/plugin create` command surfaces. Agent templates still flow through `create_subagent(...)` and `set_subagent_skill_refs(...)`.
- Documented the executable contract in `.trellis/spec/backend/agent-control-protocol.md` under `Scenario: Declarative User Plugins`.
- Added `tests/test_plugins.py`, plugin ref normalization coverage in `tests/test_subagent_store.py`, and policy gates for module ownership, target-only plugin skill injection, outside-path rejection, template creation, and permission non-bypass.

## Definition Of Done

- PRD converges on MVP scope.
- Code-spec is added before implementation.
- Implementation is split into small slices, starting with manifest parsing and registry before UI.
- Full Goal-quality gates remain green for each implementation slice.

## Out Of Scope For MVP Unless Explicitly Chosen

- Marketplace/remote plugin install.
- Arbitrary Python/JS plugin execution.
- Plugin-provided native tools that mutate files, deploy, spend money, or access secrets.
- Cross-machine distribution.
- Replacing the existing dedicated skill system.
- Letting one subagent read another subagent's plugin body.

## Technical Notes

- Existing dedicated skill spec: `.trellis/spec/backend/agent-control-protocol.md` Scenario `Per-Agent Dedicated Skills`.
- Existing skill resolution code: `src/shuheng/app.py` around `subagent_skill_roots()`, `subagent_skill_file_for_ref(...)`, `subagent_skill_pack_for_refs(...)`, and `set_subagent_skill_refs(...)`.
- Existing normalization owner: `src/shuheng/subagent_store.py::normalize_subagent_skill_refs(...)`.
- Existing policy gate: `scripts/check_policy_gates.py::assert_subagent_dedicated_skills_are_agent_scoped`.
- Existing bridge boundary: `src/shuheng/agent_bridge.py` is explicitly a thin facade and should not own plugin governance.
