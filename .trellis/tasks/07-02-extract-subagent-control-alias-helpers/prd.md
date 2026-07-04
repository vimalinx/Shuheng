# Extract Subagent Control Alias Helpers

## Goal

Move deterministic subagent control alias lookup helpers out of `src/shuheng/app.py` into the lower-level `src/shuheng/subagent_store.py` boundary while preserving current behavior and public compatibility aliases.

This continues Goal 7 app facade decomposition without changing subagent control semantics.

## Scope

In scope:

- Move `subagent_control_alias_keys(*values)` into `src/shuheng/subagent_store.py`.
- Move `resolve_subagent_control_alias(alias_map, target)` into `src/shuheng/subagent_store.py`.
- Keep `src/shuheng/app.py` exposing the same public helper names as compatibility aliases.
- Keep `register_subagent_control_aliases(alias_map, sub, *values)` in `src/shuheng/app.py` as the Orchestrator wrapper because it depends on `SubAgentRuntime`.
- Add direct `subagent_store` tests and app parity coverage.
- Expand `scripts/check_policy_gates.py` so the helper ownership and no-reverse-dependency boundary are enforced.
- Update `.trellis/spec/backend/agent-control-protocol.md` to document the durable alias helper boundary.

Out of scope:

- No changes to `apply_subagent_control(...)` behavior.
- No changes to subagent creation, reuse, deletion, persistence, or runtime dispatch.
- No movement of `State`, `SubAgentRuntime`, ledgers, approvals, artifacts, Secret Vault behavior, Web Console payloads, rendering, commands, storage roots, or history ownership.
- No storage migration and no mutation of `~/.shuheng`.

## Existing Behavior To Preserve

- Alias key generation ignores empty values and reserved live targets: `current`, `now`, and `selected`.
- Alias keys preserve insertion order and de-duplicate by exact generated key.
- Each input can produce original text, lowercase text, and compact normalized identity text.
- `resolve_subagent_control_alias(...)` checks generated keys in the same order and returns the mapped agent id on the first hit.
- Missing alias matches return the original target unchanged.
- `register_subagent_control_aliases(...)` still registers explicit values plus `sub.agent_id` and `sub.name`.

## Architecture Boundary

`subagent_store.py` may own pure identity/ref/alias shaping over explicit values and maps. It must not import `shuheng.app`, curses, mutable `State`, runtime dispatch, command handlers, rendering, Web Console, ledgers, approvals, artifacts, or storage root globals.

`app.py` remains the strong Orchestrator facade for applying control actions, resolving runtime subagent objects, maintaining alias maps during action execution, mutating state, writing ledgers, and dispatching runtime side effects.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/subagent_store.py tests/test_subagent_store.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/subagent_store.py tests/test_subagent_store.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_subagent_store.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 gate when feasible: full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.
