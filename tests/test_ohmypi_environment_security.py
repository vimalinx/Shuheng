"""Security contracts for the OMP child process environment and posture."""
from __future__ import annotations

from pathlib import Path

from shuheng import app as app_module
from shuheng import ohmypi_provider


def test_omp_child_environment_is_allowlisted_by_default() -> None:
    env = ohmypi_provider.ohmypi_subprocess_env(
        agent_dir="/tmp/shuheng-omp-agent",
        base_env={
            "PATH": "/usr/bin",
            "HOME": "/home/tester",
            "LANG": "C.UTF-8",
            "LC_MESSAGES": "C",
            "OPENAI_API_KEY": "ambient-openai-secret",
            "AWS_SECRET_ACCESS_KEY": "ambient-aws-secret",
            "SSH_AUTH_SOCK": "/tmp/agent.sock",
        },
        env_overrides={
            "SHUHENG_OMP_API_KEY_ABC123": "projected-model-secret",
            "UNTRUSTED_OVERRIDE": "must-not-pass",
        },
    )

    assert env == {
        "PATH": "/usr/bin",
        "HOME": "/home/tester",
        "LANG": "C.UTF-8",
        "LC_MESSAGES": "C",
        "PI_CODING_AGENT_DIR": "/tmp/shuheng-omp-agent",
        "SHUHENG_OMP_API_KEY_ABC123": "projected-model-secret",
    }


def test_omp_child_environment_supports_explicit_named_opt_in() -> None:
    env = ohmypi_provider.ohmypi_subprocess_env(
        agent_dir="/tmp/shuheng-omp-agent",
        base_env={
            "PATH": "/usr/bin",
            "SHUHENG_OMP_INHERIT_ENV": "CUSTOM_CERT, EXPLICIT_TOKEN invalid-name MISSING_NAME",
            "CUSTOM_CERT": "/opt/cert.pem",
            "EXPLICIT_TOKEN": "operator-approved-secret",
            "invalid-name": "must-not-pass",
        },
    )

    assert env["CUSTOM_CERT"] == "/opt/cert.pem"
    assert env["EXPLICIT_TOKEN"] == "operator-approved-secret"
    assert "SHUHENG_OMP_INHERIT_ENV" not in env
    assert "invalid-name" not in env
    assert "MISSING_NAME" not in env


def test_omp_child_environment_makes_user_local_bun_executable_for_omp_shebang(tmp_path: Path) -> None:
    bun_install = tmp_path / "custom-bun"
    bun = bun_install / "bin" / "bun"
    bun.parent.mkdir(parents=True)
    bun.write_text("#!/bin/sh\n", encoding="utf-8")
    bun.chmod(0o700)

    env = ohmypi_provider.ohmypi_subprocess_env(
        agent_dir="/tmp/shuheng-omp-agent",
        base_env={"HOME": str(tmp_path), "BUN_INSTALL": str(bun_install), "PATH": "/usr/bin"},
    )

    assert env["PATH"].split(":", 1) == [str(bun.parent), "/usr/bin"]
    assert env["BUN_INSTALL"] == str(bun_install)


def test_omp_binary_resolution_honors_custom_bun_install(monkeypatch, tmp_path: Path) -> None:
    omp = tmp_path / "custom-bun" / "bin" / "omp"
    omp.parent.mkdir(parents=True)
    omp.write_text("#!/bin/sh\n", encoding="utf-8")
    omp.chmod(0o700)
    monkeypatch.setenv("BUN_INSTALL", str(tmp_path / "custom-bun"))
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("SHUHENG_OHMYPI_BIN", raising=False)

    assert ohmypi_provider.resolve_ohmypi_binary() == str(omp)


def test_runtime_model_projection_keeps_only_generated_key_env(monkeypatch, tmp_path: Path) -> None:
    entry = app_module.LLMConfigEntry(
        "native_oai_config",
        "native_oai",
        {
            "name": "primary",
            "apikey": "model-secret",
            "apibase": "https://example.test/v1",
            "model": "test-model",
        },
    )
    monkeypatch.setattr(app_module, "load_llm_config_entries", lambda: ([entry], {"llm_nos": ["primary"]}, [], ""))
    monkeypatch.setattr(app_module, "AGENT_HARNESS_DIR", str(tmp_path / "harness"))

    config = app_module.build_ohmypi_runtime_config(
        write_files=False,
        base_env={"PATH": "/usr/bin", "OPENAI_API_KEY": "ambient-secret"},
    )

    projected_keys = [key for key in config.env if key.startswith("SHUHENG_OMP_API_KEY_")]
    assert len(projected_keys) == 1
    assert config.env[projected_keys[0]] == "model-secret"
    assert "OPENAI_API_KEY" not in config.env


def test_omp_defaults_are_governed_and_unsafe_modes_require_explicit_env(monkeypatch) -> None:
    monkeypatch.delenv("SHUHENG_OMP_PERMISSION_PROFILE", raising=False)
    monkeypatch.delenv("SHUHENG_DEFAULT_PERMISSION_PROFILE", raising=False)
    monkeypatch.delenv("SHUHENG_OMP_APPROVAL_MODE", raising=False)

    assert app_module.default_omp_permission_profile() == app_module.PERMISSION_PROFILE_STANDARD
    assert app_module.default_ohmypi_approval_mode() == "write"
    assert ohmypi_provider.normalized_ohmypi_approval_mode("") == "write"
    assert ohmypi_provider.normalized_ohmypi_approval_mode("unknown") == "write"
    assert ohmypi_provider.ohmypi_rpc_command(binary="/opt/omp", extra_args=[])[-2:] == [
        "--approval-mode",
        "write",
    ]

    monkeypatch.setenv("SHUHENG_OMP_APPROVAL_MODE", "yolo")
    assert app_module.default_omp_permission_profile() == app_module.PERMISSION_PROFILE_STANDARD
    assert app_module.default_ohmypi_approval_mode() == "write"
    assert ohmypi_provider.ohmypi_rpc_command(binary="/opt/omp", extra_args=[])[-1] == "write"

    monkeypatch.setenv("SHUHENG_OMP_PERMISSION_PROFILE", "full")
    assert app_module.default_omp_permission_profile() == app_module.PERMISSION_PROFILE_FULL
    assert app_module.default_ohmypi_approval_mode() == "yolo"
    assert ohmypi_provider.ohmypi_rpc_command(binary="/opt/omp", extra_args=[])[-2:] == [
        "--approval-mode",
        "yolo",
    ]


def test_omp_extra_args_cannot_bypass_the_canonical_approval_gate() -> None:
    command = ohmypi_provider.ohmypi_rpc_command(
        binary="/opt/omp",
        extra_args=["--approval-mode=yolo", "--model", "provider/model"],
        approval_mode="write",
        permission_profile="standard",
    )

    assert command.count("--approval-mode") == 1
    assert "--approval-mode=yolo" not in command
    assert command[command.index("--approval-mode") + 1] == "write"
    assert command[-2:] == ["--model", "provider/model"]


def test_full_prompted_mode_keeps_program_level_high_risk_gate(monkeypatch) -> None:
    permissions = app_module.permissions_for_role(
        "main_orchestrator",
        permission_profile=app_module.PERMISSION_PROFILE_FULL,
    )
    agent = ohmypi_provider.OhMyPiRpcAgent(command=["/opt/omp"])
    monkeypatch.setattr(agent, "_active_permissions", lambda: permissions)

    assert permissions["approval_required_for"]
    approved, reason = agent._should_auto_approve_extension_select(
        {
            "options": ["Approve", "Deny"],
            "title": "Allow tool: edit",
            "message": "update a project source file",
        }
    )
    assert approved is True and reason == "approved:edit"

    approved, reason = agent._should_auto_approve_extension_select(
        {
            "options": ["Approve", "Deny"],
            "title": "Allow tool: bash",
            "message": "git push --force origin main",
        }
    )
    assert approved is False and reason == "tool_requires_human_review:bash"

    approved, reason = agent._should_auto_approve_extension_select(
        {
            "options": ["Approve", "Deny"],
            "title": "Allow tool: bash",
            "message": "rm -rf /tmp/example",
        }
    )
    assert approved is False and reason == "risky_tool_prompt"


def test_always_ask_remains_an_explicit_governed_mode(monkeypatch) -> None:
    monkeypatch.setenv("SHUHENG_OMP_APPROVAL_MODE", "always-ask")

    assert app_module.default_ohmypi_approval_mode() == "always-ask"
    assert ohmypi_provider.ohmypi_rpc_command(binary="/opt/omp", extra_args=[])[-1] == "always-ask"
