"""Tests for pure command completion helpers."""
from __future__ import annotations

from ga_tui import app as app_module
from ga_tui import commands


def test_app_command_completion_helpers_reexport_module_symbols() -> None:
    assert app_module.AGENT_SUBCOMMANDS is commands.AGENT_SUBCOMMANDS
    assert app_module.AGENT_SUBCOMMANDS_REQUIRING_AGENT is commands.AGENT_SUBCOMMANDS_REQUIRING_AGENT
    assert app_module.AGENT_SUBCOMMANDS_SEND_AFTER_AGENT is commands.AGENT_SUBCOMMANDS_SEND_AFTER_AGENT
    assert app_module.WORKSPACE_SUBCOMMANDS is commands.WORKSPACE_SUBCOMMANDS
    assert app_module.completion_insert_text is commands.completion_insert_text
    assert app_module.archived_command_matches is commands.archived_command_matches
    assert app_module.workspace_command_matches is commands.workspace_command_matches


def test_completion_insert_text_preserves_sendable_behavior() -> None:
    assert commands.completion_insert_text(("/archived on", "", "显示归档", True)) == "/archived on"
    assert commands.completion_insert_text(("/workspace", "<cmd>", "查看项目工作区 provenance", False)) == "/workspace "
    assert commands.completion_insert_text(("/agent new ", "", "新建", False)) == "/agent new "


def test_archived_command_matches_filter_by_prefix() -> None:
    assert commands.archived_command_matches("/archived ") == [
        ("/archived on", "", "显示归档", True),
        ("/archived off", "", "隐藏归档", True),
        ("/archived toggle", "", "切换归档视图", True),
    ]
    assert commands.archived_command_matches("/archived o") == [
        ("/archived on", "", "显示归档", True),
        ("/archived off", "", "隐藏归档", True),
    ]
    assert commands.archived_command_matches("/ARCHIVED T") == [("/archived toggle", "", "切换归档视图", True)]
    assert commands.archived_command_matches("/archive ") == []


def test_workspace_command_matches_support_singular_and_plural_roots() -> None:
    assert commands.workspace_command_matches("/workspaces") == [
        ("/workspaces", "", "列出项目工作区 provenance", True),
    ]
    assert commands.workspace_command_matches("/workspace ") == [
        ("/workspace", "<cmd>", "查看项目工作区 provenance", False),
    ]
    assert commands.workspace_command_matches("/workspaces ") == [
        ("/workspaces", "", "列出项目工作区 provenance", True),
    ]


def test_workspace_command_matches_filter_subcommands_and_reject_extra_args() -> None:
    assert commands.workspace_command_matches("/workspace r") == [
        ("/workspace refresh", "", "刷新自动工作区索引", True),
    ]
    assert commands.workspace_command_matches("/workspace c") == [
        ("/workspace current", "", "显示自动推断的当前工作区", True),
    ]
    assert commands.workspace_command_matches("/workspace refresh ") == []
    assert commands.workspace_command_matches("/workspace refresh extra") == []
    assert commands.workspace_command_matches("/work ") == []


def test_app_command_matches_still_uses_extracted_workspace_and_archived_helpers() -> None:
    assert app_module.command_matches("/archived t") == commands.archived_command_matches("/archived t")
    assert app_module.command_matches("/workspace r") == commands.workspace_command_matches("/workspace r")
