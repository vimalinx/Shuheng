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
    assert app_module.top_level_command_matches is commands.top_level_command_matches
    assert app_module.category_command_completion_rows is commands.category_command_completion_rows
    assert app_module.AgentCommandCompletionDecision is commands.AgentCommandCompletionDecision
    assert app_module.agent_command_completion_decision is commands.agent_command_completion_decision
    assert app_module.archived_command_matches is commands.archived_command_matches
    assert app_module.workspace_command_matches is commands.workspace_command_matches


def test_completion_insert_text_preserves_sendable_behavior() -> None:
    assert commands.completion_insert_text(("/archived on", "", "显示归档", True)) == "/archived on"
    assert commands.completion_insert_text(("/workspace", "<cmd>", "查看项目工作区 provenance", False)) == "/workspace "
    assert commands.completion_insert_text(("/agent new ", "", "新建", False)) == "/agent new "


def test_top_level_command_matches_filter_visible_candidates() -> None:
    candidates = [
        ("/model", "", "管理模型", True),
        ("/memory", "", "记忆", True),
        ("/help", "", "帮助", True),
    ]

    assert commands.top_level_command_matches("model", candidates) == []
    assert commands.top_level_command_matches("/MO", candidates) == [("/model", "", "管理模型", True)]
    assert commands.top_level_command_matches("/m", candidates) == [
        ("/model", "", "管理模型", True),
        ("/memory", "", "记忆", True),
    ]
    assert commands.top_level_command_matches("/model extra", candidates) == []
    assert commands.top_level_command_matches("/unknown", candidates) == []


def test_top_level_command_matches_do_not_invent_hidden_aliases() -> None:
    visible_candidates = [
        ("/model", "", "管理模型", True),
        ("/help", "", "帮助", True),
    ]

    assert commands.top_level_command_matches("/mo", visible_candidates) == [("/model", "", "管理模型", True)]
    assert commands.top_level_command_matches("/ll", visible_candidates) == []
    assert commands.top_level_command_matches("/models", visible_candidates) == []
    assert commands.top_level_command_matches(
        "/ll",
        [*visible_candidates, ("/llm", "", "隐藏兼容别名", True)],
    ) == [("/llm", "", "隐藏兼容别名", True)]


def test_category_command_completion_rows_use_explicit_category_counts() -> None:
    category_counts = [("Work", 2), ("Personal", 1)]

    assert commands.category_command_completion_rows("/filter ", category_counts) == [
        ("/filter off", "", "关闭分类筛选", True),
        ("/filter Work", "", "2 个会话", True),
        ("/filter Personal", "", "1 个会话", True),
    ]
    assert commands.category_command_completion_rows("/filter o", category_counts) == [
        ("/filter off", "", "关闭分类筛选", True),
    ]
    assert commands.category_command_completion_rows("/filter w", category_counts) == [
        ("/filter Work", "", "2 个会话", True),
    ]
    assert commands.category_command_completion_rows("/collapse ", category_counts) == [
        ("/collapse all", "", "全部分类", True),
        ("/collapse Work", "", "2 个会话", True),
        ("/collapse Personal", "", "1 个会话", True),
    ]
    assert commands.category_command_completion_rows("/expand p", category_counts) == [
        ("/expand Personal", "", "1 个会话", True),
    ]
    assert commands.category_command_completion_rows("/filter", category_counts) == []
    assert commands.category_command_completion_rows("/category ", category_counts) == []


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


def test_app_category_command_matches_keeps_history_owned_counts_and_sorting() -> None:
    state = app_module.State(agent=None)
    alpha_path = "/tmp/shuheng-alpha.jsonl"
    beta_path = "/tmp/shuheng-beta.jsonl"
    beta_two_path = "/tmp/shuheng-beta-two.jsonl"
    state.history = [
        (beta_path, 20.0, "", 1),
        (alpha_path, 10.0, "", 1),
        (beta_two_path, 30.0, "", 1),
    ]
    state.session_meta = {
        app_module.session_key(alpha_path): {"category": "Alpha"},
        app_module.session_key(beta_path): {"category": "Beta"},
        app_module.session_key(beta_two_path): {"category": "Beta"},
    }

    assert app_module.category_command_matches("/filter ", state) == [
        ("/filter off", "", "关闭分类筛选", True),
        ("/filter Alpha", "", "1 个会话", True),
        ("/filter Beta", "", "2 个会话", True),
    ]
    assert app_module.category_command_matches("/collapse b", state) == [
        ("/collapse Beta", "", "2 个会话", True),
    ]
    assert app_module.command_matches("/expand a", state) == [
        ("/expand all", "", "全部分类", True),
        ("/expand Alpha", "", "1 个会话", True),
    ]
    assert app_module.category_command_matches("/filter ", None) == []


def test_app_command_matches_uses_top_level_helper_for_static_fallback() -> None:
    assert app_module.command_matches("model") == []
    assert app_module.command_matches("/MO") == commands.top_level_command_matches("/MO", app_module.COMMANDS)
    assert [cmd for cmd, _args, _desc, _sendable in app_module.command_matches("/mo")] == ["/model"]
    assert app_module.command_matches("/model extra") == []
    assert app_module.command_matches("/ll") == []
    assert app_module.command_matches("/models") == []


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
