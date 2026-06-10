# Group LLM Models By Provider

## Goal

Change the unified `/model` panel from broad protocol/ecosystem tabs such as `Anthropic`, `OpenAI`, and `Other` to concrete provider-based grouping, so configured models are easier to browse by actual supplier such as OpenAI, DeepSeek, Kimi, Qwen, Zhipu, MiniMax, StepFun, or custom provider domains.

## What I Already Know

* The user wants the current LLM classification changed to provider-based classification.
* The current `/model` command is already the single visible model command.
* `/llm` and `/models` are hidden compatibility aliases for the unified `/model` panel.
* Current model tabs come from `model_entry_category()`, which delegates to `provider_category()` and therefore groups by protocol-like broad categories: `Anthropic`, `OpenAI`, and `Other`.
* GenericAgent provides concrete provider templates through `assets.configure_mykey.LLM_PROVIDERS`; the TUI imports them as `CONFIG_PROVIDERS`.
* Provider templates include `id`, display `name`, protocol `type`, `template.name`, `template.apibase`, and `model_choices`.
* Configured entries loaded from `mykey.py` contain at least `name`, `apibase`, and `model`, but not necessarily the original provider template id.
* Existing `/model` behavior to preserve: current-session switching, default selection, recent model jumping, add/edit/delete, model extraction, single-model test, batch validation, reload, and hidden alias routing.

## Assumptions

* "按供应商分类" means tabs should be concrete suppliers/providers, not broad protocol categories.
* Matching should prefer known provider templates by normalized `apibase`, then by configured `name`, then fall back to URL host or a generic custom provider label.
* Tabs should show configured providers plus a short common-provider set.
* Common providers should be derived from the existing template order, initially: Anthropic, OpenAI, DeepSeek, Kimi, Qwen, and Zhipu.
* Other known providers should appear only when the user has configured at least one model/API for that provider.
* Provider labels should be human-friendly but short enough for terminal tabs; long template names can be shortened where needed.
* Existing config storage in `mykey.py` should remain unchanged.

## Open Questions

* None.

## Requirements

* Keep `/model` as the only visible model command.
* Keep `/llm` and `/models` as hidden compatible aliases.
* Replace broad model categories with concrete provider tabs in the `/model` manager.
* Show tabs for configured providers plus common providers, not every template provider.
* Derive provider identity from existing config and provider template metadata without changing `mykey.py`.
* Preserve all existing model manager actions and keybindings.
* Preserve add/edit provider template category behavior unless a code simplification naturally reuses the new provider-group helper safely.
* Update policy-gate checks to assert provider-based grouping.
* Update the executable code-spec for the changed `/model` grouping contract.

## Acceptance Criteria

* [x] A DeepSeek entry and an OpenAI entry no longer both appear under a single `OpenAI` tab.
* [x] Known providers are grouped by concrete provider identity using `LLM_PROVIDERS` metadata where possible.
* [x] Tabs include configured providers plus common providers: Anthropic, OpenAI, DeepSeek, Kimi, Qwen, and Zhipu.
* [x] Non-common template providers appear only when configured.
* [x] Unknown/custom OpenAI-compatible endpoints still get a stable provider tab from config name or endpoint host.
* [x] Switching tabs keeps selection safe after add/edit/delete/reload/validation.
* [x] Current `/model` management actions still work.
* [x] `/llm` and `/models` remain hidden aliases and do not reappear in help/completion/README.
* [x] `scripts/check_policy_gates.py` covers the provider grouping behavior and passes.
* [x] `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` passes.

## Definition Of Done

* Tests or smoke checks are updated for provider grouping.
* Syntax and project smoke checks pass.
* `.trellis/spec/backend/agent-control-protocol.md` is updated because the command surface grouping contract changed.
* The implementation is compared against `docs/agent-harness-architecture.md` before finish.
* Work is committed, the task is archived, and the session journal is recorded.

## Out Of Scope

* Changing `mykey.py` schema.
* Adding network discovery beyond existing model extraction/probe paths.
* Changing actual LLM request behavior.
* Reworking provider add/edit form UX beyond what is needed to keep classification consistent.
* Changing subagent default-model behavior except preserving it.

## Technical Notes

* Primary implementation file: `src/ga_tui/app.py`.
* Current category helpers: `provider_category()`, `provider_categories()`, `model_entry_category()`, `model_entry_categories()`, `model_entry_indices_for_category()`.
* Current model panel: `draw_model_manager()` and `open_model_manager()`.
* Current provider templates: imported from GenericAgent `assets.configure_mykey.LLM_PROVIDERS` as `CONFIG_PROVIDERS`.
* Current regression area: `scripts/check_policy_gates.py` around model command and model config assertions.
* Current spec section to update: `.trellis/spec/backend/agent-control-protocol.md` scenario `Unified Model Command Surface`.
