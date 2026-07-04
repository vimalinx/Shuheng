# Extract Subagent Control Intent Helpers

## Goal

Move the deterministic subagent control intent helpers out of `src/shuheng/app.py` and into the protocol parsing boundary, while preserving executable behavior and the public compatibility surface.

## Scope

- Extract `subagent_control_persistence_intent(...)` into `src/shuheng/control_protocol.py`.
- Extract `subagent_control_force_new_intent(...)` into `src/shuheng/control_protocol.py`.
- Keep `src/shuheng/app.py` re-export aliases for both names.
- Keep `apply_subagent_control(...)` and `register_subagent_control_aliases(...)` in `app.py`.
- Add direct tests for protocol helper behavior and app alias parity.
- Update policy gates and backend spec text so the ownership boundary is executable and documented.

## Non-Goals

- Do not change subagent creation, reuse, deletion, role/model updates, or runtime dispatch behavior.
- Do not move `apply_subagent_control(...)` into a lower-level module.
- Do not move `SubAgentRuntime`, mutable `State`, ledgers, approvals, artifacts, history, Secret Vault, Web Console, dashboard, commands, rendering, storage roots, or runtime providers.
- Do not add a dependency from `control_protocol.py` to `app.py`, curses, `State`, runtime classes, or storage-root globals.
- Do not infer persistence or force-new behavior from natural-language `target`, `value`, `name`, `profile`, or context text.

## Behavior To Preserve

- Persistence intent:
  - `persistent`, `durable`, and `long_term` are interpreted through the existing truthy parser.
  - `lifecycle` or `scope` values such as `persistent`, `durable`, `long_term`, `long-term`, `permanent`, `正式`, `持久`, `长期`, and `永久` produce persistent intent.
  - `lifecycle` or `scope` values such as `ephemeral`, `temporary`, `temp`, `session`, `session_only`, `临时`, and `暂时` produce temporary intent.
  - `temporary`, `temp`, `ephemeral`, `session_only`, and `session_scoped` truthy flags produce temporary intent.
  - Missing explicit lifecycle fields defaults to ephemeral/session-scoped behavior: `(False, True)`.
- Force-new intent:
  - `force_new`, `create_new`, `fresh`, and `separate` truthy flags force a new subagent.
  - `reuse`, `reuse_existing`, `allow_reuse`, and `dedupe` falsey flags force a new subagent.
  - scalar truthy `new` forces a new subagent.
  - `reuse_policy` values `force_new`, `never`, `none`, and `no_reuse` force a new subagent.
  - Natural-language context text and display fields remain ignored.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/control_protocol.py tests/test_control_protocol.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/control_protocol.py tests/test_control_protocol.py scripts/check_policy_gates.py`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_control_protocol.py -p no:cacheprovider`
- `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full Goal 7 gates when feasible: full Ruff, release hygiene, runtime smoke, compileall, `git diff --check`, full pytest, package build, wheel smoke, and `shuheng-check --root /home/vimalinx/Programs/GenericAgent`.
