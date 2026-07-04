# Default Full Permissions for OMP Runtime

## Goal

Make the OMP-backed Shuheng main runtime usable as a real agent by default instead of presenting itself as a read-only `specialist`. The default OMP main context pack should advertise a full, practical tool capability profile while preserving Shuheng as the owner of approvals, long-term memory, task ledgers, artifacts, and isolated OMP runtime files.

## What I Already Know

* The user observed an OMP-backed TUI transcript where the assistant reported `tools_allowed: read, reason` and `write_policy: none`, then could not explain how to switch to full mode.
* `build_main_runtime_context_pack()` currently constructs the main OMP worker with role `specialist`, so it inherits the narrow `specialist` role template.
* `permissions_for_role()` currently derives `tools_allowed` and `write_policy` directly from role templates.
* OMP is the default runtime provider on this branch, but Shuheng remains the policy and memory governance owner.
* OMP runtime files are already projected into a Shuheng-owned isolated agent directory, not the user's system `~/.omp/agent`.

## Requirements

* Add an explicit permission profile concept for context packs.
* Default the OMP main runtime context pack to `full`.
* Keep subagent context packs role-bounded by default unless a caller explicitly selects another profile.
* `full` profile must advertise practical OMP/agent capabilities: read, reason, search, repo read/write, edit/write, test, bash/shell, browser, eval, web search, git, host tools, task/subagent delegation, artifact read/write, and memory candidate submission.
* `full` profile must not remove Shuheng approval gates for high-risk actions such as deploy, external send, deletion, spending money, secret access, and permission-policy changes.
* `full` profile must still keep long-term memory as `candidate_only`; OMP must not become a direct memory writer.
* Add an env/config override so the default can be switched to `read_only`, `standard`, or `full` without changing code.
* Update provider/control-plane docs and executable policy-gate smoke coverage.

## Acceptance Criteria

* [x] A generated main OMP context pack no longer says only `tools_allowed: read, reason` by default.
* [x] The formatted OMP prompt includes the active permission profile and full tool list for the main runtime.
* [x] Role-bounded subagents still default to role-specific permissions.
* [x] An env override can force `read_only` for compatibility.
* [x] High-risk actions still evaluate through existing policy gates.
* [x] Memory write policy remains `candidate_only`.
* [x] OMP runtime remains isolated under the Shuheng harness, not system OMP config.
* [x] `python3 -m compileall -q src scripts` passes.
* [x] `python3 scripts/check_policy_gates.py` passes.

## Technical Approach

Introduce permission profiles in `src/shuheng/app.py` near the existing role permission helpers. Keep `standard` as current role-derived behavior, add `read_only` as an explicit narrow compatibility profile, and add `full` as the OMP/main-runtime default. Apply the profile when building context packs and runtime task request permissions. Expose profile metadata in the context pack and formatted prompt so OMP can answer capability questions correctly.

## Decision (ADR-lite)

Context: The user wants OMP as the primary runtime, but the TUI transcript shows it behaving like a read-only subagent because the main runtime inherits `specialist` permissions.

Decision: Make permission scope a Shuheng-owned context-pack profile. Default only the OMP main runtime to `full`; keep governed policy gates and candidate-only memory intact.

Consequences: OMP becomes more useful in normal TUI chats without moving governance into OMP. If full mode proves too broad, operators can force a narrower profile through environment/config without reverting the integration.

## Out of Scope

* Modifying the globally installed/system OMP package or `~/.omp/agent`.
* Letting OMP bypass Shuheng approvals for high-risk actions.
* Letting OMP write long-term memory, schedules, ledgers, or artifacts directly outside Shuheng-owned APIs.
* Building a full TUI settings screen for permission profiles in this task.

## Technical Notes

* Relevant code: `src/shuheng/app.py`, `src/shuheng/ohmypi_provider.py`, `scripts/check_policy_gates.py`.
* Relevant docs/specs: `docs/runtime-provider-control-plane.md`, `.trellis/spec/backend/agent-control-protocol.md`, `docs/agent-harness-architecture.md`.
* Architecture baseline impact: this moves the system closer to the baseline by keeping one strong orchestrator and bounded provider execution while improving the default capability contract for the OMP runtime.
