# Extract Subagent Identity Helpers

## Objective

Move pure subagent identity normalization and id generation helpers out of `src/shuheng/app.py` into `src/shuheng/subagent_store.py`, while preserving existing behavior through `app.py` compatibility aliases/wrappers.

## Scope

- Move implementation logic for:
  - `clean_subagent_id(...)`
  - `normalize_subagent_identity_text(...)`
  - `compact_identity_text(...)`
  - `unique_subagent_id(...)`
  - `unique_secret_subagent_id(...)`
  - `unique_runtime_subagent_id(...)`
- Keep pure helpers parameterized over explicit existing ids or existence checks where needed, so `subagent_store.py` does not import `State` or app globals.
- Keep `app.py` wrappers that inject `SUBAGENTS_DIR`, `state.subagents`, and runtime-specific uniqueness rules.
- Add or expand tests covering:
  - existing `clean_subagent_id` behavior and app alias parity
  - NFKC normalization for subagent ids
  - identity-text normalization and compact matching keys
  - persistent id uniqueness against an explicit subagent root
  - secret/runtime id uniqueness against explicit existing ids
  - app wrapper parity
- Extend policy gates for ownership and no-reverse-import constraints.
- Update `.trellis/spec/backend/agent-control-protocol.md` if the extraction succeeds.

## Out Of Scope

- Do not move `allowed_subagent_meta_fields(...)`, `subagent_runtime_meta_payload(...)`, Secret subagent payload persistence, `save_subagent_meta(...)`, profile/memory/event reads/writes, skill-ref discovery, runtime provider state, `State` mutation, Web Console payloads, rendering, commands, or transcript storage.
- Do not make subagent homes own normal conversation transcripts.
- Do not import `shuheng.app` from extracted modules.

## Invariants

- Global history remains the owner of ordinary non-secret subagent chat transcripts.
- `subagent_store.py` may own identity/path/ref shaping, but must not inspect runtime state, decode Secret Vault payloads, parse/write history transcripts, render UI rows, or dispatch runtime work.
- ID generation must preserve current user-facing shapes and collision behavior.
- Public imports and call behavior from `shuheng.app` remain compatible during decomposition.

## Verification

- `python3 -m py_compile src/shuheng/app.py src/shuheng/subagent_store.py tests/test_subagent_store.py tests/test_path_safety.py scripts/check_policy_gates.py`
- `python3 -m ruff check src/shuheng/app.py src/shuheng/subagent_store.py tests/test_subagent_store.py tests/test_path_safety.py scripts/check_policy_gates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/test_subagent_store.py tests/test_path_safety.py -p no:cacheprovider`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_policy_gates.py`
- Full release-gate verification before commit, matching the goal-7 plan.
