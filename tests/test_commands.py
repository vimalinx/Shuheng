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
    assert app_module.AgentCommandCompletionDecision is commands.AgentCommandCompletionDecision
    assert app_module.agent_command_completion_decision is commands.agent_command_completion_decision
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


def test_agent_command_completion_decision_static_rows() -> None:
    assert commands.agent_command_completion_decision("agent ").kind == "none"
    root = commands.agent_command_completion_decision("/agent")
    assert root == commands.AgentCommandCompletionDecision(
        "rows",
        (("/agent", "<cmd>", "管理/运行持久子 agent", False),),
    )
    all_rows = commands.agent_command_completion_decision("/agent ")
    assert all_rows.kind == "rows"
    assert all_rows.rows[0] == ("/agent list", "", "列出子 agent", True)
    filtered = commands.agent_command_completion_decision("/agent r")
    assert filtered.kind == "rows"
    assert filtered.rows == (
        ("/agent role", "<agent> <role>", "设置子 agent 角色", False),
        ("/agent run", "<agent> <prompt>", "ask 的别名", False),
        ("/agent reply", "<agent> <text>", "answer 的别名", False),
        ("/agent remember", "<agent> <text>", "追加子 agent 记忆", False),
        ("/agent rename", "<agent> <name>", "重命名子 agent", False),
    )
    assert commands.agent_command_completion_decision("/agent unknown ").kind == "none"
    assert commands.agent_command_completion_decision("/agent templates ").kind == "none"


def test_agent_command_completion_decision_dynamic_requests() -> None:
    assert commands.agent_command_completion_decision("/agent ask ") == commands.AgentCommandCompletionDecision(
        "subagent",
        subcmd="ask",
        agent_prefix="",
    )
    assert commands.agent_command_completion_decision("/agent ask worker") == commands.AgentCommandCompletionDecision(
        "subagent",
        subcmd="ask",
        agent_prefix="worker",
    )
    assert commands.agent_command_completion_decision("/agent ask worker ").kind == "none"
    assert commands.agent_command_completion_decision("/agent info worker ") == commands.AgentCommandCompletionDecision(
        "subagent",
        subcmd="info",
        agent_prefix="worker",
    )
    assert commands.agent_command_completion_decision("/agent role worker ") == commands.AgentCommandCompletionDecision(
        "role",
        subcmd="role",
        role_agent="worker",
        role_prefix="",
        role_base="/agent role worker ",
    )
    assert commands.agent_command_completion_decision("/agent role worker re") == commands.AgentCommandCompletionDecision(
        "role",
        subcmd="role",
        role_agent="worker",
        role_prefix="re",
        role_base="/agent role worker ",
    )
    assert commands.agent_command_completion_decision("/agent role worker re extra").kind == "none"


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


def test_app_agent_command_matches_expands_dynamic_decisions() -> None:
    state = app_module.State(agent=None)
    state.subagents = {
        "alpha": app_module.SubAgentRuntime(
            agent_id="alpha",
            name="Alpha Worker",
            home="/tmp/alpha",
            status="idle",
            updated_at=20.0,
        ),
        "beta": app_module.SubAgentRuntime(
            agent_id="beta",
            name="Beta Worker",
            home="/tmp/beta",
            status="running",
            updated_at=10.0,
        ),
    }

    assert app_module.agent_command_matches("/agent ask alp", state) == [
        ("/agent ask alpha", "<prompt>", "Alpha Worker · idle", False),
    ]
    assert app_module.agent_command_matches("/agent info beta ", state) == [
        ("/agent info beta", "", "Beta Worker · running", True),
    ]
    assert app_module.agent_command_matches("/agent role alpha ver", state) == [
        ("/agent role alpha verifier", "", app_module.ROLE_TEMPLATES["verifier"]["description"], True),
    ]
