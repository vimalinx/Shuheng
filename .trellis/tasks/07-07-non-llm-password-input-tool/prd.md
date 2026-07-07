# PRD: Non-LLM Password Input Tool

## Goal

Add a Shuheng password/credential input tool that lets an agent request a password without ever receiving the password through the LLM prompt, chat message, host-tool result, logs, trace payload, memory, or artifact text. The password must be entered through a local masked TUI input and delivered directly to a registered local consumer.

## What I Already Know

- User wants a tool for password input.
- The password must not go through the LLM.
- Shuheng already has Secret Vault password entry that masks input and intercepts `submit(...)` before normal command/LLM handling.
- OMP host tools already expose typed Shuheng tools through `ohmypi_tui_host_tool_definitions()` and `ohmypi_tui_host_tool_handler(...)`.
- Existing host-tool results are serialized back to the runtime, so the new tool result must never contain the password.

## Assumptions

- MVP should be a reusable local target registry rather than hard-coding one external service.
- A password consumer must register a target handler in the TUI state before the tool can request a password.
- If no target handler exists, the tool should fail closed and list supported non-secret target ids.
- The LLM can request `credential_request`, but it only gets a pending/status response with a request id.
- The user's next local input is masked and consumed by Shuheng, not by the LLM.

## Requirements

- Add a typed OMP/Shuheng host tool named `credential_request`.
- Tool args include `target`, optional `request_id`, optional `purpose`, optional `account`, and optional safe metadata.
- Tool returns only safe status fields such as `request_id`, `target`, `status`, and `note`.
- Tool must not accept or return a password field.
- Tool must fail closed when the TUI state is absent, target is absent, or no registered local handler exists.
- TUI must show a masked password prompt for the pending credential request.
- While a credential request is pending, submitted input must go directly to the registered target handler.
- The entered password must not be appended to `state.messages`, `input_history`, `pending_interaction`, ledgers, traces, artifacts, or host-tool result payloads.
- `/cancel`, `/lock`, or an empty password should cancel or reject the pending credential input without leaking the value.
- Secret Vault password entry keeps priority over generic credential input.

## Non-Goals

- Do not store reusable passwords.
- Do not build a credential manager or Secret Vault replacement.
- Do not implement SSH/sudo/browser-specific connectors in this slice.
- Do not let the LLM read, echo, inspect, transform, or summarize the password.
- Do not route password text through `request_user_input`, `ask_user`, queued user input, or main/subagent chat.

## Acceptance Criteria

- `credential_request` appears in OMP typed governed host tools.
- Calling `credential_request` with a registered target sets a pending masked credential input and returns a safe pending response.
- Entering a password calls the registered local handler with the plaintext and clears input state.
- The handler result can produce a safe user-visible message, but the password never appears in messages, input history, tool result, trace, or artifacts.
- Calling `credential_request` with `password`, `secret`, `token`, `content`, or `messages` fields returns an error and does not set pending input.
- Secret Vault password flow still works.
- Targeted tests, policy gates, full tests, lint, release hygiene, runtime smoke, build, wheel smoke, and `shuheng-check` pass.

## Technical Notes

- Reuse the Secret Vault input interception and masking pattern from `secret_password_entry_active(...)`, `secret_prompt_text(...)`, `secret_hint_lines(...)`, and `submit(...)`.
- Reuse typed host tool wiring around `ohmypi_typed_governed_host_tool_definitions()` and `ohmypi_tui_host_tool_handler(...)`.
- Keep all credential state runtime-local in `State`; do not persist it.
