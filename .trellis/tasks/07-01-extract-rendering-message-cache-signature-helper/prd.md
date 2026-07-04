# Extract Rendering Message Cache Signature Helper

## Goal

Continue Goal 7 by moving the remaining pure message render-cache signature helper out of `src/shuheng/app.py` into `src/shuheng/rendering.py`, while preserving the app facade and current cache behavior.

## Requirements

- Move only `message_cache_signature(messages)` into `src/shuheng/rendering.py`.
- Keep `src/shuheng/app.py` as the compatibility facade by exposing `message_cache_signature` as a direct alias.
- Keep `message_lines_cached(...)`, `prune_message_block_cache(...)`, `message_lines_from_cache(...)`, `message_block_lines(...)`, `render_assistant_text(...)`, `render_table(...)`, `markdown_blocks(...)`, and `plain_blocks(...)` in `app.py`.
- Preserve current cache invalidation semantics: message signature is based on message object identity, role string, content length, and done flag.
- Keep the extracted helper generic over message-like objects so `rendering.py` does not need to import app-owned state.
- Add focused rendering tests for direct helper behavior, changed role/content length/done/object identity behavior, and app alias parity.
- Update `scripts/check_policy_gates.py` to assert helper ownership, representative behavior, app alias parity, absence of the app-local definition, and the rendering no-reverse-dependency boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` so the durable rendering boundary includes message-cache signature ownership.

## Non-Goals

- Do not move mutable message cache ownership or cache pruning.
- Do not move `message_lines_cached(...)` because it reads and mutates `State.line_cache`, `State.line_cache_key`, and other app-owned UI state.
- Do not move message block rendering, markdown/plain block rendering, process grouping/folding, table rendering, subagent result cards, `RenderLine` allocation, curses attrs, draw functions, command/input handlers, Web Console, dashboard, runtime dispatch, storage roots, approvals, artifacts, ledgers, history ownership, or external-memory behavior.
- Do not change cache keys, rendering output, transcript ownership, or runtime behavior.
- Do not stage or commit historical untracked Trellis task directories, `goal-7/*`, or `uv.lock`.

## Acceptance Criteria

- `src/shuheng/rendering.py` owns `message_cache_signature(messages)`.
- `src/shuheng/app.py` exposes `message_cache_signature` as a compatibility alias.
- Existing `message_lines_cached(...)` continues to call the public name and preserves current behavior.
- Targeted rendering tests and policy gates pass.
- Full release gate pattern from `goal-7/plan.md` passes before commit.
- The change is committed as one coherent work commit.

## Technical Approach

Implement `rendering.message_cache_signature(messages)` as the existing pure tuple comprehension over message-like objects using `getattr(...)` for role/content/done. This keeps `rendering.py` lower-level and avoids importing `Message`, `State`, or `shuheng.app`. Remove the local app definition and add a direct alias beside the other rendering compatibility aliases.

## Definition of Done

- `python3 -m py_compile src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py tests/test_cell_utils.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.

## Architecture Baseline Check

Expected direction: closer to `docs/agent-harness-architecture.md` because deterministic render-cache signature calculation becomes a lower-level policy-gated rendering helper, while the strong Orchestrator facade still owns mutable UI state, cache storage/pruning, redraw decisions, curses drawing, command/input dispatch, runtime side effects, ledgers, approvals, artifacts, history, and external-memory boundaries.
