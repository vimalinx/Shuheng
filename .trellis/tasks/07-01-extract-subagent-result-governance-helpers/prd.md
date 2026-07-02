# Extract Subagent Result Governance Helpers

## Objective

Move pure subagent-result task-ledger helper logic out of `src/ga_tui/app.py` into `src/ga_tui/governance.py`, while keeping `app.py` compatibility wrappers for app-owned artifact-path and subagent-meta dependencies.

## Scope

- Add lower-level helpers in `governance.py` for:
  - selecting a subagent-result artifact ref from task `artifact_refs`
  - stripping the generated artifact heading/task prelude from a loaded artifact body
  - deriving a display name from an already-loaded task row and injected metadata lookup
  - computing first-seen timestamps per task id over task rows
  - identifying completed subagent-result task rows
- Keep `app.py` public helper names available.
- Keep artifact URI to local path resolution, file reads, `TEMP_SUBAGENTS_DIR`, `subagent_meta_path(...)`, and `load_subagent_meta_file(...)` injected or wrapped by `app.py`.
- Preserve current matching semantics for subagent result notices and scheduled reports.
- Add tests for direct helper behavior and app wrapper parity.
- Update policy gates and backend spec for the expanded governance boundary.

## Non-Goals

- Do not move `backfill_durable_subagent_result_messages_for_path(...)`.
- Do not move durable UI system-message persistence, session metadata writes, history restore, scheduled report row construction, Web Console payloads, rendering, command handlers, runtime dispatch, or storage roots.
- Do not change task ledger schemas, artifact URI semantics, or subagent/session/history ownership.
- Do not introduce a `governance.py` dependency on `ga_tui.app`, curses, `State`, `PanelItem`, `RenderLine`, or draw/command handlers.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/governance.py tests/test_governance.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/governance.py tests/test_governance.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_governance.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release gate from `goal-7/plan.md` before commit.

## Architecture Baseline

This should move the system closer to `docs/agent-harness-architecture.md`: subagent-result ledger row interpretation becomes a lower-level governance boundary, while `app.py` still owns orchestration, artifact storage paths, metadata IO injection, durable UI notice backfill, history ownership, rendering, commands, and runtime side effects.
