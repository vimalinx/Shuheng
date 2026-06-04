# Extract Control Protocol From App.py

## Goal

Move the current `ga-control.v2` protocol definition and parsing/coercion helpers out of the monolithic `src/ga_tui/app.py` into a focused module, so future control-protocol work has a clear source of truth and no longer requires editing the curses UI/control-plane mega-file for pure schema or parser changes.

## What I Already Know

* `src/ga_tui/app.py` is over 22k lines and currently owns UI, state, Secret Vault, scheduler, gateway, subagents, prompt injection, control parsing, and execution.
* The current protocol source of truth is `ga-control.v2` plus standalone `agenttask.v2`, documented in `.trellis/spec/backend/agent-control-protocol.md`.
* Control parsing/coercion logic is concentrated around `app.py` line 12698 through 13264.
* Execution functions such as `apply_tui_controls_from_text()`, `apply_task_control()`, and `apply_secret_subagent_controls_from_text()` still depend on `State`, scheduler functions, session operations, and subagent execution.
* Compatibility cleanup for retired vocabulary is already quarantined in `src/ga_tui/compat_legacy.py`.
* Regression coverage for control protocol behavior lives in `scripts/check_policy_gates.py`.

## Assumptions

* This task is the first extraction step, not a full `app.py` decomposition.
* Pure protocol constants, regexes, JSON parsing, schema validation, v2-to-execution action coercion, and control stripping are safe to move first.
* Runtime execution functions that mutate `State` should stay in `app.py` for this task unless a helper can be moved without importing `State`.
* `app.py` should import the extracted helpers and keep the same public function names where tests or callers expect them.
* The extracted module should not import curses, GenericAgent runtime classes, or mutable TUI state.

## Requirements

* Add a focused module under `src/ga_tui/` for the current control protocol, tentatively `control_protocol.py`.
* Move current `ga-control.v2` / `agenttask.v2` protocol constants, action sets, v2 action mapping, JSON repair/parsing, extraction, and stripping helpers into the new module.
* Keep `src/ga_tui/app.py` behavior-compatible by importing/re-exporting the moved names or replacing direct definitions with imports.
* Keep retired protocol cleanup isolated in `compat_legacy.py`; do not reintroduce retired vocabulary into active prompts, docs, or normal runtime branches.
* Avoid moving stateful execution functions in this task unless the dependency boundary is already trivial.
* Update tests only as needed to preserve current behavior and add a focused import/behavior check for the new module if coverage would otherwise stay indirect.

## Acceptance Criteria

* [x] `src/ga_tui/control_protocol.py` exists and contains the current protocol/parser/coercion helpers with no dependency on curses or GenericAgent runtime classes.
* [x] `src/ga_tui/app.py` no longer locally defines the moved pure protocol helpers.
* [x] Existing `app.py` callers still expose `extract_tui_controls()`, `strip_tui_controls()`, and related helpers so `scripts/check_policy_gates.py` keeps working.
* [x] Retired vocabulary remains quarantined and absent from active prompts.
* [x] `python3 -m py_compile src/ga_tui/app.py src/ga_tui/control_protocol.py scripts/check_policy_gates.py` passes.
* [x] `python3 scripts/check_policy_gates.py` passes.
* [x] `git diff --check` passes.

## Definition Of Done

* Relevant Trellis specs are read before implementation.
* The extraction is behavior-preserving and does not add new user-facing protocol semantics.
* The change is compared against `docs/agent-harness-architecture.md` before final reporting.
* Work is committed, then the task is archived and the journal is recorded.

## Out Of Scope

* Moving scheduler execution, subagent lifecycle execution, Secret Vault execution, or session mutation logic out of `app.py`.
* Rewriting the control schema.
* Introducing compatibility branches for retired protocol names.
* Splitting the entire UI/state layer.
* Changing GenericAgent integration or monkey-patching behavior.

## Technical Notes

* Candidate moved helpers include `normalized_control_action`, `known_tui_control`, `action_schema_valid`, `coerce_ga_control_action`, `agenttask_work_order`, `agenttask_routing`, `agenttask_target_selector`, `agenttask_contract`, `lifecycle_is_persistent`, `force_new_from_v2`, `agenttask_objective`, `format_agenttask_worker_prompt`, `execution_control_from_v2`, `controls_from_json_payload`, `repair_json_missing_tail`, `load_ga_control_json_text`, `controls_from_json_text`, `tui_control_parse_errors`, `extract_tui_controls`, and `strip_tui_controls`.
* `display_prompt_for_subagent_task()` likely stays in `app.py` because it uses UI formatting and `clean_text()`, but it may call extracted `agenttask_*` helpers.
* `format_agent_control_result()` likely stays in `app.py` because it uses `truncate_cells()`.
* `strip_tui_controls()` currently calls `strip_retired_tui_markup()` from `compat_legacy.py`; the new module can depend on that quarantine module without making retired vocabulary active.

## Completion Notes

* Added `src/ga_tui/control_protocol.py` as the focused current-control-protocol source of truth.
* Moved protocol regexes, schemas, current action sets, JSON repair/parsing, action coercion, v2-to-execution mapping, lifecycle/reuse field parsing, and strip/extract helpers out of `app.py`.
* Kept stateful execution functions in `app.py`: `apply_tui_controls_from_text()`, `apply_task_control()`, `apply_secret_subagent_controls_from_text()`, session operations, scheduler dispatch, and subagent execution remain unchanged.
* Added a policy-gate assertion that `app.py` re-exports key protocol helpers from `ga_tui.control_protocol` and that the extracted module does not import curses.
* Updated `.trellis/spec/backend/agent-control-protocol.md` to make `control_protocol.py` the documented source of truth for protocol parsing helpers.

## Verification

* `python3 -m py_compile src/ga_tui/app.py src/ga_tui/control_protocol.py scripts/check_policy_gates.py`
* `python3 scripts/check_policy_gates.py`
* `python3 -m compileall -q src scripts`
* `ga-tui-check --root /home/vimalinx/Programs/GenericAgent`
* `git diff --check`
* `rg` confirmed the moved protocol helpers are now defined only in `src/ga_tui/control_protocol.py`.
