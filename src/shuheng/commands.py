"""Pure command completion helpers for Shuheng's TUI command prompt."""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

CommandCandidate = tuple[str, str, str, bool]
SkillCompletionCandidate = tuple[str, str, str, str]
AgentCommandCompletionKind = Literal["none", "rows", "subagent", "role"]


@dataclass(frozen=True)
class AgentCommandCompletionDecision:
    kind: AgentCommandCompletionKind
    rows: tuple[CommandCandidate, ...] = ()
    subcmd: str = ""
    agent_prefix: str = ""
    role_agent: str = ""
    role_prefix: str = ""
    role_base: str = ""


@dataclass(frozen=True)
class TransientSkillInvocation:
    skill_refs: tuple[str, ...] = ()
    prompt: str = ""


AGENT_SUBCOMMANDS: list[CommandCandidate] = [
    ("list", "", "列出子 agent", True),
    ("new", "[persistent:] [role:]<name> [| profile]", "新建临时子 agent；加 persistent: 创建持久 agent", False),
    ("role", "<agent> <role>", "设置子 agent 角色", False),
    ("settings", "<agent>", "打开 agent 详细设置", False),
    ("model", "<agent> [model|inherit]", "设置 agent 默认模型", False),
    ("skill", "<agent> [add|remove|set|clear|list] [skill-ref ...]", "配置 agent 专属 skill", False),
    ("plugin", "<agent> [add|remove|set|clear|list] [plugin-skill-ref ...]", "配置 agent 专属插件 skill", False),
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
    "plugin",
    "info",
    "stop",
    "delete",
}
AGENT_SUBCOMMANDS_SEND_AFTER_AGENT = {"memory", "profile", "info", "settings", "model", "skill", "plugin", "stop", "delete"}
AGENT_SUBCOMMAND_NAMES = {cmd for cmd, _args, _desc, _sendable in AGENT_SUBCOMMANDS}
WORKSPACE_SUBCOMMANDS: list[CommandCandidate] = [
    ("list", "", "列出工作区", True),
    ("current", "", "显示自动推断的当前工作区", True),
    ("refresh", "", "刷新自动工作区索引", True),
]


def completion_insert_text(candidate: CommandCandidate) -> str:
    cmd, _args, _desc, sendable = candidate
    return cmd if sendable else cmd.rstrip() + " "


def parse_transient_skill_invocation(text: str) -> TransientSkillInvocation:
    """Parse leading `$skill` tokens without treating mid-prompt `$` as commands."""
    rest = (text or "").strip()
    refs: list[str] = []
    while rest.startswith("$"):
        parts = rest.split(maxsplit=1)
        token = parts[0][1:].strip()
        if not token:
            break
        refs.append(token.removeprefix("skill://").strip())
        rest = parts[1].lstrip() if len(parts) == 2 else ""
    return TransientSkillInvocation(tuple(ref for ref in refs if ref), rest)


def transient_skill_completion_rows(
    text: str,
    skill_candidates: Iterable[SkillCompletionCandidate],
) -> list[CommandCandidate]:
    raw = text or ""
    match = re.match(r"^\$(\S*)$", raw.strip())
    if not match:
        return []
    prefix = (match.group(1) or "").removeprefix("skill://").lower()
    name_matches: list[CommandCandidate] = []
    summary_matches: list[CommandCandidate] = []
    for ref, name, source, summary in skill_candidates:
        ref_text = str(ref or "").strip().removeprefix("skill://").strip()
        name_text = str(name or ref_text).strip()
        if not ref_text:
            continue
        hay_name = f"{ref_text} {name_text}".lower()
        hay_summary = str(summary or "").lower()
        row = (
            f"${ref_text}",
            "",
            " · ".join(part for part in (str(source or "").strip(), str(summary or "").strip()) if part),
            False,
        )
        if not prefix or hay_name.startswith(prefix) or ref_text.lower().startswith(prefix) or name_text.lower().startswith(prefix):
            name_matches.append(row)
        elif prefix in hay_name:
            name_matches.append(row)
        elif prefix in hay_summary:
            summary_matches.append(row)
    return name_matches + summary_matches


def top_level_command_matches(text: str, candidates: Iterable[CommandCandidate]) -> list[CommandCandidate]:
    raw = text or ""
    stripped = raw.strip()
    if not stripped.startswith("/") or " " in stripped:
        return []
    stripped_l = stripped.lower()
    return [candidate for candidate in candidates if candidate[0].lower().startswith(stripped_l)]


def category_command_completion_rows(
    text: str,
    category_counts: Iterable[tuple[str, int]],
) -> list[CommandCandidate]:
    raw = text or ""
    match = re.match(r"^/(filter|collapse|expand)\s+(.*)$", raw, re.I)
    if not match:
        return []
    cmd = match.group(1).lower()
    prefix = (match.group(2) or "").strip().lower()
    rows: list[CommandCandidate] = []
    if cmd == "filter" and "off".startswith(prefix):
        rows.append(("/filter off", "", "关闭分类筛选", True))
    if cmd in {"collapse", "expand"} and "all".startswith(prefix):
        rows.append((f"/{cmd} all", "", "全部分类", True))
    for label, count in category_counts:
        label_text = str(label)
        if prefix and not label_text.lower().startswith(prefix):
            continue
        rows.append((f"/{cmd} {label_text}", "", f"{int(count)} 个会话", True))
    return rows


def approval_command_completion_rows(
    text: str,
    approval_candidates: Iterable[tuple[str, str]],
) -> list[CommandCandidate]:
    raw = text or ""
    match = re.match(r"^/(approve|reject)\s+(.*)$", raw, re.I)
    if not match:
        return []
    cmd = match.group(1).lower()
    prefix = (match.group(2) or "").strip()
    rows: list[CommandCandidate] = []
    for approval_id, summary in approval_candidates:
        approval_text = str(approval_id)
        if prefix and not approval_text.startswith(prefix):
            continue
        rows.append((f"/{cmd} {approval_text}", "", str(summary), True))
    return rows


def agent_command_completion_decision(text: str) -> AgentCommandCompletionDecision:
    raw = text or ""
    if not re.match(r"^/agent(?:\s|$)", raw):
        return AgentCommandCompletionDecision("none")
    if raw == "/agent":
        return AgentCommandCompletionDecision(
            "rows",
            (("/agent", "<cmd>", "管理/运行持久子 agent", False),),
        )
    rest = raw[len("/agent"):].lstrip()
    if not rest:
        return AgentCommandCompletionDecision(
            "rows",
            tuple((f"/agent {cmd}", args, desc, sendable) for cmd, args, desc, sendable in AGENT_SUBCOMMANDS),
        )
    parts = rest.split()
    trailing_space = raw.endswith(" ")
    sub_prefix = parts[0] if parts else ""
    if len(parts) == 1 and not trailing_space:
        sub_prefix_l = sub_prefix.lower()
        return AgentCommandCompletionDecision(
            "rows",
            tuple(
                (f"/agent {cmd}", args, desc, sendable)
                for cmd, args, desc, sendable in AGENT_SUBCOMMANDS
                if cmd.startswith(sub_prefix_l)
            ),
        )
    subcmd = sub_prefix.lower()
    if subcmd not in AGENT_SUBCOMMAND_NAMES:
        return AgentCommandCompletionDecision("none")
    if subcmd not in AGENT_SUBCOMMANDS_REQUIRING_AGENT:
        return AgentCommandCompletionDecision("none")
    agent_prefix = parts[1] if len(parts) >= 2 else ""
    if subcmd == "role":
        if len(parts) > 3 or (len(parts) == 3 and trailing_space):
            return AgentCommandCompletionDecision("none")
        if len(parts) >= 3 or (len(parts) == 2 and trailing_space):
            role_agent = parts[1]
            role_prefix = parts[2].lower() if len(parts) >= 3 else ""
            return AgentCommandCompletionDecision(
                "role",
                subcmd=subcmd,
                role_agent=role_agent,
                role_prefix=role_prefix,
                role_base=f"/agent role {role_agent} ",
            )
    if len(parts) > 2 or (len(parts) == 2 and trailing_space and subcmd not in AGENT_SUBCOMMANDS_SEND_AFTER_AGENT):
        return AgentCommandCompletionDecision("none")
    return AgentCommandCompletionDecision("subagent", subcmd=subcmd, agent_prefix=agent_prefix)


def subagent_settings_target_from_command(text: str) -> str:
    raw = (text or "").strip()
    match = re.match(r"/agent\s+(?:settings|setting|config|detail|details|prefs)\s+(\S+)\s*$", raw, re.I)
    if match:
        return match.group(1)
    match = re.match(r"/agent\s+model\s+(\S+)\s*$", raw, re.I)
    return match.group(1) if match else ""


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
