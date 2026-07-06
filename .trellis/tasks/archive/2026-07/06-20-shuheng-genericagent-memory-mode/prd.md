# Align Shuheng Memory With GenericAgent Mode

## Goal

Make Shuheng-owned memory behave like GenericAgent's layered memory model for the embedded OMP runtime. The main mental model should be GenericAgent-style L0-L4 memory injection, not a workspace selector. Workspace inference can remain as provenance/observability, but it must not be the primary memory hydration path.

## Requirements

- Initialize and preserve Shuheng-owned layered memory files under `~/.shuheng/memory`.
- Use `global_mem_insight.txt` as the L1 prompt/index layer and `global_mem.txt` as the L2 fact layer.
- Provide an L0 `memory_management_sop.md` under Shuheng memory so long-term memory writes follow the GenericAgent action-verified rules.
- Preserve L3 discoverability through `~/.shuheng/memory/*.md` and `*.py` files.
- Preserve L4 as `~/.shuheng/memory/L4_raw_sessions/` plus non-destructive indexes/refs.
- Inject a `[Memory]` section analogous to GenericAgent `get_global_memory()` into context packs and OMP append prompt text.
- Keep long-term writes candidate-only and approval-gated; OMP/plugins must not directly mutate approved long-term memory.
- Keep workspace inference only as secondary provenance/project context when useful, not as the required or leading memory mode.
- Avoid mutating the user's system OMP install or legacy GenericAgent memory destructively.

## Acceptance Criteria

- [ ] A fresh Shuheng home gets initialized with L0/L1/L2 and L4 directory under `~/.shuheng/memory`.
- [ ] Existing Shuheng memory files are not overwritten.
- [ ] Context packs include a GA-style `[Memory]` prompt section referencing Shuheng paths.
- [ ] `format_context_pack_for_prompt()` surfaces layered Shuheng memory before workspace details.
- [ ] OMP append prompt generation includes layered Shuheng memory and redacts sensitive-looking content.
- [ ] Workspace memory remains available only as provenance/secondary project context.
- [ ] L4 handling remains index-only and does not rewrite raw session archives.
- [ ] `scripts/check_policy_gates.py` covers layered memory initialization, prompt injection, redaction, and candidate governance.
- [ ] Python compile/check scripts pass.

## Definition of Done

- Code changes are implemented in the Shuheng/OMP integration paths.
- Policy gate tests are updated and passing.
- The backend spec records the GA-style Shuheng layered memory contract.
- The implementation is compared against `docs/agent-harness-architecture.md`.
- Changes are committed after verification.

## Technical Approach

1. Add app-layer helpers that ensure Shuheng layered memory files exist and build a GenericAgent-like memory prompt from Shuheng-owned files.
2. Update context-pack memory hydration and formatted prompts to include the layered memory section as the main memory contract.
3. Update OMP memory prompt generation to consume the same Shuheng layered memory semantics instead of presenting only generic GA/TUI guidance.
4. Keep automatic workspace creation/indexing intact for now, but downgrade it to project provenance in prompt wording and tests.
5. Update tests/specs to remove workspace-primary assertions and require the layered memory mode.

## Decision (ADR-lite)

Context: The previous implementation introduced automatic Shuheng workspaces, but the user clarified that the target is "like GenericAgent's memory mode" rather than a workspace selector.

Decision: Make GenericAgent-style L0-L4 layered memory the primary runtime memory abstraction, stored under Shuheng home. Workspace remains an optional project provenance layer.

Consequences: This moves OMP closer to GenericAgent's useful memory behavior while keeping Shuheng as the owner of state, governance, history, candidates, and UI integration.

## Out of Scope

- Directly editing the system OMP installation.
- Directly writing approved facts from OMP responses into L1/L2/L3 without candidate approval.
- Mining L4 raw sessions into approved memory in this task.
- Removing workspace commands entirely; they can stay as observability if they do not dominate the memory prompt.

## Technical Notes

- GenericAgent initializes `memory/global_mem.txt` and `memory/global_mem_insight.txt` in `agentmain.py`.
- GenericAgent `ga.py:get_global_memory()` injects `cwd`, `[Memory]`, a fixed structure string, and L1 insight text.
- GenericAgent `do_start_long_term_update()` uses `memory/memory_management_sop.md` as L0.
- Current Shuheng code paths to modify include `memory_hydration_pack()`, `context_layers_for_task()`, `build_context_pack()`, `format_context_pack_for_prompt()`, `ohmypi_tui_memory_context_get()`, `memory_inventory()`, and `write_ohmypi_memory_prompt()`.
- Current policy tests contain workspace-primary expectations in `assert_shuheng_workspace_memory_context()` and OMP prompt checks.
