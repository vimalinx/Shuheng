"""Tests for local credential input that bypasses the LLM."""
from __future__ import annotations

import json
from typing import Any

from shuheng import app as app_module


class DummyAgent:
    pass


def state_text(state: app_module.State) -> str:
    return json.dumps(
        {
            "messages": [message.content for message in state.messages],
            "input_history": state.input_history,
            "pending_interaction": state.pending_interaction,
            "credential_request": state.credential_request,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def test_credential_request_delivers_password_only_to_registered_target() -> None:
    state = app_module.State(agent=DummyAgent())
    captured: list[tuple[str, dict[str, Any]]] = []

    def handler(password: str, request: dict[str, Any]) -> dict[str, Any]:
        captured.append((password, request))
        return {
            "status": "connected",
            "message": f"connected with {password}",
            "password": password,
            "nested": {"content": password},
        }

    app_module.register_credential_target(state, "sudo", handler, label="Sudo Password")
    host_handler = app_module.ohmypi_tui_host_tool_handler(state)
    result = host_handler(
        "credential_request",
        {
            "target": "sudo",
            "request_id": "cred-test-1",
            "purpose": "install package",
            "account": "root",
            "metadata": {"origin": "unit-test"},
        },
    )

    assert result["schema_version"] == "shuheng.tool.v1", result
    assert result["status"] == "pending", result
    assert result["request_id"] == "cred-test-1", result
    assert state.credential_request["target"] == "sudo", state.credential_request
    assert app_module.credential_input_active(state) is True

    password = "P@ssw0rd!-only-target"
    app_module.submit(state, password)

    assert captured and captured[-1][0] == password, captured
    assert captured[-1][1]["request_id"] == "cred-test-1", captured
    assert state.credential_request == {}
    assert state.input_text == ""
    assert state.input_history == []
    assert password not in json.dumps(result, ensure_ascii=False)
    assert password not in state_text(state)
    assert "[redacted credential]" in state.messages[-1].content, state.messages[-1].content


def test_credential_request_rejects_secret_bearing_args_and_unknown_targets() -> None:
    state = app_module.State(agent=DummyAgent())
    app_module.register_credential_target(state, "sudo", lambda password, request: None)
    host_handler = app_module.ohmypi_tui_host_tool_handler(state)

    forbidden = host_handler("credential_request", {"target": "sudo", "password": "leak-marker"})
    assert forbidden["status"] == "error", forbidden
    assert "password" in forbidden["forbidden_fields"], forbidden
    assert "leak-marker" not in json.dumps(forbidden, ensure_ascii=False)
    assert state.credential_request == {}

    nested_forbidden = host_handler("credential_request", {"target": "sudo", "metadata": {"messages": ["leak"]}})
    assert nested_forbidden["status"] == "error", nested_forbidden
    assert "metadata.messages" in nested_forbidden["forbidden_fields"], nested_forbidden
    assert state.credential_request == {}

    unknown = host_handler("credential_request", {"target": "missing"})
    assert unknown["status"] == "error", unknown
    assert unknown["supported_targets"] == ["sudo"], unknown
    assert state.credential_request == {}


def test_credential_input_cancel_and_secret_vault_priority() -> None:
    state = app_module.State(agent=DummyAgent())
    captured: list[str] = []
    app_module.register_credential_target(state, "sudo", lambda password, request: captured.append(password))
    host_handler = app_module.ohmypi_tui_host_tool_handler(state)

    result = host_handler("credential_request", {"target": "sudo", "request_id": "cred-cancel"})
    assert result["status"] == "pending", result
    app_module.submit(state, "/cancel")
    assert captured == []
    assert state.credential_request == {}
    assert "canceled" in state.messages[-1].content

    state.credential_request = {
        "schema_version": app_module.CREDENTIAL_REQUEST_SCHEMA,
        "request_id": "cred-secret-priority",
        "target": "sudo",
        "target_label": "Sudo Password",
    }
    state.secret_vault.pending_action = "setup_password"
    app_module.submit(state, "Aa1!aaaa")

    assert captured == []
    assert state.secret_vault.pending_action == "setup_confirm"
    assert "Aa1!aaaa" not in state_text(state)
