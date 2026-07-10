# `src/shuheng/app.py` Decomposition Plan

Date: 2026-06-30

## Purpose

`src/shuheng/app.py` is still the central Shuheng TUI/control-plane module. It is
also the highest remaining maintainability risk: current size is about 28.7k
lines and the module owns UI state, history, Secret Vault, subagents, governance
stores, runtime dispatch, local protocol records, rendering, input handling, and
the process loop.

This plan defines a low-risk split path. The goal is not to make a prettier file
tree in one rewrite. The goal is to reduce accidental coupling while preserving
the existing executable contracts, release gates, and local-alpha compatibility.

## Current Evidence

- `app.py` has 28,725 lines and 1,239 top-level classes/functions.
- Existing successful extractions already prove the intended direction:
  - `ledger_store.py` owns JSONL append/read/cache and JSON object locked update.
  - `scheduler.py` owns schedule parsing/runtime helpers.
  - `runtime_evidence.py`, `baseline.py`, and `local_protocol_registry.py` own narrow
    local-record helper contracts.
  - `control_protocol.py` and provider modules own protocol/runtime-specific
    mechanics.
- The architecture baseline says the target is a governed system: strong
  Orchestrator, restricted subagents, shared ledgers, artifact refs,
  single-writer enforcement, approval gates, auditable communication, and
  external memory. Decomposition must preserve those ownership boundaries.

## Extraction Status (2026-07-09)

A ratchet gate (`assert_app_py_does_not_grow`, `APP_PY_MAX_LINES`) now caps
app.py and only allows it to shrink. Two pure-relocation PRs landed:

- PR1: secret network/proxy cluster (5 funcs) → `secret_vault.py`.
- PR2: pure islands — `session_stable_id`/`target_matches_session_id` →
  `history_store.py`; `allowed_subagent_meta_fields` + 2 constants →
  `subagent_store.py`.

Honest finding: the **stdlib-pure relocations are essentially exhausted**. What
remains in app.py is (a) path/State/counter-binding helpers that correctly stay
(e.g. `new_session_log_path`, `legacy_*_path`, the subagent path shims), (b)
logic entangled through general helpers used dozens of times across app.py
(`normalized_role`/`normalized_subagent_role`, ~48 call sites; role machinery),
or (c) the large UI bulk — the ~110 subagent draw/input/command functions plus
`rendering`/`input_controller`/`commands` residuals. **The next material shrink
is Phase 7 (UI split), which needs the `State`/`ui_types` boundary stabilized
first — not more pure-leaf harvesting.** Apply the moveable-vs-stays heuristic
(the note under `secret_vault.py` below) to any future extraction.

## Non-Goals

- No big-bang rewrite.
- No storage-root migration while decomposing modules.
- No behavior rewrite bundled with file movement.
- No breaking public imports, console scripts, policy gates, or test helpers that
  still import functions from `shuheng.app`.
- No moving code into modules that import `shuheng.app`; extracted modules must be
  lower-level dependencies, not back-references.

## Target Dependency Direction

```text
config/path constants
  -> domain types and pure text helpers
  -> storage adapters and stores
  -> domain services
  -> renderers / command handlers / local protocol record adapters
  -> app.py orchestration facade and process loop
```

Rules:

- Lower-level modules must not import `shuheng.app`.
- `app.py` may temporarily re-export moved symbols for compatibility.
- Mutable runtime globals should be centralized before broad extraction. Tests
  currently retarget many `app.py` globals directly, so path/state extraction
  must keep a compatibility facade until tests are migrated.
- Any phase that moves storage or transcript code must include round-trip
  persistence tests, not just import tests.

## Proposed Module Boundaries

### `ui_types.py`

Own dataclasses and small state containers:

- `Message`, `RenderLine`, `StreamTarget`, `BackgroundSession`
- `SubAgentRuntime`, `SecretVaultState`, `State`
- `PanelItem`, `PolicyDecision`, `SubagentDispatchResult`
- Lightweight enums/constants that do not read environment variables

Reason: Almost every other split needs these names. Move them early, but keep
`app.py` aliases so existing tests and callers keep working.

### `text_utils.py`

Own pure text/cell helpers:

- `cell_width`, `truncate_cells`, `pad_cells`, `clean_text`, `wrap_cells`
- compact title/description helpers that do not need runtime state
- ANSI/process-block regex helpers only after their callers are ready

Reason: Pure leaf code has the lowest extraction risk and already has unit-test
coverage patterns.

### `history_store.py`

Own normal session history and metadata:

- session path/key helpers
- `load_session_meta_registry`, `save_session_meta_registry`
- transcript parsing/writing helpers
- sidebar history row cache helpers
- process-summary-safe title/description extraction

Keep in `app.py` until this module exists:

- direct UI rendering of history rows
- active runtime restore orchestration

Important invariant: non-secret subagent direct chat must restore from canonical
history transcript first; `session_meta.json` is an index/cache, not a full
transcript owner.

### `secret_vault.py`

Own encryption and Secret Vault persistence:

- vault metadata, password policy, key derivation, encrypt/decrypt
- encrypted session/subagent storage
- sealed import envelope helpers
- Secret import/native session list and restore payload parsing

Reason: This code is large but relatively cohesive. The module must not import
TUI rendering. UI prompts and copy-confirmation UX stay in `app.py` or a later
UI module.

Extraction heuristic (learned from the first secret extraction, 2026-07-09):
only functions that are **stdlib-pure and reference no app.py module globals**
relocate cleanly (e.g. `secret_auto_tor_enabled`, `secret_network_status`, the
proxy chain helpers). Two categories must **stay** in `app.py`:
1. **Path-binding shims** that inject app.py-owned path constants into
   `secret_vault.SecretVaultPaths` (e.g. `secret_vault_paths`,
   `secret_storage_path_for_session`) — `secret_vault.py` is deliberately
   "callers pass paths" and must not own or import the path constants.
2. **`State`-dependent** orchestration (e.g. `activate_secret_proxy_env`,
   `restore_secret_proxy_env`) — mutates live UI/runtime state.

Relocate the pure bodies to `secret_vault.py` and keep
`secret_X = secret_vault_store.secret_X` re-export aliases in `app.py`'s alias
block so call sites stay unchanged. The same moveable-vs-stays lens applies to
the `subagent` and `history` clusters.

### `subagent_store.py`

Own persistent subagent files and chat-history refs:

- subagent home/path helpers
- meta/profile/memory/event persistence
- legacy per-agent JSON import
- history-backed non-secret chat session indexing
- Secret-subagent storage adapter calls through `secret_vault.py`

Reason: Keeps the user's corrected invariant explicit: persistent subagent home
stores profile/memory/runtime refs, while conversation history lives in global
history or Secret Vault.

### `governance.py`

Own control-plane domain records above `ledger_store.py`:

- task/progress row helpers
- policy decisions, approvals, artifacts, traces, checkpoints, eval records
- single-writer lock wrapper around `ledger_store.update_json_dict_file`
- audit-ref collection

Reason: `ledger_store.py` should stay low-level. Governance semantics belong in
their own layer so `app.py` stops mixing UI and durable record mechanics.

### `context_packs.py`

Own memory/context hydration:

- memory inventory payloads that are not UI rendering
- context layer assembly
- context pack artifact writing
- runtime prompt context/ref formatting

Reason: This is the bridge between memory, artifacts, runtime dispatch, and
subagents. It should depend on stores/services, not on curses UI.

### `runtime_dispatch.py`

Own provider-neutral dispatch:

- runtime task request construction
- `put_agent_runtime_task`
- stream queue normalization
- subagent task/chat dispatch state transitions that are not drawing-specific

Keep the final `submit(...)` dispatcher in `app.py` until command parsing is
separated, because it currently binds UI selection, command grammar, and runtime
start behavior.

### `dashboard.py`

Own home/dashboard data shaping:

- dashboard specs, sections, status/todo rows
- scheduled report rows and home-line cache signatures
- main/subagent home line construction

Reason: This is separate from low-level message rendering and can be tested as
structured text output.

### `rendering.py`

Own curses-agnostic rendering transforms first, curses drawing second:

- message block parsing and render-line creation
- process folding/grouping
- sidebar/rightbar row formatting
- panel row shaping
- finally `draw_*` functions once their dependencies are stable

Reason: Rendering is large and tightly coupled. Split it late, after types,
history, dashboard, and stores are lower-level modules.

### `input_controller.py`

Own terminal input and mouse behavior:

- cursor movement and input layout helpers
- key decoding, bracketed paste, mouse masks
- `handle_key`, `handle_mouse`

Reason: Input is coupled to `State` and command routing. Extract after command
handlers and rendering have stable interfaces.

### `commands.py`

Own command parsing and command handlers:

- `/memory`, `/tasks`, `/approvals`, `/workspace`, `/model`, `/subagent`, etc.
- approval decision helpers
- command result objects that `app.py` can render or dispatch

Reason: Commands are currently mixed with UI state mutation. Extract only after
domain services exist, otherwise this becomes a second monolith.

## Recommended Phases

### Phase 0: Guardrails Before Movement

Deliverables:

- Add a policy gate that forbids new extracted modules from importing
  `shuheng.app`.
- Add a small import smoke that imports all planned modules.
- `app.py` line-count telemetry exists in `release_readiness.py`
  (`release_readiness_report(app_py_lines=...)` → `monolith_risk.app_py_lines`,
  informational only). It is now backed by a **hard ratchet gate**
  `assert_app_py_does_not_grow()` in `scripts/check_policy_gates.py`: the
  `APP_PY_MAX_LINES` constant (baseline 28153, set 2026-07-09) is a CI-enforced
  ceiling that may **only ever decrease**. Convention: a PR that shrinks `app.py`
  lowers `APP_PY_MAX_LINES` in the same diff, and any net growth fails
  `python3 scripts/check_policy_gates.py` with an actionable message naming the
  current count, ceiling, and delta.

Verification:

- `python3 scripts/check_policy_gates.py`
- `python3 -m pytest -q -p no:cacheprovider`
- `python3 -m compileall -q src scripts`

### Phase 1: Leaf Extraction

Move:

- `ui_types.py`
- `text_utils.py`

Compatibility:

- `app.py` imports and re-exports moved names.
- Existing tests that import from `shuheng.app` keep passing.

Success metric:

- `app.py` loses low-risk leaf code first without behavior changes.

### Phase 2: History Boundary

Move:

- normal history metadata helpers
- transcript read/write helpers
- process-summary-safe preview/title helpers

Required tests:

- stale `session_meta` cannot override transcript-backed subagent chat.
- missing/empty transcript can still use legacy full-message fallback.
- process-only OMP summaries do not become titles.

Risk:

- High, because history touches sidebar, restore, local protocol records, and subagent chat.
  Keep phase scope narrow and commit immediately after green gates.

### Phase 3: Secret Vault Boundary

Move:

- Secret crypto/storage/import helpers to `secret_vault.py`

Keep in app/rendering:

- Secret prompts
- copy-confirmation UI
- command entrypoints

Required tests:

- existing Secret Vault unit tests
- policy gate Secret subagent persistence scenarios

### Phase 4: Governance Boundary

Move:

- policy config/decision helpers
- approval/task/artifact/checkpoint/eval domain helpers
- single-writer lock wrappers

Dependency:

- `governance.py` depends on `ledger_store.py`, not on `app.py`.

Required tests:

- policy gate
- `tests/test_jsonl.py`
- targeted approval/task panel tests if added

### Phase 5: Context And Runtime Dispatch

Move:

- memory hydration/context pack construction to `context_packs.py`
- provider-neutral task request and stream normalization to
  `runtime_dispatch.py`

Risk:

- Medium-high: context packs are security and provenance boundaries.

Required tests:

- policy gate context-pack checks
- runtime smoke
- scheduler dispatch smoke

### Phase 6: Local Protocol Records And Dashboard

Move:

- Local protocol registry record shaping to `local_protocol_registry.py` or another
  lower-level local-record module
- dashboard/home line construction to `dashboard.py`

Required tests:

- local protocol registry smoke tests
- policy gate subagent conversation hydration check

### Phase 7: Rendering, Commands, Input, Process Loop

Move last:

- message rendering and process folding
- curses draw functions
- command handlers
- keyboard/mouse input

Keep in final `app.py`:

- imports/re-exports
- `main()`
- `run()`
- composition/wiring
- compatibility shims slated for later removal

Target final shape:

```text
src/shuheng/app.py                 thin executable facade
src/shuheng/ui_types.py            state/dataclasses
src/shuheng/text_utils.py          pure display/text helpers
src/shuheng/history_store.py       normal history and transcript storage
src/shuheng/secret_vault.py        encrypted storage
src/shuheng/subagent_store.py      subagent profile/memory/session refs
src/shuheng/governance.py          task/policy/approval/artifact semantics
src/shuheng/context_packs.py       context and memory hydration
src/shuheng/runtime_dispatch.py    provider-neutral dispatch
src/shuheng/dashboard.py           home/dashboard lines
src/shuheng/rendering.py           render transforms and draw helpers
src/shuheng/input_controller.py    keyboard/mouse/input behavior
src/shuheng/commands.py            command grammar and handlers
```

## Phase Exit Criteria

Every extraction phase must pass:

- `python3 -m py_compile src/shuheng/app.py <new modules>`
- `python3 -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`
- `python3 -m compileall -q src scripts`
- `git diff --check`

For phases touching packaging, release, local protocol records, runtime dispatch, or storage:

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_release_hygiene.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/runtime_smoke.py`
- `python3 -m build --sdist --wheel --outdir /tmp/shuheng-dist`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist`
- `shuheng-check`

## Stop Conditions

Stop and re-evaluate if any phase causes:

- an extracted module to import `shuheng.app`
- a second owner for history, Secret Vault, task ledgers, or memory candidates
- a change to `~/.shuheng` storage semantics
- a change to public console scripts or release posture
- a regression in policy gate, runtime smoke, or wheel/sdist smoke
- test fixtures requiring broad rewrites unrelated to the moved code

## First Concrete Task

Start with Phase 0 and Phase 1 only:

1. Add a policy gate that extracted modules cannot import `shuheng.app`.
2. Create `ui_types.py` and move dataclasses with compatibility aliases in
   `app.py`.
3. Create `text_utils.py` and move pure cell/text helpers with compatibility
   aliases in `app.py`.
4. Run the full phase exit criteria.

Do not start history or Secret Vault extraction until these two low-risk modules
are stable and committed.
