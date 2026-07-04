# Fix Secret Subagent Persistence Guidance And Reuse Matching

## Goal

Prevent Secret-mode main agents from misunderstanding how persistent Secret subagents are created and prevent fuzzy reuse from mapping a requested network-search agent onto an unrelated existing network-security agent.

## What I Already Know

* Secret subagents are persisted as encrypted `.secret` payloads under `data/sessions/secret_subagents/...`, not as plaintext directories under `memory/subagents/`.
* Main-agent hidden `<shuheng>` subagent controls are also supported in Secret mode, but only dedicated Secret subagent controls execute.
* `apply_secret_subagent_controls_from_text()` executes `subagent_create` through the same `apply_subagent_control()` path while Secret is unlocked.
* `find_reusable_subagent()` currently accepts fuzzy matches with a low score threshold, and Chinese two-character overlaps like `网络` can make `网络搜索员` reuse `网络安全专家`.
* The user wants an explicit persistent Secret network-search agent and expects the assistant not to ask the user how Secret persistence works.

## Requirements

* Secret prompt guidance must tell the main agent that persistent Secret subagents use the same `<shuheng>{"action":"subagent_create","persistent":true,...}</shuheng>` control, but are stored in the encrypted Secret vault.
* Secret prompt guidance must explicitly tell the main agent not to inspect or reason from normal `memory/subagents/` paths while Secret is unlocked.
* Fuzzy subagent reuse must not reuse a different-named agent based only on generic or broad Chinese fragments like `网络`.
* Exact id/name reuse and legitimate same-topic fuzzy reuse should continue working.
* Explicit `force_new=true`, `reuse=false`, and no-reuse wording must still bypass reuse.

## Acceptance Criteria

* [ ] Creating `网络搜索员` while `网络安全专家` exists creates a distinct persistent Secret subagent instead of reusing the security expert.
* [ ] Existing exact-name reuse still reuses the existing subagent.
* [ ] Secret hidden-control prompt includes the encrypted-vault persistence rule and the `memory/subagents/` warning.
* [ ] Policy gate coverage includes the `网络搜索员` vs `网络安全专家` false-reuse scenario.
* [ ] Compile and policy gate checks pass.

## Out Of Scope

* Rewriting the whole subagent matching algorithm.
* Changing Secret vault encryption/storage format.
* Creating the user's actual network-search agent in the live vault from this code task.

## Technical Notes

* Main file: `src/shuheng/app.py`.
* Likely functions/constants: `TUI_AGENT_CONTROL_HINT`, `reusable_subagent_score()`, `find_reusable_subagent()`, `apply_secret_subagent_controls_from_text()`.
* Regression tests live in `scripts/check_policy_gates.py`.
