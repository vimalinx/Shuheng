# Auto Shuheng Workspace Selection

## Goal

Change Shuheng workspace memory from a manual-selection model to an automatic project/workdir model. Context packs should automatically infer the relevant workspace, create or refresh its manifest/index when needed, and hydrate project memory without requiring the user to run `/workspace select`.

## What I already know

* The user explicitly corrected the previous design: "不弄手动就是自动" means the product should not require manual workspace selection.
* The previous commit `4187d48` added `~/.shuheng/workspaces/<workspace_id>/manifest.json`, `memory.md`, `index.json`, `l4_index.json`, `/workspace` commands, context-pack hydration, and policy-gate tests.
* Current implementation still treats `active.json` and `selection_mode:"manual"` as the source of truth.
* Current spec `.trellis/spec/backend/agent-control-protocol.md` has an active "Manual Shuheng Workspace Memory" scenario that now conflicts with the corrected requirement.
* The architecture baseline still wants external long-term memory, context packs, artifact refs, L4 refs, and candidate-only writes.

## Requirements

* Workspace identity must be automatic by default, derived from the current process working directory's git root when available, otherwise from the working directory itself.
* Shuheng should create or refresh the inferred workspace manifest/index automatically during context-pack generation.
* Generated workspace ids must be stable and collision-resistant for moved or similarly named directories, using a slug plus a short path hash.
* Context packs must include workspace memory by default unless the context is Secret Vault or the root cannot be resolved.
* `active.json` must no longer be the required source of truth for context hydration.
* `/workspace current` and `/workspace list` should remain useful as observability/debug commands.
* `/workspace select` and `/workspace clear` are not part of the automatic workspace command surface.
* L4 archive indexing remains non-destructive and index-only.
* Long-term memory writes remain candidate-only and approval-gated.
* The active backend spec should describe automatic workspace memory, not manual selection.

## Acceptance Criteria

* [x] Context pack generation automatically creates or loads a workspace based on the current git root/workdir.
* [x] A fresh temporary Shuheng home with no `active.json` still produces `workspace_context.included:true`.
* [x] Workspace manifests include `selection_mode:"auto"` or equivalent automatic provenance, plus the inferred root alias.
* [x] `/workspace current` reports the inferred automatic workspace.
* [x] Tests no longer assert that missing manual selection blocks workspace hydration.
* [x] L4 zip refs are still indexed as `l4://<archive>/<member>` without modifying archive bytes.
* [x] Secret Vault contexts still do not hydrate normal workspace memory.
* [x] Backend spec removes the manual-selection contract and replaces it with automatic workspace inference.

## Definition of Done

* `python3 -m py_compile src/ga_tui/app.py scripts/check_policy_gates.py` passes.
* `python3 -m compileall -q src scripts` passes.
* `python3 scripts/check_policy_gates.py` passes.
* `git diff --check` passes.
* `shuheng-check --root /home/vimalinx/Programs/GenericAgent` passes.
* Changes are committed without amending `4187d48`.

## Technical Approach

* Add workspace root inference helpers:
  * `current_workspace_root()` from `os.getcwd()` plus git-root discovery.
  * `workspace_id_for_root(root)` using basename slug plus hash.
  * `ensure_auto_workspace(root)` to create/refresh manifest, memory, index, and L4 index.
* Change `workspace_context_payload()` to call automatic inference instead of reading `active.json`.
* Keep state files only as observability (`last_auto_workspace`), not as the source required for hydration.
* Adjust `/workspace` commands to expose current/list/refresh.
* Update tests and spec to remove manual-selection assertions.

## Decision (ADR-lite)

**Context**: Manual workspace selection prevented accidental cross-project context, but the product expectation is that Shuheng automatically understands the active project.

**Decision**: The automatic inferred workspace is the default and authoritative source for context hydration. Manual selection is removed from the active hydration path.

**Consequences**: This improves usability and makes new sessions immediately useful. The main risk is wrong-root inference, so manifests keep root aliases and the `/workspace current` command must show exactly what root is being used.

## Out of Scope

* Semantic vector search.
* Automatic L4 fact mining into approved long-term memory.
* Direct memory writes by OMP/Codex/plugins.
* Moving or deleting old workspace files destructively.

## Technical Notes

* Main implementation: `src/ga_tui/app.py`.
* Regression tests: `scripts/check_policy_gates.py`.
* Spec update: `.trellis/spec/backend/agent-control-protocol.md`.
* Previous PRD for the manual approach: `.trellis/tasks/06-20-shuheng-memory-workspace-redesign/prd.md`.
