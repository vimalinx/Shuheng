# Extract Subagent Skill Ref Helpers

## Objective

Move pure subagent skill-reference normalization out of `src/shuheng/app.py` into `src/shuheng/subagent_store.py`, while preserving existing behavior through an `app.py` compatibility alias.

## Scope

- Move implementation logic for `normalize_subagent_skill_refs(...)`.
- Keep the helper pure over caller-provided values and optional limits.
- Preserve existing handling for:
  - plain strings split by spaces, commas, or newlines
  - lists, tuples, sets, and dictionaries
  - dict items with `ref`, `name`, `skill`, or `path`
  - `skill://` prefix stripping
  - cleaned text, blank filtering, long-ref filtering, case-insensitive de-duplication, and positive limit handling
- Add or expand tests covering module behavior and `app.py` alias parity.
- Extend policy gates for ownership and no-reverse-import constraints.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the extraction succeeds.

## Out Of Scope

- Do not move `subagent_skill_roots(...)`, `subagent_skill_display_name(...)`, `subagent_skill_file_for_ref(...)`, `subagent_skill_summary_from_text(...)`, `subagent_skill_pack_for_refs(...)`, `format_subagent_skill_refs(...)`, `set_subagent_skill_refs(...)`, skill file IO, skill root discovery, subagent metadata persistence, Secret payload persistence, runtime dispatch, Web Console payloads, rendering, commands, or transcript storage.
- Do not make `subagent_store.py` read local skill files or inspect runtime state.
- Do not import `shuheng.app` from extracted modules.

## Invariants

- `subagent_store.py` may own skill-ref value normalization because it is metadata/ref shaping.
- `subagent_store.py` must not own skill file resolution, skill pack assembly, UI formatting, metadata writes, Secret Vault storage, runtime providers, or command handling.
- Public imports and call behavior from `shuheng.app` remain compatible during decomposition.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/subagent_store.py tests/test_subagent_store.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/subagent_store.py tests/test_subagent_store.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_subagent_store.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release-gate verification before commit, matching the goal-7 plan.
