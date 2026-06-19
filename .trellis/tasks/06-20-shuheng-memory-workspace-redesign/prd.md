# Shuheng Memory Workspace Redesign

## Goal

Redesign Shuheng memory from a loose copied `memory/` tree into a project-workspace-oriented memory system. The new design should unify session history, global/project memory, subagent memory, harness ledgers, context packs, memory candidates, and L4 raw-session archives under a coherent Shuheng-owned model that can hydrate OMP/Codex/other agents through governed context packs.

## What I already know

* The user wants the memory system redesigned around project workspaces, with duplicated or scattered state unified.
* The user specifically likes the existing L4 memory mode and wants it used better, not discarded.
* Shuheng currently owns default state under `~/.shuheng`.
* Legacy bootstrap already copies old GenericAgent history and memory into `~/.shuheng` without mutating the old source tree.
* On this machine, `load_history()` can see 99 sidebar rows after bootstrap and `memory_inventory()` sees 491 memory entries.
* Current `~/.shuheng/memory` mixes several concerns in one folder: global memory files, SOP/tool files, subagent memories, `agent_harness`, `secret_vault`, tutorial knowledge, and `L4_raw_sessions`.
* Current context pack code already models L0-L8 layers in `context_layers_for_task()`, but the persisted filesystem layout does not match those conceptual layers.
* Current `memory_hydration_pack()` hydrates subagent profile/memory, recent mail, and static project-harness facts, but does not select project-workspace scoped memory from a workspace index.
* Current `memory_candidate.v1` already has `scope`, `type`, `ttl`, `confidence`, `dedupe_key`, duplicate/conflict fields, and human approval.
* Current L4 implementation under `~/.shuheng/memory/L4_raw_sessions` includes monthly zip archives, `all_histories.txt`, `compress_session.py`, and `salient_mining_sop.md`.
* Current L4 script still assumes the old GenericAgent raw directory (`temp/model_responses`) and can delete raw files when run with `--run`; that is too risky for a Shuheng-owned workspace design.
* Existing architecture baseline favors external long-term memory, context packs, artifact refs, progress ledgers, and candidate-only memory writes.

## Assumptions (temporary)

* "Project workspace" should mean a durable memory namespace keyed by a repo/project/work objective, not just the current Git checkout.
* The MVP should not rewrite every old memory file in place; it should add a canonical index/manifest and migration path first.
* The L4 layer should become a cold-storage source with searchable/indexed summaries and recovery refs, not a separate manual folder that agents ignore.
* The system should preserve the current rule that runtimes and plugins never write long-term memory directly.

## Open Questions

* None blocking for MVP.

## Requirements

* Shuheng must keep owning all state under `~/.shuheng` by default.
* Memory must be organized by stable scopes: global/user, project/workspace, agent/subagent, task/session, artifact/ledger, and L4 raw/cold history.
* Project memory should be first-class and retrievable by the context pack builder.
* Existing L4 archives must remain usable and traceable back to exact zip members/session ids.
* The redesign must not directly delete old history, old memory, or live session logs.
* Long-term memory writes must remain candidate-only and approval-gated.
* OMP, Codex, Claude Code, and future plugins should consume the same Shuheng memory/context API instead of reading files directly.
* MVP scope is **workspace index plus context pack integration**.
* Automatic L4 mining into long-term memory is deferred; MVP only creates/refers to L4 cold-history indexes so agents can cite exact archived sessions.
* Workspace identity is manually created and selected by the user, not automatically inferred from the current repo/workdir by default.
* Shuheng must persist the current selected workspace in its own state under `~/.shuheng`.
* Context packs include workspace memory only when a workspace is selected; no selected workspace should be explicit and safe.
* The MVP workspace control surface is slash-command driven (`/workspace list`, `/workspace new`, `/workspace select`, `/workspace current`) so it is testable before adding memory-viewer UI.

## Acceptance Criteria

* [x] A documented Shuheng memory workspace layout exists with clear ownership and scope boundaries.
* [x] A machine-readable workspace/project memory index exists or is generated.
* [x] `memory_inventory()` reports the new workspace structure without losing legacy memory visibility.
* [x] `memory_context_get` / context pack generation can include relevant project-workspace memory.
* [x] L4 archives have a Shuheng-owned index with refs to monthly zip members and optional existing summaries.
* [x] L4 processing is non-destructive by default and does not delete active raw session files.
* [x] Existing memory candidates and approval gates remain intact.
* [x] Regression tests cover migration/index generation, context pack hydration, and L4 index behavior.
* [x] Workspace creation, selection, listing, and selected-workspace persistence are covered by regression tests.
* [x] With no selected workspace, context packs do not silently inject project memory and clearly report that no workspace is active.

## Definition of Done

* Tests added or updated in `scripts/check_policy_gates.py`.
* `python3 -m py_compile src/ga_tui/app.py scripts/check_policy_gates.py` passes.
* `python3 -m compileall -q src scripts` passes.
* `python3 scripts/check_policy_gates.py` passes.
* `git diff --check` passes.
* `shuheng-check --root /home/vimalinx/Programs/GenericAgent` passes.
* `.trellis/spec/backend/agent-control-protocol.md` documents the executable memory workspace contract.
* Rollback path is clear: old files remain untouched and new generated index/layout files can be ignored or removed.

## Out of Scope (explicit)

* Replacing the current approval system.
* Letting OMP or any runtime directly write approved long-term memory.
* Deleting or moving old GenericAgent data destructively.
* Building semantic vector search in the first step unless required by the chosen MVP scope.
* Automatically mining L4 archives into approved long-term facts in the first implementation pass.
* Encrypting all normal memory; Secret Vault remains the encrypted path for secret contexts.

## Technical Notes

* Current core constants live in `src/ga_tui/app.py`: `SHUHENG_HOME`, `SHUHENG_MEMORY_DIR`, `MODEL_RESPONSES_DIR`, `L4_RAW_SESSIONS_DIR`, `SUBAGENTS_DIR`, `AGENT_HARNESS_DIR`, `SECRET_VAULT_DIR`.
* Current memory UI source is `memory_inventory()` in `src/ga_tui/app.py`.
* Current context pack path is `memory_hydration_pack()`, `context_layers_for_task()`, `build_context_pack()`, and `ohmypi_tui_memory_context_get()` in `src/ga_tui/app.py`.
* Current memory write governance path is `build_memory_candidate()`, `queue_curated_memory_candidate()`, `append_memory_candidate_record()`, and approval handling in `src/ga_tui/app.py`.
* Current bridge surface is `src/ga_tui/agent_bridge.py` with `memory_context_get` and `memory_candidate_submit`.
* Current L4 assets are under `~/.shuheng/memory/L4_raw_sessions`: monthly zip files, `all_histories.txt`, `compress_session.py`, and `salient_mining_sop.md`.
* Current L4 zip inventory on this machine: `2026-04.zip` has 1 member, `2026-05.zip` has 53 members, and `2026-06.zip` has 17 members.
* Current L4 SOP asks for `history_insight/` outputs with activity knowledge, emotion events, and incremental markers, but this is not integrated into Shuheng context packs yet.
* Relevant spec section: `.trellis/spec/backend/agent-control-protocol.md` scenario "Shuheng-Owned Storage And Archive-Backed Sidebar Rows".
* Relevant architecture baseline: `docs/agent-harness-architecture.md` L0-L8 context layering and memory candidate governance.

## Candidate Design Direction

Chosen MVP direction: **Workspace Manifest + Layered Memory Index + Context Pack Integration**.

* Keep physical legacy-compatible files where they are for now.
* Add a canonical generated index under `~/.shuheng/workspaces/`.
* Represent each workspace/project with a manifest containing identity, roots, session refs, L4 refs, memory files, subagents, artifact refs, and candidate refs.
* Teach context pack generation to hydrate project memory by the manually selected workspace id before falling back to generic project-harness facts.
* Convert L4 from "manual archive folder" into a cold memory layer with an index, while preserving exact source refs.

## Decision (ADR-lite)

**Context**: The existing Shuheng state tree now lives under `~/.shuheng`, but memory is still scattered across global memory files, subagent folders, harness ledgers, raw session history, and L4 archives. Agents need a governed way to hydrate project-relevant memory without scraping random files.

**Decision**: The MVP will implement a workspace/project memory index and connect it to context pack generation. It will not yet perform automatic L4 fact mining into long-term memory.

**Consequences**: This gives OMP and other runtimes useful project-scoped memory quickly while preserving current approval gates. L4 becomes a traceable cold source now, and deeper L4 mining can be added later as a candidate-producing Memory Curator workflow.

## Expansion Sweep

### Future evolution

* Workspace identities can later cover repo projects, content projects, study tracks, client work, and remote agent teams.
* The same workspace index can later power search, project dashboards, phone remote control, and cross-agent context routing.

### Related scenarios

* Sidebar history, `/memory`, `memory_context_get`, OMP append prompt, and agent bridge metadata should agree on the same storage boundaries.
* Legacy bootstrap, L4 archival, and future memory compaction should use the same non-destructive import/index conventions.

### Failure and edge cases

* Incorrect project inference could leak unrelated memory into a task; context packs need explicit workspace refs and exclusion notes.
* L4 mining can produce stale or over-broad facts; mined outputs should become candidates or scoped summaries with source refs, not direct global facts.
* Multiple projects may share the same repo path or move paths; manifests need stable ids plus path aliases.

## Decision (ADR-lite): Manual Workspace Selection

**Context**: Automatic repo/workdir inference is convenient but can leak unrelated project memory into a task, especially when different projects share paths, symlinks, remote agents, or cross-repo objectives.

**Decision**: Shuheng workspaces are created and selected manually for this MVP. The active workspace is persisted in Shuheng state and is the only workspace whose memory is hydrated into context packs by default.

**Consequences**: This is safer and easier to reason about. The trade-off is one extra user action before project memory appears. Automatic suggestions can be added later as suggestions only, not as implicit context injection.

## Decision (ADR-lite): Slash Command MVP

**Context**: Workspace control needs a small, verifiable product entry before deeper memory-viewer UI work.

**Decision**: The first implementation exposes workspace operations through TUI slash commands: list, current, new, and select.

**Consequences**: This keeps the MVP narrow and testable. The memory viewer can later reuse the same workspace API instead of carrying separate state logic.
