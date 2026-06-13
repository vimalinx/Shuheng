# Isolated OMP Runtime Settings

## Goal

Make the embedded Oh My Pi runtime follow the same GA-TUI model/provider settings surface while keeping the user's system-level OMP installation and `~/.omp/agent/*` untouched.

## What I Already Know

* The current experiment branch is `experiment/ohmypi-runtime-memory`, and `ohmypi` is the default runtime provider when `GA_TUI_RUNTIME_PROVIDER` is unset.
* GA-TUI `/model` stores configured providers in `mykey.py` as `LLMConfigEntry` records with `name`, `apikey`, `apibase`, `model`, and protocol-specific fields.
* OMP reads its `config.yml`, `models.yml`, sessions, auth DB, skills, rules, and prompts from its `agentDir`; the CLI help documents `PI_CODING_AGENT_DIR` as the session/config root defaulting to `~/.omp/agent`.
* The user's system OMP config currently lives at `/home/vimalinx/.omp/agent/config.yml`; this task must not write that path.
* OMP model registry supports custom OpenAI-compatible providers through `models.yml` provider entries with `baseUrl`, `apiKey`, `api`, `models`, and optional `compat`.
* Current `OhMyPiRpcAgent` starts `omp --mode rpc` without a subprocess env override, so it inherits system OMP config and environment.
* Current OMP terminal error frames can finish with an empty TUI response because `errorMessage` / `errorStatus` / `stopReason:error` is not surfaced.

## Requirements

* Add a GA-TUI-owned isolated OMP runtime root under the harness directory, not under `~/.omp`.
* Generate OMP-compatible `config.yml` and `models.yml` from GA-TUI's `/model` configuration and default model selection.
* Launch embedded OMP with subprocess-only environment overrides so `PI_CODING_AGENT_DIR` points at the isolated runtime root.
* Preserve `GA_TUI_OHMYPI_BIN` and `GA_TUI_OHMYPI_ARGS` override behavior.
* Ensure GA-TUI host tools and memory append prompt continue to work with the isolated runtime.
* Surface OMP RPC terminal error details in the TUI instead of producing an empty assistant message.
* Keep provider boundary intact: `ohmypi_provider.py` owns RPC/process/env mechanics; `app.py` owns GA-TUI model config reading and generated runtime configuration.
* Add regression coverage that proves the system OMP config path is not written or selected by the embedded runtime.

## Acceptance Criteria

* [x] `agent_runtime_registry(write_memory_prompt_file=False)` prepares an OMP adapter whose command/env points at the GA-TUI isolated OMP runtime directory.
* [x] The generated isolated OMP config includes `modelRoles.default` for the GA-TUI default model when a matching `/model` entry exists.
* [x] The generated isolated OMP `models.yml` contains custom provider/model entries derived from GA-TUI OpenAI-compatible entries.
* [x] The runtime command still includes `--append-system-prompt <GA-TUI memory prompt>`.
* [x] `OhMyPiRpcAgent` passes the configured env to `subprocess.Popen` without mutating `os.environ`.
* [x] Fake RPC tests cover terminal OMP error frame mapping to a visible queue `done` item.
* [x] Policy-gate tests verify provider boundary and that no active code references `/home/vimalinx/.omp/agent` as the embedded runtime root.
* [x] The hash of `/home/vimalinx/.omp/agent/config.yml` remains unchanged after verification smoke tests when the file exists.

## Definition of Done

* Tests added or updated in `scripts/check_policy_gates.py`.
* `python3 -m py_compile src/ga_tui/app.py src/ga_tui/ohmypi_provider.py src/ga_tui/runtime.py scripts/check_policy_gates.py` passes.
* `python3 scripts/check_policy_gates.py` passes.
* `python3 -m compileall -q src scripts` passes.
* `git diff --check` passes.
* Compare the result against `docs/agent-harness-architecture.md` and report whether it moves closer to the governed Orchestrator baseline.
* Commit changes on `experiment/ohmypi-runtime-memory`.

## Technical Approach

Add a small isolated runtime configuration layer:

* In `ohmypi_provider.py`, add data helpers for the isolated OMP runtime root, runtime env generation, OMP config/model YAML text writing, and pass an `env` dict through `OhMyPiRpcAgent` to `subprocess.Popen`.
* In `app.py`, translate GA-TUI `LLMConfigEntry` records to OMP model specs and build an `OhMyPiRuntimeConfig` before registering the OMP adapter.
* Use a deterministic provider namespace such as `ga-tui-<entry-name>` so OMP model selectors can use `<provider>/<model>`.
* For MVP, map OpenAI-compatible GA-TUI entries to OMP `api: openai-completions` or `api: openai-responses` based on `api_mode`; Anthropic mapping can remain out of scope unless directly supported by OMP schema with no extra auth semantics.
* Update terminal frame handling so `message_end`, `turn_end`, and `agent_end` with error fields produce `[Oh My Pi] ...` text.

## Decision (ADR-lite)

**Context**: Embedded OMP currently inherits system OMP config and therefore may use the user's unrelated default model and credentials.

**Decision**: GA-TUI will maintain an isolated OMP `agentDir` under its own harness runtime directory and generate OMP config/model files from GA-TUI's model manager before launching OMP.

**Consequences**: This avoids system OMP pollution and makes `/model` the single visible settings surface. The tradeoff is that GA-TUI must maintain a narrow OMP config projection and may not support every OMP provider feature in the first slice.

## Out of Scope

* Modifying `~/.omp/agent/config.yml`, `~/.omp/agent/models.yml`, or system OMP auth storage.
* Building a full bidirectional OMP model manager UI.
* Migrating OMP's own memory, vault, plugins, rules, or task agents into GA-TUI.
* Enabling unrestricted OMP host tools, host URI schemes, or direct approval mapping.
* Supporting every non-OpenAI-compatible GA-TUI provider in the initial generated `models.yml`.

## Technical Notes

* `src/ga_tui/ohmypi_provider.py` currently owns `OhMyPiRpcAgent`, `OhMyPiRuntimeAdapter`, `ohmypi_rpc_command()`, memory prompt generation, and provider metadata.
* `src/ga_tui/app.py` currently owns `load_llm_config_entries()`, `/model` UI, model validation, model switching, runtime registry composition, and app-injected OMP host tool callbacks.
* OMP source evidence is recorded in `research/local-omp-config-contract.md`.
* System OMP config hash before implementation: `cc6e3f8d7b812867006f5b64c3c094f70c424d4409a6ab737b6aa6188066c4ec`.

## Implementation Notes

* Added isolated OMP runtime helpers and `OhMyPiRuntimeConfig` / `OhMyPiRuntimeModel` in `src/ga_tui/ohmypi_provider.py`.
* Added app-layer projection from GA-TUI `/model` entries to isolated OMP `config.yml`, `models.yml`, child-process env, and startup `--model`.
* Added RPC model switching through OMP `set_model` and visible terminal error mapping for OMP error frames.
* Updated `scripts/check_policy_gates.py` with isolated runtime, child env, model-switch, error-frame, raw-secret absence, and system-config hash checks.
* Updated `.trellis/spec/backend/agent-control-protocol.md` to preserve the new executable contract.

## Verification

* `python3 -m py_compile src/ga_tui/app.py src/ga_tui/ohmypi_provider.py scripts/check_policy_gates.py` passed.
* `python3 scripts/check_policy_gates.py` passed.
* `python3 -m compileall -q src scripts` passed.
* `git diff --check` passed.
* `ga-tui-check --root /home/vimalinx/Programs/GenericAgent` passed.
* Local OMP smoke passed: `PI_CODING_AGENT_DIR=<GA-TUI harness>/runtime/ohmypi/agent omp --list-models ga-tui` returned `0` and listed GA-TUI-projected providers.
* System OMP config hash after verification: `cc6e3f8d7b812867006f5b64c3c094f70c424d4409a6ab737b6aa6188066c4ec`.
