# Extract Rendering Process Turn Helper

## Requirement

Continue Goal 7 app.py decomposition by moving the deterministic
`append_process_turn(...)` line-selection policy out of `src/ga_tui/app.py` and
into the lower-level, curses-free `src/ga_tui/rendering.py` module.

The extracted helper should return a list of rendered process-turn text lines
from already-computed inputs. `src/ga_tui/app.py` must keep the legacy public
`append_process_turn(rendered, marker, body, current, fold_details=True,
collapse_whole=False)` wrapper and inject all app-owned dependencies.

## Scope

- Add a pure helper in `src/ga_tui/rendering.py` for process-turn line
  generation.
- Keep `src/ga_tui/app.py` as the compatibility facade for the old mutating
  append API.
- Pass app-owned decisions into the lower-level helper explicitly, including
  process noise flags, call noise flag, visible final text, summary/title text,
  and already-formatted process line strings.
- Preserve current `append_process_turn(...)` behavior for visible replies,
  collapsed whole process output, process headers, process detail lines, and
  markdown-fence closing.
- Extend `tests/test_rendering.py` to cover direct helper behavior and app
  wrapper parity.
- Extend `scripts/check_policy_gates.py` to lock helper ownership, app wrapper
  parity, absence of a local pure implementation in `app.py`, and the rendering
  no-reverse-dependency boundary.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the rendering
  boundary gains a durable contract.

## Non-Goals

- Do not move `render_assistant_text(...)`.
- Do not move `process_tools(...)`, JSON-ish tool payload parsing,
  interaction extraction, ask-user handling, IRC snippets, or process grouping.
- Do not move `message_block_lines(...)`, `message_lines_from_cache(...)`,
  markdown/table/plain block rendering, `RenderLine` allocation, curses attrs,
  draw functions, or cache mutation.
- Do not touch mutable `State`, runtime dispatch, Web Console, dashboard,
  command/input handlers, storage roots, approvals, artifacts, ledgers, Secret
  Vault behavior, or history ownership.
- Do not import `ga_tui.app`, curses, `State`, Web Console, dashboard,
  runtime-dispatch, commands, or input handlers from `rendering.py`.

## Compatibility Contract

- Existing imports and tests that call `ga_tui.app.append_process_turn(...)`
  keep working.
- `rendering.py` remains a lower-level dependency of `app.py`.
- The helper in `rendering.py` must be deterministic over explicit inputs and
  must not inspect global app state.
- Behavior must stay byte-for-byte compatible for the scenarios covered by
  existing rendering behavior: final text, call noise with fold details,
  collapsed whole process output, summary fallback, and process-noise fallback.

## Verification

- `python3 -m py_compile src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/ga_tui/app.py src/ga_tui/rendering.py tests/test_rendering.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_rendering.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 gate before commit: Ruff, release hygiene, runtime smoke,
  compileall, `git diff --check`, full pytest, package build, wheel smoke, and
  `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.
- Compare the result against `docs/agent-harness-architecture.md`; the change
  should move deterministic rendering policy into a restricted lower-level
  helper while keeping app.py as the single Orchestrator/composition facade for
  mutation and side effects.

## Rollback

Revert the scoped commit or restore the wrapper body in `src/ga_tui/app.py` if
the extracted helper changes rendering behavior or creates a reverse dependency.
