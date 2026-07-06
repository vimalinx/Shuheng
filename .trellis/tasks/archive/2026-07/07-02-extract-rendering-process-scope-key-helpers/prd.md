# Extract Rendering Process Scope Key Helpers

## Objective

Continue Goal 7 by moving deterministic process/subagent metadata expansion key formatting out of `src/shuheng/app.py` and into `src/shuheng/rendering.py`, while preserving app compatibility wrappers and runtime behavior.

## Scope

- Add pure helpers in `src/shuheng/rendering.py` for:
  - process group expansion keys from an explicit display scope and group label
  - process turn expansion keys from an explicit display scope and turn label
  - subagent metadata expansion keys from an explicit display scope and metadata label
- Keep `display_scope_key(state)` in `app.py`; it still owns all `State` inspection and selected-session/subagent decisions.
- Change `app.process_group_key(...)`, `app.process_turn_key(...)`, and `app.subagent_meta_key(...)` into compatibility wrappers that inject `display_scope_key(state)`.
- Add tests and policy gates for direct helper behavior, app alias/wrapper parity, and duplicate-definition absence for moved helper names.
- Update `.trellis/spec/backend/agent-control-protocol.md` with the durable boundary.

## Out Of Scope

- Do not move `display_scope_key(state)`.
- Do not move process grouping/folding, process turn traversal, `render_assistant_text(...)`, message cache rendering, selection mutation, `State`, curses attrs, Web Console, dashboard, runtime dispatch, history, Secret Vault, ledgers, approvals, artifacts, or input handling.
- Do not change storage semantics, public console scripts, or release posture.

## Compatibility Requirements

- Existing callers of `app.process_group_key(state, label)`, `app.process_turn_key(state, label)`, and `app.subagent_meta_key(state, label)` must return identical strings.
- New helpers must accept only explicit strings and must not import `shuheng.app`, curses, runtime classes, mutable state, Web Console, dashboard, input handlers, command handlers, or draw functions.
- `process_turn_scope_key(...)` must preserve the legacy group-prefix extraction for labels like `G2T7`, returning `<scope>:G2:G2T7`; labels without a group prefix must keep the existing empty middle segment.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 release-quality gate before commit.

## Architecture Baseline

This should move the system closer to `docs/agent-harness-architecture.md` by keeping deterministic UI key formatting in the policy-gated rendering module while the strong Orchestrator facade retains state inspection, mutation, ledgers, approvals, artifacts, history, Secret Vault, Web Console, dashboard, runtime side effects, mutable UI state, and curses rendering.
