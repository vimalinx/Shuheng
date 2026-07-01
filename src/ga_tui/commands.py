"""Pure command completion helpers for Shuheng's TUI command prompt."""
from __future__ import annotations

import re

CommandCandidate = tuple[str, str, str, bool]


AGENT_SUBCOMMANDS: list[CommandCandidate] = [
    ("list", "", "列出子 agent", True),
    ("new", "[persistent:] [role:]<name> [| profile]", "新建临时子 agent；加 persistent: 创建持久 agent", False),
    ("role", "<agent> <role>", "设置子 agent 角色", False),
    ("settings", "<agent>", "打开 agent 详细设置", False),
    ("model", "<agent> [model|inherit]", "设置 agent 默认模型", False),
    ("skill", "<agent> [add|remove|set|clear|list] [skill-ref ...]", "配置 agent 专属 skill", False),
    ("templates", "", "列出角色模板", True),
    ("ask", "<agent> <prompt>", "让子 agent 执行任务", False),
    ("run", "<agent> <prompt>", "ask 的别名", False),
    ("input", "<agent> <prompt>", "ask 的别名", False),
    ("answer", "<agent> <text>", "回复等待输入的子 agent", False),
    ("reply", "<agent> <text>", "answer 的别名", False),
    ("memory", "<agent>", "查看子 agent 记忆", False),
    ("remember", "<agent> <text>", "追加子 agent 记忆", False),
    ("profile", "<agent> [text]", "查看/更新 profile", False),
    ("rename", "<agent> <name>", "重命名子 agent", False),
    ("info", "<agent>", "查看子 agent 详情", False),
    ("stop", "<agent>", "停止子 agent", False),
    ("delete", "<agent>", "移除子 agent", False),
]
AGENT_SUBCOMMANDS_REQUIRING_AGENT = {
    "ask",
    "run",
    "input",
    "answer",
    "reply",
    "memory",
    "remember",
    "profile",
    "rename",
    "role",
    "settings",
    "model",
    "skill",
    "info",
    "stop",
    "delete",
}
AGENT_SUBCOMMANDS_SEND_AFTER_AGENT = {"memory", "profile", "info", "settings", "model", "skill", "stop", "delete"}
WORKSPACE_SUBCOMMANDS: list[CommandCandidate] = [
    ("list", "", "列出工作区", True),
    ("current", "", "显示自动推断的当前工作区", True),
    ("refresh", "", "刷新自动工作区索引", True),
]


def completion_insert_text(candidate: CommandCandidate) -> str:
    cmd, _args, _desc, sendable = candidate
    return cmd if sendable else cmd.rstrip() + " "


def archived_command_matches(text: str) -> list[CommandCandidate]:
    raw = text or ""
    match = re.match(r"^/archived\s+(.*)$", raw, re.I)
    if not match:
        return []
    prefix = (match.group(1) or "").strip().lower()
    options = [("on", "显示归档"), ("off", "隐藏归档"), ("toggle", "切换归档视图")]
    return [
        (f"/archived {name}", "", desc, True)
        for name, desc in options
        if not prefix or name.startswith(prefix)
    ]


def workspace_command_matches(text: str) -> list[CommandCandidate]:
    raw = text or ""
    if not re.match(r"^/workspaces?(?:\s|$)", raw, re.I):
        return []
    if raw.strip().lower() == "/workspaces":
        return [("/workspaces", "", "列出项目工作区 provenance", True)]
    rest = re.sub(r"^/workspace\s*", "", raw, flags=re.I)
    if raw.lower().startswith("/workspaces"):
        rest = re.sub(r"^/workspaces\s*", "", raw, flags=re.I)
    if not rest:
        return [("/workspace", "<cmd>", "查看项目工作区 provenance", False)]
    parts = rest.split()
    trailing_space = raw.endswith(" ")
    sub_prefix = parts[0].lower() if parts else ""
    if len(parts) == 1 and not trailing_space:
        return [
            (f"/workspace {cmd}", args, desc, sendable)
            for cmd, args, desc, sendable in WORKSPACE_SUBCOMMANDS
            if cmd.startswith(sub_prefix)
        ]
    return []
