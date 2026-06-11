# Make Provider List Vertical

## Goal

Change the `/model` model-manager supplier selector from a single horizontal `供应商 Tabs: A / B / C` line into a vertical provider list, so many providers remain readable and the model list has a clearer left-provider/right-model layout.

## What I Already Know

* The user asked to make the supplier/provider list vertical.
* The current `/model` panel already groups models by concrete providers.
* Current rendering uses one horizontal line: `供应商 Tabs: ...`.
* Current navigation uses `Tab`, left/right, `[`, and `]` to switch provider categories.
* Current up/down navigation moves through models in the active provider.
* The change should preserve all existing model actions: current-session switch, default, recent, add/edit/delete, extraction, testing, validation, reload, and hidden aliases.

## Assumptions

* "竖列" means a left-side vertical provider rail and a right-side model list inside the same popup.
* Up/down should continue to select models, not providers. Provider switching remains on `Tab` / left/right / bracket keys to avoid changing muscle memory.
* The provider rail should scroll independently if there are more providers than visible rows.
* Empty-provider messages should appear in the right model area.

## Open Questions

* None.

## Requirements

* Render provider names as a vertical list on the left of the `/model` popup.
* Render model rows on the right of the provider list.
* Highlight the active provider in the vertical list.
* Preserve existing provider switching keys.
* Preserve existing model selection keys and model-management actions.
* Preserve provider-based grouping semantics from the previous task.
* Keep `/model` as the only visible model command and keep `/llm` / `/models` hidden aliases.
* Update tests/specs if the model panel layout contract changes.

## Acceptance Criteria

* [x] `/model` no longer renders supplier tabs as a single horizontal provider line.
* [x] The model manager renders a vertical provider rail with active-provider highlighting.
* [x] The model list renders next to the provider rail and remains filtered by the selected provider.
* [x] Up/down still moves through models in the selected provider.
* [x] Tab/left/right/bracket keys still switch providers safely.
* [x] Existing policy gate checks pass.
* [x] `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` passes.

## Definition Of Done

* Syntax and project smoke checks pass.
* The executable command/layout contract is updated if needed.
* The implementation is compared against `docs/agent-harness-architecture.md` before finish.
* Work is committed, the task is archived, and the session journal is recorded.

## Out Of Scope

* Changing provider grouping identity.
* Changing `mykey.py` schema.
* Changing actual LLM request behavior.
* Reworking provider add/edit form template categories.
* Adding mouse support for provider selection.

## Technical Notes

* Primary implementation file: `src/ga_tui/app.py`.
* Current render function: `draw_model_manager()`.
* Current loop/navigation: `open_model_manager()`.
* Current regression area: `scripts/check_policy_gates.py` model command/provider grouping checks.
* Current spec section: `.trellis/spec/backend/agent-control-protocol.md` scenario `Unified Model Command Surface`.
