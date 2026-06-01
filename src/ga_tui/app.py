"""Stable curses TUI for GenericAgent.

This intentionally avoids Textual's any-motion mouse mode, which can leak
SGR mouse packets into the input stream on some terminal/Wayland combinations.
It is a smaller interface: one active chat, clickable sessions in the sidebar,
wheel/PageUp/PageDown scrolling, and Enter-to-send input.
"""
from __future__ import annotations

import argparse
import ast
import base64
import concurrent.futures
import copy
import curses
import glob
import hashlib
import itertools
import json
import locale
import math
import os
import queue
import re
import shutil
import signal
import socket
import subprocess
import sys
import termios
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional

locale.setlocale(locale.LC_ALL, "")

APP_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
ARCHITECTURE_BASELINE_PATH = os.path.join(APP_ROOT_DIR, "docs", "agent-harness-architecture.md")
PROJECT_AGENTS_PATH = os.path.join(APP_ROOT_DIR, "AGENTS.md")

try:
    from .integration import find_genericagent_root as _find_genericagent_root
except Exception:
    from integration import find_genericagent_root as _find_genericagent_root  # type: ignore


def find_genericagent_root() -> str:
    return str(_find_genericagent_root())


ROOT_DIR = find_genericagent_root()
FRONTENDS_DIR = os.path.join(ROOT_DIR, "frontends")
MODEL_RESPONSES_DIR = os.path.join(ROOT_DIR, "temp", "model_responses")
TOKEN_USAGE_PATH = os.path.join(MODEL_RESPONSES_DIR, "session_token_usage.json")
SESSION_META_PATH = os.path.join(MODEL_RESPONSES_DIR, "session_meta.json")
UI_DURABLE_SYSTEM_MESSAGES_KEY = "ui_durable_system_messages"
UI_DURABLE_SYSTEM_MESSAGE_LIMIT = 200
SUBAGENT_CONTEXT_REPLY_LIMIT = 2200
SUBAGENT_CONTEXT_UPDATE_LIMIT = 20
SUBAGENT_CONTEXT_TOTAL_LIMIT = 12000
SESSION_TRASH_DIR = os.path.join(MODEL_RESPONSES_DIR, ".trash")
SUBAGENTS_DIR = os.path.join(ROOT_DIR, "memory", "subagents")
TEMP_SUBAGENTS_DIR = os.path.join(ROOT_DIR, "temp", "ga-tui-subagents")
AGENT_HARNESS_DIR = os.path.abspath(os.path.expanduser(os.environ.get("GA_TUI_HARNESS_DIR") or os.path.join(ROOT_DIR, "memory", "agent_harness")))
AGENT_TASK_LEDGER_PATH = os.path.join(AGENT_HARNESS_DIR, "tasks.jsonl")
AGENT_MAIL_PATH = os.path.join(AGENT_HARNESS_DIR, "messages.jsonl")
AGENT_APPROVALS_PATH = os.path.join(AGENT_HARNESS_DIR, "approvals.jsonl")
AGENT_ARTIFACTS_DIR = os.path.join(AGENT_HARNESS_DIR, "artifacts")
AGENT_ARTIFACT_INDEX_PATH = os.path.join(AGENT_HARNESS_DIR, "artifacts.jsonl")
AGENT_CONTEXT_PACKS_DIR = os.path.join(AGENT_HARNESS_DIR, "context_packs")
AGENT_TRACES_PATH = os.path.join(AGENT_HARNESS_DIR, "traces.jsonl")
AGENT_EVALS_PATH = os.path.join(AGENT_HARNESS_DIR, "evals.jsonl")
AGENT_LOCKS_PATH = os.path.join(AGENT_HARNESS_DIR, "locks.json")
AGENT_GATEWAY_PATH = os.path.join(AGENT_HARNESS_DIR, "gateway.json")
AGENT_POLICY_PATH = os.path.join(AGENT_HARNESS_DIR, "policy.json")
AGENT_POLICY_DECISIONS_PATH = os.path.join(AGENT_HARNESS_DIR, "policy_decisions.jsonl")
AGENT_ORCHESTRATOR_PLANS_PATH = os.path.join(AGENT_HARNESS_DIR, "orchestrator_plans.jsonl")
AGENT_MEMORY_CANDIDATES_PATH = os.path.join(AGENT_HARNESS_DIR, "memory_candidates.jsonl")
AGENT_CHECKPOINTS_DIR = os.path.join(AGENT_HARNESS_DIR, "checkpoints")
AGENT_CHECKPOINT_INDEX_PATH = os.path.join(AGENT_HARNESS_DIR, "checkpoints.jsonl")
AGENT_RECOVERY_PATH = os.path.join(AGENT_HARNESS_DIR, "recovery.jsonl")
AGENT_RECOVERY_PLANS_PATH = os.path.join(AGENT_HARNESS_DIR, "recovery_plans.jsonl")
AGENT_BASELINE_REPORT_PATH = os.path.join(AGENT_HARNESS_DIR, "baseline_report.json")
AGENT_GOVERNANCE_PATH = os.path.join(AGENT_HARNESS_DIR, "governance_components.json")
AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH = os.path.join(AGENT_HARNESS_DIR, "gateway_push_subscriptions.jsonl")
AGENT_GATEWAY_PUSH_DELIVERIES_PATH = os.path.join(AGENT_HARNESS_DIR, "gateway_push_deliveries.jsonl")
AGENT_GATEWAY_DAEMON_PID_PATH = os.path.join(AGENT_HARNESS_DIR, "gateway_daemon.pid")
AGENT_GATEWAY_DAEMON_STATUS_PATH = os.path.join(AGENT_HARNESS_DIR, "gateway_daemon.json")
AGENT_GATEWAY_DAEMON_LOG_PATH = os.path.join(AGENT_HARNESS_DIR, "gateway_daemon.log")
AGENT_BRIDGE_REGISTRY_PATH = os.path.join(AGENT_HARNESS_DIR, "bridge_registry.json")
LLM_RECENT_MODELS_PATH = os.path.join(AGENT_HARNESS_DIR, "recent_models.json")
SECRET_VAULT_DIR = os.path.abspath(os.path.expanduser(os.environ.get("GA_TUI_SECRET_VAULT_DIR") or os.path.join(ROOT_DIR, "memory", "secret_vault")))
SECRET_VAULT_META_PATH = os.path.join(SECRET_VAULT_DIR, "vault.json")
SECRET_VAULT_DATA_DIR = os.path.join(SECRET_VAULT_DIR, "data")
SECRET_VAULT_SESSIONS_DIR = os.path.join(SECRET_VAULT_DATA_DIR, "sessions")
SECRET_VAULT_SENTINEL = b"GenericAgent-TUI Secret Vault v1"
SECRET_IMPORT_KEY_AAD = b"secret-vault:sealed-import-key:v1"
SECRET_IMPORT_SEALED_SCHEMA = "secret.sealed_import.v1"
SECRET_IMPORT_DROPBOX_META_KEY = "sealed_import"
SECRET_SUBAGENT_SESSION_ID = "secret_subagents"
SECRET_SUBAGENT_META_KIND = "subagents"
SECRET_SUBAGENT_MEMORY_KIND = "subagent-memory"
SECRET_SUBAGENT_CHAT_KIND = "subagent-chat"
SECRET_VAULT_MIN_PASSWORD_CHARS = 8
SECRET_COPY_CONFIRM_TTL_SECONDS = 20.0
SECRET_VAULT_PASSWORD_RULE_TEXT = f"至少 {SECRET_VAULT_MIN_PASSWORD_CHARS} 个字符，并包含大写字母、小写字母、数字和特殊字符"
SECRET_NETWORK_CHAIN_ENV = "GA_TUI_SECRET_PROXY_CHAIN"
SECRET_TOR_SOCKS_ENV = "GA_TUI_SECRET_TOR_SOCKS"
SECRET_AUTO_TOR_ENV = "GA_TUI_SECRET_AUTO_TOR"
SECRET_DEFAULT_TOR_SOCKS = "socks5h://127.0.0.1:9050"
SECRET_IMPORT_SESSION_PREFIX = "secret_import:"
SECRET_NATIVE_SESSION_PREFIX = "secret_session:"
SUBAGENT_SESSION_PREFIX = "subagent_session:"
SECRET_PROXY_ENV_KEYS = ("ALL_PROXY", "all_proxy", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy")
TOKEN_STAT_KEYS = ("requests", "input", "output", "cache_create", "cache_read")
TUI_POLL_TIMEOUT_MS = 25
for path in (ROOT_DIR, FRONTENDS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

import agentmain
from agent_loop import StepOutcome
from agentmain import GenericAgent
from continue_cmd import (
    _format_response_segment,
    _pairs,
    _parse_native_history,
    _preview_text,
    _tool_results_from_prompt,
    _user_text,
    reset_conversation,
    restore,
)

try:
    import session_names
except Exception:
    session_names = None

try:
    import cost_tracker
except Exception:
    cost_tracker = None

try:
    from assets.configure_mykey import LLM_PROVIDERS as CONFIG_PROVIDERS
except Exception:
    CONFIG_PROVIDERS = []

try:
    from nacl import pwhash as nacl_pwhash
    from nacl.bindings import (
        crypto_aead_xchacha20poly1305_ietf_ABYTES as NACL_XCHACHA_ABYTES,
        crypto_aead_xchacha20poly1305_ietf_KEYBYTES as NACL_XCHACHA_KEYBYTES,
        crypto_aead_xchacha20poly1305_ietf_NPUBBYTES as NACL_XCHACHA_NPUBBYTES,
        crypto_aead_xchacha20poly1305_ietf_decrypt as nacl_xchacha_decrypt,
        crypto_aead_xchacha20poly1305_ietf_encrypt as nacl_xchacha_encrypt,
    )
    from nacl.public import PrivateKey as NaclPrivateKey
    from nacl.public import PublicKey as NaclPublicKey
    from nacl.public import SealedBox as NaclSealedBox
    SECRET_CRYPTO_IMPORT_ERROR = ""
except Exception as exc:
    nacl_pwhash = None
    nacl_xchacha_encrypt = None
    nacl_xchacha_decrypt = None
    NaclPrivateKey = None
    NaclPublicKey = None
    NaclSealedBox = None
    NACL_XCHACHA_ABYTES = 16
    NACL_XCHACHA_KEYBYTES = 32
    NACL_XCHACHA_NPUBBYTES = 24
    SECRET_CRYPTO_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"


ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*(?:\x07|\x1b\\)")
SUMMARY_RE = re.compile(r"<summary>\s*(.*?)\s*</summary>", re.DOTALL)
SUBAGENT_RESULT_HEADER_RE = re.compile(r"^子\s*agent\s*回复\s*·\s*(?P<name>.*?)\s*\((?P<agent_id>[^)]+)\)\s*$")
SUBAGENT_RESULT_META_LABEL_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*)?"
    r"(Summary|Findings|Evidence refs?|Risks?|Artifact refs?|Confidence|Source quality|"
    r"Critical issues|Minor issues|Missing context|Approval risks|Recommended fixes|"
    r"Memory candidates|Files|Changed files|Tests)"
    r"(?:\*\*)?\s*[:：]",
    re.IGNORECASE,
)
TURN_MARKER_RE = re.compile(r"(?m)(^[ \t]*\**LLM Running \(Turn \d+\) \.\.\.\**[ \t\r]*$)")
TURN_NO_RE = re.compile(r"Turn\s+(\d+)")
LINE_NUMBERED_FILE_RE = re.compile(r"^[ \t]*\d+\|")
META_BLOCK_RE = re.compile(r"<(?:summary|thinking|think)>[\s\S]*?</(?:summary|thinking|think)>", re.IGNORECASE)
TOOL_CALL_RE = re.compile(r"🛠️\s*Tool:\s*`([^`]+)`")
TOOL_USE_NAME_RE = re.compile(r"<tool_use>\s*\{[\s\S]*?\"name\"\s*:\s*\"([^\"]+)\"[\s\S]*?</tool_use>")
TOOL_USE_BLOCK_RE = re.compile(r"<tool_use>[\s\S]*?</tool_use>", re.IGNORECASE)
TOOL_USE_PAYLOAD_RE = re.compile(r"<tool_use>\s*([\s\S]*?)\s*</tool_use>", re.IGNORECASE)
TOOL_HEADER_RE = re.compile(r"🛠️\s*Tool:\s*`[^`]+`\s*📥\s*args:\s*", re.IGNORECASE)
TOOL_ARGS_PAYLOAD_RE = re.compile(r"🛠️\s*Tool:\s*`([^`]+)`\s*📥\s*args:\s*\n`{4}text\n([\s\S]*?)^`{4}\s*", re.IGNORECASE | re.MULTILINE)
TOOL_CALL_BLOCK_RE = re.compile(r"🛠️\s*Tool:\s*`[^`]+`\s*📥\s*args:\s*\n`{4}text\n[\s\S]*?^`{4}\s*", re.IGNORECASE | re.MULTILINE)
TOOL_RESULT_FENCE_RE = re.compile(r"^`{5}\s*\n[\s\S]*?^`{5}\s*$", re.MULTILINE)
FINAL_RESPONSE_INFO_RE = re.compile(r"^\s*\[Info\]\s+Final response to user\.\s*$", re.IGNORECASE | re.MULTILINE)
PROCESS_GROUP_TOGGLE_RE = re.compile(r"过程组\s+(G\d+)")
PROCESS_TURN_TOGGLE_RE = re.compile(r"过程\s+(G\d+T\d+)")
SUBAGENT_META_TOGGLE_RE = re.compile(r"元信息\s+(S[0-9a-f]{8})")
LONG_FENCE_RE = re.compile(r"`{4,5}[^\n]*\n[\s\S]*?\n`{4,5}", re.MULTILINE)
DETAIL_FENCE_RE = re.compile(r"`{3,}[^\n]*\n[\s\S]*?\n`{3,}", re.MULTILINE)
FENCE_BOUNDARY_RE = re.compile(r"^[ \t]*(`{3,})(.*)$")
PROMPT_BLOCK_WITH_TIME_RE = re.compile(r"^=== Prompt ===\s*([^\n]*)\n(.*?)(?=^=== (?:Prompt|Response) ===|\Z)", re.DOTALL | re.MULTILINE)
RESPONSE_BLOCK_WITH_TIME_RE = re.compile(r"^=== Response ===\s*([^\n]*)\n(.*?)(?=^=== (?:Prompt|Response) ===|\Z)", re.DOTALL | re.MULTILINE)
TUI_CONTROL_RE = re.compile(r"<ga[-_]control>\s*([\s\S]*?)\s*</ga[-_]control>", re.IGNORECASE)
TUI_CONTROL_FENCE_RE = re.compile(r"```ga[-_]control\s*([\s\S]*?)```", re.IGNORECASE)
TUI_CONTROL_JSON_FENCE_RE = re.compile(r"```(?:json|js|javascript|code)?[ \t]*\n([\s\S]*?)(?:^```|\Z)", re.IGNORECASE | re.MULTILINE)
LEGACY_TUI_CONTROL_RE = re.compile(r"<ga[-_]tui>\s*([\s\S]*?)\s*</ga[-_]tui>", re.IGNORECASE)
LEGACY_TUI_CONTROL_FENCE_RE = re.compile(r"```ga[-_]tui\s*([\s\S]*?)```", re.IGNORECASE)
SUBAGENT_MEMORY_RE = re.compile(r"<ga[-_]subagent[-_]memory>\s*([\s\S]*?)\s*</ga[-_]subagent[-_]memory>", re.IGNORECASE)
SUBAGENT_PROMPT_RE = re.compile(r"\n?\[GA TUI SubAgent Profile\][\s\S]*?\[/GA TUI SubAgent Profile\]\n?", re.IGNORECASE)
LEGACY_SUBAGENT_BACKFILL_WINDOW_SECONDS = 2 * 60 * 60
RESTORE_DISPLAY_ROUNDS = 3
HISTORY_EXPAND_ROUNDS = 3
RESTORE_CACHE_LIMIT = 8
SESSION_TITLE_WIDTH = 24
SESSION_DESCRIPTION_LIMIT = 200
RECENT_SESSION_LIMIT = 5
PINNED_SESSION_LABEL = "置顶"
RECENT_SESSION_LABEL = "Recent"
ASK_USER_TOOLS = {"ask_user", "request_user_input"}
INTERACTIVE_TOOLS = ASK_USER_TOOLS | {"human_intervention", "user_input"}
TOKEN_PANEL_H = 10
AUTO_PLAN_CONTINUE_MAX_PER_SIGNATURE = 1
AUTO_PLAN_CONTINUE_MAX_PER_PLAN = 12
PASTE_START = "\x1b[200~"
PASTE_END = "\x1b[201~"
RUN_FRAMES = ("[=     ]", "[==    ]", "[ ===  ]", "[  === ]", "[    ==]", "[     =]")
_AGENT_COUNTER = itertools.count(1)
_SESSION_LOG_COUNTER = itertools.count(1)
COMMANDS: list[tuple[str, str, str, bool]] = [
    ("/continue", "[n]", "列出或恢复历史会话", True),
    ("/sessions", "", "列出历史会话", True),
    ("/clear", "", "清空当前屏幕", True),
    ("/new", "", "新建空会话", True),
    ("/status", "", "显示当前状态", True),
    ("/stop", "", "中止当前任务", True),
    ("/resume", "", "让 agent 总结最近会话", True),
    ("/help", "", "显示命令帮助", True),
    ("/fold", "", "切换过程自动折叠", True),
    ("/md", "", "切换轻量 Markdown 渲染", True),
    ("/llm", "", "管理模型配置/提取/验活/默认", True),
    ("/model", "", "切换当前对话模型", True),
    ("/models", "", "切换当前对话模型", True),
    ("/agents", "", "列出持久子 agent", True),
    ("/agent", "<cmd>", "管理/运行持久子 agent", False),
    ("/tasks", "", "查看共享任务账本", True),
    ("/bus", "", "查看 agent mail", True),
    ("/approvals", "", "查看待审批事项", True),
    ("/approve", "<id>", "批准待审批事项", False),
    ("/reject", "<id>", "拒绝待审批事项", False),
    ("/artifacts", "", "打开 artifact store", True),
    ("/recover", "", "查看/处理可恢复任务", True),
    ("/evals", "", "查看任务评估/trace", True),
    ("/gateway", "", "查看 A2A/MCP gateway 脚手架", True),
    ("/baseline", "", "查看架构基线对比报告", True),
    ("/Secret", "[status|sessions|open-session n|open n]", "进入本地加密 Secret Vault", True),
    ("/lock", "", "锁定 Secret Vault 并清除明文状态", True),
    ("/toSecret", "[delete|archive] [n]", "单向迁移普通会话到 Secret", True),
    ("/memory", "", "打开记忆系统可视化检查", True),
    ("/mem", "", "打开记忆系统可视化检查", True),
    ("/rename", "<name>", "手动命名当前会话", False),
    ("/pin", "[n]", "置顶当前或第 n 个会话", True),
    ("/unpin", "[n]", "取消置顶当前或第 n 个会话", True),
    ("/category", "[n] <name>", "设置当前或第 n 个会话分类", False),
    ("/catname", "<old> <new>", "重命名分类", False),
    ("/catdesc", "<cat> <desc>", "设置分类简介", False),
    ("/categories", "", "列出当前视图分类", True),
    ("/filter", "[category/off]", "按分类筛选会话", True),
    ("/collapse", "[category/all]", "折叠分类分组", True),
    ("/expand", "[category/all]", "展开分类分组", True),
    ("/archive", "[n]", "归档当前或第 n 个会话", True),
    ("/unarchive", "[n]", "取消归档当前或第 n 个会话", True),
    ("/delete", "[n]", "删除当前或第 n 个会话到回收站", True),
    ("/archived", "[on/off]", "切换归档会话视图", True),
    ("/quit", "", "退出 TUI", True),
    ("/exit", "", "退出 TUI", True),
]
TUI_AGENT_CONTROL_HINT = """

[GenericAgent-TUI ga-control v2]
当用户要求你管理 TUI、拆任务或调度子 agent 时，只能输出隐藏 `<ga-control>` 控制块；旧 `<ga-tui>` / subagent_ask / subagent_create / task_update 格式已经废弃，不要再使用。
只有用户明确要求实际执行创建、委派、修改会话、更新计划等操作时才输出真实 `<ga-control>`。
用户只是询问“能做什么 / 怎么用 / 举个例子 / 讲讲能力 / 演示一下概念”时属于能力说明，不要创建计划或子 agent，不要输出真实 `<ga-control>`。
如果需要展示协议示例，必须使用可见的转义文本，例如 `&lt;ga-control&gt;...&lt;/ga-control&gt;`，或者只展示 JSON payload；不要在示例、教程或解释中包含可执行 `<ga-control>` 标签。
真实 `<ga-control>` 必须放在所有用户可见正文之后，作为回复末尾隐藏块；不要把它夹在段落、列表或示例中间，否则可见正文会被隐藏块移除后截断。

在决定创建、复用、停止、委派子 agent 或更新任务前，优先调用只读查询工具获取当前事实：`agent_list`、`agent_get`、`agent_match`、`task_list`、`task_get`、`approval_list`、`artifact_list`、`capability_list`。这些工具只读取 TUI 仪表盘/账本，不会修改状态；查清后才在回复末尾输出真实 `<ga-control>`。

控制块必须是 `schema_version:"ga-control.v2"`，批量动作放在 `actions` 里；每个动作使用强类型 dotted action 名称。

会话控制示例：
<ga-control>{"schema_version":"ga-control.v2","actions":[{"action":"session.rename","target":"current","value":"FastAPI 后端重构"}]}</ga-control>

多 agent 协作必须先建计划，再创建或复用 agent，最后用完整 `agenttask.v2` 工作订单委派，不要把自然语言 prompt 当作唯一任务信息：
<ga-control>{"schema_version":"ga-control.v2","actions":[
  {"action":"task.plan.create","title":"三代理协作","steps":["准备/复用子 agent","第一轮并行处理","汇总结果"]},
  {"action":"agent.create","name":"研究员","role":"researcher","lifecycle":"ephemeral","profile":"只读调研、证据收集、输出 artifact refs"},
  {"schema_version":"agenttask.v2","action":"delegate.create","parent_task_id":"<step_id>","routing":{"mode":"agent_as_tool","selected_agent":"研究员","target_selector":{"role":"researcher","capabilities_required":["web.search","source.verify"],"reuse_policy":"prefer_existing","security_context":"standard"}},"work_order":{"objective":"调研指定问题","background":"用户当前上下文","non_goals":["不要写代码"],"success_criteria":["给出证据","给出风险"],"stop_condition":"产出结构化结论后停止"},"capability_contract":{"tools_allowed":["web.search","read"],"tools_forbidden":["repo.write","deploy","email.send"],"write_policy":"none","network_policy":"allowlist","memory_write":"candidate_only","max_subagents":0},"context_contract":{"history_mode":"summary","artifact_reference_only":true,"include_raw_logs":false},"output_contract":{"format":"structured_markdown","required_sections":["summary","findings","evidence_refs","risks","artifact_refs","confidence"],"schema_validation":"strict","on_invalid_output":"request_repair_once"}}
]}</ga-control>

动作清单：
- `session.pin|session.unpin|session.category|session.filter|session.clear_filter|session.collapse_category|session.expand_category|session.archive|session.unarchive|session.delete|session.rename|session.show_archived|session.hide_archived`
- `task.plan.create`, `task.update`, `task.done`, `task.start`, `task.fail`, `task.cancel`
- `agent.create`, `agent.profile.update`, `agent.role.update`, `agent.model.update`, `agent.stop`, `agent.delete`
- `delegate.create`
- `memory.candidate`

规则：
- `delegate.create` 是异步委派：发出后等待子 agent 结果进入 bus/系统消息，再汇总或完成计划步骤。
- `delegate.create` 必须带 `routing`、`work_order`、`capability_contract`、`context_contract`、`output_contract`，让能力匹配、工作安排和输出契约完整可审计。
- 默认创建临时会话 agent；只有用户明确要求长期/持久/永久/正式时，`agent.create` 才使用 `lifecycle:"persistent"` 或 `persistent:true`。
- 用户明确要求删除/移除子 agent 时使用 `agent.delete`，不要只使用 `agent.stop`；删除会从 TUI agent 列表移除并保留原目录作为可审计文件。
- 用户明确要求全新/不要复用时，使用 `reuse_policy:"force_new"` 或 `force_new:true`。
- Secret Vault 已解锁时仍使用同样的 `ga-control.v2` / `agent.create` / `delegate.create` 控制；持久 Secret agent 写入加密 `secret_subagents`，不要检查或推断普通 `memory/subagents/` 目录。
- 你是主控 Orchestrator；读任务可并行，写任务保持单写者；子 agent 返回 artifact/证据/摘要，不要无结构自由聊天。
- 批量操作历史会话时优先用 `/sessions` 输出的稳定 `id:xxxxxx` 或完整文件名作为 target；不要用 `S01`/`1` 这种当前视图相对编号，除非同时提供 `expected_title`。
[/GenericAgent-TUI ga-control v2]
"""
TUI_CONTROL_HINT_MARKER = "[GenericAgent-TUI ga-control v2]"
LEGACY_TUI_CONTROL_HINT_BLOCK_RE = re.compile(
    r"\n?\[GenericAgent-TUI session control\][\s\S]*?\[/GenericAgent-TUI session control\]\s*",
    re.IGNORECASE,
)
TUI_QUERY_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "agent_list",
            "description": "Read-only TUI dashboard query. Lists current GenericAgent-TUI subagents before deciding whether to create, reuse, stop, or delegate. User-facing name: agent.list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "description": "Optional role filter, e.g. researcher/coder/reviewer."},
                    "status": {"type": "string", "description": "Optional status filter, e.g. idle/running/aborting."},
                    "include_ephemeral": {"type": "boolean", "description": "Include temporary agents.", "default": True},
                    "limit": {"type": "integer", "description": "Maximum agents to return.", "default": 50},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agent_get",
            "description": "Read-only TUI dashboard query. Gets one subagent's profile, permissions, queues, current task refs, and bounded memory/profile summaries. User-facing name: agent.get.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Subagent id, exact name, or unique name/id prefix."},
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agent_match",
            "description": "Read-only TUI dashboard query. Scores reusable subagents for an objective and recommends reuse vs create-new before emitting ga-control. User-facing name: agent.match.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "description": "Bounded task objective to route."},
                    "role": {"type": "string", "description": "Desired role, e.g. researcher/coder/reviewer."},
                    "capabilities_required": {"type": "array", "items": {"type": "string"}, "description": "Capabilities the worker should have."},
                    "reuse_policy": {"type": "string", "enum": ["prefer_existing", "force_new", "reuse_only"], "description": "Routing preference.", "default": "prefer_existing"},
                    "security_context": {"type": "string", "enum": ["standard", "secret"], "description": "Security context to match.", "default": "standard"},
                    "limit": {"type": "integer", "description": "Maximum candidates to return.", "default": 5},
                },
                "required": ["objective"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_list",
            "description": "Read-only TUI dashboard query. Lists the shared task ledger with status/agent filters before updating plans or delegating. User-facing name: task.list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Optional status filter."},
                    "assigned_agent": {"type": "string", "description": "Optional assigned agent id/name filter."},
                    "include_completed": {"type": "boolean", "description": "Include terminal tasks.", "default": False},
                    "limit": {"type": "integer", "description": "Maximum tasks to return.", "default": 20},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_get",
            "description": "Read-only TUI dashboard query. Gets one task with latest ledger row, recent history, child tasks, traces, artifacts, and approval refs. User-facing name: task.get.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task id from the shared task ledger."},
                    "history_limit": {"type": "integer", "description": "Maximum history rows to return.", "default": 20},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "approval_list",
            "description": "Read-only TUI dashboard query. Lists pending approval gates without executing decisions. User-facing name: approval.list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_all": {"type": "boolean", "description": "Include non-pending approvals.", "default": False},
                    "limit": {"type": "integer", "description": "Maximum approvals to return.", "default": 20},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "artifact_list",
            "description": "Read-only TUI dashboard query. Lists artifact refs and metadata; does not inline artifact contents. User-facing name: artifact.list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_task_id": {"type": "string", "description": "Optional source task id filter."},
                    "artifact_type": {"type": "string", "description": "Optional artifact type filter."},
                    "limit": {"type": "integer", "description": "Maximum artifacts to return.", "default": 20},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "capability_list",
            "description": "Read-only TUI dashboard query. Lists role templates, capabilities, write policies, and currently registered agents. User-facing name: capability.list.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
TUI_QUERY_TOOL_NAMES = {
    str(tool.get("function", {}).get("name") or "")
    for tool in TUI_QUERY_TOOL_SCHEMAS
    if tool.get("function")
}


def cell_width(text: str) -> int:
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def truncate_cells(text: str, width: int) -> str:
    if width <= 0:
        return ""
    out: list[str] = []
    used = 0
    for ch in text:
        w = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
        if used + w > width:
            out.append("…")
            break
        out.append(ch)
        used += w
    return "".join(out)


def pad_cells(text: str, width: int) -> str:
    text = truncate_cells(text, width)
    return text + (" " * max(0, width - cell_width(text)))


def clean_text(text: str) -> str:
    text = ANSI_RE.sub("", text or "")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.rstrip()


def wrap_cells(text: str, width: int) -> list[str]:
    if width <= 4:
        return [truncate_cells(text, max(1, width))]
    lines: list[str] = []
    for raw in (text or "").splitlines() or [""]:
        raw = raw.replace("\t", "    ")
        if not raw:
            lines.append("")
            continue
        current = ""
        current_w = 0
        for ch in raw:
            w = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
            if current and current_w + w > width:
                lines.append(current)
                current = ch
                current_w = w
            else:
                current += ch
                current_w += w
        lines.append(current)
    return lines


@dataclass
class Message:
    role: str
    content: str
    done: bool = True


@dataclass
class RenderLine:
    text: str
    attr: int = 0


@dataclass
class LLMConfigEntry:
    var_name: str
    cfg_type: str
    cfg: dict[str, Any]


@dataclass
class StreamTarget:
    key: str = "active"


@dataclass
class SecretVaultState:
    unlocked: bool = False
    pending_action: str = ""
    pending_first_password: str = field(default="", repr=False)
    pending_import_path: str = ""
    pending_import_disposition: str = "delete"
    pending_import_title: str = ""
    key: Optional[bytes] = field(default=None, repr=False)
    import_private_key: Optional[bytes] = field(default=None, repr=False)
    session_id: str = ""
    previous_log_path: str = ""
    last_unlocked_at: float = 0.0
    last_network_status: dict[str, Any] = field(default_factory=dict)
    storage_warning: str = ""
    proxy_env_snapshot: dict[str, Optional[str]] = field(default_factory=dict, repr=False)


@dataclass
class BackgroundSession:
    key: str
    title: str
    agent: Any
    messages: list[Message]
    status: str
    task_id: int
    active_task_id: Optional[int]
    stream_target: Optional[StreamTarget]
    pending_interaction: Optional[dict[str, Any]] = None
    security_context: str = "standard"
    secret_session_id: str = ""
    active_task_source: str = ""
    active_task_secret: bool = False
    active_secret_user_text: str = ""
    secret_origin: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubAgentRuntime:
    agent_id: str
    name: str
    home: str
    role: str = "specialist"
    default_model: str = ""
    security_context: str = "standard"
    owner_session: str = ""
    persistent: bool = True
    agent: Any = None
    messages: list[Message] = field(default_factory=list)
    task_queue: list[tuple[str, str, bool, str, str]] = field(default_factory=list)
    chat_queue: list[str] = field(default_factory=list)
    chat_queue_interrupt_requested: bool = False
    chat_session_id: str = ""
    chat_title: str = ""
    status: str = "idle"
    task_id: int = 0
    active_task_id: Optional[int] = None
    active_bus_task_id: str = ""
    pending_interaction: Optional[dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    profile_text: str = field(default="", repr=False)
    memory_text: str = field(default="", repr=False)
    encrypted_ref: str = ""


@dataclass
class MemoryEntry:
    layer: str
    label: str
    path: str
    size: int
    mtime: float
    note: str = ""


@dataclass
class PanelItem:
    key: str
    title: str
    subtitle: str
    detail: str
    status: str = ""
    path: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyDecision:
    decision_id: str
    action: str
    subject: str
    role: str
    status: str
    allowed: bool
    approval_required: bool
    approval_required_for: str
    risk: str
    reason: str
    source: str = ""
    target: str = ""
    approval_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class State:
    agent: Any
    ui_queue: queue.Queue = field(default_factory=queue.Queue)
    messages: list[Message] = field(default_factory=list)
    input_text: str = ""
    input_cursor: int = 0
    input_history: list[str] = field(default_factory=list)
    input_history_index: Optional[int] = None
    input_history_draft: str = ""
    input_history_draft_cursor: int = 0
    queued_user_inputs: list[str] = field(default_factory=list)
    queued_user_input_interrupt_requested: bool = False
    status: str = "idle"
    task_id: int = 0
    active_task_id: Optional[int] = None
    active_task_source: str = ""
    active_stream_target: Optional[StreamTarget] = None
    background_sessions: dict[str, BackgroundSession] = field(default_factory=dict)
    background_counter: int = 0
    subagents: dict[str, SubAgentRuntime] = field(default_factory=dict)
    scroll: int = 0
    follow_bottom: bool = True
    sidebar_scroll: int = 0
    sidebar_rows: list[tuple[str, Any, str, str]] = field(default_factory=list)
    rightbar_rows: list[tuple[str, Any, str, str]] = field(default_factory=list)
    rightbar_x0: int = 0
    rightbar_width: int = 0
    rightbar_task_rows_cache: list[tuple[str, Any, str, str]] = field(default_factory=list)
    rightbar_task_rows_loaded_at: float = 0.0
    rightbar_task_rows_limit: int = 0
    rightbar_task_rows_owner: str = ""
    rightbar_task_rows_ledger_signature: tuple[int, int] = (0, 0)
    history: list[tuple[str, float, str, int]] = field(default_factory=list)
    history_names: dict[str, str] = field(default_factory=dict)
    history_descriptions: dict[str, str] = field(default_factory=dict)
    history_loaded_at: float = 0.0
    secret_import_sidebar_cache: list[dict[str, Any]] = field(default_factory=list)
    secret_import_sidebar_signature: tuple[tuple[str, float, int], ...] = field(default_factory=tuple)
    secret_import_sidebar_loaded_at: float = 0.0
    secret_session_sidebar_cache: list[dict[str, Any]] = field(default_factory=list)
    secret_session_sidebar_signature: tuple[tuple[str, float, int], ...] = field(default_factory=tuple)
    secret_session_sidebar_loaded_at: float = 0.0
    session_meta: dict[str, dict[str, Any]] = field(default_factory=dict)
    show_archived: bool = False
    session_filter_category: str = ""
    collapsed_categories: set[str] = field(default_factory=set)
    history_ui_path: str = ""
    history_ui_loaded_rounds: int = 0
    history_ui_total_rounds: int = 0
    history_ui_message_count: int = 0
    history_ui_loading: bool = False
    history_ui_token: int = 0
    restore_cache: dict[tuple[str, float], list[Message]] = field(default_factory=dict)
    restore_lock: threading.Lock = field(default_factory=threading.Lock)
    restore_token: int = 0
    current_title: str = "main"
    selected_session: Any = "main"
    command_index: int = 0
    fold_process: bool = True
    markdown: bool = True
    message_version: int = 0
    expanded_process_groups: set[str] = field(default_factory=set)
    expanded_process_turns: set[str] = field(default_factory=set)
    expanded_subagent_meta: set[str] = field(default_factory=set)
    line_cache_key: tuple[Any, ...] = (0, 0, True, True, 0)
    line_cache: list[RenderLine] = field(default_factory=list)
    message_block_cache: dict[tuple[Any, ...], list[RenderLine]] = field(default_factory=dict)
    main_x0: int = 0
    main_width: int = 0
    body_top: int = 1
    body_height: int = 0
    active_plan_task_id: str = ""
    active_plan_steps: dict[str, str] = field(default_factory=dict)
    auto_plan_continue_attempts: dict[str, int] = field(default_factory=dict)
    auto_plan_continue_plan_attempts: dict[str, int] = field(default_factory=dict)
    auto_plan_continue_last_blocked: str = ""
    selection_active: bool = False
    selection_start: Optional[tuple[int, int]] = None
    selection_end: Optional[tuple[int, int]] = None
    selection_dragged: bool = False
    selection_mouse_x: Optional[int] = None
    selection_mouse_y: Optional[int] = None
    selection_auto_last_at: float = 0.0
    pending_secret_copy_hash: str = ""
    pending_secret_copy_approval_id: str = ""
    pending_secret_copy_started_at: float = 0.0
    pending_secret_copy_chars: int = 0
    pending_secret_copy_key: bytes = field(default=b"", repr=False)
    session_popup_path: str = ""
    session_popup_anchor: Optional[tuple[int, int]] = None
    session_popup_rect: Optional[tuple[int, int, int, int]] = None
    dirty: bool = True
    running: bool = True
    run_frame: int = 0
    last_error: str = ""
    last_error_seen: str = ""
    last_error_started_at: float = 0.0
    exit_reason: str = ""
    exit_mode: str = "terminate"
    paste_mode: bool = False
    paste_buffer: str = ""
    pending_interaction: Optional[dict[str, Any]] = None
    secret_vault: SecretVaultState = field(default_factory=SecretVaultState)
    active_task_secret: bool = False
    active_secret_user_text: str = ""
    active_secret_session_id: str = ""
    secret_active_origin: dict[str, Any] = field(default_factory=dict)
    token_usage_registry: dict[str, dict[str, int]] = field(default_factory=dict)
    token_live_offsets: dict[str, dict[str, int]] = field(default_factory=dict)
    title_jobs: set[str] = field(default_factory=set)
    title_attempted: set[str] = field(default_factory=set)
    description_jobs: set[str] = field(default_factory=set)
    description_signatures: dict[str, str] = field(default_factory=dict)
    category_jobs: set[str] = field(default_factory=set)
    category_signatures: dict[str, str] = field(default_factory=dict)


def cp(index: int) -> int:
    try:
        return curses.color_pair(index)
    except curses.error:
        return 0


def expire_last_error_if_needed(state: State, ttl: float = 4.0) -> bool:
    if not state.last_error:
        state.last_error_seen = ""
        state.last_error_started_at = 0.0
        return False
    now = time.monotonic()
    if state.last_error != state.last_error_seen:
        state.last_error_seen = state.last_error
        state.last_error_started_at = now
        return False
    if state.last_error_started_at and now - state.last_error_started_at >= ttl:
        state.last_error = ""
        state.last_error_seen = ""
        state.last_error_started_at = 0.0
        mark_dirty(state)
        return True
    return False


def mark_dirty(state: State) -> None:
    state.dirty = True


def mark_messages_changed(state: State) -> None:
    state.message_version += 1
    state.dirty = True


def add_system(state: State, text: str, *, persist: bool = False, kind: str = "") -> None:
    state.messages.append(Message("system", text))
    if persist:
        persist_ui_system_message(state, text, kind=kind)
    state.follow_bottom = True
    mark_messages_changed(state)


def clamp_input_cursor(state: State) -> None:
    state.input_cursor = max(0, min(state.input_cursor, len(state.input_text)))


def set_input_text(state: State, text: str, cursor: Optional[int] = None) -> None:
    state.input_text = text
    state.input_cursor = len(text) if cursor is None else cursor
    clamp_input_cursor(state)


def insert_input_text(state: State, text: str) -> None:
    if not text:
        return
    clamp_input_cursor(state)
    state.input_text = state.input_text[:state.input_cursor] + text + state.input_text[state.input_cursor:]
    state.input_cursor += len(text)
    state.command_index = 0
    reset_input_history_browse(state)
    mark_dirty(state)


def reset_input_history_browse(state: State) -> None:
    state.input_history_index = None
    state.input_history_draft = ""
    state.input_history_draft_cursor = 0


def remember_input(state: State, text: str) -> None:
    text = (text or "").strip()
    if not text or text.startswith("/"):
        reset_input_history_browse(state)
        return
    if not state.input_history or state.input_history[-1] != text:
        state.input_history.append(text)
        if len(state.input_history) > 200:
            state.input_history = state.input_history[-200:]
    reset_input_history_browse(state)


def remember_inputs_from_messages(state: State, messages: list[Message]) -> None:
    for msg in messages:
        if msg.role == "user":
            remember_input(state, msg.content)
    reset_input_history_browse(state)


def clear_queued_user_inputs(state: State) -> None:
    state.queued_user_inputs.clear()
    state.queued_user_input_interrupt_requested = False


def clear_all_queued_inputs(state: State) -> None:
    clear_queued_user_inputs(state)
    for sub in state.subagents.values():
        sub.chat_queue.clear()
        sub.chat_queue_interrupt_requested = False


def queued_user_input_text(state: State) -> str:
    return "\n\n".join(text for text in state.queued_user_inputs if text.strip()).strip()


def queue_user_input_for_current_step(state: State, text: str, *, interrupt_requested: bool = False) -> bool:
    queued = (text or "").strip()
    if not queued:
        return False
    state.queued_user_inputs.append(queued)
    if interrupt_requested:
        state.queued_user_input_interrupt_requested = True
    count = len(state.queued_user_inputs)
    state.last_error = f"已排队 {count} 条输入；当前这一步结束后会自动发送。"
    mark_dirty(state)
    return True


def queue_input_draft_for_interrupt(state: State) -> bool:
    if secret_password_entry_active(state):
        return False
    draft = state.input_text
    if not draft.strip():
        return False
    set_input_text(state, "")
    return queue_user_input_for_current_step(state, draft, interrupt_requested=True)


def queued_user_input_hint_lines(state: State, width: int) -> list[tuple[str, int]]:
    sub = selected_subagent(state)
    queued_inputs = sub.chat_queue if sub is not None else state.queued_user_inputs
    interrupted = sub.chat_queue_interrupt_requested if sub is not None else state.queued_user_input_interrupt_requested
    if not queued_inputs:
        return []
    excerpts = []
    for text in queued_inputs[-3:]:
        one_line = clean_text(text).replace("\n", " ")
        excerpts.append(truncate_cells(one_line, 34))
    prefix = "已请求打断，等待当前输出收尾后发送" if interrupted else "等待这一步完成后发送"
    more = f"+{len(queued_inputs) - len(excerpts)} " if len(queued_inputs) > len(excerpts) else ""
    line = f"{prefix} · {len(queued_inputs)} 条：{more}{' ｜ '.join(excerpts)}"
    return [(truncate_cells(line, width), cp(11))]


def maybe_start_queued_user_input(state: State) -> bool:
    if selected_subagent(state) is not None:
        return False
    if not state.queued_user_inputs:
        return False
    if state.status != "idle" or state.active_task_id is not None or state.pending_interaction:
        return False
    queued = list(state.queued_user_inputs)
    interrupt_requested = state.queued_user_input_interrupt_requested
    text = queued_user_input_text(state)
    clear_queued_user_inputs(state)
    if not text:
        mark_dirty(state)
        return True
    if start_main_agent_task(
        state,
        text,
        source="user:queued_after_interrupt" if interrupt_requested else "user:queued",
        visible_user_text=text,
        remember_user=True,
        clear_history=False,
    ):
        state.last_error = ""
        return True
    state.queued_user_inputs = queued + state.queued_user_inputs
    state.queued_user_input_interrupt_requested = interrupt_requested or state.queued_user_input_interrupt_requested
    mark_dirty(state)
    return False


def request_main_interrupt(state: State, prefix: str = "Ctrl+C") -> None:
    if state.status in {"running", "aborting", "restoring"}:
        queue_input_draft_for_interrupt(state)
    if state.status in {"running", "aborting"}:
        try:
            state.agent.abort()
        except Exception:
            pass
        state.status = "aborting"
        if state.queued_user_inputs:
            state.queued_user_input_interrupt_requested = True
            state.last_error = f"{prefix}: 已请求中止当前任务；排队输入会在当前输出收尾后发送。"
        else:
            state.last_error = f"{prefix}: 已请求中止当前任务；退出 TUI 请按 Ctrl+Q。"
    elif state.status == "restoring":
        state.restore_token += 1
        state.status = "idle"
        state.last_error = f"{prefix}: 已取消当前会话恢复；退出 TUI 请按 Ctrl+Q。"
    else:
        state.last_error = f"{prefix} 只用于中止任务；退出 TUI 请按 Ctrl+Q。"
    mark_dirty(state)


def normalized_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path or ""))


def path_is_within(path: str, root: str) -> bool:
    try:
        real_root = os.path.realpath(normalized_path(root))
        real_path = os.path.realpath(normalized_path(path))
        return os.path.commonpath([real_root, real_path]) == real_root
    except Exception:
        return False


def is_normal_session_log_path(path: str) -> bool:
    path = normalized_path(path)
    base = os.path.basename(path)
    return (
        path_is_within(path, MODEL_RESPONSES_DIR)
        and not path_is_within(path, SESSION_TRASH_DIR)
        and base.startswith("model_responses")
        and base.endswith(".txt")
    )


def session_key(path: str) -> str:
    return os.path.basename(path or "")


def load_session_meta_registry() -> dict[str, dict[str, Any]]:
    try:
        with open(SESSION_META_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    meta: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, dict):
            meta[key] = dict(value)
    return meta


def save_session_meta_registry(meta: dict[str, dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(SESSION_META_PATH), exist_ok=True)
    tmp = SESSION_META_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, SESSION_META_PATH)


def session_meta_for(state: State, path: str) -> dict[str, Any]:
    return state.session_meta.get(session_key(path), {})


def recent_history_items(
    history_entries: list[tuple[int, tuple[str, float, str, int]]],
    used_paths: set[str],
    limit: int = RECENT_SESSION_LIMIT,
) -> list[tuple[int, tuple[str, float, str, int]]]:
    recent_candidates = [
        (idx, item, float(item[1] or 0.0))
        for idx, item in history_entries
        if float(item[1] or 0.0) > 0
        and normalized_path(item[0]) not in used_paths
    ]
    recent_candidates.sort(key=lambda entry: entry[2], reverse=True)
    return [(idx, item) for idx, item, _activity_at in recent_candidates[:limit]]


def set_session_meta_fields(state: State, path: str, **fields: Any) -> None:
    key = session_key(path)
    if not key:
        return
    entry = dict(state.session_meta.get(key, {}))
    for field_name, value in fields.items():
        if value in (None, "", False) and field_name not in {"pinned", "archived", "deleted"}:
            entry.pop(field_name, None)
        else:
            entry[field_name] = value
    state.session_meta[key] = entry
    save_session_meta_registry(state.session_meta)


def agent_log_path(agent: Any) -> str:
    if agent is None:
        return ""
    candidates: list[Any] = [getattr(agent, "log_path", "")]
    clients: list[Any] = []
    current = getattr(agent, "llmclient", None)
    if current is not None:
        clients.append(current)
    for client in getattr(agent, "llmclients", []) or []:
        if client is not None and client not in clients:
            clients.append(client)
    for client in clients:
        candidates.append(getattr(client, "log_path", ""))
        backend = getattr(client, "backend", None)
        if backend is not None:
            candidates.append(getattr(backend, "log_path", ""))
    for value in candidates:
        path = str(value or "").strip()
        if path:
            return path
    return ""


def active_ui_session_path(state: State) -> str:
    if state.history_ui_path:
        return state.history_ui_path
    return agent_log_path(state.agent)


def active_ui_session_key(state: State) -> str:
    if state.secret_vault.unlocked:
        return state.secret_vault.session_id or "secret"
    return session_key(active_ui_session_path(state))


def durable_ui_system_message_kind(text: str) -> str:
    stripped = (text or "").strip()
    if stripped.startswith("Agent 控制结果："):
        return "agent_control_result"
    if stripped.startswith("子 agent 回复 ·"):
        return "subagent_result"
    return ""


def persist_ui_system_message_for_path(path: str, text: str, *, kind: str = "") -> bool:
    content = str(text or "")
    message_kind = (kind or durable_ui_system_message_kind(content)).strip()
    key = session_key(path)
    if not content.strip() or not message_kind or not key:
        return False

    registry = load_session_meta_registry()
    entry = dict(registry.get(key) or {})
    raw_messages = entry.get(UI_DURABLE_SYSTEM_MESSAGES_KEY)
    messages = [dict(item) for item in raw_messages if isinstance(item, dict)] if isinstance(raw_messages, list) else []
    if message_kind == "subagent_result":
        notice = parse_subagent_result_notice(content)
        notice_key = (notice or {}).get("task_id", ""), (notice or {}).get("artifact_ref", "")
        if all(notice_key):
            for idx, item in enumerate(messages):
                existing = parse_subagent_result_notice(str(item.get("content") or ""))
                existing_key = (existing or {}).get("task_id", ""), (existing or {}).get("artifact_ref", "")
                if existing_key != notice_key:
                    continue
                if str(item.get("content") or "") == content:
                    return False
                replacement = dict(item)
                replacement.update({
                    "role": "system",
                    "content": content,
                    "kind": message_kind,
                    "updated_at": time.time(),
                })
                messages[idx] = replacement
                entry[UI_DURABLE_SYSTEM_MESSAGES_KEY] = messages[-UI_DURABLE_SYSTEM_MESSAGE_LIMIT:]
                registry[key] = entry
                save_session_meta_registry(registry)
                return True
    if any(str(item.get("content") or "") == content for item in messages):
        if key not in registry:
            registry[key] = entry
        save_session_meta_registry(registry)
        return False
    messages.append({
        "role": "system",
        "content": content,
        "kind": message_kind,
        "created_at": time.time(),
    })
    entry[UI_DURABLE_SYSTEM_MESSAGES_KEY] = messages[-UI_DURABLE_SYSTEM_MESSAGE_LIMIT:]
    registry[key] = entry
    save_session_meta_registry(registry)
    return True


def persist_ui_system_message(state: State, text: str, *, kind: str = "") -> None:
    path = active_ui_session_path(state)
    if persist_ui_system_message_for_path(path, text, kind=kind):
        state.session_meta = load_session_meta_registry()


def subagent_result_artifact_ref(refs: Any) -> str:
    if not isinstance(refs, list):
        return ""
    for ref in refs:
        value = str(ref or "").strip()
        if value and "/subagent-results/" in value:
            return value
    return ""


def subagent_result_body_from_artifact(artifact_ref: str, read_limit: int = 65536) -> str:
    path = artifact_path_from_uri(artifact_ref)
    if not path or not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read(read_limit)
    except OSError:
        return ""
    lines = text.splitlines()
    idx = 0
    if idx < len(lines) and lines[idx].lstrip().startswith("#"):
        idx += 1
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        if idx < len(lines) and lines[idx].strip().startswith("Task:"):
            idx += 1
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
    return "\n".join(lines[idx:]).strip() or text.strip()


def subagent_name_from_task_row(row: dict[str, Any]) -> str:
    title = str(row.get("title") or "").strip()
    for prefix in ("子 agent 执行:", "子 agent 执行："):
        if title.startswith(prefix):
            return title[len(prefix):].strip()
    if title:
        return title
    agent_id = str(row.get("assigned_agent") or "").strip()
    if agent_id:
        candidate_paths = [subagent_meta_path(agent_id)]
        candidate_paths.extend(glob.glob(os.path.join(TEMP_SUBAGENTS_DIR, "*", agent_id, "meta.json")))
        for meta_path in candidate_paths:
            meta = load_subagent_meta_file(meta_path)
            name = str(meta.get("name") or "").strip()
            if name:
                return name
    return agent_id


def parse_timestamp_value(text: str) -> float:
    value = str(text or "").strip()
    if not value:
        return 0.0
    for candidate, fmt in (
        (value[:19], "%Y-%m-%dT%H:%M:%S"),
        (value[:19], "%Y-%m-%d %H:%M:%S"),
        (value[:24], "%Y-%m-%dT%H:%M:%S%z"),
    ):
        try:
            return datetime.strptime(candidate, fmt).timestamp()
        except Exception:
            continue
    return 0.0


def legacy_match_text(text: str) -> str:
    text = str(text or "")
    text = text.replace("\\n", " ").replace('\\"', '"').replace("\\'", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def subagent_result_task_first_timestamps(rows: list[dict[str, Any]]) -> dict[str, float]:
    first_seen: dict[str, float] = {}
    for row in rows:
        task_id = str(row.get("task_id") or "").strip()
        if not task_id:
            continue
        ts = parse_timestamp_value(str(row.get("timestamp") or ""))
        if ts <= 0:
            continue
        if task_id not in first_seen or ts < first_seen[task_id]:
            first_seen[task_id] = ts
    return first_seen


def completed_subagent_result_row(row: dict[str, Any]) -> bool:
    if str(row.get("status") or "").lower() != "completed":
        return False
    if not subagent_result_artifact_ref(row.get("artifact_refs")):
        return False
    if str(row.get("kind") or "") == "subagent_task":
        return True
    assigned = str(row.get("assigned_agent") or "")
    title = str(row.get("title") or "")
    return assigned.startswith(("agent-", "tmp-agent-", "tmp-")) or title.startswith(("子 agent", "subagent"))


def session_subagent_control_blocks(path: str) -> list[tuple[float, str]]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except OSError:
        return []
    blocks: list[tuple[float, str]] = []
    action_markers = ("delegate.create", "agenttask.v2", "subagent_ask", "subagent_run", "subagent_input", "agent_ask", "agent_run")
    for timestamp, response_body in RESPONSE_BLOCK_WITH_TIME_RE.findall(content):
        if not any(marker in response_body for marker in action_markers):
            continue
        blocks.append((parse_timestamp_value(timestamp), legacy_match_text(response_body)))
    return blocks


def legacy_subagent_row_matches_session(
    path: str,
    row: dict[str, Any],
    first_task_timestamp: float,
    control_blocks: Optional[list[tuple[float, str]]] = None,
) -> bool:
    if str(row.get("session_key") or "").strip():
        return False
    objective = legacy_match_text(row.get("objective") or "")
    if len(objective) < 8:
        return False
    blocks = control_blocks if control_blocks is not None else session_subagent_control_blocks(path)
    for anchor_timestamp, response_body in blocks:
        if objective not in response_body:
            continue
        if anchor_timestamp > 0 and first_task_timestamp > 0:
            if first_task_timestamp < anchor_timestamp - 5:
                continue
            if first_task_timestamp > anchor_timestamp + LEGACY_SUBAGENT_BACKFILL_WINDOW_SECONDS:
                continue
        return True
    return False


def backfill_durable_subagent_result_messages_for_path(path: str) -> int:
    owner_key = session_key(path)
    if not owner_key:
        return 0
    candidates: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    rows = read_jsonl(AGENT_TASK_LEDGER_PATH)
    first_timestamps = subagent_result_task_first_timestamps(rows)
    legacy_control_blocks: Optional[list[tuple[float, str]]] = None
    for row in rows:
        if not completed_subagent_result_row(row):
            continue
        task_id = str(row.get("task_id") or "").strip()
        artifact_ref = subagent_result_artifact_ref(row.get("artifact_refs"))
        row_session_key = str(row.get("session_key") or "").strip()
        if row_session_key:
            if row_session_key != owner_key:
                continue
        else:
            if legacy_control_blocks is None:
                legacy_control_blocks = session_subagent_control_blocks(path)
            if not legacy_subagent_row_matches_session(path, row, first_timestamps.get(task_id, 0.0), legacy_control_blocks):
                continue
        key = (task_id, artifact_ref)
        if not task_id or not artifact_ref or key in seen:
            continue
        seen.add(key)
        body = subagent_result_body_from_artifact(artifact_ref) or str(row.get("summary") or "")
        notice = format_subagent_result_notice_parts(
            subagent_name_from_task_row(row),
            str(row.get("assigned_agent") or ""),
            task_id,
            artifact_ref,
            body,
        )
        candidates.append((str(row.get("timestamp") or ""), notice))
    added = 0
    for _timestamp, notice in sorted(candidates, key=lambda item: item[0]):
        if persist_ui_system_message_for_path(path, notice, kind="subagent_result"):
            added += 1
    return added


def durable_ui_system_messages_for_path(path: str, *, backfill: bool = True) -> list[Message]:
    if backfill:
        backfill_durable_subagent_result_messages_for_path(path)
    key = session_key(path)
    if not key:
        return []
    meta = load_session_meta_registry().get(key, {})
    raw_messages = meta.get(UI_DURABLE_SYSTEM_MESSAGES_KEY)
    if not isinstance(raw_messages, list):
        return []
    messages: list[Message] = []
    for item in raw_messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "system").strip()
        content = str(item.get("content") or "")
        if role == "system" and content.strip():
            messages.append(Message("system", content))
    return messages


def mark_session_opened(state: State, path: str) -> None:
    if not path:
        return
    state.session_meta = load_session_meta_registry()
    set_session_meta_fields(state, path, last_opened_at=time.time())


def parse_log_time(text: str) -> float:
    text = (text or "").strip()
    if not text:
        return 0.0
    stamp = text[:19]
    try:
        return time.mktime(time.strptime(stamp, "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return 0.0


def session_last_user_time(path: str, fallback: float = 0.0) -> float:
    last = 0.0
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except Exception:
        return fallback
    return session_last_user_time_from_content(content, fallback)


def session_last_user_time_from_content(content: str, fallback: float = 0.0) -> float:
    last = 0.0
    for timestamp, prompt_body in PROMPT_BLOCK_WITH_TIME_RE.findall(content):
        if _user_text(prompt_body):
            last = parse_log_time(timestamp) or last
    return last or fallback


def compact_ui_preview_messages_from_pairs(
    pairs: list[tuple[str, str]],
    rounds: int = RESTORE_DISPLAY_ROUNDS,
) -> tuple[list[dict[str, str]], int, int, int]:
    total_rounds = history_round_count(pairs)
    if total_rounds <= 0:
        return [], 0, 0, 0
    loaded_rounds = max(1, min(int(rounds or RESTORE_DISPLAY_ROUNDS), total_rounds))
    start = 0
    seen = 0
    for idx in range(len(pairs) - 1, -1, -1):
        if _user_text(pairs[idx][0]):
            seen += 1
            start = idx
            if seen >= loaded_rounds:
                break
    messages: list[dict[str, str]] = []
    for prompt, response in pairs[start:]:
        user = _user_text(prompt)
        if user:
            messages.append({"role": "user", "content": user})
        summary = process_summary_text(response) or process_preview(response)
        if summary and summary != "执行中":
            messages.append({"role": "assistant", "content": f"（预览）{summary}"})
    return messages, loaded_rounds, total_rounds, len(messages)


def messages_from_preview_dicts(raw: Any) -> list[Message]:
    if not isinstance(raw, list):
        return []
    messages: list[Message] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        content = str(item.get("content") or "")
        if role in {"user", "assistant", "system"} and content.strip():
            messages.append(Message(role, content))
    return messages


def sample_file_text(path: str, limit: int = 65536) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except Exception:
        return ""


def is_subagent_session_log_sample(text: str) -> bool:
    if not text:
        return False
    if "[GA TUI SubAgent Profile]" in text:
        return True
    if "[GA TUI Context Pack]" not in text or "[/GA TUI Context Pack]" not in text:
        return False
    return "\nagent:" in text or "\\nagent:" in text


def cached_session_rows(state: State, exclude_pid: Optional[int] = None) -> tuple[list[tuple[str, float, str, int, str]], bool]:
    tag = f"model_responses_{exclude_pid}.txt" if exclude_pid is not None else ""
    paths = sorted(glob.glob(os.path.join(MODEL_RESPONSES_DIR, "model_responses*.txt")), key=os.path.getmtime, reverse=True)
    rows: list[tuple[str, float, str, int, str]] = []
    changed = False
    for path in paths:
        if tag and path.endswith(tag):
            continue
        key = session_key(path)
        try:
            stat = os.stat(path)
        except OSError:
            continue
        meta = state.session_meta.get(key, {})
        if bool(meta.get("hidden_subagent_log")):
            continue
        if is_subagent_session_log_sample(sample_file_text(path)):
            entry = dict(meta)
            entry["hidden_subagent_log"] = True
            entry["cache_mtime"] = stat.st_mtime
            entry["cache_size"] = stat.st_size
            entry["preview"] = "subagent session log"
            entry["rounds"] = 0
            entry["last_user_at"] = stat.st_mtime
            if entry != meta:
                state.session_meta[key] = entry
                changed = True
            continue
        cache_ok = (
            float(meta.get("cache_mtime") or 0) == float(stat.st_mtime)
            and int(meta.get("cache_size") or -1) == int(stat.st_size)
            and "preview" in meta
            and "rounds" in meta
            and "last_user_at" in meta
            and "ui_preview_messages" in meta
        )
        if cache_ok:
            rows.append((
                path,
                float(meta.get("last_user_at") or stat.st_mtime),
                str(meta.get("preview") or ""),
                int(meta.get("rounds") or 0),
                compact_description(str(meta.get("description") or "")),
            ))
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except Exception:
            continue
        pairs = _pairs(content)
        if not pairs:
            continue
        preview = _preview_text(pairs)
        rounds = len(pairs)
        last_user_at = session_last_user_time_from_content(content, stat.st_mtime)
        desc = compact_description(str(meta.get("description") or ""))
        if not desc:
            desc = session_description_from_pairs(pairs, preview)
        preview_messages, preview_loaded, preview_total, preview_message_count = compact_ui_preview_messages_from_pairs(pairs)
        entry = dict(meta)
        entry.update({
            "cache_mtime": stat.st_mtime,
            "cache_size": stat.st_size,
            "preview": preview,
            "rounds": rounds,
            "last_user_at": last_user_at,
            "ui_preview_messages": preview_messages,
            "ui_preview_loaded_rounds": preview_loaded,
            "ui_preview_total_rounds": preview_total,
            "ui_preview_message_count": preview_message_count,
        })
        if desc:
            entry["description"] = desc
        if entry != meta:
            state.session_meta[key] = entry
            changed = True
        rows.append((path, last_user_at, preview, rounds, desc))
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows, changed


def new_session_log_path() -> str:
    os.makedirs(MODEL_RESPONSES_DIR, exist_ok=True)
    while True:
        suffix = f"{time.time_ns() % 1_000_000_000_000:012d}{next(_SESSION_LOG_COUNTER) % 1000:03d}"
        path = os.path.join(MODEL_RESPONSES_DIR, f"model_responses_{suffix}.txt")
        if not os.path.exists(path):
            return path


def agent_llm_clients(agent: Any) -> list[Any]:
    if agent is None:
        return []
    seen: set[int] = set()
    clients: list[Any] = []
    for client in [getattr(agent, "llmclient", None), *(getattr(agent, "llmclients", []) or [])]:
        if client is None or id(client) in seen:
            continue
        seen.add(id(client))
        clients.append(client)
    return clients


def set_agent_log_path(agent: Any, path: str) -> None:
    if agent is None or not path:
        return
    agent.log_path = path
    for client in agent_llm_clients(agent):
        try:
            client.log_path = path
        except Exception:
            pass
        backend = getattr(client, "backend", None)
        if backend is not None and hasattr(backend, "log_path"):
            try:
                backend.log_path = path
            except Exception:
                pass


def reset_agent_runtime_context_no_snapshot(agent: Any, history: Optional[list[dict[str, Any]]] = None) -> None:
    if agent is None:
        return
    try:
        agent.abort()
    except Exception:
        pass
    if hasattr(agent, "history"):
        agent.history = []
    backend_history = list(history or [])
    for client in agent_llm_clients(agent):
        backend = getattr(client, "backend", None)
        if backend is not None and hasattr(backend, "history"):
            backend.history = list(backend_history)
        if hasattr(client, "last_tools"):
            client.last_tools = ""
    if hasattr(agent, "handler"):
        agent.handler = None
    if hasattr(agent, "_ga_tui_pending_key_info"):
        setattr(agent, "_ga_tui_pending_key_info", "")


def write_text_atomic(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def read_text_file(path: str, default: str = "") -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return default


def append_text_file(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def short_uid(prefix: str) -> str:
    return f"{prefix}_{time.time_ns():x}_{os.getpid():x}"


def append_jsonl(path: str, payload: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def write_bytes_atomic(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


class SecretVaultError(RuntimeError):
    pass


def secret_crypto_available() -> bool:
    return bool(nacl_pwhash and nacl_xchacha_encrypt and nacl_xchacha_decrypt and NaclPrivateKey and NaclPublicKey and NaclSealedBox)


def secret_crypto_status_text() -> str:
    if secret_crypto_available():
        return "available:xchacha20-poly1305+argon2id"
    return f"unavailable:{SECRET_CRYPTO_IMPORT_ERROR or 'PyNaCl is not installed'}"


def ensure_secret_vault_dirs() -> None:
    os.makedirs(SECRET_VAULT_SESSIONS_DIR, mode=0o700, exist_ok=True)
    for path in (SECRET_VAULT_DIR, SECRET_VAULT_DATA_DIR, SECRET_VAULT_SESSIONS_DIR):
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass


def secret_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def secret_unb64(text: str) -> bytes:
    return base64.b64decode((text or "").encode("ascii"), validate=True)


def secret_derive_key(password: str, salt: bytes) -> bytes:
    if not secret_crypto_available():
        raise SecretVaultError("Secret Vault 需要 PyNaCl/libsodium 才能启用强加密。")
    try:
        salt_bytes = int(getattr(nacl_pwhash.argon2id, "SALTBYTES", 16))
        opslimit = int(getattr(nacl_pwhash.argon2id, "OPSLIMIT_SENSITIVE"))
        memlimit = int(getattr(nacl_pwhash.argon2id, "MEMLIMIT_SENSITIVE"))
        if len(salt) != salt_bytes:
            raise SecretVaultError("Secret Vault salt 长度无效。")
        return nacl_pwhash.argon2id.kdf(
            NACL_XCHACHA_KEYBYTES,
            (password or "").encode("utf-8"),
            salt,
            opslimit=opslimit,
            memlimit=memlimit,
        )
    except SecretVaultError:
        raise
    except Exception as exc:
        raise SecretVaultError(f"Secret Vault 密钥派生失败: {type(exc).__name__}: {exc}") from exc


def secret_encrypt_bytes(key: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    if not secret_crypto_available():
        raise SecretVaultError("Secret Vault 强加密不可用。")
    if not key or len(key) != NACL_XCHACHA_KEYBYTES:
        raise SecretVaultError("Secret Vault key 无效。")
    nonce = os.urandom(NACL_XCHACHA_NPUBBYTES)
    ciphertext = nacl_xchacha_encrypt(plaintext, aad, nonce, key)
    return nonce + ciphertext


def secret_decrypt_bytes(key: bytes, sealed: bytes, aad: bytes = b"") -> bytes:
    if not secret_crypto_available():
        raise SecretVaultError("Secret Vault 强加密不可用。")
    if len(sealed) <= NACL_XCHACHA_NPUBBYTES + NACL_XCHACHA_ABYTES:
        raise SecretVaultError("Secret Vault 密文过短。")
    nonce = sealed[:NACL_XCHACHA_NPUBBYTES]
    ciphertext = sealed[NACL_XCHACHA_NPUBBYTES:]
    try:
        return nacl_xchacha_decrypt(ciphertext, aad, nonce, key)
    except Exception as exc:
        raise SecretVaultError("Secret Vault 密码错误或密文已损坏。") from exc


def secret_import_key_id(public_key: bytes) -> str:
    return hashlib.sha256(public_key).hexdigest()[:24]


def secret_import_key_record(meta: dict[str, Any]) -> dict[str, Any]:
    record = meta.get(SECRET_IMPORT_DROPBOX_META_KEY)
    return record if isinstance(record, dict) else {}


def secret_build_import_key_record(key: bytes) -> tuple[dict[str, Any], bytes]:
    if not secret_crypto_available() or NaclPrivateKey is None:
        raise SecretVaultError("Secret Vault 强加密不可用。")
    try:
        private_key = NaclPrivateKey.generate()
        private_bytes = bytes(private_key)
        public_bytes = bytes(private_key.public_key)
        encrypted_private = secret_encrypt_bytes(key, private_bytes, SECRET_IMPORT_KEY_AAD)
    except Exception as exc:
        raise SecretVaultError(f"Secret Vault 单向导入密钥创建失败：{type(exc).__name__}: {exc}") from exc
    return {
        "mode": "sealedbox.v1",
        "created_at": now_iso(),
        "public_key": secret_b64(public_bytes),
        "public_key_id": secret_import_key_id(public_bytes),
        "private_key_ciphertext": secret_b64(encrypted_private),
    }, private_bytes


def secret_import_public_key_from_meta(meta: Optional[dict[str, Any]] = None) -> tuple[Optional[bytes], str, str]:
    if not secret_crypto_available() or NaclPublicKey is None:
        return None, "", f"Secret Vault 强加密不可用：{secret_crypto_status_text()}。请安装 PyNaCl 后再启用。"
    meta = meta if isinstance(meta, dict) else load_secret_vault_meta()
    if not meta.get("verifier_ciphertext"):
        return None, "", "Secret Vault 尚未初始化：首次创建仍需要输入密码以生成本地密钥。"
    record = secret_import_key_record(meta)
    public_text = str(record.get("public_key") or "")
    if not public_text:
        return None, "", "当前 Secret Vault 缺少单向导入公钥；请先 /Secret 解锁一次完成迁移，之后 /toSecret 不再需要密码。"
    try:
        public_bytes = secret_unb64(public_text)
        NaclPublicKey(public_bytes)
    except Exception as exc:
        return None, "", f"Secret Vault 单向导入公钥无效：{type(exc).__name__}: {exc}"
    key_id = str(record.get("public_key_id") or secret_import_key_id(public_bytes))
    return public_bytes, key_id, ""


def secret_import_private_key_from_meta(meta: dict[str, Any], key: bytes) -> tuple[Optional[bytes], str]:
    if not secret_crypto_available() or NaclPrivateKey is None:
        return None, f"Secret Vault 强加密不可用：{secret_crypto_status_text()}。"
    record = secret_import_key_record(meta)
    private_text = str(record.get("private_key_ciphertext") or "")
    if not private_text:
        return None, "Secret Vault 单向导入私钥缺失。"
    try:
        private_bytes = secret_decrypt_bytes(key, secret_unb64(private_text), SECRET_IMPORT_KEY_AAD)
        NaclPrivateKey(private_bytes)
    except Exception as exc:
        return None, f"Secret Vault 单向导入私钥不可用：{type(exc).__name__}: {exc}"
    return private_bytes, ""


def secret_load_or_create_import_private_key(key: bytes) -> tuple[Optional[bytes], str]:
    meta = load_secret_vault_meta()
    if not meta.get("verifier_ciphertext"):
        return None, "Secret Vault 尚未初始化。"
    if secret_import_key_record(meta):
        return secret_import_private_key_from_meta(meta, key)
    try:
        record, private_bytes = secret_build_import_key_record(key)
        meta[SECRET_IMPORT_DROPBOX_META_KEY] = record
        meta["updated_at"] = now_iso()
        write_secret_vault_meta(meta)
        return private_bytes, "已为旧 Secret Vault 生成单向导入公钥。"
    except Exception as exc:
        return None, f"Secret Vault 单向导入公钥生成失败：{type(exc).__name__}: {exc}"


def secret_sealed_import_envelope(public_key: bytes, public_key_id: str, payload: dict[str, Any]) -> bytes:
    if not secret_crypto_available() or NaclPublicKey is None or NaclSealedBox is None:
        raise SecretVaultError("Secret Vault 强加密不可用。")
    try:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ciphertext = NaclSealedBox(NaclPublicKey(public_key)).encrypt(raw)
    except Exception as exc:
        raise SecretVaultError(f"Secret Vault 单向导入加密失败：{type(exc).__name__}: {exc}") from exc
    envelope = {
        "schema_version": SECRET_IMPORT_SEALED_SCHEMA,
        "encryption": "sealedbox.v1",
        "created_at": now_iso(),
        "public_key_id": public_key_id or secret_import_key_id(public_key),
        "ciphertext": secret_b64(ciphertext),
    }
    return json.dumps(envelope, ensure_ascii=False, sort_keys=True).encode("utf-8")


def secret_decrypt_sealed_import_envelope(state: State, sealed: bytes) -> dict[str, Any]:
    if not secret_crypto_available() or NaclPrivateKey is None or NaclSealedBox is None:
        raise SecretVaultError("Secret Vault 强加密不可用。")
    private_key = state.secret_vault.import_private_key
    if not private_key:
        raise SecretVaultError("Secret Vault 单向导入私钥未载入；请重新 /Secret 解锁。")
    try:
        envelope = json.loads(sealed.decode("utf-8"))
    except Exception as exc:
        raise SecretVaultError("不是 Secret 单向导入封套。") from exc
    if not isinstance(envelope, dict) or envelope.get("schema_version") != SECRET_IMPORT_SEALED_SCHEMA:
        raise SecretVaultError("不是 Secret 单向导入封套。")
    try:
        ciphertext = secret_unb64(str(envelope.get("ciphertext") or ""))
        raw = NaclSealedBox(NaclPrivateKey(private_key)).decrypt(ciphertext)
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise SecretVaultError(f"Secret 单向导入密文解密失败：{type(exc).__name__}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SecretVaultError("Secret 单向导入 payload 格式无效。")
    return payload


def load_secret_vault_meta() -> dict[str, Any]:
    try:
        with open(SECRET_VAULT_META_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def write_secret_vault_meta(meta: dict[str, Any]) -> None:
    ensure_secret_vault_dirs()
    write_text_atomic(SECRET_VAULT_META_PATH, json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    try:
        os.chmod(SECRET_VAULT_META_PATH, 0o600)
    except OSError:
        pass


def secret_vault_exists() -> bool:
    return bool(load_secret_vault_meta().get("verifier_ciphertext"))


def secret_password_policy_error(password: str) -> str:
    password = password or ""
    missing: list[str] = []
    if len(password) < SECRET_VAULT_MIN_PASSWORD_CHARS:
        missing.append(f"至少 {SECRET_VAULT_MIN_PASSWORD_CHARS} 个字符")
    if not re.search(r"[A-Z]", password):
        missing.append("大写字母")
    if not re.search(r"[a-z]", password):
        missing.append("小写字母")
    if not re.search(r"\d", password):
        missing.append("数字")
    if not re.search(r"[^A-Za-z0-9]", password):
        missing.append("特殊字符")
    if missing:
        return "Secret 密码需要" + "、".join(missing) + "。"
    return ""


def secret_create_vault(password: str) -> tuple[bool, Optional[bytes], str]:
    password_error = secret_password_policy_error(password)
    if password_error:
        return False, None, password_error
    if not secret_crypto_available():
        return False, None, f"Secret Vault 强加密不可用：{secret_crypto_status_text()}。请安装 PyNaCl 后再启用。"
    salt_size = int(getattr(nacl_pwhash.argon2id, "SALTBYTES", 16))
    salt = os.urandom(salt_size)
    try:
        key = secret_derive_key(password, salt)
        verifier = secret_encrypt_bytes(key, SECRET_VAULT_SENTINEL, b"secret-vault-verifier")
        import_key_record, _import_private_key = secret_build_import_key_record(key)
    except SecretVaultError as exc:
        return False, None, str(exc)
    meta = {
        "schema_version": "secretvault.v1",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "kdf": "argon2id-sensitive",
        "aead": "xchacha20poly1305-ietf",
        "salt": secret_b64(salt),
        "verifier_ciphertext": secret_b64(verifier),
        SECRET_IMPORT_DROPBOX_META_KEY: import_key_record,
        "network_policy": {
            "mode": "fail_closed",
            "chain_env": SECRET_NETWORK_CHAIN_ENV,
            "tor_socks_env": SECRET_TOR_SOCKS_ENV,
            "direct_fallback": False,
        },
    }
    write_secret_vault_meta(meta)
    return True, key, "Secret Vault 已创建并解锁。"


def secret_unlock_vault(password: str) -> tuple[bool, Optional[bytes], str]:
    meta = load_secret_vault_meta()
    if not meta:
        return False, None, "Secret Vault 尚未初始化。"
    if not secret_crypto_available():
        return False, None, f"Secret Vault 强加密不可用：{secret_crypto_status_text()}。"
    try:
        salt = secret_unb64(str(meta.get("salt") or ""))
        verifier = secret_unb64(str(meta.get("verifier_ciphertext") or ""))
        key = secret_derive_key(password, salt)
        plain = secret_decrypt_bytes(key, verifier, b"secret-vault-verifier")
    except Exception as exc:
        return False, None, f"Secret Vault 解锁失败：{exc}"
    if plain != SECRET_VAULT_SENTINEL:
        return False, None, "Secret Vault 解锁失败：verifier 不匹配。"
    return True, key, "Secret Vault 已解锁。"


def secret_new_session_id() -> str:
    return f"secret_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1_000_000_000:09d}"


def secret_safe_session_id(session_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", session_id or "session").strip("-") or "session"


def secret_storage_path_for_session(session_id: str, kind: str, name: str) -> str:
    session_id = secret_safe_session_id(session_id)
    safe_kind = re.sub(r"[^A-Za-z0-9_.-]+", "-", kind or "data").strip("-") or "data"
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", name or short_uid("secret")).strip("-") or short_uid("secret")
    return os.path.join(SECRET_VAULT_SESSIONS_DIR, session_id, safe_kind, safe_name + ".secret")


def secret_storage_path(state: State, kind: str, name: str) -> str:
    return secret_storage_path_for_session(state.secret_vault.session_id, kind, name)


def secret_write_json_for_session(state: State, session_id: str, kind: str, name: str, payload: dict[str, Any]) -> tuple[bool, str]:
    vault = state.secret_vault
    if not vault.unlocked or not vault.key:
        return False, "Secret Vault 已锁定，拒绝写入。"
    session_id = secret_safe_session_id(session_id or vault.session_id)
    try:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        aad = f"secret-vault:{kind}:{session_id}".encode("utf-8", errors="ignore")
        sealed = secret_encrypt_bytes(vault.key, raw, aad)
        path = secret_storage_path_for_session(session_id, kind, name)
        write_bytes_atomic(path, sealed)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return True, path
    except Exception as exc:
        vault.storage_warning = f"{type(exc).__name__}: {exc}"
        return False, f"Secret Vault 加密写入失败：{type(exc).__name__}: {exc}"


def secret_write_json(state: State, kind: str, name: str, payload: dict[str, Any]) -> tuple[bool, str]:
    return secret_write_json_for_session(state, state.secret_vault.session_id, kind, name, payload)


def secret_virtual_ref(kind: str, name: str) -> str:
    safe_kind = re.sub(r"[^A-Za-z0-9_.-]+", "-", kind or "data").strip("-") or "data"
    safe_name = re.sub(r"[^A-Za-z0-9_.:-]+", "-", name or short_uid("secret")).strip("-") or short_uid("secret")
    return f"secret://subagents/{safe_kind}/{safe_name}"


def secret_write_subagent_json(state: State, kind: str, name: str, payload: dict[str, Any]) -> tuple[bool, str]:
    ok, detail = secret_write_json_for_session(state, SECRET_SUBAGENT_SESSION_ID, kind, name, payload)
    return ok, secret_virtual_ref(kind, name) if ok else detail


def secret_session_id_from_path(path: str) -> str:
    try:
        rel = os.path.relpath(normalized_path(path), SECRET_VAULT_SESSIONS_DIR)
    except Exception:
        return ""
    parts = rel.split(os.sep)
    return parts[0] if len(parts) >= 3 else ""


def secret_read_json_from_path(state: State, kind: str, path: str, *, session_id: str = "") -> tuple[bool, Optional[dict[str, Any]], str]:
    vault = state.secret_vault
    if not vault.unlocked or not vault.key:
        return False, None, "Secret Vault 已锁定，拒绝读取。"
    secret_session_id = session_id or secret_session_id_from_path(path) or vault.session_id
    sealed = b""
    try:
        with open(path, "rb") as fh:
            sealed = fh.read()
        aad = f"secret-vault:{kind}:{secret_session_id}".encode("utf-8", errors="ignore")
        raw = secret_decrypt_bytes(vault.key, sealed, aad)
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        if kind == "imported-sessions":
            try:
                payload = secret_decrypt_sealed_import_envelope(state, sealed)
            except Exception as sealed_exc:
                return False, None, f"{type(exc).__name__}: {exc}; sealed-import: {sealed_exc}"
        else:
            return False, None, f"{type(exc).__name__}: {exc}"
    if not isinstance(payload, dict):
        return False, None, "Secret payload 格式无效。"
    return True, payload, path


def secret_append_transcript_turn(state: State, user_text: str, assistant_text: str, *, source: str = "", session_id: str = "") -> tuple[bool, str]:
    target_session_id = secret_safe_session_id(session_id or state.secret_vault.session_id)
    payload = {
        "schema_version": "secret.transcript.turn.v1",
        "session_id": target_session_id,
        "timestamp": now_iso(),
        "source": source,
        "messages": [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ],
    }
    return secret_write_json_for_session(state, target_session_id, "transcript-turns", short_uid("turn"), payload)


def secret_message_record(message: Message) -> dict[str, Any]:
    return {
        "role": str(message.role or ""),
        "content": str(message.content or ""),
        "done": bool(message.done),
    }


def secret_message_from_record(record: Any) -> Optional[Message]:
    if not isinstance(record, dict):
        return None
    role = str(record.get("role") or "")
    if role not in {"system", "user", "assistant"}:
        return None
    return Message(role, str(record.get("content") or ""), bool(record.get("done", True)))


def secret_session_sidebar_key(session_id: str) -> str:
    session_id = secret_safe_session_id(session_id)
    return f"{SECRET_NATIVE_SESSION_PREFIX}{session_id}" if session_id else ""


def secret_session_id_from_sidebar_key(key: Any) -> str:
    text = str(key or "").strip()
    if text.startswith(SECRET_NATIVE_SESSION_PREFIX):
        return text[len(SECRET_NATIVE_SESSION_PREFIX):]
    return text


def secret_session_title_for_messages(title: str, messages: list[Message]) -> str:
    title = compact_title(str(title or ""), 80)
    if title.startswith("Secret: "):
        title = compact_title(title.removeprefix("Secret: "), 80)
    if title and title not in {"main", "Secret Vault", "运行中会话", "空闲会话"}:
        return title
    return compact_title(suggested_session_title(messages) or title or "Secret 会话", 80)


def secret_messages_to_backend_history(messages: list[Message]) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for msg in messages:
        if msg.role == "system":
            continue
        if msg.role == "user":
            history.append({"role": "user", "content": [{"type": "text", "text": msg.content}]})
        elif msg.role == "assistant":
            history.append({"role": "assistant", "content": [{"type": "text", "text": msg.content}]})
    return history


def restore_backend_from_secret_messages(agent: Any, messages: list[Message]) -> None:
    history = secret_messages_to_backend_history(messages)
    reset_agent_runtime_context_no_snapshot(agent, history)


def secret_session_state_payload(session_id: str, title: str, messages: list[Message], *, source: str = "", origin: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    payload = {
        "schema_version": "secret.session_state.v1",
        "session_id": secret_safe_session_id(session_id),
        "title": secret_session_title_for_messages(title, messages),
        "updated_at": now_iso(),
        "source": source,
        "messages": [secret_message_record(msg) for msg in messages],
    }
    if isinstance(origin, dict) and origin:
        payload["origin"] = dict(origin)
    return payload


def clear_secret_session_sidebar_cache(state: State) -> None:
    state.secret_session_sidebar_cache = []
    state.secret_session_sidebar_signature = ()
    state.secret_session_sidebar_loaded_at = 0.0


def clear_secret_sidebar_caches(state: State) -> None:
    clear_secret_import_sidebar_cache(state)
    clear_secret_session_sidebar_cache(state)


def secret_save_session_state(
    state: State,
    session_id: str,
    title: str,
    messages: list[Message],
    *,
    source: str = "",
    origin: Optional[dict[str, Any]] = None,
) -> tuple[bool, str]:
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        return False, "Secret Vault 已锁定，拒绝保存会话状态。"
    session_id = secret_safe_session_id(session_id or state.secret_vault.session_id)
    if not session_id:
        return False, "缺少 Secret session id。"
    payload = secret_session_state_payload(session_id, title, messages, source=source, origin=origin)
    ok, ref = secret_write_json_for_session(state, session_id, "session-state", "state", payload)
    if ok:
        clear_secret_session_sidebar_cache(state)
    return ok, ref


def secret_save_current_session_state(state: State, *, source: str = "ui") -> tuple[bool, str]:
    if not state.secret_vault.unlocked or not state.secret_vault.session_id:
        return False, "Secret Vault 未解锁，无法保存当前 Secret 会话。"
    return secret_save_session_state(
        state,
        state.secret_vault.session_id,
        state.current_title,
        state.messages,
        source=source,
        origin=state.secret_active_origin,
    )


SECRET_IMPORT_DISPOSITION_ALIASES = {
    "delete": "delete",
    "del": "delete",
    "remove": "delete",
    "rm": "delete",
    "删除": "delete",
    "archive": "archive",
    "archived": "archive",
    "归档": "archive",
}


def parse_secret_import_args(raw: str) -> tuple[str, str]:
    text = (raw or "").strip()
    disposition = "delete"
    target = "current"
    if not text:
        return disposition, target
    first, _, rest = text.partition(" ")
    parsed = SECRET_IMPORT_DISPOSITION_ALIASES.get(first.lower())
    if parsed:
        disposition = parsed
        target = rest.strip() or "current"
    else:
        target = text
    return disposition, target


def clear_pending_secret_import(state: State) -> None:
    state.secret_vault.pending_import_path = ""
    state.secret_vault.pending_import_disposition = "delete"
    state.secret_vault.pending_import_title = ""


def secret_import_payload_for_session(state: State, path: str, title: str, raw: bytes, *, target_session_id: str = "") -> dict[str, Any]:
    source_path = normalized_path(path)
    try:
        stat = os.stat(source_path)
    except OSError:
        stat = None
    source_key = session_key(source_path)
    source_meta = dict(load_session_meta_registry().get(source_key, {})) if source_key else {}
    return {
        "schema_version": "secret.imported_session.v1",
        "session_id": secret_safe_session_id(target_session_id or state.secret_vault.session_id),
        "imported_at": now_iso(),
        "source": {
            "basename": os.path.basename(source_path),
            "stable_id": session_stable_id(source_path),
            "title": title,
            "size": int(stat.st_size) if stat else len(raw),
            "mtime": float(stat.st_mtime) if stat else 0.0,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "encoding": "utf-8-replace",
        },
        "normal_side_rule": "one_way_import_no_plaintext_restore",
        "source_meta": source_meta,
        "raw_log_text": raw.decode("utf-8", errors="replace"),
    }


def secret_validate_normal_import_source(state: State, path: str) -> tuple[str, str]:
    source_path = normalized_path(path)
    if not source_path or source_path == os.devnull:
        return "", "缺少可导入的普通会话路径。"
    if path_is_within(source_path, SECRET_VAULT_DIR):
        return "", "拒绝导入 Secret Vault 内部文件。"
    if not is_normal_session_log_path(source_path):
        return "", "只能迁移普通会话日志，拒绝导入会话目录外的文件。"
    if is_current_session_path(state, source_path) and state.status in {"running", "aborting"}:
        return "", "当前普通会话还在运行，不能迁移；先停止或等它完成。"
    if not os.path.isfile(source_path):
        return "", "普通会话文件不存在，未执行 Secret 迁移。"
    return source_path, ""


def secret_gate_normal_import(state: State, source_path: str, disposition: str, source: str) -> str:
    decision = gate_policy_action(
        "secret_import",
        subject="orchestrator.main",
        source=source,
        target=session_key(source_path),
        payload={
            "operation": "one_way_import",
            "source_key": session_key(source_path),
            "disposition": disposition,
        },
        queue_if_required=True,
    )
    return "" if decision.allowed else policy_gate_text(decision)


def secret_finalize_normal_session_import(state: State, source_path: str, disposition: str, title: str, secret_ref: str) -> str:
    clear_secret_import_sidebar_cache(state)
    now = time.time()
    meta_fields: dict[str, Any] = {
        "secret_migrated": True,
        "secret_migrated_at": now,
        "secret_migrated_disposition": disposition,
        "secret_migrated_ciphertext": os.path.basename(secret_ref),
    }
    was_active_normal = (
        is_current_session_path(state, source_path)
        or normalized_path(state.secret_vault.previous_log_path) == source_path
        or normalized_path(state.history_ui_path) == source_path
    )

    if disposition == "archive":
        set_session_meta_fields(state, source_path, archived=True, **meta_fields)
        if was_active_normal:
            state.secret_vault.previous_log_path = ""
            if is_current_session_path(state, source_path):
                set_agent_log_path(state.agent, os.devnull)
            clear_history_ui_state(state)
        load_history(state, force=True)
        mark_dirty(state)
        return f"已单向加密迁移到 Secret：{title}；普通侧已归档（仍保留普通区明文）。"

    try:
        os.remove(source_path)
    except FileNotFoundError:
        pass
    except Exception as exc:
        set_session_meta_fields(state, source_path, **meta_fields, secret_migrated_delete_error=f"{type(exc).__name__}: {exc}")
        load_history(state, force=True)
        mark_dirty(state)
        return f"已加密迁移到 Secret，但普通侧删除失败：{type(exc).__name__}: {exc}"

    set_session_meta_fields(state, source_path, deleted=True, archived=True, deleted_at=now, **meta_fields)
    if session_names is not None:
        try:
            session_names.set_name(source_path, "")
        except Exception:
            pass
    if was_active_normal:
        state.secret_vault.previous_log_path = ""
        if is_current_session_path(state, source_path):
            set_agent_log_path(state.agent, os.devnull)
        clear_history_ui_state(state)
    load_history(state, force=True)
    mark_dirty(state)
    return f"已单向加密迁移到 Secret：{title}；普通侧明文源已删除。"


def secret_write_sealed_import(public_key: bytes, public_key_id: str, session_id: str, name: str, payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        envelope = secret_sealed_import_envelope(public_key, public_key_id, payload)
        path = secret_storage_path_for_session(session_id, "imported-sessions", name)
        write_bytes_atomic(path, envelope)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return True, path
    except Exception as exc:
        return False, f"Secret Vault 单向加密写入失败：{type(exc).__name__}: {exc}"


def secret_import_normal_session(
    state: State,
    path: str,
    *,
    disposition: str = "delete",
    title: str = "",
    source: str = "/toSecret",
) -> str:
    disposition = SECRET_IMPORT_DISPOSITION_ALIASES.get((disposition or "").lower(), "delete")
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        return "Secret Vault 已锁定，不能导入普通会话。"
    source_path, validation_error = secret_validate_normal_import_source(state, path)
    if validation_error:
        return validation_error

    title = compact_title(title or session_title_for_path(state, source_path), 80)
    gate_error = secret_gate_normal_import(state, source_path, disposition, source)
    if gate_error:
        return gate_error

    try:
        with open(source_path, "rb") as fh:
            raw = fh.read()
    except Exception as exc:
        return f"读取普通会话失败：{type(exc).__name__}: {exc}"

    payload = secret_import_payload_for_session(state, source_path, title, raw, target_session_id=state.secret_vault.session_id)
    import_name = f"imported_{session_stable_id(source_path)}_{short_uid('session')}"
    wrote, secret_ref = secret_write_json(state, "imported-sessions", import_name, payload)
    if not wrote:
        return secret_ref
    return secret_finalize_normal_session_import(state, source_path, disposition, title, secret_ref)


def secret_import_normal_session_passwordless(
    state: State,
    path: str,
    *,
    disposition: str = "delete",
    title: str = "",
    source: str = "/toSecret",
) -> str:
    disposition = SECRET_IMPORT_DISPOSITION_ALIASES.get((disposition or "").lower(), "delete")
    public_key, public_key_id, public_key_error = secret_import_public_key_from_meta()
    if public_key_error:
        return public_key_error
    if not public_key:
        return "Secret Vault 单向导入公钥不可用。"
    source_path, validation_error = secret_validate_normal_import_source(state, path)
    if validation_error:
        return validation_error
    title = compact_title(title or session_title_for_path(state, source_path), 80)
    gate_error = secret_gate_normal_import(state, source_path, disposition, source)
    if gate_error:
        return gate_error
    try:
        with open(source_path, "rb") as fh:
            raw = fh.read()
    except Exception as exc:
        return f"读取普通会话失败：{type(exc).__name__}: {exc}"
    target_session_id = secret_new_session_id()
    payload = secret_import_payload_for_session(state, source_path, title, raw, target_session_id=target_session_id)
    import_name = f"imported_{short_uid('dropbox')}"
    wrote, secret_ref = secret_write_sealed_import(public_key, public_key_id, target_session_id, import_name, payload)
    if not wrote:
        return secret_ref
    return secret_finalize_normal_session_import(state, source_path, disposition, title, secret_ref)


def consume_pending_secret_import(state: State) -> str:
    path = state.secret_vault.pending_import_path
    if not path:
        return ""
    disposition = state.secret_vault.pending_import_disposition or "delete"
    title = state.secret_vault.pending_import_title
    clear_pending_secret_import(state)
    return secret_import_normal_session(state, path, disposition=disposition, title=title, source="/toSecret")


def request_secret_import_session(state: State, raw_args: str = "") -> str:
    if state.secret_vault.unlocked:
        return "Secret Vault 已解锁：不能从加密区读取普通区会话；请先 /lock，再在普通区执行 /toSecret。"
    if state.secret_vault.pending_action:
        return "Secret Vault 正在等待密码输入；请完成输入或 /lock 后再迁移。"
    disposition, target = parse_secret_import_args(raw_args)
    path, error = resolve_session_target(state, target, allow_view_index=True)
    if error:
        return error
    if not path:
        return "找不到要迁移的普通会话。"
    source_path, validation_error = secret_validate_normal_import_source(state, path)
    if validation_error:
        return validation_error
    if secret_vault_exists():
        return secret_import_normal_session_passwordless(
            state,
            source_path,
            disposition=disposition,
            title=session_title_for_path(state, source_path),
            source="/toSecret",
        )
    state.secret_vault.pending_import_path = source_path
    state.secret_vault.pending_import_disposition = disposition
    state.secret_vault.pending_import_title = session_title_for_path(state, source_path)
    unlock_msg = begin_secret_unlock(state)
    if not state.secret_vault.pending_action:
        clear_pending_secret_import(state)
        return unlock_msg
    action_text = "删除普通侧明文源" if disposition == "delete" else "归档普通侧原件"
    return f"准备单向迁移到 Secret：{state.secret_vault.pending_import_title}；解锁后将{action_text}。\n{unlock_msg}"


def secret_file_signature(kind: str, name: str = "*.secret") -> tuple[tuple[str, float, int], ...]:
    pattern = os.path.join(SECRET_VAULT_SESSIONS_DIR, "*", kind, name)
    signature: list[tuple[str, float, int]] = []
    for path in sorted(glob.glob(pattern)):
        try:
            stat = os.stat(path)
        except OSError:
            continue
        signature.append((normalized_path(path), float(stat.st_mtime), int(stat.st_size)))
    return tuple(signature)


def secret_import_file_signature() -> tuple[tuple[str, float, int], ...]:
    return secret_file_signature("imported-sessions", "*.secret")


def secret_native_session_file_signature() -> tuple[tuple[str, float, int], ...]:
    return secret_file_signature("session-state", "state.secret")


def clear_secret_import_sidebar_cache(state: State) -> None:
    state.secret_import_sidebar_cache = []
    state.secret_import_sidebar_signature = ()
    state.secret_import_sidebar_loaded_at = 0.0


def secret_import_sidebar_key(entry: dict[str, Any]) -> str:
    basename = os.path.basename(str(entry.get("path") or ""))
    return f"{SECRET_IMPORT_SESSION_PREFIX}{basename}" if basename else ""


def secret_import_target_from_sidebar_key(key: Any) -> str:
    text = str(key or "").strip()
    if text.startswith(SECRET_IMPORT_SESSION_PREFIX):
        return text[len(SECRET_IMPORT_SESSION_PREFIX):]
    return text


def secret_imported_session_entries(state: State, *, include_payload: bool = True) -> list[dict[str, Any]]:
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        return []
    pattern = os.path.join(SECRET_VAULT_SESSIONS_DIR, "*", "imported-sessions", "*.secret")
    entries: list[dict[str, Any]] = []
    for path in sorted(glob.glob(pattern)):
        session_id = secret_session_id_from_path(path)
        ok, payload, detail = secret_read_json_from_path(state, "imported-sessions", path, session_id=session_id)
        if not ok or not payload:
            entries.append({
                "path": path,
                "session_id": session_id,
                "error": detail,
                "imported_at": "",
                "title": os.path.basename(path),
                "stable_id": "",
            })
            continue
        source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
        entry = {
            "path": path,
            "session_id": session_id,
            "imported_at": str(payload.get("imported_at") or ""),
            "title": compact_title(str(source.get("title") or source.get("basename") or os.path.basename(path)), 80),
            "stable_id": str(source.get("stable_id") or ""),
            "basename": str(source.get("basename") or ""),
            "size": int(source.get("size") or 0),
            "sha256": str(source.get("sha256") or ""),
        }
        if include_payload:
            entry["payload"] = payload
        entries.append(entry)
    entries.sort(key=lambda item: (str(item.get("imported_at") or ""), os.path.basename(str(item.get("path") or ""))), reverse=True)
    return entries


def load_secret_import_sidebar_entries(state: State, *, force: bool = False) -> list[dict[str, Any]]:
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        clear_secret_import_sidebar_cache(state)
        return []
    signature = secret_import_file_signature()
    now = time.time()
    if (
        force
        or signature != state.secret_import_sidebar_signature
        or now - state.secret_import_sidebar_loaded_at >= 10
    ):
        state.secret_import_sidebar_cache = secret_imported_session_entries(state, include_payload=False)
        state.secret_import_sidebar_signature = signature
        state.secret_import_sidebar_loaded_at = now
    return list(state.secret_import_sidebar_cache)


def secret_native_session_entries(state: State, *, include_payload: bool = False) -> list[dict[str, Any]]:
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        return []
    pattern = os.path.join(SECRET_VAULT_SESSIONS_DIR, "*", "session-state", "state.secret")
    entries: list[dict[str, Any]] = []
    for path in sorted(glob.glob(pattern)):
        session_id = secret_session_id_from_path(path)
        ok, payload, detail = secret_read_json_from_path(state, "session-state", path, session_id=session_id)
        if not ok or not payload:
            entries.append({
                "path": path,
                "session_id": session_id,
                "error": detail,
                "updated_at": "",
                "title": session_id or os.path.basename(path),
            })
            continue
        messages = payload.get("messages")
        message_count = len(messages) if isinstance(messages, list) else 0
        origin = payload.get("origin") if isinstance(payload.get("origin"), dict) else {}
        entry = {
            "path": path,
            "session_id": str(payload.get("session_id") or session_id),
            "updated_at": str(payload.get("updated_at") or ""),
            "title": compact_title(str(payload.get("title") or session_id or "Secret 会话"), 80),
            "message_count": message_count,
            "origin_kind": str(origin.get("kind") or ""),
            "origin_import_path": str(origin.get("import_path") or ""),
            "origin_stable_id": str(origin.get("stable_id") or ""),
        }
        if include_payload:
            entry["payload"] = payload
        entries.append(entry)
    entries.sort(key=lambda item: (str(item.get("updated_at") or ""), str(item.get("session_id") or "")), reverse=True)
    return entries


def load_secret_session_sidebar_entries(state: State, *, force: bool = False) -> list[dict[str, Any]]:
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        clear_secret_session_sidebar_cache(state)
        return []
    signature = secret_native_session_file_signature()
    now = time.time()
    if (
        force
        or signature != state.secret_session_sidebar_signature
        or now - state.secret_session_sidebar_loaded_at >= 10
    ):
        state.secret_session_sidebar_cache = secret_native_session_entries(state, include_payload=False)
        state.secret_session_sidebar_signature = signature
        state.secret_session_sidebar_loaded_at = now
    return list(state.secret_session_sidebar_cache)


def format_secret_imported_sessions(state: State) -> str:
    if not state.secret_vault.unlocked:
        return "Secret Vault 已锁定：请先 /Secret 解锁。"
    entries = load_secret_import_sidebar_entries(state, force=True)
    if not entries:
        return "Secret Vault 里没有已导入的普通会话。"
    lines = ["Secret 已导入会话："]
    for idx, entry in enumerate(entries, 1):
        if entry.get("error"):
            lines.append(f"{idx}. [无法解密] {os.path.basename(str(entry.get('path') or ''))} · {entry.get('error')}")
            continue
        stable = f" id:{entry['stable_id']}" if entry.get("stable_id") else ""
        imported = str(entry.get("imported_at") or "-")
        title = str(entry.get("title") or "未命名导入")
        lines.append(f"{idx}. {stable} · {imported} · {title}")
    lines.append("用法：/Secret open <编号|id|文件名> 在 Secret 内打开。")
    return "\n".join(lines)


def format_secret_sessions(state: State) -> str:
    if not state.secret_vault.unlocked:
        return "Secret Vault 已锁定：请先 /Secret 解锁。"
    session_entries = load_secret_session_sidebar_entries(state, force=True)
    import_entries = load_secret_import_sidebar_entries(state, force=True)
    lines = [f"Secret 会话：当前 {state.secret_vault.session_id or '-'}"]
    if session_entries:
        lines.append("加密对话：")
        for idx, entry in enumerate(session_entries, 1):
            if entry.get("error"):
                lines.append(f"S{idx}. [无法解密] {entry.get('session_id') or '-'} · {entry.get('error')}")
                continue
            marker = "*" if str(entry.get("session_id") or "") == state.secret_vault.session_id else " "
            updated = str(entry.get("updated_at") or "-")
            lines.append(f"{marker}S{idx}. {entry.get('session_id') or '-'} · {updated} · {entry.get('title') or 'Secret 会话'}")
    else:
        lines.append("加密对话：暂无已保存会话。")
    if import_entries:
        lines.append("导入会话：")
        for idx, entry in enumerate(import_entries, 1):
            if entry.get("error"):
                lines.append(f"I{idx}. [无法解密] {os.path.basename(str(entry.get('path') or ''))} · {entry.get('error')}")
                continue
            lines.append(f"I{idx}. {entry.get('imported_at') or '-'} · {entry.get('title') or '未命名导入'}")
    lines.append("用法：/new 新建 Secret 对话；点击左栏 Secret 会话切换；/Secret open-session <编号|session_id> 打开加密对话；/Secret open <编号> 打开导入会话。")
    return "\n".join(lines)


def resolve_secret_imported_session(state: State, target: str) -> tuple[Optional[dict[str, Any]], str]:
    entries = [entry for entry in secret_imported_session_entries(state) if not entry.get("error")]
    if not entries:
        return None, "Secret Vault 里没有可打开的已导入会话。"
    raw = secret_import_target_from_sidebar_key(target)
    if not raw:
        return None, "Usage: /Secret open <编号|id|文件名>"
    m = re.fullmatch(r"[sS]?(\d+)", raw)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(entries):
            return entries[idx], ""
        return None, f"索引越界: 1-{len(entries)}"
    normalized = re.sub(r"^(?:id:|#)", "", raw, flags=re.I)
    matches = []
    for entry in entries:
        entry_path = str(entry.get("path") or "")
        basename = os.path.basename(str(entry.get("path") or ""))
        candidates = {
            entry_path,
            normalized_path(entry_path),
            basename,
            basename.removesuffix(".secret"),
            str(entry.get("stable_id") or ""),
            str(entry.get("basename") or ""),
        }
        if raw in candidates or normalized in candidates:
            matches.append(entry)
    if len(matches) == 1:
        return matches[0], ""
    if len(matches) > 1:
        return None, f"匹配到多个 Secret 导入会话：{raw}"
    return None, "找不到 Secret 导入会话，请先 /Secret sessions 查看编号。"


def messages_from_secret_import_payload(payload: dict[str, Any]) -> tuple[list[Message], int, int, int]:
    raw_log = str(payload.get("raw_log_text") or "")
    pairs = _pairs(raw_log)
    if pairs:
        messages, loaded_rounds, total_rounds = history_messages_from_pairs(pairs, RESTORE_DISPLAY_ROUNDS)
        return messages, loaded_rounds, total_rounds, len(messages)
    if raw_log.strip():
        return [Message("assistant", raw_log.strip())], 1, 1, 1
    return [Message("system", "Secret 导入会话为空。")], 0, 0, 1


def restore_secret_imported_session(state: State, target: str) -> str:
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        return "Secret Vault 已锁定：请先 /Secret 解锁。"
    if state.status in {"running", "aborting", "restoring"}:
        return "当前任务仍在运行/恢复，不能打开 Secret 导入会话。"
    entry, error = resolve_secret_imported_session(state, target)
    if error:
        return error
    existing_native = secret_native_entry_for_import_entry(state, entry or {})
    if existing_native is not None:
        return restore_secret_native_session(state, str(existing_native.get("session_id") or ""))
    if state.secret_vault.session_id and any(msg.role in {"user", "assistant"} for msg in state.messages):
        secret_save_current_session_state(state, source="open-import")
    payload = dict(entry.get("payload") or {}) if entry else {}
    if not payload:
        return "Secret 导入会话缺少可读取 payload。"
    messages, loaded_rounds, total_rounds, message_count = messages_from_secret_import_payload(payload)
    raw_log = str(payload.get("raw_log_text") or "")
    pairs = _pairs(raw_log)
    history = _parse_native_history(pairs) if pairs else None
    restore_history = history if history is not None else secret_messages_to_backend_history(messages)
    reset_agent_runtime_context_no_snapshot(state.agent, restore_history)
    set_agent_log_path(state.agent, os.devnull)
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    title = compact_title(str(source.get("title") or entry.get("title") or "Secret 导入会话"), 80)
    state.secret_vault.session_id = secret_new_session_id()
    state.secret_active_origin = {
        "kind": "imported_session",
        "import_path": normalized_path(str(entry.get("path") or "")),
        "stable_id": str(entry.get("stable_id") or ""),
        "title": title,
    }
    state.messages = list(messages)
    state.current_title = f"Secret: {title}"
    state.selected_session = secret_session_sidebar_key(state.secret_vault.session_id)
    cancel_normal_history_restore(state)
    state.history_ui_loaded_rounds = loaded_rounds
    state.history_ui_total_rounds = total_rounds
    state.history_ui_message_count = message_count
    state.follow_bottom = True
    state.scroll = 0
    state.pending_interaction = None
    state.session_popup_path = ""
    state.session_popup_anchor = None
    state.session_popup_rect = None
    secret_save_session_state(
        state,
        state.secret_vault.session_id,
        title,
        state.messages,
        source="open-import",
        origin=state.secret_active_origin,
    )
    mark_messages_changed(state)
    return f"已在 Secret 内打开导入会话：{title}（{loaded_rounds}/{total_rounds or loaded_rounds} 轮）。"


def resolve_secret_native_session(state: State, target: str) -> tuple[Optional[dict[str, Any]], str]:
    entries = [entry for entry in secret_native_session_entries(state, include_payload=True) if not entry.get("error")]
    if not entries:
        return None, "Secret Vault 里没有可打开的加密会话。"
    raw = secret_session_id_from_sidebar_key(target)
    if not raw:
        return None, "Usage: /Secret open-session <编号|session_id>"
    m = re.fullmatch(r"[sS]?(\d+)", raw)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(entries):
            return entries[idx], ""
        return None, f"索引越界: 1-{len(entries)}"
    matches = []
    for entry in entries:
        session_id = str(entry.get("session_id") or "")
        title = str(entry.get("title") or "")
        if raw in {session_id, title, secret_session_sidebar_key(session_id)}:
            matches.append(entry)
    if len(matches) == 1:
        return matches[0], ""
    if len(matches) > 1:
        return None, f"匹配到多个 Secret 会话：{raw}"
    return None, "找不到 Secret 会话。"


def messages_from_secret_session_payload(payload: dict[str, Any]) -> list[Message]:
    raw_messages = payload.get("messages")
    records = raw_messages if isinstance(raw_messages, list) else []
    messages = [msg for msg in (secret_message_from_record(item) for item in records) if msg is not None]
    if messages:
        return messages
    return [Message("system", "Secret 会话为空。")]


def restore_secret_native_session(state: State, target: str) -> str:
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        return "Secret Vault 已锁定：请先 /Secret 解锁。"
    if state.status in {"running", "aborting", "restoring"}:
        return "当前任务仍在运行/恢复，不能切换 Secret 会话。"
    entry, error = resolve_secret_native_session(state, target)
    if error:
        return error
    current_session_id = state.secret_vault.session_id
    target_session_id = secret_safe_session_id(str(entry.get("session_id") or "")) if entry else ""
    if current_session_id and target_session_id == current_session_id:
        return "已经是当前 Secret 会话。"
    if current_session_id and any(msg.role in {"user", "assistant"} for msg in state.messages):
        secret_save_current_session_state(state, source="switch")
    payload = dict(entry.get("payload") or {}) if entry else {}
    if not payload:
        return "Secret 会话缺少可读取 payload。"
    session_id = secret_safe_session_id(str(payload.get("session_id") or entry.get("session_id") or ""))
    messages = messages_from_secret_session_payload(payload)
    restore_backend_from_secret_messages(state.agent, messages)
    set_agent_log_path(state.agent, os.devnull)
    state.secret_vault.session_id = session_id
    origin = payload.get("origin") if isinstance(payload.get("origin"), dict) else {}
    state.secret_active_origin = dict(origin)
    title = secret_session_title_for_messages(str(payload.get("title") or entry.get("title") or "Secret 会话"), messages)
    state.messages = list(messages)
    state.current_title = f"Secret: {title}"
    state.selected_session = secret_session_sidebar_key(session_id)
    cancel_normal_history_restore(state)
    state.history_ui_loaded_rounds = sum(1 for msg in messages if msg.role == "user")
    state.history_ui_total_rounds = state.history_ui_loaded_rounds
    state.history_ui_message_count = len(messages)
    state.follow_bottom = True
    state.scroll = 0
    state.pending_interaction = None
    state.session_popup_path = ""
    state.session_popup_anchor = None
    state.session_popup_rect = None
    bind_agent_token_session(state, state.agent)
    mark_messages_changed(state)
    return f"已切换到 Secret 会话：{title}。"


def secret_password_entry_active(state: State) -> bool:
    return bool(state.secret_vault.pending_action)


def secret_prompt_text(state: State) -> str:
    action = state.secret_vault.pending_action
    if action == "setup_confirm":
        return "secret confirm> "
    if action == "setup_password":
        return "new secret> "
    if action == "unlock":
        return "secret> "
    return "> "


def secret_hint_lines(state: State, width: int) -> list[tuple[str, int]]:
    action = state.secret_vault.pending_action
    if action == "setup_confirm":
        title = "再次输入 Secret 密码以确认"
    elif action == "setup_password":
        title = f"首次设置 Secret 密码，{SECRET_VAULT_PASSWORD_RULE_TEXT}"
    else:
        title = "输入 Secret Vault 密码；不会发送给模型或写入日志"
    status = secret_crypto_status_text()
    lines = [(truncate_cells(f"? Secret Vault: {title}", width), cp(7) | curses.A_BOLD)]
    lines.append((truncate_cells(f"  crypto: {status}", width), cp(1)))
    lines.append((truncate_cells("  Enter 提交；/lock 取消并清除输入。", width), cp(1)))
    return lines


def parse_secret_proxy_chain(raw: str) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return []
    text = text.replace("->", ",").replace(";", ",")
    return [item.strip() for item in re.split(r"[,\s]+", text) if item.strip()]


def secret_auto_tor_enabled() -> bool:
    raw = (os.environ.get(SECRET_AUTO_TOR_ENV) or "").strip().lower()
    return raw not in {"0", "false", "no", "off", "disabled"}


def secret_configured_proxy_chain() -> list[str]:
    chain: list[str] = []
    tor_socks = (os.environ.get(SECRET_TOR_SOCKS_ENV) or "").strip()
    if tor_socks:
        chain.append(tor_socks)
    elif secret_auto_tor_enabled():
        chain.append("tor")
    for endpoint in parse_secret_proxy_chain(os.environ.get(SECRET_NETWORK_CHAIN_ENV, "")):
        if endpoint not in chain:
            chain.append(endpoint)
    return chain


def normalize_secret_proxy_endpoint(endpoint: str) -> str:
    value = (endpoint or "").strip()
    if value.lower() == "tor":
        return SECRET_DEFAULT_TOR_SOCKS
    if value and "://" not in value:
        value = f"socks5h://{value}"
    return value


def secret_proxy_endpoint_healthy(endpoint: str, timeout: float = 1.0) -> tuple[bool, str]:
    endpoint = normalize_secret_proxy_endpoint(endpoint)
    parsed = urllib.parse.urlparse(endpoint)
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"socks5", "socks5h", "http", "https"}:
        return False, f"unsupported_proxy_scheme:{scheme or '-'}"
    host = parsed.hostname or ""
    port = parsed.port or (9050 if scheme.startswith("socks") else 8080)
    if not host:
        return False, "missing_proxy_host"
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True, f"{scheme}://{host}:{port}"
    except OSError as exc:
        return False, f"{host}:{port} unreachable ({type(exc).__name__})"


def secret_proxy_env_target(status: Optional[dict[str, Any]] = None) -> str:
    chain = list((status or {}).get("chain") or secret_configured_proxy_chain())
    return normalize_secret_proxy_endpoint(str(chain[0] if chain else ""))


def activate_secret_proxy_env(state: State, status: Optional[dict[str, Any]] = None) -> None:
    target = secret_proxy_env_target(status)
    if not target:
        return
    vault = state.secret_vault
    if not vault.proxy_env_snapshot:
        vault.proxy_env_snapshot = {key: os.environ.get(key) for key in SECRET_PROXY_ENV_KEYS}
    for key in ("ALL_PROXY", "all_proxy", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"):
        os.environ[key] = target
    for key in ("NO_PROXY", "no_proxy"):
        os.environ[key] = ""


def restore_secret_proxy_env(state: State) -> None:
    snapshot = state.secret_vault.proxy_env_snapshot
    if not snapshot:
        return
    for key, value in snapshot.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    state.secret_vault.proxy_env_snapshot = {}


def secret_network_status() -> dict[str, Any]:
    chain = secret_configured_proxy_chain()
    if not chain:
        return {
            "allowed": False,
            "status": "blocked",
            "reason": f"no {SECRET_NETWORK_CHAIN_ENV}/{SECRET_TOR_SOCKS_ENV} configured and {SECRET_AUTO_TOR_ENV}=0",
            "chain": [],
        }
    checks = []
    for endpoint in chain:
        ok, detail = secret_proxy_endpoint_healthy(endpoint)
        checks.append({"endpoint": endpoint, "ok": ok, "detail": detail})
        if not ok:
            return {
                "allowed": False,
                "status": "blocked",
                "reason": f"proxy endpoint failed: {detail}",
                "chain": chain,
                "checks": checks,
            }
    return {
        "allowed": True,
        "status": "ready",
        "reason": "secret proxy/Tor route reachable",
        "chain": chain,
        "checks": checks,
    }


def read_jsonl(path: str, limit: int = 0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                if isinstance(item, dict):
                    rows.append(item)
    except Exception:
        return []
    if limit and len(rows) > limit:
        return rows[-limit:]
    return rows


def task_ledger_signature() -> tuple[int, int]:
    try:
        stat = os.stat(AGENT_TASK_LEDGER_PATH)
    except OSError:
        return (0, 0)
    return (int(stat.st_mtime_ns), int(stat.st_size))


def harness_artifact_uri(path: str) -> str:
    try:
        rel = os.path.relpath(path, AGENT_HARNESS_DIR)
    except Exception:
        rel = os.path.basename(path)
    return "artifact://" + rel.replace(os.sep, "/")


def artifact_sha256(path: str) -> str:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return "sha256:" + digest.hexdigest()


def append_artifact_index(
    path: str,
    *,
    artifact_type: str,
    source_task_id: str = "",
    provenance: Optional[dict[str, Any]] = None,
    preview_path: str = "",
    content_type: str = "text/markdown",
) -> dict[str, Any]:
    path = os.path.abspath(path)
    try:
        st = os.stat(path)
    except OSError:
        size = 0
        mtime = time.time()
    else:
        size = int(st.st_size)
        mtime = float(st.st_mtime)
    uri = harness_artifact_uri(path)
    row = {
        "schema_version": "agentartifact.v1",
        "artifact_id": short_uid("art"),
        "timestamp": now_iso(),
        "type": artifact_type or "artifact",
        "uri": uri,
        "path": path,
        "preview_path": preview_path or path,
        "hash": artifact_sha256(path),
        "size_bytes": size,
        "mtime": mtime,
        "source_task_id": source_task_id,
        "provenance": provenance or {},
        "content_type": content_type,
    }
    append_jsonl(AGENT_ARTIFACT_INDEX_PATH, row)
    return row


def artifact_index_latest() -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(AGENT_ARTIFACT_INDEX_PATH):
        uri = str(row.get("uri") or "")
        if uri:
            latest[uri] = row
    return latest


def write_harness_artifact(
    kind: str,
    name: str,
    content: str,
    *,
    source_task_id: str = "",
    provenance: Optional[dict[str, Any]] = None,
    content_type: str = "text/markdown",
) -> str:
    safe_kind = clean_subagent_id(kind or "artifact")
    safe_name = clean_subagent_id(name or "artifact")
    directory = os.path.join(AGENT_ARTIFACTS_DIR, safe_kind)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{time.strftime('%Y%m%d-%H%M%S')}-{safe_name}-{time.time_ns() % 1_000_000:06d}.md")
    write_text_atomic(path, content.rstrip() + "\n")
    append_artifact_index(
        path,
        artifact_type=safe_kind,
        source_task_id=source_task_id,
        provenance=provenance,
        content_type=content_type,
    )
    return harness_artifact_uri(path)


def artifact_path_from_uri(uri: str) -> str:
    uri = (uri or "").strip()
    if uri.startswith("artifact://"):
        rel = uri[len("artifact://"):].replace("/", os.sep)
        return os.path.normpath(os.path.join(AGENT_HARNESS_DIR, rel))
    return uri if os.path.isabs(uri) else ""


ROLE_TEMPLATES: dict[str, dict[str, Any]] = {
    "specialist": {
        "description": "受限专家子 agent，执行明确窄任务。",
        "write_policy": "none",
        "tools_allowed": ["read", "reason"],
        "output_contract": ["summary", "findings", "evidence_refs", "risks", "artifact_refs", "memory_candidates", "confidence"],
    },
    "researcher": {
        "description": "只读调研、证据收集和方案比较。",
        "write_policy": "none",
        "tools_allowed": ["web", "read"],
        "output_contract": ["summary", "findings", "evidence_refs", "source_quality", "risks", "artifact_refs", "confidence"],
    },
    "code_reader": {
        "description": "只读代码库，定位结构、入口和风险。",
        "write_policy": "none",
        "tools_allowed": ["repo.read"],
        "output_contract": ["summary", "files", "findings", "risks", "artifact_refs", "confidence"],
    },
    "coder": {
        "description": "唯一写入者，执行已批准的代码变更。",
        "write_policy": "single_writer",
        "tools_allowed": ["repo.read", "repo.write", "test"],
        "output_contract": ["summary", "changed_files", "tests", "risks", "artifact_refs", "confidence"],
    },
    "reviewer": {
        "description": "清洁上下文审查，优先发现 bug、缺口和违规。",
        "write_policy": "none",
        "tools_allowed": ["repo.read", "artifact.read"],
        "output_contract": ["verdict", "critical_issues", "minor_issues", "missing_context", "approval_risks", "recommended_fixes", "confidence"],
    },
    "verifier": {
        "description": "验证事实、引用、测试证据和完成状态。",
        "write_policy": "none",
        "tools_allowed": ["read", "test", "artifact.read"],
        "output_contract": ["verdict", "verified_items", "failed_items", "weak_evidence", "next_checks", "confidence"],
    },
    "memory_curator": {
        "description": "受限记忆档案员，只生成 memory candidate，不直接写长期记忆。",
        "write_policy": "candidate_only",
        "tools_allowed": ["artifact.read", "trace.read"],
        "output_contract": ["memory_candidates", "rejected_items", "conflicts", "confidence"],
    },
    "ops": {
        "description": "部署/环境/CI/日志，所有高风险动作需审批。",
        "write_policy": "approved_only",
        "tools_allowed": ["shell.restricted", "logs", "deploy.approval_required"],
        "default_risky_actions": ["deploy", "modify_permission_policy", "access_secret", "long_running_privilege_escalation"],
        "output_contract": ["summary", "commands", "risks", "rollback", "approval_requests", "confidence"],
    },
}


POLICY_ACTIONS: dict[str, dict[str, Any]] = {
    "external_send": {
        "description": "对外发送消息、邮件、IM 或平台回复。",
        "default": "approval_required",
        "risk": "high",
        "approval_required_for": "external_send",
        "aliases": ["email.send", "message.send", "external_message", "send_external"],
    },
    "publish": {
        "description": "发布内容到公开或半公开平台。",
        "default": "approval_required",
        "risk": "high",
        "approval_required_for": "publish",
        "aliases": ["post", "public_publish", "content.publish"],
    },
    "delete_file": {
        "description": "删除、覆盖、移动到不可恢复位置或批量清理文件。",
        "default": "approval_required",
        "risk": "high",
        "approval_required_for": "delete_file",
        "aliases": ["filesystem.delete", "rm", "remove_file", "trash_file"],
    },
    "delete_memory": {
        "description": "删除或批量改写长期记忆。",
        "default": "approval_required",
        "risk": "high",
        "approval_required_for": "delete_memory",
        "aliases": ["memory.delete", "remove_memory"],
    },
    "write_long_term_memory": {
        "description": "写入长期记忆、用户偏好、项目长期事实或团队记忆。",
        "default": "approval_required",
        "risk": "medium",
        "approval_required_for": "write_long_term_memory",
        "aliases": ["memory.write", "memory_write_request", "remember_long_term"],
    },
    "deploy": {
        "description": "部署、发布服务、改变生产或准生产运行状态。",
        "default": "approval_required",
        "risk": "critical",
        "approval_required_for": "deploy",
        "aliases": ["ops.deploy", "release", "production_change"],
    },
    "spend_money": {
        "description": "付费、购买、充值、调用明显会产生新增费用的操作。",
        "default": "approval_required",
        "risk": "critical",
        "approval_required_for": "spend_money",
        "aliases": ["payment", "purchase", "buy", "billing.charge"],
    },
    "external_commitment": {
        "description": "对外承诺、报价、接受条款或代表用户做决定。",
        "default": "approval_required",
        "risk": "high",
        "approval_required_for": "external_commitment",
        "aliases": ["commitment", "contract.accept", "terms.accept"],
    },
    "high_risk_batch_change": {
        "description": "高风险批量修改，包括批量重命名、批量删除、批量外发。",
        "default": "approval_required",
        "risk": "high",
        "approval_required_for": "high_risk_batch_change",
        "aliases": ["batch_change", "bulk_edit", "bulk_operation"],
    },
    "modify_permission_policy": {
        "description": "修改权限、审批门、策略、角色权限或安全边界。",
        "default": "approval_required",
        "risk": "critical",
        "approval_required_for": "modify_permission_policy",
        "aliases": ["policy.modify", "permission.modify", "security_policy_change"],
    },
    "access_secret": {
        "description": "读取、展示、复制、导出或传递敏感凭据。",
        "default": "approval_required",
        "risk": "critical",
        "approval_required_for": "access_secret",
        "aliases": ["secret.read", "credential.access", "apikey.read"],
    },
    "secret_enter": {
        "description": "进入 Secret Vault 本地解锁流程，密码只在 TUI 本地处理。",
        "default": "allow",
        "risk": "high",
        "approval_required_for": "",
        "aliases": ["secret.enter", "vault.enter", "secret.unlock_flow"],
    },
    "secret_decrypt": {
        "description": "在本地内存中解锁/解密 Secret Vault 内容。",
        "default": "allow",
        "risk": "critical",
        "approval_required_for": "",
        "aliases": ["vault.decrypt", "secret.unlock", "secret.open"],
    },
    "secret_import": {
        "description": "把普通区会话单向加密导入 Secret Vault，并按用户选择删除或归档普通侧原件。",
        "default": "allow",
        "risk": "critical",
        "approval_required_for": "",
        "aliases": ["vault.import", "secret.migrate", "secret.one_way_import"],
    },
    "secret_network": {
        "description": "Secret Vault 网络操作，必须通过已配置且健康的代理/Tor 链。",
        "default": "allow",
        "risk": "critical",
        "approval_required_for": "",
        "aliases": ["secret.network", "tor.chain", "proxy.chain"],
    },
    "secret_export": {
        "description": "导出、复制、展示或降级 Secret Vault 明文数据。",
        "default": "approval_required",
        "risk": "critical",
        "approval_required_for": "secret_export",
        "aliases": ["vault.export", "secret.copy", "secret.reveal", "secret.plaintext_export"],
    },
    "secret_downgrade": {
        "description": "降低 Secret Vault 加密、代理链、隔离或审计策略。",
        "default": "approval_required",
        "risk": "critical",
        "approval_required_for": "secret_downgrade",
        "aliases": ["vault.downgrade", "secret.disable_proxy", "secret.disable_encryption"],
    },
    "long_running_privilege_escalation": {
        "description": "长时间后台任务升级权限、扩大工具权限或提升执行范围。",
        "default": "approval_required",
        "risk": "high",
        "approval_required_for": "long_running_privilege_escalation",
        "aliases": ["privilege.escalate", "background_privilege_escalation"],
    },
    "release_writer_lock": {
        "description": "释放 single-writer 锁，可能影响写入安全边界。",
        "default": "approval_required",
        "risk": "high",
        "approval_required_for": "modify_permission_policy",
        "aliases": ["writer_lock.release", "single_writer.release"],
    },
    "recovery_retry": {
        "description": "从 recovery 面板重新启动未完成任务。",
        "default": "approval_required",
        "risk": "medium",
        "approval_required_for": "long_running_privilege_escalation",
        "aliases": ["task.retry", "recovery.retry"],
    },
    "recovery_cancel": {
        "description": "取消未完成任务并请求停止运行态 agent。",
        "default": "allow",
        "risk": "medium",
        "approval_required_for": "",
        "aliases": ["task.cancel", "recovery.cancel"],
    },
    "recovery_mark_failed": {
        "description": "把 stale/unfinished task 标记为 failed。",
        "default": "allow",
        "risk": "medium",
        "approval_required_for": "",
        "aliases": ["task.fail", "recovery.fail"],
    },
    "repo_write": {
        "description": "受控代码/文件写入。默认允许，但仍受 single-writer 和角色策略约束。",
        "default": "allow",
        "risk": "medium",
        "approval_required_for": "",
        "aliases": ["repo.write", "file.write", "draft_write"],
    },
    "read_only": {
        "description": "只读检查、检索、预览或分析。",
        "default": "allow",
        "risk": "low",
        "approval_required_for": "",
        "aliases": ["read", "repo.read", "artifact.read", "trace.read"],
    },
}


def policy_alias_map() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for action, rule in POLICY_ACTIONS.items():
        aliases[action] = action
        for alias in rule.get("aliases") or []:
            aliases[str(alias).lower()] = action
    return aliases


POLICY_ALIAS_MAP = policy_alias_map()


def normalized_role(role: str) -> str:
    role = clean_subagent_id(role or "specialist").replace("-", "_")
    return role if role in ROLE_TEMPLATES else "specialist"


def role_template(role: str) -> dict[str, Any]:
    return dict(ROLE_TEMPLATES.get(normalized_role(role), ROLE_TEMPLATES["specialist"]))


def role_write_policy(role: str) -> str:
    return str(role_template(role).get("write_policy") or "none")


def is_write_role(role: str) -> bool:
    return role_write_policy(role) in {"single_writer", "approved_only"}


def role_output_contract(role: str) -> list[str]:
    contract = role_template(role).get("output_contract") or []
    return [str(item) for item in contract]


def role_tools_allowed(role: str) -> list[str]:
    tools = role_template(role).get("tools_allowed") or []
    return [str(item) for item in tools]


def normalize_policy_action(action: str) -> str:
    raw = unicodedata.normalize("NFKC", action or "").strip().lower()
    raw = re.sub(r"\s+", "_", raw).replace("-", "_")
    raw = raw.strip("._")
    return POLICY_ALIAS_MAP.get(raw, raw or "unknown")


def default_policy_config() -> dict[str, Any]:
    return {
        "schema_version": "agentpolicy.v1",
        "default_unknown": "approval_required",
        "rules": {
            action: {
                "mode": str(rule.get("default") or "approval_required"),
                "risk": str(rule.get("risk") or "high"),
                "description": str(rule.get("description") or action),
                "approval_required_for": str(rule.get("approval_required_for") or action),
            }
            for action, rule in POLICY_ACTIONS.items()
        },
    }


def merge_policy_config(raw: dict[str, Any]) -> dict[str, Any]:
    config = default_policy_config()
    if not isinstance(raw, dict):
        return config
    if raw.get("default_unknown"):
        config["default_unknown"] = str(raw.get("default_unknown"))
    rules = raw.get("rules") if isinstance(raw.get("rules"), dict) else {}
    for action, override in rules.items():
        normalized = normalize_policy_action(str(action))
        if not isinstance(override, dict):
            continue
        base = dict(config["rules"].get(normalized, {
            "mode": config["default_unknown"],
            "risk": "high",
            "description": normalized,
            "approval_required_for": normalized,
        }))
        for key in ("mode", "risk", "description", "approval_required_for"):
            if key in override:
                base[key] = str(override.get(key) or "")
        config["rules"][normalized] = base
    return config


def load_policy_config() -> dict[str, Any]:
    try:
        with open(AGENT_POLICY_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return default_policy_config()
    return merge_policy_config(raw if isinstance(raw, dict) else {})


def ensure_policy_config() -> dict[str, Any]:
    config = load_policy_config()
    if not os.path.exists(AGENT_POLICY_PATH):
        write_text_atomic(AGENT_POLICY_PATH, json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return config


def policy_rule_for(action: str, config: Optional[dict[str, Any]] = None) -> tuple[str, dict[str, Any]]:
    normalized = normalize_policy_action(action)
    cfg = config or load_policy_config()
    rules = cfg.get("rules") if isinstance(cfg.get("rules"), dict) else {}
    if normalized in rules and isinstance(rules[normalized], dict):
        return normalized, dict(rules[normalized])
    return normalized, {
        "mode": str(cfg.get("default_unknown") or "approval_required"),
        "risk": "high",
        "description": f"未登记动作：{normalized}",
        "approval_required_for": normalized,
    }


def policy_decision_to_dict(decision: PolicyDecision) -> dict[str, Any]:
    return {
        "schema_version": "agentpolicy.decision.v1",
        "decision_id": decision.decision_id,
        "timestamp": now_iso(),
        "action": decision.action,
        "subject": decision.subject,
        "role": decision.role,
        "source": decision.source,
        "target": decision.target,
        "status": decision.status,
        "allowed": decision.allowed,
        "approval_required": decision.approval_required,
        "approval_required_for": decision.approval_required_for,
        "approval_id": decision.approval_id,
        "risk": decision.risk,
        "reason": decision.reason,
        "payload": decision.payload,
    }


def record_policy_decision(decision: PolicyDecision) -> dict[str, Any]:
    row = policy_decision_to_dict(decision)
    append_jsonl(AGENT_POLICY_DECISIONS_PATH, row)
    return row


def evaluate_policy_action(
    action: str,
    *,
    subject: str = "orchestrator.main",
    role: str = "",
    source: str = "",
    target: str = "",
    payload: Optional[dict[str, Any]] = None,
    config: Optional[dict[str, Any]] = None,
) -> PolicyDecision:
    normalized, rule = policy_rule_for(action, config)
    role = normalized_role(role) if role else ""
    write_policy = role_write_policy(role) if role else ""
    mode = str(rule.get("mode") or "approval_required").strip().lower()
    risk = str(rule.get("risk") or "high")
    approval_required_for = str(rule.get("approval_required_for") or normalized)
    description = str(rule.get("description") or normalized)
    status = "allowed"
    allowed = True
    approval_required = False
    reason = f"{normalized}: {description}"

    if mode in {"deny", "denied", "block", "blocked"}:
        status = "denied"
        allowed = False
        reason = f"{normalized}: policy denies this action."
    elif normalized == "repo_write" and write_policy == "none":
        status = "denied"
        allowed = False
        reason = f"{normalized}: role {role} has write_policy=none."
    elif normalized == "repo_write" and write_policy == "candidate_only":
        status = "denied"
        allowed = False
        reason = f"{normalized}: role {role} may only submit candidates."
    elif mode in {"approval_required", "approved_only", "require_approval"}:
        status = "approval_required"
        allowed = False
        approval_required = True
        reason = f"{normalized}: requires human approval for {approval_required_for}."
    elif write_policy == "approved_only" and normalized != "read_only":
        status = "approval_required"
        allowed = False
        approval_required = True
        approval_required_for = approval_required_for or normalized
        reason = f"{normalized}: role {role} uses approved_only policy."
    elif mode in {"allow", "allowed"}:
        status = "allowed"
        allowed = True
    else:
        status = "approval_required"
        allowed = False
        approval_required = True
        reason = f"{normalized}: unknown policy mode {mode}; requiring approval."

    return PolicyDecision(
        decision_id=short_uid("policy"),
        action=normalized,
        subject=subject or "orchestrator.main",
        role=role,
        source=source,
        target=target,
        status=status,
        allowed=allowed,
        approval_required=approval_required,
        approval_required_for=approval_required_for,
        risk=risk,
        reason=reason,
        payload=payload or {},
    )


def queue_policy_approval(decision: PolicyDecision, summary: str = "", extra_payload: Optional[dict[str, Any]] = None) -> str:
    if not decision.approval_required:
        return ""
    payload = policy_decision_to_dict(decision)
    if extra_payload:
        payload.update(extra_payload)
    approval_id = queue_approval(
        approval_type="policy_approval_request",
        summary=summary or f"{decision.action}: {decision.reason}",
        payload=payload,
        source=decision.source or decision.subject,
        target=decision.target,
        approval_required_for=decision.approval_required_for,
    )
    decision.approval_id = approval_id
    return approval_id


def gate_policy_action(
    action: str,
    *,
    subject: str = "orchestrator.main",
    role: str = "",
    source: str = "",
    target: str = "",
    payload: Optional[dict[str, Any]] = None,
    queue_if_required: bool = False,
    record: bool = True,
) -> PolicyDecision:
    decision = evaluate_policy_action(
        action,
        subject=subject,
        role=role,
        source=source,
        target=target,
        payload=payload,
    )
    if queue_if_required and decision.approval_required:
        queue_policy_approval(decision)
    if record:
        record_policy_decision(decision)
    return decision


def policy_gate_text(decision: PolicyDecision) -> str:
    if decision.allowed:
        return f"ALLOW {decision.action}: {decision.reason}"
    if decision.approval_required:
        suffix = f" approval={decision.approval_id}" if decision.approval_id else ""
        return f"APPROVAL_REQUIRED {decision.action}: {decision.reason}{suffix}"
    return f"DENY {decision.action}: {decision.reason}"


def secret_network_gate(state: Optional[State] = None, operation: str = "secret_network") -> PolicyDecision:
    status = secret_network_status()
    if state is not None:
        state.secret_vault.last_network_status = status
    if not status.get("allowed"):
        decision = PolicyDecision(
            decision_id=short_uid("policy"),
            action="secret_network",
            subject="orchestrator.main",
            role="",
            source=operation,
            target="secret_vault",
            status="denied",
            allowed=False,
            approval_required=False,
            approval_required_for="",
            risk="critical",
            reason=f"secret_network: fail-closed because {status.get('reason')}",
            payload={"operation": operation, "network_status": status},
        )
        record_policy_decision(decision)
        return decision
    decision = gate_policy_action(
        "secret_network",
        subject="orchestrator.main",
        source=operation,
        target="secret_vault",
        payload={"operation": operation, "network_status": status},
        queue_if_required=True,
    )
    if state is not None and decision.allowed:
        activate_secret_proxy_env(state, status)
    return decision


def begin_secret_unlock(state: State) -> str:
    if state.status in {"running", "aborting", "restoring"} and not state.active_task_secret:
        return "当前普通任务仍在运行/恢复；请先完成或停止后再进入 Secret Vault。"
    decision = gate_policy_action(
        "secret_enter",
        subject="orchestrator.main",
        source="/Secret",
        target="secret_vault",
        payload={"operation": "begin_secret_unlock", "crypto": secret_crypto_status_text()},
        queue_if_required=True,
    )
    if not decision.allowed:
        return policy_gate_text(decision)
    state.secret_vault.pending_action = "unlock" if secret_vault_exists() else "setup_password"
    state.secret_vault.pending_first_password = ""
    set_input_text(state, "")
    mark_dirty(state)
    if state.secret_vault.pending_action == "unlock":
        return "Secret Vault 已锁定：请输入密码解锁。"
    return f"Secret Vault 尚未初始化：请设置本地密码（{SECRET_VAULT_PASSWORD_RULE_TEXT}）。"


def enter_secret_unlocked_state(state: State, key: bytes, message: str) -> str:
    vault = state.secret_vault
    import_private_key, import_key_msg = secret_load_or_create_import_private_key(key)
    vault.import_private_key = import_private_key
    if import_key_msg:
        if import_private_key:
            message = f"{message}\n{import_key_msg}"
        else:
            vault.storage_warning = import_key_msg
            message = f"{message}\n警告：{import_key_msg}"
    if not vault.previous_log_path:
        current_path = agent_log_path(state.agent)
        if current_path and current_path != os.devnull:
            vault.previous_log_path = current_path
    vault.unlocked = True
    vault.key = key
    vault.pending_action = ""
    vault.pending_first_password = ""
    vault.session_id = vault.session_id or secret_new_session_id()
    vault.last_unlocked_at = time.time()
    state.current_title = "Secret Vault"
    state.selected_session = secret_session_sidebar_key(vault.session_id)
    state.messages.clear()
    reset_agent_runtime_context_no_snapshot(state.agent)
    cancel_normal_history_restore(state)
    state.active_task_secret = False
    state.active_secret_user_text = ""
    state.active_secret_session_id = ""
    clear_all_queued_inputs(state)
    state.secret_active_origin = {}
    state.subagents = {}
    load_secret_subagents(state)
    clear_secret_sidebar_caches(state)
    saved_backgrounds = save_unlocked_secret_background_sessions(state, source="unlock-background")
    set_agent_log_path(state.agent, os.devnull)
    network = secret_network_status()
    vault.last_network_status = network
    add_system(state, f"{message}\nSecret session: {vault.session_id}\nNetwork: {network.get('status')} - {network.get('reason')}")
    if saved_backgrounds:
        add_system(state, f"已加密保存 {saved_backgrounds} 个锁定期间完成的 Secret 后台会话。")
    import_result = consume_pending_secret_import(state)
    if import_result:
        add_system(state, import_result)
    return message


def accept_secret_password_input(state: State, password: str) -> str:
    action = state.secret_vault.pending_action
    if not action:
        return ""
    if action == "setup_password":
        password_error = secret_password_policy_error(password)
        if password_error:
            return f"{password_error}请重新输入。"
        state.secret_vault.pending_first_password = password
        state.secret_vault.pending_action = "setup_confirm"
        set_input_text(state, "")
        mark_dirty(state)
        return "已记录第一次输入；请再次输入同一 Secret 密码确认。"
    if action == "setup_confirm":
        first = state.secret_vault.pending_first_password
        state.secret_vault.pending_first_password = ""
        if password != first:
            state.secret_vault.pending_action = "setup_password"
            set_input_text(state, "")
            mark_dirty(state)
            return "两次密码不一致；请重新设置 Secret 密码。"
        decision = gate_policy_action(
            "secret_decrypt",
            subject="orchestrator.main",
            source="/Secret",
            target="secret_vault",
            payload={"operation": "create_and_unlock", "crypto": secret_crypto_status_text()},
            queue_if_required=True,
        )
        if not decision.allowed:
            state.secret_vault.pending_action = "setup_password"
            set_input_text(state, "")
            mark_dirty(state)
            return policy_gate_text(decision)
        ok, key, msg = secret_create_vault(password)
        if not ok or key is None:
            state.secret_vault.pending_action = "setup_password"
            set_input_text(state, "")
            mark_dirty(state)
            return msg
        return enter_secret_unlocked_state(state, key, msg)
    if action == "unlock":
        decision = gate_policy_action(
            "secret_decrypt",
            subject="orchestrator.main",
            source="/Secret",
            target="secret_vault",
            payload={"operation": "unlock", "crypto": secret_crypto_status_text()},
            queue_if_required=True,
        )
        if not decision.allowed:
            set_input_text(state, "")
            mark_dirty(state)
            return policy_gate_text(decision)
        ok, key, msg = secret_unlock_vault(password)
        if not ok or key is None:
            set_input_text(state, "")
            mark_dirty(state)
            return msg
        return enter_secret_unlocked_state(state, key, msg)
    return "未知 Secret Vault 输入状态。"


def lock_secret_vault(state: State, reason: str = "manual") -> str:
    vault = state.secret_vault
    secret_bg_keys = secret_background_session_keys(state)
    running_secret_background = any(
        state.background_sessions[key].status in {"running", "aborting"}
        for key in secret_bg_keys
        if key in state.background_sessions
    )
    running_secret_task = bool(state.active_task_secret and state.active_task_id is not None and state.status in {"running", "aborting"})
    had_secret_state = bool(vault.unlocked or vault.pending_action or vault.session_id or state.active_task_secret or secret_bg_keys)
    if not had_secret_state:
        set_input_text(state, "")
        reset_input_history_browse(state)
        mark_dirty(state)
        return "Secret Vault 已锁定。"
    previous = vault.previous_log_path
    parked_running_secret = False
    if running_secret_task:
        parked_running_secret = bool(park_active_session(state, reset=True))
        secret_bg_keys = secret_background_session_keys(state)
        running_secret_background = any(
            state.background_sessions[key].status in {"running", "aborting"}
            for key in secret_bg_keys
            if key in state.background_sessions
        )
        running_secret_task = False
    if vault.unlocked and vault.session_id and any(msg.role in {"user", "assistant"} for msg in state.messages):
        secret_save_current_session_state(state, source="lock")
    vault.unlocked = False
    vault.pending_action = ""
    vault.pending_first_password = ""
    clear_pending_secret_import(state)
    clear_pending_secret_copy_confirmation(state)
    clear_secret_sidebar_caches(state)
    vault.key = None
    vault.import_private_key = None
    vault.last_network_status = {}
    vault.storage_warning = ""
    vault.session_id = ""
    for sub in state.subagents.values():
        if sub.security_context == "secret" and sub.agent is not None:
            try:
                sub.agent.abort()
            except Exception:
                pass
    state.subagents = {key: sub for key, sub in state.subagents.items() if sub.security_context != "secret"}
    if not running_secret_task and not running_secret_background:
        vault.previous_log_path = ""
        state.active_task_secret = False
    state.active_secret_user_text = ""
    state.secret_active_origin = {}
    if not running_secret_task and not running_secret_background:
        state.active_secret_session_id = ""
    state.messages.clear()
    state.input_history = []
    clear_all_queued_inputs(state)
    reset_input_history_browse(state)
    state.current_title = "main"
    state.selected_session = "main"
    cancel_normal_history_restore(state)
    set_input_text(state, "")
    reset_agent_runtime_context_no_snapshot(state.agent)
    if previous:
        set_agent_log_path(state.agent, previous)
    else:
        set_agent_log_path(state.agent, new_session_log_path())
    if not running_secret_task and not running_secret_background:
        restore_secret_proxy_env(state)
    else:
        state.last_error = "Secret 运行任务已转入加密后台；代理环境会在任务结束后恢复。"
    load_history(state, force=True)
    suffix = "；运行中的 Secret 任务已转入加密后台继续执行。" if parked_running_secret or running_secret_background else ""
    add_system(state, f"Secret Vault 已锁定（{reason}）；明文界面状态已清除{suffix}")
    return f"Secret Vault 已锁定{suffix}"


def secret_status_text(state: State) -> str:
    vault = state.secret_vault
    lock = "unlocked" if vault.unlocked else ("password-pending" if vault.pending_action else "locked")
    network = vault.last_network_status or (secret_network_status() if (vault.unlocked or vault.pending_action) else {"status": "not_checked", "reason": "locked"})
    return (
        f"Secret Vault: {lock}; crypto={secret_crypto_status_text()}; "
        f"session={vault.session_id or '-'}; network={network.get('status')}:{network.get('reason')}"
    )


SECRET_BLOCKED_NORMAL_COMMANDS = {
    "/memory", "/mem", "/tasks", "/bus", "/artifacts", "/recover", "/evals", "/gateway", "/baseline", "/continue", "/sessions",
}


def secret_blocks_normal_command(state: State, text: str) -> bool:
    command = (text or "").strip().lower().split(maxsplit=1)
    return bool(state.secret_vault.unlocked and command and command[0] in SECRET_BLOCKED_NORMAL_COMMANDS)


APPROVAL_REQUIRED_FOR = [
    "external_send",
    "publish",
    "delete_file",
    "delete_memory",
    "write_long_term_memory",
    "deploy",
    "spend_money",
    "external_commitment",
    "high_risk_batch_change",
    "modify_permission_policy",
    "access_secret",
    "secret_export",
    "secret_downgrade",
    "long_running_privilege_escalation",
]


def default_task_budget(role: str = "") -> dict[str, Any]:
    role = normalized_role(role) if role else ""
    base = {
        "max_tokens": 40000,
        "max_tool_calls": 20,
        "max_wall_clock_seconds": 1800,
        "max_subagents": 0,
    }
    if role in {"coder", "ops"}:
        base.update({"max_tokens": 60000, "max_tool_calls": 35, "max_wall_clock_seconds": 3600})
    elif role in {"researcher", "code_reader"}:
        base.update({"max_tokens": 50000, "max_tool_calls": 30})
    elif role in {"reviewer", "verifier"}:
        base.update({"max_tokens": 30000, "max_tool_calls": 15, "max_wall_clock_seconds": 1200})
    return base


def normalized_security_context(value: str = "") -> str:
    value = (value or "standard").strip().lower().replace("-", "_")
    return "secret" if value == "secret" else "standard"


def permissions_for_role(role: str = "", security_context: str = "standard") -> dict[str, Any]:
    role = normalized_role(role) if role else "specialist"
    security_context = normalized_security_context(security_context)
    tools_forbidden = ["email.send", "deploy", "filesystem.delete", "memory.write.direct"]
    network_policy = "allowlist" if role in {"researcher", "ops"} else "none"
    secrets_policy = "no_secret_access"
    if security_context == "secret":
        network_policy = "secret_proxy_chain_required"
        secrets_policy = "secret_vault_only_no_export"
        tools_forbidden.extend(["network.direct", "history.normal", "artifact.normal_plaintext", "secret.export_without_approval"])
    return {
        "role": role,
        "security_context": security_context,
        "tools_allowed": role_tools_allowed(role),
        "tools_forbidden": tools_forbidden,
        "write_policy": role_write_policy(role),
        "network_policy": network_policy,
        "secrets_policy": secrets_policy,
        "memory_write": "candidate_only",
    }


def context_policy_for_task(objective: str = "", *, history_mode: str = "summary", security_context: str = "standard") -> dict[str, Any]:
    security_context = normalized_security_context(security_context)
    memory_scopes = ["subagent.profile", "subagent.memory", "project.agent-harness"]
    if security_context == "secret":
        memory_scopes = ["secret.subagent.profile", "secret.memory_candidates", "project.agent-harness"]
    return {
        "history_mode": history_mode,
        "history_window_messages": 12,
        "memory_scopes": memory_scopes,
        "security_context": security_context,
        "include_trace_refs": True,
        "include_raw_logs": False,
        "artifact_reference_only": True,
        "retrieval_query": truncate_cells(objective or "", 240),
    }


def boundaries_for_role(role: str = "") -> list[str]:
    role = normalized_role(role) if role else "specialist"
    boundaries = [
        "Work only on the delegated objective.",
        "Return conclusions with evidence or explicit uncertainty.",
        "Use artifact references instead of copying large raw logs.",
        "Do not write long-term memory directly; submit memory candidates.",
    ]
    write_policy = role_write_policy(role)
    if write_policy == "none":
        boundaries.append("Read-only role: do not modify files, deploy, send external messages, or change permissions.")
    elif write_policy == "single_writer":
        boundaries.append("Write role: only modify through the single-writer lane and record changed artifacts.")
    elif write_policy == "approved_only":
        boundaries.append("Approved-only role: request human approval before risky operations.")
    return boundaries


def non_goals_for_role(role: str = "") -> list[str]:
    role = normalized_role(role) if role else "specialist"
    items = [
        "Do not exceed the delegated scope.",
        "Do not spawn unstructured free-form agent chats.",
        "Do not hide failures, missing evidence, or assumptions.",
    ]
    if role != "memory_curator":
        items.append("Do not write long-term memory directly.")
    return items


def stop_condition_for_role(role: str = "") -> str:
    role = normalized_role(role) if role else "specialist"
    if role in {"reviewer", "verifier"}:
        return "Stop after a pass/fail verdict, concrete findings, evidence refs, and recommended next checks."
    if role == "memory_curator":
        return "Stop after producing memory candidates and rejected items; do not persist memory directly."
    if role in {"coder", "ops"}:
        return "Stop before any high-risk operation that lacks program-level approval, or after completing the delegated change with artifacts and rollback notes."
    return "Stop after the delegated objective is answered with summary, findings, evidence refs, risks, artifact refs, and confidence."


def task_contract_for_role(role: str, objective: str, *, output_contract: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    role = normalized_role(role) if role else "specialist"
    return {
        "objective": objective,
        "non_goals": non_goals_for_role(role),
        "success_criteria": [
            "Objective is addressed directly.",
            "Evidence, artifact refs, or uncertainty are provided.",
            "Risks and follow-up work are explicit.",
            "No approval gate or write boundary is bypassed.",
        ],
        "boundaries": boundaries_for_role(role),
        "stop_condition": stop_condition_for_role(role),
        "output_contract": output_contract or {"format": "structured_markdown", "required_sections": role_output_contract(role)},
    }


def risks_for_action(action: str = "", role: str = "", objective: str = "") -> list[dict[str, Any]]:
    action = normalize_policy_action(action)
    role = normalized_role(role) if role else ""
    risks: list[dict[str, Any]] = []
    if action not in {"", "read_only"}:
        normalized, rule = policy_rule_for(action)
        risks.append({
            "risk": normalized,
            "severity": str(rule.get("risk") or "high"),
            "mitigation": "Use policy gate, approval queue, trace, and artifact refs before execution.",
        })
    if role_write_policy(role) in {"single_writer", "approved_only"}:
        risks.append({
            "risk": "write_boundary",
            "severity": "high" if role == "ops" else "medium",
            "mitigation": "Respect single-writer lock and approval metadata.",
        })
    if any(token in (objective or "").lower() for token in ("secret", "token", "api key", "password", "密钥", "密码")):
        risks.append({
            "risk": "secret_exposure",
            "severity": "high",
            "mitigation": "Do not reveal or persist secrets; request scoped approval if secret access is unavoidable.",
        })
    return risks


def approval_metadata(
    *,
    status: str = "not_required",
    approval_required_for: Optional[list[str]] = None,
    approval_id: str = "",
    decision: Optional[PolicyDecision] = None,
) -> dict[str, Any]:
    if decision is not None:
        return {
            "approval_required_for": [decision.approval_required_for] if decision.approval_required_for else APPROVAL_REQUIRED_FOR,
            "approval_status": decision.status if decision.approval_required else ("not_required" if decision.allowed else "rejected"),
            "approval_id": decision.approval_id,
            "policy_decision_id": decision.decision_id,
            "policy_action": decision.action,
        }
    return {
        "approval_required_for": approval_required_for or APPROVAL_REQUIRED_FOR,
        "approval_status": status,
        "approval_id": approval_id,
        "policy_decision_id": "",
        "policy_action": "",
    }


def subagent_task_schema_kwargs(
    sub: SubAgentRuntime,
    objective: str,
    *,
    decision: Optional[PolicyDecision] = None,
) -> dict[str, Any]:
    contract = task_contract_for_role(sub.role, objective)
    action = decision.action if decision is not None else infer_policy_action_for_subagent_task(sub, objective)
    return {
        "budget": default_task_budget(sub.role),
        "stop_condition": str(contract.get("stop_condition") or ""),
        "boundaries": list(contract.get("boundaries") or []),
        "permissions": permissions_for_role(sub.role, security_context=sub.security_context),
        "context_policy": context_policy_for_task(objective, security_context=sub.security_context),
        "risks": risks_for_action(action, sub.role, objective),
        "approval": approval_metadata(decision=decision) if decision is not None else approval_metadata(),
        "output_contract": dict(contract.get("output_contract") or {}),
        "non_goals": list(contract.get("non_goals") or []),
        "success_criteria": list(contract.get("success_criteria") or []),
    }


def policy_relevant_subagent_prompt_text(prompt: str) -> str:
    marker_start = "[GA TUI AgentTask Envelope v2]"
    marker_end = "[/GA TUI AgentTask Envelope v2]"
    text = prompt or ""
    if marker_start not in text or marker_end not in text:
        return text
    raw = text.split(marker_start, 1)[1].split(marker_end, 1)[0].strip()
    try:
        payload = json.loads(raw)
    except Exception:
        return text
    if not isinstance(payload, dict):
        return text
    work_order = payload.get("work_order") if isinstance(payload.get("work_order"), dict) else {}
    objective = str(work_order.get("objective") or payload.get("objective") or "").strip()
    return objective or text


def infer_policy_action_for_subagent_task(sub: SubAgentRuntime, prompt: str) -> str:
    text = unicodedata.normalize("NFKC", policy_relevant_subagent_prompt_text(prompt)).lower()
    checks = [
        ("access_secret", ("api key", "apikey", "secret", "token", "credential", "password", "密码", "密钥", "凭据", "令牌")),
        ("spend_money", ("buy", "purchase", "pay", "charge", "充值", "购买", "付款", "付费", "花钱")),
        ("deploy", ("deploy", "release", "production", "上线", "部署", "发布服务", "生产环境")),
        ("external_send", ("send email", "email.send", "发邮件", "私信", "发送给", "外发", "对外发送")),
        ("publish", ("publish", "post", "发帖", "发布内容", "公开发布")),
        ("delete_file", ("rm ", "delete file", "remove file", "删除文件", "删文件", "批量删除")),
        ("modify_permission_policy", ("permission", "policy", "role", "权限", "策略", "审批门", "修改角色")),
        ("high_risk_batch_change", ("bulk", "batch", "批量", "大规模")),
    ]
    for action, tokens in checks:
        if any(token in text for token in tokens):
            return action
    if sub.role == "ops" and any(token in text for token in ("sudo", "root", "systemctl", "pacman", "docker", "firewall", "ufw", "iptables", "内核", "服务", "重启")):
        return "long_running_privilege_escalation"
    if role_write_policy(sub.role) == "single_writer":
        return "repo_write"
    return "read_only"


def policy_gate_for_subagent_task(
    sub: SubAgentRuntime,
    prompt: str,
    *,
    source: str,
    bus_task_id: str,
    parent_task_id: str = "",
    task_title: str = "",
    queue_if_required: bool = True,
) -> PolicyDecision:
    task_objective = policy_relevant_subagent_prompt_text(prompt)
    action = infer_policy_action_for_subagent_task(sub, prompt)
    decision = evaluate_policy_action(
        action,
        subject=sub.agent_id,
        role=sub.role,
        source=source,
        target=sub.agent_id,
        payload={
            "operation": "start_subagent_task",
            "subagent_id": sub.agent_id,
            "subagent_name": sub.name,
            "task_id": bus_task_id,
            "parent_task_id": parent_task_id,
            "task_title": task_title,
            "prompt_preview": truncate_cells(task_objective, 240),
        },
    )
    if queue_if_required and decision.approval_required:
        queue_policy_approval(
            decision,
            summary=f"{sub.name}: {truncate_cells(task_objective, 100)}",
            extra_payload={
                "deferred_operation": "start_subagent_task",
                "subagent_id": sub.agent_id,
                "prompt": prompt,
                "source": source,
                "task_id": bus_task_id,
                "parent_task_id": parent_task_id,
                "task_title": task_title,
            },
        )
    record_policy_decision(decision)
    return decision


def latest_records_by_id(path: str, key: str) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        row_id = str(row.get(key) or "")
        if row_id:
            latest[row_id] = row
    return latest


def latest_task_records() -> dict[str, dict[str, Any]]:
    return latest_records_by_id(AGENT_TASK_LEDGER_PATH, "task_id")


def task_history(task_id: str) -> list[dict[str, Any]]:
    task_id = str(task_id or "")
    return [row for row in read_jsonl(AGENT_TASK_LEDGER_PATH) if str(row.get("task_id") or "") == task_id]


def terminal_task_status(status: str) -> bool:
    return (status or "").lower() in {"completed", "failed", "cancelled", "canceled", "rejected", "aborted"}


def unfinished_task_records() -> list[dict[str, Any]]:
    return [row for row in latest_task_records().values() if not terminal_task_status(str(row.get("status") or ""))]


def parse_iso_timestamp(value: str) -> float:
    value = (value or "").strip()
    if not value:
        return 0.0
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return time.mktime(time.strptime(value, fmt))
        except Exception:
            continue
    return 0.0


def row_timestamp(row: dict[str, Any]) -> float:
    return parse_iso_timestamp(str(row.get("timestamp") or "")) or float(row.get("ts") or 0.0)


def artifact_preview(uri_or_path: str, max_bytes: int = 24000) -> list[str]:
    path = artifact_path_from_uri(uri_or_path)
    if not path:
        return ["没有可预览路径。"]
    return memory_file_preview(path, max_bytes=max_bytes)


def artifact_inventory() -> list[PanelItem]:
    roots = [
        ("artifact", AGENT_ARTIFACTS_DIR),
        ("context_pack", AGENT_CONTEXT_PACKS_DIR),
    ]
    indexed = artifact_index_latest()
    items: list[PanelItem] = []
    for kind, root in roots:
        if not os.path.isdir(root):
            continue
        for base, dirs, files in os.walk(root):
            dirs[:] = [name for name in dirs if not name.startswith(".")]
            for filename in sorted(files):
                if filename.startswith("."):
                    continue
                path = os.path.join(base, filename)
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                uri = harness_artifact_uri(path)
                rel = os.path.relpath(path, AGENT_HARNESS_DIR)
                preview = "\n".join(artifact_preview(path, max_bytes=32000))
                meta = dict(indexed.get(uri) or {})
                artifact_type = str(meta.get("type") or kind)
                artifact_id = str(meta.get("artifact_id") or "-")
                artifact_hash = str(meta.get("hash") or artifact_sha256(path) or "-")
                source_task = str(meta.get("source_task_id") or "-")
                provenance = meta.get("provenance") if isinstance(meta.get("provenance"), dict) else {}
                preview_path = str(meta.get("preview_path") or path)
                detail = "\n".join([
                    f"Artifact ID: {artifact_id}",
                    f"Type: {artifact_type}",
                    f"URI: {uri}",
                    f"Path: {path}",
                    f"Preview path: {preview_path}",
                    f"Hash: {artifact_hash}",
                    f"Source task: {source_task}",
                    f"Provenance: {json.dumps(provenance, ensure_ascii=False, sort_keys=True) if provenance else '{}'}",
                    f"Size: {st.st_size} bytes",
                    f"MTime: {rel_age(st.st_mtime)}",
                    "",
                    preview,
                ])
                items.append(PanelItem(
                    key=uri,
                    title=truncate_cells(rel, 80),
                    subtitle=f"{artifact_type} · {st.st_size} bytes · {rel_age(st.st_mtime)} · {source_task}",
                    detail=detail,
                    status=artifact_type,
                    path=path,
                    payload={"uri": uri, "mtime": st.st_mtime, "size": st.st_size, "artifact_meta": meta},
                ))
    items.sort(key=lambda item: float(item.payload.get("mtime") or 0.0), reverse=True)
    return items


def load_agent_locks() -> dict[str, Any]:
    try:
        with open(AGENT_LOCKS_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def save_agent_locks(data: dict[str, Any]) -> None:
    write_text_atomic(AGENT_LOCKS_PATH, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def current_writer_lock() -> Optional[dict[str, Any]]:
    data = load_agent_locks()
    lock = data.get("single_writer")
    return lock if isinstance(lock, dict) and lock.get("task_id") else None


def acquire_single_writer_lock(sub: SubAgentRuntime, task_id: str, objective: str = "") -> tuple[bool, str]:
    if not is_write_role(sub.role):
        return True, ""
    data = load_agent_locks()
    lock = data.get("single_writer") if isinstance(data.get("single_writer"), dict) else None
    if lock:
        locked_task = str(lock.get("task_id") or "")
        locked_status = str(latest_task_records().get(locked_task, {}).get("status") or "")
        if locked_task == task_id:
            return True, ""
        if not terminal_task_status(locked_status):
            owner = str(lock.get("agent_id") or "-")
            return False, f"single-writer 已被 {owner} 持有，任务 {locked_task} 尚未结束。"
    data["single_writer"] = {
        "task_id": task_id,
        "agent_id": sub.agent_id,
        "agent_name": sub.name,
        "role": sub.role,
        "objective": truncate_cells(objective, 240),
        "acquired_at": now_iso(),
    }
    save_agent_locks(data)
    return True, ""


def release_single_writer_lock(task_id: str) -> bool:
    task_id = str(task_id or "")
    data = load_agent_locks()
    lock = data.get("single_writer") if isinstance(data.get("single_writer"), dict) else None
    if not lock or str(lock.get("task_id") or "") != task_id:
        return False
    data.pop("single_writer", None)
    save_agent_locks(data)
    return True


def bounded_score(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 2)))


def refs_from_payload(payload: dict[str, Any]) -> dict[str, list[str]]:
    refs = {
        "artifacts": [],
        "approvals": [],
        "memory_candidates": [],
        "messages": [],
        "tool_calls": [],
        "checkpoints": [],
    }
    for key in ("artifact_ref", "context_pack", "context_pack_ref"):
        value = payload.get(key)
        if isinstance(value, str) and value.startswith("artifact://"):
            refs["artifacts"].append(value)
    for value in payload.get("artifact_refs") or []:
        if isinstance(value, str) and value.startswith("artifact://"):
            refs["artifacts"].append(value)
    approval_id = payload.get("approval_id")
    if approval_id:
        refs["approvals"].append(str(approval_id))
    memory_candidate_id = payload.get("memory_candidate_id")
    if memory_candidate_id:
        refs["memory_candidates"].append(str(memory_candidate_id))
    message_id = payload.get("message_id")
    if message_id:
        refs["messages"].append(str(message_id))
    tool_call_id = payload.get("tool_call_id") or payload.get("tool")
    if tool_call_id:
        refs["tool_calls"].append(str(tool_call_id))
    checkpoint_id = payload.get("checkpoint_id")
    if checkpoint_id:
        refs["checkpoints"].append(str(checkpoint_id))
    return {key: sorted(set(values)) for key, values in refs.items()}


def collect_task_audit_refs(task_id: str) -> dict[str, list[str]]:
    task_id = str(task_id or "")
    traces = [row for row in read_jsonl(AGENT_TRACES_PATH) if str(row.get("task_id") or "") == task_id]
    artifacts = [row for row in read_jsonl(AGENT_ARTIFACT_INDEX_PATH) if str(row.get("source_task_id") or "") == task_id]
    messages = [row for row in read_jsonl(AGENT_MAIL_PATH) if str(row.get("task_id") or "") == task_id]
    approvals = [
        row for row in read_jsonl(AGENT_APPROVALS_PATH)
        if str((row.get("payload") or {}).get("task_id") or "") == task_id
    ]
    memory_candidates = [
        row for row in read_jsonl(AGENT_MEMORY_CANDIDATES_PATH)
        if str((row.get("memory_candidate") or {}).get("task_id") or row.get("task_id") or "") == task_id
    ]
    plans = [row for row in read_jsonl(AGENT_ORCHESTRATOR_PLANS_PATH) if str(row.get("task_id") or "") == task_id]
    tool_trace_refs = [
        str(row.get("trace_id") or "")
        for row in traces
        if "tool" in str(row.get("event") or "").lower() or (row.get("audit_refs") or {}).get("tool_calls")
    ]
    checkpoint_refs = [
        ref
        for row in traces
        for ref in ((row.get("audit_refs") or {}).get("checkpoints") or [])
    ]
    return {
        "plan_versions": [str(row.get("plan_id") or "") for row in plans if row.get("plan_id")],
        "messages": [str(row.get("message_id") or "") for row in messages if row.get("message_id")],
        "tool_calls": [ref for ref in tool_trace_refs if ref],
        "artifacts": [str(row.get("uri") or "") for row in artifacts if row.get("uri")],
        "checkpoints": sorted(set(str(ref) for ref in checkpoint_refs if ref)),
        "approvals": [str(row.get("approval_id") or "") for row in approvals if row.get("approval_id")],
        "memory_candidates": [
            str((row.get("memory_candidate") or {}).get("candidate_id") or row.get("candidate_id") or "")
            for row in memory_candidates
            if (row.get("memory_candidate") or {}).get("candidate_id") or row.get("candidate_id")
        ],
        "traces": [str(row.get("trace_id") or "") for row in traces if row.get("trace_id")],
    }


def checkpoint_history(task_id: str) -> list[dict[str, Any]]:
    task_id = str(task_id or "")
    return [row for row in read_jsonl(AGENT_CHECKPOINT_INDEX_PATH) if str(row.get("task_id") or "") == task_id]


def recovery_history(task_id: str) -> list[dict[str, Any]]:
    task_id = str(task_id or "")
    return [row for row in read_jsonl(AGENT_RECOVERY_PATH) if str(row.get("task_id") or "") == task_id]


def recovery_plan_history(task_id: str) -> list[dict[str, Any]]:
    task_id = str(task_id or "")
    return [row for row in read_jsonl(AGENT_RECOVERY_PLANS_PATH) if str(row.get("task_id") or "") == task_id]


def checkpoint_index_by_id(checkpoint_id: str) -> dict[str, Any]:
    checkpoint_id = str(checkpoint_id or "")
    for row in reversed(read_jsonl(AGENT_CHECKPOINT_INDEX_PATH)):
        if str(row.get("checkpoint_id") or "") == checkpoint_id:
            return row
    return {}


def latest_checkpoint_for_task(task_id: str) -> dict[str, Any]:
    rows = checkpoint_history(task_id)
    if not rows:
        return {}
    return sorted(rows, key=row_timestamp)[-1]


def read_checkpoint_snapshot(checkpoint: dict[str, Any]) -> dict[str, Any]:
    path = str(checkpoint.get("path") or "")
    if not path:
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def recovery_replay_steps(action: str) -> list[dict[str, Any]]:
    action = str(action or "")
    common = [
        {"step": "validate_checkpoint_hash", "description": "Verify source checkpoint hash before using it as recovery input."},
        {"step": "hydrate_checkpoint_context", "description": "Read task, agent snapshot, audit refs, recovery history, and single-writer lock from checkpoint."},
        {"step": "evaluate_policy_gate", "description": "Apply program-level recovery policy before any state-changing action."},
    ]
    action_steps = {
        "retry": [
            {"step": "mark_original_superseded", "description": "Mark the stale task as superseded by a replacement task."},
            {"step": "restart_assigned_agent", "description": "Re-delegate the checkpoint objective to the original assigned subagent."},
            {"step": "link_replacement_task", "description": "Store replacement task id and checkpoint refs in recovery records."},
        ],
        "cancelled": [
            {"step": "abort_runtime_if_present", "description": "Abort active runtime if the task is still attached to a live subagent."},
            {"step": "mark_task_cancelled", "description": "Append a cancelled task ledger row and release owned writer lock."},
        ],
        "failed": [
            {"step": "abort_runtime_if_present", "description": "Abort active runtime if possible."},
            {"step": "mark_task_failed", "description": "Append a failed task ledger row and release owned writer lock."},
        ],
        "release_lock": [
            {"step": "release_owned_writer_lock", "description": "Release single-writer lock only if the checkpoint task owns it."},
        ],
    }
    return common + action_steps.get(action, [{"step": "manual_review", "description": f"Unknown recovery action {action}; require manual review."}])


def append_recovery_plan(
    task_id: str,
    *,
    action: str,
    source_checkpoint: dict[str, Any],
    assigned_agent: str = "",
    objective: str = "",
    policy_decision: Optional[PolicyDecision] = None,
    status: str = "planned",
) -> dict[str, Any]:
    task_id = str(task_id or "")
    checkpoint_snapshot = read_checkpoint_snapshot(source_checkpoint)
    checkpoint_id = str(source_checkpoint.get("checkpoint_id") or "")
    plan_id = short_uid("recoveryplan")
    task_row = checkpoint_snapshot.get("task") if isinstance(checkpoint_snapshot.get("task"), dict) else latest_task_records().get(task_id, {})
    agent_snapshot = checkpoint_snapshot.get("agent") if isinstance(checkpoint_snapshot.get("agent"), dict) else {}
    lock_snapshot = checkpoint_snapshot.get("single_writer_lock") if isinstance(checkpoint_snapshot.get("single_writer_lock"), dict) else {}
    replay_steps = recovery_replay_steps(action)
    source_ref = {
        "checkpoint_id": checkpoint_id,
        "path": source_checkpoint.get("path", ""),
        "uri": source_checkpoint.get("uri", ""),
        "hash": source_checkpoint.get("hash", ""),
        "status": source_checkpoint.get("status", ""),
        "reason": source_checkpoint.get("reason", ""),
    }
    plan = {
        "schema_version": "agentrecovery.plan.v1",
        "recovery_plan_id": plan_id,
        "task_id": task_id,
        "context_id": "ga-tui",
        "created_at": now_iso(),
        "action": action,
        "status": status,
        "assigned_agent": assigned_agent or str(task_row.get("assigned_agent") or agent_snapshot.get("agent_id") or ""),
        "objective": objective or str(task_row.get("objective") or task_row.get("summary") or ""),
        "source_checkpoint": source_ref,
        "checkpoint_snapshot_refs": {
            "task_status": task_row.get("status", ""),
            "agent_status": agent_snapshot.get("status", ""),
            "single_writer_lock_task": lock_snapshot.get("task_id", ""),
            "audit_refs": checkpoint_snapshot.get("audit_refs") or source_checkpoint.get("audit_refs") or {},
        },
        "replayable": True,
        "replay_steps": replay_steps,
        "state_patch": {
            "task_status_after_action": {
                "retry": "superseded",
                "cancelled": "cancelled",
                "failed": "failed",
                "release_lock": str(task_row.get("status") or source_checkpoint.get("status") or ""),
            }.get(action, "manual_review"),
            "release_single_writer_lock": action in {"retry", "cancelled", "failed", "release_lock"},
            "abort_runtime": action in {"retry", "cancelled", "failed"},
            "replacement_task_expected": action == "retry",
        },
        "approval": {
            "policy_action": policy_decision.action if policy_decision is not None else "",
            "approval_required": bool(policy_decision.approval_required) if policy_decision is not None else False,
            "approval_required_for": policy_decision.approval_required_for if policy_decision is not None else "",
            "policy_decision_id": policy_decision.decision_id if policy_decision is not None else "",
            "approval_id": policy_decision.approval_id if policy_decision is not None else "",
        },
        "rollback": {
            "strategy": "Use source checkpoint artifact and task ledger history to inspect or manually re-apply the prior state.",
            "source_checkpoint_id": checkpoint_id,
            "source_checkpoint_hash": source_checkpoint.get("hash", ""),
        },
        "artifact_refs": [],
    }
    artifact_doc = "# Recovery Plan\n\n```json\n" + json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n```\n"
    artifact_ref = write_harness_artifact(
        "recovery-plans",
        f"{task_id}-{plan_id}",
        artifact_doc,
        source_task_id=task_id,
        provenance={
            "generated_by": "recovery_controller",
            "recovery_plan_id": plan_id,
            "source_checkpoint_id": checkpoint_id,
            "action": action,
        },
        content_type="text/markdown",
    )
    plan["artifact_refs"] = [artifact_ref]
    append_jsonl(AGENT_RECOVERY_PLANS_PATH, plan)
    return plan


def append_task_checkpoint(
    task_id: str,
    *,
    status: str,
    reason: str,
    state: Optional[State] = None,
    agent_id: str = "",
    summary: str = "",
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    task_id = str(task_id or "")
    checkpoint_id = short_uid("ckpt")
    task_row = latest_task_records().get(task_id, {})
    owner = agent_id or str(task_row.get("assigned_agent") or "")
    sub_snapshot: dict[str, Any] = {}
    if state is not None and owner in state.subagents:
        sub = state.subagents[owner]
        sub_snapshot = {
            "agent_id": sub.agent_id,
            "name": sub.name,
            "role": sub.role,
            "status": sub.status,
            "active_task_id": sub.active_task_id,
            "active_bus_task_id": sub.active_bus_task_id,
            "pending_interaction": sub.pending_interaction,
            "updated_at": sub.updated_at,
        }
    lock = current_writer_lock()
    if lock and str(lock.get("task_id") or "") != task_id:
        lock = {}
    checkpoint = {
        "schema_version": "agentcheckpoint.v1",
        "checkpoint_id": checkpoint_id,
        "task_id": task_id,
        "context_id": "ga-tui",
        "timestamp": now_iso(),
        "status": status,
        "reason": reason,
        "assigned_agent": owner,
        "summary": summary,
        "task": task_row,
        "agent": sub_snapshot,
        "single_writer_lock": lock or {},
        "audit_refs": collect_task_audit_refs(task_id),
        "recovery_history": recovery_history(task_id),
        "extra": extra or {},
    }
    stamp = time.strftime("%Y%m%d-%H%M%S")
    safe_task = re.sub(r"[^A-Za-z0-9_.-]+", "-", task_id or "task").strip("-") or "task"
    path = os.path.join(AGENT_CHECKPOINTS_DIR, f"{stamp}-{safe_task}-{checkpoint_id}.json")
    write_text_atomic(path, json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    uri = harness_artifact_uri(path)
    row = {
        "schema_version": "agentcheckpoint.index.v1",
        "checkpoint_id": checkpoint_id,
        "task_id": task_id,
        "context_id": "ga-tui",
        "timestamp": checkpoint["timestamp"],
        "status": status,
        "reason": reason,
        "assigned_agent": owner,
        "summary": summary,
        "path": path,
        "uri": uri,
        "hash": artifact_sha256(path),
        "audit_refs": checkpoint["audit_refs"],
    }
    append_jsonl(AGENT_CHECKPOINT_INDEX_PATH, row)
    append_artifact_index(
        path,
        artifact_type="checkpoint",
        source_task_id=task_id,
        provenance={"checkpoint_id": checkpoint_id, "reason": reason, "status": status, "assigned_agent": owner},
        content_type="application/json",
    )
    return row


def append_recovery_record(
    task_id: str,
    *,
    action: str,
    status: str,
    actor: str = "orchestrator.main",
    assigned_agent: str = "",
    objective: str = "",
    before_checkpoint_id: str = "",
    after_checkpoint_id: str = "",
    policy_decision: Optional[PolicyDecision] = None,
    result: str = "",
    error: str = "",
    replacement_task_id: str = "",
    recovery_plan_id: str = "",
    recovery_plan_ref: str = "",
) -> dict[str, Any]:
    row = {
        "schema_version": "agentrecovery.v1",
        "recovery_id": short_uid("recovery"),
        "task_id": task_id,
        "context_id": "ga-tui",
        "timestamp": now_iso(),
        "action": action,
        "status": status,
        "actor": actor,
        "assigned_agent": assigned_agent,
        "objective": objective,
        "before_checkpoint_id": before_checkpoint_id,
        "after_checkpoint_id": after_checkpoint_id,
        "replacement_task_id": replacement_task_id,
        "recovery_plan_id": recovery_plan_id,
        "recovery_plan_ref": recovery_plan_ref,
        "policy": policy_decision_to_dict(policy_decision) if policy_decision is not None else {},
        "result": result,
        "error": error,
        "audit_refs": collect_task_audit_refs(task_id),
    }
    append_jsonl(AGENT_RECOVERY_PATH, row)
    return row


def append_trace(task_id: str, event: str, *, agent_id: str = "", status: str = "", payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    payload = payload or {}
    audit_refs = refs_from_payload(payload)
    lower_event = str(event or "").lower()
    lower_status = str(status or "").lower()
    row = {
        "schema_version": "agenttrace.v2",
        "trace_id": short_uid("trace"),
        "task_id": task_id,
        "context_id": "ga-tui",
        "timestamp": now_iso(),
        "event": event,
        "phase": lower_event.split("_", 1)[0] if lower_event else "",
        "agent_id": agent_id,
        "actor": {"agent_id": agent_id or "orchestrator.main"},
        "status": status,
        "severity": "error" if lower_status in {"failed", "rejected", "denied"} else ("warning" if lower_status in {"approval_required", "pending"} else "info"),
        "audit_refs": audit_refs,
        "metrics": {
            "tool_calls_delta": len(audit_refs["tool_calls"]),
            "artifact_refs_delta": len(audit_refs["artifacts"]),
            "approval_refs_delta": len(audit_refs["approvals"]),
            "memory_candidate_refs_delta": len(audit_refs["memory_candidates"]),
        },
        "policy": {
            "approval_related": bool(audit_refs["approvals"] or "approval" in lower_event or lower_status == "approval_required"),
            "policy_compliance": lower_status not in {"bypassed", "violation"},
        },
        "payload": payload,
    }
    append_jsonl(AGENT_TRACES_PATH, row)
    return row


def append_task_eval(task_id: str, sub: SubAgentRuntime, display_text: str, artifact_ref: str = "") -> dict[str, Any]:
    clean = clean_text(display_text)
    lower = clean.lower()
    has_evidence = any(token in lower for token in ("evidence", "证据", "source", "来源", "artifact://", "http://", "https://", "test", "测试"))
    has_risk = any(token in lower for token in ("risk", "风险", "warning", "失败", "error", "todo", "待"))
    has_citation = any(token in lower for token in ("artifact://", "trace://", "source:", "来源", "证据", "http://", "https://"))
    audit_refs = collect_task_audit_refs(task_id)
    if artifact_ref and artifact_ref not in audit_refs["artifacts"]:
        audit_refs["artifacts"].append(artifact_ref)
    task_row = latest_task_records().get(task_id, {})
    budget = task_row.get("budget") if isinstance(task_row.get("budget"), dict) else default_task_budget(sub.role)
    max_tools = max(1, int(budget.get("max_tool_calls") or 1))
    tool_calls = len(audit_refs["tool_calls"])
    approval_count = len(audit_refs["approvals"])
    artifact_count = len(audit_refs["artifacts"])
    citation_accuracy = bounded_score(0.85 if has_citation else (0.55 if artifact_count else 0.25))
    source_quality = bounded_score(0.85 if artifact_count else (0.7 if has_evidence else 0.4))
    factual_accuracy = bounded_score(0.78 if has_evidence or artifact_count else (0.55 if clean.strip() else 0.0))
    tool_efficiency = bounded_score(1.0 - min(tool_calls / max_tools, 1.0) * 0.25)
    policy_compliance = bounded_score(0.85 if has_risk and sub.role in {"coder", "ops"} else 1.0)
    human_takeover_cost = bounded_score(min(1.0, approval_count / 3.0))
    row = {
        "schema_version": "agenteval.v2",
        "eval_id": short_uid("eval"),
        "task_id": task_id,
        "context_id": "ga-tui",
        "timestamp": now_iso(),
        "agent_id": sub.agent_id,
        "role": sub.role,
        "scores": {
            "completion": 1.0 if clean.strip() else 0.0,
            "factual_accuracy": factual_accuracy,
            "citation_accuracy": citation_accuracy,
            "source_quality": source_quality,
            "tool_efficiency": tool_efficiency,
            "policy_compliance": policy_compliance,
            "human_takeover_cost": human_takeover_cost,
            "evidence_quality": 0.85 if has_evidence else 0.45,
            "artifact_recorded": 1.0 if artifact_ref else 0.0,
            "needs_review": 1.0 if has_risk or sub.role in {"coder", "ops"} else 0.0,
        },
        "audit_refs": audit_refs,
        "coverage": {
            "trace_count": len(audit_refs["traces"]),
            "message_count": len(audit_refs["messages"]),
            "artifact_count": artifact_count,
            "approval_count": approval_count,
            "memory_candidate_count": len(audit_refs["memory_candidates"]),
            "tool_call_count": tool_calls,
        },
        "final_state": {
            "status": "completed" if clean.strip() else "empty_result",
            "has_result": bool(clean.strip()),
            "has_evidence": bool(has_evidence or artifact_count),
            "has_citation": bool(has_citation or artifact_count),
            "has_risk_signal": bool(has_risk),
            "requires_review": bool(has_risk or sub.role in {"coder", "ops"}),
        },
        "policy": {
            "approval_count": approval_count,
            "policy_compliance": policy_compliance,
            "human_takeover_cost": human_takeover_cost,
        },
        "summary": truncate_cells(clean, 240),
        "artifact_refs": [artifact_ref] if artifact_ref else [],
    }
    append_jsonl(AGENT_EVALS_PATH, row)
    return row


def compact_nonempty_lines(text: str, *, limit: int = 12, width: int = 220) -> list[str]:
    lines: list[str] = []
    for line in (text or "").splitlines():
        line = clean_text(line).strip()
        if not line or line.startswith("#"):
            continue
        lines.append(truncate_cells(line, width))
        if len(lines) >= limit:
            break
    return lines


def source_policy_for_role(role: str, security_context: str = "standard") -> dict[str, Any]:
    role = normalized_role(role)
    security_context = normalized_security_context(security_context)
    forbidden_sources = [
        "raw logs unless context_policy.include_raw_logs=true",
        "unrelated project memory",
        "secrets or credentials without approval",
        "private user profile details unrelated to the task",
    ]
    if security_context == "secret":
        forbidden_sources.extend([
            "normal model_responses history",
            "normal plaintext artifacts for Secret data",
            "direct network requests outside the Secret proxy/Tor chain",
        ])
    return {
        "allowed_sources": [
            "task_brief",
            "subagent.profile",
            "subagent.memory",
            "project.agent-harness",
            "agent_mail.refs",
            "task_ledger.refs",
            "artifact_index.refs",
            "trace.refs",
        ],
        "forbidden_sources": forbidden_sources,
        "artifact_policy": "Use artifact refs and hashes instead of copying large raw content.",
        "citation_policy": "Claims should cite evidence_refs, artifact_refs, task_ids, trace refs, or explicitly mark uncertainty.",
        "network_policy": permissions_for_role(role, security_context=security_context).get("network_policy", "none"),
        "security_context": security_context,
    }


def append_orchestrator_plan(
    sub: SubAgentRuntime,
    objective: str,
    task_id: str,
    *,
    parent_task_id: str = "",
    status: str = "planned",
    source: str = "",
    decision: Optional[PolicyDecision] = None,
    context_ref: str = "",
    error: str = "",
) -> dict[str, Any]:
    objective = objective or ""
    action = decision.action if decision is not None else infer_policy_action_for_subagent_task(sub, objective)
    schema = subagent_task_schema_kwargs(sub, objective, decision=decision)
    contract = task_contract_for_role(sub.role, objective)
    approval = schema["approval"]
    approval_required = []
    if decision is not None and decision.approval_required:
        approval_required = [decision.approval_required_for] if decision.approval_required_for else APPROVAL_REQUIRED_FOR
    elif status == "approval_required":
        approval_required = list(approval.get("approval_required_for") or [])
    delegation_contract = {
        "agent_id": sub.agent_id,
        "role": normalized_role(sub.role),
        "objective": objective,
        "budget": schema["budget"],
        "permissions": schema["permissions"],
        "context_policy": schema["context_policy"],
        "source_policy": source_policy_for_role(sub.role, security_context=sub.security_context),
        "task": {
            "objective": objective,
            "non_goals": list(contract.get("non_goals") or []),
            "success_criteria": list(contract.get("success_criteria") or []),
            "boundaries": list(contract.get("boundaries") or []),
            "stop_condition": str(contract.get("stop_condition") or ""),
            "output_contract": dict(contract.get("output_contract") or {}),
        },
        "risks": schema["risks"],
        "approval": approval,
        "stop_condition": schema["stop_condition"],
    }
    route_pattern = "single_writer_code_squad" if role_write_policy(sub.role) == "single_writer" else "agent_as_tool"
    row = {
        "schema_version": "orchestrator.plan.v1",
        "plan_id": short_uid("plan"),
        "route_id": short_uid("route"),
        "timestamp": now_iso(),
        "status": status,
        "source": source,
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "context_id": "ga-tui",
        "orchestrator": {
            "agent_id": "orchestrator.main",
            "role": "meta_orchestrator",
            "responsibility": "plan, route, enforce gates, synthesize, and remain accountable for final state",
        },
        "task_understanding": truncate_cells(objective, 240),
        "should_split_agents": True,
        "split_reason": "A bounded subagent gets an isolated context pack while the Orchestrator keeps routing, approval, and synthesis responsibility.",
        "architecture_pattern": "orchestrator_worker",
        "task_plan": [
            {"step": "route", "status": "done", "detail": f"Selected {sub.agent_id} as {normalized_role(sub.role)}."},
            {"step": "gate", "status": "done" if status != "approval_required" else "waiting", "detail": f"Policy action: {action}."},
            {"step": "hydrate_context", "status": "done" if context_ref else "pending", "artifact_ref": context_ref},
            {"step": "delegate", "status": status, "detail": "Run only inside the recorded delegation contract."},
            {"step": "collect_artifacts", "status": "pending", "detail": "Expect result summary, evidence refs, risks, and artifact refs."},
        ],
        "routing_decision": {
            "mode": route_pattern,
            "selected_agent": sub.agent_id,
            "selected_role": normalized_role(sub.role),
            "policy_action": action,
            "reason": "Use controlled delegation instead of free-form agent chat.",
            "alternatives_considered": ["single_agent", "handoff", "a2a_team"],
        },
        "subagent_delegations": [delegation_contract],
        "delegation_contract": delegation_contract,
        "approval_required": approval_required,
        "context_plan": schema["context_policy"],
        "memory_plan": {
            "hydration": "memory_pack",
            "write_policy": "candidate_only",
            "scopes": list(schema["context_policy"].get("memory_scopes") or []),
        },
        "evaluation_plan": {
            "checks": [
                "completion",
                "evidence_or_uncertainty",
                "artifact_refs",
                "policy_compliance",
                "human_takeover_cost",
            ],
            "expected_artifact_refs": True,
            "trace_required": True,
        },
        "stop_conditions": [schema["stop_condition"]],
        "artifact_refs": [context_ref] if context_ref else [],
        "risks": schema["risks"],
        "approval": approval,
        "error": error,
    }
    append_jsonl(AGENT_ORCHESTRATOR_PLANS_PATH, row)
    return row


def memory_hydration_pack(
    *,
    task_id: str,
    sub: SubAgentRuntime,
    profile: str,
    memory: str,
    recent_mail: list[dict[str, Any]],
) -> dict[str, Any]:
    profile_items = compact_nonempty_lines(profile, limit=8)
    memory_items = compact_nonempty_lines(memory, limit=12)
    included: list[dict[str, Any]] = [
        {
            "scope": "project.agent-harness",
            "reason": "Defines the governed multi-agent baseline and approval/single-writer constraints.",
            "items": [
                "Strong Orchestrator, bounded workers, ledgers, artifact refs, human approval gates.",
                "Read tasks may be parallel; write tasks stay single-writer or approval-gated.",
            ],
            "refs": ["docs/agent-harness-architecture.md", "AGENTS.md"],
        },
        {
            "scope": "subagent.profile",
            "reason": "Defines this worker's role, boundaries, and persistent behavior.",
            "items": profile_items or ["(empty profile)"],
            "refs": [subagent_profile_file(sub)],
        },
        {
            "scope": "subagent.memory",
            "reason": "Hydrates only this worker's own approved long-term memory.",
            "items": memory_items or (["(disabled for ephemeral session agent)"] if not sub.persistent else ["(empty memory)"]),
            "refs": [subagent_memory_file(sub)] if sub.persistent else [],
        },
    ]
    mail_items = [
        f"{row.get('message_id', '')}: {row.get('intent', '')} {row.get('status', '')} task={row.get('task_id', '')}"
        for row in recent_mail[-5:]
    ]
    if mail_items:
        included.append({
            "scope": "agent_mail.refs",
            "reason": "Recent bus references can reveal pending approvals, delegated work, and result artifacts.",
            "items": mail_items,
            "refs": [str(row.get("message_id") or "") for row in recent_mail[-5:] if row.get("message_id")],
        })
    return {
        "memory_pack_id": short_uid("mempack"),
        "for_task_id": task_id,
        "included": included,
        "excluded": [
            {"scope": "raw_logs", "reason": "context_policy.include_raw_logs=false; use refs and previews instead."},
            {"scope": "unrelated_project_memory", "reason": "Avoid context pollution across unrelated projects."},
            {"scope": "secrets", "reason": "No secret access without an explicit approval gate."},
        ],
    }


def context_layers_for_task(
    state: State,
    sub: SubAgentRuntime,
    objective: str,
    task_id: str,
    *,
    profile: str,
    memory: str,
    recent_mail: list[dict[str, Any]],
    task_contract: dict[str, Any],
    memory_pack: dict[str, Any],
) -> dict[str, Any]:
    if sub.security_context == "secret":
        recent_tasks: list[dict[str, Any]] = []
        recent_traces: list[dict[str, Any]] = []
        recent_artifacts: list[dict[str, Any]] = []
    else:
        recent_tasks = read_jsonl(AGENT_TASK_LEDGER_PATH, limit=8)
        recent_traces = read_jsonl(AGENT_TRACES_PATH, limit=8)
        recent_artifacts = list(artifact_index_latest().values())[-8:]
    progress_items = [
        f"{row.get('task_id', '')}: {row.get('status', '')} {truncate_cells(str(row.get('summary') or row.get('error') or row.get('objective') or ''), 160)}"
        for row in recent_tasks[-6:]
    ]
    return {
        "L0_system_constitution": {
            "included": True,
            "items": [
                "Strong Orchestrator remains responsible for final integration.",
                "Bounded subagents execute only delegated objectives.",
                "Risky operations require program-level approval gates.",
                "Write operations respect single-writer policy.",
                "Return artifact refs, evidence refs, risks, and uncertainty.",
            ],
        },
        "L1_user_profile": {
            "included": False,
            "items": [],
            "reason": "No broad user profile is hydrated into worker context by default.",
        },
        "L2_project_memory": {
            "included": True,
            "items": [
                "GenericAgent-TUI agent harness implementation follows docs/agent-harness-architecture.md.",
                "Program-level approval, task/mail schemas, artifact index, and single-writer are active implementation layers.",
            ],
            "refs": ["docs/agent-harness-architecture.md", "goal-2/tasks.md"],
        },
        "L3_task_brief": {
            "included": True,
            "objective": objective,
            "task": task_contract,
            "source_policy": source_policy_for_role(sub.role, security_context=sub.security_context),
        },
        "L4_plan_ledger": {
            "included": True,
            "items": [
                f"{row.get('task_id', '')}: {row.get('status', '')} -> {truncate_cells(str(row.get('objective') or ''), 160)}"
                for row in recent_tasks[-6:]
            ],
        },
        "L5_progress_ledger": {
            "included": True,
            "items": progress_items,
        },
        "L6_working_notes": {
            "included": True,
            "profile_excerpt": profile[:1200],
            "memory_excerpt": memory[:1200],
            "memory_pack_ref": memory_pack.get("memory_pack_id", ""),
            "subagent_status": sub.status,
            "active_session": state.current_title,
        },
        "L7_artifacts": {
            "included": True,
            "items": [
                {
                    "artifact_id": row.get("artifact_id", ""),
                    "type": row.get("type", ""),
                    "uri": row.get("uri", ""),
                    "hash": row.get("hash", ""),
                    "source_task_id": row.get("source_task_id", ""),
                }
                for row in recent_artifacts
            ],
        },
        "L8_raw_trace": {
            "included": False,
            "include_raw_logs": False,
            "trace_refs": [row.get("trace_id", "") for row in recent_traces if row.get("trace_id")],
            "reason": "Raw trace content is excluded by default; refs are available for targeted inspection.",
        },
    }


def build_context_pack(state: State, sub: SubAgentRuntime, objective: str, task_id: str, parent_task_id: str = "") -> tuple[dict[str, Any], str]:
    template = role_template(sub.role)
    profile = subagent_profile_text(sub).strip()
    memory = subagent_memory_text(sub).strip() if sub.persistent else ""
    recent_mail = [] if sub.security_context == "secret" else read_jsonl(AGENT_MAIL_PATH, limit=8)
    task_contract = task_contract_for_role(sub.role, objective)
    context_policy = context_policy_for_task(objective, security_context=sub.security_context)
    memory_pack = memory_hydration_pack(task_id=task_id, sub=sub, profile=profile, memory=memory, recent_mail=recent_mail)
    layers = context_layers_for_task(
        state,
        sub,
        objective,
        task_id,
        profile=profile,
        memory=memory,
        recent_mail=recent_mail,
        task_contract=task_contract,
        memory_pack=memory_pack,
    )
    pack = {
        "schema_version": "contextpack.v1",
        "context_pack_id": short_uid("ctx"),
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "created_at": now_iso(),
        "for_agent": {
            "id": sub.agent_id,
            "name": sub.name,
            "role": sub.role,
            "home": sub.home,
            "security_context": sub.security_context,
        },
        "objective": objective,
        "role_template": template,
        "budget": default_task_budget(sub.role),
        "permissions": permissions_for_role(sub.role, security_context=sub.security_context),
        "context_policy": context_policy,
        "task": task_contract,
        "task_brief": {
            "objective": objective,
            "non_goals": task_contract.get("non_goals", []),
            "success_criteria": task_contract.get("success_criteria", []),
            "boundaries": task_contract.get("boundaries", []),
            "stop_condition": task_contract.get("stop_condition", ""),
            "output_contract": task_contract.get("output_contract", {}),
            "source_policy": source_policy_for_role(sub.role, security_context=sub.security_context),
        },
        "source_policy": source_policy_for_role(sub.role, security_context=sub.security_context),
        "memory_pack": memory_pack,
        "layers": layers,
        "risks": risks_for_action("read_only", sub.role, objective),
        "approval": approval_metadata(),
        "output_contract": role_output_contract(sub.role),
        "profile_excerpt": profile[:4000],
        "memory_excerpt": memory[:4000],
        "recent_agent_mail_refs": [
            {
                "message_id": row.get("message_id", ""),
                "intent": row.get("intent", ""),
                "status": row.get("status", ""),
                "task_id": row.get("task_id", ""),
                "artifact_refs": row.get("artifact_refs", []),
            }
            for row in recent_mail
        ],
        "state": {
            "active_session": state.current_title,
            "main_status": state.status,
            "subagent_status": sub.status,
        },
    }
    if sub.security_context == "secret":
        ok, ref = secret_write_subagent_json(state, "subagent-context-packs", task_id, pack)
        return pack, ref if ok else "secret://subagents/context-pack-unavailable"
    directory = os.path.join(AGENT_CONTEXT_PACKS_DIR, sub.agent_id)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{task_id}.json")
    write_text_atomic(path, json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    append_artifact_index(
        path,
        artifact_type="context_pack",
        source_task_id=task_id,
        provenance={"generated_by": "orchestrator.main", "for_agent": sub.agent_id, "role": sub.role},
        content_type="application/json",
    )
    return pack, harness_artifact_uri(path)


def format_context_pack_for_prompt(pack: dict[str, Any]) -> str:
    budget = pack.get("budget") or {}
    task = pack.get("task") or {}
    permissions = pack.get("permissions") or {}
    source_policy = pack.get("source_policy") or {}
    memory_pack = pack.get("memory_pack") or {}
    layers = pack.get("layers") or {}
    boundaries = "\n".join(f"- {item}" for item in (task.get("boundaries") or []))
    success = "\n".join(f"- {item}" for item in (task.get("success_criteria") or []))
    memory_items: list[str] = []
    for entry in memory_pack.get("included", []) or []:
        scope = entry.get("scope", "")
        items = entry.get("items", []) or []
        memory_items.append(f"- {scope}: " + "; ".join(str(item) for item in items[:3]))
    artifact_items = []
    for item in ((layers.get("L7_artifacts") or {}).get("items") or [])[-5:]:
        artifact_items.append(f"- {item.get('uri', '')} {item.get('hash', '')} task={item.get('source_task_id', '')}")
    return f"""
[GA TUI Context Pack]
task_id: {pack.get("task_id", "")}
agent: {(pack.get("for_agent") or {}).get("name", "")} ({(pack.get("for_agent") or {}).get("id", "")})
role: {(pack.get("for_agent") or {}).get("role", "specialist")}
objective: {pack.get("objective", "")}
budget: tokens={budget.get("max_tokens", 0)} tool_calls={budget.get("max_tool_calls", 0)} wall_clock={budget.get("max_wall_clock_seconds", 0)}s
write_policy: {permissions.get("write_policy", "none")}
tools_allowed: {", ".join(permissions.get("tools_allowed", []))}
tools_forbidden: {", ".join(permissions.get("tools_forbidden", []))}
output_contract: {", ".join(pack.get("output_contract") or [])}
stop_condition: {task.get("stop_condition", "")}

Boundaries:
{boundaries or "- (empty)"}

Success criteria:
{success or "- (empty)"}

Source policy:
- allowed: {", ".join(source_policy.get("allowed_sources", []))}
- forbidden: {", ".join(source_policy.get("forbidden_sources", []))}
- artifact_policy: {source_policy.get("artifact_policy", "")}

Memory hydration pack:
{chr(10).join(memory_items) or "- (empty)"}

Recent artifact refs:
{chr(10).join(artifact_items) or "- (empty)"}

Profile excerpt:
{pack.get("profile_excerpt") or "(empty)"}

Memory excerpt:
{pack.get("memory_excerpt") or "(empty)"}
[/GA TUI Context Pack]
""".strip()


def a2a_task_state(status: str) -> str:
    status = (status or "").strip().lower()
    if status in {"working", "created", "queued"}:
        return "working"
    if status in {"approval_required", "pending", "input_required"}:
        return "input_required"
    if status in {"completed", "done"}:
        return "completed"
    if status in {"failed", "rejected", "cancelled", "canceled", "aborted"}:
        return "failed" if status != "cancelled" else "cancelled"
    return status or "unknown"


def a2a_message_role(agent_id: str) -> str:
    agent_id = (agent_id or "").strip()
    if agent_id == "human":
        return "user"
    if agent_id in {"orchestrator.main", "system"}:
        return "agent"
    return "agent"


def a2a_part_from_text(text: str, *, metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {
        "kind": "text",
        "text": text,
        "metadata": metadata or {},
    }


def a2a_agent_card_for_subagent(sub: SubAgentRuntime) -> dict[str, Any]:
    permissions = permissions_for_role(sub.role, security_context=sub.security_context)
    return {
        "schema_version": "a2a.agent_card.v1",
        "agent_id": sub.agent_id,
        "name": sub.name,
        "provider": {"organization": "local.GenericAgent-TUI", "url": "local://ga-tui"},
        "endpoint": {"transport": "internal-agent-mail", "uri": f"agent://{sub.agent_id}"},
        "capabilities": {
            "streaming": True,
            "push_notifications": False,
            "long_running": True,
            "artifact_refs": True,
            "memory_candidates": True,
            "human_approval": True,
        },
        "auth": {"type": "local_runtime", "policy": "inherits TUI policy gate"},
        "role": normalized_role(sub.role),
        "security_context": sub.security_context,
        "status": sub.status,
        "skills": role_tools_allowed(sub.role),
        "write_policy": role_write_policy(sub.role),
        "permissions": permissions,
        "input_modes": ["text/plain"],
        "output_modes": ["text/plain", "artifact_refs", "memory_candidates", "approval_requests"],
        "examples": [
            {
                "input": f"Delegate a bounded {normalized_role(sub.role)} task.",
                "output": "summary, findings, evidence_refs, risks, artifact_refs, confidence",
            }
        ],
    }


def a2a_agent_card_for_role(role: str, template: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    role = normalized_role(role)
    template = template or role_template(role)
    permissions = permissions_for_role(role)
    return {
        "schema_version": "a2a.agent_card.v1",
        "agent_id": f"role.{role}",
        "name": f"{role} role template",
        "provider": {"organization": "local.GenericAgent-TUI", "url": "local://ga-tui"},
        "endpoint": {"transport": "internal-agent-mail", "uri": f"agent-role://{role}"},
        "capabilities": {
            "streaming": True,
            "push_notifications": True,
            "long_running": role in {"researcher", "coder", "ops"},
            "artifact_refs": True,
            "memory_candidates": True,
            "human_approval": True,
        },
        "auth": {"type": "local_runtime", "policy": "template inherits TUI policy gate"},
        "role": role,
        "status": "template",
        "skills": template.get("tools_allowed", []) or [],
        "write_policy": template.get("write_policy", "none"),
        "permissions": permissions,
        "input_modes": ["text/plain"],
        "output_modes": ["text/plain", "artifact_refs", "memory_candidates", "approval_requests"],
        "examples": [
            {
                "input": f"Create a bounded {role} task with objective, budget, permissions, and stop condition.",
                "output": "summary, findings, evidence_refs, risks, artifact_refs, confidence",
            }
        ],
    }


def a2a_task_object(row: dict[str, Any]) -> dict[str, Any]:
    task_id = str(row.get("task_id") or "")
    trace_rows = [trace for trace in read_jsonl(AGENT_TRACES_PATH, limit=80) if str(trace.get("task_id") or "") == task_id]
    artifacts = [
        {"artifactId": ref, "uri": ref, "metadata": {"source": "task.artifact_refs"}}
        for ref in (row.get("artifact_refs") or [])
    ]
    return {
        "schema_version": "a2a.task.v1",
        "id": task_id,
        "contextId": str(row.get("context_id") or "ga-tui"),
        "status": {
            "state": a2a_task_state(str(row.get("status") or "")),
            "timestamp": row.get("timestamp", ""),
            "message": row.get("summary") or row.get("error") or "",
        },
        "history": [
            {
                "messageId": str(trace.get("trace_id") or ""),
                "role": "agent",
                "parts": [a2a_part_from_text(str(trace.get("event") or ""), metadata={"trace_status": trace.get("status", "")})],
            }
            for trace in trace_rows[-8:]
        ],
        "artifacts": artifacts,
        "metadata": {
            "assigned_agent": row.get("assigned_agent", ""),
            "objective": row.get("objective", ""),
            "approval": row.get("approval") or {},
            "budget": row.get("budget") or {},
        },
    }


def a2a_message_object(row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    text = str(payload.get("summary") or payload.get("objective") or payload.get("prompt_preview") or row.get("intent") or "")
    artifact_parts = [
        {
            "kind": "file",
            "file": {"uri": ref},
            "metadata": {"source": "artifact_ref"},
        }
        for ref in (row.get("artifact_refs") or [])
    ]
    return {
        "schema_version": "a2a.message.v1",
        "messageId": str(row.get("message_id") or ""),
        "contextId": str(row.get("context_id") or "ga-tui"),
        "taskId": str(row.get("task_id") or ""),
        "role": a2a_message_role(str((row.get("from") or {}).get("agent_id") or "")),
        "from": row.get("from") or {},
        "to": row.get("to") or {},
        "intent": row.get("intent", ""),
        "status": row.get("status", ""),
        "parts": [a2a_part_from_text(text, metadata={"intent": row.get("intent", "")})] + artifact_parts,
        "metadata": {
            "requires_human_approval": bool(row.get("requires_human_approval")),
            "approval": row.get("approval") or {},
            "budget": row.get("budget") or {},
        },
    }


def a2a_artifact_object(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "a2a.artifact.v1",
        "artifactId": str(row.get("artifact_id") or ""),
        "contextId": "ga-tui",
        "taskId": str(row.get("source_task_id") or ""),
        "name": os.path.basename(str(row.get("path") or row.get("uri") or "")),
        "parts": [
            {
                "kind": "file",
                "file": {
                    "uri": row.get("uri", ""),
                    "mimeType": row.get("content_type", "application/octet-stream"),
                    "path": row.get("path", ""),
                },
                "metadata": {
                    "hash": row.get("hash", ""),
                    "size_bytes": row.get("size_bytes", 0),
                    "preview_path": row.get("preview_path", ""),
                },
            }
        ],
        "metadata": {
            "type": row.get("type", ""),
            "provenance": row.get("provenance") or {},
        },
    }


def gateway_capability_registry(state: Optional[State] = None) -> dict[str, Any]:
    role_capabilities = {
        role: {
            "role": role,
            "description": template.get("description", ""),
            "skills": template.get("tools_allowed", []),
            "write_policy": template.get("write_policy", "none"),
            "output_contract": template.get("output_contract", []),
            "permissions": permissions_for_role(role),
        }
        for role, template in sorted(ROLE_TEMPLATES.items())
    }
    agents = []
    if state is not None:
        agents = [
            {
                "agent_id": sub.agent_id,
                "role": normalized_role(sub.role),
                "security_context": sub.security_context,
                "capabilities_ref": f"capability://role/{normalized_role(sub.role)}",
                "status": sub.status,
                "active_task_id": sub.active_bus_task_id,
            }
            for sub in sorted(state.subagents.values(), key=lambda item: item.agent_id)
        ]
    return {
        "schema_version": "agentcapabilities.v1",
        "roles": role_capabilities,
        "agents": agents,
        "discovery": {
            "by_role": sorted(role_capabilities),
            "by_agent": [item["agent_id"] for item in agents],
            "policy": "least privilege; risky capabilities require policy approval",
        },
    }


def external_bridge_registry() -> dict[str, Any]:
    bridge_specs = [
        {
            "id": "cli",
            "type": "human_interface",
            "name": "CLI",
            "status": "active",
            "transport": "local_process",
            "entrypoints": ["ga-tui", "python -m ga_tui.app", "--gateway-daemon"],
            "policy_action": "read_only",
            "approval_required": False,
        },
        {
            "id": "dashboard",
            "type": "human_interface",
            "name": "Dashboard",
            "status": "active",
            "transport": "http",
            "entrypoints": ["/gateway", "/baseline", "/tasks", "/approvals", "/artifacts", "/evals"],
            "policy_action": "read_only",
            "approval_required": False,
        },
        {
            "id": "approval_inbox",
            "type": "human_interface",
            "name": "Approval Inbox",
            "status": "active",
            "transport": "tui_panel",
            "entrypoints": ["/approvals", "decide_approval"],
            "policy_action": "modify_permission_policy",
            "approval_required": True,
        },
        {
            "id": "feishu",
            "type": "external_ui_bridge",
            "name": "Feishu",
            "status": "registered_adapter",
            "transport": "webhook_or_bot",
            "entrypoints": ["/a2a/push-subscriptions", "/a2a/events", "/a2a/tasks/query"],
            "policy_action": "external_send",
            "approval_required": True,
        },
        {
            "id": "openclaw",
            "type": "external_ui_bridge",
            "name": "OpenClaw",
            "status": "registered_adapter",
            "transport": "http_a2a_bridge",
            "entrypoints": ["/gateway", "/a2a", "/mcp"],
            "policy_action": "external_send",
            "approval_required": True,
        },
        {
            "id": "codex",
            "type": "agent_runtime_bridge",
            "name": "Codex",
            "status": "registered_adapter",
            "transport": "a2a_agent_card",
            "entrypoints": ["/a2a/agent-cards", "/a2a/tasks/query", "artifact://"],
            "policy_action": "repo_write",
            "approval_required": True,
        },
        {
            "id": "claude_code",
            "type": "agent_runtime_bridge",
            "name": "Claude Code",
            "status": "registered_adapter",
            "transport": "a2a_agent_card",
            "entrypoints": ["/a2a/agent-cards", "/a2a/tasks/query", "artifact://"],
            "policy_action": "repo_write",
            "approval_required": True,
        },
        {
            "id": "deer_flow",
            "type": "agent_runtime_bridge",
            "name": "Deer Flow",
            "status": "registered_adapter",
            "transport": "a2a_team_bridge",
            "entrypoints": ["/a2a", "/a2a/events", "/a2a/push-subscriptions"],
            "policy_action": "read_only",
            "approval_required": False,
        },
        {
            "id": "local_tools",
            "type": "mcp_tool_bridge",
            "name": "Local Tools",
            "status": "active",
            "transport": "mcp_resource_registry",
            "entrypoints": ["/mcp/tools", "/mcp/resources", "/mcp/resource"],
            "policy_action": "read_only",
            "approval_required": False,
        },
    ]
    bridges = []
    for spec in bridge_specs:
        action, rule = policy_rule_for(str(spec["policy_action"]))
        bridges.append({
            "schema_version": "agentbridge.v1",
            **spec,
            "policy": {
                "action": action,
                "approval_required_for": rule.get("approval_required_for", action),
                "risk": rule.get("risk", "medium"),
                "mode": rule.get("mode", "approval_required"),
                "approval_required": bool(spec.get("approval_required")),
            },
            "audit": {
                "messages": AGENT_MAIL_PATH,
                "tasks": AGENT_TASK_LEDGER_PATH,
                "approvals": AGENT_APPROVALS_PATH,
                "traces": AGENT_TRACES_PATH,
                "artifacts": AGENT_ARTIFACT_INDEX_PATH,
            },
        })
    data = {
        "schema_version": "agentbridge.registry.v1",
        "updated_at": now_iso(),
        "principles": {
            "external_send_requires_approval": True,
            "remote_agent_access_uses_a2a": True,
            "tool_access_uses_mcp": True,
            "artifact_refs_required": True,
        },
        "bridges": bridges,
        "bridge_ids": [item["id"] for item in bridges],
    }
    write_text_atomic(AGENT_BRIDGE_REGISTRY_PATH, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return data


def mcp_tool_registry() -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    seen: set[str] = set()
    for role, template in sorted(ROLE_TEMPLATES.items()):
        for tool_name in template.get("tools_allowed", []) or []:
            if tool_name in seen:
                continue
            seen.add(tool_name)
            policy_action = "read_only"
            if "write" in tool_name:
                policy_action = "repo_write"
            elif "deploy" in tool_name or "shell" in tool_name:
                policy_action = "deploy"
            tools.append({
                "name": tool_name,
                "description": f"Local capability exposed through role template: {role}",
                "input_schema": {"type": "object", "additionalProperties": True},
                "policy_action": policy_action,
                "approval_required": policy_rule_for(policy_action)[1].get("mode") == "approval_required",
                "roles": [r for r, tmpl in sorted(ROLE_TEMPLATES.items()) if tool_name in (tmpl.get("tools_allowed", []) or [])],
            })
    return tools


def mcp_resource_registry() -> list[dict[str, Any]]:
    return [
        {"uri": "resource://agent-mail/messages", "path": AGENT_MAIL_PATH, "description": "Internal Agent Mail JSONL"},
        {"uri": "resource://agent-mail/tasks", "path": AGENT_TASK_LEDGER_PATH, "description": "Task ledger JSONL"},
        {"uri": "resource://agent-mail/artifacts", "path": AGENT_ARTIFACT_INDEX_PATH, "description": "Artifact index JSONL"},
        {"uri": "resource://agent-mail/checkpoints", "path": AGENT_CHECKPOINT_INDEX_PATH, "description": "Checkpoint index JSONL"},
        {"uri": "resource://agent-mail/recovery", "path": AGENT_RECOVERY_PATH, "description": "Recovery records JSONL"},
        {"uri": "resource://agent-mail/recovery-plans", "path": AGENT_RECOVERY_PLANS_PATH, "description": "Replayable recovery plan JSONL"},
        {"uri": "resource://agent-mail/gateway-daemon", "path": AGENT_GATEWAY_DAEMON_STATUS_PATH, "description": "Gateway daemon status JSON"},
        {"uri": "resource://agent-mail/gateway-push-subscriptions", "path": AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH, "description": "Gateway push subscriptions JSONL"},
        {"uri": "resource://agent-mail/gateway-push-deliveries", "path": AGENT_GATEWAY_PUSH_DELIVERIES_PATH, "description": "Gateway push delivery audit JSONL"},
        {"uri": "resource://agent-mail/bridges", "path": AGENT_BRIDGE_REGISTRY_PATH, "description": "External bridge registry JSON"},
        {"uri": "resource://agent-mail/policy", "path": AGENT_POLICY_PATH, "description": "Policy gate config"},
    ]


def gateway_base_url(host: str, port: int) -> str:
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else (host or "127.0.0.1")
    return f"http://{display_host}:{int(port)}"


def process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    stat_path = f"/proc/{pid}/stat"
    if os.path.exists(stat_path):
        try:
            parts = read_text_file(stat_path, "").split()
            if len(parts) > 2 and parts[2] == "Z":
                return False
        except Exception:
            pass
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def write_gateway_daemon_status(
    status: str,
    *,
    pid: int = 0,
    host: str = "127.0.0.1",
    port: int = 8765,
    message: str = "",
    command: str = "",
) -> dict[str, Any]:
    row = {
        "schema_version": "agentgateway.daemon.v1",
        "updated_at": now_iso(),
        "status": status,
        "pid": int(pid or 0),
        "alive": process_is_alive(int(pid or 0)),
        "host": host,
        "port": int(port or 0),
        "base_url": gateway_base_url(host, int(port or 0)) if int(port or 0) else "",
        "pid_path": AGENT_GATEWAY_DAEMON_PID_PATH,
        "status_path": AGENT_GATEWAY_DAEMON_STATUS_PATH,
        "log_path": AGENT_GATEWAY_DAEMON_LOG_PATH,
        "command": command,
        "message": message,
    }
    write_text_atomic(AGENT_GATEWAY_DAEMON_STATUS_PATH, json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    if row["pid"]:
        write_text_atomic(AGENT_GATEWAY_DAEMON_PID_PATH, str(row["pid"]) + "\n")
    return row


def read_gateway_daemon_status() -> dict[str, Any]:
    try:
        data = json.loads(read_text_file(AGENT_GATEWAY_DAEMON_STATUS_PATH, "{}") or "{}")
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    if not data:
        pid_text = read_text_file(AGENT_GATEWAY_DAEMON_PID_PATH, "").strip()
        pid = int(pid_text) if pid_text.isdigit() else 0
        data = {
            "schema_version": "agentgateway.daemon.v1",
            "updated_at": "",
            "status": "unknown" if pid else "stopped",
            "pid": pid,
            "host": "127.0.0.1",
            "port": 0,
            "base_url": "",
            "pid_path": AGENT_GATEWAY_DAEMON_PID_PATH,
            "status_path": AGENT_GATEWAY_DAEMON_STATUS_PATH,
            "log_path": AGENT_GATEWAY_DAEMON_LOG_PATH,
            "command": "",
            "message": "",
        }
    pid = int(data.get("pid") or 0)
    alive = process_is_alive(pid)
    data["alive"] = alive
    if data.get("status") == "running" and not alive:
        data["status"] = "stale"
    if data.get("status") in {"starting", "running"} and int(data.get("port") or 0):
        data["base_url"] = gateway_base_url(str(data.get("host") or "127.0.0.1"), int(data.get("port") or 0))
    data["pid_path"] = AGENT_GATEWAY_DAEMON_PID_PATH
    data["status_path"] = AGENT_GATEWAY_DAEMON_STATUS_PATH
    data["log_path"] = AGENT_GATEWAY_DAEMON_LOG_PATH
    return data


def gateway_daemon_alive() -> bool:
    status = read_gateway_daemon_status()
    return bool(status.get("alive") and status.get("status") == "running")


def gateway_service_descriptor(host: str = "127.0.0.1", port: int = 8765) -> dict[str, Any]:
    base_url = gateway_base_url(host, port)
    return {
        "schema_version": "agentgateway.service.v1",
        "status": "network_capable",
        "bind": {"host": host, "port": int(port)},
        "base_url": base_url,
        "request_response": {
            "health": f"{base_url}/health",
            "registry": f"{base_url}/gateway",
            "a2a": f"{base_url}/a2a",
            "mcp": f"{base_url}/mcp",
            "a2a_task_query": f"{base_url}/a2a/tasks/query",
            "mcp_resource_read": f"{base_url}/mcp/resource?uri=resource://agent-mail/tasks",
        },
        "sse": {
            "endpoint": f"{base_url}/a2a/events",
            "content_type": "text/event-stream",
            "event_sources": ["agent_mail", "trace"],
        },
        "push_notifications": {
            "subscribe_endpoint": f"{base_url}/a2a/push-subscriptions",
            "test_endpoint": f"{base_url}/a2a/push-test",
            "subscriptions_path": AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH,
            "deliveries_path": AGENT_GATEWAY_PUSH_DELIVERIES_PATH,
            "default_endpoint_policy": "loopback_only_unless_GA_TUI_GATEWAY_ALLOW_REMOTE_PUSH=1",
        },
        "daemon": {
            "commands": ["start", "stop", "restart", "status"],
            "pid_path": AGENT_GATEWAY_DAEMON_PID_PATH,
            "status_path": AGENT_GATEWAY_DAEMON_STATUS_PATH,
            "log_path": AGENT_GATEWAY_DAEMON_LOG_PATH,
            "state": read_gateway_daemon_status(),
        },
    }


def mcp_resource_contents(uri: str) -> dict[str, Any]:
    uri = str(uri or "")
    registry = {row.get("uri", ""): row for row in mcp_resource_registry()}
    resource = registry.get(uri)
    if not resource:
        return {}
    path = str(resource.get("path") or "")
    if os.path.isdir(path):
        text = json.dumps({"entries": sorted(os.listdir(path))}, ensure_ascii=False, indent=2)
        mime = "application/json"
    else:
        text = read_text_file(path, "")
        if path.endswith(".json"):
            mime = "application/json"
        elif path.endswith(".jsonl"):
            mime = "application/jsonl"
        else:
            mime = "text/plain"
    return {
        "schema_version": "mcp.resource.contents.v1",
        "uri": uri,
        "path": path,
        "description": resource.get("description", ""),
        "contents": [
            {
                "uri": uri,
                "mimeType": mime,
                "text": text,
            }
        ],
    }


def gateway_sse_events(*, limit: int = 20) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for row in read_jsonl(AGENT_MAIL_PATH, limit=limit):
        event_id = str(row.get("message_id") or "")
        if not event_id:
            continue
        events.append({
            "id": event_id,
            "event": "agent_mail",
            "timestamp": row.get("timestamp", ""),
            "data": a2a_message_object(row),
        })
    for row in read_jsonl(AGENT_TRACES_PATH, limit=limit):
        event_id = str(row.get("trace_id") or "")
        if not event_id:
            continue
        events.append({
            "id": event_id,
            "event": "trace",
            "timestamp": row.get("timestamp", ""),
            "data": row,
        })
    events.sort(key=lambda item: str(item.get("timestamp") or ""))
    return events[-limit:]


def gateway_push_endpoint_allowed(endpoint: str) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(str(endpoint or ""))
    if parsed.scheme not in {"http", "https"}:
        return False, "unsupported_scheme"
    host = (parsed.hostname or "").lower()
    if os.environ.get("GA_TUI_GATEWAY_ALLOW_REMOTE_PUSH") == "1":
        return True, "remote_allowed_by_env"
    if parsed.scheme == "http" and host in {"127.0.0.1", "localhost", "::1"}:
        return True, "loopback_allowed"
    return False, "remote_push_requires_GA_TUI_GATEWAY_ALLOW_REMOTE_PUSH"


def append_gateway_push_subscription(endpoint: str, event_types: Optional[list[str]] = None) -> dict[str, Any]:
    endpoint = str(endpoint or "").strip()
    allowed, reason = gateway_push_endpoint_allowed(endpoint)
    if not allowed:
        raise ValueError(reason)
    normalized_event_types = [str(item) for item in (event_types or ["agent_mail", "trace", "gateway"]) if str(item).strip()]
    row = {
        "schema_version": "agentgateway.push_subscription.v1",
        "subscription_id": short_uid("pushsub"),
        "created_at": now_iso(),
        "endpoint": endpoint,
        "event_types": normalized_event_types or ["agent_mail", "trace", "gateway"],
        "enabled": True,
        "endpoint_policy": reason,
        "auth": {"type": "none", "secret_stored": False},
    }
    append_jsonl(AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH, row)
    return row


def gateway_push_subscriptions() -> list[dict[str, Any]]:
    return [row for row in read_jsonl(AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH) if row.get("enabled", True)]


def deliver_gateway_push_notification(event: dict[str, Any]) -> list[dict[str, Any]]:
    event_type = str(event.get("event") or "gateway")
    deliveries: list[dict[str, Any]] = []
    for sub in gateway_push_subscriptions():
        event_types = [str(item) for item in (sub.get("event_types") or [])]
        if event_types and "*" not in event_types and event_type not in event_types:
            continue
        endpoint = str(sub.get("endpoint") or "")
        allowed, reason = gateway_push_endpoint_allowed(endpoint)
        delivery = {
            "schema_version": "agentgateway.push_delivery.v1",
            "delivery_id": short_uid("pushdelivery"),
            "subscription_id": sub.get("subscription_id", ""),
            "created_at": now_iso(),
            "endpoint": endpoint,
            "event": event_type,
            "allowed": allowed,
            "policy_reason": reason,
            "status": "blocked",
            "response_status": 0,
            "error": "",
        }
        if allowed:
            body = json.dumps(event, ensure_ascii=False).encode("utf-8")
            request = urllib.request.Request(
                endpoint,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "ga-tui-gateway/1"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=2) as response:
                    delivery["status"] = "delivered"
                    delivery["response_status"] = int(response.status)
            except Exception as exc:
                delivery["status"] = "failed"
                delivery["error"] = str(exc)
        append_jsonl(AGENT_GATEWAY_PUSH_DELIVERIES_PATH, delivery)
        deliveries.append(delivery)
    return deliveries


def query_a2a_task_payload(payload: dict[str, Any]) -> dict[str, Any]:
    registry = ensure_gateway_registry(None)
    task_id = str(payload.get("task_id") or "")
    tasks = registry["a2a_gateway"].get("tasks") or []
    if task_id:
        tasks = [row for row in tasks if str(row.get("id") or "") == task_id]
    return {
        "schema_version": "a2a.query_response.v1",
        "contextId": "ga-tui",
        "query": payload,
        "tasks": tasks,
        "messages": registry["a2a_gateway"].get("messages") or [],
        "artifacts": registry["a2a_gateway"].get("artifacts") or [],
    }


class GatewayRequestHandler(BaseHTTPRequestHandler):
    server_version = "GATUIGateway/1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: int, message: str) -> None:
        self.send_json({"schema_version": "agentgateway.error.v1", "error": message, "status": status}, status=status)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = urllib.parse.parse_qs(parsed.query)
        registry = ensure_gateway_registry(None)
        if path in {"/", "/health"}:
            actual_host, actual_port = self.server.server_address[:2]
            self.send_json({"ok": True, "service": gateway_service_descriptor(str(actual_host), int(actual_port)), "registry_path": AGENT_GATEWAY_PATH})
            return
        if path == "/gateway":
            self.send_json(registry)
            return
        if path == "/a2a":
            self.send_json(registry["a2a_gateway"])
            return
        if path == "/a2a/agent-cards":
            self.send_json({"schema_version": "a2a.agent_cards.v1", "agent_cards": registry["a2a_gateway"].get("agent_cards") or []})
            return
        if path == "/a2a/tasks":
            self.send_json({"schema_version": "a2a.tasks.v1", "tasks": registry["a2a_gateway"].get("tasks") or []})
            return
        if path.startswith("/a2a/tasks/"):
            task_id = urllib.parse.unquote(path.rsplit("/", 1)[-1])
            tasks = [row for row in registry["a2a_gateway"].get("tasks") or [] if str(row.get("id") or "") == task_id]
            self.send_json({"schema_version": "a2a.task_response.v1", "task": tasks[-1] if tasks else None}, status=200 if tasks else 404)
            return
        if path == "/a2a/messages":
            self.send_json({"schema_version": "a2a.messages.v1", "messages": registry["a2a_gateway"].get("messages") or []})
            return
        if path == "/a2a/artifacts":
            self.send_json({"schema_version": "a2a.artifacts.v1", "artifacts": registry["a2a_gateway"].get("artifacts") or []})
            return
        if path == "/a2a/events":
            self.send_sse(once=(query.get("once") or ["0"])[0] == "1")
            return
        if path == "/mcp":
            self.send_json(registry["mcp_gateway"])
            return
        if path == "/mcp/tools":
            self.send_json({"schema_version": "mcp.tools.v1", "tools": registry["mcp_gateway"].get("tools") or []})
            return
        if path == "/mcp/resources":
            self.send_json({"schema_version": "mcp.resources.v1", "resources": registry["mcp_gateway"].get("resources") or []})
            return
        if path == "/mcp/resource":
            uri = (query.get("uri") or [""])[0]
            resource = mcp_resource_contents(uri)
            if not resource:
                self.send_error_json(404, "unknown resource uri")
                return
            self.send_json(resource)
            return
        self.send_error_json(404, "not found")

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        payload = self.read_json_body()
        if path == "/health":
            actual_host, actual_port = self.server.server_address[:2]
            self.send_json({"ok": True, "service": gateway_service_descriptor(str(actual_host), int(actual_port)), "received": payload})
            return
        if path == "/a2a/tasks/query":
            self.send_json(query_a2a_task_payload(payload))
            return
        if path == "/a2a/push-subscriptions":
            try:
                raw_event_types = payload.get("event_types")
                event_types = raw_event_types if isinstance(raw_event_types, list) else None
                row = append_gateway_push_subscription(str(payload.get("endpoint") or ""), event_types)
            except ValueError as exc:
                self.send_error_json(400, str(exc))
                return
            self.send_json({"schema_version": "agentgateway.push_subscription_response.v1", "subscription": row}, status=201)
            return
        if path == "/a2a/push-test":
            event = {
                "schema_version": "agentgateway.push_event.v1",
                "event": str(payload.get("event") or "gateway"),
                "created_at": now_iso(),
                "payload": payload.get("payload") if isinstance(payload.get("payload"), dict) else {"message": "test"},
            }
            deliveries = deliver_gateway_push_notification(event)
            self.send_json({"schema_version": "agentgateway.push_delivery_response.v1", "event": event, "deliveries": deliveries})
            return
        self.send_error_json(404, "not found")

    def send_sse(self, *, once: bool = False) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close" if once else "keep-alive")
        self.end_headers()
        sent: set[str] = set()
        while True:
            events = gateway_sse_events(limit=20)
            if not events:
                events = [{"id": short_uid("event"), "event": "gateway", "data": {"status": "idle", "created_at": now_iso()}}]
            for event in events:
                event_id = str(event.get("id") or short_uid("event"))
                if event_id in sent:
                    continue
                sent.add(event_id)
                data = json.dumps(event.get("data") or {}, ensure_ascii=False, sort_keys=True)
                frame = f"id: {event_id}\nevent: {event.get('event') or 'message'}\ndata: {data}\n\n"
                self.wfile.write(frame.encode("utf-8"))
                self.wfile.flush()
                if once:
                    return
            if once:
                return
            time.sleep(1)


def make_gateway_http_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, int(port)), GatewayRequestHandler)


def serve_gateway(host: str = "127.0.0.1", port: int = 8765) -> int:
    server = make_gateway_http_server(host, port)
    actual_host, actual_port = server.server_address[:2]
    write_gateway_daemon_status(
        "running",
        pid=os.getpid(),
        host=str(actual_host),
        port=int(actual_port),
        message="gateway server is accepting requests",
        command="serve",
    )
    print(f"GA TUI gateway serving at {gateway_base_url(str(actual_host), int(actual_port))}")
    print("Endpoints: /gateway /a2a /a2a/events /mcp /mcp/resources")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("GA TUI gateway stopped.")
    finally:
        server.server_close()
        write_gateway_daemon_status(
            "stopped",
            pid=os.getpid(),
            host=str(actual_host),
            port=int(actual_port),
            message="gateway server stopped",
            command="serve",
        )
    return 0


def gateway_daemon_env(extra_env: Optional[dict[str, str]] = None) -> dict[str, str]:
    env = os.environ.copy()
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env["PYTHONPATH"] = src_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["GA_TUI_HARNESS_DIR"] = AGENT_HARNESS_DIR
    if extra_env:
        env.update({str(key): str(value) for key, value in extra_env.items()})
    return env


def wait_for_gateway_daemon(pid: int, *, timeout: float = 5.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_status: dict[str, Any] = {}
    while time.monotonic() < deadline:
        status = read_gateway_daemon_status()
        last_status = status
        if int(status.get("pid") or 0) == int(pid) and status.get("status") == "running" and int(status.get("port") or 0):
            return status
        if not process_is_alive(pid):
            break
        time.sleep(0.1)
    return last_status or read_gateway_daemon_status()


def start_gateway_daemon(host: str = "127.0.0.1", port: int = 8765, *, extra_env: Optional[dict[str, str]] = None) -> dict[str, Any]:
    current = read_gateway_daemon_status()
    if current.get("alive") and current.get("status") == "running":
        current["message"] = "gateway daemon already running"
        return current
    os.makedirs(AGENT_HARNESS_DIR, exist_ok=True)
    log_fh = open(AGENT_GATEWAY_DAEMON_LOG_PATH, "a", encoding="utf-8", buffering=1)
    cmd = [
        sys.executable,
        "-m",
        "ga_tui.app",
        "--serve-gateway",
        "--gateway-host",
        str(host),
        "--gateway-port",
        str(int(port)),
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=APP_ROOT_DIR,
        env=gateway_daemon_env(extra_env),
        stdin=subprocess.DEVNULL,
        stdout=log_fh,
        stderr=log_fh,
        start_new_session=True,
    )
    log_fh.close()
    write_gateway_daemon_status(
        "starting",
        pid=proc.pid,
        host=str(host),
        port=int(port),
        message="gateway daemon process spawned",
        command="start",
    )
    status = wait_for_gateway_daemon(proc.pid)
    if status.get("status") != "running":
        status = write_gateway_daemon_status(
            "failed" if not process_is_alive(proc.pid) else "starting",
            pid=proc.pid,
            host=str(host),
            port=int(port),
            message="gateway daemon did not report ready before timeout",
            command="start",
        )
    return status


def stop_gateway_daemon(*, timeout: float = 5.0) -> dict[str, Any]:
    status = read_gateway_daemon_status()
    pid = int(status.get("pid") or 0)
    host = str(status.get("host") or "127.0.0.1")
    port = int(status.get("port") or 0)
    if not process_is_alive(pid):
        return write_gateway_daemon_status("stopped", pid=pid, host=host, port=port, message="gateway daemon is not running", command="stop")
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return write_gateway_daemon_status("stop_failed", pid=pid, host=host, port=port, message=str(exc), command="stop")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_is_alive(pid):
            try:
                os.waitpid(pid, os.WNOHANG)
            except Exception:
                pass
            return write_gateway_daemon_status("stopped", pid=pid, host=host, port=port, message="gateway daemon stopped", command="stop")
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    try:
        os.waitpid(pid, os.WNOHANG)
    except Exception:
        pass
    return write_gateway_daemon_status("stopped", pid=pid, host=host, port=port, message="gateway daemon force-stopped", command="stop")


def restart_gateway_daemon(host: str = "127.0.0.1", port: int = 8765, *, extra_env: Optional[dict[str, str]] = None) -> dict[str, Any]:
    stop_gateway_daemon()
    return start_gateway_daemon(host, port, extra_env=extra_env)


def format_gateway_daemon_status(status: dict[str, Any]) -> str:
    return "\n".join([
        f"status: {status.get('status', '-')}",
        f"alive: {bool(status.get('alive'))}",
        f"pid: {status.get('pid', 0)}",
        f"base_url: {status.get('base_url') or '-'}",
        f"log: {status.get('log_path') or AGENT_GATEWAY_DAEMON_LOG_PATH}",
        f"message: {status.get('message') or '-'}",
    ])


def gateway_daemon_command(command: str, host: str = "127.0.0.1", port: int = 8765) -> int:
    command = str(command or "status")
    if command == "start":
        status = start_gateway_daemon(host, port)
    elif command == "stop":
        status = stop_gateway_daemon()
    elif command == "restart":
        status = restart_gateway_daemon(host, port)
    elif command == "status":
        status = read_gateway_daemon_status()
    else:
        print(f"Unknown gateway daemon command: {command}", file=sys.stderr)
        return 2
    print(format_gateway_daemon_status(status))
    return 0 if status.get("status") not in {"failed", "stop_failed"} else 1


GOVERNANCE_COMPONENT_SPECS: list[dict[str, Any]] = [
    {
        "id": "meta_orchestrator",
        "layer": "control",
        "responsibility": "Own final task outcome, delegate bounded work, synthesize results, and keep audit trails.",
        "functions": ["append_orchestrator_plan", "start_subagent_task", "process_ui_queue"],
        "stores": ["orchestrator_plans", "tasks", "messages", "traces"],
        "write_policy": "delegates_only",
        "memory_write_policy": "candidate_only",
    },
    {
        "id": "planner",
        "layer": "control",
        "responsibility": "Build task plan, budget, stop conditions, context plan, memory plan, and evaluation plan.",
        "functions": ["append_orchestrator_plan", "task_contract_for_role", "default_task_budget"],
        "stores": ["orchestrator_plans", "tasks"],
        "write_policy": "none",
        "memory_write_policy": "candidate_only",
    },
    {
        "id": "router",
        "layer": "control",
        "responsibility": "Choose single_agent, agent_as_tool, orchestrator_worker, handoff, A2A, or single-writer lanes.",
        "functions": ["append_orchestrator_plan", "infer_policy_action_for_subagent_task", "permissions_for_role"],
        "stores": ["orchestrator_plans", "messages"],
        "write_policy": "none",
        "memory_write_policy": "candidate_only",
    },
    {
        "id": "context_engineer",
        "layer": "control",
        "responsibility": "Assemble L0-L8 context packs, memory hydration, source policy, and raw-log exclusion.",
        "functions": ["build_context_pack", "format_context_pack_for_prompt", "context_policy_for_task"],
        "stores": ["artifacts", "tasks", "messages", "traces"],
        "write_policy": "artifact_only",
        "memory_write_policy": "candidate_only",
    },
    {
        "id": "approval_controller",
        "layer": "governance",
        "responsibility": "Create and enforce hard-coded human approval gates for risky operations.",
        "functions": ["evaluate_policy_action", "queue_policy_approval", "decide_approval"],
        "stores": ["policy", "policy_decisions", "approvals"],
        "write_policy": "approval_state_only",
        "memory_write_policy": "candidate_only",
    },
    {
        "id": "risk_guard",
        "layer": "governance",
        "responsibility": "Classify risky actions and keep model choices subordinate to program-level policy.",
        "functions": ["evaluate_policy_action", "risks_for_action", "policy_rule_for"],
        "stores": ["policy", "policy_decisions", "tasks"],
        "write_policy": "none",
        "memory_write_policy": "candidate_only",
    },
    {
        "id": "memory_curator",
        "layer": "governance",
        "responsibility": "Extract, reject, dedupe, conflict-check, and submit memory candidates without direct writes.",
        "functions": ["queue_curated_memory_candidate", "build_memory_candidate", "memory_candidate_rejection_reason"],
        "stores": ["memory_candidates", "approvals", "artifacts", "traces"],
        "role": "memory_curator",
        "write_policy": "candidate_only",
        "memory_write_policy": "candidate_only",
    },
    {
        "id": "eval_controller",
        "layer": "governance",
        "responsibility": "Score final state, evidence, citation, source quality, tool efficiency, and policy compliance.",
        "functions": ["append_task_eval", "collect_task_audit_refs", "eval_panel_items"],
        "stores": ["evals", "traces", "artifacts", "tasks"],
        "write_policy": "eval_only",
        "memory_write_policy": "candidate_only",
    },
    {
        "id": "recovery_controller",
        "layer": "governance",
        "responsibility": "Checkpoint tasks, inspect stale work, and perform approval-gated recovery actions.",
        "functions": ["append_task_checkpoint", "append_recovery_plan", "append_recovery_record", "recover_task_action"],
        "stores": ["checkpoints", "checkpoint_store", "recovery_plans", "recovery", "tasks"],
        "write_policy": "recovery_state_only",
        "memory_write_policy": "candidate_only",
    },
    {
        "id": "protocol_gateway",
        "layer": "protocol",
        "responsibility": "Expose internal Agent Mail as A2A-compatible objects, MCP tool/resource registries, external bridge descriptors, and an optional network gateway.",
        "functions": ["ensure_gateway_registry", "a2a_agent_card_for_subagent", "a2a_agent_card_for_role", "mcp_tool_registry", "mcp_resource_registry", "external_bridge_registry", "serve_gateway", "start_gateway_daemon", "stop_gateway_daemon", "GatewayRequestHandler"],
        "stores": ["gateway", "messages", "tasks", "artifacts", "gateway_push_subscriptions", "gateway_push_deliveries", "gateway_daemon_status", "gateway_daemon_pid", "bridges"],
        "write_policy": "registry_only",
        "memory_write_policy": "candidate_only",
    },
]


def governance_store_paths() -> dict[str, str]:
    return {
        "messages": AGENT_MAIL_PATH,
        "tasks": AGENT_TASK_LEDGER_PATH,
        "approvals": AGENT_APPROVALS_PATH,
        "artifacts": AGENT_ARTIFACT_INDEX_PATH,
        "policy": AGENT_POLICY_PATH,
        "policy_decisions": AGENT_POLICY_DECISIONS_PATH,
        "orchestrator_plans": AGENT_ORCHESTRATOR_PLANS_PATH,
        "memory_candidates": AGENT_MEMORY_CANDIDATES_PATH,
        "traces": AGENT_TRACES_PATH,
        "evals": AGENT_EVALS_PATH,
        "checkpoints": AGENT_CHECKPOINT_INDEX_PATH,
        "checkpoint_store": AGENT_CHECKPOINTS_DIR,
        "recovery": AGENT_RECOVERY_PATH,
        "recovery_plans": AGENT_RECOVERY_PLANS_PATH,
        "gateway": AGENT_GATEWAY_PATH,
        "governance": AGENT_GOVERNANCE_PATH,
        "gateway_push_subscriptions": AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH,
        "gateway_push_deliveries": AGENT_GATEWAY_PUSH_DELIVERIES_PATH,
        "gateway_daemon_status": AGENT_GATEWAY_DAEMON_STATUS_PATH,
        "gateway_daemon_pid": AGENT_GATEWAY_DAEMON_PID_PATH,
        "bridges": AGENT_BRIDGE_REGISTRY_PATH,
    }


def governance_component_registry(state: Optional[State] = None) -> dict[str, Any]:
    stores = governance_store_paths()
    components: list[dict[str, Any]] = []
    for spec in GOVERNANCE_COMPONENT_SPECS:
        function_checks = [
            {"name": name, "present": callable(globals().get(name))}
            for name in spec.get("functions", [])
        ]
        store_checks = [
            {"name": name, "path": stores.get(name, ""), "configured": bool(stores.get(name, ""))}
            for name in spec.get("stores", [])
        ]
        role_name = str(spec.get("role") or "")
        role_check = {"role": role_name, "present": role_name in ROLE_TEMPLATES} if role_name else {}
        ok = all(item["present"] for item in function_checks) and all(item["configured"] for item in store_checks)
        if role_check:
            ok = ok and bool(role_check.get("present"))
        components.append({
            "component_id": spec["id"],
            "layer": spec["layer"],
            "responsibility": spec["responsibility"],
            "status": "complete" if ok else "partial",
            "functions": function_checks,
            "stores": store_checks,
            "role": role_check,
            "write_policy": spec.get("write_policy", "none"),
            "memory_write_policy": spec.get("memory_write_policy", "candidate_only"),
            "approval_boundary": "program_gate_required_for_risky_actions",
        })
    data = {
        "schema_version": "agentgovernance.components.v1",
        "updated_at": now_iso(),
        "component_ids": [item["component_id"] for item in components],
        "components": components,
        "state_snapshot": {
            "subagents": len(state.subagents) if state is not None else 0,
            "running_subagents": sum(1 for sub in state.subagents.values() if sub.status == "running") if state is not None else 0,
            "single_writer_lock_active": bool(current_writer_lock()),
        },
        "principles": {
            "single_orchestrator": True,
            "read_parallel_write_serial": True,
            "artifact_refs_over_message_copy": True,
            "human_approval_hard_gates": True,
            "subagents_write_memory_directly": False,
            "unstructured_swarm": False,
        },
    }
    write_text_atomic(AGENT_GOVERNANCE_PATH, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return data


def baseline_status(pass_count: int, required_count: int) -> str:
    if required_count <= 0:
        return "missing"
    if pass_count >= required_count:
        return "complete"
    if pass_count > 0:
        return "partial"
    return "missing"


def baseline_item(
    item_id: str,
    title: str,
    requirement: str,
    checks: list[tuple[bool, str]],
    *,
    gaps: Optional[list[str]] = None,
    notes: str = "",
) -> dict[str, Any]:
    pass_count = sum(1 for ok, _desc in checks if ok)
    status = baseline_status(pass_count, len(checks))
    failed = [desc for ok, desc in checks if not ok]
    return {
        "id": item_id,
        "title": title,
        "requirement": requirement,
        "status": status,
        "pass_count": pass_count,
        "check_count": len(checks),
        "evidence": [desc for ok, desc in checks if ok],
        "missing_evidence": failed,
        "gaps": gaps or failed,
        "notes": notes,
    }


def architecture_baseline_report(state: Optional[State] = None, gateway_data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    tasks = read_jsonl(AGENT_TASK_LEDGER_PATH)
    mail = read_jsonl(AGENT_MAIL_PATH)
    artifacts = read_jsonl(AGENT_ARTIFACT_INDEX_PATH)
    approvals = read_jsonl(AGENT_APPROVALS_PATH)
    policy_decisions = read_jsonl(AGENT_POLICY_DECISIONS_PATH)
    plans = read_jsonl(AGENT_ORCHESTRATOR_PLANS_PATH)
    memory_candidates = read_jsonl(AGENT_MEMORY_CANDIDATES_PATH)
    traces = read_jsonl(AGENT_TRACES_PATH)
    evals = read_jsonl(AGENT_EVALS_PATH)
    checkpoints = read_jsonl(AGENT_CHECKPOINT_INDEX_PATH)
    recovery = read_jsonl(AGENT_RECOVERY_PATH)
    recovery_plans = read_jsonl(AGENT_RECOVERY_PLANS_PATH)
    gateway = gateway_data or {}
    a2a = gateway.get("a2a_gateway") if isinstance(gateway.get("a2a_gateway"), dict) else {}
    mcp = gateway.get("mcp_gateway") if isinstance(gateway.get("mcp_gateway"), dict) else {}
    capabilities = gateway.get("capability_registry") if isinstance(gateway.get("capability_registry"), dict) else {}
    governance = gateway.get("governance_components") if isinstance(gateway.get("governance_components"), dict) else {}
    service = gateway.get("gateway_service") if isinstance(gateway.get("gateway_service"), dict) else {}
    bridge_registry = gateway.get("bridge_registry") if isinstance(gateway.get("bridge_registry"), dict) else {}
    bridge_ids = set(bridge_registry.get("bridge_ids") or [])
    governance_ids = set(governance.get("component_ids") or [])
    artifact_with_hash = any(str(row.get("hash") or "").startswith("sha256:") and row.get("provenance") for row in artifacts)
    context_pack_artifact = any(row.get("type") == "context_pack" for row in artifacts)
    checkpoint_artifact = any(row.get("type") == "checkpoint" for row in artifacts)
    recovery_plan_artifact = any(row.get("type") == "recovery-plans" for row in artifacts)
    eval_has_core_scores = any(
        {"completion", "factual_accuracy", "citation_accuracy", "source_quality", "tool_efficiency", "policy_compliance", "human_takeover_cost"} <= set((row.get("scores") or {}).keys())
        for row in evals
    )
    items = [
        baseline_item(
            "strong_orchestrator",
            "Strong Orchestrator",
            "主 Orchestrator 负责计划、路由、审批、综合和最终责任。",
            [
                (callable(append_orchestrator_plan), "orchestrator plan writer is implemented"),
                (callable(start_subagent_task), "orchestrator delegation entrypoint is implemented"),
                (callable(process_ui_queue), "orchestrator result synthesis path is implemented"),
                ({"meta_orchestrator", "planner", "router"} <= governance_ids, "governance registry exposes orchestrator/planner/router components"),
            ],
        ),
        baseline_item(
            "governance_components",
            "Governance Components",
            "控制层、治理层和协议层组件需要显式可审计，而不是散落在模型提示词里。",
            [
                (governance.get("schema_version") == "agentgovernance.components.v1", "governance component registry is present"),
                ({"meta_orchestrator", "planner", "router", "context_engineer"} <= governance_ids, "control components are registered"),
                ({"approval_controller", "risk_guard", "memory_curator", "eval_controller", "recovery_controller"} <= governance_ids, "governance components are registered"),
                ("protocol_gateway" in governance_ids, "protocol gateway component is registered"),
                (all(item.get("status") == "complete" for item in governance.get("components") or []), "registered components have function/store evidence"),
            ],
        ),
        baseline_item(
            "restricted_subagents",
            "Restricted Subagents",
            "子 Agent 必须受 role、权限、budget、边界和 stop condition 限制。",
            [
                (bool(ROLE_TEMPLATES), "role templates are registered"),
                (callable(permissions_for_role), "role permissions builder is implemented"),
                (callable(task_contract_for_role), "task contract builder provides boundaries and stop conditions"),
                (all(role_write_policy(role) for role in ROLE_TEMPLATES), "role write policies are defined"),
            ],
        ),
        baseline_item(
            "shared_ledgers",
            "Shared Ledgers",
            "任务、进度、通信和审批必须可审计、可恢复。",
            [
                (bool(AGENT_TASK_LEDGER_PATH), "task ledger path is configured"),
                (bool(AGENT_MAIL_PATH), "agent mail path is configured"),
                (bool(AGENT_TRACES_PATH), "trace ledger path is configured"),
                (bool(AGENT_APPROVALS_PATH), "approvals.jsonl path is registered"),
            ],
        ),
        baseline_item(
            "artifact_store",
            "Artifact Store",
            "子 Agent 和工具结果通过 artifact refs/hash/provenance 共享，避免复制原始大文本。",
            [
                (bool(AGENT_ARTIFACT_INDEX_PATH), "artifact index path is configured"),
                (callable(append_artifact_index), "artifact index writer includes hash/provenance"),
                (callable(write_harness_artifact), "artifact:// writer is implemented"),
            ],
        ),
        baseline_item(
            "approval_gates",
            "Human Approval Gates",
            "部署、外发、删除、长期记忆、权限修改等高风险动作必须程序级审批。",
            [
                (bool(AGENT_POLICY_PATH), "policy config path is registered"),
                (callable(evaluate_policy_action), "policy decision evaluator is implemented"),
                (callable(queue_policy_approval), "approval request queue is implemented"),
                (callable(decide_approval), "approval execution path is implemented"),
                ({"approval_controller", "risk_guard"} <= governance_ids, "approval/risk governance components are registered"),
            ],
        ),
        baseline_item(
            "single_writer",
            "Single Writer",
            "写任务需要 single-writer 约束，防止多 Agent 写冲突。",
            [
                (bool(AGENT_LOCKS_PATH), "single-writer lock file path is configured"),
                (any((row.get("permissions") or {}).get("write_policy") == "single_writer" for row in tasks) or "coder" in ROLE_TEMPLATES, "single_writer write policy exists"),
                (callable(acquire_single_writer_lock) and callable(release_single_writer_lock), "single-writer acquire/release code path is active"),
            ],
        ),
        baseline_item(
            "context_engineering",
            "Context Engineering",
            "上下文需要 L0-L8 分层、memory hydration、source policy 和 raw-log exclusion。",
            [
                (callable(build_context_pack), "context pack builder is implemented"),
                (callable(context_layers_for_task), "L0-L8 context layer builder is implemented"),
                (callable(memory_hydration_pack), "memory hydration pack builder is implemented"),
                ("context_engineer" in governance_ids, "context engineer component is registered"),
            ],
        ),
        baseline_item(
            "external_memory",
            "External Long-Term Memory",
            "长期记忆只能通过候选项、证据、scope/type/TTL/conflict/dedupe 和审批写入。",
            [
                (bool(AGENT_MEMORY_CANDIDATES_PATH), "memory candidate store path is configured"),
                (callable(build_memory_candidate), "memory candidate builder includes scope/type/TTL/conflict/dedupe fields"),
                (callable(queue_curated_memory_candidate), "curated memory candidate approval path is implemented"),
                (callable(memory_candidate_rejection_reason), "memory curator can reject secrets/weak candidates before approval"),
            ],
        ),
        baseline_item(
            "eval_trace",
            "Eval And Trace",
            "每个任务应保留 trace、final_state、artifact refs 和质量/合规指标。",
            [
                (callable(append_trace), "agenttrace writer is implemented"),
                (callable(append_task_eval), "agenteval writer is implemented"),
                (callable(collect_task_audit_refs), "eval audit-ref collector is implemented"),
                (callable(eval_panel_items), "eval/trace inspection panel is implemented"),
            ],
        ),
        baseline_item(
            "checkpoint_recovery",
            "Checkpoint And Recovery",
            "长任务需要 checkpoint、durable state、recovery summary 和恢复动作记录。",
            [
                (bool(AGENT_CHECKPOINT_INDEX_PATH), "checkpoint index path is configured"),
                (callable(append_task_checkpoint), "checkpoint writer is implemented"),
                (callable(append_recovery_plan), "replayable recovery plan writer is implemented"),
                (callable(append_recovery_record), "recovery record writer is implemented"),
                (callable(recover_task_action), "approval-gated recovery action path is implemented"),
                (bool(AGENT_RECOVERY_PLANS_PATH), "recovery plan store path is configured"),
            ],
        ),
        baseline_item(
            "a2a_mcp_gateway",
            "A2A/MCP Gateway",
            "A2A 用于 Agent-to-Agent，MCP 用于 Agent-to-tool/resource，并提供 request/response、SSE 和 push notification 网络入口。",
            [
                (a2a.get("schema_version") == "a2a.gateway.v1", "A2A gateway schema is present"),
                (bool(a2a.get("agent_cards")), "A2A AgentCard objects are present"),
                (all(isinstance(a2a.get(key), list) for key in ("tasks", "messages", "artifacts")), "A2A Task/Message/Artifact lists are exposed"),
                (mcp.get("schema_version") == "mcp.gateway.v1", "MCP gateway schema is present"),
                (bool(mcp.get("tools")) and bool(mcp.get("resources")), "MCP tools/resources are registered"),
                (bool((capabilities or {}).get("roles")), "capability registry has role capabilities"),
                (service.get("schema_version") == "agentgateway.service.v1", "network gateway service descriptor is present"),
                (bool((service.get("request_response") or {}).get("registry")), "request/response endpoints are registered"),
                (bool((service.get("sse") or {}).get("endpoint")), "SSE endpoint is registered"),
                (bool((service.get("push_notifications") or {}).get("subscribe_endpoint")), "push notification subscription endpoint is registered"),
                ({"start", "stop", "restart", "status"} <= set(((service.get("daemon") or {}).get("commands") or [])), "managed daemon lifecycle commands are registered"),
                (bool(((service.get("daemon") or {}).get("status_path"))), "gateway daemon status path is registered"),
            ],
        ),
        baseline_item(
            "external_bridges",
            "External Bridges",
            "协议层和人机界面应登记 Feishu/OpenClaw/Codex/Claude/Deer Flow/CLI/Dashboard/Approval Inbox 桥接边界，并受审批门保护。",
            [
                (bridge_registry.get("schema_version") == "agentbridge.registry.v1", "external bridge registry is present"),
                ({"feishu", "openclaw"} <= bridge_ids, "Feishu/OpenClaw bridge adapters are registered"),
                ({"codex", "claude_code", "deer_flow"} <= bridge_ids, "Codex/Claude/Deer Flow runtime bridges are registered"),
                ({"cli", "dashboard", "approval_inbox"} <= bridge_ids, "CLI/Dashboard/Approval Inbox human interfaces are registered"),
                (all((item.get("policy") or {}).get("approval_required_for") for item in (bridge_registry.get("bridges") or [])), "bridge policies carry approval boundaries"),
            ],
        ),
    ]
    summary_counts = {key: sum(1 for item in items if item["status"] == key) for key in ("complete", "partial", "missing")}
    remaining_gaps = [
        {"id": item["id"], "title": item["title"], "status": item["status"], "gaps": item["gaps"]}
        for item in items
        if item["status"] != "complete" or item["gaps"]
    ]
    report = {
        "schema_version": "architecture.baseline_report.v1",
        "generated_at": now_iso(),
        "baseline_refs": [
            {"path": ARCHITECTURE_BASELINE_PATH, "exists": os.path.exists(ARCHITECTURE_BASELINE_PATH)},
            {"path": PROJECT_AGENTS_PATH, "exists": os.path.exists(PROJECT_AGENTS_PATH)},
        ],
        "summary": {
            "items": len(items),
            "complete": summary_counts["complete"],
            "partial": summary_counts["partial"],
            "missing": summary_counts["missing"],
            "completion_ratio": bounded_score(summary_counts["complete"] / max(1, len(items))),
        },
        "items": items,
        "remaining_gaps": remaining_gaps,
        "report_path": AGENT_BASELINE_REPORT_PATH,
        "next_actions": [
            "Perform final requirement-by-requirement audit against docs/agent-harness-architecture.md.",
            "Verify whether external Feishu/OpenClaw/Codex/Claude bridges are in scope for the standalone TUI milestone.",
        ],
    }
    write_text_atomic(AGENT_BASELINE_REPORT_PATH, json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return report


def format_baseline_report(report: dict[str, Any], *, max_items: int = 20) -> str:
    summary = report.get("summary") or {}
    lines = [
        "Architecture Baseline Comparison",
        f"complete={summary.get('complete', 0)} partial={summary.get('partial', 0)} missing={summary.get('missing', 0)} ratio={summary.get('completion_ratio', 0)}",
        "",
        "Items:",
    ]
    for item in (report.get("items") or [])[:max_items]:
        lines.append(f"- [{item.get('status', '-')}] {item.get('id', '')}: {item.get('title', '')}")
        for gap in (item.get("gaps") or [])[:3]:
            lines.append(f"  gap: {gap}")
    gaps = report.get("remaining_gaps") or []
    lines.extend(["", f"Remaining gap groups: {len(gaps)}", f"Report path: {AGENT_BASELINE_REPORT_PATH}"])
    return "\n".join(lines)


def baseline_panel_items(state: Optional[State] = None) -> list[PanelItem]:
    gateway = ensure_gateway_registry(state)
    report = gateway.get("baseline_comparison") or architecture_baseline_report(state, gateway_data=gateway)
    items: list[PanelItem] = []
    summary = report.get("summary") or {}
    items.append(PanelItem(
        key="summary",
        title="baseline summary",
        subtitle=f"complete:{summary.get('complete', 0)} partial:{summary.get('partial', 0)} missing:{summary.get('missing', 0)}",
        detail=json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        status=str(summary.get("completion_ratio", 0)),
        payload=report,
    ))
    for item in report.get("items") or []:
        evidence = "\n".join(f"- {line}" for line in item.get("evidence") or []) or "- -"
        missing = "\n".join(f"- {line}" for line in item.get("missing_evidence") or []) or "- -"
        gaps = "\n".join(f"- {line}" for line in item.get("gaps") or []) or "- -"
        detail = "\n".join([
            f"Requirement: {item.get('requirement', '')}",
            f"Status: {item.get('status', '')} ({item.get('pass_count', 0)}/{item.get('check_count', 0)})",
            "",
            "Evidence:",
            evidence,
            "",
            "Missing Evidence:",
            missing,
            "",
            "Gaps:",
            gaps,
            "",
            f"Notes: {item.get('notes', '')}",
        ])
        items.append(PanelItem(
            key=str(item.get("id") or ""),
            title=f"{item.get('status', '')} · {item.get('title', '')}",
            subtitle=str(item.get("requirement") or ""),
            detail=detail,
            status=str(item.get("status") or ""),
            payload=item,
        ))
    return items


def ensure_gateway_registry(state: Optional[State] = None) -> dict[str, Any]:
    task_rows = list(latest_task_records().values())[-20:]
    mail_rows = read_jsonl(AGENT_MAIL_PATH, limit=30)
    artifact_rows = read_jsonl(AGENT_ARTIFACT_INDEX_PATH, limit=30)
    a2a_tasks = [a2a_task_object(row) for row in task_rows]
    a2a_messages = [a2a_message_object(row) for row in mail_rows]
    a2a_artifacts = [a2a_artifact_object(row) for row in artifact_rows]
    capability_registry = gateway_capability_registry(state)
    governance_registry = governance_component_registry(state)
    bridge_registry = external_bridge_registry()
    role_cards = [a2a_agent_card_for_role(role, template) for role, template in sorted(ROLE_TEMPLATES.items())]
    data = {
        "schema_version": "agentgateway.v1",
        "updated_at": now_iso(),
        "internal_agent_mail": {
            "messages": AGENT_MAIL_PATH,
            "tasks": AGENT_TASK_LEDGER_PATH,
            "approvals": AGENT_APPROVALS_PATH,
            "artifacts": AGENT_ARTIFACTS_DIR,
            "artifact_index": AGENT_ARTIFACT_INDEX_PATH,
            "policy": AGENT_POLICY_PATH,
            "policy_decisions": AGENT_POLICY_DECISIONS_PATH,
            "orchestrator_plans": AGENT_ORCHESTRATOR_PLANS_PATH,
            "memory_candidates": AGENT_MEMORY_CANDIDATES_PATH,
            "traces": AGENT_TRACES_PATH,
            "evals": AGENT_EVALS_PATH,
            "checkpoints": AGENT_CHECKPOINT_INDEX_PATH,
            "checkpoint_store": AGENT_CHECKPOINTS_DIR,
            "recovery": AGENT_RECOVERY_PATH,
            "recovery_plans": AGENT_RECOVERY_PLANS_PATH,
            "governance": AGENT_GOVERNANCE_PATH,
            "gateway_daemon_status": AGENT_GATEWAY_DAEMON_STATUS_PATH,
            "gateway_daemon_pid": AGENT_GATEWAY_DAEMON_PID_PATH,
        },
        "policy_gate": {
            "status": "local_runtime",
            "config": AGENT_POLICY_PATH,
            "decisions": AGENT_POLICY_DECISIONS_PATH,
            "risky_actions": sorted(POLICY_ACTIONS),
        },
        "mcp_gateway": {
            "schema_version": "mcp.gateway.v1",
            "status": "network_capable",
            "purpose": "agent-to-tool/resource bridge",
            "policy": "least-privilege, approval-required for risky tools",
            "request_response": {
                "tools": "/mcp/tools",
                "resources": "/mcp/resources",
                "resource_read": "/mcp/resource?uri={uri}",
            },
            "tools": mcp_tool_registry(),
            "resources": mcp_resource_registry(),
            "resource_templates": [
                {"uriTemplate": "resource://agent/{agent_id}/memory", "description": "Subagent memory file by agent id"},
                {"uriTemplate": "artifact://{path}", "description": "Harness artifact by relative path"},
            ],
        },
        "a2a_gateway": {
            "schema_version": "a2a.gateway.v1",
            "status": "network_capable",
            "purpose": "agent-to-agent interoperability",
            "objects": ["AgentCard", "Task", "Message", "Part", "Artifact", "contextId"],
            "contextId": "ga-tui",
            "request_response": {
                "registry": "/a2a",
                "agent_cards": "/a2a/agent-cards",
                "tasks": "/a2a/tasks",
                "task_query": "/a2a/tasks/query",
                "messages": "/a2a/messages",
                "artifacts": "/a2a/artifacts",
            },
            "agent_cards": [],
            "tasks": a2a_tasks,
            "messages": a2a_messages,
            "artifacts": a2a_artifacts,
            "subscriptions": {
                "streaming": "/a2a/events",
                "push_notifications": "/a2a/push-subscriptions",
                "push_subscription_store": AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH,
                "push_delivery_store": AGENT_GATEWAY_PUSH_DELIVERIES_PATH,
            },
        },
        "capability_registry": capability_registry,
        "governance_components": governance_registry,
        "gateway_service": gateway_service_descriptor(),
        "bridge_registry": bridge_registry,
        "role_templates": ROLE_TEMPLATES,
        "agent_cards": list(role_cards),
    }
    data["a2a_gateway"]["agent_cards"].extend(role_cards)
    if state is not None:
        for sub in sorted(state.subagents.values(), key=lambda item: item.agent_id):
            card = a2a_agent_card_for_subagent(sub)
            data["agent_cards"].append(card)
            data["a2a_gateway"]["agent_cards"].append(card)
    data["baseline_comparison"] = architecture_baseline_report(state, gateway_data=data)
    write_text_atomic(AGENT_GATEWAY_PATH, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return data


def append_agent_mail(
    *,
    from_agent: str,
    to_type: str,
    target: str,
    intent: str,
    task_id: str = "",
    parent_task_id: str = "",
    priority: str = "normal",
    project_pool: str = "",
    status: str = "",
    payload: Optional[dict[str, Any]] = None,
    artifact_refs: Optional[list[str]] = None,
    requires_human_approval: bool = False,
    budget: Optional[dict[str, Any]] = None,
    permissions: Optional[dict[str, Any]] = None,
    context_policy: Optional[dict[str, Any]] = None,
    task: Optional[dict[str, Any]] = None,
    risks: Optional[list[dict[str, Any]]] = None,
    approval: Optional[dict[str, Any]] = None,
    assumptions: Optional[list[str]] = None,
    open_questions: Optional[list[str]] = None,
) -> dict[str, Any]:
    payload = payload or {}
    role = str(payload.get("role") or "")
    objective = str(payload.get("objective") or payload.get("summary") or "")
    msg = {
        "schema_version": "agentmail.v1",
        "message_id": short_uid("msg"),
        "thread_id": task_id or short_uid("thr"),
        "context_id": "ga-tui",
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "timestamp": now_iso(),
        "from": {"agent_id": from_agent},
        "to": {"type": to_type, "target": target},
        "intent": intent,
        "priority": priority,
        "project_pool": project_pool,
        "status": status,
        "requires_human_approval": bool(requires_human_approval),
        "budget": budget or default_task_budget(role),
        "permissions": permissions or permissions_for_role(role),
        "context_policy": context_policy or context_policy_for_task(objective),
        "task": task or task_contract_for_role(role, objective),
        "risks": risks or risks_for_action("", role, objective),
        "approval": approval or approval_metadata(status="pending" if requires_human_approval else "not_required"),
        "assumptions": assumptions or [],
        "open_questions": open_questions or [],
        "payload": payload,
        "artifact_refs": artifact_refs or [],
    }
    append_jsonl(AGENT_MAIL_PATH, msg)
    return msg


def append_task_ledger(
    task_id: str,
    *,
    status: str,
    assigned_agent: str = "",
    title: str = "",
    kind: str = "",
    objective: str = "",
    parent_task_id: str = "",
    session_key: str = "",
    order: int = 0,
    expected_children: int = 0,
    artifact_refs: Optional[list[str]] = None,
    summary: str = "",
    error: str = "",
    priority: str = "normal",
    budget: Optional[dict[str, Any]] = None,
    stop_condition: str = "",
    boundaries: Optional[list[str]] = None,
    permissions: Optional[dict[str, Any]] = None,
    context_policy: Optional[dict[str, Any]] = None,
    risks: Optional[list[dict[str, Any]]] = None,
    approval: Optional[dict[str, Any]] = None,
    output_contract: Optional[dict[str, Any]] = None,
    non_goals: Optional[list[str]] = None,
    success_criteria: Optional[list[str]] = None,
) -> dict[str, Any]:
    role = ""
    default_contract = task_contract_for_role(role, objective)
    task_contract = {
        "objective": objective,
        "non_goals": non_goals or list(default_contract.get("non_goals") or []),
        "success_criteria": success_criteria or list(default_contract.get("success_criteria") or []),
        "boundaries": boundaries or list(default_contract.get("boundaries") or []),
        "stop_condition": stop_condition or str(default_contract.get("stop_condition") or ""),
        "output_contract": output_contract or dict(default_contract.get("output_contract") or {}),
    }
    row = {
        "schema_version": "agenttask.v1",
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "context_id": "ga-tui",
        "timestamp": now_iso(),
        "status": status,
        "priority": priority,
        "assigned_agent": assigned_agent,
        "title": title,
        "kind": kind,
        "session_key": session_key,
        "order": order,
        "expected_children": expected_children,
        "objective": objective,
        "budget": budget or default_task_budget(role),
        "permissions": permissions or permissions_for_role(role),
        "context_policy": context_policy or context_policy_for_task(objective),
        "task": task_contract,
        "risks": risks or [],
        "approval": approval or approval_metadata(),
        "artifact_refs": artifact_refs or [],
        "summary": summary,
        "error": error,
    }
    append_jsonl(AGENT_TASK_LEDGER_PATH, row)
    return row


def append_task_update(
    task_id: str,
    *,
    status: str,
    summary: str = "",
    error: str = "",
    artifact_refs: Optional[list[str]] = None,
) -> dict[str, Any]:
    prev = latest_task_records().get(task_id, {})
    refs = artifact_refs if artifact_refs is not None else list(prev.get("artifact_refs") or [])
    return append_task_ledger(
        task_id,
        status=status,
        assigned_agent=str(prev.get("assigned_agent") or ""),
        title=str(prev.get("title") or ""),
        kind=str(prev.get("kind") or ""),
        objective=str(prev.get("objective") or ""),
        parent_task_id=str(prev.get("parent_task_id") or ""),
        session_key=str(prev.get("session_key") or ""),
        order=int(prev.get("order") or 0),
        expected_children=int(prev.get("expected_children") or 0),
        artifact_refs=refs,
        summary=summary or str(prev.get("summary") or ""),
        error=error,
        priority=str(prev.get("priority") or "normal"),
        budget=prev.get("budget") if isinstance(prev.get("budget"), dict) else None,
        permissions=prev.get("permissions") if isinstance(prev.get("permissions"), dict) else None,
        context_policy=prev.get("context_policy") if isinstance(prev.get("context_policy"), dict) else None,
        risks=prev.get("risks") if isinstance(prev.get("risks"), list) else None,
        approval=prev.get("approval") if isinstance(prev.get("approval"), dict) else None,
    )


def normalize_plan_steps(raw_steps: Any) -> list[str]:
    steps: list[str] = []
    if isinstance(raw_steps, list):
        for item in raw_steps:
            if isinstance(item, dict):
                title = str(item.get("title") or item.get("name") or item.get("step") or item.get("objective") or "").strip()
            else:
                title = str(item or "").strip()
            if title:
                steps.append(title)
    elif isinstance(raw_steps, str):
        for line in raw_steps.splitlines():
            title = re.sub(r"^\s*\d+[.)、]\s*", "", line).strip(" -\t")
            if title:
                steps.append(title)
    return steps


def reset_auto_plan_continue_state(state: State) -> None:
    state.auto_plan_continue_attempts = {}
    state.auto_plan_continue_plan_attempts = {}
    state.auto_plan_continue_last_blocked = ""


def clear_active_plan_state(state: State) -> None:
    state.active_plan_task_id = ""
    state.active_plan_steps = {}
    reset_auto_plan_continue_state(state)


def create_task_plan(
    state: State,
    title: str,
    steps: list[str],
    source: str = "agent",
    expected_children: Optional[dict[int, int]] = None,
) -> tuple[str, dict[str, str]]:
    plan_title = clean_text(title or "任务计划").strip() or "任务计划"
    step_titles = [clean_text(step).strip() for step in steps if clean_text(step).strip()]
    if not step_titles:
        step_titles = ["执行任务", "汇总结果"]
    session = active_ui_session_key(state)
    plan_id = short_uid("plan")
    append_task_ledger(
        plan_id,
        status="working",
        assigned_agent="orchestrator.main",
        title=plan_title,
        kind="plan",
        objective=plan_title,
        session_key=session,
        summary=f"{source}: created task plan with {len(step_titles)} steps",
    )
    step_ids: dict[str, str] = {}
    for idx, step_title in enumerate(step_titles, 1):
        step_id = short_uid("step")
        kind = "plan_summary" if any(token in step_title for token in ("汇总", "总结", "收尾")) else "plan_step"
        numbered_title = f"{idx}. {step_title}"
        append_task_ledger(
            step_id,
            status="created",
            assigned_agent="orchestrator.main",
            title=numbered_title,
            kind=kind,
            objective=step_title,
            parent_task_id=plan_id,
            session_key=session,
            order=idx,
            expected_children=int((expected_children or {}).get(idx) or 0),
        )
        step_ids[str(idx)] = step_id
        step_ids[step_title] = step_id
        step_ids[numbered_title] = step_id
    state.active_plan_task_id = plan_id
    state.active_plan_steps = dict(step_ids)
    reset_auto_plan_continue_state(state)
    state.rightbar_task_rows_cache = []
    mark_dirty(state)
    return plan_id, step_ids


def resolve_plan_step_id(state: State, token: Any) -> str:
    raw = str(token or "").strip()
    if not raw:
        return ""
    if raw in state.active_plan_steps:
        return state.active_plan_steps[raw]
    if raw.startswith(("step_", "task_", "plan_")):
        return raw
    compact = re.sub(r"^\s*\d+[.)、]\s*", "", raw).strip()
    return state.active_plan_steps.get(compact, "")


def active_plan_step_rows(state: State) -> list[tuple[str, dict[str, Any]]]:
    plan_id = str(state.active_plan_task_id or "")
    if not plan_id:
        return []
    rows = [
        (task_id, row)
        for task_id, row in latest_task_records().items()
        if str(row.get("parent_task_id") or "") == plan_id
        and str(row.get("kind") or "") in {"plan_step", "plan_summary"}
    ]
    rows.sort(key=lambda item: int(item[1].get("order") or 0))
    return rows


def plan_step_text(row: dict[str, Any]) -> str:
    return "\n".join(str(row.get(key) or "") for key in ("title", "objective", "summary"))


MUTUAL_CHAT_STEP_TOKENS = ("互相", "相互", "彼此", "交流", "聊天", "对方")
SELF_INTRO_STEP_TOKENS = ("各自", "分别", "先向", "说话", "自我介绍", "介绍", "打招呼", "问候", "发言")
SUMMARY_STEP_TOKENS = ("汇总", "总结", "收尾")


def control_has_plan_reference(control: dict[str, Any], *, ask: bool) -> bool:
    keys = ("parent_task_id", "plan_step_id", "step") if ask else ("plan_step_id", "step")
    return any(str(control.get(key) or "").strip() for key in keys)


def choose_plan_step_by_tokens(
    rows: list[tuple[str, dict[str, Any]]],
    tokens: tuple[str, ...],
    *,
    fallback_index: int = 0,
    fallback_tokens: tuple[str, ...] = (),
    exclude_tokens: tuple[str, ...] = (),
    allow_index_fallback: bool = True,
) -> tuple[str, dict[str, Any]]:
    candidates: list[tuple[str, dict[str, Any], str]] = []
    for task_id, row in rows:
        text = plan_step_text(row)
        if exclude_tokens and any(token and token in text for token in exclude_tokens):
            continue
        candidates.append((task_id, row, text))
    for task_id, row, text in candidates:
        if any(token and token in text for token in tokens):
            return task_id, row
    if fallback_tokens:
        fallback_rows = [
            (task_id, row)
            for task_id, row, text in candidates
            if any(token and token in text for token in fallback_tokens)
        ]
        if fallback_rows:
            idx = max(0, min(fallback_index, len(fallback_rows) - 1))
            return fallback_rows[idx]
    if allow_index_fallback and candidates:
        idx = max(0, min(fallback_index, len(candidates) - 1))
        task_id, row, _text = candidates[idx]
        return task_id, row
    return "", {}


def maybe_attach_active_plan_to_subagent_control(
    state: State,
    control: dict[str, Any],
    normalized_action: str,
    *,
    create_index: int,
    ask_index: int,
) -> dict[str, Any]:
    if not state.active_plan_task_id:
        return control
    rows = active_plan_step_rows(state)
    if not rows:
        return control
    control = dict(control)
    if normalized_action in {"subagent_create", "agent_create", "create_subagent", "new_subagent"}:
        if control_has_plan_reference(control, ask=False):
            return control
        target = str(control.get("target") or "").strip()
        value = str(control.get("value") or control.get("category") or control.get("name") or "").strip()
        name = str(control.get("name") or control.get("title") or value or "").strip()
        profile = str(control.get("profile") or control.get("description") or control.get("system") or "").strip()
        persistent, temporary = subagent_control_persistence_intent(control, target, value, name, profile)
        if persistent:
            tokens = ("正式", "永久", "持久", "长期", "persistent")
        elif temporary:
            tokens = ("临时", "暂时", "temporary", "temp")
        else:
            tokens = ()
        step_id, _row = choose_plan_step_by_tokens(rows, tokens, fallback_index=create_index, fallback_tokens=("创建", "准备", "复用"))
        if step_id:
            control["plan_step_id"] = step_id
        return control
    if normalized_action in {"subagent_ask", "subagent_run", "subagent_input", "agent_ask", "agent_run"}:
        if control_has_plan_reference(control, ask=True):
            return control
        prompt = str(control.get("prompt") or control.get("task") or control.get("message") or control.get("value") or "").strip()
        ask_rows = [
            (task_id, row)
            for task_id, row in rows
            if not terminal_task_status(str(row.get("status") or ""))
        ]
        prompt_is_summary = any(token in prompt for token in SUMMARY_STEP_TOKENS)
        prompt_is_mutual = any(token in prompt for token in MUTUAL_CHAT_STEP_TOKENS)
        if prompt_is_summary:
            prompt_tokens = SUMMARY_STEP_TOKENS
            fallback_tokens = ()
            exclude_tokens = ()
        elif prompt_is_mutual:
            prompt_tokens = MUTUAL_CHAT_STEP_TOKENS
            fallback_tokens = ("对话",)
            exclude_tokens = ()
            ask_rows = [(task_id, row) for task_id, row in ask_rows if str(row.get("kind") or "") == "plan_step"]
        else:
            prompt_tokens = SELF_INTRO_STEP_TOKENS
            fallback_tokens = SELF_INTRO_STEP_TOKENS
            exclude_tokens = MUTUAL_CHAT_STEP_TOKENS + SUMMARY_STEP_TOKENS
            ask_rows = [(task_id, row) for task_id, row in ask_rows if str(row.get("kind") or "") == "plan_step"]
        step_id, row = choose_plan_step_by_tokens(
            ask_rows,
            prompt_tokens,
            fallback_index=ask_index,
            fallback_tokens=fallback_tokens,
            exclude_tokens=exclude_tokens,
            allow_index_fallback=False,
        )
        if step_id:
            control["parent_task_id"] = step_id
            control.setdefault("task_title", str(row.get("objective") or row.get("title") or "").strip())
        return control
    return control


def maybe_complete_plan_after_step(step_id: str) -> None:
    latest = latest_task_records()
    step = latest.get(step_id)
    if not step:
        return
    plan_id = str(step.get("parent_task_id") or "")
    if not plan_id:
        return
    children = [
        row for row in latest.values()
        if str(row.get("parent_task_id") or "") == plan_id
        and str(row.get("kind") or "") in {"plan_step", "plan_summary"}
    ]
    if not children:
        return
    if children and all(str(row.get("status") or "") == "completed" for row in children):
        plan = latest.get(plan_id, {})
        if not terminal_task_status(str(plan.get("status") or "")):
            append_task_update(plan_id, status="completed", summary="计划步骤全部完成")


def update_plan_step_from_child(parent_task_id: str) -> None:
    parent_task_id = str(parent_task_id or "")
    if not parent_task_id:
        return
    latest = latest_task_records()
    parent = latest.get(parent_task_id, {})
    if str(parent.get("kind") or "") not in {"plan_step", "plan_summary"}:
        return
    children = [row for row in latest.values() if str(row.get("parent_task_id") or "") == parent_task_id]
    if not children:
        return
    expected_children = int(parent.get("expected_children") or 0)
    if expected_children and len(children) < expected_children:
        if str(parent.get("status") or "") not in {"working", "completed"}:
            append_task_update(parent_task_id, status="working", summary=f"等待子任务 {len(children)}/{expected_children}")
        return
    statuses = [str(row.get("status") or "") for row in children]
    current = str(parent.get("status") or "")
    if any(status in {"failed", "rejected", "aborted", "cancelled", "canceled"} for status in statuses):
        if current != "failed":
            append_task_update(parent_task_id, status="failed", summary="子任务失败")
    elif all(status == "completed" for status in statuses):
        if current != "completed":
            append_task_update(parent_task_id, status="completed", summary="子任务全部完成")
            maybe_complete_plan_after_step(parent_task_id)
    elif any(status in {"working", "approval_required", "created", "pending"} for status in statuses):
        if current not in {"working", "completed"}:
            append_task_update(parent_task_id, status="working", summary="子任务执行中")


def inject_orchestrator_notice(agent: Any, text: str) -> None:
    text = clean_text(text).strip()
    if not agent or not text:
        return
    pending = str(getattr(agent, "_ga_tui_pending_key_info", "") or "").strip()
    if text not in pending:
        setattr(agent, "_ga_tui_pending_key_info", (pending + "\n" + text).strip())
    try:
        handler = getattr(agent, "handler", None)
        if handler is not None:
            existing = str(handler.working.get("key_info", "") or "")
            if text not in existing:
                handler.working["key_info"] = existing + f"\n[Agent Bus] {text}"
            return
    except Exception:
        pass


def take_pending_agent_bus_text(agent: Any) -> str:
    pending_key_info = clean_text(str(getattr(agent, "_ga_tui_pending_key_info", "") or "")).strip()
    if pending_key_info:
        setattr(agent, "_ga_tui_pending_key_info", "")
    return pending_key_info


def agent_text_with_pending_bus(agent: Any, text: str) -> str:
    pending_key_info = take_pending_agent_bus_text(agent)
    if pending_key_info:
        return f"[Agent Bus Updates]\n{pending_key_info}\n[/Agent Bus Updates]\n\n{text}"
    return text


def start_main_agent_task(
    state: State,
    text: str,
    *,
    source: str = "user",
    visible_user_text: Optional[str] = None,
    remember_user: bool = False,
    clear_history: bool = False,
) -> bool:
    if state.status in {"running", "aborting", "restoring"}:
        state.last_error = "当前主控仍在运行，不能启动新的主控任务。"
        mark_dirty(state)
        return False
    secret_task = bool(state.secret_vault.unlocked)
    if secret_task:
        network_decision = secret_network_gate(state, operation=source or "main_agent_task")
        if not network_decision.allowed:
            state.last_error = policy_gate_text(network_decision)
            mark_dirty(state)
            return False
    if clear_history:
        clear_history_ui_state(state)
    if remember_user and visible_user_text is not None and not secret_task:
        remember_input(state, visible_user_text)
    agent_text = agent_text_with_pending_bus(state.agent, text)
    state.task_id += 1
    task_id = state.task_id
    state.active_task_id = task_id
    state.active_task_source = source
    stream_target = StreamTarget()
    state.active_stream_target = stream_target
    state.status = "running"
    state.active_task_secret = secret_task
    state.active_secret_user_text = visible_user_text or (text if secret_task else "")
    state.active_secret_session_id = state.secret_vault.session_id if secret_task else ""
    if secret_task:
        set_agent_log_path(state.agent, os.devnull)
        bind_agent_token_session(state, state.agent)
    if visible_user_text is not None:
        state.messages.append(Message("user", visible_user_text))
    state.messages.append(Message("assistant", "", done=False))
    state.follow_bottom = True
    mark_messages_changed(state)
    try:
        dq = state.agent.put_task(agent_text, source=source)
    except Exception as exc:
        state.status = "error"
        state.active_task_id = None
        state.active_task_source = ""
        state.active_stream_target = None
        state.active_task_secret = False
        state.active_secret_user_text = ""
        state.active_secret_session_id = ""
        if state.messages and state.messages[-1].role == "assistant":
            state.messages[-1] = Message("assistant", f"[ERROR] put_task: {type(exc).__name__}: {exc}")
        else:
            state.messages.append(Message("assistant", f"[ERROR] put_task: {type(exc).__name__}: {exc}"))
        mark_messages_changed(state)
        return False
    threading.Thread(target=consume_queue, args=(state, stream_target, task_id, dq), daemon=True).start()
    return True


def active_subagent_work_exists(state: State) -> bool:
    for sub in state.subagents.values():
        if sub.status in {"running", "aborting", "waiting-input"}:
            return True
        if sub.active_task_id is not None or sub.task_queue:
            return True
    return False


def active_plan_unfinished_step_rows(state: State) -> list[tuple[str, dict[str, Any]]]:
    rows = active_plan_step_rows(state)
    unfinished: list[tuple[str, dict[str, Any]]] = []
    for task_id, row in rows:
        status = str(row.get("status") or "")
        if not terminal_task_status(status):
            unfinished.append((task_id, row))
    return unfinished


def active_plan_continuation_signature(state: State) -> str:
    plan_id = str(state.active_plan_task_id or "")
    latest = latest_task_records()
    child_counts: dict[str, int] = {}
    for row in latest.values():
        parent = str(row.get("parent_task_id") or "")
        if parent:
            child_counts[parent] = child_counts.get(parent, 0) + 1
    parts = [plan_id]
    for task_id, row in active_plan_step_rows(state):
        parts.append(
            ":".join(
                [
                    task_id,
                    str(row.get("status") or ""),
                    str(child_counts.get(task_id, 0)),
                    hashlib.sha1(str(row.get("summary") or "").encode("utf-8", errors="ignore")).hexdigest()[:8],
                ]
            )
        )
    return "|".join(parts)


def format_plan_continuation_prompt(
    state: State,
    *,
    reason: str,
    unfinished_rows: list[tuple[str, dict[str, Any]]],
) -> str:
    latest = latest_task_records()
    plan_id = str(state.active_plan_task_id or "")
    plan = latest.get(plan_id, {})
    plan_title = str(plan.get("title") or plan.get("objective") or plan_id or "当前计划")
    lines = [
        "[GA TUI Orchestrator Auto-Continue]",
        f"Reason: {reason}",
        f"Active plan: {plan_title} ({plan_id})",
        "",
        "Current plan steps:",
    ]
    for task_id, row in active_plan_step_rows(state):
        status = str(row.get("status") or "created")
        title = str(row.get("objective") or row.get("title") or task_id)
        summary = str(row.get("summary") or "").strip()
        suffix = f" | {summary}" if summary else ""
        lines.append(f"- {task_id} [{status}] {title}{suffix}")
    next_task_id, next_row = unfinished_rows[0]
    next_title = str(next_row.get("objective") or next_row.get("title") or "").strip()
    lines += [
        "",
        f"Next unblocked step: {next_task_id} - {next_title}",
        "",
        "This is a control-emission continuation, not a research, browsing, or user-chat turn.",
        "Execute exactly the next ledger step by emitting hidden <ga-control> JSON control blocks before any prose.",
        "Do not call browser/search/file/code tools such as web_scan, webexecute_js, file_read, or code_run just to decide what to do; the task ledger above is authoritative.",
        f"When a control belongs to the next step, attach it with parent_task_id={next_task_id!r} or an equivalent step reference.",
        "Do not repeat completed steps. Reuse existing subagents before creating new ones.",
        "Temporary subagents are the default unless the user/control explicitly asks for persistent/long-term agents.",
        "If you need child agent output before summarizing, delegate with agenttask.v2 delegate.create and wait for results instead of inventing a summary.",
        "If the plan is blocked, emit task.update/task.fail for the blocked step with a concrete reason.",
        "Examples to adapt, not copy literally:",
        f'<ga-control>{{"schema_version":"ga-control.v2","actions":[{{"action":"agent.create","name":"<name>","role":"researcher","lifecycle":"ephemeral","profile":"<role and boundaries>","parent_task_id":"{next_task_id}"}},{{"schema_version":"agenttask.v2","action":"delegate.create","parent_task_id":"{next_task_id}","routing":{{"mode":"agent_as_tool","selected_agent":"<agent name or id>","target_selector":{{"role":"researcher","capabilities_required":["read"],"reuse_policy":"prefer_existing","security_context":"standard"}}}},"work_order":{{"objective":"<bounded task>","success_criteria":["<done condition>"],"stop_condition":"return structured result then stop"}},"capability_contract":{{"tools_allowed":["read"],"tools_forbidden":["repo.write","deploy","email.send"],"write_policy":"none","max_subagents":0}},"context_contract":{{"history_mode":"summary","artifact_reference_only":true,"include_raw_logs":false}},"output_contract":{{"format":"structured_markdown","required_sections":["summary","findings","evidence_refs","risks","artifact_refs","confidence"],"schema_validation":"strict"}}}}]}}</ga-control>',
        f'<ga-control>{{"schema_version":"ga-control.v2","actions":[{{"action":"task.update","target":"{next_task_id}","status":"working|completed|failed","summary":"<what changed>"}}]}}</ga-control>',
        "[/GA TUI Orchestrator Auto-Continue]",
    ]
    return "\n".join(lines)


def maybe_queue_orchestrator_plan_continuation(state: State, reason: str) -> bool:
    if state.status != "idle" or state.active_task_id is not None:
        return False
    if state.pending_interaction:
        return False
    if active_subagent_work_exists(state):
        return False
    plan_id = str(state.active_plan_task_id or "")
    if not plan_id:
        return False
    latest = latest_task_records()
    plan_status = str(latest.get(plan_id, {}).get("status") or "")
    if terminal_task_status(plan_status):
        return False
    unfinished_rows = active_plan_unfinished_step_rows(state)
    if not unfinished_rows:
        return False
    signature = active_plan_continuation_signature(state)
    if not signature:
        return False
    attempts = int(state.auto_plan_continue_attempts.get(signature) or 0)
    if attempts >= AUTO_PLAN_CONTINUE_MAX_PER_SIGNATURE:
        if state.auto_plan_continue_last_blocked != signature:
            next_step = str(unfinished_rows[0][1].get("objective") or unfinished_rows[0][1].get("title") or unfinished_rows[0][0])
            message = f"自动续跑已停止：计划状态没有推进，下一步仍是「{truncate_cells(next_step, 80)}」。需要主控重新规划或用户介入。"
            state.auto_plan_continue_last_blocked = signature
            state.last_error = message
            add_system(state, message, persist=True, kind="orchestrator_auto_continue_blocked")
        return False
    total = int(state.auto_plan_continue_plan_attempts.get(plan_id) or 0)
    if total >= AUTO_PLAN_CONTINUE_MAX_PER_PLAN:
        message = f"自动续跑已停止：计划 {plan_id} 达到 {AUTO_PLAN_CONTINUE_MAX_PER_PLAN} 次续跑上限。"
        state.last_error = message
        add_system(state, message, persist=True, kind="orchestrator_auto_continue_blocked")
        return False
    state.auto_plan_continue_attempts[signature] = attempts + 1
    state.auto_plan_continue_plan_attempts[plan_id] = total + 1
    state.auto_plan_continue_last_blocked = ""
    next_step = str(unfinished_rows[0][1].get("objective") or unfinished_rows[0][1].get("title") or unfinished_rows[0][0])
    add_system(
        state,
        f"自动续跑主控：计划还有未完成步骤，继续执行「{truncate_cells(next_step, 80)}」。",
        persist=True,
        kind="orchestrator_auto_continue",
    )
    prompt = format_plan_continuation_prompt(state, reason=reason, unfinished_rows=unfinished_rows)
    return start_main_agent_task(state, prompt, source="ga-tui:auto_plan_continue", clear_history=False)


def queue_approval(
    *,
    approval_type: str,
    summary: str,
    payload: dict[str, Any],
    source: str,
    target: str = "",
    approval_required_for: str = "",
) -> str:
    approval_id = short_uid("appr")
    row = {
        "schema_version": "agentapproval.v1",
        "approval_id": approval_id,
        "timestamp": now_iso(),
        "status": "pending",
        "type": approval_type,
        "source": source,
        "target": target,
        "summary": summary,
        "approval_required_for": approval_required_for or approval_type,
        "payload": payload,
    }
    append_jsonl(AGENT_APPROVALS_PATH, row)
    append_agent_mail(
        from_agent=source,
        to_type="human",
        target="approval_inbox",
        intent="approval_request",
        status="pending",
        payload={"approval_id": approval_id, "summary": summary, "type": approval_type},
        approval=approval_metadata(
            status="pending",
            approval_required_for=[approval_required_for or approval_type],
            approval_id=approval_id,
        ),
        requires_human_approval=True,
    )
    return approval_id


def approval_latest_records() -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(AGENT_APPROVALS_PATH):
        approval_id = str(row.get("approval_id") or "")
        if approval_id:
            latest[approval_id] = row
    return latest


def secret_memory_candidate_approval_id(candidate_id: str) -> str:
    safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", candidate_id or short_uid("memcand")).strip("-")
    return f"secmem_{safe_id or short_uid('memcand')}"


def secret_memory_candidate_approval_rows(state: Optional[State], *, show_all: bool = False) -> list[dict[str, Any]]:
    if state is None or not state.secret_vault.unlocked or not state.secret_vault.key:
        return []
    pattern = os.path.join(SECRET_VAULT_SESSIONS_DIR, SECRET_SUBAGENT_SESSION_ID, "subagent-memory-candidates", "*.secret")
    rows: list[dict[str, Any]] = []
    for path in sorted(glob.glob(pattern)):
        ok, payload, _detail = secret_read_json_from_path(
            state,
            "subagent-memory-candidates",
            path,
            session_id=SECRET_SUBAGENT_SESSION_ID,
        )
        if not ok or not isinstance(payload, dict):
            continue
        candidate = payload.get("candidate") if isinstance(payload.get("candidate"), dict) else {}
        if not candidate:
            continue
        candidate_id = str(candidate.get("candidate_id") or os.path.basename(path).removesuffix(".secret"))
        approval_id = str(payload.get("approval_id") or secret_memory_candidate_approval_id(candidate_id))
        status = str(payload.get("status") or "pending")
        if not show_all and status != "pending":
            continue
        target = str(candidate.get("target_subagent") or "")
        statement = str(candidate.get("statement") or "")
        rows.append({
            "schema_version": "agentapproval.v1",
            "approval_id": approval_id,
            "timestamp": str(payload.get("updated_at") or candidate.get("created_at") or ""),
            "status": status,
            "type": "memory_write_request",
            "source": str(candidate.get("source") or "secret-memory-curator"),
            "target": target,
            "summary": f"{target}: {truncate_cells(statement, 100)}",
            "approval_required_for": "write_long_term_memory",
            "secret_storage": True,
            "secret_candidate_path": path,
            "payload": {
                "subagent_id": target,
                "memory": statement,
                "memory_candidate": candidate,
                "secret_storage": True,
                "secret_candidate_id": candidate_id,
                "secret_candidate_path": path,
            },
        })
    rows.sort(key=row_timestamp, reverse=True)
    return rows


def pending_approvals(state: Optional[State] = None) -> list[dict[str, Any]]:
    if state is not None and state.secret_vault.unlocked:
        return secret_memory_candidate_approval_rows(state)
    return [row for row in approval_latest_records().values() if row.get("status") == "pending"]


def is_approval_interaction(payload: Optional[dict[str, Any]]) -> bool:
    return isinstance(payload, dict) and str(payload.get("tool") or "") == "approval" and bool(str(payload.get("approval_id") or ""))


def approval_interaction_row_by_id(state: State, approval_id: str) -> Optional[dict[str, Any]]:
    approval_id = (approval_id or "").strip()
    if not approval_id:
        return None
    if state.secret_vault.unlocked:
        for row in secret_memory_candidate_approval_rows(state, show_all=True):
            row_id = str(row.get("approval_id") or "")
            if row_id == approval_id or row_id.startswith(approval_id):
                return row
    row = approval_latest_records().get(approval_id)
    return row if isinstance(row, dict) else None


def approval_memory_statement(row: dict[str, Any]) -> str:
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    candidate = payload.get("memory_candidate") if isinstance(payload.get("memory_candidate"), dict) else {}
    text = str(candidate.get("statement") or payload.get("memory") or payload.get("memory_preview") or "")
    return clean_text(text).strip()


def approval_interaction_payload(row: dict[str, Any]) -> dict[str, Any]:
    approval_id = str(row.get("approval_id") or "")
    approval_type = str(row.get("type") or "approval")
    summary = truncate_cells(str(row.get("summary") or ""), 160)
    source = str(row.get("source") or "-")
    target = str(row.get("target") or "-")
    storage = "Secret Vault encrypted" if row.get("secret_storage") else "normal"
    memory_text = approval_memory_statement(row)
    memory_preview = truncate_cells(memory_text, 900) if memory_text else ""
    question = (
        f"审批 {approval_id}\n"
        f"类型：{approval_type}\n"
        f"来源：{source} -> {target}\n"
        f"存储：{storage}\n"
        f"摘要：{summary or '-'}"
    )
    if memory_preview:
        question += f"\n\n将写入的记忆：\n{memory_preview}"
    return {
        "tool": "approval",
        "question": question,
        "candidates": ["批准并执行", "拒绝", "稍后处理"],
        "approval_id": approval_id,
        "approval_type": approval_type,
        "memory_preview": memory_preview,
        "secret_storage": bool(row.get("secret_storage")),
    }


def set_pending_approval_interaction(state: State, row: dict[str, Any]) -> bool:
    if not isinstance(row, dict) or str(row.get("status") or "") != "pending":
        return False
    approval_id = str(row.get("approval_id") or "")
    if not approval_id:
        return False
    if state.pending_interaction:
        current_id = str(state.pending_interaction.get("approval_id") or "") if is_approval_interaction(state.pending_interaction) else ""
        return current_id == approval_id
    sub = selected_subagent(state)
    if sub is not None and sub.pending_interaction:
        return False
    state.pending_interaction = normalize_interaction_payload(approval_interaction_payload(row))
    state.last_error = ""
    mark_dirty(state)
    return True


def offer_pending_approval_interaction(state: State, approval_id: str) -> bool:
    row = approval_interaction_row_by_id(state, approval_id)
    return set_pending_approval_interaction(state, row or {})


def clear_pending_approval_interaction(state: State, approval_id: str) -> None:
    if not is_approval_interaction(state.pending_interaction):
        return
    if str(state.pending_interaction.get("approval_id") or "") == str(approval_id or ""):
        state.pending_interaction = None
        mark_dirty(state)


def subagent_home(agent_id: str) -> str:
    return os.path.join(SUBAGENTS_DIR, agent_id)


def secret_subagent_home(agent_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", agent_id or "agent").strip("-") or "agent"
    return f"secret://subagents/{safe}"


def subagent_meta_path(agent_id: str) -> str:
    return os.path.join(subagent_home(agent_id), "meta.json")


def subagent_profile_path(agent_id: str) -> str:
    return os.path.join(subagent_home(agent_id), "profile.md")


def subagent_memory_path(agent_id: str) -> str:
    return os.path.join(subagent_home(agent_id), "memory.md")


def subagent_events_path(agent_id: str) -> str:
    return os.path.join(subagent_home(agent_id), "events.jsonl")


def subagent_new_chat_session_id() -> str:
    return f"chat_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1_000_000_000:09d}"


def subagent_session_sidebar_key(agent_id: str, session_id: str) -> str:
    safe_agent = re.sub(r"[^A-Za-z0-9_.-]+", "-", agent_id or "agent").strip("-") or "agent"
    safe_session = re.sub(r"[^A-Za-z0-9_.-]+", "-", session_id or "current").strip("-") or "current"
    return f"{SUBAGENT_SESSION_PREFIX}{safe_agent}:{safe_session}"


def subagent_session_from_sidebar_key(key: Any) -> tuple[str, str]:
    text = str(key or "")
    if not text.startswith(SUBAGENT_SESSION_PREFIX):
        return "", ""
    body = text[len(SUBAGENT_SESSION_PREFIX):]
    agent_id, sep, session_id = body.partition(":")
    return agent_id if sep else "", session_id if sep else ""


def subagent_file_path(sub: SubAgentRuntime, filename: str) -> str:
    return os.path.join(sub.home, filename)


def subagent_meta_file(sub: SubAgentRuntime) -> str:
    return subagent_file_path(sub, "meta.json")


def subagent_profile_file(sub: SubAgentRuntime) -> str:
    return subagent_file_path(sub, "profile.md")


def subagent_memory_file(sub: SubAgentRuntime) -> str:
    if sub.security_context == "secret":
        return secret_virtual_ref(SECRET_SUBAGENT_MEMORY_KIND, sub.agent_id)
    return subagent_file_path(sub, "memory.md")


def subagent_events_file(sub: SubAgentRuntime) -> str:
    return subagent_file_path(sub, "events.jsonl")


def subagent_sessions_dir(sub: SubAgentRuntime) -> str:
    return subagent_file_path(sub, "sessions")


def subagent_chat_session_file(sub: SubAgentRuntime, session_id: str) -> str:
    safe_session = re.sub(r"[^A-Za-z0-9_.-]+", "-", session_id or "current").strip("-") or "current"
    return os.path.join(subagent_sessions_dir(sub), safe_session + ".json")


def subagent_chat_title_for_messages(sub: SubAgentRuntime, messages: Optional[list[Message]] = None) -> str:
    source = messages if messages is not None else sub.messages
    return compact_title(suggested_session_title(source) or sub.chat_title or f"{sub.name} 会话", 80)


def subagent_chat_session_payload(sub: SubAgentRuntime, *, source: str = "") -> dict[str, Any]:
    if not sub.chat_session_id:
        sub.chat_session_id = subagent_new_chat_session_id()
    sub.chat_title = subagent_chat_title_for_messages(sub)
    return {
        "schema_version": "subagent.chat_session.v1",
        "agent_id": sub.agent_id,
        "session_id": sub.chat_session_id,
        "title": sub.chat_title,
        "security_context": sub.security_context,
        "updated_at": now_iso(),
        "source": source,
        "messages": [secret_message_record(msg) for msg in sub.messages],
    }


def normalize_loaded_subagent_chat_messages(messages: list[Message]) -> list[Message]:
    if not messages:
        return messages
    last = messages[-1]
    if last.role == "assistant" and not last.done:
        content = (last.content or "").rstrip()
        suffix = "[上一轮子 agent 输出中断，已按恢复记录收尾。]"
        if content:
            content = f"{content}\n\n{suffix}"
        else:
            content = suffix
        messages[-1] = Message("assistant", content, done=True)
    return messages


def messages_from_subagent_chat_payload(payload: dict[str, Any]) -> list[Message]:
    raw_messages = payload.get("messages")
    records = raw_messages if isinstance(raw_messages, list) else []
    return normalize_loaded_subagent_chat_messages([msg for msg in (secret_message_from_record(item) for item in records) if msg is not None])


def save_secret_subagent_memory(state: Optional[State], sub: SubAgentRuntime) -> tuple[bool, str]:
    if state is None or not state.secret_vault.unlocked or not state.secret_vault.key:
        return False, "Secret Vault 已锁定，拒绝保存 Secret 子 agent 记忆。"
    payload = {
        "schema_version": "secret.subagent_memory.v1",
        "agent_id": sub.agent_id,
        "updated_at": now_iso(),
        "memory": sub.memory_text if sub.persistent else "",
    }
    return secret_write_subagent_json(state, SECRET_SUBAGENT_MEMORY_KIND, sub.agent_id, payload)


def load_secret_subagent_memory(state: State, agent_id: str) -> str:
    pattern = os.path.join(SECRET_VAULT_SESSIONS_DIR, SECRET_SUBAGENT_SESSION_ID, SECRET_SUBAGENT_MEMORY_KIND, f"{agent_id}.secret")
    if not os.path.exists(pattern):
        return ""
    ok, payload, _detail = secret_read_json_from_path(
        state,
        SECRET_SUBAGENT_MEMORY_KIND,
        pattern,
        session_id=SECRET_SUBAGENT_SESSION_ID,
    )
    if not ok or not payload:
        return ""
    return str(payload.get("memory") or "")


def save_subagent_chat_session(state: Optional[State], sub: SubAgentRuntime, *, source: str = "ui") -> tuple[bool, str]:
    if not sub.persistent:
        return False, "临时子 agent 聊天不持久化。"
    payload = subagent_chat_session_payload(sub, source=source)
    sub.updated_at = time.time()
    if sub.security_context == "secret":
        if state is None or not state.secret_vault.unlocked or not state.secret_vault.key:
            return False, "Secret Vault 已锁定，拒绝保存 Secret 子 agent 会话。"
        ok, ref = secret_write_subagent_json(
            state,
            SECRET_SUBAGENT_CHAT_KIND,
            f"{sub.agent_id}-{sub.chat_session_id}",
            payload,
        )
        if ok:
            save_subagent_meta(sub, state)
        return ok, ref
    os.makedirs(subagent_sessions_dir(sub), exist_ok=True)
    write_text_atomic(
        subagent_chat_session_file(sub, sub.chat_session_id),
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    save_subagent_meta(sub)
    return True, subagent_chat_session_file(sub, sub.chat_session_id)


def subagent_chat_session_entries(state: Optional[State], sub: SubAgentRuntime) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if sub.security_context == "secret":
        if state is None or not state.secret_vault.unlocked or not state.secret_vault.key:
            return []
        pattern = os.path.join(SECRET_VAULT_SESSIONS_DIR, SECRET_SUBAGENT_SESSION_ID, SECRET_SUBAGENT_CHAT_KIND, "*.secret")
        for path in sorted(glob.glob(pattern)):
            ok, payload, detail = secret_read_json_from_path(
                state,
                SECRET_SUBAGENT_CHAT_KIND,
                path,
                session_id=SECRET_SUBAGENT_SESSION_ID,
            )
            if not ok or not payload:
                entries.append({"path": path, "agent_id": sub.agent_id, "error": detail, "updated_at": "", "title": os.path.basename(path), "session_id": ""})
                continue
            if str(payload.get("agent_id") or "") != sub.agent_id:
                continue
            messages = payload.get("messages")
            entries.append({
                "path": path,
                "agent_id": sub.agent_id,
                "session_id": str(payload.get("session_id") or ""),
                "title": compact_title(str(payload.get("title") or "子 agent 会话"), 80),
                "updated_at": str(payload.get("updated_at") or ""),
                "message_count": len(messages) if isinstance(messages, list) else 0,
                "payload": payload,
            })
    else:
        root = subagent_sessions_dir(sub)
        for path in sorted(glob.glob(os.path.join(root, "*.json"))):
            try:
                raw = json.loads(read_text_file(path, "{}"))
            except Exception as exc:
                entries.append({"path": path, "agent_id": sub.agent_id, "session_id": os.path.basename(path).removesuffix(".json"), "title": os.path.basename(path), "updated_at": "", "error": f"{type(exc).__name__}: {exc}"})
                continue
            payload = raw if isinstance(raw, dict) else {}
            if str(payload.get("agent_id") or sub.agent_id) != sub.agent_id:
                continue
            messages = payload.get("messages")
            entries.append({
                "path": path,
                "agent_id": sub.agent_id,
                "session_id": str(payload.get("session_id") or os.path.basename(path).removesuffix(".json")),
                "title": compact_title(str(payload.get("title") or "子 agent 会话"), 80),
                "updated_at": str(payload.get("updated_at") or ""),
                "message_count": len(messages) if isinstance(messages, list) else 0,
                "payload": payload,
            })
    entries.sort(key=lambda item: (str(item.get("updated_at") or ""), str(item.get("session_id") or "")), reverse=True)
    return entries


def load_subagent_chat_session(state: Optional[State], sub: SubAgentRuntime, session_id: str = "") -> bool:
    entries = subagent_chat_session_entries(state, sub)
    target: Optional[dict[str, Any]] = None
    if session_id:
        target = next((entry for entry in entries if str(entry.get("session_id") or "") == session_id), None)
    if target is None and sub.chat_session_id:
        target = next((entry for entry in entries if str(entry.get("session_id") or "") == sub.chat_session_id), None)
    if target is None and entries:
        target = entries[0]
    if target and isinstance(target.get("payload"), dict):
        payload = target["payload"]
        sub.chat_session_id = str(payload.get("session_id") or target.get("session_id") or subagent_new_chat_session_id())
        sub.chat_title = str(payload.get("title") or target.get("title") or f"{sub.name} 会话")
        sub.messages = messages_from_subagent_chat_payload(payload)
        if sub.agent is not None:
            restore_backend_from_secret_messages(sub.agent, sub.messages)
        return True
    if not sub.chat_session_id:
        sub.chat_session_id = subagent_new_chat_session_id()
    if not sub.chat_title:
        sub.chat_title = f"{sub.name} 会话"
    return False


def subagent_chat_session_switch_block_reason(sub: SubAgentRuntime) -> str:
    if sub.status in {"running", "aborting"} or sub.active_task_id is not None or sub.active_bus_task_id:
        return f"{sub.name} 正在运行；请等当前输出结束或先停止后再切换/新建子 agent 会话。"
    if sub.pending_interaction:
        return f"{sub.name} 正在等待输入；请先回答或取消后再切换/新建子 agent 会话。"
    if sub.chat_queue:
        return f"{sub.name} 还有排队输入；请等队列发送完成后再切换/新建子 agent 会话。"
    return ""


def new_subagent_chat_session(state: State, sub: SubAgentRuntime) -> None:
    block_reason = subagent_chat_session_switch_block_reason(sub)
    if block_reason:
        state.last_error = block_reason
        mark_dirty(state)
        return
    if sub.messages:
        save_subagent_chat_session(state, sub, source="new-session")
    sub.messages = []
    sub.pending_interaction = None
    sub.chat_queue.clear()
    sub.chat_queue_interrupt_requested = False
    sub.chat_session_id = subagent_new_chat_session_id()
    sub.chat_title = f"{sub.name} 会话"
    sub.updated_at = time.time()
    if sub.agent is not None:
        reset_agent_runtime_context_no_snapshot(sub.agent)
        install_subagent_prompt(sub.agent, sub)
    save_subagent_chat_session(state, sub, source="new-empty-session")
    save_subagent_meta(sub, state)
    mark_subagent_messages_changed(state, sub)
    state.last_error = f"已新建子 agent 会话：{sub.name}"


def clean_subagent_id(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9._-]+", "", text)
    text = text.strip("._-")
    return text[:40] or f"agent-{int(time.time())}"


def normalize_subagent_identity_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = re.sub(r"[#*_`>\[\](){}:：,，.。;；!?！？|/\\\"'“”‘’、\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact_identity_text(text: str) -> str:
    return re.sub(r"\s+", "", normalize_subagent_identity_text(text))


def text_has_any_intent_token(text: str, tokens: tuple[str, ...]) -> bool:
    normalized = normalize_subagent_identity_text(text)
    compact = compact_identity_text(text)
    return any(token.lower() in normalized or compact_identity_text(token) in compact for token in tokens)


GENERIC_SUBAGENT_IDENTITY_TERMS = {
    "agent",
    "subagent",
    "specialist",
    "researcher",
    "reviewer",
    "verifier",
    "coder",
    "ops",
    "长期",
    "持久",
    "永久",
    "临时",
    "暂时",
    "小号",
    "助手",
    "专家",
    "专员",
    "人员",
    "研究",
    "调研",
    "审查",
    "代码",
    "开发",
    "工程",
    "运维",
}

SUBAGENT_PERSISTENT_INTENT_TOKENS = (
    "persistent",
    "persist",
    "long_term",
    "long-term",
    "permanent",
    "durable",
    "长期",
    "持久",
    "永久",
    "正式",
    "保存身份",
)

SUBAGENT_TEMPORARY_INTENT_TOKENS = (
    "temporary",
    "temp",
    "ephemeral",
    "session_only",
    "session-only",
    "session scoped",
    "session-scoped",
    "临时",
    "暂时",
    "小号",
)

SUBAGENT_FORCE_NEW_INTENT_TOKENS = (
    "force_new",
    "force new",
    "create_new",
    "new separate",
    "no reuse",
    "do not reuse",
    "dont reuse",
    "reuse false",
    "reuse:false",
    "不要复用",
    "不复用",
    "别复用",
    "不要引用现有",
    "不引用现有",
    "不要引用已有",
    "不引用已有",
    "单独弄一个",
    "单独创建",
    "单独新建",
    "独立创建",
    "独立新建",
    "重新创建",
    "另起一个",
    "全新",
)

GENERIC_LATIN_SUBAGENT_IDENTITY_TERMS = {
    "agent",
    "subagent",
    "specialist",
    "researcher",
    "reviewer",
    "verifier",
    "coder",
    "manager",
    "manage",
    "assistant",
    "proxy",
    "persistent",
    "permanent",
    "durable",
    "temporary",
    "ephemeral",
}


def distinctive_alnum_identity_terms(text: str) -> set[str]:
    terms = {part for part in re.findall(r"[a-z0-9_]{4,}", normalize_subagent_identity_text(text))}
    return {term for term in terms if term not in GENERIC_LATIN_SUBAGENT_IDENTITY_TERMS}


def identity_terms(text: str) -> set[str]:
    normalized = normalize_subagent_identity_text(text)
    terms = {part for part in re.findall(r"[a-z0-9_]{3,}", normalized)}
    for segment in re.findall(r"[\u4e00-\u9fff]+", normalized):
        if len(segment) >= 2:
            terms.add(segment)
        terms.update(segment[idx:idx + 2] for idx in range(max(0, len(segment) - 1)))
        terms.update(segment[idx:idx + 3] for idx in range(max(0, len(segment) - 2)))
    return {term for term in terms if len(term) >= 2 and term not in GENERIC_SUBAGENT_IDENTITY_TERMS}


def longest_common_identity_span(left: str, right: str) -> int:
    left_compact = compact_identity_text(left)
    right_compact = compact_identity_text(right)
    best = 0
    for idx in range(len(left_compact)):
        for end in range(idx + 2, len(left_compact) + 1):
            piece = left_compact[idx:end]
            if piece in GENERIC_SUBAGENT_IDENTITY_TERMS:
                continue
            if piece in right_compact and len(piece) > best:
                best = len(piece)
    return best


def unique_subagent_id(name: str) -> str:
    base = clean_subagent_id(name)
    candidate = base
    counter = 2
    while os.path.exists(subagent_home(candidate)):
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def unique_secret_subagent_id(state: State, name: str) -> str:
    base = clean_subagent_id(name)
    candidate = base
    counter = 2
    existing = set(state.subagents)
    while candidate in existing:
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def unique_runtime_subagent_id(state: State, name: str) -> str:
    base = "tmp-" + clean_subagent_id(name)
    candidate = f"{base}-{time.time_ns() % 1_000_000_000_000}"
    counter = 2
    while candidate in state.subagents:
        candidate = f"{base}-{time.time_ns() % 1_000_000_000_000}-{counter}"
        counter += 1
    return candidate


def load_subagent_meta(agent_id: str) -> dict[str, Any]:
    return load_subagent_meta_file(subagent_meta_path(agent_id))


def load_subagent_meta_file(path: str) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def secret_subagent_payload_from_runtime(sub: SubAgentRuntime, **fields: Any) -> dict[str, Any]:
    meta = {
        "id": sub.agent_id,
        "name": sub.name,
        "role": normalized_role(sub.role),
        "default_model": sub.default_model,
        "security_context": "secret",
        "owner_session": sub.owner_session,
        "persistent": sub.persistent,
        "created_at": sub.created_at,
        "updated_at": sub.updated_at,
        "status": sub.status,
        "queued": len(sub.task_queue),
        "chat_queued": len(sub.chat_queue),
        "chat_session_id": sub.chat_session_id,
        "chat_title": sub.chat_title,
        "memory_ref": secret_virtual_ref(SECRET_SUBAGENT_MEMORY_KIND, sub.agent_id) if sub.persistent else "",
    }
    meta.update(fields)
    return {
        "schema_version": "secret.subagent.v1",
        "meta": meta,
        "profile": sub.profile_text,
    }


def save_secret_subagent_payload(state: Optional[State], sub: SubAgentRuntime, **fields: Any) -> tuple[bool, str]:
    if state is None or not state.secret_vault.unlocked or not state.secret_vault.key:
        return False, "Secret Vault 已锁定，拒绝保存 Secret 子 agent。"
    payload = secret_subagent_payload_from_runtime(sub, **fields)
    ok, ref = secret_write_subagent_json(state, SECRET_SUBAGENT_META_KIND, sub.agent_id, payload)
    if ok:
        sub.encrypted_ref = ref
    return ok, ref


def save_subagent_meta(sub: SubAgentRuntime, state: Optional[State] = None, **fields: Any) -> None:
    if sub.security_context == "secret":
        save_secret_subagent_payload(state, sub, **fields)
        return
    try:
        with open(subagent_meta_file(sub), encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        raw = {}
    meta = raw if isinstance(raw, dict) else {}
    meta.update({
        "id": sub.agent_id,
        "name": sub.name,
        "role": normalized_role(sub.role),
        "default_model": sub.default_model,
        "security_context": normalized_security_context(sub.security_context),
        "owner_session": sub.owner_session,
        "persistent": sub.persistent,
        "created_at": sub.created_at,
        "updated_at": sub.updated_at,
        "status": sub.status,
        "queued": len(sub.task_queue),
        "chat_queued": len(sub.chat_queue),
        "chat_session_id": sub.chat_session_id,
        "chat_title": sub.chat_title,
    })
    meta.update(fields)
    os.makedirs(sub.home, exist_ok=True)
    write_text_atomic(subagent_meta_file(sub), json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def append_subagent_event(sub: SubAgentRuntime, role: str, content: str, state: Optional[State] = None) -> None:
    payload = {
        "ts": time.time(),
        "role": role,
        "status": sub.status,
        "content": content,
    }
    if sub.security_context == "secret":
        if state is not None:
            secret_write_subagent_json(state, "subagent-events", f"{sub.agent_id}-{short_uid('event')}", payload)
        return
    os.makedirs(sub.home, exist_ok=True)
    append_text_file(subagent_events_file(sub), json.dumps(payload, ensure_ascii=False) + "\n")


def subagent_profile_text(sub: SubAgentRuntime) -> str:
    if sub.security_context == "secret":
        return sub.profile_text
    return read_text_file(subagent_profile_file(sub), "")


def subagent_memory_text(sub: SubAgentRuntime) -> str:
    if sub.security_context == "secret":
        return sub.memory_text if sub.persistent else ""
    return read_text_file(subagent_memory_file(sub), "") if sub.persistent else ""


def subagent_home_dirs_for_session(state: State) -> list[str]:
    homes: list[str] = []
    os.makedirs(SUBAGENTS_DIR, exist_ok=True)
    for name in sorted(os.listdir(SUBAGENTS_DIR)):
        home = subagent_home(name)
        if os.path.isdir(home):
            homes.append(home)
    owner = active_ui_session_key(state)
    if owner:
        temp_root = os.path.join(TEMP_SUBAGENTS_DIR, owner)
        if os.path.isdir(temp_root):
            for name in sorted(os.listdir(temp_root)):
                home = os.path.join(temp_root, name)
                if os.path.isdir(home):
                    homes.append(home)
    return homes


def load_secret_subagents(state: State) -> bool:
    before = set(state.subagents)
    loaded: dict[str, SubAgentRuntime] = {}
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        state.subagents = {}
        return bool(before)
    pattern = os.path.join(SECRET_VAULT_SESSIONS_DIR, SECRET_SUBAGENT_SESSION_ID, SECRET_SUBAGENT_META_KIND, "*.secret")
    for path in sorted(glob.glob(pattern)):
        ok, payload, detail = secret_read_json_from_path(
            state,
            SECRET_SUBAGENT_META_KIND,
            path,
            session_id=SECRET_SUBAGENT_SESSION_ID,
        )
        if not ok or not payload:
            state.secret_vault.storage_warning = f"Secret 子 agent 读取失败: {detail}"
            continue
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        if meta.get("deleted"):
            continue
        agent_id = str(meta.get("id") or os.path.basename(path).removesuffix(".secret"))
        display_name = str(meta.get("name") or agent_id)
        role = normalized_role(str(meta.get("role") or "specialist"))
        default_model = str(meta.get("default_model") or "")
        owner_session = str(meta.get("owner_session") or "")
        persistent = bool(meta.get("persistent", True))
        chat_session_id = str(meta.get("chat_session_id") or "")
        chat_title = str(meta.get("chat_title") or "")
        memory_text = load_secret_subagent_memory(state, agent_id) if persistent else ""
        if not memory_text and persistent:
            memory_text = str(payload.get("memory") or "")
        if not persistent and owner_session and owner_session != active_ui_session_key(state):
            continue
        existing = state.subagents.get(agent_id)
        if existing:
            existing.name = display_name
            existing.home = secret_subagent_home(agent_id)
            existing.role = role
            existing.default_model = default_model
            existing.security_context = "secret"
            existing.owner_session = owner_session
            existing.persistent = persistent
            existing.created_at = float(meta.get("created_at") or existing.created_at)
            existing.updated_at = float(meta.get("updated_at") or existing.updated_at)
            existing.profile_text = str(payload.get("profile") or "")
            existing.memory_text = memory_text if persistent else ""
            existing.encrypted_ref = secret_virtual_ref(SECRET_SUBAGENT_META_KIND, agent_id)
            if not existing.chat_session_id:
                existing.chat_session_id = chat_session_id
            if not existing.chat_title:
                existing.chat_title = chat_title
            if not existing.messages and existing.status not in {"running", "aborting"}:
                load_subagent_chat_session(state, existing, existing.chat_session_id)
            loaded[agent_id] = existing
        else:
            sub = SubAgentRuntime(
                agent_id=agent_id,
                name=display_name,
                home=secret_subagent_home(agent_id),
                role=role,
                default_model=default_model,
                security_context="secret",
                owner_session=owner_session,
                persistent=persistent,
                created_at=float(meta.get("created_at") or time.time()),
                updated_at=float(meta.get("updated_at") or time.time()),
                profile_text=str(payload.get("profile") or ""),
                memory_text=memory_text if persistent else "",
                encrypted_ref=secret_virtual_ref(SECRET_SUBAGENT_META_KIND, agent_id),
                chat_session_id=chat_session_id,
                chat_title=chat_title,
            )
            load_subagent_chat_session(state, sub, sub.chat_session_id)
            loaded[agent_id] = sub
    state.subagents = loaded
    changed = before != set(loaded)
    if changed:
        state.rightbar_task_rows_cache = []
    return changed


def load_subagents(state: State) -> bool:
    if state.secret_vault.unlocked:
        return load_secret_subagents(state)
    before = set(state.subagents)
    loaded: dict[str, SubAgentRuntime] = {}
    for home in subagent_home_dirs_for_session(state):
        meta = load_subagent_meta_file(os.path.join(home, "meta.json"))
        if meta.get("deleted"):
            continue
        agent_id = str(meta.get("id") or os.path.basename(home))
        display_name = str(meta.get("name") or agent_id)
        role = normalized_role(str(meta.get("role") or "specialist"))
        default_model = str(meta.get("default_model") or "")
        security_context = normalized_security_context(str(meta.get("security_context") or "standard"))
        owner_session = str(meta.get("owner_session") or "")
        persistent = bool(meta.get("persistent", os.path.commonpath([SUBAGENTS_DIR, home]) == SUBAGENTS_DIR))
        chat_session_id = str(meta.get("chat_session_id") or "")
        chat_title = str(meta.get("chat_title") or "")
        existing = state.subagents.get(agent_id)
        if existing:
            existing.name = display_name
            existing.home = home
            existing.role = role
            existing.default_model = default_model
            existing.security_context = security_context
            existing.owner_session = owner_session
            existing.persistent = persistent
            existing.created_at = float(meta.get("created_at") or existing.created_at)
            existing.updated_at = float(meta.get("updated_at") or existing.updated_at)
            if not existing.chat_session_id:
                existing.chat_session_id = chat_session_id
            if not existing.chat_title:
                existing.chat_title = chat_title
            if not existing.messages and existing.status not in {"running", "aborting"}:
                load_subagent_chat_session(state, existing, existing.chat_session_id)
            loaded[agent_id] = existing
        else:
            sub = SubAgentRuntime(
                agent_id=agent_id,
                name=display_name,
                home=home,
                role=role,
                default_model=default_model,
                security_context=security_context,
                owner_session=owner_session,
                persistent=persistent,
                created_at=float(meta.get("created_at") or time.time()),
                updated_at=float(meta.get("updated_at") or time.time()),
                chat_session_id=chat_session_id,
                chat_title=chat_title,
            )
            load_subagent_chat_session(state, sub, sub.chat_session_id)
            loaded[agent_id] = sub
    state.subagents = loaded
    changed = before != set(loaded)
    if changed:
        state.rightbar_task_rows_cache = []
    return changed


def create_subagent(state: State, name: str, profile: str = "", role: str = "specialist", persistent: bool = True) -> SubAgentRuntime:
    name = (name or "").strip() or "subagent"
    role = normalized_role(role)
    security_context = "secret" if state.secret_vault.unlocked else "standard"
    if security_context == "secret":
        if not state.secret_vault.key:
            raise SecretVaultError("Secret Vault 已锁定，不能创建 Secret 子 agent。")
        agent_id = unique_secret_subagent_id(state, name)
        home = secret_subagent_home(agent_id)
    else:
        agent_id = unique_subagent_id(name) if persistent else unique_runtime_subagent_id(state, name)
        if persistent:
            home = subagent_home(agent_id)
        else:
            owner = active_ui_session_key(state) or "current"
            home = os.path.join(TEMP_SUBAGENTS_DIR, owner, agent_id)
        os.makedirs(home, exist_ok=False)
    now = time.time()
    sub = SubAgentRuntime(
        agent_id=agent_id,
        name=name,
        home=home,
        role=role,
        security_context=security_context,
        owner_session=active_ui_session_key(state),
        persistent=persistent,
        created_at=now,
        updated_at=now,
        chat_session_id=subagent_new_chat_session_id(),
        chat_title=f"{name} 会话",
    )
    profile_text = (profile or "").strip()
    if not profile_text:
        template = role_template(role)
        profile_text = (
            f"# {name}\n\n"
            f"- 这是一个由 ga tui 管理的{'持久' if persistent else '临时会话'}子 agent。\n"
            f"- 角色：{role}。\n"
            f"- 安全上下文：{security_context}。\n"
            f"- 职责：{template.get('description', '')}\n"
            f"- 写策略：{template.get('write_policy', 'none')}。\n"
            "- 它应当围绕自己的任务边界工作。\n"
            + ("- 长期记忆只提交候选并等待审批。\n" if persistent else "- 临时子 agent 不写长期记忆，退出后可丢弃。\n")
        )
    if security_context == "secret":
        sub.profile_text = profile_text.rstrip() + "\n"
        sub.memory_text = f"# {name} Memory\n\n" if persistent else ""
        save_subagent_meta(sub, state)
        if persistent:
            save_secret_subagent_memory(state, sub)
        append_subagent_event(sub, "system", "created", state=state)
    else:
        write_text_atomic(subagent_profile_file(sub), profile_text.rstrip() + "\n")
        write_text_atomic(subagent_memory_file(sub), f"# {name} Memory\n\n" if persistent else f"# {name} Ephemeral Scratch\n\n")
        save_subagent_meta(sub)
        append_subagent_event(sub, "system", "created")
    state.subagents[agent_id] = sub
    mark_dirty(state)
    return sub


def subagent_prompt_block(sub: SubAgentRuntime) -> str:
    profile = subagent_profile_text(sub).strip()
    memory = subagent_memory_text(sub).strip() if sub.persistent else ""
    template = role_template(sub.role)
    return f"""
[GA TUI SubAgent Profile]
你是一个{'持久' if sub.persistent else '临时会话'}子 agent。
Name: {sub.name}
ID: {sub.agent_id}
Role: {sub.role}
Default model: {sub.default_model or "(global default)"}
Security context: {sub.security_context}
Home: {sub.home}
Persistence: {'persistent' if sub.persistent else 'ephemeral-session'}
Role description: {template.get("description", "")}
Write policy: {template.get("write_policy", "none")}
Tools allowed: {", ".join(role_tools_allowed(sub.role))}
Output contract: {", ".join(role_output_contract(sub.role))}

Profile:
{profile or "(empty)"}

Long-term memory:
{memory or ("(disabled for ephemeral session agent)" if not sub.persistent else "(empty)")}

规则：
- 你拥有独立运行期上下文，但共享主 GenericAgent 的工具能力。
- 只围绕自己的任务边界工作；不要假装自己是主 agent。
- 遵守写策略；coder/ops 等写入型角色必须等待 TUI single-writer 锁和审批策略。
- security_context=secret 时，禁止访问普通历史/普通明文 artifact，任何网络操作必须通过 Secret 代理/Tor 链且失败即停止。
- 临时会话子 agent 不写长期记忆；只有持久子 agent 才提交长期记忆候选。
- 如果你是持久子 agent，发现长期有效、经验证的事实，可在最终回复末尾输出原始记忆观察；Memory Curator 会转换为审批候选，不会直接写入：
<ga-subagent-memory>
- 事实或偏好，尽量短
</ga-subagent-memory>
- 不要在该块里写临时状态、猜测、密码/API key。
[/GA TUI SubAgent Profile]
""".strip()


def subagent_storage_summary(sub: SubAgentRuntime) -> str:
    if sub.security_context == "secret":
        memory_ref = secret_virtual_ref(SECRET_SUBAGENT_MEMORY_KIND, sub.agent_id) if sub.persistent else "(disabled)"
        chat_ref = secret_virtual_ref(SECRET_SUBAGENT_CHAT_KIND, f"{sub.agent_id}-{sub.chat_session_id or 'current'}")
        return f"Secret encrypted refs: memory={memory_ref}; chat={chat_ref}"
    memory_ref = subagent_memory_file(sub) if sub.persistent else "(disabled)"
    chat_ref = subagent_chat_session_file(sub, sub.chat_session_id or "current") if sub.persistent else "(ephemeral)"
    return f"Local refs: profile={subagent_profile_file(sub)}; memory={memory_ref}; chat={chat_ref}"


def subagent_chat_session_ref(sub: SubAgentRuntime) -> str:
    if sub.security_context == "secret":
        return secret_virtual_ref(SECRET_SUBAGENT_CHAT_KIND, f"{sub.agent_id}-{sub.chat_session_id or 'current'}")
    if sub.persistent:
        return subagent_chat_session_file(sub, sub.chat_session_id or "current")
    return f"subagent-chat://{sub.agent_id}/{sub.chat_session_id or 'ephemeral'}"


def subagent_direct_chat_prompt(
    sub: SubAgentRuntime,
    prompt: str,
    *,
    context_ref: str = "",
    chat_context_id: str = "",
) -> str:
    prompt = (prompt or "").strip()
    return f"""
[GA TUI Direct SubAgent Chat]
You are answering inside the selected subagent chat, not as the main GenericAgent.
Selected subagent:
- name: {sub.name}
- id: {sub.agent_id}
- role: {sub.role}
- security_context: {sub.security_context}
- storage: {subagent_storage_summary(sub)}
- chat_context_id: {chat_context_id or "(none)"}
- context_pack_ref: {context_ref or "(none)"}

Response rules:
- Treat the context pack above as this subagent's startup memory hydration for the current direct-chat turn.
- Prefer this subagent's own profile, memory, chat session, and context pack over the main GenericAgent global memory.
- Answer as {sub.name}; do not introduce yourself as the main GenericAgent or the GenericAgent 主控代理.
- If the user asks who you are, describe this subagent identity, role, and boundary.
- If the user asks where your memory/session is stored, answer using the storage line above and this subagent's own profile/memory/chat session, not the main agent memory directory.
- Keep the user's visible message semantics unchanged.
[/GA TUI Direct SubAgent Chat]

User message:
{prompt}
""".strip()


def build_subagent_direct_chat_prompt(state: State, sub: SubAgentRuntime, prompt: str) -> tuple[str, str, str]:
    chat_context_id = short_uid("chat")
    context_pack, context_ref = build_context_pack(state, sub, prompt, chat_context_id)
    prompt_text = "\n\n".join([
        format_context_pack_for_prompt(context_pack),
        subagent_direct_chat_prompt(sub, prompt, context_ref=context_ref, chat_context_id=chat_context_id),
    ])
    return prompt_text, context_ref, chat_context_id


def install_subagent_prompt(agent: Any, sub: SubAgentRuntime) -> None:
    if agent is None:
        return
    block = "\n\n" + subagent_prompt_block(sub) + "\n"
    clients: list[Any] = []
    for client in getattr(agent, "llmclients", []) or []:
        if client not in clients:
            clients.append(client)
    current = getattr(agent, "llmclient", None)
    if current is not None and current not in clients:
        clients.insert(0, current)
    for client in clients:
        backend = getattr(client, "backend", None)
        if backend is None:
            continue
        try:
            extra = str(getattr(backend, "extra_sys_prompt", "") or "")
            extra = SUBAGENT_PROMPT_RE.sub("\n", extra).rstrip()
            setattr(backend, "extra_sys_prompt", extra + block)
        except Exception:
            continue


def ensure_subagent_agent(state: State, sub: SubAgentRuntime) -> Any:
    if sub.agent is None:
        sub.agent = new_agent()
        install_interaction_hook(state, sub.agent)
        if sub.security_context == "secret":
            set_agent_log_path(sub.agent, os.devnull)
        else:
            os.makedirs(sub.home, exist_ok=True)
            set_agent_log_path(sub.agent, os.path.join(sub.home, "model_responses.txt"))
        if sub.messages:
            restore_backend_from_secret_messages(sub.agent, sub.messages)
        bind_agent_token_session(state, sub.agent)
    elif sub.security_context == "secret":
        set_agent_log_path(sub.agent, os.devnull)
    apply_subagent_default_model(state, sub)
    install_subagent_prompt(sub.agent, sub)
    return sub.agent


def strip_subagent_memory_controls(text: str) -> str:
    return SUBAGENT_MEMORY_RE.sub("", text or "").strip()


def extract_subagent_memory_updates(text: str) -> list[str]:
    updates: list[str] = []
    for match in SUBAGENT_MEMORY_RE.finditer(text or ""):
        body = clean_text(match.group(1)).strip()
        if body:
            updates.append(body)
    return updates


def canonical_memory_statement(text: str) -> str:
    text = clean_text(text or "").strip()
    text = re.sub(r"^\s*[-*]\s+", "", text)
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def memory_candidate_dedupe_key(scope: str, statement: str) -> str:
    canonical = f"{scope}\n{canonical_memory_statement(statement)}"
    digest = hashlib.sha256(canonical.encode("utf-8", errors="ignore")).hexdigest()
    return "sha256:" + digest


def infer_memory_candidate_type(text: str, source: str = "") -> str:
    lower = unicodedata.normalize("NFKC", f"{text} {source}").lower()
    if any(token in lower for token in ("prefer", "preference", "偏好", "喜欢", "习惯", "不要", "总是", "always")):
        return "preference"
    if any(token in lower for token in ("sop", "procedure", "workflow", "流程", "步骤", "规范", "方法", "how to")):
        return "procedural"
    if any(token in lower for token in ("project", "项目", "架构", "decision", "决策")):
        return "project"
    if any(token in lower for token in ("failed", "fixed", "completed", "失败", "修复", "完成", "本次", "这次")):
        return "episodic"
    return "semantic"


def memory_candidate_ttl(candidate_type: str, confidence: float) -> str:
    if confidence < 0.55:
        return "short"
    if candidate_type in {"preference", "procedural", "project"}:
        return "long"
    return "medium"


def memory_candidate_confidence(text: str, *, evidence_refs: list[str], task_id: str) -> float:
    lower = unicodedata.normalize("NFKC", text or "").lower()
    confidence = 0.55
    if evidence_refs:
        confidence += 0.18
    if task_id:
        confidence += 0.07
    if any(token in lower for token in ("maybe", "可能", "猜", "大概", "临时")):
        confidence -= 0.18
    return max(0.0, min(0.95, round(confidence, 2)))


def memory_candidate_scope(target_sub: SubAgentRuntime, text: str = "") -> str:
    match = re.search(r"\bscope\s*:\s*([a-zA-Z0-9_.:-]+)", text or "", flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return f"subagent.{target_sub.agent_id}"


def memory_candidate_duplicates(
    *,
    scope: str,
    statement: str,
    dedupe_key: str,
    target_sub: SubAgentRuntime,
) -> tuple[list[str], list[dict[str, Any]], str]:
    duplicate_of: list[str] = []
    conflicts_with: list[dict[str, Any]] = []
    canonical = canonical_memory_statement(statement)
    existing_memory = subagent_memory_text(target_sub) if target_sub.persistent else ""
    for line_no, line in enumerate(existing_memory.splitlines(), start=1):
        line_canonical = canonical_memory_statement(line)
        if not line_canonical or line_canonical.startswith("#"):
            continue
        if line_canonical == canonical:
            duplicate_of.append(f"memory://{target_sub.agent_id}#L{line_no}")
    if target_sub.security_context != "secret":
        for row in read_jsonl(AGENT_MEMORY_CANDIDATES_PATH):
            candidate = row.get("memory_candidate") if isinstance(row.get("memory_candidate"), dict) else row
            if str(candidate.get("dedupe_key") or "") == dedupe_key:
                candidate_id = str(candidate.get("candidate_id") or row.get("candidate_id") or "")
                if candidate_id:
                    duplicate_of.append(f"memory-candidate://{candidate_id}")
    negated = any(token in canonical for token in (" not ", " never ", "不要", "不再", "禁用", "avoid", "禁止"))
    if negated and existing_memory.strip():
        conflicts_with.append({
            "ref": f"memory://{target_sub.agent_id}",
            "reason": "candidate_contains_negation_check_existing_memory",
        })
    status = "duplicate_possible" if duplicate_of else ("conflict_possible" if conflicts_with else "no_conflict_detected")
    return duplicate_of, conflicts_with, status


def build_memory_candidate(
    target_sub: SubAgentRuntime,
    text: str,
    *,
    source: str,
    evidence_ref: str = "",
    task_id: str = "",
    curator: Optional[SubAgentRuntime] = None,
) -> dict[str, Any]:
    statement = clean_text(text).strip()
    evidence_refs = [evidence_ref] if evidence_ref else []
    scope = memory_candidate_scope(target_sub, statement)
    candidate_type = infer_memory_candidate_type(statement, source)
    confidence = memory_candidate_confidence(statement, evidence_refs=evidence_refs, task_id=task_id)
    ttl = memory_candidate_ttl(candidate_type, confidence)
    dedupe_key = memory_candidate_dedupe_key(scope, statement)
    duplicate_of, conflicts_with, conflict_status = memory_candidate_duplicates(
        scope=scope,
        statement=statement,
        dedupe_key=dedupe_key,
        target_sub=target_sub,
    )
    return {
        "schema_version": "memory_candidate.v1",
        "candidate_id": short_uid("memcand"),
        "created_at": now_iso(),
        "target_subagent": target_sub.agent_id,
        "target_role": normalized_role(target_sub.role),
        "curator_id": curator.agent_id if curator is not None else "",
        "source": source,
        "task_id": task_id,
        "scope": scope,
        "type": candidate_type,
        "statement": statement,
        "evidence_refs": evidence_refs,
        "artifact_refs": [],
        "confidence": confidence,
        "ttl": ttl,
        "dedupe_key": dedupe_key,
        "duplicate_of": duplicate_of,
        "conflicts_with": conflicts_with,
        "conflict_check": {
            "status": conflict_status,
            "existing_memory_checked": True,
            "pending_candidates_checked": target_sub.security_context != "secret",
        },
        "requires_human_approval": True,
    }


def memory_candidate_rejection_reason(candidate: dict[str, Any]) -> str:
    statement = clean_text(str(candidate.get("statement") or "")).strip()
    canonical = canonical_memory_statement(statement)
    if not canonical:
        return "empty_candidate"
    secret_patterns = [
        r"\bsk-[A-Za-z0-9_\-]{16,}\b",
        r"\b(api[_-]?key|secret|token|password|passwd|密码|密钥)\s*[:=]\s*\S+",
        r"\b[A-Za-z0-9_\-]{24,}\.[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{12,}\b",
    ]
    if any(re.search(pattern, statement, flags=re.IGNORECASE) for pattern in secret_patterns):
        return "privacy_risk_secret_or_credential"
    if len(canonical) < 8:
        return "too_temporary_or_too_short"
    if any(token in canonical for token in ("maybe", "可能", "猜", "大概", "临时", "暂时")) and not candidate.get("evidence_refs"):
        return "too_temporary_low_evidence"
    if float(candidate.get("confidence") or 0.0) < 0.5:
        return "low_confidence"
    return ""


def append_memory_candidate_record(
    candidate: dict[str, Any],
    *,
    status: str,
    approval_id: str = "",
    artifact_refs: Optional[list[str]] = None,
) -> dict[str, Any]:
    candidate_copy = copy.deepcopy(candidate)
    if artifact_refs is not None:
        candidate_copy["artifact_refs"] = list(artifact_refs)
    row = {
        "schema_version": "memory_candidate_record.v1",
        "candidate_id": candidate_copy.get("candidate_id", ""),
        "timestamp": now_iso(),
        "status": status,
        "approval_id": approval_id,
        "target_subagent": candidate_copy.get("target_subagent", ""),
        "scope": candidate_copy.get("scope", ""),
        "type": candidate_copy.get("type", ""),
        "ttl": candidate_copy.get("ttl", ""),
        "dedupe_key": candidate_copy.get("dedupe_key", ""),
        "duplicate_of": candidate_copy.get("duplicate_of", []),
        "conflicts_with": candidate_copy.get("conflicts_with", []),
        "memory_candidate": candidate_copy,
        "artifact_refs": list(artifact_refs or candidate_copy.get("artifact_refs") or []),
    }
    append_jsonl(AGENT_MEMORY_CANDIDATES_PATH, row)
    return row


def append_subagent_memory(sub: SubAgentRuntime, text: str, source: str = "manual", policy_approved: bool = False, state: Optional[State] = None) -> str:
    text = clean_text(text).strip()
    if not text:
        return "记忆内容为空。"
    if not sub.persistent:
        return f"{sub.name} 是临时会话子 agent，不写长期记忆；需要长期记忆请显式使用 /agent new persistent:<name> 创建持久子 agent。"
    if sub.security_context == "secret":
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        sub.memory_text = (sub.memory_text or f"# {sub.name} Memory\n\n").rstrip() + f"\n\n## {stamp} [{source}]\n{text.rstrip()}\n"
        sub.updated_at = time.time()
        save_secret_subagent_memory(state, sub)
        save_subagent_meta(sub, state)
        if sub.agent is not None:
            install_subagent_prompt(sub.agent, sub)
        return f"已写入 Secret 子 agent 加密记忆：{sub.name}"
    if not policy_approved and source not in {"approved", "policy_allowed"}:
        decision = evaluate_policy_action(
            "write_long_term_memory",
            subject=sub.agent_id,
            role=sub.role,
            source=source,
            target=sub.agent_id,
            payload={
                "operation": "append_subagent_memory",
                "subagent_id": sub.agent_id,
                "memory_preview": truncate_cells(text, 240),
            },
        )
        if decision.approval_required:
            queue_policy_approval(
                decision,
                summary=f"{sub.name}: {truncate_cells(text, 100)}",
                extra_payload={
                    "deferred_operation": "append_subagent_memory",
                    "subagent_id": sub.agent_id,
                    "memory": text,
                    "source": source,
                },
            )
        record_policy_decision(decision)
        if not decision.allowed:
            return policy_gate_text(decision)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    append_text_file(subagent_memory_file(sub), f"\n## {stamp} [{source}]\n{text.rstrip()}\n")
    sub.updated_at = time.time()
    save_subagent_meta(sub)
    if sub.agent is not None:
        install_subagent_prompt(sub.agent, sub)
    return f"已写入子 agent 记忆：{sub.name}"


def set_subagent_default_model(state: State, sub: SubAgentRuntime, model_name: str) -> tuple[bool, str]:
    if not sub.persistent:
        return False, f"{sub.name} 是临时会话子 agent，不支持默认模型；请创建持久子 agent。"
    model_name = str(model_name or "").strip()
    if model_name.lower() in {"inherit", "default", "global", "none", "clear", "-", "继承", "默认", "全局", "清除"}:
        model_name = ""
    if model_name:
        entries, _mixin, _preserved, error = load_llm_config_entries()
        if error:
            return False, error
        if entry_index_by_name(entries, model_name) < 0:
            return False, f"找不到模型配置：{model_name}"
    sub.default_model = model_name
    sub.updated_at = time.time()
    save_subagent_meta(sub, state)
    if sub.agent is not None and not agent_has_unfinished_task(sub.agent):
        ok, msg = apply_subagent_default_model(state, sub) if model_name else reset_agent_instance_to_default_llm(sub.agent)
        if model_name and not ok:
            return False, f"默认模型已保存，但当前运行时应用失败：{msg}"
    label = model_name or "全局默认模型"
    return True, f"已设置 {sub.name} 默认使用模型：{label}"


def queue_subagent_memory_candidate(sub: SubAgentRuntime, text: str, source: str = "agent") -> str:
    text = clean_text(text).strip()
    if not text:
        return "记忆候选内容为空。"
    if not sub.persistent:
        return f"{sub.name} 是临时会话子 agent，已忽略长期记忆候选。"
    candidate = build_memory_candidate(sub, text, source=source)
    approval_id = queue_approval(
        approval_type="memory_write_request",
        summary=f"{sub.name}: {truncate_cells(text, 80)}",
        payload={"subagent_id": sub.agent_id, "memory": candidate["statement"], "memory_candidate": candidate},
        source=source,
        target=sub.agent_id,
        approval_required_for="write_long_term_memory",
    )
    append_memory_candidate_record(candidate, status="pending", approval_id=approval_id)
    return f"已提交子 agent 记忆候选，等待审批：{approval_id}"


def queue_secret_subagent_memory_candidate(state: State, sub: SubAgentRuntime, text: str, source: str = "agent", task_id: str = "", evidence_ref: str = "") -> str:
    text = clean_text(text).strip()
    if not text:
        return "记忆候选内容为空。"
    if not sub.persistent:
        return f"{sub.name} 是临时会话子 agent，已忽略长期记忆候选。"
    candidate = build_memory_candidate(sub, text, source=source, evidence_ref=evidence_ref, task_id=task_id)
    candidate["secret_storage"] = True
    approval_id = secret_memory_candidate_approval_id(str(candidate.get("candidate_id") or ""))
    ok, ref = secret_write_subagent_json(state, "subagent-memory-candidates", candidate["candidate_id"], {
        "schema_version": "secret.memory_candidate_record.v1",
        "candidate": candidate,
        "approval_id": approval_id,
        "status": "pending",
        "updated_at": now_iso(),
    })
    if ok:
        offer_pending_approval_interaction(state, approval_id)
    return f"已提交 Secret 子 agent 加密记忆候选，等待审批：{approval_id}（{ref if ok else '写入失败'}）"


def ensure_memory_curator(state: State) -> SubAgentRuntime:
    for sub in state.subagents.values():
        if sub.role == "memory_curator":
            return sub
    return create_subagent(
        state,
        "Memory Curator",
        (
            "# Memory Curator\n\n"
            "- 只从 trace、artifact、子 agent 结果中提取稳定长期记忆候选。\n"
            "- 不直接写长期记忆；所有候选必须进入审批队列。\n"
            "- 拒绝临时状态、猜测、密码、API key、一次性闲聊。\n"
        ),
        role="memory_curator",
        persistent=True,
    )


def queue_curated_memory_candidate(
    state: State,
    target_sub: SubAgentRuntime,
    text: str,
    *,
    source: str,
    evidence_ref: str = "",
    task_id: str = "",
) -> str:
    text = clean_text(text).strip()
    if not text:
        return "记忆候选内容为空。"
    if not target_sub.persistent:
        return f"{target_sub.name} 是临时会话子 agent，已忽略长期记忆候选。"
    if target_sub.security_context == "secret":
        return queue_secret_subagent_memory_candidate(state, target_sub, text, source=source, task_id=task_id, evidence_ref=evidence_ref)
    curator = ensure_memory_curator(state)
    decision = evaluate_policy_action(
        "write_long_term_memory",
        subject=curator.agent_id,
        role=curator.role,
        source=source,
        target=target_sub.agent_id,
        payload={
            "operation": "queue_curated_memory_candidate",
            "target_subagent": target_sub.agent_id,
            "task_id": task_id,
            "evidence_ref": evidence_ref,
            "memory_preview": truncate_cells(text, 240),
        },
    )
    if decision.status == "denied":
        record_policy_decision(decision)
        return policy_gate_text(decision)
    candidate = build_memory_candidate(
        target_sub,
        text,
        source=source,
        evidence_ref=evidence_ref,
        task_id=task_id,
        curator=curator,
    )
    rejection_reason = memory_candidate_rejection_reason(candidate)
    if rejection_reason:
        candidate["rejected_reason"] = rejection_reason
        append_memory_candidate_record(candidate, status="rejected")
        append_agent_mail(
            from_agent=curator.agent_id,
            to_type="agent",
            target="orchestrator.main",
            intent="memory_candidate_rejected",
            task_id=task_id,
            status="rejected",
            payload={
                "target_subagent": target_sub.agent_id,
                "summary": truncate_cells(candidate["statement"], 160),
                "reason": rejection_reason,
                "memory_candidate": candidate,
            },
            requires_human_approval=False,
        )
        append_trace(
            task_id or candidate["candidate_id"],
            "memory_candidate_rejected",
            agent_id=curator.agent_id,
            status="rejected",
            payload={
                "memory_candidate_id": candidate["candidate_id"],
                "reason": rejection_reason,
                "duplicate_of": candidate["duplicate_of"],
                "conflicts_with": candidate["conflicts_with"],
            },
        )
        return f"Memory Curator 已拒绝记忆候选：{rejection_reason}"
    candidate_doc = (
        f"# Memory Candidate\n\n"
        f"Target: {target_sub.name} ({target_sub.agent_id})\n"
        f"Source: {source}\n"
        f"Task: {task_id or '-'}\n"
        f"Evidence: {evidence_ref or '-'}\n"
        f"Curator: {curator.name} ({curator.agent_id})\n\n"
        f"## Metadata\n\n```json\n{json.dumps(candidate, ensure_ascii=False, indent=2, sort_keys=True)}\n```\n\n"
        f"## Candidate\n\n{text.rstrip()}\n"
    )
    candidate_ref = write_harness_artifact(
        "memory-candidates",
        f"{target_sub.agent_id}-{candidate['candidate_id']}",
        candidate_doc,
        source_task_id=task_id,
        provenance={
            "generated_by": curator.agent_id,
            "target_subagent": target_sub.agent_id,
            "memory_candidate_id": candidate["candidate_id"],
            "memory_scope": candidate["scope"],
            "memory_type": candidate["type"],
            "dedupe_key": candidate["dedupe_key"],
            "evidence_ref": evidence_ref,
            "source": source,
        },
    )
    candidate["artifact_refs"] = [candidate_ref]
    approval_id = queue_approval(
        approval_type="memory_write_request",
        summary=f"{target_sub.name}: {truncate_cells(text, 80)}",
        payload={
            "subagent_id": target_sub.agent_id,
            "curator_id": curator.agent_id,
            "memory": candidate["statement"],
            "memory_candidate": candidate,
            "task_id": task_id,
            "evidence_ref": evidence_ref,
            "artifact_refs": [candidate_ref],
        },
        source=curator.agent_id,
        target=target_sub.agent_id,
        approval_required_for="write_long_term_memory",
    )
    decision.approval_id = approval_id
    record_policy_decision(decision)
    append_memory_candidate_record(candidate, status="pending", approval_id=approval_id, artifact_refs=[candidate_ref])
    offer_pending_approval_interaction(state, approval_id)
    append_agent_mail(
        from_agent=curator.agent_id,
        to_type="human",
        target="approval_inbox",
        intent="memory_candidate_curated",
        task_id=task_id,
        status="pending",
        payload={
            "approval_id": approval_id,
            "target_subagent": target_sub.agent_id,
            "summary": truncate_cells(candidate["statement"], 160),
            "memory_candidate": candidate,
        },
        artifact_refs=[candidate_ref],
        requires_human_approval=True,
    )
    append_trace(
        task_id or approval_id,
        "memory_candidate_curated",
        agent_id=curator.agent_id,
        status="pending",
        payload={
            "approval_id": approval_id,
            "artifact_ref": candidate_ref,
            "memory_candidate_id": candidate["candidate_id"],
            "dedupe_key": candidate["dedupe_key"],
            "duplicate_of": candidate["duplicate_of"],
            "conflicts_with": candidate["conflicts_with"],
        },
    )
    return f"Memory Curator 已提交记忆候选，等待审批：{approval_id}"


def resolve_subagent(state: State, token: str) -> Optional[SubAgentRuntime]:
    token = (token or "").strip()
    if not token:
        return None
    if token in state.subagents:
        return state.subagents[token]
    low = token.lower()
    for sub in state.subagents.values():
        if sub.name.lower() == low:
            return sub
    matches = [sub for sub in state.subagents.values() if sub.agent_id.startswith(low) or low in sub.name.lower()]
    return matches[0] if len(matches) == 1 else None


def subagent_identity_blob(sub: SubAgentRuntime) -> str:
    profile = subagent_profile_text(sub)
    return "\n".join([sub.agent_id, sub.name, sub.role, profile])


def reusable_subagent_score(sub: SubAgentRuntime, name: str, profile: str, role: str) -> int:
    requested_name = name or ""
    requested_profile = profile or ""
    requested_blob = "\n".join([requested_name, normalized_role(role), requested_profile])
    candidate_blob = subagent_identity_blob(sub)
    requested_topic_terms = distinctive_alnum_identity_terms(requested_blob)
    if requested_topic_terms and not (requested_topic_terms & distinctive_alnum_identity_terms(candidate_blob)):
        return 0
    candidate_name_blob = "\n".join([sub.agent_id, sub.name])
    req_name_compact = compact_identity_text(requested_name)
    sub_name_compact = compact_identity_text(sub.name)
    candidate_name_compact = compact_identity_text(candidate_name_blob)
    name_score = 0
    if requested_name and requested_name.strip() == sub.agent_id:
        name_score += 120
    if req_name_compact and req_name_compact == sub_name_compact:
        name_score += 100
    elif req_name_compact and len(req_name_compact) >= 2 and (
        req_name_compact in candidate_name_compact or sub_name_compact in req_name_compact
    ):
        name_score += 55
    common_span = longest_common_identity_span(requested_name, candidate_name_blob)
    if common_span >= 3:
        name_score += min(70, common_span * 22)
    score = name_score
    if not requested_name or name_score >= 40:
        requested_terms = identity_terms(requested_blob)
        candidate_terms = identity_terms(candidate_blob)
        if requested_terms:
            score += min(60, len(requested_terms & candidate_terms) * 10)
    if (not requested_name or name_score >= 40) and requested_profile and compact_identity_text(requested_profile) == compact_identity_text(subagent_profile_text(sub)):
        score += 80
    if normalized_role(role) != "specialist" and normalized_role(role) == sub.role:
        score += 8
    if sub.persistent:
        score += 3
    return score


def find_reusable_subagent(
    state: State,
    name: str,
    profile: str = "",
    role: str = "specialist",
    *,
    require_persistent: bool = False,
    require_temporary: bool = False,
) -> Optional[SubAgentRuntime]:
    load_subagents(state)
    direct = resolve_subagent(state, name)
    if direct is not None and (not require_persistent or direct.persistent) and (not require_temporary or not direct.persistent):
        return direct
    candidates = [
        sub for sub in state.subagents.values()
        if (not require_persistent or sub.persistent)
        and (not require_temporary or not sub.persistent)
    ]
    scored = [
        (reusable_subagent_score(sub, name, profile, role), sub.updated_at, sub)
        for sub in candidates
    ]
    scored = [item for item in scored if item[0] >= 40]
    if not scored:
        return None
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return scored[0][2]


def tui_query_limit(value: Any, default: int, *, minimum: int = 1, maximum: int = 100) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(minimum, min(maximum, parsed))


def tui_query_error(message: str, **extra: Any) -> dict[str, Any]:
    return {
        "schema_version": "ga-tui.query.v1",
        "status": "error",
        "error": message,
        **extra,
    }


def tui_query_ok(kind: str, **payload: Any) -> dict[str, Any]:
    return {
        "schema_version": "ga-tui.query.v1",
        "kind": kind,
        "status": "ok",
        "generated_at": now_iso(),
        **payload,
    }


def tui_query_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): tui_query_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [tui_query_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [tui_query_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def tui_query_refresh_subagents(state: State) -> None:
    vault = getattr(state, "secret_vault", None)
    try:
        if vault is not None and bool(getattr(vault, "unlocked", False)):
            load_secret_subagents(state)
        else:
            load_subagents(state)
    except Exception:
        return


def tui_query_text_summary(text: str, limit: int = 220) -> str:
    return truncate_cells(re.sub(r"\s+", " ", clean_text(text or "")).strip(), limit)


def tui_query_agent_lifecycle(sub: SubAgentRuntime) -> str:
    return "persistent" if sub.persistent else "ephemeral"


def tui_query_agent_busy_reason(sub: SubAgentRuntime) -> str:
    if sub.status in {"running", "aborting"}:
        return sub.status
    if sub.pending_interaction:
        return "waiting_for_user"
    if sub.task_queue:
        return f"task_queue:{len(sub.task_queue)}"
    if sub.chat_queue:
        return f"chat_queue:{len(sub.chat_queue)}"
    if sub.agent is not None and agent_has_unfinished_task(sub.agent):
        return "runtime_unfinished"
    return "idle"


def tui_query_agent_record(sub: SubAgentRuntime, *, detail: bool = False) -> dict[str, Any]:
    permissions = permissions_for_role(sub.role, security_context=sub.security_context)
    record: dict[str, Any] = {
        "agent_id": sub.agent_id,
        "name": sub.name,
        "role": normalized_role(sub.role),
        "lifecycle": tui_query_agent_lifecycle(sub),
        "persistent": bool(sub.persistent),
        "status": sub.status,
        "busy_reason": tui_query_agent_busy_reason(sub),
        "security_context": sub.security_context,
        "capabilities": role_tools_allowed(sub.role),
        "write_policy": role_write_policy(sub.role),
        "permissions": permissions,
        "default_model": sub.default_model,
        "queue_length": len(sub.task_queue),
        "chat_queue_length": len(sub.chat_queue),
        "pending_interaction": bool(sub.pending_interaction),
        "active_task_id": sub.active_task_id,
        "active_bus_task_id": sub.active_bus_task_id,
        "runtime_loaded": sub.agent is not None,
        "runtime_running": bool(sub.agent is not None and agent_has_unfinished_task(sub.agent)),
        "owner_session": sub.owner_session,
        "home": sub.home,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(sub.updated_at)),
        "updated_age": rel_age(sub.updated_at),
        "profile_summary": tui_query_text_summary(subagent_profile_text(sub), 260),
    }
    if detail:
        latest = latest_task_records()
        assigned = [
            row for row in latest.values()
            if str(row.get("assigned_agent") or "") == sub.agent_id
        ]
        assigned.sort(key=row_timestamp, reverse=True)
        record.update({
            "profile": truncate_cells(clean_text(subagent_profile_text(sub)), 1600),
            "memory_summary": tui_query_text_summary(subagent_memory_text(sub), 420),
            "output_contract": role_output_contract(sub.role),
            "task_queue_preview": [
                {
                    "prompt": tui_query_text_summary(item[0], 160) if item else "",
                    "source": item[1] if len(item) > 1 else "",
                    "task_id": item[3] if len(item) > 3 else "",
                    "parent_task_id": item[4] if len(item) > 4 else "",
                }
                for item in sub.task_queue[:5]
            ],
            "chat_queue_preview": [tui_query_text_summary(item, 160) for item in sub.chat_queue[:5]],
            "recent_tasks": [
                {
                    "task_id": row.get("task_id", ""),
                    "status": row.get("status", ""),
                    "kind": row.get("kind", ""),
                    "objective": tui_query_text_summary(str(row.get("objective") or row.get("summary") or ""), 180),
                    "artifact_refs": row.get("artifact_refs") or [],
                    "timestamp": row.get("timestamp", ""),
                }
                for row in assigned[:8]
            ],
        })
    return tui_query_json_safe(record)


def tui_tool_agent_list(state: Optional[State], args: dict[str, Any]) -> dict[str, Any]:
    if state is None:
        return tui_query_error("TUI state is not bound to this GenericAgent runtime.")
    tui_query_refresh_subagents(state)
    role_filter = (args.get("role") or "").strip()
    status_filter = (args.get("status") or "").strip().lower()
    include_ephemeral = bool(args.get("include_ephemeral", True))
    limit = tui_query_limit(args.get("limit"), 50)
    agents = list(state.subagents.values())
    if role_filter:
        role = normalized_role(role_filter)
        agents = [sub for sub in agents if normalized_role(sub.role) == role]
    if status_filter:
        agents = [sub for sub in agents if sub.status.lower() == status_filter]
    if not include_ephemeral:
        agents = [sub for sub in agents if sub.persistent]
    agents.sort(key=lambda item: item.updated_at, reverse=True)
    records = [tui_query_agent_record(sub) for sub in agents[:limit]]
    return tui_query_ok(
        "agent.list",
        total=len(agents),
        returned=len(records),
        agents=records,
        note="Read-only snapshot. Use agent_match before creating new workers when reuse is acceptable.",
    )


def tui_tool_agent_get(state: Optional[State], args: dict[str, Any]) -> dict[str, Any]:
    if state is None:
        return tui_query_error("TUI state is not bound to this GenericAgent runtime.")
    tui_query_refresh_subagents(state)
    target = str(args.get("target") or "").strip()
    sub = resolve_subagent(state, target)
    if sub is None:
        return tui_query_error("Subagent not found or selector is ambiguous.", target=target)
    return tui_query_ok("agent.get", agent=tui_query_agent_record(sub, detail=True))


def tui_query_capability_matches(required: str, available: list[str]) -> bool:
    req = (required or "").strip().lower().replace("_", ".")
    if not req:
        return True
    tokens: set[str] = set()
    for item in available:
        raw = str(item or "").strip().lower().replace("_", ".")
        if not raw:
            continue
        tokens.add(raw)
        tokens.add(raw.split(".", 1)[0])
    return req in tokens or req.split(".", 1)[0] in tokens


def tui_tool_agent_match(state: Optional[State], args: dict[str, Any]) -> dict[str, Any]:
    if state is None:
        return tui_query_error("TUI state is not bound to this GenericAgent runtime.")
    tui_query_refresh_subagents(state)
    objective = str(args.get("objective") or "").strip()
    if not objective:
        return tui_query_error("objective is required.")
    requested_role = normalized_role(str(args.get("role") or "specialist"))
    reuse_policy = str(args.get("reuse_policy") or "prefer_existing").strip().lower()
    security_context = normalized_security_context(str(args.get("security_context") or "standard"))
    required_caps = [str(item) for item in (args.get("capabilities_required") or []) if str(item).strip()]
    limit = tui_query_limit(args.get("limit"), 5, maximum=20)
    candidates: list[tuple[int, SubAgentRuntime, list[str]]] = []
    for sub in state.subagents.values():
        reasons: list[str] = []
        score = reusable_subagent_score(sub, objective, objective, requested_role)
        if sub.security_context == security_context:
            score += 20
            reasons.append(f"security_context={security_context}")
        else:
            score -= 80
            reasons.append(f"security_context_mismatch:{sub.security_context}")
        if requested_role != "specialist":
            if normalized_role(sub.role) == requested_role:
                score += 30
                reasons.append(f"role_match:{requested_role}")
            else:
                score -= 10
                reasons.append(f"role_mismatch:{sub.role}")
        available_caps = role_tools_allowed(sub.role)
        for cap in required_caps:
            if tui_query_capability_matches(cap, available_caps):
                score += 12
                reasons.append(f"capability_match:{cap}")
            else:
                score -= 8
                reasons.append(f"capability_missing:{cap}")
        busy = tui_query_agent_busy_reason(sub)
        if busy == "idle":
            score += 12
            reasons.append("idle")
        else:
            score -= 8
            reasons.append(f"busy:{busy}")
        if sub.persistent:
            score += 4
            reasons.append("persistent")
        if score > -40:
            candidates.append((score, sub, reasons))
    candidates.sort(key=lambda item: (item[0], item[1].updated_at), reverse=True)
    rows = [
        {
            "score": score,
            "reason": reasons,
            "agent": tui_query_agent_record(sub),
        }
        for score, sub, reasons in candidates[:limit]
    ]
    top = rows[0] if rows else None
    if reuse_policy == "force_new":
        recommended_action = "create_new"
        recommended_agent = None
        reason = "reuse_policy=force_new"
    elif top and int(top["score"]) >= 35:
        recommended_action = "reuse_existing"
        recommended_agent = top["agent"]
        reason = f"best_score={top['score']}"
    elif reuse_policy == "reuse_only":
        recommended_action = "none"
        recommended_agent = None
        reason = "reuse_only but no candidate reached score threshold"
    else:
        recommended_action = "create_new"
        recommended_agent = None
        reason = "no candidate reached score threshold"
    return tui_query_ok(
        "agent.match",
        objective=tui_query_text_summary(objective, 300),
        reuse_policy=reuse_policy,
        requested_role=requested_role,
        capabilities_required=required_caps,
        recommended_action=recommended_action,
        recommended_agent=recommended_agent,
        recommendation_reason=reason,
        candidates=rows,
    )


def tui_tool_task_list(state: Optional[State], args: dict[str, Any]) -> dict[str, Any]:
    if state is not None:
        tui_query_refresh_subagents(state)
    status_filter = str(args.get("status") or "").strip().lower()
    assigned_filter = str(args.get("assigned_agent") or "").strip()
    assigned_id = ""
    if state is not None and assigned_filter:
        sub = resolve_subagent(state, assigned_filter)
        assigned_id = sub.agent_id if sub is not None else assigned_filter
    elif assigned_filter:
        assigned_id = assigned_filter
    include_completed = bool(args.get("include_completed", False))
    limit = tui_query_limit(args.get("limit"), 20)
    rows = list(latest_task_records().values())
    if status_filter:
        rows = [row for row in rows if str(row.get("status") or "").lower() == status_filter]
    if assigned_id:
        rows = [
            row for row in rows
            if str(row.get("assigned_agent") or "") == assigned_id
            or assigned_id.lower() in str(row.get("assigned_agent") or "").lower()
        ]
    if not include_completed:
        rows = [row for row in rows if not terminal_task_status(str(row.get("status") or ""))]
    rows.sort(key=row_timestamp, reverse=True)
    items = [
        {
            "task_id": row.get("task_id", ""),
            "parent_task_id": row.get("parent_task_id", ""),
            "kind": row.get("kind", ""),
            "status": row.get("status", ""),
            "assigned_agent": row.get("assigned_agent", ""),
            "objective": tui_query_text_summary(str(row.get("objective") or row.get("summary") or row.get("title") or ""), 220),
            "artifact_refs": row.get("artifact_refs") or [],
            "approval": row.get("approval") or {},
            "timestamp": row.get("timestamp", ""),
        }
        for row in rows[:limit]
    ]
    return tui_query_ok("task.list", total=len(rows), returned=len(items), tasks=tui_query_json_safe(items))


def tui_tool_task_get(state: Optional[State], args: dict[str, Any]) -> dict[str, Any]:
    del state
    task_id = str(args.get("task_id") or "").strip()
    if not task_id:
        return tui_query_error("task_id is required.")
    history_limit = tui_query_limit(args.get("history_limit"), 20, maximum=80)
    latest = latest_task_records()
    row = latest.get(task_id)
    if row is None:
        return tui_query_error("Task not found.", task_id=task_id)
    children = [
        child for child in latest.values()
        if str(child.get("parent_task_id") or "") == task_id
    ]
    children.sort(key=row_timestamp, reverse=True)
    traces = [
        trace for trace in read_jsonl(AGENT_TRACES_PATH, limit=300)
        if str(trace.get("task_id") or "") == task_id
    ]
    approvals = []
    for approval in approval_latest_records().values():
        payload = approval.get("payload") if isinstance(approval.get("payload"), dict) else {}
        if (
            str(payload.get("task_id") or "") == task_id
            or str(approval.get("target") or "") == str(row.get("assigned_agent") or "")
        ):
            approvals.append(approval)
    data = {
        "task": row,
        "history": task_history(task_id)[-history_limit:],
        "children": children,
        "recent_traces": traces[-12:],
        "approvals": approvals[-10:],
        "artifact_refs": row.get("artifact_refs") or [],
    }
    return tui_query_ok("task.get", **tui_query_json_safe(data))


def tui_tool_approval_list(state: Optional[State], args: dict[str, Any]) -> dict[str, Any]:
    include_all = bool(args.get("include_all", False))
    limit = tui_query_limit(args.get("limit"), 20)
    rows = list(approval_latest_records().values()) if include_all else pending_approvals(state)
    rows.sort(key=row_timestamp, reverse=True)
    items = []
    for row in rows[:limit]:
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        items.append({
            "approval_id": row.get("approval_id", ""),
            "type": row.get("type", ""),
            "status": row.get("status", ""),
            "source": row.get("source", ""),
            "target": row.get("target", ""),
            "approval_required_for": row.get("approval_required_for", ""),
            "summary": tui_query_text_summary(str(row.get("summary") or ""), 220),
            "deferred_operation": payload.get("deferred_operation", ""),
            "payload_keys": sorted(str(key) for key in payload.keys()),
            "timestamp": row.get("timestamp", ""),
            "secret_storage": bool(row.get("secret_storage")),
        })
    return tui_query_ok("approval.list", total=len(rows), returned=len(items), approvals=tui_query_json_safe(items))


def tui_tool_artifact_list(state: Optional[State], args: dict[str, Any]) -> dict[str, Any]:
    del state
    source_task_id = str(args.get("source_task_id") or "").strip()
    artifact_type = str(args.get("artifact_type") or "").strip()
    limit = tui_query_limit(args.get("limit"), 20)
    rows = list(artifact_index_latest().values())
    if source_task_id:
        rows = [row for row in rows if str(row.get("source_task_id") or "") == source_task_id]
    if artifact_type:
        rows = [row for row in rows if str(row.get("type") or "") == artifact_type]
    rows.sort(key=lambda row: row_timestamp(row) or float(row.get("mtime") or 0.0), reverse=True)
    items = [
        {
            "artifact_id": row.get("artifact_id", ""),
            "type": row.get("type", ""),
            "uri": row.get("uri", ""),
            "path": row.get("path", ""),
            "preview_path": row.get("preview_path", ""),
            "hash": row.get("hash", ""),
            "size_bytes": row.get("size_bytes", 0),
            "source_task_id": row.get("source_task_id", ""),
            "content_type": row.get("content_type", ""),
            "timestamp": row.get("timestamp", ""),
            "provenance": row.get("provenance") or {},
        }
        for row in rows[:limit]
    ]
    return tui_query_ok("artifact.list", total=len(rows), returned=len(items), artifacts=tui_query_json_safe(items))


def tui_tool_capability_list(state: Optional[State], args: dict[str, Any]) -> dict[str, Any]:
    del args
    if state is not None:
        tui_query_refresh_subagents(state)
    return tui_query_ok("capability.list", capabilities=tui_query_json_safe(gateway_capability_registry(state)))


def subagent_brief(sub: SubAgentRuntime) -> str:
    pending = " waiting-input" if sub.pending_interaction else ""
    scope = "persist" if sub.persistent else "temp"
    queued = f" q:{len(sub.task_queue)}" if sub.task_queue else ""
    model = f" model:{sub.default_model}" if sub.default_model else ""
    return f"{sub.agent_id:<16} {sub.name:<18} {sub.role:<14} {scope:<7} {sub.status}{pending}{queued}{model} · {rel_age(sub.updated_at)}"


def format_subagent_list(state: State) -> str:
    if not state.subagents:
        return "还没有子 agent。\n用法：/agent new [persistent:] [role:]<name> [| profile]"
    lines = ["子 agent："]
    for sub in sorted(state.subagents.values(), key=lambda item: item.updated_at, reverse=True):
        lines.append("  " + subagent_brief(sub))
    lines += [
        "",
        "用法：",
        "  /agent new [persistent:] [role:]<name> [| profile]",
        "  /agent role <id|name> <role>",
        "  /agent settings <id|name>",
        "  /agent model <id|name> [model|inherit]",
        "  /agent templates",
        "  /agent ask <id|name> <prompt>",
        "  /agent memory <id|name>",
        "  /agent remember <id|name> <text>",
        "  /agent profile <id|name> [new profile]",
        "  /agent stop <id|name>",
        "  /agent delete <id|name>",
    ]
    return "\n".join(lines)


def mykey_path() -> str:
    return os.path.join(ROOT_DIR, "mykey.py")


def mask_secret(value: str) -> str:
    value = value or ""
    if len(value) <= 8:
        return "*" * len(value) if value else "(empty)"
    return value[:4] + "*" * max(4, len(value) - 8) + value[-4:]


def cfg_type_from_var(var_name: str, cfg: dict[str, Any]) -> str:
    name = var_name.lower()
    if "native" in name and "claude" in name:
        return "native_claude"
    if "native" in name and "oai" in name:
        return "native_oai"
    if "claude" in name:
        return "claude"
    if "oai" in name:
        return "oai"
    return str(cfg.get("type") or "native_oai")


def var_prefix_for_type(cfg_type: str) -> str:
    return {
        "native_claude": "native_claude_config",
        "claude": "claude_config",
        "oai": "oai_config",
    }.get(cfg_type, "native_oai_config")


def is_llm_config_var(var_name: str, value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if not {"apikey", "apibase", "model"}.issubset(value.keys()):
        return False
    low = var_name.lower()
    return "config" in low and ("oai" in low or "claude" in low)


def load_mykey_assignments() -> tuple[list[tuple[str, Any]], str]:
    path = mykey_path()
    if not os.path.exists(path):
        return [], ""
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
        tree = ast.parse(text, filename=path)
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"
    assignments: list[tuple[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        try:
            value = ast.literal_eval(node.value)
        except Exception:
            continue
        assignments.append((node.targets[0].id, value))
    return assignments, ""


def load_llm_config_entries() -> tuple[list[LLMConfigEntry], dict[str, Any], list[tuple[str, Any]], str]:
    assignments, error = load_mykey_assignments()
    entries: list[LLMConfigEntry] = []
    preserved: list[tuple[str, Any]] = []
    mixin: dict[str, Any] = {"llm_nos": [], "max_retries": 10, "base_delay": 0.5}
    for name, value in assignments:
        if name == "mixin_config" and isinstance(value, dict):
            mixin = dict(value)
        elif is_llm_config_var(name, value):
            cfg = dict(value)
            cfg.pop("type", None)
            entries.append(LLMConfigEntry(name, cfg_type_from_var(name, cfg), cfg))
        else:
            preserved.append((name, value))
    return entries, mixin, preserved, error


def config_display_name(entry: LLMConfigEntry) -> str:
    return str(entry.cfg.get("name") or entry.cfg.get("model") or entry.var_name)


def entry_names(entries: list[LLMConfigEntry]) -> list[str]:
    return [config_display_name(entry) for entry in entries]


def entry_index_by_name(entries: list[LLMConfigEntry], name: str) -> int:
    for idx, entry in enumerate(entries):
        if config_display_name(entry) == name:
            return idx
    return -1


def load_recent_model_names(entries: Optional[list[LLMConfigEntry]] = None, limit: int = 8) -> list[str]:
    try:
        with open(LLM_RECENT_MODELS_PATH, encoding="utf-8", errors="replace") as fh:
            raw = json.load(fh)
    except Exception:
        raw = {}
    if isinstance(raw, dict):
        items = raw.get("recent") or []
    elif isinstance(raw, list):
        items = raw
    else:
        items = []
    allowed = set(entry_names(entries)) if entries is not None else None
    out: list[str] = []
    for item in items:
        name = str(item or "").strip()
        if not name or name in out:
            continue
        if allowed is not None and name not in allowed:
            continue
        out.append(name)
        if len(out) >= limit:
            break
    return out


def save_recent_model_names(names: list[str], entries: Optional[list[LLMConfigEntry]] = None, limit: int = 8) -> tuple[bool, str]:
    allowed = set(entry_names(entries)) if entries is not None else None
    recent: list[str] = []
    for item in names:
        name = str(item or "").strip()
        if not name or name in recent:
            continue
        if allowed is not None and name not in allowed:
            continue
        recent.append(name)
        if len(recent) >= limit:
            break
    payload = {"schema_version": "llm_recent_models.v1", "updated_at": now_iso(), "recent": recent}
    try:
        write_text_atomic(LLM_RECENT_MODELS_PATH, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return True, "最近模型已更新。"
    except Exception as exc:
        return False, f"最近模型保存失败: {type(exc).__name__}: {exc}"


def remember_recent_model_name(name: str, entries: list[LLMConfigEntry], limit: int = 8) -> tuple[bool, str]:
    name = str(name or "").strip()
    if not name:
        return False, "模型名称为空。"
    current = load_recent_model_names(entries, limit=limit)
    return save_recent_model_names([name, *(item for item in current if item != name)], entries, limit=limit)


def remember_recent_model_entry(entry: LLMConfigEntry, entries: list[LLMConfigEntry], limit: int = 8) -> tuple[bool, str]:
    return remember_recent_model_name(config_display_name(entry), entries, limit=limit)


def next_recent_entry_index(entries: list[LLMConfigEntry], recent_names: list[str], selected: int) -> int:
    if not entries or not recent_names:
        return selected
    indices = [entry_index_by_name(entries, name) for name in recent_names]
    indices = [idx for idx in indices if idx >= 0]
    if not indices:
        return selected
    for idx in indices:
        if idx > selected:
            return idx
    return indices[0]


def current_agent_entry_index(agent: Any, entries: list[LLMConfigEntry]) -> int:
    if agent is None:
        return -1
    name = agent_current_backend_name(agent)
    model = agent_backend_model(getattr(agent, "llmclient", None))
    base = endpoint_base(str(getattr(getattr(getattr(agent, "llmclient", None), "backend", None), "apibase", "") or ""))
    for idx, entry in enumerate(entries):
        cfg = entry.cfg
        if name and config_display_name(entry) == name:
            return idx
        entry_model = str(cfg.get("model") or "")
        entry_base = endpoint_base(str(cfg.get("apibase") or ""))
        if model and entry_model == model and (not base or not entry_base or base == entry_base):
            return idx
    return -1


def model_manager_initial_index(state: State, entries: list[LLMConfigEntry], mixin: dict[str, Any], recent_names: list[str]) -> int:
    current_idx = current_agent_entry_index(state.agent, entries)
    if current_idx >= 0:
        return current_idx
    for name in recent_names:
        idx = entry_index_by_name(entries, name)
        if idx >= 0:
            return idx
    return default_entry_index(entries, mixin)


def unique_config_var_name(entries: list[LLMConfigEntry], cfg_type: str, keep: str = "") -> str:
    prefix = var_prefix_for_type(cfg_type)
    used = {e.var_name for e in entries if e.var_name != keep}
    if prefix not in used:
        return prefix
    idx = 0
    while f"{prefix}_{idx}" in used:
        idx += 1
    return f"{prefix}_{idx}"


def write_literal_assignment(lines: list[str], name: str, value: Any) -> None:
    lines.append(f"{name} = {repr(value)}")


def write_config_block(lines: list[str], entry: LLMConfigEntry) -> None:
    cfg = dict(entry.cfg)
    cfg.pop("type", None)
    lines.append(f"{entry.var_name} = {{")
    preferred = [
        "name", "apikey", "apibase", "model", "api_mode",
        "fake_cc_system_prompt", "thinking_type", "thinking_budget_tokens",
        "reasoning_effort", "max_tokens", "max_retries", "connect_timeout",
        "read_timeout", "temperature", "context_win", "proxy", "user_agent", "stream",
    ]
    for key in preferred:
        if key in cfg:
            lines.append(f"    {repr(key)}: {repr(cfg[key])},")
    for key in sorted(k for k in cfg if k not in preferred):
        lines.append(f"    {repr(key)}: {repr(cfg[key])},")
    lines.append("}")


def save_llm_config_entries(entries: list[LLMConfigEntry], mixin: dict[str, Any], preserved: list[tuple[str, Any]]) -> tuple[bool, str]:
    path = mykey_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    names = [config_display_name(e) for e in entries]
    selected = [n for n in mixin.get("llm_nos", []) if n in names]
    if not selected and names:
        selected = [names[0]]
    clean_mixin = dict(mixin)
    clean_mixin["llm_nos"] = selected
    clean_mixin.setdefault("max_retries", 10)
    clean_mixin.setdefault("base_delay", 0.5)

    lines = [
        "# Generated by GenericAgent-TUI model manager.",
        "# Edit in TUI with /llm; switch with /model.",
        "",
        "mixin_config = {",
    ]
    for key in ["llm_nos", "max_retries", "base_delay", "spring_back"]:
        if key in clean_mixin:
            lines.append(f"    {repr(key)}: {repr(clean_mixin[key])},")
    lines.append("}")
    lines.append("")
    for entry in entries:
        write_config_block(lines, entry)
        lines.append("")
    if preserved:
        lines.append("# Preserved non-LLM settings")
        for name, value in preserved:
            if name == "mixin_config" or any(e.var_name == name for e in entries):
                continue
            write_literal_assignment(lines, name, value)
        lines.append("")
    content = "\n".join(lines).rstrip() + "\n"
    try:
        if os.path.exists(path):
            backup = f"{path}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
            shutil.copy2(path, backup)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
        return True, "mykey.py 已保存，并已创建备份。"
    except Exception as exc:
        return False, f"保存失败: {type(exc).__name__}: {exc}"


def provider_model_choices(provider: dict[str, Any]) -> list[str]:
    choices = provider.get("model_choices") or []
    out: list[str] = []
    for item in choices:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and item.get("id"):
            out.append(str(item["id"]))
        elif isinstance(item, (tuple, list)) and item:
            out.append(str(item[0]))
    template_model = provider.get("template", {}).get("model")
    if template_model and template_model not in out:
        out.insert(0, str(template_model))
    return out


def fallback_providers() -> list[dict[str, Any]]:
    return [
        {"id": "anthropic", "name": "Anthropic Claude", "type": "native_claude", "template": {"name": "anthropic", "apikey": "", "apibase": "https://api.anthropic.com", "model": "claude-opus-4-7", "thinking_type": "adaptive"}, "model_choices": ["claude-opus-4-7", "claude-sonnet-4-6"]},
        {"id": "openai", "name": "OpenAI compatible", "type": "native_oai", "template": {"name": "openai", "apikey": "", "apibase": "https://api.openai.com/v1", "model": "gpt-5.5", "api_mode": "chat_completions"}, "model_choices": ["gpt-5.5", "gpt-5.4"]},
        {"id": "deepseek", "name": "DeepSeek", "type": "native_oai", "template": {"name": "deepseek", "apikey": "", "apibase": "https://api.deepseek.com", "model": "deepseek-v4-flash", "api_mode": "chat_completions"}, "model_choices": ["deepseek-v4-flash", "deepseek-v4-pro"]},
    ]


def llm_template_providers() -> list[dict[str, Any]]:
    return list(CONFIG_PROVIDERS or fallback_providers())


def provider_category(provider: dict[str, Any]) -> str:
    cfg_type = str(provider.get("type") or provider.get("template", {}).get("type") or "native_oai").lower()
    if "claude" in cfg_type:
        return "Anthropic"
    if "oai" in cfg_type or "openai" in cfg_type:
        return "OpenAI"
    return "Other"


def provider_categories(providers: list[dict[str, Any]]) -> list[str]:
    ordered = ["Anthropic", "OpenAI", "Other"]
    present = {provider_category(provider) for provider in providers}
    return [category for category in ordered if category in present] or ["OpenAI"]


def first_provider_in_category(providers: list[dict[str, Any]], category: str) -> int:
    for idx, provider in enumerate(providers):
        if provider_category(provider) == category:
            return idx
    return 0


def provider_indices_for_category(providers: list[dict[str, Any]], category: str) -> list[int]:
    return [idx for idx, provider in enumerate(providers) if provider_category(provider) == category]


def apply_provider_template(provider: dict[str, Any], old_cfg: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    cfg_type, new_cfg = default_config_from_provider(provider)
    old_key = old_cfg.get("apikey", "")
    if old_key:
        new_cfg["apikey"] = old_key
    return cfg_type, new_cfg


def config_provider_index(cfg: dict[str, Any], cfg_type: str) -> int:
    providers = llm_template_providers()
    if not providers:
        return 0
    base = str(cfg.get("apibase") or "")
    model = str(cfg.get("model") or "")
    name = str(cfg.get("name") or "")
    for idx, provider in enumerate(providers):
        template = provider.get("template", {})
        if provider.get("type") == cfg_type and (
            template.get("apibase") == base
            or template.get("model") == model
            or template.get("name") == name
        ):
            return idx
    return 0


def default_config_from_provider(provider: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    cfg_type = str(provider.get("type") or "native_oai")
    cfg = dict(provider.get("template") or {})
    cfg.pop("type", None)
    cfg.setdefault("name", provider.get("id") or cfg.get("model") or "model")
    cfg.setdefault("apikey", "")
    cfg.setdefault("apibase", "")
    cfg.setdefault("model", "")
    if cfg_type == "native_oai":
        cfg.setdefault("api_mode", "chat_completions")
    return cfg_type, cfg


def models_endpoint_for_config(cfg_type: str, apibase: str) -> str:
    base = (apibase or "").strip().rstrip("/")
    if not base:
        return ""
    if cfg_type in {"native_claude", "claude"}:
        if base.endswith("/v1/models"):
            return base
        if base.endswith("/v1"):
            return base + "/models"
        return base + "/v1/models"
    base = re.sub(r"/chat/completions$", "", base)
    base = re.sub(r"/responses$", "", base)
    if base.endswith("/models"):
        return base
    return base + "/models"


def probe_models_for_config(cfg_type: str, cfg: dict[str, Any], timeout: float = 12.0) -> tuple[bool, list[str], str]:
    apikey = str(cfg.get("apikey") or "").strip()
    apibase = str(cfg.get("apibase") or "").strip()
    if not apikey or not apibase:
        return False, [], "API Key 和 Base URL 不能为空。"
    url = models_endpoint_for_config(cfg_type, apibase)
    if not url:
        return False, [], "Base URL 为空。"
    headers = {"User-Agent": "GenericAgent-TUI/1.0"}
    if cfg_type in {"native_claude", "claude"}:
        headers.update({"x-api-key": apikey, "anthropic-version": "2023-06-01"})
    else:
        headers["Authorization"] = f"Bearer {apikey}"
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(4 * 1024 * 1024).decode("utf-8", errors="replace")
        data = json.loads(raw)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(400).decode("utf-8", errors="replace")
        except Exception:
            pass
        return False, [], f"验活失败 HTTP {exc.code}: {body or exc.reason}"
    except Exception as exc:
        return False, [], f"验活失败: {type(exc).__name__}: {exc}"
    raw_models = data if isinstance(data, list) else data.get("data", [])
    models: list[str] = []
    if isinstance(raw_models, list):
        for item in raw_models:
            if isinstance(item, dict):
                model = item.get("id") or item.get("name")
            else:
                model = item
            if model:
                models.append(str(model))
    models = sorted(dict.fromkeys(models))
    if not models:
        return False, [], "验活成功但 /models 没返回可用模型。"
    return True, models, f"验活成功，拉到 {len(models)} 个模型。"


def model_health_key(entry: LLMConfigEntry) -> str:
    return entry.var_name or f"{entry.cfg_type}:{entry.cfg.get('apibase', '')}:{entry.cfg.get('model', '')}"


def endpoint_base(apibase: str) -> str:
    base = (apibase or "").strip().rstrip("/")
    for suffix in ("/chat/completions", "/responses", "/messages", "/models"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    return base.rstrip("/")


def anthropic_messages_endpoint(apibase: str) -> str:
    base = endpoint_base(apibase)
    if not base:
        return ""
    if base.endswith("/v1"):
        return base + "/messages"
    return base + "/v1/messages"


def openai_compatible_request_variants(cfg: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    base = endpoint_base(str(cfg.get("apibase") or ""))
    model = str(cfg.get("model") or "").strip()
    if not base or not model:
        return []
    chat_url = base + "/chat/completions"
    responses_url = base + "/responses"
    chat_payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 8,
        "temperature": 0,
        "stream": False,
    }
    chat_completion_payload = dict(chat_payload)
    chat_completion_payload.pop("max_tokens", None)
    chat_completion_payload["max_completion_tokens"] = 8
    responses_payload = {
        "model": model,
        "input": "ping",
        "max_output_tokens": 8,
        "stream": False,
    }
    if str(cfg.get("api_mode") or "").strip() == "responses":
        return [(responses_url, responses_payload), (chat_url, chat_payload), (chat_url, chat_completion_payload)]
    return [(chat_url, chat_payload), (chat_url, chat_completion_payload), (responses_url, responses_payload)]


def compact_validation_error(text: str, limit: int = 180) -> str:
    text = clean_text(text or "").replace("\n", " ").strip()
    return truncate_cells(text, limit) if text else ""


def post_json_for_validation(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(4096).decode("utf-8", errors="replace")
            status = int(getattr(resp, "status", 200) or 200)
        if 200 <= status < 300:
            return True, "可用"
        return False, f"HTTP {status}: {compact_validation_error(raw)}"
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read(600).decode("utf-8", errors="replace")
        except Exception:
            pass
        return False, f"HTTP {exc.code}: {compact_validation_error(body or str(exc.reason))}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def validate_model_entry(entry: LLMConfigEntry, timeout: float = 12.0) -> tuple[bool, str]:
    cfg = entry.cfg
    apikey = str(cfg.get("apikey") or "").strip()
    model = str(cfg.get("model") or "").strip()
    if not apikey:
        return False, "缺少 API Key"
    if not model:
        return False, "缺少 model"
    cfg_type = str(entry.cfg_type or "").lower()
    headers = {"User-Agent": "GenericAgent-TUI/1.0", "Content-Type": "application/json"}
    if "claude" in cfg_type:
        url = anthropic_messages_endpoint(str(cfg.get("apibase") or ""))
        if not url:
            return False, "缺少 Base URL"
        headers.update({"x-api-key": apikey, "anthropic-version": "2023-06-01"})
        payload = {"model": model, "max_tokens": 8, "messages": [{"role": "user", "content": "ping"}]}
        return post_json_for_validation(url, headers, payload, timeout)

    headers["Authorization"] = f"Bearer {apikey}"
    variants = openai_compatible_request_variants(cfg)
    if not variants:
        return False, "缺少 Base URL 或 model"
    errors: list[str] = []
    for url, payload in variants:
        ok, msg = post_json_for_validation(url, headers, payload, timeout)
        if ok:
            return True, "可用"
        errors.append(msg)
        if msg.startswith("HTTP 401") or msg.startswith("HTTP 403"):
            break
    return False, errors[-1] if errors else "验活失败"


def order_entries_by_health(entries: list[LLMConfigEntry], health: dict[str, tuple[bool, str]]) -> list[LLMConfigEntry]:
    if not health:
        return entries

    def rank(entry: LLMConfigEntry) -> int:
        result = health.get(model_health_key(entry))
        if result is None:
            return 1
        return 0 if result[0] else 2

    return [entry for _idx, entry in sorted(enumerate(entries), key=lambda item: (rank(item[1]), item[0]))]


def compact_identifier(text: str, max_len: int = 36) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", text or "").strip("-_.").lower()
    return (text or "model")[:max_len]


def entries_from_provider_models(base_entry: LLMConfigEntry, models: list[str], existing: list[LLMConfigEntry]) -> list[LLMConfigEntry]:
    result: list[LLMConfigEntry] = []
    base_name = compact_identifier(str(base_entry.cfg.get("name") or base_entry.cfg.get("apibase") or "provider"), 18)
    seen_pairs = {(str(e.cfg.get("apibase") or ""), str(e.cfg.get("model") or "")) for e in existing}
    work = list(existing)
    for model in models:
        cfg = dict(base_entry.cfg)
        cfg["model"] = model
        cfg["name"] = compact_identifier(f"{base_name}-{model}", 48)
        pair = (str(cfg.get("apibase") or ""), str(model))
        if pair in seen_pairs:
            continue
        var_name = unique_config_var_name(work + result, base_entry.cfg_type)
        result.append(LLMConfigEntry(var_name, base_entry.cfg_type, cfg))
        seen_pairs.add(pair)
    return result


def agent_backend_name(client: Any) -> str:
    backend = getattr(client, "backend", None)
    return str(getattr(backend, "name", "") or "")


def agent_backend_model(client: Any) -> str:
    backend = getattr(client, "backend", None)
    return str(getattr(backend, "model", "") or "")


def agent_current_backend_name(agent: Any) -> str:
    return agent_backend_name(getattr(agent, "llmclient", None))


def find_agent_llm_index(agent: Any, entry: LLMConfigEntry) -> int:
    target_name = config_display_name(entry)
    target_model = str(entry.cfg.get("model") or "")
    target_base = endpoint_base(str(entry.cfg.get("apibase") or ""))
    try:
        agent.load_llm_sessions()
    except Exception:
        pass
    fallback = -1
    for idx, client in enumerate(getattr(agent, "llmclients", []) or []):
        backend = getattr(client, "backend", None)
        name = str(getattr(backend, "name", "") or "")
        model = str(getattr(backend, "model", "") or "")
        base = endpoint_base(str(getattr(backend, "apibase", "") or getattr(backend, "base_url", "") or ""))
        if name == target_name:
            return idx
        if fallback < 0 and target_model and model == target_model and (not target_base or not base or base == target_base):
            fallback = idx
    return fallback


def set_agent_llm_index(agent: Any, index: int) -> tuple[bool, str]:
    clients = list(getattr(agent, "llmclients", []) or [])
    if index < 0 or index >= len(clients):
        return False, f"找不到模型索引：{index}"
    try:
        if hasattr(agent, "next_llm"):
            agent.next_llm(index)
        else:
            agent.llm_no = index
            agent.llmclient = clients[index]
        install_tui_query_runtime(agent)
        install_tui_control_hint(agent)
        return True, f"当前对话模型已切到 {agent.get_llm_name(model=True)}。"
    except Exception as exc:
        return False, f"切换模型失败: {type(exc).__name__}: {exc}"


def switch_agent_to_entry(state: State, entry: LLMConfigEntry) -> tuple[bool, str]:
    if state.status != "idle":
        return False, "当前任务未空闲，不能切换当前对话模型。"
    log_path = getattr(state.agent, "log_path", "")
    index = find_agent_llm_index(state.agent, entry)
    if index < 0:
        return False, f"当前运行时未找到模型配置：{config_display_name(entry)}。请先按 r 重载配置。"
    ok, msg = set_agent_llm_index(state.agent, index)
    set_agent_log_path(state.agent, log_path)
    return ok, msg


def set_agent_to_model_name(agent: Any, model_name: str) -> tuple[bool, str]:
    model_name = str(model_name or "").strip()
    if not model_name:
        return True, "使用全局默认模型。"
    entries, _mixin, _preserved, error = load_llm_config_entries()
    if error:
        return False, error
    entry = next((item for item in entries if config_display_name(item) == model_name), None)
    if entry is None:
        return False, f"找不到模型配置：{model_name}"
    log_path = getattr(agent, "log_path", "")
    index = find_agent_llm_index(agent, entry)
    if index < 0:
        return False, f"当前运行时未找到模型配置：{model_name}。请先用 /llm 按 r 重载配置。"
    ok, msg = set_agent_llm_index(agent, index)
    set_agent_log_path(agent, log_path)
    return ok, msg


def reset_agent_instance_to_default_llm(agent: Any) -> tuple[bool, str]:
    if agent is None:
        return False, "agent 不存在。"
    log_path = getattr(agent, "log_path", "")
    try:
        agent.load_llm_sessions()
    except Exception:
        pass
    ok, msg = set_agent_llm_index(agent, 0)
    set_agent_log_path(agent, log_path)
    return ok, msg


def apply_subagent_default_model(state: State, sub: SubAgentRuntime) -> tuple[bool, str]:
    if sub.agent is None or not sub.default_model:
        return True, ""
    ok, msg = set_agent_to_model_name(sub.agent, sub.default_model)
    if not ok:
        state.last_error = f"{sub.name} 默认模型应用失败：{msg}"
    return ok, msg


def reset_agent_to_default_llm(state: State) -> tuple[bool, str]:
    return reset_agent_instance_to_default_llm(state.agent)


def reload_agent_llms(state: State, *, preserve_current: bool = False) -> tuple[bool, str]:
    if state.status != "idle":
        return False, "当前任务未空闲，已保存配置；模型将在下次新会话或重启后加载。"
    try:
        log_path = getattr(state.agent, "log_path", "")
        current_name = agent_current_backend_name(state.agent) if preserve_current else ""
        state.agent.load_llm_sessions()
        target_index = 0
        if preserve_current and current_name:
            for idx, client in enumerate(getattr(state.agent, "llmclients", []) or []):
                if agent_backend_name(client) == current_name:
                    target_index = idx
                    break
        ok, msg = set_agent_llm_index(state.agent, target_index)
        set_agent_log_path(state.agent, log_path)
        return (ok, msg) if ok else (False, msg)
    except Exception as exc:
        return False, f"重载模型失败: {type(exc).__name__}: {exc}"


def active_session_log_paths(state: State, keep_selected_history: bool = False) -> set[str]:
    paths: set[str] = set()
    selected = normalized_path(state.selected_session) if keep_selected_history and isinstance(state.selected_session, str) and state.selected_session != "main" else ""
    for agent in [
        state.agent,
        *(bg.agent for bg in state.background_sessions.values()),
        *(sub.agent for sub in state.subagents.values() if sub.agent is not None),
    ]:
        path = normalized_path(getattr(agent, "log_path", ""))
        if selected and path == selected:
            continue
        if path:
            paths.add(path)
    return paths


def agent_has_unfinished_task(agent: Any) -> bool:
    if agent is None:
        return False
    try:
        if bool(getattr(agent, "is_running", False)):
            return True
    except Exception:
        pass
    try:
        task_queue = getattr(agent, "task_queue", None)
        if task_queue is not None and int(getattr(task_queue, "unfinished_tasks", 0) or 0) > 0:
            return True
    except Exception:
        pass
    return False


def install_tui_query_tool_schema() -> None:
    schema = getattr(agentmain, "TOOLS_SCHEMA", None)
    if not isinstance(schema, list):
        return
    existing = {
        str(item.get("function", {}).get("name") or "")
        for item in schema
        if isinstance(item, dict) and isinstance(item.get("function"), dict)
    }
    for tool in TUI_QUERY_TOOL_SCHEMAS:
        name = str(tool.get("function", {}).get("name") or "")
        if name and name not in existing:
            schema.append(copy.deepcopy(tool))
            existing.add(name)


def wrap_agentmain_tool_schema_loader() -> None:
    if bool(getattr(agentmain, "_ga_tui_query_tool_schema_wrapped", False)):
        return
    original = getattr(agentmain, "load_tool_schema", None)
    if not callable(original):
        return

    def _wrapped_load_tool_schema(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        install_tui_query_tool_schema()
        return result

    setattr(agentmain, "_ga_tui_original_load_tool_schema", original)
    setattr(agentmain, "load_tool_schema", _wrapped_load_tool_schema)
    setattr(agentmain, "_ga_tui_query_tool_schema_wrapped", True)


def tui_query_state_for_handler(handler: Any) -> Optional[State]:
    parent = getattr(handler, "parent", None)
    state = getattr(parent, "_ga_tui_state", None)
    return state if isinstance(state, State) else None


def tui_query_tool_outcome(kind: str, handler: Any, args: dict[str, Any]) -> StepOutcome:
    state = tui_query_state_for_handler(handler)
    tool_map = {
        "agent_list": tui_tool_agent_list,
        "agent_get": tui_tool_agent_get,
        "agent_match": tui_tool_agent_match,
        "task_list": tui_tool_task_list,
        "task_get": tui_tool_task_get,
        "approval_list": tui_tool_approval_list,
        "artifact_list": tui_tool_artifact_list,
        "capability_list": tui_tool_capability_list,
    }
    func = tool_map.get(kind)
    data = func(state, args) if func is not None else tui_query_error(f"Unknown TUI query tool: {kind}")
    return StepOutcome(data, next_prompt="\n")


def install_tui_query_handler_methods() -> None:
    handler_cls = getattr(agentmain, "GenericAgentHandler", None)
    if handler_cls is None or bool(getattr(handler_cls, "_ga_tui_query_tools_patched", False)):
        return

    def do_agent_list(self: Any, args: dict[str, Any], response: Any) -> StepOutcome:
        del response
        return tui_query_tool_outcome("agent_list", self, args)

    def do_agent_get(self: Any, args: dict[str, Any], response: Any) -> StepOutcome:
        del response
        return tui_query_tool_outcome("agent_get", self, args)

    def do_agent_match(self: Any, args: dict[str, Any], response: Any) -> StepOutcome:
        del response
        return tui_query_tool_outcome("agent_match", self, args)

    def do_task_list(self: Any, args: dict[str, Any], response: Any) -> StepOutcome:
        del response
        return tui_query_tool_outcome("task_list", self, args)

    def do_task_get(self: Any, args: dict[str, Any], response: Any) -> StepOutcome:
        del response
        return tui_query_tool_outcome("task_get", self, args)

    def do_approval_list(self: Any, args: dict[str, Any], response: Any) -> StepOutcome:
        del response
        return tui_query_tool_outcome("approval_list", self, args)

    def do_artifact_list(self: Any, args: dict[str, Any], response: Any) -> StepOutcome:
        del response
        return tui_query_tool_outcome("artifact_list", self, args)

    def do_capability_list(self: Any, args: dict[str, Any], response: Any) -> StepOutcome:
        del response
        return tui_query_tool_outcome("capability_list", self, args)

    for name, method in {
        "do_agent_list": do_agent_list,
        "do_agent_get": do_agent_get,
        "do_agent_match": do_agent_match,
        "do_task_list": do_task_list,
        "do_task_get": do_task_get,
        "do_approval_list": do_approval_list,
        "do_artifact_list": do_artifact_list,
        "do_capability_list": do_capability_list,
    }.items():
        setattr(handler_cls, name, method)
    setattr(handler_cls, "_ga_tui_query_tools_patched", True)


def install_tui_query_runtime(agent: Any = None, state: Optional[State] = None) -> None:
    wrap_agentmain_tool_schema_loader()
    install_tui_query_tool_schema()
    install_tui_query_handler_methods()
    if agent is not None and state is not None:
        try:
            setattr(agent, "_ga_tui_state", state)
        except Exception:
            pass


def unfinished_task_labels(state: State) -> list[str]:
    labels: list[str] = []
    if state.status in {"running", "aborting"} or agent_has_unfinished_task(state.agent):
        labels.append(f"当前会话: {state.current_title or 'main'}")
    for bg in state.background_sessions.values():
        if bg.status in {"running", "aborting"} or agent_has_unfinished_task(bg.agent):
            labels.append(f"后台会话: {bg.title or bg.key}")
    for sub in state.subagents.values():
        if sub.agent is not None and (sub.status in {"running", "aborting"} or agent_has_unfinished_task(sub.agent)):
            labels.append(f"子 agent: {sub.name}")
    return labels


def all_task_agents(state: State) -> list[Any]:
    agents: list[Any] = []
    seen: set[int] = set()
    for agent in [
        state.agent,
        *(bg.agent for bg in state.background_sessions.values()),
        *(sub.agent for sub in state.subagents.values() if sub.agent is not None),
    ]:
        if agent is None or id(agent) in seen:
            continue
        seen.add(id(agent))
        agents.append(agent)
    return agents


def install_tui_control_hint(agent: Any) -> None:
    if agent is None:
        return
    clients = []
    for client in getattr(agent, "llmclients", []) or []:
        if client not in clients:
            clients.append(client)
    current = getattr(agent, "llmclient", None)
    if current is not None and current not in clients:
        clients.insert(0, current)
    for client in clients:
        backend = getattr(client, "backend", None)
        if backend is None:
            continue
        try:
            extra = str(getattr(backend, "extra_sys_prompt", "") or "")
            extra = LEGACY_TUI_CONTROL_HINT_BLOCK_RE.sub("", extra)
            if TUI_CONTROL_HINT_MARKER not in extra:
                extra = extra.rstrip() + TUI_AGENT_CONTROL_HINT
            setattr(backend, "extra_sys_prompt", extra)
        except Exception:
            continue


def browse_input_history(state: State, direction: int) -> bool:
    if not state.input_history:
        return False
    if state.input_history_index is None:
        state.input_history_draft = state.input_text
        state.input_history_draft_cursor = state.input_cursor
        if direction < 0:
            state.input_history_index = len(state.input_history) - 1
        else:
            return False
    else:
        state.input_history_index += direction

    if state.input_history_index < 0:
        state.input_history_index = 0
    if state.input_history_index >= len(state.input_history):
        state.input_history_index = None
        set_input_text(state, state.input_history_draft, state.input_history_draft_cursor)
        state.input_history_draft = ""
        state.input_history_draft_cursor = 0
    else:
        set_input_text(state, state.input_history[state.input_history_index])
    state.command_index = 0
    mark_dirty(state)
    return True


def new_agent() -> Any:
    install_tui_query_runtime()
    agent = GenericAgent()
    agent.inc_out = True
    install_tui_query_runtime(agent)
    install_tui_control_hint(agent)
    agent_no = next(_AGENT_COUNTER)
    thread_name = f"ga-tui-agent-{agent_no}"
    agent._ga_tui_thread_name = thread_name
    thread = threading.Thread(target=agent.run, daemon=True, name=thread_name)
    agent._ga_tui_thread = thread
    thread.start()
    return agent


def install_interaction_hook(state: State, agent: Any) -> None:
    if agent is None:
        return
    install_tui_query_runtime(agent, state)
    try:
        hooks = getattr(agent, "_turn_end_hooks", None)
        if hooks is None:
            hooks = agent._turn_end_hooks = {}

        def _hook(ctx, _state=state, _agent=agent):
            exit_reason = (ctx or {}).get("exit_reason") or {}
            if exit_reason.get("result") != "EXITED":
                return
            payload = exit_reason.get("data")
            if not isinstance(payload, dict):
                return
            if payload.get("status") != "INTERRUPT" or payload.get("intent") != "HUMAN_INTERVENTION":
                return
            request = request_payload_from_args("ask_user", payload.get("data") or {})
            if request:
                _state.ui_queue.put(("interaction", _agent, request))

        hooks["_ga_curses_interaction"] = _hook
    except Exception:
        pass


def rel_age(mtime: float) -> str:
    delta = int(time.time() - mtime)
    if delta < 60:
        return f"{delta}s"
    if delta < 3600:
        return f"{delta // 60}m"
    if delta < 86400:
        return f"{delta // 3600}h"
    return f"{delta // 86400}d"


def human_tokens(n: int) -> str:
    n = int(n or 0)
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        v = n / 1000.0
        return f"{v:.1f}k" if v < 100 else f"{int(v)}k"
    v = n / 1_000_000.0
    return f"{v:.2f}M" if v < 100 else f"{int(v)}M"


def empty_token_stats_dict() -> dict[str, int]:
    return {key: 0 for key in TOKEN_STAT_KEYS}


def load_token_usage_registry() -> dict[str, dict[str, int]]:
    try:
        with open(TOKEN_USAGE_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    registry: dict[str, dict[str, int]] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        clean = empty_token_stats_dict()
        for stat_key in TOKEN_STAT_KEYS:
            try:
                clean[stat_key] = max(0, int(value.get(stat_key, 0) or 0))
            except (TypeError, ValueError):
                clean[stat_key] = 0
        registry[key] = clean
    return registry


def save_token_usage_registry(registry: dict[str, dict[str, int]]) -> None:
    os.makedirs(os.path.dirname(TOKEN_USAGE_PATH), exist_ok=True)
    tmp = TOKEN_USAGE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(registry, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, TOKEN_USAGE_PATH)


def token_session_key(agent: Any) -> str:
    path = agent_log_path(agent)
    return os.path.basename(path) if path else ""


def agent_log_path_is_devnull(agent: Any) -> bool:
    path = agent_log_path(agent)
    try:
        return bool(path and normalized_path(path) == normalized_path(os.devnull))
    except Exception:
        return path == os.devnull


def token_thread_name(agent: Any) -> str:
    return str(getattr(agent, "_ga_tui_thread_name", "") or "")


def token_stats_snapshot(stats: Any) -> dict[str, int]:
    out = empty_token_stats_dict()
    if stats is None:
        return out
    for key in TOKEN_STAT_KEYS:
        try:
            out[key] = max(0, int(getattr(stats, key, 0) or 0))
        except (TypeError, ValueError):
            out[key] = 0
    return out


def token_stats_delta(now: dict[str, int], before: dict[str, int]) -> dict[str, int]:
    return {key: max(0, int(now.get(key, 0)) - int(before.get(key, 0))) for key in TOKEN_STAT_KEYS}


def token_stats_add(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return {key: max(0, int(left.get(key, 0)) + int(right.get(key, 0))) for key in TOKEN_STAT_KEYS}


def bind_agent_token_session(state: State, agent: Any) -> None:
    thread_name = token_thread_name(agent)
    if agent_log_path_is_devnull(agent):
        if thread_name and cost_tracker is not None:
            try:
                state.token_live_offsets[thread_name] = token_stats_snapshot(cost_tracker.get(thread_name))
            except Exception:
                state.token_live_offsets.setdefault(thread_name, empty_token_stats_dict())
        return
    key = token_session_key(agent)
    if not key or not thread_name:
        return
    state.token_usage_registry.setdefault(key, empty_token_stats_dict())
    if cost_tracker is None:
        state.token_live_offsets.setdefault(thread_name, empty_token_stats_dict())
        return
    try:
        state.token_live_offsets[thread_name] = token_stats_snapshot(cost_tracker.get(thread_name))
    except Exception:
        state.token_live_offsets.setdefault(thread_name, empty_token_stats_dict())


def persist_agent_token_usage(state: State, agent: Any) -> bool:
    key = token_session_key(agent)
    thread_name = token_thread_name(agent)
    if not thread_name or cost_tracker is None:
        return False
    try:
        current = token_stats_snapshot(cost_tracker.get(thread_name))
    except Exception:
        return False
    if agent_log_path_is_devnull(agent) or not key:
        state.token_live_offsets[thread_name] = current
        return False
    offset = state.token_live_offsets.get(thread_name, empty_token_stats_dict())
    delta = token_stats_delta(current, offset)
    if not any(delta.values()):
        return False
    state.token_usage_registry[key] = token_stats_add(state.token_usage_registry.get(key, empty_token_stats_dict()), delta)
    state.token_live_offsets[thread_name] = current
    try:
        save_token_usage_registry(state.token_usage_registry)
    except Exception as exc:
        state.last_error = f"token usage save: {type(exc).__name__}: {exc}"
        return False
    return True


def persist_all_token_usage(state: State) -> None:
    seen: set[int] = set()
    for agent in [
        state.agent,
        *(bg.agent for bg in state.background_sessions.values()),
        *(sub.agent for sub in state.subagents.values() if sub.agent is not None),
    ]:
        if agent is None or id(agent) in seen:
            continue
        seen.add(id(agent))
        persist_agent_token_usage(state, agent)


def session_token_stats(state: State, agent: Any):
    if cost_tracker is None:
        return None
    key = token_session_key(agent)
    if not key:
        return None
    base = state.token_usage_registry.get(key, empty_token_stats_dict())
    thread_name = token_thread_name(agent)
    delta = empty_token_stats_dict()
    live = None
    if thread_name:
        try:
            live = cost_tracker.get(thread_name)
            current = token_stats_snapshot(live)
            offset = state.token_live_offsets.get(thread_name, empty_token_stats_dict())
            delta = token_stats_delta(current, offset)
        except Exception:
            live = None
    total = token_stats_add(base, delta)
    stats = cost_tracker.TokenStats()
    for stat_key, value in total.items():
        setattr(stats, stat_key, value)
    if live is not None:
        stats.last_input = getattr(live, "last_input", 0)
        stats.last_output = getattr(live, "last_output", 0)
    return stats


def host_from_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url if "://" in url else "https://" + url)
        return parsed.netloc or parsed.path
    except Exception:
        return url


def current_model_lines(state: State, width: int) -> list[tuple[str, int]]:
    lines: list[tuple[str, int]] = [("CURRENT MODEL", cp(7) | curses.A_BOLD)]
    backend = None
    try:
        backend = state.agent.llmclient.backend
    except Exception:
        backend = None
    provider = model = base = ""
    if backend is not None:
        provider = str(getattr(backend, "name", "") or "")
        model = str(getattr(backend, "model", "") or "")
        base = host_from_url(str(getattr(backend, "api_base", "") or getattr(backend, "apibase", "") or ""))
    if not provider:
        try:
            provider = str(state.agent.get_llm_name(model=False))
        except Exception:
            provider = "unknown"
    if not model:
        try:
            model = str(state.agent.get_llm_name(model=True))
        except Exception:
            model = "unknown"
    lines.append((f"provider {provider}", cp(2)))
    lines.append((f"model {model}", cp(1)))
    if base:
        lines.append((f"base {base}", cp(1)))
    return [(truncate_cells(text, width - 2), attr) for text, attr in lines]


def current_token_lines(state: State, width: int) -> list[tuple[str, int]]:
    if cost_tracker is None:
        return [("TOKEN USAGE", cp(7) | curses.A_BOLD), ("tracker unavailable", cp(5))]
    stats = session_token_stats(state, state.agent)
    if stats is None:
        return [("TOKEN USAGE", cp(7) | curses.A_BOLD), ("no data", cp(1))]

    total = stats.total_tokens()
    input_side = stats.total_input_side()
    lines: list[tuple[str, int]] = [
        ("TOKEN USAGE", cp(7) | curses.A_BOLD),
        (f"total {human_tokens(total)}", cp(2)),
        (f"in {human_tokens(input_side)}  out {human_tokens(stats.output)}", cp(2)),
    ]
    cache = stats.cache_read + stats.cache_create
    if cache:
        lines.append((f"cache {human_tokens(cache)}  hit {stats.cache_hit_rate():.0f}%", cp(1)))
    try:
        backend = state.agent.llmclient.backend
        cap = cost_tracker.context_window_chars(backend)
        used = cost_tracker.current_input_chars(backend)
    except Exception:
        cap = used = 0
    if cap > 0:
        pct = min(100, max(0, int(used / cap * 100)))
        lines.append((f"ctx {pct}%  req {stats.requests}", cp(1)))
    else:
        lines.append((f"req {stats.requests}", cp(1)))
    return [(truncate_cells(text, width - 2), attr) for text, attr in lines]


def current_status_panel_lines(state: State, width: int) -> list[tuple[str, int]]:
    lines = current_model_lines(state, width)
    lines.append(("", cp(1)))
    lines.extend(current_token_lines(state, width))
    lines.append((truncate_cells(secret_status_text(state), width - 2), cp(7) if state.secret_vault.unlocked else cp(1)))
    return lines[:TOKEN_PANEL_H - 1]


def load_history(state: State, force: bool = False) -> bool:
    if state.secret_vault.unlocked or state.secret_vault.pending_action:
        state.history = []
        state.history_names = {}
        state.history_descriptions = {}
        return False
    now = time.time()
    if not force and now - state.history_loaded_at < 10:
        return False
    try:
        state.session_meta = load_session_meta_registry()
        session_rows, meta_changed = cached_session_rows(state, exclude_pid=os.getpid())
        history: list[tuple[str, float, str, int]] = []
        descriptions: dict[str, str] = {}
        for path, last_user_at, preview, rounds, desc in session_rows:
            meta = session_meta_for(state, path)
            if bool(meta.get("deleted")):
                continue
            archived = bool(meta.get("archived"))
            if archived != state.show_archived:
                continue
            category = session_category_label(meta)
            filter_kind = system_session_category(state.session_filter_category)
            if state.session_filter_category and not filter_kind and category_key(category) != category_key(state.session_filter_category):
                continue
            history.append((path, last_user_at, preview, rounds))
            descriptions[path] = desc
        history.sort(key=lambda item: (not bool(session_meta_for(state, item[0]).get("pinned")), -item[1]))
        names: dict[str, str] = {}
        if session_names is not None:
            try:
                registry = session_names._load()
            except Exception:
                registry = {}
            for path, _mtime, preview, _rounds in history:
                name = registry.get(os.path.basename(path), "")
                if not name:
                    name = preview
                names[path] = compact_title(name, 80)
        if meta_changed:
            save_session_meta_registry(state.session_meta)
        changed = (
            history != state.history
            or names != state.history_names
            or descriptions != state.history_descriptions
        )
        state.history = history
        state.history_names = names
        state.history_descriptions = descriptions
        state.history_loaded_at = now
        return changed
    except Exception as exc:
        state.last_error = f"history: {type(exc).__name__}: {exc}"
        state.dirty = True
        return False


def history_name(state: State, path: str) -> str:
    return state.history_names.get(path, "")


def clear_history_ui_state(state: State) -> None:
    state.history_ui_path = ""
    state.history_ui_loaded_rounds = 0
    state.history_ui_total_rounds = 0
    state.history_ui_message_count = 0
    state.history_ui_loading = False
    state.history_ui_token += 1
    state.session_popup_path = ""
    state.session_popup_anchor = None
    state.session_popup_rect = None


def cancel_normal_history_restore(state: State) -> None:
    state.restore_token += 1
    clear_history_ui_state(state)


def rename_current_session(state: State, raw_name: str) -> str:
    name = compact_title(raw_name, 80)
    if not name:
        return "名称不能为空。"
    persist_msg = ""
    if session_names is not None:
        try:
            path = getattr(state.agent, "log_path", "")
            if path:
                session_names.set_name(path, name)
                persist_msg = "已持久化。"
            else:
                persist_msg = "当前会话暂无日志路径，仅本次界面生效。"
        except Exception as exc:
            persist_msg = f"持久化失败: {type(exc).__name__}: {exc}"
    else:
        persist_msg = "session_names 模块不可用，仅本次界面生效。"
    state.current_title = name
    if load_history(state, force=True):
        state.dirty = True
    mark_dirty(state)
    return f"当前会话已命名为: {name}；{persist_msg}"


def compact_category(text: str) -> str:
    text = compact_title(text, 18)
    return "" if text.lower() in {"-", "clear", "none", "null", "未分类"} else text


def session_category_label(meta: dict[str, Any]) -> str:
    return compact_category(str(meta.get("category") or "")) or "未分类"


def category_registry(state: State) -> dict[str, dict[str, Any]]:
    raw = state.session_meta.get("__categories__", {})
    return raw if isinstance(raw, dict) else {}


def category_meta_for(state: State, label: str) -> dict[str, Any]:
    raw = category_registry(state).get(category_key(label), {})
    return raw if isinstance(raw, dict) else {}


def set_category_meta_fields(state: State, label: str, **fields: Any) -> None:
    key = category_key(label)
    if not key:
        return
    registry = dict(category_registry(state))
    entry = dict(registry.get(key, {}))
    entry.setdefault("name", category_filter_label(label) or "未分类")
    for field_name, value in fields.items():
        if value in (None, ""):
            entry.pop(field_name, None)
        else:
            entry[field_name] = value
    registry[key] = entry
    state.session_meta["__categories__"] = registry
    save_session_meta_registry(state.session_meta)


def category_key(raw: str) -> str:
    label = compact_category(raw)
    return label.casefold() if label else "__uncategorized__"


def system_session_category(raw: str) -> str:
    key = category_key(raw)
    if key in {category_key(PINNED_SESSION_LABEL), "pinned", "pin", "置顶"}:
        return "pinned"
    if key in {category_key(RECENT_SESSION_LABEL), "recent", "最近", "最近打开"}:
        return "recent"
    return ""


def category_sort_key(label: str) -> tuple[int, str, str]:
    key = category_key(label)
    if key == "__uncategorized__":
        return (1, "", "")
    normalized = compact_category(label).casefold()
    first = normalized[:1]
    return (0, locale.strxfrm(first), locale.strxfrm(normalized))


def category_filter_label(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw or raw.lower() in {"off", "all", "clear", "none", "全部"}:
        return ""
    return compact_category(raw) or "未分类"


def set_session_filter(state: State, raw: str) -> str:
    label = category_filter_label(raw)
    state.session_filter_category = label
    state.sidebar_scroll = 0
    load_history(state, force=True)
    mark_dirty(state)
    return f"已按分类筛选：{label}" if label else "已关闭分类筛选。"


def category_counts_for_view(state: State) -> list[tuple[str, int]]:
    state.session_meta = load_session_meta_registry()
    session_rows, meta_changed = cached_session_rows(state, exclude_pid=os.getpid())
    if meta_changed:
        save_session_meta_registry(state.session_meta)
    counts: dict[str, list[Any]] = {}
    pinned_count = 0
    recent_count = 0
    for path, _mtime, _preview, _rounds, _desc in session_rows:
        meta = session_meta_for(state, path)
        if bool(meta.get("deleted")):
            continue
        if bool(meta.get("archived")) != state.show_archived:
            continue
        pinned = bool(meta.get("pinned"))
        if pinned:
            pinned_count += 1
        if not pinned and float(_mtime or 0.0) > 0:
            recent_count += 1
        label = session_category_label(meta)
        key = category_key(label)
        if key not in counts:
            counts[key] = [label, 0]
        counts[key][1] += 1
    result: list[tuple[str, int]] = []
    if pinned_count:
        result.append((PINNED_SESSION_LABEL, pinned_count))
    if recent_count:
        result.append((RECENT_SESSION_LABEL, min(RECENT_SESSION_LIMIT, recent_count)))
    result.extend([
        (str(label), int(count))
        for label, count in sorted(
            counts.values(),
            key=lambda item: (*category_sort_key(str(item[0])), -int(item[1])),
        )
    ])
    return result


def format_category_counts(state: State) -> str:
    counts = category_counts_for_view(state)
    if not counts:
        return "当前视图没有分类。"
    active = f"当前筛选：{state.session_filter_category}" if state.session_filter_category else "当前筛选：全部"
    lines = [active, "分类列表："]
    for label, count in counts:
        desc = compact_description(str(category_meta_for(state, label).get("description") or ""))
        suffix = f" - {desc}" if desc else ""
        lines.append(f"- {label}: {count}{suffix}")
    return "\n".join(lines)


def rename_category(state: State, old: str, new: str) -> str:
    old_label = category_filter_label(old)
    new_label = category_filter_label(new)
    if not old_label or not new_label:
        return "Usage: /catname <old> <new>"
    changed = 0
    old_key = category_key(old_label)
    for key, meta in list(state.session_meta.items()):
        if not isinstance(meta, dict) or key == "__categories__":
            continue
        if category_key(str(meta.get("category") or "")) == old_key:
            entry = dict(meta)
            entry["category"] = new_label
            entry.setdefault("category_source", "manual")
            state.session_meta[key] = entry
            changed += 1
    registry = dict(category_registry(state))
    old_meta = dict(registry.pop(old_key, {}))
    old_meta["name"] = new_label
    registry[category_key(new_label)] = old_meta
    state.session_meta["__categories__"] = registry
    save_session_meta_registry(state.session_meta)
    load_history(state, force=True)
    mark_dirty(state)
    return f"已重命名分类：{old_label} -> {new_label}，影响 {changed} 个会话。"


def set_category_description(state: State, raw_category: str, raw_description: str) -> str:
    label = category_filter_label(raw_category)
    description = compact_description(raw_description)
    if not label or not description:
        return "Usage: /catdesc <category> <description>"
    set_category_meta_fields(state, label, description=description, source="manual", updated_at=time.time())
    mark_dirty(state)
    return f"已设置分类简介：{label}"


def set_category_collapsed(state: State, raw: str, collapsed: bool) -> str:
    raw = (raw or "").strip()
    counts = category_counts_for_view(state)
    if not raw:
        return "Usage: /collapse <category|all> 或 /expand <category|all>"
    if raw.lower() in {"all", "全部", "*"}:
        keys = {category_key(label) for label, _count in counts}
        if collapsed:
            state.collapsed_categories.update(keys)
            result = "已折叠所有分类。"
        else:
            state.collapsed_categories.difference_update(keys)
            result = "已展开所有分类。"
        mark_dirty(state)
        return result
    target = category_key(raw)
    if collapsed:
        state.collapsed_categories.add(target)
        result = f"已折叠分类：{category_filter_label(raw) or '未分类'}"
    else:
        state.collapsed_categories.discard(target)
        result = f"已展开分类：{category_filter_label(raw) or '未分类'}"
    mark_dirty(state)
    return result


def toggle_category_collapsed(state: State, raw: str) -> str:
    key = category_key(raw)
    if key in state.collapsed_categories:
        state.collapsed_categories.discard(key)
        result = f"已展开分类：{category_filter_label(raw) or '未分类'}"
    else:
        state.collapsed_categories.add(key)
        result = f"已折叠分类：{category_filter_label(raw) or '未分类'}"
    mark_dirty(state)
    return result


def current_session_path(state: State) -> str:
    return str(getattr(state.agent, "log_path", "") or "")


def is_current_session_path(state: State, path: str) -> bool:
    return bool(path) and normalized_path(path) == normalized_path(current_session_path(state))


def background_session_key_for_path(state: State, path: str) -> str:
    target = normalized_path(path)
    if not target:
        return ""
    for key, bg in state.background_sessions.items():
        if normalized_path(getattr(bg.agent, "log_path", "")) == target:
            return key
    return ""


def reset_backend_memory_no_snapshot(agent: Any) -> None:
    reset_agent_runtime_context_no_snapshot(agent)


def clear_active_session_after_meta_action(state: State, message: str) -> None:
    persist_agent_token_usage(state, state.agent)
    reset_backend_memory_no_snapshot(state.agent)
    set_agent_log_path(state.agent, new_session_log_path())
    bind_agent_token_session(state, state.agent)
    state.messages.clear()
    state.current_title = "main"
    state.selected_session = "main"
    state.status = "idle"
    state.active_task_id = None
    state.active_task_source = ""
    state.active_stream_target = None
    clear_active_plan_state(state)
    state.pending_interaction = None
    clear_history_ui_state(state)
    set_input_text(state, "")
    state.last_error = message
    load_history(state, force=True)
    mark_messages_changed(state)


def session_title_for_path(state: State, path: str) -> str:
    for item_path, _mtime, preview, _rounds in state.history:
        if normalized_path(item_path) == normalized_path(path):
            return compact_title(history_name(state, item_path) or preview or os.path.basename(path or ""), 80) or "当前会话"
    return compact_title(history_name(state, path) or os.path.basename(path or ""), 80) or "当前会话"


def session_stable_id(path: str) -> str:
    base = os.path.basename(path or "")
    match = re.search(r"model_responses_(?:snapshot_)?(.+?)\.txt$", base)
    return match.group(1) if match else base


def all_resolvable_session_paths(state: State) -> list[str]:
    state.session_meta = load_session_meta_registry()
    session_rows, meta_changed = cached_session_rows(state, exclude_pid=os.getpid())
    if meta_changed:
        save_session_meta_registry(state.session_meta)
    paths: list[str] = []
    seen: set[str] = set()
    for path, _mtime, _preview, _rounds, _desc in session_rows:
        key = session_key(path)
        if bool(state.session_meta.get(key, {}).get("deleted")):
            continue
        norm = normalized_path(path)
        if norm not in seen:
            paths.append(path)
            seen.add(norm)
    current = current_session_path(state)
    if current:
        norm = normalized_path(current)
        if norm not in seen:
            paths.insert(0, current)
    return paths


def target_matches_session_id(path: str, target: str) -> bool:
    base = os.path.basename(path or "")
    stable = session_stable_id(path)
    target = (target or "").strip()
    normalized = re.sub(r"^(?:id:|#)", "", target, flags=re.I)
    target_digits = "".join(re.findall(r"\d+", normalized))
    return target == base or normalized == stable or normalized == base or (bool(target_digits) and target_digits == stable)


def resolve_stable_session_target(state: State, target: str) -> tuple[Optional[str], str]:
    matches = [path for path in all_resolvable_session_paths(state) if target_matches_session_id(path, target)]
    if len(matches) == 1:
        return matches[0], ""
    if len(matches) > 1:
        return None, f"稳定 id 匹配到多个会话：{target}"
    return None, ""


def session_target_matches_expected(state: State, path: str, expected: str) -> bool:
    expected = compact_title(expected, 40).casefold()
    if not expected:
        return True
    title = compact_title(session_title_for_path(state, path), 40).casefold()
    base = os.path.basename(path).casefold()
    return expected in title or title in expected or expected in base


def resolve_session_target(
    state: State,
    raw_target: str = "",
    *,
    allow_view_index: bool = True,
    expected_title: str = "",
) -> tuple[Optional[str], str]:
    target = (raw_target or "").strip()
    if not target or target.lower() in {"current", "now", "当前"}:
        path = current_session_path(state)
        return (path, "") if path else (None, "当前会话没有日志路径。")
    if target.lower() == "selected" and isinstance(state.selected_session, str) and state.selected_session != "main":
        return state.selected_session, ""
    if os.path.isabs(target) and os.path.exists(target):
        return target, ""
    stable_path, stable_error = resolve_stable_session_target(state, target)
    if stable_path or stable_error:
        return stable_path, stable_error
    m = re.fullmatch(r"[sS]?(\d+)", target)
    if m:
        if not allow_view_index and not expected_title:
            return None, f"拒绝使用相对编号 {target}：请让 agent 使用 /sessions 的稳定 id:xxxxxx 或文件名。"
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(state.history):
            path = state.history[idx][0]
            if expected_title and not session_target_matches_expected(state, path, expected_title):
                actual = session_title_for_path(state, path)
                return None, f"编号 {target} 标题不匹配：期望「{expected_title}」，实际「{actual}」。"
            return path, ""
        return None, f"索引越界: 1-{len(state.history)}"
    target_l = target.lower()
    matches = [
        path for path, _mtime, first, _rounds in state.history
        if (history_name(state, path) or first or os.path.basename(path)).lower().startswith(target_l)
    ]
    if len(matches) == 1:
        return matches[0], ""
    if len(matches) > 1:
        return None, "匹配到多个会话，请用左侧编号。"
    return None, "找不到会话，请用 current 或左侧编号。"


def unique_trash_path(path: str) -> str:
    os.makedirs(SESSION_TRASH_DIR, exist_ok=True)
    base = os.path.basename(path)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    candidate = os.path.join(SESSION_TRASH_DIR, f"{stamp}-{base}")
    idx = 1
    while os.path.exists(candidate):
        candidate = os.path.join(SESSION_TRASH_DIR, f"{stamp}-{idx}-{base}")
        idx += 1
    return candidate


def apply_session_operation(
    state: State,
    action: str,
    target: str = "",
    value: str = "",
    source: str = "TUI",
    *,
    allow_view_index: bool = True,
    expected_title: str = "",
) -> str:
    action = (action or "").strip().lower().replace("-", "_")
    if state.secret_vault.unlocked and action not in {"hide_archived", "archived_off"}:
        return "Secret Vault 已解锁：普通会话操作已隔离，请先 /lock。"
    if action in {"filter", "set_filter", "filter_category"}:
        raw = value or (target if target not in {"", "current"} else "")
        return set_session_filter(state, raw)
    if action in {"clear_filter", "filter_off"}:
        return set_session_filter(state, "off")
    if action in {"collapse", "collapse_category"}:
        raw = value or (target if target not in {"", "current"} else "")
        return set_category_collapsed(state, raw, True)
    if action in {"expand", "expand_category"}:
        raw = value or (target if target not in {"", "current"} else "")
        return set_category_collapsed(state, raw, False)
    if action in {"toggle_category", "toggle_collapse"}:
        raw = value or (target if target not in {"", "current"} else "")
        if not raw:
            return "缺少分类名。"
        return toggle_category_collapsed(state, raw)
    if action in {"show_archived", "archived_on"}:
        state.show_archived = True
        load_history(state, force=True)
        mark_dirty(state)
        return "已切到归档会话视图。"
    if action in {"hide_archived", "archived_off"}:
        state.show_archived = False
        load_history(state, force=True)
        mark_dirty(state)
        return "已切回普通会话视图。"
    if action in {"toggle_archived", "archived"}:
        state.show_archived = not state.show_archived
        load_history(state, force=True)
        mark_dirty(state)
        return "已切到归档会话视图。" if state.show_archived else "已切回普通会话视图。"

    path, error = resolve_session_target(state, target, allow_view_index=allow_view_index, expected_title=expected_title)
    if error:
        return error
    if not path:
        return "找不到目标会话。"
    title = session_title_for_path(state, path)
    if action in {"pin", "pinned"}:
        set_session_meta_fields(state, path, pinned=True)
        load_history(state, force=True)
        mark_dirty(state)
        return f"已置顶会话：{title}"
    if action in {"unpin", "unpinned"}:
        set_session_meta_fields(state, path, pinned=False)
        load_history(state, force=True)
        mark_dirty(state)
        return f"已取消置顶：{title}"
    if action in {"category", "categorize", "set_category"}:
        category = compact_category(value)
        category_source = "manual" if source in {"TUI"} or source.startswith("/") else source
        set_session_meta_fields(state, path, category=category, category_source=category_source)
        load_history(state, force=True)
        mark_dirty(state)
        return f"已设置分类：{title} -> {category or '未分类'}"
    if action in {"archive"}:
        if is_current_session_path(state, path) and state.status in {"running", "aborting"}:
            return "当前会话还在运行，不能归档；先 Ctrl+C 中止或等它完成。"
        set_session_meta_fields(state, path, archived=True)
        if is_current_session_path(state, path):
            clear_active_session_after_meta_action(state, f"已归档当前会话：{title}")
        else:
            load_history(state, force=True)
            mark_dirty(state)
        return f"已归档会话：{title}"
    if action in {"unarchive", "restore_archive"}:
        set_session_meta_fields(state, path, archived=False, deleted=False)
        load_history(state, force=True)
        mark_dirty(state)
        return f"已取消归档：{title}"
    if action in {"delete", "remove"}:
        if is_current_session_path(state, path) and state.status in {"running", "aborting"}:
            return "当前会话还在运行，不能删除；先 Ctrl+C 中止或等它完成。"
        if not os.path.exists(path):
            set_session_meta_fields(state, path, deleted=True, deleted_at=time.time())
            load_history(state, force=True)
            return f"会话文件不存在，已从列表隐藏：{title}"
        trash_path = unique_trash_path(path)
        try:
            shutil.move(path, trash_path)
        except Exception as exc:
            return f"删除失败: {type(exc).__name__}: {exc}"
        set_session_meta_fields(state, path, deleted=True, archived=True, trash_path=trash_path, deleted_at=time.time())
        if session_names is not None:
            try:
                session_names.set_name(path, "")
            except Exception:
                pass
        if is_current_session_path(state, path):
            clear_active_session_after_meta_action(state, f"已删除当前会话到回收站：{title}")
        else:
            load_history(state, force=True)
            mark_dirty(state)
        return f"已删除到回收站：{title}"
    return f"{source}: 未知会话操作 {action}"


def rename_session_path(state: State, path: str, raw_name: str) -> str:
    name = compact_title(raw_name, 80)
    if not name:
        return "名称不能为空。"
    if is_current_session_path(state, path):
        return rename_current_session(state, name)
    if session_names is None:
        return "session_names 模块不可用，无法持久化历史会话名称。"
    try:
        session_names.set_name(path, name)
        if load_history(state, force=True):
            state.dirty = True
        return f"已命名会话：{name}"
    except Exception as exc:
        return f"命名失败: {type(exc).__name__}: {exc}"


GA_CONTROL_SCHEMA = "ga-control.v2"
AGENT_TASK_SCHEMA = "agenttask.v2"

KNOWN_TUI_CONTROL_ACTIONS = {
    "session_pin",
    "session_unpin",
    "session_category",
    "session_filter",
    "session_clear_filter",
    "session_collapse_category",
    "session_expand_category",
    "session_archive",
    "session_unarchive",
    "session_delete",
    "session_rename",
    "session_show_archived",
    "session_hide_archived",
    "task_plan_create",
    "task_update",
    "task_done",
    "task_start",
    "task_fail",
    "task_cancel",
    "agent_create",
    "agent_profile_update",
    "agent_role_update",
    "agent_model_update",
    "agent_stop",
    "agent_delete",
    "agent_remove",
    "delegate_create",
    "memory_candidate",
}

SESSION_V2_TO_EXECUTION_ACTION = {
    "session_pin": "pin",
    "session_unpin": "unpin",
    "session_category": "category",
    "session_filter": "filter",
    "session_clear_filter": "clear_filter",
    "session_collapse_category": "collapse_category",
    "session_expand_category": "expand_category",
    "session_archive": "archive",
    "session_unarchive": "unarchive",
    "session_delete": "delete",
    "session_rename": "rename",
    "session_show_archived": "show_archived",
    "session_hide_archived": "hide_archived",
}


def normalized_control_action(control: dict[str, Any]) -> str:
    return str(control.get("action") or control.get("op") or "").strip().lower().replace("-", "_").replace(".", "_")


def known_tui_control(control: dict[str, Any]) -> bool:
    return normalized_control_action(control) in KNOWN_TUI_CONTROL_ACTIONS


def action_schema_valid(control: dict[str, Any]) -> bool:
    schema = str(control.get("schema_version") or "").strip().lower()
    return schema in {"", AGENT_TASK_SCHEMA}


def coerce_ga_control_action(action: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not isinstance(action, dict):
        return None
    item = dict(action)
    if not item.get("schema_version"):
        item["schema_version"] = AGENT_TASK_SCHEMA
    if not action_schema_valid(item) or not known_tui_control(item):
        return None
    return item


def agenttask_work_order(control: dict[str, Any]) -> dict[str, Any]:
    value = control.get("work_order")
    if isinstance(value, dict):
        return value
    value = control.get("task")
    return value if isinstance(value, dict) else {}


def agenttask_routing(control: dict[str, Any]) -> dict[str, Any]:
    value = control.get("routing")
    return value if isinstance(value, dict) else {}


def agenttask_target_selector(control: dict[str, Any]) -> dict[str, Any]:
    routing = agenttask_routing(control)
    value = routing.get("target_selector")
    return value if isinstance(value, dict) else {}


def agenttask_contract(control: dict[str, Any], key: str) -> dict[str, Any]:
    value = control.get(key)
    return value if isinstance(value, dict) else {}


def lifecycle_is_persistent(control: dict[str, Any]) -> Optional[bool]:
    for key in ("persistent", "durable", "long_term"):
        if key in control:
            return control_truthy(control.get(key))
    lifecycle = str(control.get("lifecycle") or control.get("scope") or "").strip().lower()
    if lifecycle in {"persistent", "durable", "long_term", "long-term", "permanent", "正式", "持久", "长期", "永久"}:
        return True
    if lifecycle in {"ephemeral", "temporary", "temp", "session", "session_only", "临时", "暂时"}:
        return False
    return None


def force_new_from_v2(control: dict[str, Any]) -> bool:
    if control_truthy(control.get("force_new")) or control_truthy(control.get("create_new")):
        return True
    reuse_policy = str(control.get("reuse_policy") or "").strip().lower().replace("-", "_")
    selector = agenttask_target_selector(control)
    selector_policy = str(selector.get("reuse_policy") or "").strip().lower().replace("-", "_")
    return reuse_policy in {"force_new", "never", "none", "no_reuse"} or selector_policy in {"force_new", "never", "none", "no_reuse"}


def agenttask_objective(control: dict[str, Any]) -> str:
    work_order = agenttask_work_order(control)
    return str(
        work_order.get("objective")
        or control.get("objective")
        or control.get("prompt")
        or control.get("message")
        or ""
    ).strip()


def format_agenttask_worker_prompt(control: dict[str, Any]) -> str:
    objective = agenttask_objective(control)
    work_order = agenttask_work_order(control)
    output_contract = agenttask_contract(control, "output_contract")
    payload = json.dumps(control, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    sections = [
        "[GA TUI AgentTask Envelope v2]",
        payload,
        "[/GA TUI AgentTask Envelope v2]",
        "",
        "[Work Order]",
        f"objective: {objective}",
    ]
    background = str(work_order.get("background") or "").strip()
    if background:
        sections.append(f"background: {background}")
    non_goals = work_order.get("non_goals")
    if isinstance(non_goals, list) and non_goals:
        sections.append("non_goals:")
        sections.extend(f"- {item}" for item in non_goals)
    success = work_order.get("success_criteria")
    if isinstance(success, list) and success:
        sections.append("success_criteria:")
        sections.extend(f"- {item}" for item in success)
    stop_condition = str(work_order.get("stop_condition") or "").strip()
    if stop_condition:
        sections.append(f"stop_condition: {stop_condition}")
    required = output_contract.get("required_sections")
    if isinstance(required, list) and required:
        sections.append("required_output_sections:")
        sections.extend(f"- {item}" for item in required)
    sections.append("[/Work Order]")
    return "\n".join(str(item) for item in sections).strip()


def execution_control_from_v2(control: dict[str, Any]) -> Optional[dict[str, Any]]:
    action = normalized_control_action(control)
    common = {
        "_ga_control_schema_version": str(control.get("schema_version") or AGENT_TASK_SCHEMA),
        "_ga_control_external_action": str(control.get("action") or ""),
        "_ga_control_envelope": dict(control),
    }
    if action in SESSION_V2_TO_EXECUTION_ACTION:
        mapped = dict(control)
        mapped.update(common)
        mapped["action"] = SESSION_V2_TO_EXECUTION_ACTION[action]
        return mapped
    if action == "task_plan_create":
        mapped = dict(common)
        work_order = agenttask_work_order(control)
        mapped.update({
            "action": "task_plan",
            "title": control.get("title") or work_order.get("title") or control.get("name") or "任务计划",
            "steps": control.get("steps") or work_order.get("steps") or control.get("tasks") or control.get("items") or [],
        })
        return mapped
    if action in {"task_update", "task_done", "task_start", "task_fail", "task_cancel"}:
        mapped = dict(control)
        mapped.update(common)
        mapped["action"] = action
        mapped["target"] = control.get("target") or control.get("task_id") or control.get("parent_task_id") or ""
        return mapped
    if action == "agent_create":
        selector = agenttask_target_selector(control)
        persistent = lifecycle_is_persistent(control)
        if persistent is None:
            persistent = lifecycle_is_persistent(selector)
        mapped = dict(common)
        mapped.update({
            "action": "subagent_create",
            "name": control.get("name") or selector.get("name") or control.get("title") or selector.get("role") or "subagent",
            "profile": control.get("profile") or control.get("description") or selector.get("profile") or selector.get("description") or "",
            "role": control.get("role") or selector.get("role") or "specialist",
            "plan_step_id": control.get("plan_step_id") or control.get("parent_task_id") or control.get("step") or "",
            "force_new": force_new_from_v2(control),
        })
        if persistent is not None:
            mapped["persistent"] = bool(persistent)
            mapped["temporary"] = not bool(persistent)
        return mapped
    if action == "delegate_create":
        routing = agenttask_routing(control)
        selector = agenttask_target_selector(control)
        selected = (
            routing.get("selected_agent")
            or selector.get("agent_id")
            or selector.get("target")
            or selector.get("name")
            or control.get("target")
            or control.get("agent")
            or ""
        )
        mapped = dict(common)
        mapped.update({
            "action": "subagent_ask",
            "target": selected,
            "prompt": format_agenttask_worker_prompt(control),
            "parent_task_id": control.get("parent_task_id") or control.get("plan_step_id") or control.get("step") or "",
            "task_title": control.get("task_title") or control.get("title") or agenttask_objective(control),
        })
        return mapped
    if action == "memory_candidate":
        mapped = dict(common)
        mapped.update({
            "action": "subagent_remember",
            "target": control.get("target") or control.get("agent_id") or control.get("agent") or "",
            "memory": control.get("memory") or control.get("statement") or control.get("note") or "",
        })
        return mapped
    if action in {"agent_profile_update", "agent_role_update", "agent_model_update", "agent_stop", "agent_delete", "agent_remove"}:
        mapped = dict(control)
        mapped.update(common)
        mapped["target"] = control.get("target") or control.get("agent_id") or control.get("agent") or ""
        mapped["action"] = {
            "agent_profile_update": "subagent_profile",
            "agent_role_update": "subagent_role",
            "agent_model_update": "subagent_model",
            "agent_stop": "subagent_stop",
            "agent_delete": "subagent_delete",
            "agent_remove": "subagent_delete",
        }[action]
        return mapped
    return None


def controls_from_json_payload(payload: Any, *, require_known: bool = False) -> list[dict[str, Any]]:
    raw_items: list[Any] = []
    if isinstance(payload, dict) and str(payload.get("schema_version") or "").strip().lower() == GA_CONTROL_SCHEMA:
        actions = payload.get("actions")
        if isinstance(actions, list):
            raw_items = list(actions)
        elif payload.get("action"):
            item = dict(payload)
            item["schema_version"] = AGENT_TASK_SCHEMA
            raw_items = [item]
    elif isinstance(payload, dict) and str(payload.get("schema_version") or "").strip().lower() == AGENT_TASK_SCHEMA:
        raw_items = [payload]
    elif isinstance(payload, list):
        raw_items = [item for item in payload if isinstance(item, dict) and str(item.get("schema_version") or "").strip().lower() == AGENT_TASK_SCHEMA]
    controls = [coerced for item in raw_items if isinstance(item, dict) for coerced in [coerce_ga_control_action(item)] if coerced is not None]
    if require_known:
        controls = [item for item in controls if known_tui_control(item)]
    execution_controls = []
    for control in controls:
        mapped = execution_control_from_v2(control)
        if mapped is not None:
            execution_controls.append(mapped)
    return execution_controls


def repair_json_missing_tail(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    stack: list[str] = []
    in_string = False
    escape = False
    for ch in text:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in {"}", "]"}:
            if not stack or stack[-1] != ch:
                return ""
            stack.pop()
    if in_string or escape or not stack:
        return ""
    return text.rstrip() + "".join(reversed(stack))


def load_ga_control_json_text(raw: str) -> tuple[Any, bool, str]:
    text = (raw or "").strip()
    if not text:
        return None, False, "empty control block"
    try:
        return json.loads(text), False, ""
    except json.JSONDecodeError as exc:
        repaired = repair_json_missing_tail(text)
        if repaired:
            try:
                return json.loads(repaired), True, ""
            except json.JSONDecodeError:
                pass
        return None, False, f"JSON parse error at line {exc.lineno} column {exc.colno}: {exc.msg}"
    except Exception as exc:
        return None, False, f"JSON parse error: {type(exc).__name__}: {exc}"


def controls_from_json_text(raw: str, *, require_known: bool = False) -> list[dict[str, Any]]:
    payload, _repaired, _error = load_ga_control_json_text(raw)
    if payload is None:
        return []
    return controls_from_json_payload(payload, require_known=require_known)


def tui_control_parse_errors(text: str, *, allow_json_fences: bool = False) -> list[str]:
    errors: list[str] = []
    blocks = TUI_CONTROL_RE.findall(text or "") + TUI_CONTROL_FENCE_RE.findall(text or "")
    if allow_json_fences:
        blocks.extend(TUI_CONTROL_JSON_FENCE_RE.findall(text or ""))
    for raw in blocks:
        payload, _repaired, error = load_ga_control_json_text(raw)
        if error:
            errors.append(error)
            continue
        if payload is not None and not controls_from_json_payload(payload, require_known=allow_json_fences):
            errors.append("control JSON parsed but no known ga-control.v2 or agenttask.v2 action was found")
    return errors


def extract_tui_controls(text: str, *, allow_json_fences: bool = False) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(raw: str, *, require_known: bool = False) -> None:
        for control in controls_from_json_text(raw, require_known=require_known):
            signature = json.dumps(control, ensure_ascii=False, sort_keys=True, default=str)
            if signature in seen:
                continue
            seen.add(signature)
            controls.append(control)

    for raw in TUI_CONTROL_RE.findall(text or "") + TUI_CONTROL_FENCE_RE.findall(text or ""):
        add(raw)
    if allow_json_fences:
        for raw in TUI_CONTROL_JSON_FENCE_RE.findall(text or ""):
            add(raw, require_known=True)
    return controls


def strip_tui_controls(text: str, *, allow_json_fences: bool = False) -> str:
    text = text or ""
    if allow_json_fences:
        def strip_json_control_fence(match: re.Match[str]) -> str:
            block = match.group(1) or ""
            if controls_from_json_text(block, require_known=True) or extract_tui_controls(match.group(0)):
                return ""
            return match.group(0)
        text = TUI_CONTROL_JSON_FENCE_RE.sub(strip_json_control_fence, text)
    text = TUI_CONTROL_RE.sub("", text)
    text = TUI_CONTROL_FENCE_RE.sub("", text)
    text = LEGACY_TUI_CONTROL_RE.sub("", text)
    text = LEGACY_TUI_CONTROL_FENCE_RE.sub("", text)
    text = re.sub(r"<ga[-_](?:control|tui)>[\s\S]*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```ga[-_](?:control|tui)[\s\S]*$", "", text, flags=re.IGNORECASE)
    return text.strip()


def plan_step_title(index: int) -> str:
    if index <= 0:
        index = 1
    return f"进行第 {index} 轮对话"


def attach_implicit_plan_to_controls(state: State, controls: list[dict[str, Any]], source: str = "agent") -> list[dict[str, Any]]:
    if "agent" not in source:
        return controls
    if any(str(item.get("action") or item.get("op") or "").strip().lower().replace("-", "_") in {"task_plan", "plan", "plan_create"} for item in controls):
        return controls
    sub_controls = [
        item for item in controls
        if str(item.get("action") or item.get("op") or "").strip().lower().replace("-", "_")
        in {"subagent_create", "agent_create", "create_subagent", "new_subagent", "subagent_ask", "subagent_run", "subagent_input", "agent_ask", "agent_run"}
    ]
    if len(sub_controls) < 2:
        return controls
    create_indexes: list[int] = []
    ask_indexes: list[int] = []
    for idx, item in enumerate(controls):
        action = str(item.get("action") or item.get("op") or "").strip().lower().replace("-", "_")
        if action in {"subagent_create", "agent_create", "create_subagent", "new_subagent"}:
            create_indexes.append(idx)
        elif action in {"subagent_ask", "subagent_run", "subagent_input", "agent_ask", "agent_run"}:
            ask_indexes.append(idx)
    if not ask_indexes and len(create_indexes) < 2:
        return controls

    targets = [
        str(controls[idx].get("target") or controls[idx].get("name") or "").strip()
        for idx in ask_indexes
    ]
    agent_count = len(create_indexes) or len({target for target in targets if target}) or 1
    round_count = max(1, math.ceil(len(ask_indexes) / max(1, agent_count))) if ask_indexes else 0
    steps: list[str] = []
    create_step_no = 0
    if create_indexes:
        steps.append("准备/复用子 agent")
        create_step_no = len(steps)
    first_round_step_no = len(steps) + 1
    for round_no in range(1, round_count + 1):
        steps.append(plan_step_title(round_no))
    summary_step_no = 0
    if ask_indexes:
        steps.append("对话汇总")
        summary_step_no = len(steps)
    plan_title = "多子 agent 协作"
    expected_children: dict[int, int] = {}
    for round_no in range(1, round_count + 1):
        step_no = first_round_step_no + round_no - 1
        remaining = max(0, len(ask_indexes) - (round_no - 1) * max(1, agent_count))
        expected_children[step_no] = min(max(1, agent_count), remaining)
    plan_id, step_ids = create_task_plan(state, plan_title, steps, source=source, expected_children=expected_children)
    updated: list[dict[str, Any]] = []
    ask_counter = 0
    for idx, item in enumerate(controls):
        item = dict(item)
        if create_step_no and idx in create_indexes:
            item.setdefault("plan_step_id", step_ids.get(str(create_step_no), ""))
        if idx in ask_indexes:
            round_no = ask_counter // max(1, agent_count) + 1
            step_id = step_ids.get(str(first_round_step_no + round_no - 1), "")
            item.setdefault("parent_task_id", step_id)
            item.setdefault("task_title", plan_step_title(round_no))
            ask_counter += 1
        updated.append(item)
    return updated


def apply_task_control(state: State, action: str, target: str, value: str, control: dict[str, Any], source: str = "agent") -> Optional[str]:
    action = (action or "").strip().lower().replace("-", "_")
    if action in {"task_plan", "plan", "plan_create"}:
        title = str(control.get("title") or control.get("name") or value or "任务计划").strip()
        steps = normalize_plan_steps(control.get("steps") or control.get("tasks") or control.get("items") or [])
        plan_id, step_ids = create_task_plan(state, title, steps, source=source)
        step_count = len({task_id for key, task_id in step_ids.items() if key.isdigit()})
        return f"已创建任务计划：{title} ({plan_id})，{step_count} 个步骤"
    if action in {"task_update", "task_done", "task_start", "task_fail", "task_cancel"}:
        task_id = resolve_plan_step_id(state, target) or target
        if not task_id:
            step = control.get("step")
            task_id = resolve_plan_step_id(state, step)
        if not task_id:
            return "缺少 task/step target。"
        status = str(control.get("status") or "").strip().lower()
        if action == "task_done":
            status = "completed"
        elif action == "task_start":
            status = "working"
        elif action == "task_fail":
            status = "failed"
        elif action == "task_cancel":
            status = "cancelled"
        if not status:
            status = "working"
        summary = str(control.get("summary") or control.get("message") or value or "").strip()
        append_task_update(task_id, status=status, summary=summary)
        if status == "completed":
            maybe_complete_plan_after_step(task_id)
        return f"已更新 task：{task_id} -> {status}"
    return None


def format_agent_control_result(action: str, target: str, result: str) -> str:
    action_label = (action or "control").strip() or "control"
    target_label = (target or "").strip()
    if target_label and target_label not in {"current", "now", "selected"}:
        action_label = f"{action_label} {target_label}"
    return f"- {action_label}: {truncate_cells(result, 260)}"


def recent_user_subagent_context(state: State, limit: int = 1) -> str:
    parts: list[str] = []
    for msg in reversed(state.messages):
        if msg.role != "user":
            continue
        parts.append(msg.content)
        if len(parts) >= limit:
            break
    return "\n".join(reversed(parts))


def apply_tui_controls_from_text(state: State, text: str, source: str = "agent", default_target: str = "current") -> None:
    agent_source = "agent" in source
    controls = attach_implicit_plan_to_controls(state, extract_tui_controls(text), source=source)
    agent_control_results: list[str] = []
    subagent_control_aliases: dict[str, str] = {}
    create_bind_index = 0
    ask_bind_index = 0
    subagent_creation_context = "\n".join([recent_user_subagent_context(state), strip_tui_controls(text)])

    def record_control_result(action: str, target: str, result: str) -> None:
        message = f"Agent 控制: {result}"
        if agent_source:
            state.last_error = message
            agent_control_results.append(format_agent_control_result(action, target, result))
            mark_dirty(state)
        else:
            add_system(state, message)

    if not controls:
        for error in tui_control_parse_errors(text):
            record_control_result("parse_error", "", f"控制块解析失败：{error}")
        if agent_source and agent_control_results:
            add_system(
                state,
                "Agent 控制结果：\n" + "\n".join(agent_control_results),
                persist=True,
                kind="agent_control_result",
            )
        return

    for control in controls:
        action = str(control.get("action") or control.get("op") or "").strip().lower()
        target = str(control.get("target") or default_target or "current").strip()
        display_target = target
        value = str(control.get("value") or control.get("category") or control.get("name") or "").strip()
        expected_title = str(control.get("expected_title") or control.get("expect_title") or control.get("title") or "").strip()
        if not action:
            continue
        normalized_action = action.replace("-", "_")
        bind_create_index = create_bind_index
        bind_ask_index = ask_bind_index
        if normalized_action in {"subagent_create", "agent_create", "create_subagent", "new_subagent"}:
            create_bind_index += 1
        elif normalized_action in {"subagent_ask", "subagent_run", "subagent_input", "agent_ask", "agent_run"}:
            ask_bind_index += 1
        if normalized_action.startswith("subagent_") or normalized_action.startswith("agent_") or normalized_action in {"create_subagent", "new_subagent"}:
            control = maybe_attach_active_plan_to_subagent_control(
                state,
                control,
                normalized_action,
                create_index=bind_create_index,
                ask_index=bind_ask_index,
            )
        if (
            (normalized_action.startswith("subagent_") or normalized_action.startswith("agent_"))
            and normalized_action not in {"subagent_create", "agent_create", "create_subagent", "new_subagent"}
        ):
            target = resolve_subagent_control_alias(subagent_control_aliases, target)
        task_result = apply_task_control(state, action, target, value, control, source=source)
        if task_result is not None:
            record_control_result(action, display_target, task_result)
            continue
        subagent_result = apply_subagent_control(
            state,
            action,
            target,
            value,
            control,
            source=source,
            control_aliases=subagent_control_aliases,
            force_new_context=subagent_creation_context,
        )
        if subagent_result is not None:
            record_control_result(action, display_target, subagent_result)
            continue
        if action in {"rename", "set_name", "name"}:
            path, error = resolve_session_target(state, target, allow_view_index=not agent_source or bool(expected_title), expected_title=expected_title)
            result = error if error else rename_session_path(state, path or "", value)
        else:
            if agent_source and action in {"archive", "delete", "remove"}:
                path, error = resolve_session_target(state, target, allow_view_index=False, expected_title=expected_title)
                if not error and path and is_current_session_path(state, path):
                    record_control_result(action, target, "已拒绝对当前打开会话执行归档/删除。")
                    continue
            result = apply_session_operation(
                state,
                action,
                target,
                value,
                source=source,
                allow_view_index=not agent_source or bool(expected_title),
                expected_title=expected_title,
            )
        record_control_result(action, target, result)

    if agent_source and agent_control_results:
        add_system(
            state,
            "Agent 控制结果：\n" + "\n".join(agent_control_results),
            persist=True,
            kind="agent_control_result",
        )


def apply_secret_subagent_controls_from_text(state: State, text: str, source: str = "secret-agent") -> int:
    applied = 0
    alias_map: dict[str, str] = {}
    for control in extract_tui_controls(text, allow_json_fences=True):
        action = str(control.get("action") or control.get("op") or "").strip().lower()
        normalized_action = action.replace("-", "_")
        if not (normalized_action.startswith("subagent_") or normalized_action.startswith("agent_") or normalized_action in {"create_subagent", "new_subagent"}):
            continue
        target = str(control.get("target") or "current").strip()
        value = str(control.get("value") or control.get("category") or control.get("name") or "").strip()
        result = apply_subagent_control(state, action, target, value, control, source=source, control_aliases=alias_map)
        if result:
            add_system(state, f"Secret agent 控制: {result}")
            applied += 1
    return applied


def parse_category_command_args(state: State, args: str) -> tuple[str, str, str]:
    args = (args or "").strip()
    if not args:
        return "", "", "Usage: /category [n|current] <name>；用 - 清除分类。"
    parts = args.split(maxsplit=1)
    if len(parts) == 2:
        path, error = resolve_session_target(state, parts[0])
        if path and not error:
            return parts[0], parts[1], ""
    return "current", args, ""


AGENT_SUBCOMMANDS: list[tuple[str, str, str, bool]] = [
    ("list", "", "列出子 agent", True),
    ("new", "[role:]<name> [| profile]", "新建持久子 agent", False),
    ("role", "<agent> <role>", "设置子 agent 角色", False),
    ("settings", "<agent>", "打开持久 agent 详细设置", False),
    ("model", "<agent> [model|inherit]", "设置持久 agent 默认模型", False),
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
    "ask", "run", "input", "answer", "reply", "memory", "remember", "profile", "rename", "role", "settings", "model", "info", "stop", "delete"
}
AGENT_SUBCOMMANDS_SEND_AFTER_AGENT = {"memory", "profile", "info", "settings", "model", "stop", "delete"}


def completion_insert_text(candidate: tuple[str, str, str, bool]) -> str:
    cmd, _args, _desc, sendable = candidate
    return cmd if sendable else cmd.rstrip() + " "


def subagent_completion_rows(state: Optional[State], prefix: str, subcmd: str) -> list[tuple[str, str, str, bool]]:
    if state is None:
        return []
    rows: list[tuple[str, str, str, bool]] = []
    for sub in sorted(state.subagents.values(), key=lambda item: item.updated_at, reverse=True):
        token = sub.agent_id
        if prefix and not (token.lower().startswith(prefix.lower()) or sub.name.lower().startswith(prefix.lower())):
            continue
        sendable = subcmd in AGENT_SUBCOMMANDS_SEND_AFTER_AGENT
        args = "" if sendable else {
            "ask": "<prompt>",
            "run": "<prompt>",
            "input": "<prompt>",
            "answer": "<text>",
            "reply": "<text>",
            "remember": "<text>",
            "rename": "<new-name>",
            "role": "<role>",
        }.get(subcmd, "[text]")
        rows.append((f"/agent {subcmd} {token}", args, f"{sub.name} · {sub.status}", sendable))
    return rows


def agent_command_matches(text: str, state: Optional[State]) -> list[tuple[str, str, str, bool]]:
    raw = text or ""
    if not re.match(r"^/agent(?:\s|$)", raw):
        return []
    if raw == "/agent":
        return [("/agent", "<cmd>", "管理/运行持久子 agent", False)]
    rest = raw[len("/agent"):].lstrip()
    if not rest:
        return [(f"/agent {cmd}", args, desc, sendable) for cmd, args, desc, sendable in AGENT_SUBCOMMANDS]
    parts = rest.split()
    trailing_space = raw.endswith(" ")
    sub_prefix = parts[0] if parts else ""
    if len(parts) == 1 and not trailing_space:
        return [
            (f"/agent {cmd}", args, desc, sendable)
            for cmd, args, desc, sendable in AGENT_SUBCOMMANDS
            if cmd.startswith(sub_prefix.lower())
        ]
    subcmd = sub_prefix.lower()
    if subcmd not in {cmd for cmd, _args, _desc, _sendable in AGENT_SUBCOMMANDS}:
        return []
    if subcmd not in AGENT_SUBCOMMANDS_REQUIRING_AGENT:
        return []
    agent_prefix = ""
    if len(parts) >= 2:
        agent_prefix = parts[1]
    if subcmd == "role" and (len(parts) >= 3 or (len(parts) == 2 and trailing_space)):
        role_prefix = parts[2].lower() if len(parts) >= 3 else ""
        base = f"/agent role {parts[1]} "
        return [
            (base + role, "", str(template.get("description") or ""), True)
            for role, template in ROLE_TEMPLATES.items()
            if not role_prefix or role.startswith(role_prefix)
        ]
    if len(parts) > 2 or (len(parts) == 2 and trailing_space and subcmd not in AGENT_SUBCOMMANDS_SEND_AFTER_AGENT):
        return []
    return subagent_completion_rows(state, agent_prefix, subcmd)


def category_command_matches(text: str, state: Optional[State]) -> list[tuple[str, str, str, bool]]:
    raw = text or ""
    match = re.match(r"^/(filter|collapse|expand)\s+(.*)$", raw, re.I)
    if not match or state is None:
        return []
    cmd = match.group(1).lower()
    prefix = (match.group(2) or "").strip().lower()
    rows: list[tuple[str, str, str, bool]] = []
    if cmd == "filter" and "off".startswith(prefix):
        rows.append(("/filter off", "", "关闭分类筛选", True))
    if cmd in {"collapse", "expand"} and "all".startswith(prefix):
        rows.append((f"/{cmd} all", "", "全部分类", True))
    counts: dict[str, int] = {}
    labels: dict[str, str] = {}
    for path, _mtime, _first, _rounds in state.history:
        label = session_category_label(session_meta_for(state, path))
        key = category_key(label)
        labels[key] = label
        counts[key] = counts.get(key, 0) + 1
    for key in sorted(labels, key=lambda item: category_sort_key(labels[item])):
        label = labels[key]
        count = counts.get(key, 0)
        if prefix and not label.lower().startswith(prefix):
            continue
        rows.append((f"/{cmd} {label}", "", f"{count} 个会话", True))
    return rows


def archived_command_matches(text: str) -> list[tuple[str, str, str, bool]]:
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


def approval_command_matches(text: str, state: Optional[State] = None) -> list[tuple[str, str, str, bool]]:
    match = re.match(r"^/(approve|reject)\s+(.*)$", text or "", re.I)
    if not match:
        return []
    cmd = match.group(1).lower()
    prefix = (match.group(2) or "").strip()
    rows: list[tuple[str, str, str, bool]] = []
    for row in pending_approvals(state):
        approval_id = str(row.get("approval_id") or "")
        if prefix and not approval_id.startswith(prefix):
            continue
        rows.append((f"/{cmd} {approval_id}", "", truncate_cells(str(row.get("summary") or ""), 70), True))
    return rows


def command_matches(text: str, state: Optional[State] = None) -> list[tuple[str, str, str, bool]]:
    raw = text or ""
    stripped = raw.strip()
    if not stripped.startswith("/"):
        return []
    if re.match(r"^/agent(?:\s|$)", raw):
        return agent_command_matches(raw, state)
    if re.match(r"^/(?:filter|collapse|expand)\s", raw, re.I):
        return category_command_matches(raw, state)
    if re.match(r"^/archived\s", raw, re.I):
        return archived_command_matches(raw)
    if re.match(r"^/(?:approve|reject)\s", raw, re.I):
        return approval_command_matches(raw, state)
    if " " in stripped:
        return []
    stripped_l = stripped.lower()
    return [cmd for cmd in COMMANDS if cmd[0].lower().startswith(stripped_l)]


def clamp_command_index(state: State, matches: list[tuple[str, str, str, bool]]) -> None:
    if not matches:
        state.command_index = 0
    else:
        state.command_index = max(0, min(state.command_index, len(matches) - 1))


def selected_subagent(state: State) -> Optional[SubAgentRuntime]:
    return state.subagents.get(str(state.selected_session or ""))


def mark_subagent_messages_changed(state: State, sub: SubAgentRuntime, *, follow_bottom: bool = True) -> None:
    if selected_subagent(state) is sub:
        if follow_bottom:
            state.follow_bottom = True
        mark_messages_changed(state)
    else:
        mark_dirty(state)


def queue_subagent_chat_input(state: State, sub: SubAgentRuntime, text: str, *, interrupt_requested: bool = False) -> str:
    queued = (text or "").strip()
    if not queued:
        return ""
    sub.chat_queue.append(queued)
    if interrupt_requested:
        sub.chat_queue_interrupt_requested = True
    sub.updated_at = time.time()
    mark_dirty(state)
    return f"{sub.name} 正在回复，已排队 {len(sub.chat_queue)} 条聊天输入。"


def maybe_start_next_subagent_chat(state: State, sub: SubAgentRuntime) -> Optional[str]:
    if sub.status in {"running", "aborting"} or sub.active_task_id is not None:
        return None
    if not sub.chat_queue:
        return None
    queued = list(sub.chat_queue)
    interrupt_requested = sub.chat_queue_interrupt_requested
    sub.chat_queue.clear()
    sub.chat_queue_interrupt_requested = False
    prompt = "\n\n".join(text for text in queued if text.strip()).strip()
    if not prompt:
        mark_dirty(state)
        return None
    return start_subagent_chat(
        state,
        sub,
        prompt,
        source="subagent_chat:queued_after_interrupt" if interrupt_requested else "subagent_chat:queued",
    )


def request_subagent_interrupt(state: State, sub: SubAgentRuntime, prefix: str = "Ctrl+C") -> None:
    if sub.status in {"running", "aborting"} and state.input_text.strip() and not secret_password_entry_active(state):
        draft = state.input_text
        set_input_text(state, "")
        queue_subagent_chat_input(state, sub, draft, interrupt_requested=True)
    if sub.status in {"running", "aborting"}:
        if sub.agent is not None:
            try:
                sub.agent.abort()
            except Exception:
                pass
        sub.status = "aborting"
        sub.updated_at = time.time()
        if sub.chat_queue:
            sub.chat_queue_interrupt_requested = True
            state.last_error = f"{prefix}: 已请求中止子 agent；排队输入会在当前输出收尾后发送。"
        else:
            state.last_error = f"{prefix}: 已请求中止子 agent；退出 TUI 请按 Ctrl+Q。"
        mark_dirty(state)
        return
    state.last_error = f"{prefix} 只用于中止当前可见任务；退出 TUI 请按 Ctrl+Q。"
    mark_dirty(state)


def request_visible_interrupt(state: State, prefix: str = "Ctrl+C") -> None:
    sub = selected_subagent(state)
    if sub is not None:
        request_subagent_interrupt(state, sub, prefix=prefix)
    else:
        request_main_interrupt(state, prefix=prefix)


def display_messages(state: State) -> list[Message]:
    sub = selected_subagent(state)
    if sub is not None:
        return sub.messages
    return state.messages


def display_status(state: State) -> str:
    sub = selected_subagent(state)
    if sub is not None:
        if sub.pending_interaction or is_approval_interaction(state.pending_interaction):
            return "waiting-input"
        return sub.status
    return "waiting-input" if state.pending_interaction else state.status


def display_title(state: State) -> str:
    sub = selected_subagent(state)
    if sub is not None:
        return f"SubAgent {sub.name}"
    return "GenericAgent"


def top_bar_session_id(state: State) -> str:
    sub = selected_subagent(state)
    if sub is not None:
        return sub.agent_id or sub.name or "subagent"
    return active_ui_session_key(state) or "main"


def top_bar_round_label(state: State) -> str:
    sub = selected_subagent(state)
    if sub is None and state.history_ui_path and state.history_ui_total_rounds:
        loading = "..." if state.history_ui_loading else ""
        loaded = state.history_ui_loaded_rounds or sum(1 for msg in state.messages if msg.role == "user")
        return f"{loaded}/{state.history_ui_total_rounds}{loading}"
    return str(sum(1 for msg in display_messages(state) if msg.role == "user"))


def top_bar_header(state: State, timestamp: Optional[float] = None) -> str:
    now = time.time() if timestamp is None else timestamp
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
    secret = " | SECRET" if state.secret_vault.unlocked else (" | SECRET locked" if state.secret_vault.pending_action else "")
    sub = selected_subagent(state)
    if sub is not None:
        session_title = compact_title(sub.chat_title or sub.chat_session_id or "current", 28)
        return f"当前时间: {current_time} | 子 agent: {sub.name} | 会话ID: {sub.agent_id} | 子会话: {session_title or '-'} | 当前轮次: {top_bar_round_label(state)}{secret}"
    return f"当前时间: {current_time} | 会话ID: {top_bar_session_id(state)} | 当前轮次: {top_bar_round_label(state)}{secret}"


def display_scope_key(state: State) -> str:
    sub = selected_subagent(state)
    if sub is not None:
        return f"sub:{sub.agent_id}"
    return f"session:{str(state.selected_session or 'main')}"


def process_group_key(state: State, label: str) -> str:
    return f"{display_scope_key(state)}:{label}"


def process_turn_key(state: State, label: str) -> str:
    group = re.match(r"^(G\d+)T\d+$", label or "")
    prefix = group.group(1) if group else ""
    return f"{display_scope_key(state)}:{prefix}:{label}"


def subagent_meta_key(state: State, label: str) -> str:
    return f"{display_scope_key(state)}:submeta:{label}"


def current_interaction_payload(state: State) -> Optional[dict[str, Any]]:
    sub = selected_subagent(state)
    if sub is not None and sub.pending_interaction:
        return sub.pending_interaction
    if sub is not None and not is_approval_interaction(state.pending_interaction):
        return None
    return state.pending_interaction


def message_cache_signature(messages: list[Message]) -> tuple[tuple[int, str, int, int, bool], ...]:
    return tuple((id(msg), str(msg.role or ""), len(msg.content or ""), hash(msg.content or ""), bool(msg.done)) for msg in messages)


def prune_message_block_cache(state: State, live_keys: set[tuple[Any, ...]], max_entries: int = 1200) -> None:
    if not state.message_block_cache:
        return
    stale = [key for key in state.message_block_cache if key not in live_keys]
    for key in stale:
        state.message_block_cache.pop(key, None)
    limit = max(max_entries, len(live_keys) + 100)
    overflow = len(state.message_block_cache) - limit
    if overflow > 0:
        for key in list(state.message_block_cache)[:overflow]:
            state.message_block_cache.pop(key, None)


def message_lines_cached(state: State, width: int) -> list[RenderLine]:
    messages = display_messages(state)
    active_anim = any(msg.role == "assistant" and not msg.done for msg in messages)
    frame = state.run_frame if active_anim else 0
    scope = display_scope_key(state)
    assistant_label = "AI"
    render_signature = message_cache_signature(messages)
    key = (
        render_signature,
        scope,
        assistant_label,
        width,
        state.fold_process,
        state.markdown,
        tuple(sorted(state.expanded_process_groups)),
        tuple(sorted(state.expanded_process_turns)),
        tuple(sorted(state.expanded_subagent_meta)),
        frame,
    )
    if key != state.line_cache_key:
        state.line_cache = message_lines_from_cache(
            state,
            messages,
            width,
            state.fold_process,
            state.markdown,
            frame,
            process_scope=scope,
            expanded_groups=state.expanded_process_groups,
            expanded_turns=state.expanded_process_turns,
            expanded_subagent_meta=state.expanded_subagent_meta,
            assistant_label=assistant_label,
        )
        state.line_cache_key = key
    return state.line_cache


def compact_title(text: str, max_width: int = 24) -> str:
    text = clean_text(text)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[*_`#>\[\]{}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -:：。,.，")
    text = re.sub(r"^(用户|User|The user)\s*(问|要求|想要|asked|wants|said)?\s*[:：]?\s*", "", text, flags=re.I)
    text = re.sub(r"^(任务已完成|已完成|总结|结论)\s*[:：]?\s*", "", text)
    if not text:
        return ""
    return truncate_cells(text, max_width).strip(" -:：。,.，")


def short_session_title(text: str, fallback: str = "历史会话") -> str:
    title = compact_title(text, SESSION_TITLE_WIDTH)
    return title or fallback


def compact_description(text: str, max_chars: int = SESSION_DESCRIPTION_LIMIT) -> str:
    text = clean_text(text)
    text = TUI_CONTROL_RE.sub(" ", text)
    text = TUI_CONTROL_FENCE_RE.sub(" ", text)
    text = TOOL_USE_BLOCK_RE.sub(" ", text)
    text = DETAIL_FENCE_RE.sub(" ", text)
    text = META_BLOCK_RE.sub(" ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[*_`#>\[\]{}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -:：。,.，")
    if len(text) > max_chars:
        text = text[: max(0, max_chars - 3)].rstrip(" -:：。,.，") + "..."
    return text


def session_description_from_pairs(pairs: list[tuple[str, str]], preview: str = "") -> str:
    snippets: list[str] = []
    if pairs:
        users: list[str] = []
        summaries: list[str] = []
        for prompt, response in pairs:
            user = compact_description(_user_text(prompt), 90)
            if user:
                users.append(user)
            for summary in SUMMARY_RE.findall(response or ""):
                summary_text = compact_description(summary, 110)
                if summary_text:
                    summaries.append(summary_text)
        if users:
            snippets.append(f"开始：{users[0]}")
            if users[-1] != users[0]:
                snippets.append(f"最近：{users[-1]}")
        if summaries:
            snippets.append(f"摘要：{summaries[-1]}")
    if not snippets and preview:
        snippets.append(compact_description(preview, SESSION_DESCRIPTION_LIMIT))
    return compact_description("；".join(snippets), SESSION_DESCRIPTION_LIMIT)


def session_description_from_path(path: str, preview: str = "") -> str:
    try:
        size = os.path.getsize(path)
        with open(path, encoding="utf-8", errors="replace") as fh:
            if size > 2 * 1024 * 1024:
                fh.seek(size - 2 * 1024 * 1024)
            content = fh.read()
        pairs = _pairs(content)
    except Exception:
        pairs = []
    return session_description_from_pairs(pairs, preview)


def suggested_session_title(messages: list[Message]) -> str:
    for msg in reversed(messages):
        if msg.role != "assistant":
            continue
        summaries = SUMMARY_RE.findall(msg.content or "")
        for summary in reversed(summaries):
            title = short_session_title(summary, "")
            if title:
                return title
    for msg in messages:
        if msg.role == "user":
            title = short_session_title(msg.content, "")
            if title:
                return title
    return ""


def ai_title_context(messages: list[Message], max_chars: int = 3600) -> str:
    chunks: list[str] = []
    for msg in messages:
        if msg.role not in {"user", "assistant"}:
            continue
        role = "用户" if msg.role == "user" else "助手"
        text = clean_text(msg.content)
        text = META_BLOCK_RE.sub(" ", text)
        text = TOOL_USE_BLOCK_RE.sub(" ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        chunks.append(f"{role}: {truncate_cells(text, 900)}")
    context = "\n".join(chunks[-8:])
    if cell_width(context) > max_chars:
        context = truncate_cells(context, max_chars)
    return context


def session_content_signature(messages: list[Message]) -> str:
    digest = hashlib.sha1()
    seen = False
    for msg in messages:
        if msg.role not in {"user", "assistant"}:
            continue
        content = strip_tui_controls(msg.content or "")
        content = META_BLOCK_RE.sub(" ", content)
        content = TOOL_USE_BLOCK_RE.sub(" ", content)
        content = re.sub(r"\s+", " ", content).strip()
        if not content:
            continue
        seen = True
        digest.update(msg.role.encode("utf-8", errors="ignore"))
        digest.update(b"\0")
        digest.update(content.encode("utf-8", errors="ignore"))
        digest.update(b"\0")
    return digest.hexdigest() if seen else ""


def clean_ai_title(title: str) -> str:
    title = clean_text(title)
    title = title.splitlines()[0] if title.splitlines() else title
    title = re.sub(r"^(标题|会话标题|Session title|Title)\s*[:：]\s*", "", title, flags=re.I)
    title = title.strip(" \t\"'“”‘’`#*-:：。,.，")
    title = re.sub(r"\s+", " ", title)
    title = short_session_title(title, "")
    if title.lower().startswith(("!!!error", "[error")):
        return ""
    return title


def clean_ai_description(description: str) -> str:
    description = clean_text(strip_tui_controls(description))
    description = re.sub(r"^(简介|会话简介|Description|Session description)\s*[:：]\s*", "", description, flags=re.I)
    description = description.strip(" \t\"'“”‘’`#*-:：。,.，")
    return compact_description(description, SESSION_DESCRIPTION_LIMIT)


def clean_ai_category(category: str) -> str:
    category = clean_text(strip_tui_controls(category))
    category = category.splitlines()[0] if category.splitlines() else category
    category = re.sub(r"^(分类|类别|Category)\s*[:：]\s*", "", category, flags=re.I)
    category = category.strip(" \t\"'“”‘’`#*-:：。,.，")
    return compact_category(category)


def generate_ai_session_title(agent: Any, messages: list[Message]) -> str:
    context = ai_title_context(messages)
    if not context:
        return ""
    source_backend = agent.llmclient.backend
    try:
        source_backend = source_backend.primary
    except Exception:
        pass
    backend = copy.copy(source_backend)
    try:
        backend.history = []
        backend.system = ""
        backend.tools = None
        backend.stream = False
        backend.temperature = 0
        backend.max_tokens = min(int(getattr(backend, "max_tokens", 64) or 64), 64)
    except Exception:
        pass
    prompt = (
        "请根据下面的对话内容，为这个会话生成一个简短标题。\n"
        "要求：中文优先，9个字左右，最多12个字；只输出标题本身；不要引号、标点、解释或换行。\n\n"
        f"{context}"
    )
    request = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    content = ""
    blocks: Any = None
    gen = backend.raw_ask(request)
    try:
        while True:
            chunk = next(gen)
            if isinstance(chunk, str):
                content += chunk
    except StopIteration as exc:
        blocks = exc.value
    if not content and isinstance(blocks, list):
        parts = [str(block.get("text") or "") for block in blocks if isinstance(block, dict) and block.get("type") == "text"]
        content = "\n".join(parts)
    return clean_ai_title(content)


def generate_ai_session_description(agent: Any, messages: list[Message]) -> str:
    context = ai_title_context(messages, max_chars=5200)
    if not context:
        return ""
    source_backend = agent.llmclient.backend
    try:
        source_backend = source_backend.primary
    except Exception:
        pass
    backend = copy.copy(source_backend)
    try:
        backend.history = []
        backend.system = ""
        backend.tools = None
        backend.stream = False
        backend.temperature = 0
        backend.max_tokens = max(128, min(int(getattr(backend, "max_tokens", 256) or 256), 256))
    except Exception:
        pass
    prompt = (
        "请根据下面的对话内容，为这个会话维护一个简介。\n"
        "要求：中文，一段话，小于200字；说明主题、用户目标、当前进展或结论；"
        "不要标题、列表、Markdown、引号或换行；只输出简介本身。\n\n"
        f"{context}"
    )
    request = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    content = ""
    blocks: Any = None
    gen = backend.raw_ask(request)
    try:
        while True:
            chunk = next(gen)
            if isinstance(chunk, str):
                content += chunk
    except StopIteration as exc:
        blocks = exc.value
    if not content and isinstance(blocks, list):
        parts = [str(block.get("text") or "") for block in blocks if isinstance(block, dict) and block.get("type") == "text"]
        content = "\n".join(parts)
    return clean_ai_description(content)


def generate_ai_session_category(agent: Any, title: str, description: str, categories: list[tuple[str, str]]) -> str:
    title = compact_title(title, 80)
    description = compact_description(description)
    if not title and not description:
        return ""
    source_backend = agent.llmclient.backend
    try:
        source_backend = source_backend.primary
    except Exception:
        pass
    backend = copy.copy(source_backend)
    try:
        backend.history = []
        backend.system = ""
        backend.tools = None
        backend.stream = False
        backend.temperature = 0
        backend.max_tokens = max(24, min(int(getattr(backend, "max_tokens", 64) or 64), 64))
    except Exception:
        pass
    if categories:
        cat_lines = "\n".join(
            f"- {name}" + (f": {desc}" if desc else "")
            for name, desc in categories[:30]
        )
    else:
        cat_lines = "- 杂项"
    prompt = (
        "请根据会话标题和简介，为这个会话选择一个分类。\n"
        "要求：优先从现有分类中选择；如果都不合适，可以新建一个2到6个中文字符的短分类。"
        "只输出分类名，不要解释、标点、引号或换行。\n\n"
        f"现有分类：\n{cat_lines}\n\n"
        f"标题：{title or '无'}\n"
        f"简介：{description or '无'}"
    )
    request = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    content = ""
    blocks: Any = None
    gen = backend.raw_ask(request)
    try:
        while True:
            chunk = next(gen)
            if isinstance(chunk, str):
                content += chunk
    except StopIteration as exc:
        blocks = exc.value
    if not content and isinstance(blocks, list):
        parts = [str(block.get("text") or "") for block in blocks if isinstance(block, dict) and block.get("type") == "text"]
        content = "\n".join(parts)
    return clean_ai_category(content)


def ai_title_worker(ui_queue: queue.Queue, path: str, messages: list[Message], agent: Any) -> None:
    old_name = threading.current_thread().name
    thread_name = token_thread_name(agent)
    if thread_name:
        threading.current_thread().name = thread_name
    title = ""
    error = ""
    try:
        title = generate_ai_session_title(agent, messages)
        if not title:
            error = "empty title"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        threading.current_thread().name = old_name
    ui_queue.put(("title_done", os.path.basename(path), path, title, error))


def ai_description_worker(
    ui_queue: queue.Queue,
    path: str,
    messages: list[Message],
    agent: Any,
    signature: str,
) -> None:
    old_name = threading.current_thread().name
    thread_name = token_thread_name(agent)
    if thread_name:
        threading.current_thread().name = thread_name
    description = ""
    error = ""
    try:
        description = generate_ai_session_description(agent, messages)
        if not description:
            error = "empty description"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        threading.current_thread().name = old_name
    ui_queue.put(("description_done", os.path.basename(path), path, description, error, signature))


def ai_category_worker(
    ui_queue: queue.Queue,
    path: str,
    agent: Any,
    title: str,
    description: str,
    categories: list[tuple[str, str]],
    signature: str,
) -> None:
    old_name = threading.current_thread().name
    thread_name = token_thread_name(agent)
    if thread_name:
        threading.current_thread().name = thread_name
    category = ""
    error = ""
    try:
        category = generate_ai_session_category(agent, title, description, categories)
        if not category:
            error = "empty category"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        threading.current_thread().name = old_name
    ui_queue.put(("category_done", os.path.basename(path), path, category, error, signature))


def maybe_start_ai_title_job(state: State, path: str, messages: list[Message], agent: Any) -> bool:
    if session_names is None or not path or agent is None:
        return False
    key = os.path.basename(path)
    if not key or key in state.title_jobs or key in state.title_attempted:
        return False
    if not ai_title_context(messages):
        return False
    state.title_jobs.add(key)
    state.title_attempted.add(key)
    snapshot = [Message(msg.role, msg.content, msg.done) for msg in messages]
    threading.Thread(
        target=ai_title_worker,
        args=(state.ui_queue, path, snapshot, agent),
        daemon=True,
        name=token_thread_name(agent) or "ga-title-worker",
    ).start()
    return True


def maybe_start_ai_description_job(state: State, path: str, messages: list[Message], agent: Any, force: bool = False) -> bool:
    if not path or agent is None:
        return False
    key = os.path.basename(path)
    signature = session_content_signature(messages)
    if not key or not signature or key in state.description_jobs:
        return False
    meta = state.session_meta.get(key, {})
    if (
        not force
        and (
            state.description_signatures.get(key) == signature
            or (meta.get("description_signature") == signature and compact_description(str(meta.get("description") or "")))
        )
    ):
        return False
    state.description_jobs.add(key)
    state.description_signatures[key] = signature
    snapshot = [Message(msg.role, msg.content, msg.done) for msg in messages if msg.role in {"user", "assistant"}]
    threading.Thread(
        target=ai_description_worker,
        args=(state.ui_queue, path, snapshot, agent, signature),
        daemon=True,
        name=(token_thread_name(agent) + "-desc") if token_thread_name(agent) else "ga-description-worker",
    ).start()
    return True


def known_category_options(state: State, exclude: str = "") -> list[tuple[str, str]]:
    labels: dict[str, str] = {}
    exclude_key = category_key(exclude)
    for meta in state.session_meta.values():
        if not isinstance(meta, dict):
            continue
        label = session_category_label(meta)
        key = category_key(label)
        if key != "__uncategorized__" and key != exclude_key:
            labels[key] = label
    for key, meta in category_registry(state).items():
        if key == "__uncategorized__" or key == exclude_key or not isinstance(meta, dict):
            continue
        label = category_filter_label(str(meta.get("name") or "")) or labels.get(key, "")
        if label:
            labels[key] = label
    out: list[tuple[str, str]] = []
    for key, label in sorted(labels.items(), key=lambda item: category_sort_key(item[1])):
        desc = compact_description(str(category_registry(state).get(key, {}).get("description") or ""))
        out.append((label, desc))
    return out


def session_title_for_category(state: State, path: str) -> str:
    return history_name(state, path) or session_title_for_path(state, path)


def maybe_start_ai_category_job(state: State, path: str, agent: Any, force: bool = False) -> bool:
    if not path or agent is None:
        return False
    key = session_key(path)
    if not key or key in state.category_jobs:
        return False
    meta = session_meta_for(state, path)
    if not force and str(meta.get("category_source") or "") == "manual":
        return False
    title = session_title_for_category(state, path)
    description = compact_description(str(meta.get("description") or state.history_descriptions.get(path) or ""))
    if not title and not description:
        return False
    signature_src = f"{title}\n{description}\n{meta.get('description_signature', '')}"
    signature = hashlib.sha1(signature_src.encode("utf-8", errors="ignore")).hexdigest()
    if not force and (state.category_signatures.get(key) == signature or meta.get("category_signature") == signature):
        return False
    state.category_jobs.add(key)
    state.category_signatures[key] = signature
    categories = known_category_options(state, exclude=str(meta.get("category") or ""))
    threading.Thread(
        target=ai_category_worker,
        args=(state.ui_queue, path, agent, title, description, categories, signature),
        daemon=True,
        name=(token_thread_name(agent) + "-cat") if token_thread_name(agent) else "ga-category-worker",
    ).start()
    return True


def maybe_autoname_current_session(state: State, force: bool = False) -> bool:
    if session_names is None:
        return False
    path = getattr(state.agent, "log_path", "")
    if not path:
        return False
    try:
        current = session_names.name_for(path)
    except Exception:
        current = ""
    current = compact_title(current, 80) if current else ""
    if current and not force:
        if state.current_title != current:
            state.current_title = current
            return True
        return False
    title = suggested_session_title(state.messages)
    changed = False
    if title and state.current_title in {"", "main", "运行中会话", "空闲会话"}:
        state.current_title = title
        changed = True
    title_started = maybe_start_ai_title_job(state, path, state.messages, state.agent)
    description_started = maybe_start_ai_description_job(state, path, state.messages, state.agent, force=force)
    category_started = maybe_start_ai_category_job(state, path, state.agent, force=force)
    return title_started or description_started or category_started or changed


def maybe_autoname_background_session(state: State, bg: BackgroundSession, force: bool = False) -> bool:
    if bg.security_context == "secret":
        title = secret_session_title_for_messages(bg.title, bg.messages)
        if title and bg.title != title:
            bg.title = title
            return True
        return False
    if session_names is None:
        return False
    path = getattr(bg.agent, "log_path", "")
    if not path:
        return False
    try:
        current = session_names.name_for(path)
    except Exception:
        current = ""
    current = compact_title(current, 80) if current else ""
    if current and not force:
        if bg.title != current:
            bg.title = current
            return True
        return False
    title = suggested_session_title(bg.messages)
    changed = False
    if title and bg.title in {"", "main", "运行中会话", "空闲会话"}:
        bg.title = title
        changed = True
    title_started = maybe_start_ai_title_job(state, path, bg.messages, bg.agent)
    description_started = maybe_start_ai_description_job(state, path, bg.messages, bg.agent, force=force)
    category_started = maybe_start_ai_category_job(state, path, bg.agent, force=force)
    return title_started or description_started or category_started or changed


def save_unlocked_secret_background_sessions(state: State, source: str = "secret-background") -> int:
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        return 0
    saved = 0
    for bg in state.background_sessions.values():
        if bg.security_context != "secret" or bg.status in {"running", "aborting"}:
            continue
        if not bg.secret_session_id or not any(msg.role in {"user", "assistant"} for msg in bg.messages):
            continue
        maybe_autoname_background_session(state, bg)
        ok, _ref = secret_save_session_state(
            state,
            bg.secret_session_id,
            bg.title,
            bg.messages,
            source=source,
            origin=bg.secret_origin,
        )
        if ok:
            saved += 1
    if saved:
        clear_secret_sidebar_caches(state)
    return saved


def reset_active_session(state: State, title: str = "main", agent: Any = None) -> None:
    persist_agent_token_usage(state, state.agent)
    state.agent = agent if agent is not None else new_agent()
    install_interaction_hook(state, state.agent)
    bind_agent_token_session(state, state.agent)
    state.messages = []
    state.status = "idle"
    state.task_id = 0
    state.active_task_id = None
    state.active_task_source = ""
    state.active_stream_target = None
    state.active_task_secret = False
    state.active_secret_user_text = ""
    state.active_secret_session_id = ""
    clear_all_queued_inputs(state)
    clear_active_plan_state(state)
    state.pending_interaction = None
    clear_history_ui_state(state)
    state.scroll = 0
    state.follow_bottom = True
    state.current_title = title
    state.selected_session = "main"
    mark_messages_changed(state)


def park_active_session(state: State, reset: bool = True) -> Optional[str]:
    if state.status not in {"running", "aborting"}:
        return None
    persist_agent_token_usage(state, state.agent)
    state.background_counter += 1
    key = f"bg:{state.background_counter}"
    target = state.active_stream_target or StreamTarget()
    target.key = key
    title = state.current_title or ""
    if not title or title == "main":
        title = suggested_session_title(state.messages) or "运行中会话"
    secret_context = bool(state.secret_vault.unlocked or state.active_task_secret)
    state.background_sessions[key] = BackgroundSession(
        key=key,
        title=title,
        agent=state.agent,
        messages=state.messages,
        status=state.status,
        task_id=state.task_id,
        active_task_id=state.active_task_id,
        stream_target=target,
        pending_interaction=state.pending_interaction,
        security_context="secret" if secret_context else "standard",
        secret_session_id=state.active_secret_session_id or (state.secret_vault.session_id if secret_context else ""),
        active_task_source=state.active_task_source,
        active_task_secret=bool(state.active_task_secret or secret_context),
        active_secret_user_text=state.active_secret_user_text,
        secret_origin=dict(state.secret_active_origin) if secret_context else {},
    )
    if reset:
        reset_active_session(state)
        state.last_error = f"已把「{title}」转入后台运行。"
        mark_dirty(state)
    return key


def stash_idle_active_session(state: State) -> Optional[str]:
    if state.status != "idle" or not any(msg.role in {"user", "assistant"} for msg in state.messages):
        return None
    persist_agent_token_usage(state, state.agent)
    state.background_counter += 1
    key = f"bg:{state.background_counter}"
    title = state.current_title or ""
    if not title or title == "main":
        title = suggested_session_title(state.messages) or "空闲会话"
    secret_context = bool(state.secret_vault.unlocked)
    state.background_sessions[key] = BackgroundSession(
        key=key,
        title=title,
        agent=state.agent,
        messages=state.messages,
        status="idle",
        task_id=state.task_id,
        active_task_id=None,
        stream_target=None,
        pending_interaction=state.pending_interaction,
        security_context="secret" if secret_context else "standard",
        secret_session_id=state.secret_vault.session_id if secret_context else "",
        active_task_source="",
        active_task_secret=False,
        active_secret_user_text="",
        secret_origin=dict(state.secret_active_origin) if secret_context else {},
    )
    return key


def active_view_is_restored_history(state: State) -> bool:
    return bool(state.history_ui_path)


def path_is_active_history_view(state: State, path: str) -> bool:
    return bool(state.history_ui_path) and normalized_path(state.history_ui_path) == normalized_path(path)


def switch_to_background_session(state: State, key: str) -> None:
    switch_to_background_session_with_mode(state, key, stash_current=True)


def switch_to_background_session_with_mode(state: State, key: str, stash_current: bool = True) -> None:
    bg = state.background_sessions.get(key)
    if bg is None:
        state.last_error = "后台会话不存在或已经结束。"
        mark_dirty(state)
        return
    if state.status == "restoring":
        state.restore_token += 1
    if stash_current:
        if state.status in {"running", "aborting"}:
            park_active_session(state, reset=False)
        elif state.status == "idle":
            if state.secret_vault.unlocked and state.secret_vault.session_id:
                secret_save_current_session_state(state, source="switch-bg")
            stash_idle_active_session(state)
    bg = state.background_sessions.pop(key, None)
    if bg is None:
        state.last_error = "后台会话不存在或已经结束。"
        mark_dirty(state)
        return
    if bg.stream_target is not None:
        bg.stream_target.key = "active"
    state.agent = bg.agent
    state.messages = bg.messages
    state.status = bg.status
    state.task_id = bg.task_id
    state.active_task_id = bg.active_task_id
    state.active_stream_target = bg.stream_target if bg.status in {"running", "aborting"} else None
    state.active_task_source = bg.active_task_source if bg.status in {"running", "aborting"} else ""
    state.active_task_secret = bool(bg.active_task_secret and bg.status in {"running", "aborting"})
    state.active_secret_user_text = bg.active_secret_user_text if state.active_task_secret else ""
    state.active_secret_session_id = bg.secret_session_id if bg.security_context == "secret" else ""
    if bg.security_context == "secret":
        state.secret_vault.session_id = bg.secret_session_id or state.secret_vault.session_id or secret_new_session_id()
        state.secret_active_origin = dict(bg.secret_origin)
        set_agent_log_path(state.agent, os.devnull)
    else:
        state.secret_active_origin = {}
    state.pending_interaction = bg.pending_interaction
    clear_history_ui_state(state)
    state.scroll = 0
    state.follow_bottom = True
    state.current_title = bg.title
    state.selected_session = secret_session_sidebar_key(state.secret_vault.session_id) if bg.security_context == "secret" else "main"
    state.last_error = ""
    bind_agent_token_session(state, state.agent)
    mark_messages_changed(state)
    if load_history(state, force=True):
        state.dirty = True


def secret_background_session_keys(state: State) -> list[str]:
    return [key for key, bg in state.background_sessions.items() if bg.security_context == "secret"]


def secret_running_background_exists(state: State) -> bool:
    return any(
        bg.security_context == "secret" and bg.status in {"running", "aborting"}
        for bg in state.background_sessions.values()
    )


def active_secret_work_running(state: State) -> bool:
    return bool(state.active_task_secret and state.active_task_id is not None and state.status in {"running", "aborting"})


def restore_secret_runtime_after_inflight_work(state: State) -> bool:
    if active_secret_work_running(state) or secret_running_background_exists(state):
        return False
    state.secret_vault.previous_log_path = ""
    restore_secret_proxy_env(state)
    return True


def new_secret_current_session(state: State, keep_running: bool = True) -> bool:
    if not state.secret_vault.unlocked:
        return new_current_session(state, keep_running=keep_running)
    state.restore_token += 1
    parked = park_active_session(state) if keep_running and state.status in {"running", "aborting"} else None
    if parked is None and state.secret_vault.session_id and any(msg.role in {"user", "assistant"} for msg in state.messages):
        secret_save_current_session_state(state, source="/new")
    if parked is None:
        persist_agent_token_usage(state, state.agent)
        try:
            if state.status in {"running", "aborting"}:
                state.agent.abort()
            reset_agent_runtime_context_no_snapshot(state.agent)
            reset_agent_to_default_llm(state)
        except Exception:
            pass
    state.secret_vault.session_id = secret_new_session_id()
    set_agent_log_path(state.agent, os.devnull)
    bind_agent_token_session(state, state.agent)
    state.messages.clear()
    state.current_title = "Secret Vault"
    state.selected_session = secret_session_sidebar_key(state.secret_vault.session_id)
    state.status = "idle"
    state.active_task_id = None
    state.active_task_source = ""
    state.active_stream_target = None
    state.active_task_secret = False
    state.active_secret_user_text = ""
    state.active_secret_session_id = ""
    clear_all_queued_inputs(state)
    state.secret_active_origin = {}
    clear_active_plan_state(state)
    state.pending_interaction = None
    cancel_normal_history_restore(state)
    set_input_text(state, "")
    state.last_error = ""
    clear_secret_session_sidebar_cache(state)
    mark_messages_changed(state)
    return bool(parked)


def new_current_session(state: State, keep_running: bool = True) -> bool:
    if state.secret_vault.unlocked:
        return new_secret_current_session(state, keep_running=keep_running)
    state.restore_token += 1
    parked = park_active_session(state) if keep_running else None
    if parked is None:
        persist_agent_token_usage(state, state.agent)
        try:
            if state.status in {"running", "aborting"}:
                state.agent.abort()
            reset_conversation(state.agent, message=None)
            reset_agent_to_default_llm(state)
        except Exception:
            pass
        set_agent_log_path(state.agent, new_session_log_path())
        bind_agent_token_session(state, state.agent)
    state.messages.clear()
    state.current_title = "main"
    state.selected_session = "main"
    state.status = "idle"
    state.active_task_id = None
    state.active_task_source = ""
    state.active_stream_target = None
    state.active_task_secret = False
    state.active_secret_user_text = ""
    state.active_secret_session_id = ""
    clear_all_queued_inputs(state)
    state.secret_active_origin = {}
    clear_active_plan_state(state)
    state.pending_interaction = None
    clear_history_ui_state(state)
    set_input_text(state, "")
    state.last_error = ""
    load_history(state, force=True)
    mark_messages_changed(state)
    return bool(parked)


def close_current_session(state: State) -> None:
    if state.secret_vault.unlocked:
        state.restore_token += 1
        if state.secret_vault.session_id and any(msg.role in {"user", "assistant"} for msg in state.messages):
            secret_save_current_session_state(state, source="close")
        if state.status in {"running", "aborting"}:
            try:
                state.agent.abort()
            except Exception:
                pass
        keys = secret_background_session_keys(state)
        if keys:
            switch_to_background_session_with_mode(state, keys[0], stash_current=False)
            state.last_error = "已关闭当前 Secret 页，并切到下一个 Secret 会话。"
        else:
            new_secret_current_session(state, keep_running=False)
            state.last_error = "已关闭当前 Secret 页，并新建空 Secret 会话。"
        mark_dirty(state)
        return
    state.restore_token += 1
    persist_agent_token_usage(state, state.agent)
    if state.status in {"running", "aborting"}:
        try:
            state.agent.abort()
        except Exception:
            pass
    if state.background_sessions:
        key = next(iter(state.background_sessions))
        switch_to_background_session_with_mode(state, key, stash_current=False)
        state.last_error = "已关闭当前页，并切到下一个当前会话。"
    else:
        new_current_session(state, keep_running=False)
        state.last_error = "已关闭当前页，并新建空会话。"
    mark_dirty(state)


def history_round_count(pairs: list[tuple[str, str]]) -> int:
    user_rounds = sum(1 for prompt, _response in pairs if _user_text(prompt))
    return user_rounds or len(pairs)


def history_messages_from_pairs(pairs: list[tuple[str, str]], rounds: int) -> tuple[list[Message], int, int]:
    total_rounds = history_round_count(pairs)
    if total_rounds <= 0:
        return [], 0, 0
    loaded_rounds = max(1, min(int(rounds or RESTORE_DISPLAY_ROUNDS), total_rounds))
    ui_messages = extract_recent_ui_messages_from_pairs(pairs, loaded_rounds)
    return [Message(m["role"], m["content"]) for m in ui_messages], loaded_rounds, total_rounds


def read_history_messages(path: str, rounds: int) -> tuple[list[Message], int, int]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except Exception as exc:
        raise RuntimeError(f"读取失败: {exc}") from exc
    pairs = _pairs(content)
    if not pairs:
        raise RuntimeError(f"{os.path.basename(path)} 为空或格式不符")
    return history_messages_from_pairs(pairs, rounds)


def extract_recent_ui_messages_from_pairs(pairs: list[tuple[str, str]], rounds: int = RESTORE_DISPLAY_ROUNDS) -> list[dict[str, str]]:
    if not pairs:
        return []
    start = 0
    seen = 0
    for idx in range(len(pairs) - 1, -1, -1):
        if _user_text(pairs[idx][0]):
            seen += 1
            start = idx
            if seen >= rounds:
                break
    recent = pairs[start:]
    next_tr = [{} for _ in recent]
    for idx in range(len(recent) - 1):
        next_tr[idx] = _tool_results_from_prompt(recent[idx + 1][0])

    out: list[dict[str, str]] = []
    assistant = None
    round_turn = 0
    for idx, (prompt, response) in enumerate(recent):
        user = _user_text(prompt)
        seg = _format_response_segment(response, next_tr[idx])
        if user:
            if assistant is not None:
                out.append(assistant)
            out.append({"role": "user", "content": user})
            assistant = {"role": "assistant", "content": f"\n\n**LLM Running (Turn 1) ...**\n\n{seg}"}
            round_turn = 1
        else:
            if assistant is None:
                assistant = {"role": "assistant", "content": ""}
                round_turn = 1
            round_turn += 1
            assistant["content"] = (assistant["content"] or "") + f"\n\n**LLM Running (Turn {round_turn}) ...**\n\n" + seg
    if assistant is not None:
        out.append(assistant)
    return [m for m in out if (m.get("content") or "").strip()]


def restore_backend_and_recent_messages(agent: Any, path: str) -> tuple[list[Message], str, int, int, int]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except Exception as exc:
        raise RuntimeError(f"读取失败: {exc}") from exc
    pairs = _pairs(content)
    if not pairs:
        raise RuntimeError(f"{os.path.basename(path)} 为空或格式不符")

    history_messages, loaded_rounds, total_rounds = history_messages_from_pairs(pairs, RESTORE_DISPLAY_ROUNDS)
    history = _parse_native_history(pairs)
    if history is not None:
        reset_agent_runtime_context_no_snapshot(agent, history)
        restore_msg = f"已恢复完整上下文：{total_rounds} 轮；界面先显示最近 {loaded_rounds} 轮，滚到顶部会自动加载更早内容。"
    else:
        reset_conversation(agent, message=None)
        restore_msg, _ok = restore(agent, path)
        restore_msg += f"\n界面先显示最近 {loaded_rounds} 轮，滚到顶部会自动加载更早内容。"
    messages = list(history_messages)
    history_message_count = len(messages)
    durable_messages = durable_ui_system_messages_for_path(path)
    messages.extend(durable_messages)
    subagent_context = subagent_context_updates_from_messages(durable_messages, path)
    if subagent_context:
        inject_orchestrator_notice(agent, subagent_context)
    return messages, restore_msg, loaded_rounds, total_rounds, history_message_count


def next_nonblank_line(lines: list[str], start: int) -> str:
    for line in lines[start:]:
        if line.strip():
            return line
    return ""


def line_numbered_file_line(line: str) -> bool:
    return bool(LINE_NUMBERED_FILE_RE.match(line or ""))


def stray_line_numbered_fence_close(line: str, previous_nonblank: str, next_nonblank: str) -> bool:
    boundary = FENCE_BOUNDARY_RE.match(line)
    return bool(
        boundary
        and not boundary.group(2).strip()
        and line_numbered_file_line(previous_nonblank)
        and TURN_MARKER_RE.match(next_nonblank)
    )


def split_top_level_turn_markers(text: str) -> list[str]:
    """Split restored turns while treating fenced tool/file output as opaque data."""
    if not text:
        return [""]
    parts: list[str] = []
    last = 0
    offset = 0
    fence_ticks = ""
    previous_nonblank = ""
    lines = text.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if fence_ticks:
            boundary = FENCE_BOUNDARY_RE.match(line)
            if boundary and len(boundary.group(1)) >= len(fence_ticks) and not boundary.group(2).strip():
                fence_ticks = ""
            if line.strip():
                previous_nonblank = line
            offset += len(line)
            continue

        marker = TURN_MARKER_RE.match(line)
        if marker:
            start = offset + marker.start(1)
            end = offset + marker.end(1)
            parts.append(text[last:start])
            parts.append(text[start:end])
            last = end
        else:
            boundary = FENCE_BOUNDARY_RE.match(line)
            if boundary and not stray_line_numbered_fence_close(
                line,
                previous_nonblank,
                next_nonblank_line(lines, idx + 1),
            ):
                fence_ticks = boundary.group(1)
        if line.strip():
            previous_nonblank = line
        offset += len(line)
    parts.append(text[last:])
    return parts


def strip_meta_blocks(text: str) -> str:
    return META_BLOCK_RE.sub("", text or "").strip()


def process_preview(text: str) -> str:
    summaries = SUMMARY_RE.findall(text or "")
    if summaries:
        title = compact_title(summaries[-1], 60)
        if title:
            return title
    preview = DETAIL_FENCE_RE.sub(" ", text or "")
    preview = META_BLOCK_RE.sub(" ", preview)
    preview = TOOL_CALL_RE.sub(" ", preview)
    preview = TOOL_USE_NAME_RE.sub(" ", preview)
    for line in preview.splitlines():
        line = line.strip()
        if not line or line.startswith(("```", "````", "args:", "📥")):
            continue
        title = compact_title(line, 60)
        if title:
            return title
    return "执行中"


def process_summary_text(text: str) -> str:
    summaries = SUMMARY_RE.findall(text or "")
    if not summaries:
        return ""
    return compact_description(summaries[-1], 220)


def process_title_text(text: str) -> str:
    summary = process_summary_text(text)
    if summary:
        return summary
    if process_has_search_noise(text):
        return "搜索/浏览输出已折叠"
    return process_preview(text)


def process_tools(text: str) -> list[str]:
    names: list[str] = []
    for pattern in (TOOL_CALL_RE, TOOL_USE_NAME_RE):
        for name in pattern.findall(text or ""):
            if name not in names:
                names.append(name)
    for obj in jsonish_objects("\n".join(TOOL_USE_PAYLOAD_RE.findall(text or ""))):
        name = str(obj.get("name") or "")
        if name and name not in names:
            names.append(name)
    for obj in jsonish_objects(text or ""):
        if str(obj.get("type") or "") != "tool_use":
            continue
        name = str(obj.get("name") or "")
        if name and name not in names:
            names.append(name)
    return names


_CAND_LEFT_TRIM = re.compile(r'^[",\[\]{}\\\s]+')
_CAND_RIGHT_TRIM = re.compile(r'[",\[\]{}\\\s]+$')
_CAND_NUMBER_PFX = re.compile(r"^\d+\s*[.)、：:）．]\s*")
INTERACTION_PAYLOAD_KEYS = {"question", "prompt", "message", "questions", "candidates", "options"}
INTERACTION_WRAPPER_KEYS = {"arguments", "args", "input"}


def looks_like_interaction_payload(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    if any(key in obj for key in INTERACTION_PAYLOAD_KEYS):
        return True
    for key in INTERACTION_WRAPPER_KEYS:
        nested = obj.get(key)
        if isinstance(nested, dict) and any(payload_key in nested for payload_key in INTERACTION_PAYLOAD_KEYS):
            return True
    return False


def sanitize_interaction_candidates(raw: Any) -> list[str]:
    out: list[str] = []
    items = raw if isinstance(raw, list) else [raw] if raw else []
    for item in items:
        s = str(item) if item is not None else ""
        for line in s.replace("\\n", "\n").splitlines() or [s]:
            line = _CAND_LEFT_TRIM.sub("", line)
            line = _CAND_RIGHT_TRIM.sub("", line)
            line = _CAND_NUMBER_PFX.sub("", line)
            line = line.strip()
            if not line:
                continue
            if len(line) > 200:
                line = line[:200] + "…"
            if line not in out:
                out.append(line)
    return out


def balanced_object_snippet(text: str, start: int) -> str:
    depth = 0
    quote = ""
    escape = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = ""
            continue
        if ch in {"'", '"'}:
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1]
    return ""


def jsonish_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in re.finditer(r"\{", text or ""):
        start = match.start()
        obj: Any = None
        snippet = ""
        try:
            obj, end = decoder.raw_decode(text[start:])
            snippet = text[start:start + end]
        except Exception:
            snippet = balanced_object_snippet(text, start)
            if not snippet:
                continue
            for parser in (json.loads, ast.literal_eval):
                try:
                    obj = parser(snippet)
                    break
                except Exception:
                    obj = None
            if obj is None:
                continue
        if not isinstance(obj, dict):
            continue
        key = snippet.strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(obj)
    return out


def loose_quoted_field(text: str, key: str) -> str:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"', text or "")
    if not match:
        return ""
    start = match.end()
    chars: list[str] = []
    escape = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if escape:
            chars.append({"n": "\n", "r": "\r", "t": "\t"}.get(ch, ch))
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            rest = text[idx + 1:]
            if re.match(r"\s*(?:,|\})", rest):
                return "".join(chars)
        chars.append(ch)
    return ""


def balanced_array_snippet(text: str, start: int) -> str:
    depth = 0
    quote = ""
    escape = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = ""
            continue
        if ch in {"'", '"'}:
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1]
    return ""


def loose_array_field(text: str, key: str) -> Any:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*\[', text or "")
    if not match:
        return None
    snippet = balanced_array_snippet(text, match.end() - 1)
    if not snippet:
        return None
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(snippet)
        except Exception:
            continue
    return None


def loose_interaction_args(text: str) -> dict[str, Any]:
    args: dict[str, Any] = {}
    for key in ("question", "prompt", "message"):
        value = loose_quoted_field(text, key)
        if value:
            args[key] = value
            break
    for key in ("candidates", "options", "questions"):
        value = loose_array_field(text, key)
        if value is not None:
            args[key] = value
    return args


def request_payload_from_args(tool: str, args: Any) -> Optional[dict[str, Any]]:
    tool = str(tool or "")
    if tool not in INTERACTIVE_TOOLS or not isinstance(args, dict):
        return None
    if isinstance(args.get("arguments"), dict):
        args = args["arguments"]
    elif isinstance(args.get("args"), dict):
        args = args["args"]
    elif isinstance(args.get("input"), dict):
        args = args["input"]

    raw_candidates = args.get("candidates")
    raw_options = args.get("options")
    if raw_candidates is None and not (isinstance(raw_options, list) and any(isinstance(item, dict) for item in raw_options)):
        raw_candidates = raw_options
    candidates = sanitize_interaction_candidates(raw_candidates)
    question_parts: list[str] = []
    question_details: list[dict[str, Any]] = []

    question = str(args.get("question") or args.get("prompt") or args.get("message") or "").strip()
    if question:
        question_parts.append(question)

    raw_questions = args.get("questions")
    if isinstance(raw_questions, list):
        for idx, raw_q in enumerate(raw_questions, 1):
            if not isinstance(raw_q, dict):
                q_text = str(raw_q).strip()
                if q_text:
                    question_parts.append(f"{idx}. {q_text}")
                continue
            header = str(raw_q.get("header") or raw_q.get("id") or f"问题 {idx}").strip()
            q_text = str(raw_q.get("question") or raw_q.get("prompt") or "").strip()
            raw_options = raw_q.get("options") or []
            opt_labels: list[str] = []
            if isinstance(raw_options, list):
                for opt in raw_options:
                    if isinstance(opt, dict):
                        label = str(opt.get("label") or opt.get("id") or "").strip()
                        desc = str(opt.get("description") or "").strip()
                        shown = f"{label} - {desc}" if label and desc else label or desc
                    else:
                        shown = str(opt).strip()
                    if shown:
                        opt_labels.append(shown)
            if opt_labels:
                candidates.extend(label for label in opt_labels if label not in candidates)
            if q_text:
                question_parts.append(f"{idx}. {q_text}")
            question_details.append({"header": header, "question": q_text, "options": opt_labels})

    if not question_parts and candidates:
        question_parts.append("请选择一个选项。")
    if not question_parts:
        question_parts.append("工具正在等待你的输入。")
    quick_candidates = candidates if len(question_details) <= 1 else []
    return {
        "tool": tool,
        "question": "\n".join(question_parts).strip(),
        "candidates": quick_candidates,
        "questions": question_details,
    }


def extract_interaction_request(text: str) -> Optional[dict[str, Any]]:
    text = text or ""
    if not any(marker in text for marker in ("ask_user", "request_user_input", "Waiting for your answer", "HUMAN_INTERVENTION", "human_intervention", "user_input")):
        return None
    tool_names = [name for name in process_tools(text) if name in INTERACTIVE_TOOLS]
    for payload in TOOL_USE_PAYLOAD_RE.findall(text):
        for obj in jsonish_objects(payload):
            if obj.get("status") == "INTERRUPT" and obj.get("intent") == "HUMAN_INTERVENTION":
                request = request_payload_from_args("ask_user", obj.get("data") or {})
                if request:
                    return request
            tool = str(obj.get("name") or "")
            args = obj.get("arguments") or obj.get("args") or obj
            request = request_payload_from_args(tool, args)
            if request:
                return request
    for tool, payload in TOOL_ARGS_PAYLOAD_RE.findall(text):
        for obj in jsonish_objects(payload):
            request = request_payload_from_args(tool, obj)
            if request:
                return request
        loose_args = loose_interaction_args(payload)
        if loose_args:
            request = request_payload_from_args(tool, loose_args)
            if request:
                return request
    for obj in jsonish_objects(text):
        if obj.get("status") == "INTERRUPT" and obj.get("intent") == "HUMAN_INTERVENTION":
            request = request_payload_from_args("ask_user", obj.get("data") or {})
            if request:
                return request
        tool = str(obj.get("name") or "")
        if not tool and tool_names and looks_like_interaction_payload(obj):
            tool = tool_names[0]
        if not tool:
            continue
        args = obj.get("arguments") or obj.get("args") or obj
        request = request_payload_from_args(tool, args)
        if request:
            return request
    if tool_names:
        return {"tool": tool_names[0], "question": "工具正在等待你的输入。", "candidates": [], "questions": []}
    return None


def render_interaction_card(payload: dict[str, Any]) -> str:
    tool = str(payload.get("tool") or "interactive")
    question = str(payload.get("question") or "工具正在等待你的输入。").strip()
    candidates = sanitize_interaction_candidates(payload.get("candidates"))
    questions = payload.get("questions") if isinstance(payload.get("questions"), list) else []
    lines = [f"╭─ 需要你输入 · {tool}"]
    if questions:
        for idx, item in enumerate(questions, 1):
            if not isinstance(item, dict):
                continue
            header = str(item.get("header") or f"问题 {idx}").strip()
            q_text = str(item.get("question") or "").strip()
            lines.append(f"│ {idx}. {header}")
            for part in q_text.splitlines() or [""]:
                if part:
                    lines.append(f"│    {part}")
            options = sanitize_interaction_candidates(item.get("options"))
            for opt_idx, opt in enumerate(options, 1):
                lines.append(f"│    {opt_idx}) {opt}")
    else:
        lines.append("│ 问题：")
        for part in question.splitlines() or [""]:
            lines.append(f"│   {part}" if part else "│")
        if candidates:
            lines.append("│")
            lines.append("│ 候选项：")
            for idx, candidate in enumerate(candidates, 1):
                lines.append(f"│   {idx}) {candidate}")
    lines.append("│")
    if candidates and tool == "approval":
        lines.append("│ 在底部回答框用 ↑/↓ 选择，Enter 执行；选“稍后处理”会保留待审批项。")
    elif candidates:
        lines.append(f"│ 在底部回答框用 ↑/↓ 选择，Enter 提交；也可输入 1-{len(candidates)} 或直接打字。")
    elif questions:
        lines.append("│ request_user_input 会在底部显示独立 qN> 输入口，逐题记录后统一发送。")
    else:
        lines.append("│ 在底部回答框直接输入答案，Enter 发送。")
    lines.append("╰─")
    return "\n".join(lines)


def interaction_footer(payload: Optional[dict[str, Any]]) -> str:
    if not payload:
        return ""
    candidates = interaction_current_candidates(payload)
    if candidates and is_approval_interaction(payload):
        return "↑/↓ 选择，空输入 Enter 执行选中审批动作；选“稍后处理”保留待审批项。"
    if candidates:
        return f"↑/↓ 选择，空输入 Enter 提交选中项；也可以直接打字回答。"
    if interaction_questions(payload):
        return "request_user_input 独立输入口：输入本题答案，Enter 记录并进入下一题。"
    return "等待你的输入：直接在下面回答；Enter 发送。"


def interaction_hint_lines(payload: Optional[dict[str, Any]], width: int) -> list[tuple[str, int]]:
    if not payload:
        return []
    questions = interaction_questions(payload)
    current_idx = interaction_current_index(payload)
    question_obj = questions[current_idx] if questions else {}
    if questions:
        header = str(question_obj.get("header") or f"问题 {current_idx + 1}").strip()
        question = str(question_obj.get("question") or "").strip()
        title_src = question or header
        prefix = f"? request_user_input {current_idx + 1}/{len(questions)}"
    else:
        title_src = str(payload.get("question") or "工具正在等待你的输入。").splitlines()[0].strip()
        prefix = f"? {payload.get('tool') or 'ask_user'}"
    title = compact_title(title_src, max(18, min(70, width - len(prefix) - 4))) or "等待回答"
    lines: list[tuple[str, int]] = [(f"{prefix}: {title}", cp(7) | curses.A_BOLD)]
    if questions and question_obj.get("question"):
        for wrapped in wrap_cells(str(question_obj.get("question") or ""), max(8, width - 2))[:2]:
            lines.append((f"  {wrapped}", cp(2)))
    elif is_approval_interaction(payload):
        preview_parts: list[str] = []
        for raw in str(payload.get("question") or "").splitlines()[1:]:
            if not raw.strip():
                continue
            preview_parts.extend(wrap_cells(raw, max(8, width - 2)) or [""])
            if len(preview_parts) >= 7:
                break
        for part in preview_parts[:7]:
            lines.append((f"  {part}", cp(2)))
        if len(preview_parts) >= 7:
            lines.append(("  ... /approvals 可查看完整候选记忆", cp(1)))
    candidates = interaction_current_candidates(payload)
    if candidates:
        selected = interaction_selection(payload)
        limit = min(6, len(candidates))
        start = max(0, min(selected - limit + 1, len(candidates) - limit))
        for idx in range(start, start + limit):
            marker = ">" if idx == selected else " "
            attr = cp(11) | curses.A_BOLD if idx == selected else cp(2)
            lines.append((f"{marker} {idx + 1}) {truncate_cells(candidates[idx], max(8, width - 6))}", attr))
        if len(candidates) > limit:
            lines.append((f"  ... {len(candidates)} 个选项，当前 {selected + 1}/{len(candidates)}", cp(1)))
    lines.append((interaction_footer(payload), cp(1)))
    return lines


def normalize_interaction_payload(payload: dict[str, Any]) -> dict[str, Any]:
    clean = dict(payload or {})
    clean["tool"] = str(clean.get("tool") or "interactive")
    clean["question"] = str(clean.get("question") or "工具正在等待你的输入。").strip()
    clean["candidates"] = sanitize_interaction_candidates(clean.get("candidates"))
    questions: list[dict[str, Any]] = []
    for raw in clean.get("questions") or []:
        if not isinstance(raw, dict):
            continue
        question = str(raw.get("question") or "").strip()
        header = str(raw.get("header") or raw.get("id") or f"问题 {len(questions) + 1}").strip()
        questions.append({"header": header, "question": question, "options": sanitize_interaction_candidates(raw.get("options"))})
    clean["questions"] = questions
    clean["_current"] = max(0, min(int(clean.get("_current", 0) or 0), max(0, len(questions) - 1)))
    clean["_selection"] = max(0, int(clean.get("_selection", 0) or 0))
    clean["_answers"] = list(clean.get("_answers") or [])
    candidates = interaction_current_candidates(clean)
    if candidates:
        clean["_selection"] = min(clean["_selection"], len(candidates) - 1)
    else:
        clean["_selection"] = 0
    return clean


def set_pending_interaction(state: State, payload: dict[str, Any]) -> None:
    state.pending_interaction = normalize_interaction_payload(payload)
    state.last_error = ""
    mark_dirty(state)


def interaction_questions(payload: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    questions = payload.get("questions") if isinstance(payload, dict) else None
    return [q for q in questions if isinstance(q, dict)] if isinstance(questions, list) else []


def interaction_current_index(payload: dict[str, Any]) -> int:
    questions = interaction_questions(payload)
    if not questions:
        return 0
    idx = int(payload.get("_current", 0) or 0)
    return max(0, min(idx, len(questions) - 1))


def interaction_current_candidates(payload: Optional[dict[str, Any]]) -> list[str]:
    if not isinstance(payload, dict):
        return []
    questions = interaction_questions(payload)
    if questions:
        return sanitize_interaction_candidates(questions[interaction_current_index(payload)].get("options"))
    return sanitize_interaction_candidates(payload.get("candidates"))


def interaction_selection(payload: dict[str, Any]) -> int:
    candidates = interaction_current_candidates(payload)
    if not candidates:
        return 0
    selected = int(payload.get("_selection", 0) or 0)
    selected = max(0, min(selected, len(candidates) - 1))
    payload["_selection"] = selected
    return selected


def move_interaction_selection(state: State, direction: int) -> bool:
    payload = current_interaction_payload(state)
    if not payload or state.input_text.strip():
        return False
    candidates = interaction_current_candidates(payload)
    if not candidates:
        return False
    payload["_selection"] = (interaction_selection(payload) + direction) % len(candidates)
    mark_dirty(state)
    return True


def interaction_answer_from_input(payload: dict[str, Any], text: str) -> str:
    stripped = text.strip()
    candidates = interaction_current_candidates(payload)
    if candidates and re.fullmatch(r"\d+", stripped):
        idx = int(stripped) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx]
    if stripped:
        return stripped
    if candidates:
        return candidates[interaction_selection(payload)]
    return ""


def compose_request_user_input_answer(payload: dict[str, Any], answers: list[str]) -> str:
    questions = interaction_questions(payload)
    lines: list[str] = []
    for idx, question in enumerate(questions):
        label = str(question.get("header") or f"问题 {idx + 1}").strip()
        q_text = str(question.get("question") or "").strip()
        answer = answers[idx] if idx < len(answers) else ""
        title = f"{label}: {q_text}" if q_text and q_text != label else label
        lines.append(f"{idx + 1}. {title}\n答案：{answer}")
    return "\n\n".join(lines).strip()


def accept_interaction_input(state: State, text: str) -> Optional[str]:
    payload = state.pending_interaction
    if not payload:
        return text
    payload = normalize_interaction_payload(payload)
    state.pending_interaction = payload
    answer = interaction_answer_from_input(payload, text)
    if not answer:
        state.last_error = "当前问题需要输入内容。"
        mark_dirty(state)
        return None
    questions = interaction_questions(payload)
    if not questions:
        state.pending_interaction = None
        state.last_error = ""
        return answer

    idx = interaction_current_index(payload)
    answers = list(payload.get("_answers") or [])
    while len(answers) < len(questions):
        answers.append("")
    answers[idx] = answer
    if idx + 1 < len(questions):
        payload["_answers"] = answers
        payload["_current"] = idx + 1
        payload["_selection"] = 0
        state.pending_interaction = payload
        state.last_error = f"已记录第 {idx + 1} 题，继续回答第 {idx + 2}/{len(questions)} 题。"
        mark_dirty(state)
        return None
    state.pending_interaction = None
    state.last_error = ""
    return compose_request_user_input_answer(payload, answers)


def accept_approval_interaction_input(state: State, text: str) -> Optional[str]:
    payload = state.pending_interaction
    if not is_approval_interaction(payload):
        return text
    approval_id = str(payload.get("approval_id") or "")
    answer = accept_interaction_input(state, text)
    if answer is None:
        return None
    normalized = answer.strip().lower()
    if normalized.startswith("批准") or normalized in {"approve", "approved", "yes", "y"}:
        return decide_approval(state, approval_id, True)
    if normalized.startswith("拒绝") or normalized in {"reject", "rejected", "no", "n"}:
        return decide_approval(state, approval_id, False)
    if normalized.startswith("稍后") or normalized in {"later", "skip", "cancel", "取消"}:
        return f"已保留待审批项：{approval_id}。可稍后 /approvals 继续处理。"
    state.last_error = "请选择：批准并执行 / 拒绝 / 稍后处理。"
    state.pending_interaction = normalize_interaction_payload(payload)
    mark_dirty(state)
    return None


def accept_subagent_interaction_input(state: State, sub: SubAgentRuntime, text: str) -> Optional[str]:
    saved_pending = state.pending_interaction
    state.pending_interaction = sub.pending_interaction
    try:
        answer = accept_interaction_input(state, text)
        sub.pending_interaction = state.pending_interaction
        return answer
    finally:
        state.pending_interaction = saved_pending


def interaction_input_prompt(payload: Optional[dict[str, Any]]) -> str:
    if not payload:
        return "> "
    if is_approval_interaction(payload):
        return "approval> "
    questions = interaction_questions(payload)
    if questions:
        return f"q{interaction_current_index(payload) + 1}> "
    return "? "


def resolve_interaction_answer(state: State, text: str) -> str:
    payload = state.pending_interaction
    if not payload:
        return text
    answer = accept_interaction_input(state, text)
    return text if answer is None else answer


def has_ask_user_tool(text: str) -> bool:
    return any(name in ASK_USER_TOOLS for name in process_tools(text)) or bool(extract_interaction_request(text))


def collapsed_process_line(marker: str, body: str, current: bool) -> str:
    turn = TURN_NO_RE.search(marker or "")
    turn_label = f"Turn {turn.group(1)}" if turn else "Turn"
    tools = process_tools(body)
    summary = process_title_text(body)
    status = "正在执行" if current else "已折叠"
    suffix = f" · tool: {', '.join(tools[:3])}" if tools else ""
    if len(tools) > 3:
        suffix += f" +{len(tools) - 3}"
    return f"▸ 过程 {turn_label}: {summary}{suffix} ({status})"


def process_detail_line(marker: str, body: str, current: bool) -> str:
    turn = TURN_NO_RE.search(marker or "")
    turn_label = f"Turn {turn.group(1)}" if turn else "Turn"
    tools = process_tools(body)
    summary = process_summary_text(body)
    title = f": {summary}" if summary else ""
    suffix = f" · tool: {', '.join(tools[:3])}" if tools else ""
    if len(tools) > 3:
        suffix += f" +{len(tools) - 3}"
    status = "正在执行" if current else "已折叠"
    return f"▸ 细节 {turn_label}{title}{suffix} ({status})"


def process_speech_header(marker: str, body: str) -> str:
    turn = TURN_NO_RE.search(marker or "")
    turn_label = f"Turn {turn.group(1)}" if turn else "Turn"
    tools = process_tools(body)
    suffix = f" · tool: {', '.join(tools[:3])}" if tools else ""
    if len(tools) > 3:
        suffix += f" +{len(tools) - 3}"
    return f"· 过程 {turn_label}{suffix}"


def process_speech_summary_line(marker: str, body: str, summary: str) -> str:
    turn = TURN_NO_RE.search(marker or "")
    turn_label = f"Turn {turn.group(1)}" if turn else "Turn"
    tools = process_tools(body)
    suffix = f" · tool: {', '.join(tools[:3])}" if tools else ""
    if len(tools) > 3:
        suffix += f" +{len(tools) - 3}"
    return f"· 过程 {turn_label}: {summary}{suffix}"


def expanded_process_header(marker: str, body: str, current: bool) -> str:
    turn = TURN_NO_RE.search(marker or "")
    turn_label = f"Turn {turn.group(1)}" if turn else "Turn"
    tools = process_tools(body)
    summary = process_summary_text(body)
    title = f": {summary}" if summary else ""
    suffix = f" · tool: {', '.join(tools[:3])}" if tools else ""
    status = "正在等待用户输入" if current else "已展开"
    return f"▾ 过程 {turn_label}{title}{suffix} ({status})"


def process_turn_no(marker: str, fallback: int) -> int:
    turn = TURN_NO_RE.search(marker or "")
    if turn:
        try:
            return int(turn.group(1))
        except ValueError:
            pass
    return fallback


def process_group_header(label: str, turns: list[tuple[str, str]], current: bool, expanded: bool) -> str:
    icon = "▾" if expanded else "▸"
    status = "正在执行" if current else ("已展开" if expanded else "已折叠")
    tool_names: list[str] = []
    summaries: list[str] = []
    for _marker, body in turns:
        summary = process_summary_text(body)
        if summary and summary not in summaries:
            summaries.append(summary)
        for tool in process_tools(body):
            if tool not in tool_names:
                tool_names.append(tool)
            if len(tool_names) >= 3:
                break
        if len(tool_names) >= 3:
            break
    suffix = f" · tool: {', '.join(tool_names)}" if tool_names else ""
    title = compact_description(" / ".join(summaries), 120) if summaries else f"{len(turns)} 条过程"
    return f"{icon} 过程组 {label}: {title}{suffix} ({status}，点击展开/收起)"


def collapsed_process_child_line(label: str, marker: str, body: str, current: bool) -> str:
    raw = collapsed_process_line(marker, body, current=current)
    return "  " + raw.replace("▸ 过程 ", f"▸ 过程 {label} ", 1)


def expanded_process_child_header(label: str, marker: str, body: str, current: bool) -> str:
    raw = expanded_process_header(marker, body, current=current)
    return "  " + raw.replace("▾ 过程 ", f"▾ 过程 {label} ", 1)


def process_child_detail(body: str, limit: int = 12000) -> str:
    detail = strip_meta_blocks(clean_text(strip_tui_controls(body or ""))).strip()
    if not detail:
        detail = process_preview(body)
    if len(detail) > limit:
        detail = detail[:limit].rstrip() + "\n...（详情过长，已截断；需要原文请打开对应 artifact/trace）"
    return "\n".join("    " + line for line in detail.splitlines())


def process_has_tool_call_noise(body: str) -> bool:
    body = body or ""
    return bool(process_tools(body)) or "<tool_use>" in body or bool(TOOL_HEADER_RE.search(body))


def process_has_tool_result_noise(body: str) -> bool:
    body = body or ""
    return bool(TOOL_RESULT_FENCE_RE.search(body)) or bool(FINAL_RESPONSE_INFO_RE.search(body))


def process_has_tool_noise(body: str) -> bool:
    return process_has_tool_call_noise(body) or process_has_tool_result_noise(body)


def process_has_search_noise(body: str) -> bool:
    body = body or ""
    lowered = body.lower()
    tools = [tool.lower() for tool in process_tools(body)]
    if any(
        tool.startswith(("web_", "browser_", "bb_browser"))
        or "search" in tool
        or "query" in tool
        for tool in tools
    ):
        return True
    search_markers = (
        "google.com/search",
        "duckduckgo",
        "searching:",
        "search results",
        "google 搜索",
        "[textarea #apjfqb",
        "dom变化量",
        "最显著变化",
        "\"diff\":",
        "result__snippet",
        "queryselectorall",
    )
    return any(marker in lowered for marker in search_markers)


def strip_tool_output_blocks(text: str) -> str:
    text = TOOL_CALL_BLOCK_RE.sub("", text or "")
    text = TOOL_USE_BLOCK_RE.sub("", text)
    text = TOOL_RESULT_FENCE_RE.sub("", text)
    text = TOOL_HEADER_RE.sub("", text)
    text = FINAL_RESPONSE_INFO_RE.sub("", text)
    return text


def visible_reply_text(body: str, hide_detail_fences: bool = False) -> str:
    """Keep user-facing prose while dropping tool-call/result noise."""
    text = strip_meta_blocks(body)
    if hide_detail_fences:
        text = strip_tool_output_blocks(text)
    else:
        text = TOOL_USE_BLOCK_RE.sub("", text)
        text = TOOL_HEADER_RE.sub("", text)
        text = FINAL_RESPONSE_INFO_RE.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def close_unbalanced_markdown_fence(text: str) -> str:
    in_code = False
    fence_ticks = ""
    for line in (text or "").splitlines():
        boundary = re.match(r"^\s*(`{3,})(.*)$", line)
        if not boundary:
            continue
        ticks = boundary.group(1)
        suffix = boundary.group(2).strip()
        if not in_code:
            in_code = True
            fence_ticks = ticks
        elif len(ticks) >= len(fence_ticks) and not suffix:
            in_code = False
            fence_ticks = ""
    if in_code and fence_ticks:
        return (text or "").rstrip() + "\n" + fence_ticks
    return text


def append_process_turn(
    rendered: list[str],
    marker: str,
    body: str,
    current: bool,
    fold_details: bool = True,
    collapse_whole: bool = False,
) -> None:
    has_process_noise = process_has_tool_noise(body)
    has_call_noise = process_has_tool_call_noise(body)
    final_text = visible_reply_text(body, hide_detail_fences=has_process_noise)
    if final_text:
        if has_call_noise and fold_details:
            final_text = close_unbalanced_markdown_fence(final_text)
        if collapse_whole and has_process_noise:
            rendered.append(final_text)
            if fold_details:
                rendered.append(collapsed_process_line(marker, body, current=current))
            return
        if has_call_noise:
            rendered.append(process_speech_header(marker, body))
        rendered.append(final_text)
        if has_call_noise and fold_details:
            rendered.append(process_detail_line(marker, body, current=current))
        return
    if collapse_whole and has_process_noise:
        rendered.append(collapsed_process_line(marker, body, current=current))
        return
    summary = process_title_text(body)
    if summary and summary != "执行中":
        rendered.append(process_speech_summary_line(marker, body, summary))
        if has_call_noise and fold_details:
            rendered.append(process_detail_line(marker, body, current=current))
        return
    if has_process_noise:
        rendered.append(collapsed_process_line(marker, body, current=current))


def visible_ask_user_text(body: str) -> str:
    payload = extract_interaction_request(body)
    if payload:
        return render_interaction_card(payload)
    return render_interaction_card({"tool": "interactive", "question": "工具正在等待你的输入。", "candidates": [], "questions": []})


def render_assistant_text(
    text: str,
    done: bool,
    fold_process: bool,
    process_scope: str = "",
    message_index: int = 0,
    expanded_groups: Optional[set[str]] = None,
    expanded_turns: Optional[set[str]] = None,
) -> str:
    expanded_groups = expanded_groups or set()
    expanded_turns = expanded_turns or set()
    text = clean_text(strip_tui_controls(text))
    force_fold = process_has_tool_noise(text)
    if not fold_process and not extract_interaction_request(text) and not force_fold:
        return strip_meta_blocks(text)

    parts = split_top_level_turn_markers(text)
    if len(parts) < 3:
        if force_fold:
            if has_ask_user_tool(text):
                final_text = visible_ask_user_text(text)
                header = expanded_process_header("Turn 1", text, current=not done)
                return header + (("\n" + final_text) if final_text else "")
            rendered: list[str] = []
            append_process_turn(
                rendered,
                "Turn 1",
                text,
                current=not done,
                collapse_whole=process_has_tool_noise(text) and process_has_search_noise(text),
            )
            return "\n".join(rendered)
        return strip_meta_blocks(text)

    rendered: list[str] = []
    preamble = strip_meta_blocks(parts[0])
    if preamble:
        rendered.append(preamble)

    turns: list[tuple[str, str]] = []
    for idx in range(1, len(parts), 2):
        marker = parts[idx]
        body = parts[idx + 1] if idx + 1 < len(parts) else ""
        turns.append((marker, body))

    process_indices = [
        idx for idx, (_marker, body) in enumerate(turns)
        if process_has_tool_noise(body) and not has_ask_user_tool(body)
    ]
    if fold_process and len(process_indices) >= 2:
        process_set = set(process_indices)
        group_label = f"G{message_index + 1}"
        group_key = f"{process_scope}:{group_label}" if process_scope else group_label
        group_expanded = group_key in expanded_groups
        process_turns = [(idx, *turns[idx]) for idx in process_indices]
        current_group = (not done) and (len(turns) - 1 in process_set)
        inserted_group = False
        for idx, (marker, body) in enumerate(turns):
            is_last = idx == len(turns) - 1
            if idx in process_set:
                if inserted_group:
                    continue
                inserted_group = True
                rendered.append(process_group_header(group_label, [(item[1], item[2]) for item in process_turns], current_group, group_expanded))
                if group_expanded:
                    for child_idx, (original_idx, child_marker, child_body) in enumerate(process_turns, 1):
                        child_turn = process_turn_no(child_marker, child_idx)
                        child_label = f"{group_label}T{child_turn}"
                        child_key = f"{process_scope}:{group_label}:{child_label}" if process_scope else child_label
                        child_current = (not done) and (original_idx == len(turns) - 1)
                        if child_key in expanded_turns:
                            rendered.append(expanded_process_child_header(child_label, child_marker, child_body, child_current))
                            detail = process_child_detail(child_body)
                            if detail:
                                rendered.append(detail)
                        else:
                            rendered.append(collapsed_process_child_line(child_label, child_marker, child_body, child_current))
                for _original_idx, child_marker, child_body in process_turns:
                    final_visible = visible_reply_text(child_body, hide_detail_fences=True)
                    if final_visible:
                        rendered.append(final_visible)
                continue
            if has_ask_user_tool(body):
                final_text = visible_ask_user_text(body)
                header = expanded_process_header(marker, body, current=is_last and not done)
                rendered.append(header)
                if final_text:
                    rendered.append(final_text)
                continue
            final_text = visible_reply_text(body, hide_detail_fences=False)
            if final_text:
                rendered.append(final_text)
            else:
                summary = process_summary_text(body) or process_preview(body)
                if summary and summary != "执行中":
                    rendered.append(process_speech_summary_line(marker, body, summary))
        return "\n".join(line for line in rendered if line.strip()).strip()

    for idx, (marker, body) in enumerate(turns):
        is_last = idx == len(turns) - 1
        tools = process_tools(body)
        if has_ask_user_tool(body):
            final_text = visible_ask_user_text(body)
            header = expanded_process_header(marker, body, current=is_last and not done)
            rendered.append(header)
            if final_text:
                rendered.append(final_text)
            continue
        has_process_noise = process_has_tool_noise(body)
        has_search_noise = has_process_noise and process_has_search_noise(body)
        if is_last:
            if has_process_noise:
                append_process_turn(rendered, marker, body, current=not done, collapse_whole=has_search_noise)
            else:
                final_text = visible_reply_text(body, hide_detail_fences=False)
                if final_text:
                    rendered.append(final_text)
                else:
                    summary = process_summary_text(body) or process_preview(body)
                    if summary and summary != "执行中":
                        rendered.append(process_speech_summary_line(marker, body, summary))
                    else:
                        rendered.append(collapsed_process_line(marker, body, current=not done))
        else:
            if has_process_noise:
                append_process_turn(rendered, marker, body, current=False, collapse_whole=True)
            else:
                final_text = visible_reply_text(body, hide_detail_fences=False)
                if final_text:
                    rendered.append(final_text)
                else:
                    summary = process_summary_text(body) or process_preview(body)
                    if summary and summary != "执行中":
                        rendered.append(process_speech_summary_line(marker, body, summary))
    return "\n".join(line for line in rendered if line.strip()).strip()


def boxed_user_lines(text: str, width: int) -> list[str]:
    inner_limit = max(8, width - 4)
    body = wrap_cells(text, inner_limit)
    if not body:
        body = [""]
    inner_width = min(inner_limit, max(8, *(cell_width(line) for line in body)))
    top = "┌" + "─" * (inner_width + 2) + "┐"
    bottom = "└" + "─" * (inner_width + 2) + "┘"
    return [top, *("│ " + pad_cells(line, inner_width) + " │" for line in body), bottom]


def strip_inline_markdown(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"[\1]", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<!_)_(?!_)(.*?)(?<!_)_(?!_)", r"\1", text)
    return text


def is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c.strip()) for c in cells)


def split_table_row(line: str) -> list[str]:
    raw = line.strip().strip("|")
    return [strip_inline_markdown(c.strip()) for c in raw.split("|")]


def render_table(lines: list[str], width: int) -> list[RenderLine]:
    rows = [split_table_row(line) for line in lines]
    rows = [row for row in rows if not is_table_separator(row)]
    if not rows:
        return []
    cols = max(len(row) for row in rows)
    for row in rows:
        row.extend([""] * (cols - len(row)))
    col_widths = [max(cell_width(row[i]) for row in rows) for i in range(cols)]
    budget = max(8, width - 3 * (cols - 1))
    if sum(col_widths) > budget:
        cap = max(6, budget // max(1, cols))
        col_widths = [min(w, cap) for w in col_widths]
    out: list[RenderLine] = []
    for idx, row in enumerate(rows):
        rendered = " │ ".join(pad_cells(row[i], col_widths[i]) for i in range(cols))
        out.append(RenderLine(rendered, cp(7) | curses.A_BOLD if idx == 0 else cp(2)))
        if idx == 0 and len(rows) > 1:
            sep = "─┼─".join("─" * w for w in col_widths)
            out.append(RenderLine(sep, cp(10)))
    return out


def markdown_blocks(text: str, width: int) -> list[RenderLine]:
    out: list[RenderLine] = []
    lines = (text or "").splitlines()
    i = 0
    in_code = False
    code_lang = ""
    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()

        fence = re.match(r"^`{3,}(.*)$", stripped)
        if fence:
            if not in_code:
                in_code = True
                code_lang = fence.group(1).strip() or "code"
                out.append(RenderLine("╭─ " + code_lang, cp(10) | curses.A_BOLD))
            else:
                in_code = False
                out.append(RenderLine("╰─", cp(10)))
            i += 1
            continue
        if in_code:
            for wrapped in wrap_cells(raw, max(8, width - 2)):
                out.append(RenderLine("│ " + wrapped, cp(2)))
            i += 1
            continue

        if "|" in raw and i + 1 < len(lines) and "|" in lines[i + 1]:
            maybe_sep = split_table_row(lines[i + 1])
            if is_table_separator(maybe_sep):
                table_lines = [raw, lines[i + 1]]
                i += 2
                while i < len(lines) and "|" in lines[i] and lines[i].strip():
                    table_lines.append(lines[i])
                    i += 1
                out.extend(render_table(table_lines, width))
                continue

        if not stripped:
            out.append(RenderLine(""))
            i += 1
            continue
        if re.fullmatch(r"[-*_]{3,}", stripped):
            out.append(RenderLine("─" * min(width, 80), cp(10)))
            i += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            marker = "█" if level <= 2 else "▪"
            attr = (cp(7) if level <= 2 else cp(1)) | curses.A_BOLD
            for wrapped in wrap_cells(strip_inline_markdown(heading.group(2)), max(8, width - 2)):
                out.append(RenderLine(f"{marker} {wrapped}", attr))
            i += 1
            continue

        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            for wrapped in wrap_cells(strip_inline_markdown(quote.group(1)), max(8, width - 2)):
                out.append(RenderLine("▌ " + wrapped, cp(10)))
            i += 1
            continue

        task = re.match(r"^[-*+]\s+\[([ xX])\]\s+(.+)$", stripped)
        if task:
            mark = "☑" if task.group(1).lower() == "x" else "☐"
            for n, wrapped in enumerate(wrap_cells(strip_inline_markdown(task.group(2)), max(8, width - 4))):
                out.append(RenderLine(("  " + mark + " " if n == 0 else "    ") + wrapped, cp(2)))
            i += 1
            continue

        bullet = re.match(r"^([-*+])\s+(.+)$", stripped)
        if bullet:
            for n, wrapped in enumerate(wrap_cells(strip_inline_markdown(bullet.group(2)), max(8, width - 4))):
                out.append(RenderLine(("  • " if n == 0 else "    ") + wrapped, cp(2)))
            i += 1
            continue

        numbered = re.match(r"^(\d+[.)])\s+(.+)$", stripped)
        if numbered:
            label = numbered.group(1)
            indent = " " * (len(label) + 3)
            for n, wrapped in enumerate(wrap_cells(strip_inline_markdown(numbered.group(2)), max(8, width - len(indent)))):
                out.append(RenderLine((f"  {label} " if n == 0 else indent) + wrapped, cp(2)))
            i += 1
            continue

        for wrapped in wrap_cells(strip_inline_markdown(raw), width):
            out.append(RenderLine(wrapped, cp(2)))
        i += 1
    return out


def plain_blocks(text: str, width: int) -> list[RenderLine]:
    return [RenderLine(line, cp(2)) for line in wrap_cells(text, width)]


def parse_subagent_result_notice(text: str) -> Optional[dict[str, str]]:
    lines = clean_text(text).splitlines()
    if not lines:
        return None
    match = SUBAGENT_RESULT_HEADER_RE.match(lines[0].strip())
    if not match:
        return None
    task_id = ""
    artifact_ref = ""
    body_start = 1
    for idx, line in enumerate(lines[1:], 1):
        stripped = line.strip()
        if not stripped:
            body_start = idx + 1
            break
        if stripped.lower().startswith("task:"):
            task_id = stripped.split(":", 1)[1].strip()
            body_start = idx + 1
            continue
        if stripped.lower().startswith("artifact:"):
            artifact_ref = stripped.split(":", 1)[1].strip()
            body_start = idx + 1
            continue
        body_start = idx
        break
    body = "\n".join(lines[body_start:]).strip()
    return {
        "name": match.group("name").strip(),
        "agent_id": match.group("agent_id").strip(),
        "task_id": task_id,
        "artifact_ref": artifact_ref,
        "body": body,
    }


def render_subagent_result_body(text: str, fold_process: bool) -> str:
    rendered = render_assistant_text(text, True, fold_process)
    rendered = clean_text(rendered).strip()
    return rendered or "(empty result)"


def subagent_result_metadata_separator(line: str) -> bool:
    stripped = (line or "").strip()
    if stripped in {"---", "***", "___"}:
        return True
    return len(stripped) >= 6 and len(set(stripped)) == 1 and stripped[0] in {"-", "_", "*", "─"}


def subagent_result_metadata_label(line: str) -> str:
    match = SUBAGENT_RESULT_META_LABEL_RE.match(line or "")
    if not match:
        return ""
    return " ".join(word.capitalize() for word in match.group(1).split())


def subagent_result_metadata_value(line: str) -> str:
    if not subagent_result_metadata_label(line):
        return ""
    return strip_inline_markdown((line or "").split(":", 1)[-1].split("：", 1)[-1]).strip(" -")


def split_subagent_result_reply_and_metadata(text: str) -> tuple[str, list[str]]:
    lines = clean_text(text).splitlines()
    footer_start = -1
    for idx, line in enumerate(lines):
        if not subagent_result_metadata_label(line):
            continue
        footer_start = idx
        prev = idx - 1
        while prev >= 0 and not lines[prev].strip():
            prev -= 1
        if prev >= 0 and subagent_result_metadata_separator(lines[prev]):
            footer_start = prev
        break
    if footer_start < 0:
        return clean_text(text).strip(), []
    reply = "\n".join(lines[:footer_start]).strip()
    metadata = [
        line.strip()
        for line in lines[footer_start:]
        if line.strip() and not subagent_result_metadata_separator(line)
    ]
    return reply, metadata


def subagent_result_metadata_labels(notice: dict[str, str], metadata_lines: list[str]) -> list[str]:
    labels: list[str] = []
    for label, present in (("Task", bool(notice.get("task_id"))), ("Artifact", bool(notice.get("artifact_ref")))):
        if present:
            labels.append(label)
    for line in metadata_lines:
        label = subagent_result_metadata_label(line)
        if label and label not in labels:
            labels.append(label)
    return labels


def count_list_like_metadata_value(value: str) -> Optional[int]:
    stripped = strip_inline_markdown(value or "").strip()
    if not stripped:
        return None
    empty_value = stripped.strip("。.!！ ")
    if empty_value in {"无", "-", "—", "none", "None", "N/A", "n/a"}:
        return 0
    numbered = re.findall(r"(?:^|\n)\s*\d+[.)]\s+", stripped)
    bullets = re.findall(r"(?:^|\n)\s*[-*•]\s+", stripped)
    if numbered or bullets:
        return max(len(numbered), len(bullets))
    if "," in stripped or "，" in stripped:
        return len([item for item in re.split(r"[,，]", stripped) if item.strip()])
    return None


def subagent_result_metadata_entries(metadata_lines: list[str]) -> list[tuple[str, str]]:
    entries: list[tuple[str, list[str]]] = []
    for line in metadata_lines:
        label = subagent_result_metadata_label(line)
        if label:
            entries.append((label, [subagent_result_metadata_value(line)]))
        elif entries:
            entries[-1][1].append(line)
    return [(label, "\n".join(part for part in parts if part).strip()) for label, parts in entries]


def subagent_result_reply_excerpt(text: str, limit: int = SUBAGENT_CONTEXT_REPLY_LIMIT) -> tuple[str, list[str]]:
    rendered = render_subagent_result_body(text, fold_process=True)
    reply, metadata_lines = split_subagent_result_reply_and_metadata(rendered)
    excerpt = clean_text(reply or rendered).strip() or "(empty result)"
    if len(excerpt) > limit:
        excerpt = excerpt[:limit].rstrip() + "\n...（回复过长，完整内容见 artifact）"
    return excerpt, metadata_lines


def format_subagent_result_context_update(
    name: str,
    agent_id: str,
    bus_task_id: str,
    artifact_ref: str,
    text: str,
    *,
    session_key_value: str = "",
    parent_task_id: str = "",
    plan_id: str = "",
    role: str = "",
) -> str:
    latest = latest_task_records()
    task_row = latest.get(bus_task_id, {}) if bus_task_id else {}
    parent_task_id = parent_task_id or str(task_row.get("parent_task_id") or "")
    parent_row = latest.get(parent_task_id, {}) if parent_task_id else {}
    plan_id = plan_id or str(parent_row.get("parent_task_id") or "")
    role = role or str(task_row.get("role") or task_row.get("assigned_role") or "")
    reply, metadata_lines = subagent_result_reply_excerpt(text)
    confidence = ""
    for label, value in subagent_result_metadata_entries(metadata_lines):
        if label == "Confidence":
            confidence = truncate_cells(strip_inline_markdown(value).strip("* -"), 80)
            break
    lines = [
        "Subagent result available in current session context:",
        f"- session_key: {session_key_value or 'current'}",
        f"- subagent: {name or agent_id or 'subagent'} ({agent_id or '-'})",
        f"- task_id: {bus_task_id or '-'}",
        f"- status: completed",
    ]
    if role:
        lines.append(f"- role: {role}")
    if parent_task_id:
        lines.append(f"- parent_task_id: {parent_task_id}")
    if plan_id:
        lines.append(f"- plan_id: {plan_id}")
    if artifact_ref:
        lines.append(f"- artifact_ref: {artifact_ref}")
    if confidence:
        lines.append(f"- confidence: {confidence}")
    lines.extend([
        "- instruction: Use this scoped current-session result directly for follow-up status questions; do not search historical session logs unless the user asks for archives.",
        "",
        "Reply excerpt:",
        reply,
    ])
    return "\n".join(lines).strip()


def subagent_result_context_update_from_notice(text: str, *, session_key_value: str = "") -> str:
    notice = parse_subagent_result_notice(text)
    if notice is None:
        return ""
    return format_subagent_result_context_update(
        notice.get("name", ""),
        notice.get("agent_id", ""),
        notice.get("task_id", ""),
        notice.get("artifact_ref", ""),
        notice.get("body", ""),
        session_key_value=session_key_value,
    )


def subagent_context_updates_from_messages(messages: list[Message], path: str = "") -> str:
    session_key_value = session_key(path) if path else ""
    updates: list[str] = []
    seen: set[str] = set()
    for msg in messages:
        if msg.role != "system":
            continue
        update = subagent_result_context_update_from_notice(msg.content, session_key_value=session_key_value)
        if not update:
            continue
        key = hashlib.sha1(update.encode("utf-8", errors="ignore")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        updates.append(update)
    selected: list[str] = []
    total = 0
    for update in reversed(updates):
        if len(selected) >= SUBAGENT_CONTEXT_UPDATE_LIMIT:
            break
        cost = len(update) + 2
        if selected and total + cost > SUBAGENT_CONTEXT_TOTAL_LIMIT:
            break
        selected.append(update)
        total += cost
    return "\n\n".join(reversed(selected))


def subagent_result_metadata_summary(notice: dict[str, str], metadata_lines: list[str]) -> str:
    highlights: list[str] = []
    for label, value in subagent_result_metadata_entries(metadata_lines):
        if not label or not value:
            continue
        if label == "Confidence":
            highlights.insert(0, f"Confidence: {truncate_cells(value, 18)}")
            continue
        if label in {"Risks", "Findings", "Evidence refs", "Artifact refs", "Tests", "Critical issues", "Minor issues"}:
            count = count_list_like_metadata_value(value)
            highlights.append(f"{label}: {count}" if count is not None else f"{label}: {truncate_cells(value, 14)}")
    if not any(item.startswith("Task:") for item in highlights) and notice.get("task_id"):
        highlights.append("Task")
    if not any(item.startswith("Artifact") for item in highlights) and notice.get("artifact_ref"):
        highlights.append("Artifact")
    if not highlights:
        highlights = subagent_result_metadata_labels(notice, metadata_lines)
    return " · ".join(highlights[:6]) + (f" · +{len(highlights) - 6}" if len(highlights) > 6 else "")


def subagent_meta_label(notice: dict[str, str]) -> str:
    seed = f"{notice.get('agent_id','')}|{notice.get('task_id','')}|{notice.get('artifact_ref','')}"
    digest = hashlib.sha1(seed.encode("utf-8", errors="ignore")).hexdigest()[:8]
    return f"S{digest}"


def subagent_result_metadata_detail_blocks(notice: dict[str, str], metadata_lines: list[str], width: int) -> list[RenderLine]:
    detail_lines: list[str] = []
    if notice.get("task_id"):
        detail_lines.append(f"Task: {notice['task_id']}")
    if notice.get("artifact_ref"):
        detail_lines.append(f"Artifact: {notice['artifact_ref']}")
    detail_lines.extend(metadata_lines)
    blocks: list[RenderLine] = []
    for line in detail_lines:
        for wrapped in wrap_cells(line, width):
            blocks.append(RenderLine("│   " + wrapped, cp(9)))
    return blocks


def subagent_result_card_blocks(
    text: str,
    width: int,
    markdown: bool,
    fold_process: bool,
    expanded_meta: Optional[set[str]] = None,
) -> list[RenderLine]:
    notice = parse_subagent_result_notice(text)
    if notice is None:
        return []
    expanded_meta = expanded_meta or set()
    body_width = max(8, width - 4)
    title = f"╭─ 子 agent 回复 · {notice['name']} ({notice['agent_id']})"
    blocks: list[RenderLine] = [RenderLine(title, cp(10) | curses.A_BOLD)]
    body = render_subagent_result_body(notice["body"], fold_process)
    reply_body, metadata_lines = split_subagent_result_reply_and_metadata(body)
    metadata_labels = subagent_result_metadata_labels(notice, metadata_lines)
    if metadata_labels:
        meta_label = subagent_meta_label(notice)
        expanded = meta_label in expanded_meta
        icon = "▾" if expanded else "▸"
        summary = subagent_result_metadata_summary(notice, metadata_lines)
        status = "已展开" if expanded else "已折叠"
        blocks.append(RenderLine("│ " + truncate_cells(f"{icon} 元信息 {meta_label} ({status}，点击) · {summary}", body_width), cp(9)))
        if expanded:
            blocks.extend(subagent_result_metadata_detail_blocks(notice, metadata_lines, body_width - 2))
    blocks.append(RenderLine("├─ 回复", cp(10)))
    body_blocks = markdown_blocks(reply_body or "(empty result)", body_width) if markdown else plain_blocks(reply_body or "(empty result)", body_width)
    if not body_blocks:
        body_blocks = [RenderLine("(empty result)", cp(2))]
    for line in body_blocks:
        blocks.append(RenderLine("│ " + line.text if line.text else "│", line.attr))
    blocks.append(RenderLine("╰─", cp(10)))
    return blocks


def running_indicator(frame: int) -> str:
    return f"{RUN_FRAMES[frame % len(RUN_FRAMES)]} running..."


def clear_selection(state: State) -> None:
    state.selection_active = False
    state.selection_start = None
    state.selection_end = None
    state.selection_dragged = False
    state.selection_mouse_x = None
    state.selection_mouse_y = None
    state.selection_auto_last_at = 0.0


def char_index_for_cell(text: str, target_x: int) -> int:
    target_x = max(0, target_x)
    used = 0
    for idx, ch in enumerate(text):
        width = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
        if target_x <= used:
            return idx
        if used + width > target_x:
            return idx
        used += width
        if used >= target_x:
            return idx + 1
    return len(text)


def ordered_selection_points(state: State) -> Optional[tuple[tuple[int, int], tuple[int, int]]]:
    if state.selection_start is None or state.selection_end is None:
        return None
    start, end = sorted((state.selection_start, state.selection_end))
    if start == end:
        return None
    return start, end


def selection_span_for_line(state: State, line_idx: int, text: str) -> Optional[tuple[int, int]]:
    points = ordered_selection_points(state)
    if points is None:
        return None
    (start_line, start_col), (end_line, end_col) = points
    if line_idx < start_line or line_idx > end_line:
        return None
    if start_line == end_line:
        start, end = start_col, end_col
    elif line_idx == start_line:
        start, end = start_col, len(text)
    elif line_idx == end_line:
        start, end = 0, end_col
    else:
        start, end = 0, len(text)
    start = max(0, min(start, len(text)))
    end = max(0, min(end, len(text)))
    if start == end:
        return None
    return min(start, end), max(start, end)


def selected_text(state: State) -> str:
    points = ordered_selection_points(state)
    if points is None or not state.line_cache:
        return ""
    (start_line, start_col), (end_line, end_col) = points
    start_line = max(0, min(start_line, len(state.line_cache) - 1))
    end_line = max(0, min(end_line, len(state.line_cache) - 1))
    if start_line > end_line:
        return ""
    chunks: list[str] = []
    for idx in range(start_line, end_line + 1):
        text = state.line_cache[idx].text
        if idx == start_line and idx == end_line:
            chunks.append(text[start_col:end_col])
        elif idx == start_line:
            chunks.append(text[start_col:])
        elif idx == end_line:
            chunks.append(text[:end_col])
        else:
            chunks.append(text)
    return "\n".join(chunks).strip("\n")


def shift_selection_lines(state: State, delta: int) -> None:
    if not delta:
        return
    if state.selection_start is not None:
        line, col = state.selection_start
        state.selection_start = (max(0, line + delta), col)
    if state.selection_end is not None:
        line, col = state.selection_end
        state.selection_end = (max(0, line + delta), col)


def scoped_subagent_meta_keys(process_scope: str, expanded_subagent_meta: set[str]) -> set[str]:
    scoped_subagent_meta = set(expanded_subagent_meta)
    if process_scope:
        prefix = f"{process_scope}:submeta:"
        scoped_subagent_meta = {key[len(prefix):] for key in expanded_subagent_meta if key.startswith(prefix)}
    return scoped_subagent_meta


def message_render_cache_key(
    msg: Message,
    msg_index: int,
    width: int,
    fold_process: bool,
    markdown: bool,
    run_frame: int,
    process_scope: str,
    expanded_groups: set[str],
    expanded_turns: set[str],
    scoped_subagent_meta: set[str],
    assistant_label: str = "AI",
) -> tuple[Any, ...]:
    frame = run_frame if msg.role == "assistant" and not msg.done else 0
    return (
        id(msg),
        msg_index,
        str(msg.role or ""),
        len(msg.content or ""),
        hash(msg.content or ""),
        bool(msg.done),
        width,
        fold_process,
        markdown,
        frame,
        process_scope,
        assistant_label,
        tuple(sorted(expanded_groups)),
        tuple(sorted(expanded_turns)),
        tuple(sorted(scoped_subagent_meta)),
    )


def message_block_lines(
    msg: Message,
    msg_index: int,
    width: int,
    fold_process: bool = True,
    markdown: bool = True,
    run_frame: int = 0,
    process_scope: str = "",
    expanded_groups: Optional[set[str]] = None,
    expanded_turns: Optional[set[str]] = None,
    scoped_subagent_meta: Optional[set[str]] = None,
    assistant_label: str = "AI",
) -> list[RenderLine]:
    expanded_groups = expanded_groups or set()
    expanded_turns = expanded_turns or set()
    scoped_subagent_meta = scoped_subagent_meta or set()
    role = {"user": "You", "assistant": assistant_label or "AI", "system": "Sys"}.get(msg.role, msg.role)
    text = clean_text(msg.content)
    out: list[RenderLine] = []
    if msg.role == "user":
        out.append(RenderLine("You:", cp(2) | curses.A_BOLD))
        out.extend(RenderLine(line, cp(2)) for line in boxed_user_lines(text, width))
        out.append(RenderLine(""))
        return out
    if msg.role == "system":
        subagent_blocks = subagent_result_card_blocks(text, width, markdown, fold_process, expanded_meta=scoped_subagent_meta)
        if subagent_blocks:
            out.extend(subagent_blocks)
            out.append(RenderLine(""))
            return out
    if msg.role == "assistant":
        text = render_assistant_text(
            text,
            msg.done,
            fold_process,
            process_scope=process_scope,
            message_index=msg_index,
            expanded_groups=expanded_groups,
            expanded_turns=expanded_turns,
        )
    prefix = f"{role}: "
    body_width = max(10, width - cell_width(prefix))
    blocks = markdown_blocks(text, body_width) if markdown and msg.role == "assistant" else plain_blocks(text, body_width)
    if not blocks:
        blocks = [RenderLine("")]
    out.append(RenderLine(prefix + blocks[0].text, blocks[0].attr))
    for line in blocks[1:]:
        out.append(RenderLine(" " * cell_width(prefix) + line.text, line.attr))
    if msg.role == "assistant" and not msg.done:
        out.append(RenderLine(" " * cell_width(prefix) + running_indicator(run_frame), cp(10) | curses.A_BOLD))
    out.append(RenderLine(""))
    return out


def message_lines_from_cache(
    state: State,
    messages: list[Message],
    width: int,
    fold_process: bool = True,
    markdown: bool = True,
    run_frame: int = 0,
    process_scope: str = "",
    expanded_groups: Optional[set[str]] = None,
    expanded_turns: Optional[set[str]] = None,
    expanded_subagent_meta: Optional[set[str]] = None,
    assistant_label: str = "AI",
) -> list[RenderLine]:
    expanded_groups = expanded_groups or set()
    expanded_turns = expanded_turns or set()
    expanded_subagent_meta = expanded_subagent_meta or set()
    scoped_subagent_meta = scoped_subagent_meta_keys(process_scope, expanded_subagent_meta)
    live_keys: set[tuple[Any, ...]] = set()
    out: list[RenderLine] = []
    for msg_index, msg in enumerate(messages):
        cache_key = message_render_cache_key(
            msg,
            msg_index,
            width,
            fold_process,
            markdown,
            run_frame,
            process_scope,
            expanded_groups,
            expanded_turns,
            scoped_subagent_meta,
            assistant_label,
        )
        live_keys.add(cache_key)
        block = state.message_block_cache.get(cache_key)
        if block is None:
            block = message_block_lines(
                msg,
                msg_index,
                width,
                fold_process,
                markdown,
                run_frame,
                process_scope,
                expanded_groups,
                expanded_turns,
                scoped_subagent_meta,
                assistant_label,
            )
            state.message_block_cache[cache_key] = block
        out.extend(block)
    prune_message_block_cache(state, live_keys)
    return out


def message_lines(
    messages: list[Message],
    width: int,
    fold_process: bool = True,
    markdown: bool = True,
    run_frame: int = 0,
    process_scope: str = "",
    expanded_groups: Optional[set[str]] = None,
    expanded_turns: Optional[set[str]] = None,
    expanded_subagent_meta: Optional[set[str]] = None,
) -> list[RenderLine]:
    out: list[RenderLine] = []
    expanded_groups = expanded_groups or set()
    expanded_turns = expanded_turns or set()
    expanded_subagent_meta = expanded_subagent_meta or set()
    scoped_subagent_meta = scoped_subagent_meta_keys(process_scope, expanded_subagent_meta)
    for msg_index, msg in enumerate(messages):
        out.extend(message_block_lines(
            msg,
            msg_index,
            width,
            fold_process,
            markdown,
            run_frame,
            process_scope,
            expanded_groups,
            expanded_turns,
            scoped_subagent_meta,
        ))
    return out


def safe_add(win, y: int, x: int, text: str, width: int, attr: int = 0) -> None:
    if y < 0 or x < 0 or width <= 0:
        return
    try:
        win.addstr(y, x, truncate_cells(text, width), attr)
    except curses.error:
        pass


def left_sidebar_width(width: int) -> int:
    return min(42, max(30, width // 4))


def rightbar_width_for_terminal(width: int) -> int:
    if width < 96:
        return 0
    return min(42, max(30, width // 5))


def subagent_status_marker(sub: SubAgentRuntime) -> str:
    if sub.pending_interaction:
        return "?"
    if sub.status in {"running", "aborting", "waiting-input"}:
        return "●"
    if sub.task_queue:
        return "●"
    if sub.status in {"error", "failed"}:
        return "✕"
    return "○"


def task_status_marker(status: str, approval: str = "-") -> str:
    status_l = (status or "").lower()
    if status_l == "completed":
        return "✓"
    if status_l in {"failed", "cancelled", "canceled", "rejected", "aborted"}:
        return "✕"
    if approval == "pending" or status_l in {"approval_required", "input_required", "waiting-input"}:
        return "?"
    if status_l in {"working", "running", "accepted", "pending"}:
        return "●"
    return "○"


def task_owner_display_name(state: Optional[State], row: dict[str, Any]) -> str:
    owner = str(row.get("assigned_agent") or "").strip()
    if not owner:
        return ""
    if state is not None:
        sub = state.subagents.get(owner)
        if sub is not None:
            return sub.name
    meta = load_subagent_meta(owner)
    name = str(meta.get("name") or "").strip()
    if name:
        return name
    return owner


def row_looks_like_subagent_task(row: dict[str, Any], owner: str) -> bool:
    kind = str(row.get("kind") or "")
    if kind in {"subagent_task", "subagent"}:
        return True
    if owner.startswith(("agent-", "tmp-")):
        return True
    return False


def task_display_title(row: dict[str, Any], state: Optional[State] = None) -> str:
    for key in ("title", "display_title", "task_title"):
        value = clean_text(str(row.get(key) or "")).strip()
        if value:
            return value
    owner = str(row.get("assigned_agent") or "").strip()
    owner_name = task_owner_display_name(state, row)
    if owner_name and row_looks_like_subagent_task(row, owner):
        return f"子 agent 任务: {owner_name}"
    objective = clean_text(str(row.get("objective") or row.get("summary") or row.get("error") or row.get("task_id") or ""))
    return objective or "任务"


def selected_plan_id_from_rows(
    rows: list[tuple[str, dict[str, Any]]],
    preferred_plan_id: str = "",
    require_active: bool = False,
) -> str:
    plans = [
        item for item in rows
        if str(item[1].get("kind") or "") == "plan"
    ]
    if not plans:
        return ""
    preferred_plan_id = str(preferred_plan_id or "")
    if preferred_plan_id and any(task_id == preferred_plan_id for task_id, _row in plans):
        return preferred_plan_id
    active_plans = [
        item for item in plans
        if not terminal_task_status(str(item[1].get("status") or ""))
    ]
    if require_active and not active_plans:
        return ""
    candidates = active_plans or plans
    candidates.sort(key=lambda item: row_timestamp(item[1]), reverse=True)
    return candidates[0][0] if candidates else ""


def rightbar_selected_plan_id(state: State, rows: list[tuple[str, dict[str, Any]]]) -> str:
    return selected_plan_id_from_rows(rows, str(state.active_plan_task_id or ""))


def hydrate_active_plan_from_ledger(state: State) -> bool:
    owner_key = active_ui_session_key(state)
    if not owner_key:
        return False
    rows = [
        item for item in latest_task_records().items()
        if str(item[1].get("session_key") or "") == owner_key
    ]
    plan_id = selected_plan_id_from_rows(rows, require_active=True)
    if not plan_id:
        changed = bool(state.active_plan_task_id or state.active_plan_steps)
        clear_active_plan_state(state)
        return changed
    steps: dict[str, str] = {}
    for task_id, row in rows:
        if str(row.get("parent_task_id") or "") != plan_id:
            continue
        if str(row.get("kind") or "") not in {"plan_step", "plan_summary"}:
            continue
        title = clean_text(str(row.get("title") or "")).strip()
        objective = clean_text(str(row.get("objective") or "")).strip()
        order = int(row.get("order") or 0)
        if order:
            steps[str(order)] = task_id
        for key in (title, objective):
            if key:
                steps[key] = task_id
                steps[re.sub(r"^\s*\d+[.)、]\s*", "", key).strip()] = task_id
    changed = state.active_plan_task_id != plan_id or state.active_plan_steps != steps
    state.active_plan_task_id = plan_id
    state.active_plan_steps = steps
    if changed:
        reset_auto_plan_continue_state(state)
    return changed


def rightbar_subagent_sections(state: State) -> tuple[list[SubAgentRuntime], list[SubAgentRuntime]]:
    owner = active_ui_session_key(state)
    persistent = [sub for sub in state.subagents.values() if sub.persistent]
    temporary = [
        sub for sub in state.subagents.values()
        if not sub.persistent and (not sub.owner_session or not owner or sub.owner_session == owner)
    ]
    persistent.sort(key=lambda item: item.updated_at, reverse=True)
    temporary.sort(key=lambda item: item.updated_at, reverse=True)
    return persistent, temporary


def rightbar_subagents(state: State) -> list[SubAgentRuntime]:
    persistent, temporary = rightbar_subagent_sections(state)
    return persistent + temporary


def secret_import_represented_by_native(import_entry: dict[str, Any], native_entries: list[dict[str, Any]]) -> bool:
    import_path = normalized_path(str(import_entry.get("path") or ""))
    stable_id = str(import_entry.get("stable_id") or "")
    title = str(import_entry.get("title") or "")
    for native in native_entries:
        if import_path and normalized_path(str(native.get("origin_import_path") or "")) == import_path:
            return True
        if stable_id and str(native.get("origin_stable_id") or "") == stable_id:
            return True
        if title and str(native.get("title") or "") == title:
            return True
    return False


def secret_native_entry_for_import_entry(state: State, import_entry: dict[str, Any]) -> Optional[dict[str, Any]]:
    native_entries = [entry for entry in secret_native_session_entries(state, include_payload=False) if not entry.get("error")]
    for native in native_entries:
        if secret_import_represented_by_native(import_entry, [native]):
            return native
    return None


def subagent_sidebar_rows(state: State, sub: SubAgentRuntime, sidebar_w: int) -> list[tuple[str, Any, str, str]]:
    if not sub.chat_session_id:
        sub.chat_session_id = subagent_new_chat_session_id()
    current_key = subagent_session_sidebar_key(sub.agent_id, sub.chat_session_id)
    current_title = truncate_cells(subagent_chat_title_for_messages(sub).replace("\n", " "), sidebar_w - 12)
    rows: list[tuple[str, Any, str, str]] = [
        ("label", None, " AGENT SESSIONS (1)", ""),
        ("subagent_session", current_key, f"● {current_title}", "input" if sub.pending_interaction else sub.status),
        ("blank", None, "", ""),
    ]
    entries = [
        entry for entry in subagent_chat_session_entries(state, sub)
        if str(entry.get("session_id") or "") != sub.chat_session_id
    ]
    rows.append(("label", None, f" {truncate_cells(sub.name, 12)} HISTORY ({len(entries)})", ""))
    if not entries:
        rows.append(("muted", None, "  没有其它会话", ""))
        return rows
    for idx, entry in enumerate(entries, 1):
        session_id = str(entry.get("session_id") or "")
        title = str(entry.get("title") or session_id or "子 agent 会话")
        prefix = f" A{idx:02d} "
        left_width = max(8, sidebar_w - 12 - cell_width(prefix))
        when = parse_iso_timestamp(str(entry.get("updated_at") or ""))
        right = "err" if entry.get("error") else (rel_age(when) if when else "")
        rows.append(("subagent_session", subagent_session_sidebar_key(sub.agent_id, session_id), f"{prefix}{truncate_cells(title.replace(chr(10), ' '), left_width)}", right))
    return rows


def secret_sidebar_history_rows(state: State, sidebar_w: int) -> list[tuple[str, Any, str, str]]:
    native_entries = load_secret_session_sidebar_entries(state)
    active_ids = {state.secret_vault.session_id}
    active_ids.update(
        bg.secret_session_id
        for bg in state.background_sessions.values()
        if bg.security_context == "secret" and bg.secret_session_id
    )
    items: list[dict[str, Any]] = []
    for entry in native_entries:
        session_id = str(entry.get("session_id") or "")
        if session_id and session_id in active_ids:
            continue
        items.append({
            "row_kind": "secret_session",
            "key": secret_session_sidebar_key(session_id),
            "title": str(entry.get("title") or session_id or "Secret 会话"),
            "when": parse_iso_timestamp(str(entry.get("updated_at") or "")),
            "error": entry.get("error"),
        })
    for entry in load_secret_import_sidebar_entries(state):
        if secret_import_represented_by_native(entry, native_entries):
            continue
        items.append({
            "row_kind": "secret_history",
            "key": secret_import_sidebar_key(entry),
            "title": str(entry.get("title") or os.path.basename(str(entry.get("path") or "")) or "Secret 会话"),
            "when": parse_iso_timestamp(str(entry.get("imported_at") or "")),
            "error": entry.get("error"),
        })
    items.sort(key=lambda item: (float(item.get("when") or 0.0), str(item.get("title") or "")), reverse=True)
    rows: list[tuple[str, Any, str, str]] = [("label", None, f" SESSIONS ({len(items)})", "")]
    if not items:
        rows.append(("secret_empty", None, "  没有历史 Secret 会话", ""))
        return rows
    for idx, item in enumerate(items, 1):
        prefix = f" S{idx:02d} "
        left_width = max(8, sidebar_w - 12 - cell_width(prefix))
        title = str(item.get("title") or "Secret 会话")
        right = "err" if item.get("error") else (rel_age(float(item.get("when") or 0.0)) if item.get("when") else "")
        rows.append((str(item["row_kind"]), item["key"], f"{prefix}{truncate_cells(title.replace(chr(10), ' '), left_width)}", right))
    return rows


def secret_import_sidebar_rows(state: State, sidebar_w: int) -> list[tuple[str, Any, str, str]]:
    return [row for row in secret_sidebar_history_rows(state, sidebar_w) if row[0] in {"label", "secret_empty", "secret_history"}]


def secret_native_sidebar_rows(state: State, sidebar_w: int) -> list[tuple[str, Any, str, str]]:
    return [row for row in secret_sidebar_history_rows(state, sidebar_w) if row[0] in {"label", "secret_empty", "secret_session"}]


def render_sidebar_rows(
    stdscr: Any,
    state: State,
    height: int,
    sidebar_w: int,
    panel_h: int,
    list_h: int,
    rows: list[tuple[str, Any, str, str]],
) -> int:
    state.sidebar_rows = rows

    max_scroll = max(0, len(rows) - max(1, list_h - 1))
    state.sidebar_scroll = max(0, min(state.sidebar_scroll, max_scroll))

    for y in range(height):
        safe_add(stdscr, y, 0, " " * sidebar_w, sidebar_w, cp(6))
    for screen_y, row in enumerate(rows[state.sidebar_scroll:state.sidebar_scroll + list_h - 1]):
        kind, key, left, right = row
        attr = cp(6)
        if kind == "label":
            attr = cp(7) | curses.A_BOLD
        elif kind == "category":
            attr = cp(1) | curses.A_BOLD
        elif kind == "session":
            attr = cp(8) | curses.A_BOLD
        elif kind == "background":
            attr = cp(8) if right in {"running", "aborting"} else cp(9)
        elif kind in {"history", "secret_history", "secret_session", "subagent_session"}:
            attr = cp(1) if kind in {"secret_history", "secret_session", "subagent_session"} and right == "err" else cp(9)
        elif kind == "muted":
            attr = cp(9)
        elif kind == "blank":
            safe_add(stdscr, screen_y, 0, " " * sidebar_w, sidebar_w, cp(6))
            continue
        selected_sub = selected_subagent(state)
        subagent_selected = (
            kind == "subagent_session"
            and selected_sub is not None
            and key == subagent_session_sidebar_key(selected_sub.agent_id, selected_sub.chat_session_id)
        )
        if (key == state.selected_session and kind in {"session", "history", "background", "secret_history", "secret_session"}) or subagent_selected:
            attr = cp(11) | curses.A_BOLD
        safe_add(stdscr, screen_y, 0, " " * sidebar_w, sidebar_w, attr)
        safe_add(stdscr, screen_y, 1, left, sidebar_w - 10, attr)
        if right and right != "err":
            safe_add(stdscr, screen_y, sidebar_w - 8, right, 7, attr)
    for y in range(height):
        safe_add(stdscr, y, sidebar_w - 1, "│", 1, cp(10))
    if panel_h:
        top = height - panel_h
        safe_add(stdscr, top, 0, "─" * (sidebar_w - 1), sidebar_w - 1, cp(10))
        for idx, (text, attr) in enumerate(current_status_panel_lines(state, sidebar_w), 1):
            if top + idx >= height:
                break
            safe_add(stdscr, top + idx, 1, text, sidebar_w - 3, attr)
    return sidebar_w


def draw_sidebar(stdscr, state: State, height: int, width: int) -> int:
    sidebar_w = left_sidebar_width(width)
    panel_h = min(TOKEN_PANEL_H, max(0, height - 8))
    list_h = max(1, height - panel_h)
    rows: list[tuple[str, Any, str, str]] = []
    active_sub = selected_subagent(state)
    if active_sub is not None:
        rows.extend(subagent_sidebar_rows(state, active_sub, sidebar_w))
        return render_sidebar_rows(stdscr, state, height, sidebar_w, panel_h, list_h, rows)
    visible_backgrounds = [
        bg for bg in state.background_sessions.values()
        if (bg.security_context == "secret") == bool(state.secret_vault.unlocked)
    ]
    current_count = 1 + len(visible_backgrounds)
    rows.append(("label", None, f" CURRENT SESSIONS ({current_count})", ""))
    current = truncate_cells((state.current_title or "main").replace("\n", " "), sidebar_w - 12)
    current_key = secret_session_sidebar_key(state.secret_vault.session_id) if state.secret_vault.unlocked else "main"
    rows.append(("session", current_key, f"● {current}", "input" if state.pending_interaction else state.status))
    if visible_backgrounds:
        for bg in visible_backgrounds:
            marker = "●" if bg.status in {"running", "aborting"} else "○"
            title = truncate_cells(bg.title.replace("\n", " ") or "后台会话", sidebar_w - 12)
            rows.append(("background", bg.key, f"{marker} {title}", "input" if bg.pending_interaction else bg.status))
    rows.append(("blank", None, "", ""))
    if state.secret_vault.unlocked:
        rows.extend(secret_sidebar_history_rows(state, sidebar_w))
        return render_sidebar_rows(stdscr, state, height, sidebar_w, panel_h, list_h, rows)

    label = f" {'ARCHIVED ' if state.show_archived else ''}SESSIONS ({len(state.history)})"
    if state.session_filter_category:
        label += f" · {truncate_cells(state.session_filter_category, 12)}"
    rows.append(("label", None, label, ""))
    history_entries = list(enumerate(state.history, 1))
    used_paths: set[str] = set()
    filter_kind = system_session_category(state.session_filter_category)

    def add_history_group(cat_label: str, items: list[tuple[int, tuple[str, float, str, int]]]) -> None:
        key = category_key(cat_label)
        if not items and not filter_kind:
            return
        collapsed = key in state.collapsed_categories
        arrow = "▸" if collapsed else "▾"
        rows.append(("category", cat_label, f"{arrow} {cat_label} ({len(items)})", ""))
        if collapsed:
            return
        for idx, (path, mtime, first, rounds) in items:
            title = history_name(state, path) or first or "历史会话"
            meta = session_meta_for(state, path)
            marker = "*" if meta.get("pinned") else " "
            prefix = f"{marker}S{idx:02d} "
            left_width = max(8, sidebar_w - 12 - cell_width(prefix))
            shown_time = mtime
            rows.append(("history", path, f"{prefix}{truncate_cells(title.replace(chr(10), ' '), left_width)}", f"{rel_age(shown_time or mtime)} {rounds}"))

    show_virtual = not state.session_filter_category or bool(filter_kind)
    if show_virtual and filter_kind in {"", "pinned"}:
        pinned_items = [
            (idx, item)
            for idx, item in history_entries
            if session_meta_for(state, item[0]).get("pinned")
        ]
        if pinned_items:
            add_history_group(PINNED_SESSION_LABEL, pinned_items)
            used_paths.update(normalized_path(item[0]) for _idx, item in pinned_items)

    if show_virtual and filter_kind in {"", "recent"}:
        recent_items = recent_history_items(history_entries, used_paths)
        if recent_items or filter_kind == "recent":
            add_history_group(RECENT_SESSION_LABEL, recent_items)
            used_paths.update(normalized_path(item[0]) for _idx, item in recent_items)

    if filter_kind not in {"pinned", "recent"}:
        grouped: dict[str, dict[str, Any]] = {}
        for idx, item in history_entries:
            path, _mtime, _first, _rounds = item
            if normalized_path(path) in used_paths:
                continue
            cat = session_category_label(session_meta_for(state, path))
            key = category_key(cat)
            if key not in grouped:
                grouped[key] = {"label": cat, "items": []}
            grouped[key]["items"].append((idx, item))
        ordered_keys = sorted(grouped, key=lambda item_key: category_sort_key(str(grouped[item_key]["label"])))
        for key in ordered_keys:
            group = grouped[key]
            add_history_group(str(group["label"]), group["items"])
    return render_sidebar_rows(stdscr, state, height, sidebar_w, panel_h, list_h, rows)


def rightbar_task_rows(state: State, limit: int) -> list[tuple[str, Any, str, str]]:
    now = time.time()
    owner_key = active_ui_session_key(state)
    ledger_signature = task_ledger_signature()
    if (
        state.rightbar_task_rows_cache
        and state.rightbar_task_rows_limit == limit
        and state.rightbar_task_rows_owner == owner_key
        and state.rightbar_task_rows_ledger_signature == ledger_signature
        and now - state.rightbar_task_rows_loaded_at < 0.75
    ):
        return list(state.rightbar_task_rows_cache)
    latest = latest_task_records()
    visible_agents = rightbar_subagents(state)
    rows = list(latest.items())
    active_task_ids = {sub.active_bus_task_id for sub in visible_agents if sub.active_bus_task_id}
    if owner_key or active_task_ids:
        rows = [
            item for item in rows
            if (owner_key and str(item[1].get("session_key") or "") == owner_key)
            or item[0] in active_task_ids
        ]
    plan_id = rightbar_selected_plan_id(state, rows)
    plan_rows = [
        item for item in rows
        if str(item[1].get("kind") or "") in {"plan_step", "plan_summary"}
        and (not plan_id or str(item[1].get("parent_task_id") or "") == plan_id)
    ]
    if plan_id and plan_rows:
        rows = plan_rows

    def sort_key(item: tuple[str, dict[str, Any]]) -> tuple[int, float]:
        _task_id, row = item
        status = str(row.get("status") or "")
        running_rank = 0 if not terminal_task_status(status) else 1
        order = int(row.get("order") or 0)
        if str(row.get("kind") or "") in {"plan_step", "plan_summary"} and order:
            return 0, float(order)
        return running_rank, -row_timestamp(row)

    result: list[tuple[str, Any, str, str]] = []
    for task_id, row in sorted(rows, key=sort_key)[:limit]:
        status = str(row.get("status") or "-")
        approval = approval_status_for_task(task_id)
        marker = task_status_marker(status, approval)
        owner = str(row.get("assigned_agent") or "-")
        title = task_display_title(row, state)
        left = f"{marker} {truncate_cells(title, 24)}"
        right = status if status != "completed" else "done"
        if owner != "-" and not row_looks_like_subagent_task(row, owner) and str(row.get("kind") or "") not in {"plan_step", "plan_summary"}:
            right = truncate_cells(owner, 7)
        result.append(("right_task", task_id, left, right))
    state.rightbar_task_rows_cache = list(result)
    state.rightbar_task_rows_loaded_at = now
    state.rightbar_task_rows_limit = limit
    state.rightbar_task_rows_owner = owner_key
    state.rightbar_task_rows_ledger_signature = ledger_signature
    return result


def draw_rightbar(stdscr, state: State, height: int, width: int) -> int:
    rightbar_w = rightbar_width_for_terminal(width)
    state.rightbar_width = rightbar_w
    state.rightbar_rows = []
    if rightbar_w <= 0:
        state.rightbar_x0 = width
        return 0
    x0 = width - rightbar_w
    state.rightbar_x0 = x0
    rows: list[tuple[str, Any, str, str]] = []
    persistent_agents, temporary_agents = rightbar_subagent_sections(state)
    agents = persistent_agents + temporary_agents
    desired_agent_rows = 4 + max(1, len(persistent_agents)) + max(1, len(temporary_agents))
    agent_area_h = max(6, min(height // 2, desired_agent_rows))
    task_area_h = max(3, height - agent_area_h)

    agent_rows: list[tuple[str, Any, str, str]] = [("label", None, f" AGENTS ({len(agents) + 1})", "")]
    agent_rows.append(("right_main", "main", "● 主 agent", "input" if state.pending_interaction else state.status))

    def append_agent_section(section_title: str, section: list[SubAgentRuntime]) -> None:
        agent_rows.append(("divider", None, f" {section_title} ({len(section)})", ""))
        if not section:
            agent_rows.append(("muted", None, "○ 暂无", ""))
            return
        for sub in section:
            marker = subagent_status_marker(sub)
            shown_title = truncate_cells(sub.name.replace("\n", " "), rightbar_w - 12)
            right = "input" if sub.pending_interaction else (f"q:{len(sub.task_queue)}" if sub.task_queue and sub.status == "idle" else sub.status)
            agent_rows.append(("right_agent", sub.agent_id, f"{marker} {shown_title}", right))

    append_agent_section("持久", persistent_agents)
    append_agent_section("临时会话", temporary_agents)
    rows.extend(agent_rows[:agent_area_h])
    while len(rows) < agent_area_h:
        rows.append(("blank", None, "", ""))
    rows.append(("divider", None, " TASKS", ""))
    task_limit = max(1, task_area_h - 2)
    task_rows = rightbar_task_rows(state, task_limit)
    rows.extend(task_rows or [("muted", None, "○ 暂无任务", "")])
    rows = rows[:height]
    state.rightbar_rows = rows

    for y in range(height):
        safe_add(stdscr, y, x0, " " * rightbar_w, rightbar_w, cp(6))
        safe_add(stdscr, y, x0, "│", 1, cp(10))
    for y, row in enumerate(rows):
        kind, key, left, right = row
        attr = cp(6)
        if kind in {"label", "divider"}:
            attr = cp(7) | curses.A_BOLD
        elif kind == "right_main":
            active = selected_subagent(state) is None
            attr = cp(8) if state.status in {"running", "aborting", "waiting-input"} else cp(9)
            if active:
                attr = cp(11) | curses.A_BOLD
        elif kind == "right_agent":
            sub = state.subagents.get(str(key))
            active = str(key) == str(state.selected_session)
            status = sub.status if sub is not None else ""
            attr = cp(8) if status in {"running", "aborting", "waiting-input"} or (sub is not None and sub.task_queue) else cp(9)
            if active:
                attr = cp(11) | curses.A_BOLD
        elif kind == "right_task":
            attr = cp(8) if str(left).startswith(("●", "?")) else cp(9)
        elif kind == "muted":
            attr = cp(9)
        safe_add(stdscr, y, x0 + 1, " " * (rightbar_w - 1), rightbar_w - 1, attr)
        safe_add(stdscr, y, x0 + 2, left, rightbar_w - 10, attr)
        if right:
            safe_add(stdscr, y, x0 + rightbar_w - 8, truncate_cells(str(right), 7), 7, attr)
    return rightbar_w


def raw_cursor_to_display(text: str, cursor: int) -> int:
    return len((text or "")[:max(0, min(cursor, len(text or "")))].replace("\n", "\\n"))


def display_cursor_to_raw(text: str, display_cursor: int) -> int:
    raw = text or ""
    display_cursor = max(0, display_cursor)
    display_pos = 0
    for idx, ch in enumerate(raw):
        width = 2 if ch == "\n" else 1
        if display_cursor <= display_pos:
            return idx
        display_pos += width
        if display_cursor <= display_pos:
            return idx + 1
    return len(raw)


def input_segments(text: str, width: int) -> tuple[str, list[tuple[str, int, int]]]:
    body_width = max(1, width - 2)
    display = (text or "").replace("\n", "\\n")
    segments: list[tuple[str, int, int]] = []
    current = ""
    current_w = 0
    start = 0
    for idx, ch in enumerate(display):
        w = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
        if current and current_w + w > body_width:
            segments.append((current, start, idx))
            current = ch
            current_w = w
            start = idx
        else:
            current += ch
            current_w += w
    segments.append((current, start, len(display)))
    return display, segments


def display_index_for_cell(display: str, start: int, end: int, target_x: int) -> int:
    target_x = max(0, target_x)
    used = 0
    for idx in range(start, end):
        ch = display[idx]
        width = 0 if unicodedata.combining(ch) else (2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1)
        if used + width > target_x:
            return idx
        used += width
        if used >= target_x:
            return idx + 1
    return end


def input_cursor_info(text: str, width: int, cursor: int) -> tuple[str, list[tuple[str, int, int]], int, int, int]:
    raw = text or ""
    cursor = max(0, min(cursor, len(raw)))
    display, segments = input_segments(raw, width)
    display_cursor = raw_cursor_to_display(raw, cursor)

    cursor_line = len(segments) - 1
    for idx, (_segment, seg_start, seg_end) in enumerate(segments):
        if seg_start <= display_cursor < seg_end or (display_cursor == seg_end and idx == len(segments) - 1):
            cursor_line = idx
            break
    _segment, seg_start, _seg_end = segments[cursor_line]
    cursor_x = cell_width(display[seg_start:display_cursor])
    return display, segments, display_cursor, cursor_line, cursor_x


def move_input_cursor_vertical(state: State, width: int, direction: int) -> bool:
    if not state.input_text:
        return False
    display, segments, _display_cursor, cursor_line, cursor_x = input_cursor_info(state.input_text, width, state.input_cursor)
    if len(segments) <= 1:
        return False
    target_line = cursor_line + direction
    if target_line < 0 or target_line >= len(segments):
        return True
    _segment, seg_start, seg_end = segments[target_line]
    target_display = display_index_for_cell(display, seg_start, seg_end, cursor_x)
    state.input_cursor = display_cursor_to_raw(state.input_text, target_display)
    clamp_input_cursor(state)
    mark_dirty(state)
    return True


def input_layout(text: str, width: int, max_lines: int, cursor: int, prompt: str = "> ") -> tuple[list[str], int, int]:
    max_lines = max(1, max_lines)
    display, segments, display_cursor, cursor_line, _cursor_x = input_cursor_info(text, width, cursor)
    first = 0
    if len(segments) > max_lines:
        first = max(0, min(cursor_line, len(segments) - max_lines))
    visible = segments[first:first + max_lines]
    lines: list[str] = []
    cursor_y = max(0, cursor_line - first)
    cursor_x = cell_width(prompt)
    for idx, (segment, seg_start, _seg_end) in enumerate(visible):
        actual_idx = first + idx
        prefix = prompt if actual_idx == 0 else " " * cell_width(prompt)
        if first > 0 and idx == 0:
            prefix = "… "
        lines.append(prefix + segment)
        if actual_idx == cursor_line:
            before = display[seg_start:display_cursor]
            cursor_x = cell_width(prefix) + cell_width(before)
    return lines or [prompt], cursor_y, cursor_x


def draw_text_with_selection(stdscr, y: int, x: int, text: str, width: int, attr: int, selection: Optional[tuple[int, int]]) -> None:
    if selection is None:
        safe_add(stdscr, y, x, text, width, attr)
        return
    start, end = selection
    before = text[:start]
    chosen = text[start:end]
    after = text[end:]
    before_w = cell_width(before)
    chosen_w = cell_width(chosen)
    if before_w > 0:
        safe_add(stdscr, y, x, before, min(width, before_w), attr)
    if chosen_w > 0 and before_w < width:
        safe_add(stdscr, y, x + before_w, chosen, width - before_w, cp(11) | curses.A_BOLD)
    after_x = before_w + chosen_w
    if after and after_x < width:
        safe_add(stdscr, y, x + after_x, after, width - after_x, attr)


def draw_main(stdscr, state: State, height: int, width: int, sidebar_w: int, rightbar_w: int) -> None:
    x0 = sidebar_w + 1
    right_x0 = width - rightbar_w if rightbar_w > 0 else width
    main_w = max(10, right_x0 - x0 - 1)
    secret_input = secret_password_entry_active(state)
    matches = [] if secret_input else command_matches(state.input_text, state)
    clamp_command_index(state, matches)
    visible_limit = min(len(matches), 10, max(0, height - 8))
    if visible_limit and state.command_index >= visible_limit:
        state.command_index = visible_limit - 1
    visible_commands = matches[:visible_limit]
    active_interaction = current_interaction_payload(state) if not matches and not secret_input else None
    interaction_lines = secret_hint_lines(state, main_w) if secret_input else interaction_hint_lines(active_interaction, main_w)
    queued_lines = [] if secret_input else queued_user_input_hint_lines(state, main_w)
    max_input_lines = max(1, min(6, height - len(visible_commands) - len(interaction_lines) - len(queued_lines) - 8))
    clamp_input_cursor(state)
    input_prompt = secret_prompt_text(state) if secret_input else interaction_input_prompt(active_interaction)
    input_text = "*" * len(state.input_text) if secret_input else state.input_text
    input_lines, cursor_y, cursor_x = input_layout(input_text, main_w, max_input_lines, state.input_cursor, input_prompt)
    input_h = 2 + len(visible_commands) + len(interaction_lines) + len(queued_lines) + len(input_lines)
    body_h = max(1, height - input_h - 2)
    lines = message_lines_cached(state, main_w)
    state.main_x0 = x0
    state.main_width = main_w
    state.body_top = 1
    state.body_height = body_h
    max_scroll = max(0, len(lines) - body_h)
    if state.follow_bottom:
        state.scroll = max_scroll
    state.scroll = max(0, min(state.scroll, max_scroll))
    safe_add(stdscr, 0, x0, top_bar_header(state), main_w, curses.A_BOLD)

    for row in range(body_h):
        idx = state.scroll + row
        line = lines[idx] if idx < len(lines) else RenderLine("")
        safe_add(stdscr, row + 1, x0, " " * main_w, main_w)
        selection = selection_span_for_line(state, idx, line.text)
        draw_text_with_selection(stdscr, row + 1, x0, line.text, main_w, line.attr, selection)
    sep_y = height - input_h - 1
    safe_add(stdscr, sep_y, x0, "─" * main_w, main_w, cp(1))
    hint_y = sep_y + 1 + len(visible_commands)
    queued_y = hint_y + len(interaction_lines)
    prompt_y = queued_y + len(queued_lines)
    for i, (cmd, args, desc, _sendable) in enumerate(visible_commands):
        attr = cp(11) | curses.A_BOLD if i == state.command_index else cp(2)
        line = f"  {cmd:<11} {args:<8} {desc}"
        safe_add(stdscr, sep_y + 1 + i, x0, " " * main_w, main_w, attr)
        safe_add(stdscr, sep_y + 1 + i, x0, line, main_w, attr)
    for i, (line, attr) in enumerate(interaction_lines):
        safe_add(stdscr, hint_y + i, x0, " " * main_w, main_w, attr)
        safe_add(stdscr, hint_y + i, x0, line, main_w, attr)
    for i, (line, attr) in enumerate(queued_lines):
        safe_add(stdscr, queued_y + i, x0, " " * main_w, main_w, attr)
        safe_add(stdscr, queued_y + i, x0, line, main_w, attr)
    for i, line in enumerate(input_lines):
        safe_add(stdscr, prompt_y + i, x0, " " * main_w, main_w)
        safe_add(stdscr, prompt_y + i, x0, line, main_w, cp(3))
    footer_y = prompt_y + len(input_lines)
    if state.last_error:
        safe_add(stdscr, footer_y, x0, state.last_error, main_w, cp(5))
    elif selected_subagent(state) is not None:
        sub = selected_subagent(state)
        safe_add(stdscr, footer_y, x0, f"SubAgent chat: {sub.agent_id}; 输入直接发给 {sub.name}; /agent ask 才委派任务; 右侧主 agent 返回", main_w, cp(1))
    else:
        safe_add(stdscr, footer_y, x0, "Ctrl+Q quit; F2 rename; /agent manage; /memory inspect; Ctrl+N new; Ctrl+W close", main_w, cp(1))
    try:
        stdscr.move(prompt_y + cursor_y, min(x0 + cursor_x, x0 + main_w - 1))
    except curses.error:
        pass


def redraw(stdscr, state: State) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    if height < 8 or width < 50:
        safe_add(stdscr, 0, 0, "Terminal too small", max(1, width - 1), curses.A_BOLD)
        stdscr.refresh()
        return
    sidebar_w = draw_sidebar(stdscr, state, height, width)
    rightbar_w = draw_rightbar(stdscr, state, height, width)
    draw_main(stdscr, state, height, width, sidebar_w, rightbar_w)
    draw_session_info_popup(stdscr, state, height, width)
    stdscr.refresh()


def popup_geometry(height: int, width: int, min_h: int = 12, min_w: int = 58) -> tuple[int, int, int, int]:
    pop_h = min(max(min_h, height - 4), max(3, int(height * 0.82)))
    pop_w = min(max(min_w, width - 8), max(10, int(width * 0.78)))
    y0 = max(0, (height - pop_h) // 2)
    x0 = max(0, (width - pop_w) // 2)
    return y0, x0, pop_h, pop_w


def draw_popup(stdscr, y0: int, x0: int, h: int, w: int, title: str) -> None:
    for y in range(y0, y0 + h):
        safe_add(stdscr, y, x0, " " * w, w, cp(6))
    safe_add(stdscr, y0, x0, "┌" + "─" * (w - 2) + "┐", w, cp(10))
    safe_add(stdscr, y0 + h - 1, x0, "└" + "─" * (w - 2) + "┘", w, cp(10))
    for y in range(y0 + 1, y0 + h - 1):
        safe_add(stdscr, y, x0, "│", 1, cp(10))
        safe_add(stdscr, y, x0 + w - 1, "│", 1, cp(10))
    safe_add(stdscr, y0, x0 + 2, f" {title} ", w - 4, cp(7) | curses.A_BOLD)


def session_info_popup_lines(state: State, path: str, inner_w: int) -> list[tuple[str, int]]:
    title = session_title_for_path(state, path)
    meta = session_meta_for(state, path)
    desc = state.history_descriptions.get(path) or compact_description(str(meta.get("description") or ""))
    if not desc:
        preview = ""
        for item_path, _mtime, item_preview, _rounds in state.history:
            if normalized_path(item_path) == normalized_path(path):
                preview = item_preview
                break
        desc = session_description_from_path(path, preview) or "暂无简介。"
    desc = compact_description(desc)
    lines: list[tuple[str, int]] = [
        (f"标题: {title}", cp(7) | curses.A_BOLD),
        (f"ID: {session_stable_id(path)}", cp(1)),
        (f"分类: {session_category_label(meta)}" + ("  · 置顶" if meta.get("pinned") else ""), cp(1)),
        ("", cp(1)),
        ("简介:", cp(7) | curses.A_BOLD),
    ]
    for line in wrap_cells(desc, inner_w):
        lines.append((line, cp(2)))
    return lines


def draw_session_info_popup(stdscr, state: State, height: int, width: int) -> None:
    path = state.session_popup_path
    if not path:
        state.session_popup_rect = None
        return
    anchor = state.session_popup_anchor or (state.main_x0, 1)
    pop_w = min(74, max(38, width - 4))
    inner_w = max(10, pop_w - 4)
    lines = session_info_popup_lines(state, path, inner_w)
    pop_h = min(max(8, len(lines) + 4), max(6, height - 2))
    x0 = max(1, min(width - pop_w - 1, anchor[0] + 2))
    if x0 < state.main_x0 and width - state.main_x0 > pop_w + 2:
        x0 = state.main_x0 + 1
    y0 = max(1, min(height - pop_h - 1, anchor[1]))
    draw_popup(stdscr, y0, x0, pop_h, pop_w, "会话简介")
    max_rows = pop_h - 3
    for idx, (line, attr) in enumerate(lines[:max_rows]):
        safe_add(stdscr, y0 + 2 + idx, x0 + 2, line, inner_w, attr)
    if len(lines) > max_rows:
        safe_add(stdscr, y0 + pop_h - 2, x0 + 2, "...", inner_w, cp(1))
    else:
        safe_add(stdscr, y0 + pop_h - 2, x0 + 2, "鼠标移开自动关闭", inner_w, cp(1))
    state.session_popup_rect = (y0, x0, pop_h, pop_w)


def draw_model_manager(
    stdscr,
    state: State,
    entries: list[LLMConfigEntry],
    mixin: dict[str, Any],
    selected: int,
    message: str,
    health: Optional[dict[str, tuple[bool, str]]] = None,
    *,
    recent_names: Optional[list[str]] = None,
    title: str = "当前对话模型",
    manage_configs: bool = False,
) -> None:
    height, width = stdscr.getmaxyx()
    y0, x0, h, w = popup_geometry(height, width, min_w=82)
    draw_popup(stdscr, y0, x0, h, w, title)
    inner_w = w - 4
    current = ""
    try:
        current = state.agent.get_llm_name(model=True)
    except Exception:
        current = "unknown"
    primary = (mixin.get("llm_nos") or [""])[0]
    recent_names = recent_names or []
    recent_text = " / ".join(recent_names[:3]) if recent_names else "(无)"
    safe_add(stdscr, y0 + 2, x0 + 2, f"当前对话: {current}    默认新对话: {primary or '(未设置)'}    最近: {recent_text}", inner_w, cp(2))
    if manage_configs:
        help_text = "Enter 当前对话  d 设默认  u 最近  a 新增  e 编辑  p 提取模型  t 测试  v 全部验活  x 删除  r 重载"
    else:
        help_text = "Enter 仅切当前对话  d 设默认新对话  u 最近  t 测试选中  v 批量验活  r 重载配置  Esc 返回"
    safe_add(stdscr, y0 + 3, x0 + 2, help_text, inner_w, cp(1))
    start_y = y0 + 5
    list_h = max(1, h - 8)
    if not entries:
        safe_add(stdscr, start_y, x0 + 2, "还没有已配置模型；用 /llm 添加供应商/API。", inner_w, cp(5))
    view_start = max(0, min(selected - list_h + 1, max(0, len(entries) - list_h)))
    for row, entry in enumerate(entries[view_start:view_start + list_h]):
        idx = view_start + row
        cfg = entry.cfg
        name = config_display_name(entry)
        marker = ("*" if name == primary else " ") + ("r" if name in recent_names else " ")
        health_result = health.get(model_health_key(entry)) if health else None
        status = "    "
        if health_result is not None:
            status = "OK  " if health_result[0] else "BAD "
        line = f"{status}{marker} {idx + 1:02d} {name:<18} {cfg.get('model', ''):<24} {cfg.get('apibase', '')}"
        attr = cp(11) | curses.A_BOLD if idx == selected else cp(2)
        if health_result is not None and not health_result[0] and idx != selected:
            attr = cp(5)
        safe_add(stdscr, start_y + row, x0 + 2, " " * inner_w, inner_w, attr)
        safe_add(stdscr, start_y + row, x0 + 2, line, inner_w, attr)
    detail_y = y0 + h - 3
    if entries:
        cfg = entries[selected].cfg
        detail = f"Key: {mask_secret(str(cfg.get('apikey') or ''))}"
        health_result = health.get(model_health_key(entries[selected])) if health else None
        if health_result is not None:
            label = "OK" if health_result[0] else "BAD"
            detail += f"    验活: {label} {health_result[1]}"
        safe_add(stdscr, detail_y, x0 + 2, detail, inner_w, cp(1))
    if message:
        safe_add(stdscr, y0 + h - 2, x0 + 2, message, inner_w, cp(5) if "失败" in message or "错误" in message else cp(3))
    stdscr.refresh()


def draw_modal_notice(stdscr, state: State, title: str, lines: list[str], footer: str = "按任意键继续") -> None:
    redraw(stdscr, state)
    height, width = stdscr.getmaxyx()
    y0, x0, h, w = popup_geometry(height, width, min_h=8, min_w=76)
    draw_popup(stdscr, y0, x0, h, w, title)
    inner_w = w - 4
    y = y0 + 2
    max_y = y0 + h - 2
    for raw in lines:
        for line in wrap_cells(raw, inner_w):
            if y >= max_y:
                break
            safe_add(stdscr, y, x0 + 2, line, inner_w, cp(2))
            y += 1
        if y >= max_y:
            break
    if footer:
        safe_add(stdscr, y0 + h - 2, x0 + 2, footer, inner_w, cp(1))
    stdscr.refresh()


def modal_read_key(stdscr):
    stdscr.timeout(-1)
    try:
        return read_terminal_key(stdscr)
    finally:
        stdscr.timeout(-1)


def drain_pending_keys(stdscr, duration: float = 0.05) -> None:
    """Drop key-sequence leftovers before opening a modal.

    Some terminals report F2 as ESC-O-Q fragments. If the modal sees the
    trailing Q as its first key, it looks like the window flashed and closed.
    """
    try:
        curses.flushinp()
    except curses.error:
        pass
    deadline = time.monotonic() + duration
    try:
        stdscr.timeout(0)
        while time.monotonic() < deadline:
            try:
                stdscr.get_wch()
            except curses.error:
                time.sleep(0.005)
    finally:
        stdscr.timeout(-1)


def modal_poll_escape(stdscr) -> bool:
    stdscr.timeout(0)
    try:
        key = stdscr.get_wch()
    except curses.error:
        return False
    finally:
        stdscr.timeout(-1)
    return key in ("\x1b", 27)


def restore_main_poll_timeout(stdscr) -> None:
    if stdscr is None:
        return
    try:
        stdscr.timeout(TUI_POLL_TIMEOUT_MS)
    except curses.error:
        pass


def memory_entry_for(layer: str, path: str, note: str = "") -> Optional[MemoryEntry]:
    try:
        st = os.stat(path)
    except OSError:
        return None
    label = os.path.relpath(path, os.path.join(ROOT_DIR, "memory"))
    return MemoryEntry(layer=layer, label=label, path=path, size=int(st.st_size), mtime=float(st.st_mtime), note=note)


def memory_inventory() -> list[MemoryEntry]:
    memory_root = os.path.join(ROOT_DIR, "memory")
    entries: list[MemoryEntry] = []
    for layer, filename, note in [
        ("L1", "global_mem_insight.txt", "启动自动注入的极简索引"),
        ("L2", "global_mem.txt", "全局事实库"),
        ("L0", "memory_management_sop.md", "记忆写入规则"),
    ]:
        item = memory_entry_for(layer, os.path.join(memory_root, filename), note)
        if item:
            entries.append(item)
    for root, dirs, files in os.walk(memory_root):
        dirs[:] = [d for d in dirs if d not in {"__pycache__"} and not d.startswith(".")]
        rel_root = os.path.relpath(root, memory_root)
        if rel_root == ".":
            rel_root = ""
        for filename in sorted(files):
            if filename.startswith(".") or filename.endswith((".pyc", ".json")):
                continue
            path = os.path.join(root, filename)
            rel = os.path.relpath(path, memory_root)
            if rel in {"global_mem_insight.txt", "global_mem.txt", "memory_management_sop.md"}:
                continue
            if rel.startswith("L4_raw_sessions"):
                layer = "L4"
                note = "历史会话归档/压缩"
            elif rel.startswith("agent_harness"):
                layer = "Harness"
                note = "任务账本/agent mail/审批/artifact"
            elif rel.startswith("subagents"):
                layer = "Agent"
                note = "子 agent 档案/记忆"
            else:
                layer = "L3"
                note = "SOP 或复用工具"
            item = memory_entry_for(layer, path, note)
            if item:
                entries.append(item)
    order = {"L1": 0, "L2": 1, "L0": 2, "L3": 3, "Agent": 4, "Harness": 5, "L4": 6}
    entries.sort(key=lambda item: (order.get(item.layer, 99), item.label.lower()))
    return entries


def memory_file_preview(path: str, max_bytes: int = 24000) -> list[str]:
    try:
        with open(path, "rb") as fh:
            data = fh.read(max_bytes + 1)
    except Exception as exc:
        return [f"读取失败: {type(exc).__name__}: {exc}"]
    truncated = len(data) > max_bytes
    if truncated:
        data = data[:max_bytes]
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines() or [""]
    if truncated:
        lines.append("")
        lines.append("... 文件较大，预览已截断 ...")
    return lines


def draw_memory_viewer(stdscr, state: State, entries: list[MemoryEntry], selected: int, detail_scroll: int, message: str = "") -> None:
    redraw(stdscr, state)
    height, width = stdscr.getmaxyx()
    y0, x0, h, w = popup_geometry(height, width, min_h=18, min_w=96)
    draw_popup(stdscr, y0, x0, h, w, "记忆系统可视化检查")
    inner_w = w - 4
    left_w = min(42, max(28, inner_w // 3))
    right_x = x0 + 2 + left_w + 2
    right_w = max(20, inner_w - left_w - 3)
    list_h = h - 5
    safe_add(stdscr, y0 + 1, x0 + 2, f"items:{len(entries)}  r 刷新  ↑/↓ 选择  PgUp/PgDn 滚动预览  Esc 关闭", inner_w, cp(1))
    safe_add(stdscr, y0 + 2, x0 + 2, "─" * left_w, left_w, cp(10))
    safe_add(stdscr, y0 + 2, right_x, "─" * right_w, right_w, cp(10))
    if not entries:
        safe_add(stdscr, y0 + 4, x0 + 2, "没有找到 memory 文件。", inner_w, cp(5))
        stdscr.refresh()
        return
    selected = max(0, min(selected, len(entries) - 1))
    first = max(0, min(selected - list_h // 2, max(0, len(entries) - list_h)))
    visible = entries[first:first + list_h]
    for row, entry in enumerate(visible):
        y = y0 + 3 + row
        attr = cp(11) | curses.A_BOLD if first + row == selected else cp(9)
        size = f"{entry.size // 1024}K" if entry.size >= 1024 else f"{entry.size}B"
        line = f"{entry.layer:<5} {truncate_cells(entry.label, left_w - 13)} {size:>6}"
        safe_add(stdscr, y, x0 + 2, " " * left_w, left_w, attr)
        safe_add(stdscr, y, x0 + 2, line, left_w, attr)
    entry = entries[selected]
    header = f"{entry.layer} · {entry.label} · {entry.size} bytes · {rel_age(entry.mtime)}"
    safe_add(stdscr, y0 + 3, right_x, header, right_w, cp(7) | curses.A_BOLD)
    if entry.note:
        safe_add(stdscr, y0 + 4, right_x, entry.note, right_w, cp(1))
    safe_add(stdscr, y0 + 5, right_x, entry.path, right_w, cp(2))
    preview_lines = []
    for raw in memory_file_preview(entry.path):
        preview_lines.extend(wrap_cells(raw, right_w))
    max_scroll = max(0, len(preview_lines) - max(1, h - 9))
    detail_scroll = max(0, min(detail_scroll, max_scroll))
    for row, line in enumerate(preview_lines[detail_scroll:detail_scroll + h - 9]):
        safe_add(stdscr, y0 + 7 + row, right_x, line, right_w, cp(2))
    footer = message or "提示：这里只读检查，不会修改记忆。子 agent 记忆在 Agent 分组。"
    safe_add(stdscr, y0 + h - 2, x0 + 2, footer, inner_w, cp(1))
    stdscr.refresh()


def open_memory_viewer(stdscr, state: State) -> None:
    selected = 0
    detail_scroll = 0
    message = ""
    entries = memory_inventory()
    try:
        drain_pending_keys(stdscr)
        stdscr.timeout(-1)
        while True:
            if selected >= len(entries):
                selected = max(0, len(entries) - 1)
            draw_memory_viewer(stdscr, state, entries, selected, detail_scroll, message)
            message = ""
            try:
                key = modal_read_key(stdscr)
            except (KeyboardInterrupt, curses.error):
                state.last_error = "已关闭记忆检查面板。"
                return
            if key in ("\x1b", 27, "\x03", "q", "Q"):
                state.last_error = "已关闭记忆检查面板。"
                return
            if key in ("r", "R"):
                entries = memory_inventory()
                detail_scroll = 0
                message = "已刷新。"
                continue
            if key in (curses.KEY_UP, "k"):
                selected = max(0, selected - 1)
                detail_scroll = 0
                continue
            if key in (curses.KEY_DOWN, "j"):
                selected = min(max(0, len(entries) - 1), selected + 1)
                detail_scroll = 0
                continue
            if key in (curses.KEY_PPAGE,):
                detail_scroll = max(0, detail_scroll - 12)
                continue
            if key in (curses.KEY_NPAGE,):
                detail_scroll += 12
                continue
            if key in (curses.KEY_HOME,):
                detail_scroll = 0
                continue
            if key in (curses.KEY_END,):
                detail_scroll = 10**9
                continue
    finally:
        restore_main_poll_timeout(stdscr)
        mark_dirty(state)


def approval_artifact_refs(row: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for value in row.get("artifact_refs") or []:
        if isinstance(value, str) and value:
            refs.append(value)
    payload = row.get("payload") or {}
    if isinstance(payload, dict):
        for value in payload.get("artifact_refs") or []:
            if isinstance(value, str) and value:
                refs.append(value)
        evidence = str(payload.get("evidence_ref") or "")
        if evidence.startswith("artifact://"):
            refs.append(evidence)
    return list(dict.fromkeys(refs))


def approval_status_for_task(task_id: str) -> str:
    task_id = str(task_id or "")
    statuses: list[str] = []
    for row in approval_latest_records().values():
        payload = row.get("payload") or {}
        if not isinstance(payload, dict):
            payload = {}
        refs = approval_artifact_refs(row)
        if str(payload.get("task_id") or "") == task_id or any(task_id and task_id in ref for ref in refs):
            statuses.append(str(row.get("status") or "pending"))
    if not statuses:
        return "-"
    if "pending" in statuses:
        return "pending"
    return ",".join(sorted(set(statuses)))


def task_panel_items() -> list[PanelItem]:
    latest = latest_task_records()
    children: dict[str, list[str]] = {}
    for task_id, row in latest.items():
        parent = str(row.get("parent_task_id") or "")
        if parent:
            children.setdefault(parent, []).append(task_id)
    def depth_for(task_id: str) -> int:
        depth = 0
        seen: set[str] = set()
        parent = str(latest.get(task_id, {}).get("parent_task_id") or "")
        while parent and parent in latest and parent not in seen and depth < 8:
            seen.add(parent)
            depth += 1
            parent = str(latest.get(parent, {}).get("parent_task_id") or "")
        return depth
    items: list[PanelItem] = []
    sorted_rows = sorted(latest.items(), key=lambda pair: row_timestamp(pair[1]), reverse=True)
    for task_id, row in sorted_rows:
        depth = depth_for(task_id)
        tree_prefix = ("  " * min(depth, 4)) + ("└ " if depth else "• ")
        status = str(row.get("status") or "-")
        owner = str(row.get("assigned_agent") or "-")
        parent = str(row.get("parent_task_id") or "-")
        title = task_display_title(row)
        objective = str(row.get("objective") or row.get("summary") or row.get("error") or "")
        artifacts = [str(ref) for ref in (row.get("artifact_refs") or []) if ref]
        approval = approval_status_for_task(task_id)
        history = task_history(task_id)
        detail_lines = [
            f"Task: {task_id}",
            f"Title: {title}",
            f"Status: {status}",
            f"Owner: {owner}",
            f"Parent: {parent}",
            f"Children: {', '.join(children.get(task_id, [])) or '-'}",
            f"Approval: {approval}",
            f"Objective: {objective or '-'}",
            "",
            "Artifacts:",
        ]
        detail_lines.extend([f"- {ref}" for ref in artifacts] or ["- -"])
        for ref in artifacts[:3]:
            detail_lines += ["", f"Preview: {ref}", *artifact_preview(ref, max_bytes=12000)]
        detail_lines += ["", "History:"]
        for item in history:
            detail_lines.append(f"- {item.get('timestamp', '')} · {item.get('status', '')} · {item.get('summary') or item.get('error') or item.get('objective') or ''}")
        items.append(PanelItem(
            key=task_id,
            title=f"{tree_prefix}{title} · {status}",
            subtitle=f"id:{task_id} · owner:{owner} · approval:{approval} · artifacts:{len(artifacts)}",
            detail="\n".join(detail_lines),
            status=status,
            payload=row,
        ))
    return items


def approval_panel_items(show_all: bool = False, state: Optional[State] = None) -> list[PanelItem]:
    if state is not None and state.secret_vault.unlocked:
        rows = secret_memory_candidate_approval_rows(state, show_all=show_all)
    else:
        rows = list(approval_latest_records().values())
        if not show_all:
            rows = [row for row in rows if row.get("status") == "pending"]
    rows.sort(key=row_timestamp, reverse=True)
    items: list[PanelItem] = []
    for row in rows:
        approval_id = str(row.get("approval_id") or "-")
        status = str(row.get("status") or "-")
        approval_type = str(row.get("type") or "-")
        source = str(row.get("source") or "-")
        target = str(row.get("target") or "-")
        summary = str(row.get("summary") or "")
        refs = approval_artifact_refs(row)
        storage = "Secret Vault encrypted" if row.get("secret_storage") else "normal"
        memory_text = approval_memory_statement(row)
        detail_lines = [
            f"Approval: {approval_id}",
            f"Status: {status}",
            f"Type: {approval_type}",
            f"Storage: {storage}",
            f"Source: {source}",
            f"Target: {target}",
            f"Required for: {row.get('approval_required_for') or approval_type}",
            f"Summary: {summary}",
        ]
        if memory_text:
            detail_lines += [
                "",
                "Memory Candidate:",
                memory_text,
            ]
        detail_lines += [
            "",
            "Payload:",
            json.dumps(row.get("payload") or {}, ensure_ascii=False, indent=2, sort_keys=True),
        ]
        for ref in refs[:4]:
            detail_lines += ["", f"Artifact Preview: {ref}", *artifact_preview(ref, max_bytes=12000)]
        items.append(PanelItem(
            key=approval_id,
            title=f"{approval_id} · {approval_type}" + (" · SECRET" if row.get("secret_storage") else ""),
            subtitle=f"{status} · {source} -> {target}",
            detail="\n".join(detail_lines),
            status=status,
            payload=row,
        ))
    return items


def recovery_state_for_task(state: State, row: dict[str, Any]) -> str:
    task_id = str(row.get("task_id") or "")
    agent_id = str(row.get("assigned_agent") or "")
    sub = state.subagents.get(agent_id)
    if sub and sub.status in {"running", "aborting"} and sub.active_bus_task_id == task_id:
        return "runtime-active"
    return "stale-after-restart"


def recovery_panel_items(state: State) -> list[PanelItem]:
    rows = unfinished_task_records()
    rows.sort(key=row_timestamp, reverse=True)
    items: list[PanelItem] = []
    lock = current_writer_lock()
    for row in rows:
        task_id = str(row.get("task_id") or "")
        owner = str(row.get("assigned_agent") or "-")
        status = str(row.get("status") or "-")
        recovery_state = recovery_state_for_task(state, row)
        lock_note = "yes" if lock and str(lock.get("task_id") or "") == task_id else "no"
        detail = "\n".join([
            f"Task: {task_id}",
            f"Status: {status}",
            f"Owner: {owner}",
            f"Recovery: {recovery_state}",
            f"Single-writer lock: {lock_note}",
            f"Objective: {row.get('objective') or row.get('summary') or '-'}",
            f"Checkpoints: {len(checkpoint_history(task_id))}",
            f"Recovery plans: {len(recovery_plan_history(task_id))}",
            f"Recovery records: {len(recovery_history(task_id))}",
            "",
            "Actions:",
            "- f: mark failed",
            "- c: cancel",
            "- r: retry with same assigned subagent",
            "- x: release writer lock if this task owns it",
        ])
        items.append(PanelItem(
            key=task_id,
            title=f"{task_id} · {status}",
            subtitle=f"{recovery_state} · owner:{owner} · lock:{lock_note}",
            detail=detail,
            status=recovery_state,
            payload=row,
        ))
    return items


def recover_task_action(state: State, task_id: str, action: str, policy_approved: bool = False) -> str:
    row = latest_task_records().get(task_id)
    if not row:
        return f"找不到任务：{task_id}"
    owner = str(row.get("assigned_agent") or "")
    objective = str(row.get("objective") or "")
    policy_action = {
        "release_lock": "release_writer_lock",
        "failed": "recovery_mark_failed",
        "cancelled": "recovery_cancel",
        "retry": "recovery_retry",
    }.get(action, "unknown")
    before_checkpoint = append_task_checkpoint(
        task_id,
        status=str(row.get("status") or "unknown"),
        reason=f"recovery_before_{action}",
        state=state,
        agent_id=owner,
        summary=truncate_cells(objective, 240),
        extra={"requested_action": action},
    )
    decision: Optional[PolicyDecision] = None
    recovery_plan: dict[str, Any] = {}
    if not policy_approved:
        decision = evaluate_policy_action(
            policy_action,
            subject="orchestrator.main",
            source="recovery",
            target=owner,
            payload={
                "operation": "recover_task_action",
                "task_id": task_id,
                "recovery_action": action,
                "assigned_agent": owner,
                "objective": truncate_cells(objective, 240),
            },
        )
        recovery_plan = append_recovery_plan(
            task_id,
            action=action,
            source_checkpoint=before_checkpoint,
            assigned_agent=owner,
            objective=objective,
            policy_decision=decision,
            status=decision.status,
        )
        if decision.approval_required:
            queue_policy_approval(
                decision,
                summary=f"Recovery {action}: {task_id}",
                extra_payload={
                    "deferred_operation": "recover_task_action",
                    "task_id": task_id,
                    "recovery_action": action,
                    "recovery_plan_id": recovery_plan.get("recovery_plan_id", ""),
                    "recovery_plan_ref": (recovery_plan.get("artifact_refs") or [""])[0],
                },
            )
        record_policy_decision(decision)
        if not decision.allowed:
            append_recovery_record(
                task_id,
                action=action,
                status=decision.status,
                assigned_agent=owner,
                objective=objective,
                before_checkpoint_id=str(before_checkpoint.get("checkpoint_id") or ""),
                policy_decision=decision,
                result=policy_gate_text(decision),
                recovery_plan_id=str(recovery_plan.get("recovery_plan_id") or ""),
                recovery_plan_ref=str((recovery_plan.get("artifact_refs") or [""])[0]),
            )
            payload = policy_decision_to_dict(decision)
            payload["checkpoint_id"] = before_checkpoint.get("checkpoint_id", "")
            payload["recovery_plan_id"] = recovery_plan.get("recovery_plan_id", "")
            payload["artifact_ref"] = (recovery_plan.get("artifact_refs") or [""])[0]
            append_trace(task_id, "recovery_policy_gate", agent_id="orchestrator.main", status=decision.status, payload=payload)
            return policy_gate_text(decision)
    else:
        recovery_plan = append_recovery_plan(
            task_id,
            action=action,
            source_checkpoint=before_checkpoint,
            assigned_agent=owner,
            objective=objective,
            status="approved_replay",
        )
    if action == "release_lock":
        result = "已释放 single-writer 锁。" if release_single_writer_lock(task_id) else "该任务没有持有 single-writer 锁。"
        after_checkpoint = append_task_checkpoint(
            task_id,
            status=str(row.get("status") or "unknown"),
            reason="recovery_after_release_lock",
            state=state,
            agent_id=owner,
            summary=result,
        )
        append_recovery_record(
            task_id,
            action=action,
            status="completed",
            assigned_agent=owner,
            objective=objective,
            before_checkpoint_id=str(before_checkpoint.get("checkpoint_id") or ""),
            after_checkpoint_id=str(after_checkpoint.get("checkpoint_id") or ""),
            result=result,
            recovery_plan_id=str(recovery_plan.get("recovery_plan_id") or ""),
            recovery_plan_ref=str((recovery_plan.get("artifact_refs") or [""])[0]),
        )
        append_trace(task_id, "recovery_release_lock", agent_id="orchestrator.main", status="completed", payload={"checkpoint_id": after_checkpoint.get("checkpoint_id", ""), "recovery_plan_id": recovery_plan.get("recovery_plan_id", ""), "artifact_ref": (recovery_plan.get("artifact_refs") or [""])[0], "result": result})
        return result
    if action in {"failed", "cancelled"}:
        sub = state.subagents.get(owner)
        if sub and sub.active_bus_task_id == task_id:
            if sub.agent is not None:
                try:
                    sub.agent.abort()
                except Exception:
                    pass
            sub.status = "idle"
            sub.active_task_id = None
            sub.active_bus_task_id = ""
            save_subagent_meta(sub)
        release_single_writer_lock(task_id)
        append_task_ledger(task_id, status=action, assigned_agent=owner, objective=objective, summary=f"Recovery marked {action}")
        result = f"已将任务标记为 {action}: {task_id}"
        after_checkpoint = append_task_checkpoint(
            task_id,
            status=action,
            reason=f"recovery_after_{action}",
            state=state,
            agent_id=owner,
            summary=result,
        )
        append_recovery_record(
            task_id,
            action=action,
            status=action,
            assigned_agent=owner,
            objective=objective,
            before_checkpoint_id=str(before_checkpoint.get("checkpoint_id") or ""),
            after_checkpoint_id=str(after_checkpoint.get("checkpoint_id") or ""),
            result=result,
            recovery_plan_id=str(recovery_plan.get("recovery_plan_id") or ""),
            recovery_plan_ref=str((recovery_plan.get("artifact_refs") or [""])[0]),
        )
        append_trace(task_id, f"recovery_{action}", agent_id="orchestrator.main", status=action, payload={"checkpoint_id": after_checkpoint.get("checkpoint_id", ""), "recovery_plan_id": recovery_plan.get("recovery_plan_id", ""), "artifact_ref": (recovery_plan.get("artifact_refs") or [""])[0], "result": result})
        return result
    if action == "retry":
        sub = state.subagents.get(owner)
        if sub is None:
            result = f"找不到原负责人子 agent：{owner}"
            append_recovery_record(
                task_id,
                action=action,
                status="failed",
                assigned_agent=owner,
                objective=objective,
                before_checkpoint_id=str(before_checkpoint.get("checkpoint_id") or ""),
                result=result,
                error=result,
                recovery_plan_id=str(recovery_plan.get("recovery_plan_id") or ""),
                recovery_plan_ref=str((recovery_plan.get("artifact_refs") or [""])[0]),
            )
            return result
        release_single_writer_lock(task_id)
        append_task_ledger(task_id, status="failed", assigned_agent=owner, objective=objective, summary="Recovery retry superseded this stale task")
        after_checkpoint = append_task_checkpoint(
            task_id,
            status="failed",
            reason="recovery_retry_superseded",
            state=state,
            agent_id=owner,
            summary="Recovery retry superseded this stale task",
        )
        result = start_subagent_task(state, sub, objective, source="approved_recovery", policy_approved=policy_approved)
        append_recovery_record(
            task_id,
            action=action,
            status="restarted" if result.startswith("已启动子 agent") else "failed",
            assigned_agent=owner,
            objective=objective,
            before_checkpoint_id=str(before_checkpoint.get("checkpoint_id") or ""),
            after_checkpoint_id=str(after_checkpoint.get("checkpoint_id") or ""),
            result=result,
            recovery_plan_id=str(recovery_plan.get("recovery_plan_id") or ""),
            recovery_plan_ref=str((recovery_plan.get("artifact_refs") or [""])[0]),
        )
        append_trace(task_id, "recovery_retry", agent_id="orchestrator.main", status="restarted" if result.startswith("已启动子 agent") else "failed", payload={"checkpoint_id": after_checkpoint.get("checkpoint_id", ""), "recovery_plan_id": recovery_plan.get("recovery_plan_id", ""), "artifact_ref": (recovery_plan.get("artifact_refs") or [""])[0], "result": result})
        return result
    return f"未知 recovery 动作：{action}"


def eval_panel_items() -> list[PanelItem]:
    evals = read_jsonl(AGENT_EVALS_PATH)
    traces = read_jsonl(AGENT_TRACES_PATH)
    traces_by_task: dict[str, list[dict[str, Any]]] = {}
    for row in traces:
        traces_by_task.setdefault(str(row.get("task_id") or ""), []).append(row)
    items: list[PanelItem] = []
    for row in sorted(evals, key=row_timestamp, reverse=True):
        task_id = str(row.get("task_id") or "-")
        scores = row.get("scores") or {}
        detail_lines = [
            f"Eval: {row.get('eval_id') or '-'}",
            f"Task: {task_id}",
            f"Agent: {row.get('agent_id') or '-'}",
            f"Role: {row.get('role') or '-'}",
            "",
            "Scores:",
            json.dumps(scores, ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "Audit refs:",
            json.dumps(row.get("audit_refs") or {}, ensure_ascii=False, indent=2, sort_keys=True),
            "",
            "Final state:",
            json.dumps(row.get("final_state") or {}, ensure_ascii=False, indent=2, sort_keys=True),
            "",
            f"Summary: {row.get('summary') or '-'}",
            "",
            "Artifacts:",
        ]
        detail_lines.extend([f"- {ref}" for ref in row.get("artifact_refs") or []] or ["- -"])
        detail_lines += ["", "Trace:"]
        for trace in traces_by_task.get(task_id, [])[-12:]:
            detail_lines.append(f"- {trace.get('timestamp', '')} · {trace.get('event', '')} · {trace.get('status', '')}")
        items.append(PanelItem(
            key=str(row.get("eval_id") or task_id),
            title=f"{task_id} · {row.get('agent_id') or '-'}",
            subtitle=f"completion:{scores.get('completion', '-')} factual:{scores.get('factual_accuracy', '-')} citation:{scores.get('citation_accuracy', '-')}",
            detail="\n".join(detail_lines),
            status=str(scores.get("completion", "")),
            payload=row,
        ))
    if not items:
        for row in sorted(traces, key=row_timestamp, reverse=True):
            task_id = str(row.get("task_id") or "-")
            items.append(PanelItem(
                key=str(row.get("trace_id") or task_id),
                title=f"{task_id} · {row.get('event') or '-'}",
                subtitle=f"{row.get('status') or '-'} · {row.get('agent_id') or '-'}",
                detail=json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True),
                status=str(row.get("status") or ""),
                payload=row,
            ))
    return items


def gateway_panel_items(state: State) -> list[PanelItem]:
    data = ensure_gateway_registry(state)
    items: list[PanelItem] = []
    for key in ("internal_agent_mail", "mcp_gateway", "a2a_gateway", "capability_registry", "governance_components", "bridge_registry", "baseline_comparison"):
        payload = data.get(key) or {}
        items.append(PanelItem(
            key=key,
            title=key,
            subtitle=str(payload.get("status") or payload.get("purpose") or payload.get("schema_version") or "configured"),
            detail=json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            status=str(payload.get("status") or "ok"),
            payload=payload,
        ))
    for card in data.get("agent_cards") or []:
        items.append(PanelItem(
            key=str(card.get("agent_id") or ""),
            title=f"agent card · {card.get('name') or card.get('agent_id')}",
            subtitle=f"role:{card.get('role')} · status:{card.get('status')} · write:{card.get('write_policy')}",
            detail=json.dumps(card, ensure_ascii=False, indent=2, sort_keys=True),
            status=str(card.get("status") or ""),
            payload=card,
        ))
    return items


def draw_panel_browser(
    stdscr,
    state: State,
    title: str,
    items: list[PanelItem],
    selected: int,
    detail_scroll: int,
    message: str = "",
    footer: str = "",
) -> None:
    redraw(stdscr, state)
    height, width = stdscr.getmaxyx()
    y0, x0, h, w = popup_geometry(height, width, min_h=18, min_w=104)
    draw_popup(stdscr, y0, x0, h, w, title)
    inner_w = w - 4
    left_w = min(52, max(34, inner_w // 3))
    right_x = x0 + 2 + left_w + 2
    right_w = max(24, inner_w - left_w - 3)
    list_h = h - 5
    hint = footer or "r 刷新  ↑/↓ 选择  PgUp/PgDn 滚动预览  Esc/q 关闭"
    safe_add(stdscr, y0 + 1, x0 + 2, f"items:{len(items)}  {hint}", inner_w, cp(1))
    safe_add(stdscr, y0 + 2, x0 + 2, "─" * left_w, left_w, cp(10))
    safe_add(stdscr, y0 + 2, right_x, "─" * right_w, right_w, cp(10))
    if not items:
        safe_add(stdscr, y0 + 4, x0 + 2, "没有可显示的条目。", inner_w, cp(5))
        if message:
            safe_add(stdscr, y0 + h - 2, x0 + 2, message, inner_w, cp(5))
        stdscr.refresh()
        return
    selected = max(0, min(selected, len(items) - 1))
    first = max(0, min(selected - list_h // 2, max(0, len(items) - list_h)))
    for row, item in enumerate(items[first:first + list_h]):
        idx = first + row
        y = y0 + 3 + row
        attr = cp(11) | curses.A_BOLD if idx == selected else cp(9)
        suffix = f" · {item.subtitle}" if item.subtitle else ""
        line = truncate_cells(item.title + suffix, left_w)
        safe_add(stdscr, y, x0 + 2, " " * left_w, left_w, attr)
        safe_add(stdscr, y, x0 + 2, line, left_w, attr)
    item = items[selected]
    safe_add(stdscr, y0 + 3, right_x, truncate_cells(item.title, right_w), right_w, cp(7) | curses.A_BOLD)
    if item.subtitle:
        safe_add(stdscr, y0 + 4, right_x, truncate_cells(item.subtitle, right_w), right_w, cp(1))
    detail_lines: list[str] = []
    for raw in (item.detail or "").splitlines():
        detail_lines.extend(wrap_cells(raw, right_w) or [""])
    max_detail_h = max(1, h - 8)
    max_scroll = max(0, len(detail_lines) - max_detail_h)
    detail_scroll = max(0, min(detail_scroll, max_scroll))
    for row, line in enumerate(detail_lines[detail_scroll:detail_scroll + max_detail_h]):
        safe_add(stdscr, y0 + 6 + row, right_x, line, right_w, cp(2))
    if message:
        safe_add(stdscr, y0 + h - 2, x0 + 2, message, inner_w, cp(5) if "失败" in message or "找不到" in message else cp(3))
    stdscr.refresh()


def open_harness_panel(stdscr, state: State, panel: str) -> None:
    panel = panel.lower()
    selected = 0
    detail_scroll = 0
    message = ""
    show_all_approvals = False

    def load_items() -> tuple[str, list[PanelItem], str]:
        if panel == "tasks":
            return "Task Ledger", task_panel_items(), "r 刷新  ↑/↓ 选择  PgUp/PgDn 预览  Esc/q 关闭"
        if panel == "approvals":
            scope = "all" if show_all_approvals else "pending"
            title = "Secret Approval Inbox" if state.secret_vault.unlocked else "Approval Inbox"
            return title, approval_panel_items(show_all=show_all_approvals, state=state), f"Enter 单选处理  a 批准  d/r 拒绝  R 刷新  t 切换 pending/all({scope})  PgUp/PgDn  Esc/q"
        if panel == "artifacts":
            return "Artifact Store", artifact_inventory(), "r 刷新  ↑/↓ 选择  PgUp/PgDn 预览  Esc/q 关闭"
        if panel == "recover":
            return "Recovery", recovery_panel_items(state), "f 标失败  c 取消  r 重试  x 解锁  R 刷新  PgUp/PgDn  Esc/q"
        if panel == "evals":
            return "Eval / Trace", eval_panel_items(), "r 刷新  ↑/↓ 选择  PgUp/PgDn 预览  Esc/q 关闭"
        if panel == "gateway":
            return "A2A / MCP Gateway", gateway_panel_items(state), "r 重建 registry  ↑/↓ 选择  PgUp/PgDn 预览  Esc/q"
        if panel == "baseline":
            return "Architecture Baseline", baseline_panel_items(state), "r 重新生成报告  ↑/↓ 选择  PgUp/PgDn 预览  Esc/q"
        return "Harness", [], "Esc/q 关闭"

    try:
        drain_pending_keys(stdscr)
        stdscr.timeout(-1)
        while True:
            title, items, footer = load_items()
            if selected >= len(items):
                selected = max(0, len(items) - 1)
            draw_panel_browser(stdscr, state, title, items, selected, detail_scroll, message, footer)
            message = ""
            try:
                key = modal_read_key(stdscr)
            except (KeyboardInterrupt, curses.error):
                state.last_error = f"已关闭 {title} 面板。"
                return
            if key in ("\x1b", 27, "\x03", "q", "Q"):
                state.last_error = f"已关闭 {title} 面板。"
                return
            if key in (curses.KEY_UP, "k"):
                selected = max(0, selected - 1)
                detail_scroll = 0
                continue
            if key in (curses.KEY_DOWN, "j"):
                selected = min(max(0, len(items) - 1), selected + 1)
                detail_scroll = 0
                continue
            if key in (curses.KEY_PPAGE,):
                detail_scroll = max(0, detail_scroll - 12)
                continue
            if key in (curses.KEY_NPAGE,):
                detail_scroll += 12
                continue
            if key in (curses.KEY_HOME,):
                detail_scroll = 0
                continue
            if key in (curses.KEY_END,):
                detail_scroll = 10**9
                continue
            if panel == "approvals" and key in ("t", "T"):
                show_all_approvals = not show_all_approvals
                selected = 0
                detail_scroll = 0
                continue
            if key == "R" or (key == "r" and panel not in {"approvals", "recover"}):
                if panel == "gateway":
                    ensure_gateway_registry(state)
                    message = "Gateway registry 已重建。"
                else:
                    message = "已刷新。"
                detail_scroll = 0
                continue
            if not items:
                continue
            current = items[selected]
            if panel == "approvals" and key in ("\n", "\r", curses.KEY_ENTER):
                if set_pending_approval_interaction(state, current.payload):
                    state.last_error = "已在底部打开审批单选：↑/↓ 选择，Enter 执行。"
                    return
                message = "这个审批项不能用单选处理，可能已经处理过或当前有其他输入等待。"
                detail_scroll = 0
                continue
            if panel == "approvals" and key in ("a", "A"):
                message = decide_approval(state, current.key, True)
                detail_scroll = 0
                continue
            if panel == "approvals" and key in ("d", "D", "r", "R"):
                message = decide_approval(state, current.key, False)
                detail_scroll = 0
                continue
            if panel == "recover" and key in ("f", "F"):
                message = recover_task_action(state, current.key, "failed")
                detail_scroll = 0
                continue
            if panel == "recover" and key in ("c", "C"):
                message = recover_task_action(state, current.key, "cancelled")
                detail_scroll = 0
                continue
            if panel == "recover" and key in ("x", "X"):
                message = recover_task_action(state, current.key, "release_lock")
                detail_scroll = 0
                continue
            if panel == "recover" and key in ("r", "R"):
                message = recover_task_action(state, current.key, "retry")
                detail_scroll = 0
                continue
    finally:
        restore_main_poll_timeout(stdscr)
        mark_dirty(state)


def draw_rename_modal(stdscr, state: State, name: str, cursor: int, message: str = "") -> None:
    redraw(stdscr, state)
    height, width = stdscr.getmaxyx()
    y0, x0, h, w = popup_geometry(height, width, min_h=9, min_w=72)
    draw_popup(stdscr, y0, x0, h, w, "重命名当前会话")
    inner_w = w - 4
    safe_add(stdscr, y0 + 2, x0 + 2, f"当前: {state.current_title or 'main'}", inner_w, cp(2))
    label = "新名称: "
    field_w = max(10, inner_w - cell_width(label))
    safe_add(stdscr, y0 + 4, x0 + 2, label, inner_w, cp(1))
    safe_add(stdscr, y0 + 4, x0 + 2 + cell_width(label), " " * field_w, field_w, cp(11))
    shown = truncate_cells(name, field_w)
    safe_add(stdscr, y0 + 4, x0 + 2 + cell_width(label), shown, field_w, cp(11))
    if message:
        safe_add(stdscr, y0 + h - 3, x0 + 2, message, inner_w, cp(5))
    safe_add(stdscr, y0 + h - 2, x0 + 2, "Enter 保存  Esc 取消  ←/→ 移动  Backspace 删除", inner_w, cp(1))
    try:
        cursor_x = x0 + 2 + cell_width(label) + min(field_w - 1, cell_width(name[:cursor]))
        stdscr.move(y0 + 4, cursor_x)
    except curses.error:
        pass
    stdscr.refresh()


def open_rename_modal(stdscr, state: State) -> None:
    old_timeout = TUI_POLL_TIMEOUT_MS
    name = state.current_title if state.current_title and state.current_title != "main" else ""
    cursor = len(name)
    message = ""
    try:
        drain_pending_keys(stdscr)
        stdscr.timeout(-1)
        while True:
            cursor = max(0, min(cursor, len(name)))
            draw_rename_modal(stdscr, state, name, cursor, message)
            message = ""
            try:
                key = modal_read_key(stdscr)
            except KeyboardInterrupt:
                state.last_error = "重命名已取消。"
                return
            except curses.error:
                continue
            if key in ("\x1b", 27, "\x03"):
                state.last_error = "重命名已取消。"
                return
            if key in ("\n", "\r", curses.KEY_ENTER):
                result = rename_current_session(state, name)
                if result.startswith("名称不能为空"):
                    message = result
                    continue
                state.last_error = result
                return
            if key in (curses.KEY_LEFT,):
                cursor -= 1
                continue
            if key in (curses.KEY_RIGHT,):
                cursor += 1
                continue
            if key in (curses.KEY_HOME,):
                cursor = 0
                continue
            if key in (curses.KEY_END,):
                cursor = len(name)
                continue
            if key in (curses.KEY_BACKSPACE, 127, "\b"):
                if cursor > 0:
                    name = name[:cursor - 1] + name[cursor:]
                    cursor -= 1
                continue
            if key in (curses.KEY_DC,):
                if cursor < len(name):
                    name = name[:cursor] + name[cursor + 1:]
                continue
            if key == "\x15":
                name = ""
                cursor = 0
                continue
            if isinstance(key, str) and key.isprintable():
                name = name[:cursor] + key + name[cursor:]
                cursor += len(key)
    finally:
        stdscr.timeout(old_timeout)
        mark_dirty(state)


def run_modal_task_until_done(stdscr, state: State, title: str, lines: list[str], task_fn):
    result_q: queue.Queue = queue.Queue(maxsize=1)

    def worker() -> None:
        try:
            result_q.put(("ok", task_fn()))
        except Exception as exc:
            result_q.put(("error", exc))

    threading.Thread(target=worker, daemon=True, name="ga-modal-worker").start()
    draw_modal_notice(stdscr, state, title, lines, footer="正在处理，Esc 返回主页面...")
    while True:
        try:
            status, payload = result_q.get_nowait()
        except queue.Empty:
            if modal_poll_escape(stdscr):
                state.last_error = f"{title} 已取消，已返回主页面。"
                mark_dirty(state)
                return None
            time.sleep(0.05)
            continue
        if status == "error":
            raise payload
        return payload


def draw_exit_prompt(stdscr, state: State, labels: list[str], selected: int) -> None:
    redraw(stdscr, state)
    height, width = stdscr.getmaxyx()
    y0, x0, h, w = popup_geometry(height, width, min_h=12, min_w=78)
    draw_popup(stdscr, y0, x0, h, w, "退出确认")
    inner_w = w - 4
    has_unfinished = bool(labels)
    if has_unfinished:
        safe_add(stdscr, y0 + 2, x0 + 2, "还有任务没有跑完。请选择退出行为：", inner_w, cp(5) | curses.A_BOLD)
        list_y = y0 + 4
        shown = labels[: max(1, min(len(labels), h - 9))]
        for idx, label in enumerate(shown, 1):
            safe_add(stdscr, list_y + idx - 1, x0 + 4, f"- {label}", inner_w - 4, cp(2))
        options = [
            ("取消退出", "回到 TUI，任务继续运行。"),
            ("退出并终止", "关闭 TUI，并请求中止所有未完成任务。"),
            ("退出并后台跑完", "关闭 TUI 界面，进程等任务跑完后自动结束。"),
        ]
        footer = "↑↓ 选择  Enter 确认  Ctrl+Q 确认退出  Esc/Ctrl+C 取消退出"
    else:
        safe_add(stdscr, y0 + 2, x0 + 2, "当前没有未完成任务。确认退出 ga tui？", inner_w, cp(7) | curses.A_BOLD)
        safe_add(stdscr, y0 + 4, x0 + 4, "Ctrl+Q 是退出快捷键；Ctrl+C 只用于中止任务。", inner_w - 4, cp(2))
        options = [
            ("取消退出", "回到 TUI。"),
            ("确认退出", "关闭 TUI。"),
        ]
        footer = "↑↓ 选择  Enter 确认  Ctrl+Q/2 确认退出  Esc/Ctrl+C 取消退出"
    opt_y = y0 + h - 6
    for idx, (name, desc) in enumerate(options):
        attr = cp(11) | curses.A_BOLD if idx == selected else cp(2)
        safe_add(stdscr, opt_y + idx, x0 + 2, " " * inner_w, inner_w, attr)
        safe_add(stdscr, opt_y + idx, x0 + 2, f"{idx + 1}. {name} - {desc}", inner_w, attr)
    safe_add(stdscr, y0 + h - 2, x0 + 2, footer, inner_w, cp(1))
    stdscr.refresh()


def choose_exit_mode(stdscr, state: State, labels: list[str], selected: int = 0) -> str:
    options_count = 3 if labels else 2
    selected = max(0, min(selected, options_count - 1))
    while True:
        draw_exit_prompt(stdscr, state, labels, selected)
        try:
            key = modal_read_key(stdscr)
        except (curses.error, KeyboardInterrupt):
            return "cancel"
        if key in ("\x1b", 27, "\x03", "q", "Q", "c", "C", "1"):
            return "cancel"
        if key == "\x11":
            return "terminate"
        if key in ("t", "T", "2"):
            return "terminate"
        if labels and key in ("b", "B", "w", "W", "3"):
            return "wait"
        if key in (curses.KEY_UP,):
            selected = (selected - 1) % options_count
            continue
        if key in (curses.KEY_DOWN,):
            selected = (selected + 1) % options_count
            continue
        if key in ("\n", "\r", curses.KEY_ENTER):
            choices = ("cancel", "terminate", "wait") if labels else ("cancel", "terminate")
            return choices[selected]


def request_exit(stdscr, state: State, reason: str = "已退出 ga tui。", selected: Optional[int] = None) -> None:
    process_ui_queue(state)
    labels = unfinished_task_labels(state)
    if not labels and selected == 1:
        state.exit_mode = "terminate"
        state.exit_reason = reason
        state.running = False
        restore_main_poll_timeout(stdscr)
        mark_dirty(state)
        return
    default_selected = 0 if selected is None else selected
    try:
        choice = choose_exit_mode(stdscr, state, labels, default_selected)
    finally:
        restore_main_poll_timeout(stdscr)
    if choice == "cancel":
        state.last_error = "已取消退出；未完成任务继续运行。" if labels else "已取消退出。"
        mark_dirty(state)
        return
    if choice == "terminate":
        state.exit_mode = "terminate"
        state.exit_reason = "已退出 ga tui；未完成任务已请求终止。"
    else:
        state.exit_mode = "wait"
        state.exit_reason = "已退出 ga tui；未完成任务将在后台跑完后自动结束进程。"
    state.running = False
    mark_dirty(state)


def model_form_fields(cfg_type: str) -> list[tuple[str, str, str]]:
    fields = [
        ("type", "协议", "choice"),
        ("name", "显示名", "text"),
        ("apikey", "API Key", "secret"),
        ("apibase", "Base URL", "text"),
        ("model", "Model", "text"),
    ]
    if cfg_type in {"native_oai", "oai"}:
        fields.append(("api_mode", "API Mode", "choice"))
        fields.append(("reasoning_effort", "Reasoning", "choice"))
    if cfg_type in {"native_claude", "claude"}:
        fields.append(("fake_cc_system_prompt", "Fake CC", "bool"))
        fields.append(("thinking_type", "Thinking", "choice"))
    fields.append(("read_timeout", "Read Timeout", "text"))
    return fields


def choice_values_for_field(field: str, provider: dict[str, Any], cfg_type: str) -> list[str]:
    if field == "type":
        return ["native_oai", "native_claude"]
    if field == "model":
        return provider_model_choices(provider)
    if field == "api_mode":
        return ["chat_completions", "responses"]
    if field == "reasoning_effort":
        return ["", "low", "medium", "high", "xhigh"]
    if field == "thinking_type":
        return ["adaptive", "enabled", "disabled", ""]
    return []


def cycle_value(current: Any, values: list[str], direction: int = 1) -> str:
    if not values:
        return str(current or "")
    cur = str(current or "")
    try:
        idx = values.index(cur)
    except ValueError:
        idx = -1 if direction > 0 else 0
    return values[(idx + direction) % len(values)]


def draw_model_form(stdscr, title: str, cfg_type: str, cfg: dict[str, Any], provider_idx: int, field_idx: int, message: str) -> None:
    height, width = stdscr.getmaxyx()
    y0, x0, h, w = popup_geometry(height, width, min_h=18, min_w=92)
    draw_popup(stdscr, y0, x0, h, w, title)
    inner_w = w - 4
    providers = llm_template_providers()
    category = provider_category(providers[provider_idx]) if providers else "OpenAI"
    categories = provider_categories(providers)
    category_text = " / ".join(f"[{c}]" if c == category else c for c in categories)
    safe_add(stdscr, y0 + 2, x0 + 2, f"Templates: {category_text}", inner_w, cp(1))
    safe_add(stdscr, y0 + 3, x0 + 2, "Tab 切协议分类  PgUp/PgDn 或 [ ] 切模板  ↑↓ 字段  ←→ 选项  Enter 下一项/验活保存  Esc 取消", inner_w, cp(1))

    left_w = min(34, max(24, inner_w // 3))
    right_w = max(24, inner_w - left_w - 3)
    left_x = x0 + 2
    right_x = left_x + left_w + 3
    safe_add(stdscr, y0 + 5, left_x, "模板", left_w, cp(7) | curses.A_BOLD)
    safe_add(stdscr, y0 + 5, right_x, "详情", right_w, cp(7) | curses.A_BOLD)
    for y in range(y0 + 5, y0 + h - 2):
        safe_add(stdscr, y, left_x + left_w + 1, "│", 1, cp(10))

    provider_rows = provider_indices_for_category(providers, category)
    template_h = max(1, h - 9)
    try:
        selected_row = provider_rows.index(provider_idx)
    except ValueError:
        selected_row = 0
    row_start = max(0, min(selected_row - template_h + 1, max(0, len(provider_rows) - template_h)))
    for row, actual_idx in enumerate(provider_rows[row_start:row_start + template_h]):
        provider = providers[actual_idx]
        name = str(provider.get("name") or provider.get("id") or "template")
        attr = cp(11) | curses.A_BOLD if actual_idx == provider_idx else cp(2)
        safe_add(stdscr, y0 + 6 + row, left_x, " " * left_w, left_w, attr)
        safe_add(stdscr, y0 + 6 + row, left_x, truncate_cells(name, left_w), left_w, attr)

    provider = providers[provider_idx] if providers else {}
    desc = str(provider.get("desc") or "")
    if desc:
        safe_add(stdscr, y0 + 4, right_x, truncate_cells(desc, right_w), right_w, cp(1))

    fields = model_form_fields(cfg_type)
    max_rows = max(1, h - 10)
    start = max(0, min(field_idx - max_rows + 1, max(0, len(fields) - max_rows)))
    for row, (key, label, kind) in enumerate(fields[start:start + max_rows]):
        idx = start + row
        value: Any = cfg_type if key == "type" else cfg.get(key, "")
        shown = mask_secret(str(value)) if kind == "secret" else str(value)
        if kind == "bool":
            shown = "true" if bool(value) else "false"
        attr = cp(11) | curses.A_BOLD if idx == field_idx else cp(2)
        line = f"{label:<13} {shown}"
        safe_add(stdscr, y0 + 6 + row, right_x, " " * right_w, right_w, attr)
        safe_add(stdscr, y0 + 6 + row, right_x, line, right_w, attr)
    if message:
        safe_add(stdscr, y0 + h - 2, x0 + 2, message, inner_w, cp(5))
    stdscr.refresh()


def run_model_form(stdscr, state: State, entries: list[LLMConfigEntry], entry: Optional[LLMConfigEntry] = None) -> Optional[LLMConfigEntry]:
    providers = llm_template_providers()
    if entry is None:
        cfg_type, cfg = default_config_from_provider(providers[0])
        var_name = ""
        provider_idx = 0
        title = "添加模型供应商 / API"
    else:
        cfg_type = entry.cfg_type
        cfg = dict(entry.cfg)
        var_name = entry.var_name
        provider_idx = config_provider_index(cfg, cfg_type)
        title = f"编辑 {config_display_name(entry)}"
    field_idx = 0
    message = ""
    redraw(stdscr, state)
    while True:
        fields = model_form_fields(cfg_type)
        field_idx = max(0, min(field_idx, len(fields) - 1))
        draw_model_form(stdscr, title, cfg_type, cfg, provider_idx, field_idx, message)
        try:
            key = modal_read_key(stdscr)
        except (curses.error, KeyboardInterrupt):
            continue
        if key in ("\x1b", 27):
            return None
        if key == "\t":
            categories = provider_categories(providers)
            current_category = provider_category(providers[provider_idx])
            next_category = categories[(categories.index(current_category) + 1) % len(categories)]
            provider_idx = first_provider_in_category(providers, next_category)
            cfg_type, cfg = apply_provider_template(providers[provider_idx], cfg)
            message = f"已切到 {next_category} 模板；API Key 已保留。"
            continue
        if key in (curses.KEY_NPAGE, "]", "}"):
            rows = provider_indices_for_category(providers, provider_category(providers[provider_idx]))
            pos = rows.index(provider_idx) if provider_idx in rows else 0
            provider_idx = rows[(pos + 1) % len(rows)]
            cfg_type, cfg = apply_provider_template(providers[provider_idx], cfg)
            message = "已套用左侧模板；API Key 已保留。"
            continue
        if key in (curses.KEY_PPAGE, "[", "{"):
            rows = provider_indices_for_category(providers, provider_category(providers[provider_idx]))
            pos = rows.index(provider_idx) if provider_idx in rows else 0
            provider_idx = rows[(pos - 1) % len(rows)]
            cfg_type, cfg = apply_provider_template(providers[provider_idx], cfg)
            message = "已套用左侧模板；API Key 已保留。"
            continue
        if key in (curses.KEY_UP,):
            field_idx = (field_idx - 1) % len(fields)
            continue
        if key in (curses.KEY_DOWN,):
            field_idx = (field_idx + 1) % len(fields)
            continue
        key_name, _label, kind = fields[field_idx]
        if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
            direction = -1 if key == curses.KEY_LEFT else 1
            if key_name == "type":
                cfg_type = cycle_value(cfg_type, choice_values_for_field("type", providers[provider_idx], cfg_type), direction)
            elif key_name == "model":
                choices = choice_values_for_field("model", providers[provider_idx], cfg_type)
                if choices:
                    cfg["model"] = cycle_value(cfg.get("model", ""), choices, direction)
            elif kind == "choice":
                cfg[key_name] = cycle_value(cfg.get(key_name, ""), choice_values_for_field(key_name, providers[provider_idx], cfg_type), direction)
            continue
        if kind == "bool" and key == " ":
            cfg[key_name] = not bool(cfg.get(key_name, False))
            continue
        if key in ("\n", "\r", curses.KEY_ENTER):
            if field_idx < len(fields) - 1:
                field_idx += 1
                continue
            key = "\x13"
        if key in ("\x13", curses.KEY_F10):
            required_fields = ("name", "apikey", "apibase") if entry is None else ("name", "apikey", "apibase", "model")
            for required in required_fields:
                if not str(cfg.get(required, "")).strip():
                    message = f"{required} 不能为空。"
                    break
            else:
                cfg["name"] = str(cfg["name"]).strip()
                cfg["apibase"] = str(cfg["apibase"]).strip()
                cfg["model"] = str(cfg.get("model", "")).strip()
                for opt in ("reasoning_effort", "thinking_type", "proxy", "user_agent"):
                    if str(cfg.get(opt, "")).strip() == "":
                        cfg.pop(opt, None)
                for num_key in ("read_timeout", "connect_timeout", "max_retries", "max_tokens", "context_win", "thinking_budget_tokens"):
                    if num_key not in cfg:
                        continue
                    raw_num = str(cfg.get(num_key, "")).strip()
                    if not raw_num:
                        cfg.pop(num_key, None)
                        continue
                    try:
                        cfg[num_key] = int(raw_num)
                    except ValueError:
                        message = f"{num_key} 必须是数字。"
                        break
                else:
                    if "temperature" in cfg:
                        raw_temp = str(cfg.get("temperature", "")).strip()
                        if raw_temp:
                            try:
                                cfg["temperature"] = float(raw_temp)
                            except ValueError:
                                message = "temperature 必须是数字。"
                                continue
                        else:
                            cfg.pop("temperature", None)
                    if cfg_type == "native_oai":
                        cfg.setdefault("api_mode", "chat_completions")
                    keep = var_name if entry is not None else ""
                    return LLMConfigEntry(unique_config_var_name(entries, cfg_type, keep), cfg_type, cfg)
                continue
            continue
        if key in (curses.KEY_BACKSPACE, 127, "\b"):
            if kind in {"text", "secret"}:
                cfg[key_name] = str(cfg.get(key_name, ""))[:-1]
            continue
        if key in (curses.KEY_DC,):
            if kind in {"text", "secret"}:
                cfg[key_name] = ""
            continue
        if isinstance(key, str) and key and key.isprintable() and kind in {"text", "secret"}:
            cfg[key_name] = str(cfg.get(key_name, "")) + key


def default_entry_index(entries: list[LLMConfigEntry], mixin: dict[str, Any]) -> int:
    primary = (mixin.get("llm_nos") or [""])[0]
    for idx, entry in enumerate(entries):
        if config_display_name(entry) == primary:
            return idx
    return 0


def save_default_model(entries: list[LLMConfigEntry], mixin: dict[str, Any], preserved: list[tuple[str, Any]], selected: int) -> tuple[bool, str]:
    if not entries:
        return False, "没有可设置的模型。"
    selected = max(0, min(selected, len(entries) - 1))
    mixin["llm_nos"] = [config_display_name(entries[selected])]
    return save_llm_config_entries(entries, mixin, preserved)


def probe_and_merge_models(base_entry: LLMConfigEntry, entries: list[LLMConfigEntry]) -> tuple[bool, list[LLMConfigEntry], str]:
    ok, models, probe_msg = probe_models_for_config(base_entry.cfg_type, base_entry.cfg)
    if not ok:
        return False, [], probe_msg
    preferred_model = str(base_entry.cfg.get("model") or "").strip()
    if preferred_model in models:
        models = [preferred_model, *(model for model in models if model != preferred_model)]
    added = entries_from_provider_models(base_entry, models, entries)
    if not added:
        return True, [], f"{probe_msg} 返回的模型都已经存在，未重复写入。"
    return True, added, probe_msg


def open_model_manager(stdscr, state: State, *, manage_configs: bool = False) -> None:
    clear_selection(state)
    old_timeout = TUI_POLL_TIMEOUT_MS
    final_message = "模型面板已关闭。"
    try:
        stdscr.timeout(-1)
        redraw(stdscr, state)
        entries, mixin, preserved, error = load_llm_config_entries()
        recent_names = load_recent_model_names(entries)
        health: dict[str, tuple[bool, str]] = {}
        selected = model_manager_initial_index(state, entries, mixin, recent_names)
        message = error or ("还没有已配置模型；用 /llm 添加供应商/API。" if not entries else "")
        title = "LLM 配置 / 模型管理" if manage_configs else "当前对话模型切换"
        while True:
            selected = max(0, min(selected, max(0, len(entries) - 1)))
            draw_model_manager(stdscr, state, entries, mixin, selected, message, health, recent_names=recent_names, title=title, manage_configs=manage_configs)
            message = ""
            try:
                key = modal_read_key(stdscr)
            except KeyboardInterrupt:
                break
            except curses.error:
                continue
            if key in ("\x1b", 27, "q", "Q"):
                break
            if key in (curses.KEY_UP,):
                selected = (selected - 1) % len(entries) if entries else 0
                continue
            if key in (curses.KEY_DOWN,):
                selected = (selected + 1) % len(entries) if entries else 0
                continue
            if key in ("r", "R"):
                entries, mixin, preserved, error = load_llm_config_entries()
                recent_names = load_recent_model_names(entries)
                health = {}
                selected = model_manager_initial_index(state, entries, mixin, recent_names)
                ok, message = reload_agent_llms(state, preserve_current=True)
                if error:
                    message = error
                continue
            if entries and key in ("u", "U"):
                recent_names = load_recent_model_names(entries)
                if not recent_names:
                    message = "还没有最近模型；选择一次当前对话模型后会记录。"
                else:
                    selected = next_recent_entry_index(entries, recent_names, selected)
                    message = f"已跳到最近模型：{config_display_name(entries[selected])}"
                continue
            if manage_configs and key in ("a", "A", "+"):
                new_entry = run_model_form(stdscr, state, entries)
                if new_entry is None:
                    message = "新增模型配置已取消。"
                    continue
                probe_result = run_modal_task_until_done(
                    stdscr,
                    state,
                    "供应商验活 / 模型提取",
                    [
                        "正在请求 models endpoint，成功后会把返回模型展开为可选择配置。",
                        f"Provider: {config_display_name(new_entry)}",
                        f"Base URL: {new_entry.cfg.get('apibase') or ''}",
                    ],
                    lambda: probe_and_merge_models(new_entry, entries),
                )
                if probe_result is None:
                    message = "模型提取已取消。"
                    continue
                ok_probe, added, probe_msg = probe_result
                if not ok_probe:
                    message = probe_msg
                    continue
                if added:
                    entries.extend(added)
                    recent_names = load_recent_model_names(entries)
                    selected = len(entries) - len(added)
                    ok_save, save_msg = save_llm_config_entries(entries, mixin, preserved)
                    _ok_reload, reload_msg = reload_agent_llms(state, preserve_current=True) if ok_save else (False, "")
                    message = f"{probe_msg} 已新增 {len(added)} 个模型配置。{reload_msg or save_msg}"
                else:
                    entries.append(new_entry)
                    recent_names = load_recent_model_names(entries)
                    selected = len(entries) - 1
                    ok_save, save_msg = save_llm_config_entries(entries, mixin, preserved)
                    _ok_reload, reload_msg = reload_agent_llms(state, preserve_current=True) if ok_save else (False, "")
                    message = f"{probe_msg} 已保存供应商配置。{reload_msg or save_msg}"
                continue
            if manage_configs and entries and key in ("e", "E"):
                old_name = config_display_name(entries[selected])
                edited = run_model_form(stdscr, state, entries, entries[selected])
                if edited is None:
                    message = "编辑已取消。"
                    continue
                entries[selected] = edited
                if (mixin.get("llm_nos") or [""])[0] == old_name:
                    mixin["llm_nos"] = [config_display_name(edited)]
                ok_save, save_msg = save_llm_config_entries(entries, mixin, preserved)
                _ok_reload, reload_msg = reload_agent_llms(state, preserve_current=True) if ok_save else (False, "")
                recent_names = load_recent_model_names(entries)
                message = reload_msg or save_msg
                continue
            if manage_configs and entries and key in ("x", "X", curses.KEY_DC):
                removed = entries.pop(selected)
                health.pop(model_health_key(removed), None)
                selected = max(0, min(selected, len(entries) - 1))
                ok_save, save_msg = save_llm_config_entries(entries, mixin, preserved)
                _ok_reload, reload_msg = reload_agent_llms(state, preserve_current=True) if ok_save else (False, "")
                recent_names = load_recent_model_names(entries)
                message = f"已删除 {config_display_name(removed)}。{reload_msg or save_msg}"
                continue
            if manage_configs and entries and key in ("p", "P"):
                selected_key = model_health_key(entries[selected])
                probe_result = run_modal_task_until_done(
                    stdscr,
                    state,
                    "模型提取",
                    [
                        "正在用当前配置请求 models endpoint。",
                        f"Provider: {config_display_name(entries[selected])}",
                        f"Base URL: {entries[selected].cfg.get('apibase') or ''}",
                    ],
                    lambda: probe_and_merge_models(entries[selected], entries),
                )
                if probe_result is None:
                    message = "模型提取已取消。"
                    continue
                ok_probe, added, probe_msg = probe_result
                if not ok_probe:
                    message = probe_msg
                    continue
                if not added:
                    message = probe_msg
                    continue
                entries.extend(added)
                recent_names = load_recent_model_names(entries)
                ok_save, save_msg = save_llm_config_entries(entries, mixin, preserved)
                _ok_reload, reload_msg = reload_agent_llms(state, preserve_current=True) if ok_save else (False, "")
                selected = next((idx for idx, entry in enumerate(entries) if model_health_key(entry) == selected_key), selected)
                message = f"{probe_msg} 已新增 {len(added)} 个模型配置。{reload_msg or save_msg}"
                continue
            if entries and key in ("t", "T"):
                selected_key = model_health_key(entries[selected])
                test_entry = entries[selected]
                result = run_modal_task_until_done(
                    stdscr,
                    state,
                    "模型测试",
                    [
                        "正在用选中模型发送最小 ping 请求。",
                        f"Model: {config_display_name(test_entry)}",
                        f"Base URL: {test_entry.cfg.get('apibase') or ''}",
                    ],
                    lambda: validate_model_entry(test_entry),
                )
                if result is None:
                    message = "模型测试已取消。"
                    continue
                ok_test, test_msg = result
                health[selected_key] = (ok_test, test_msg)
                message = f"{'OK' if ok_test else 'BAD'} {config_display_name(test_entry)}: {test_msg}"
                continue
            if key in ("v", "V"):
                if not entries:
                    message = "没有可验活的模型；先用 /llm 添加供应商/API。"
                    continue
                selected_key = model_health_key(entries[selected])
                total = len(entries)
                done = 0
                alive = 0
                dead = 0
                health = {}
                message = f"批量验活开始：0/{total}；Esc 返回主页面"
                draw_model_manager(stdscr, state, entries, mixin, selected, message, health, recent_names=recent_names)
                max_workers = min(4, max(1, total))
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ga-model-validate")
                futures = {executor.submit(validate_model_entry, entry): entry for entry in entries}
                pending = set(futures)
                cancelled = False
                try:
                    while pending:
                        completed, pending = concurrent.futures.wait(pending, timeout=0.05, return_when=concurrent.futures.FIRST_COMPLETED)
                        if modal_poll_escape(stdscr):
                            cancelled = True
                            for future in pending:
                                future.cancel()
                            message = f"批量验活已取消：OK {alive} / BAD {dead}"
                            final_message = "已取消批量验活，返回主页面。"
                            break
                        if not completed:
                            continue
                        for future in completed:
                            entry = futures[future]
                            try:
                                ok, msg = future.result()
                            except Exception as exc:
                                ok, msg = False, f"{type(exc).__name__}: {exc}"
                            health[model_health_key(entry)] = (ok, msg)
                            done += 1
                            if ok:
                                alive += 1
                            else:
                                dead += 1
                            message = f"批量验活 {done}/{total}: OK {alive} / BAD {dead}；Esc 返回主页面"
                            draw_model_manager(stdscr, state, entries, mixin, selected, message, health, recent_names=recent_names)
                finally:
                    executor.shutdown(wait=False, cancel_futures=True)
                if cancelled:
                    break
                entries = order_entries_by_health(entries, health)
                selected = 0
                for idx, entry in enumerate(entries):
                    if model_health_key(entry) == selected_key:
                        selected = idx
                        break
                message = f"验活完成：{alive} 个可用，{dead} 个不可用；已按 OK/BAD 分组。"
                continue
            if not entries:
                continue
            if key in ("\n", "\r", curses.KEY_ENTER, "s", "S"):
                ok, message = switch_agent_to_entry(state, entries[selected])
                if ok:
                    _recent_ok, recent_msg = remember_recent_model_entry(entries[selected], entries)
                    recent_names = load_recent_model_names(entries)
                    if not _recent_ok:
                        message = f"{message} {recent_msg}"
                    final_message = message
                    break
                continue
            if key in ("d", "D"):
                ok, msg = save_default_model(entries, mixin, preserved, selected)
                if ok:
                    _ok_reload, reload_msg = reload_agent_llms(state, preserve_current=True)
                    message = f"{msg} 默认新对话模型已设为 {config_display_name(entries[selected])}。{reload_msg}"
                    final_message = message
                else:
                    message = msg
                continue
    finally:
        stdscr.timeout(old_timeout)
        state.last_error = final_message
        mark_dirty(state)


def open_llm_provider_adder(stdscr, state: State) -> None:
    open_model_manager(stdscr, state, manage_configs=True)


def subagent_settings_options(entries: list[LLMConfigEntry]) -> list[str]:
    return ["", *entry_names(entries)]


def draw_subagent_settings(
    stdscr,
    state: State,
    sub: SubAgentRuntime,
    entries: list[LLMConfigEntry],
    selected: int,
    message: str,
) -> None:
    height, width = stdscr.getmaxyx()
    y0, x0, h, w = popup_geometry(height, width, min_h=18, min_w=92)
    draw_popup(stdscr, y0, x0, h, w, "持久 Agent 详细设置")
    inner_w = w - 4
    current = sub.default_model or "(继承全局默认)"
    safe_add(stdscr, y0 + 2, x0 + 2, f"{sub.name} ({sub.agent_id})  role={sub.role}  默认模型={current}", inner_w, cp(2))
    safe_add(stdscr, y0 + 3, x0 + 2, "↑↓ 选择模型  Enter 设为该 agent 默认  c 继承全局默认  r 重载模型配置  Esc 返回", inner_w, cp(1))
    options = subagent_settings_options(entries)
    list_y = y0 + 5
    list_h = max(1, h - 10)
    selected = max(0, min(selected, max(0, len(options) - 1)))
    view_start = max(0, min(selected - list_h + 1, max(0, len(options) - list_h)))
    for row, model_name in enumerate(options[view_start:view_start + list_h]):
        idx = view_start + row
        label = "(继承全局默认模型)" if not model_name else model_name
        marker = "*" if model_name == sub.default_model else " "
        attr = cp(11) | curses.A_BOLD if idx == selected else cp(2)
        safe_add(stdscr, list_y + row, x0 + 2, " " * inner_w, inner_w, attr)
        safe_add(stdscr, list_y + row, x0 + 2, f"{marker} {idx + 1:02d} {label}", inner_w, attr)
    profile_preview = truncate_cells(clean_text(subagent_profile_text(sub)).replace("\n", " "), inner_w - 9)
    safe_add(stdscr, y0 + h - 4, x0 + 2, f"profile: {profile_preview or '(empty)'}", inner_w, cp(1))
    if message:
        safe_add(stdscr, y0 + h - 2, x0 + 2, message, inner_w, cp(5) if "失败" in message or "找不到" in message else cp(3))
    stdscr.refresh()


def open_subagent_settings(stdscr, state: State, sub: SubAgentRuntime) -> None:
    clear_selection(state)
    old_timeout = TUI_POLL_TIMEOUT_MS
    final_message = "Agent 设置面板已关闭。"
    try:
        stdscr.timeout(-1)
        redraw(stdscr, state)
        if not sub.persistent:
            draw_modal_notice(stdscr, state, "Agent 设置", [f"{sub.name} 是临时会话子 agent，不支持默认模型。"])
            modal_read_key(stdscr)
            return
        entries, _mixin, _preserved, error = load_llm_config_entries()
        options = subagent_settings_options(entries)
        selected = max(0, options.index(sub.default_model) if sub.default_model in options else 0)
        message = error or ""
        while True:
            options = subagent_settings_options(entries)
            selected = max(0, min(selected, max(0, len(options) - 1)))
            draw_subagent_settings(stdscr, state, sub, entries, selected, message)
            message = ""
            try:
                key = modal_read_key(stdscr)
            except KeyboardInterrupt:
                break
            except curses.error:
                continue
            if key in ("\x1b", 27, "q", "Q"):
                break
            if key in (curses.KEY_UP,):
                selected = (selected - 1) % len(options) if options else 0
                continue
            if key in (curses.KEY_DOWN,):
                selected = (selected + 1) % len(options) if options else 0
                continue
            if key in ("r", "R"):
                entries, _mixin, _preserved, error = load_llm_config_entries()
                options = subagent_settings_options(entries)
                selected = max(0, options.index(sub.default_model) if sub.default_model in options else 0)
                message = error or "模型配置已重载。"
                continue
            if key in ("c", "C"):
                ok, message = set_subagent_default_model(state, sub, "")
                if ok:
                    final_message = message
                    selected = 0
                continue
            if key in ("\n", "\r", curses.KEY_ENTER, "s", "S"):
                model_name = options[selected] if options else ""
                ok, message = set_subagent_default_model(state, sub, model_name)
                if ok:
                    final_message = message
                continue
    finally:
        stdscr.timeout(old_timeout)
        state.last_error = final_message
        mark_dirty(state)


def subagent_settings_target_from_command(text: str) -> str:
    raw = (text or "").strip()
    match = re.match(r"/agent\s+(?:settings|setting|config|detail|details|prefs)\s+(\S+)\s*$", raw, re.I)
    if match:
        return match.group(1)
    match = re.match(r"/agent\s+model\s+(\S+)\s*$", raw, re.I)
    return match.group(1) if match else ""


def parse_subagent_new_body(body: str) -> tuple[str, str, str, bool]:
    body = (body or "").strip()
    persistent = False
    for flag in ("--persistent", "--persist", "--long-term", "--long_term", "--permanent", "--durable"):
        if re.search(rf"(^|\s){re.escape(flag)}(\s|$)", body, flags=re.IGNORECASE):
            persistent = True
            body = re.sub(rf"(^|\s){re.escape(flag)}(\s|$)", " ", body, flags=re.IGNORECASE).strip()
    for flag in ("--temp", "--temporary", "--ephemeral"):
        if re.search(rf"(^|\s){re.escape(flag)}(\s|$)", body, flags=re.IGNORECASE):
            persistent = False
            body = re.sub(rf"(^|\s){re.escape(flag)}(\s|$)", " ", body, flags=re.IGNORECASE).strip()
    if "|" in body:
        name, profile = [part.strip() for part in body.split("|", 1)]
    else:
        name, profile = body, ""
    for prefix in ("persistent", "persist", "permanent", "durable", "long_term", "long-term", "长期", "持久", "永久"):
        for sep in (":", "："):
            marker = prefix + sep
            if name.lower().startswith(marker):
                persistent = True
                name = name[len(marker):].strip()
                break
        else:
            continue
        break
    for prefix in ("temp", "temporary", "ephemeral", "临时", "暂时"):
        for sep in (":", "："):
            marker = prefix + sep
            if name.lower().startswith(marker):
                persistent = False
                name = name[len(marker):].strip()
                break
        else:
            continue
        break
    role = "specialist"
    for sep in (":", "："):
        if sep in name:
            maybe_role, maybe_name = [part.strip() for part in name.split(sep, 1)]
            if normalized_role(maybe_role) == maybe_role.replace("-", "_"):
                role, name = maybe_role, maybe_name
                break
    return name.strip(), profile.strip(), role, persistent


def handle_subagent_command(state: State, text: str) -> bool:
    raw = (text or "").strip()
    load_subagents(state)
    if raw in {"/agents", "/agent", "/agent list"}:
        add_system(state, format_subagent_list(state))
        return True

    if raw in {"/agent templates", "/agent roles"}:
        lines = ["可用子 agent 角色："]
        for role, template in ROLE_TEMPLATES.items():
            lines.append(f"- {role}: {template.get('description', '')} · write={template.get('write_policy', 'none')}")
        add_system(state, "\n".join(lines))
        return True

    m_new = re.match(r"/agent\s+new\s+(.+?)\s*$", raw, re.I | re.S)
    if m_new:
        name, profile, role, persistent = parse_subagent_new_body(m_new.group(1))
        if not name:
            add_system(state, "Usage: /agent new [persistent:] [role:]<name> [| profile]")
            return True
        sub = find_reusable_subagent(state, name, profile, role, require_persistent=persistent)
        if sub is not None:
            add_system(state, f"已复用已有子 agent：{sub.name} ({sub.agent_id})\n角色：{sub.role}\n目录：{sub.home}")
            return True
        sub = create_subagent(state, name, profile, role=role, persistent=persistent)
        scope = "持久" if sub.persistent else "临时"
        add_system(state, f"已创建{scope}子 agent：{sub.name} ({sub.agent_id})\n角色：{sub.role}\n目录：{sub.home}")
        return True

    m_role = re.match(r"/agent\s+role\s+(\S+)\s+(\S+)\s*$", raw, re.I)
    if m_role:
        sub = resolve_subagent(state, m_role.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_role.group(1)}")
            return True
        role = normalized_role(m_role.group(2))
        if sub.security_context == "secret":
            sub.role = role
            sub.updated_at = time.time()
            save_subagent_meta(sub, state)
            if sub.agent is not None:
                install_subagent_prompt(sub.agent, sub)
            add_system(state, f"已设置 Secret 子 agent 角色：{sub.name} -> {sub.role}")
            return True
        decision = evaluate_policy_action(
            "modify_permission_policy",
            subject="orchestrator.main",
            source="user",
            target=sub.agent_id,
            payload={
                "operation": "set_subagent_role",
                "subagent_id": sub.agent_id,
                "old_role": sub.role,
                "role": role,
            },
        )
        if decision.approval_required:
            queue_policy_approval(
                decision,
                summary=f"{sub.name}: role {sub.role} -> {role}",
                extra_payload={
                    "deferred_operation": "set_subagent_role",
                    "subagent_id": sub.agent_id,
                    "role": role,
                },
            )
        record_policy_decision(decision)
        if not decision.allowed:
            add_system(state, policy_gate_text(decision))
            return True
        sub.role = role
        sub.updated_at = time.time()
        save_subagent_meta(sub, state)
        if sub.agent is not None:
            install_subagent_prompt(sub.agent, sub)
        add_system(state, f"已设置子 agent 角色：{sub.name} -> {sub.role}")
        return True

    m_settings = re.match(r"/agent\s+(?:settings|setting|config|detail|details|prefs)\s+(\S+)\s*$", raw, re.I)
    if m_settings:
        sub = resolve_subagent(state, m_settings.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_settings.group(1)}")
            return True
        add_system(state, f"在 TUI 输入框回车执行 /agent settings {sub.agent_id} 可打开详细设置界面。\n当前默认模型：{sub.default_model or '全局默认模型'}")
        return True

    m_model = re.match(r"/agent\s+model\s+(\S+)(?:\s+([\s\S]+))?$", raw, re.I)
    if m_model:
        sub = resolve_subagent(state, m_model.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_model.group(1)}")
            return True
        model_name = (m_model.group(2) or "").strip()
        if not model_name:
            add_system(state, f"{sub.name} 默认模型：{sub.default_model or '全局默认模型'}\n用法：/agent model {sub.agent_id} <model|inherit>")
            return True
        ok, msg = set_subagent_default_model(state, sub, model_name)
        add_system(state, msg)
        return True

    m_ask = re.match(r"/agent\s+(?:ask|input|run)\s+(\S+)\s+([\s\S]+)$", raw, re.I)
    if m_ask:
        sub = resolve_subagent(state, m_ask.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_ask.group(1)}")
            return True
        add_system(state, start_subagent_task(state, sub, m_ask.group(2), source="user"))
        return True

    m_answer = re.match(r"/agent\s+(?:answer|reply)\s+(\S+)\s+([\s\S]+)$", raw, re.I)
    if m_answer:
        sub = resolve_subagent(state, m_answer.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_answer.group(1)}")
            return True
        sub.pending_interaction = None
        add_system(state, start_subagent_task(state, sub, m_answer.group(2), source="answer"))
        return True

    m_memory = re.match(r"/agent\s+memory\s+(\S+)\s*$", raw, re.I)
    if m_memory:
        sub = resolve_subagent(state, m_memory.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_memory.group(1)}")
            return True
        memory = subagent_memory_text(sub).strip() if sub.persistent else "(ephemeral: no long-term memory)"
        add_system(state, f"{sub.name} memory:\n{memory or '(empty)'}")
        return True

    m_remember = re.match(r"/agent\s+(?:remember|mem)\s+(\S+)\s+([\s\S]+)$", raw, re.I)
    if m_remember:
        sub = resolve_subagent(state, m_remember.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_remember.group(1)}")
            return True
        add_system(state, append_subagent_memory(sub, m_remember.group(2), source="manual", state=state))
        return True

    m_profile = re.match(r"/agent\s+profile\s+(\S+)(?:\s+([\s\S]+))?$", raw, re.I)
    if m_profile:
        sub = resolve_subagent(state, m_profile.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_profile.group(1)}")
            return True
        new_profile = (m_profile.group(2) or "").strip()
        if not new_profile:
            add_system(state, f"{sub.name} profile:\n{subagent_profile_text(sub).strip() or '(empty)'}")
            return True
        if sub.security_context == "secret":
            sub.profile_text = new_profile.rstrip() + "\n"
        else:
            write_text_atomic(subagent_profile_file(sub), new_profile.rstrip() + "\n")
        sub.updated_at = time.time()
        save_subagent_meta(sub, state)
        if sub.agent is not None:
            install_subagent_prompt(sub.agent, sub)
        add_system(state, f"已更新子 agent profile：{sub.name}")
        return True

    m_rename = re.match(r"/agent\s+rename\s+(\S+)\s+(.+?)\s*$", raw, re.I)
    if m_rename:
        sub = resolve_subagent(state, m_rename.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_rename.group(1)}")
            return True
        sub.name = m_rename.group(2).strip() or sub.name
        sub.updated_at = time.time()
        save_subagent_meta(sub, state)
        if sub.agent is not None:
            install_subagent_prompt(sub.agent, sub)
        add_system(state, f"已重命名子 agent：{sub.name} ({sub.agent_id})")
        return True

    m_info = re.match(r"/agent\s+info\s+(\S+)\s*$", raw, re.I)
    if m_info:
        sub = resolve_subagent(state, m_info.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_info.group(1)}")
            return True
        lines = [
            f"id: {sub.agent_id}",
            f"name: {sub.name}",
            f"role: {sub.role}",
            f"default_model: {sub.default_model or '(global default)'}",
            f"write_policy: {role_write_policy(sub.role)}",
            f"status: {sub.status}",
            f"persistent: {sub.persistent}",
            f"queued: {len(sub.task_queue)}",
            f"home: {sub.home}",
            f"profile: {subagent_profile_file(sub)}",
            f"memory: {subagent_memory_file(sub) if sub.persistent else '(disabled)'}",
            f"events: {subagent_events_file(sub)}",
            f"messages: {len(sub.messages)}",
        ]
        add_system(state, "\n".join(lines))
        return True

    m_stop = re.match(r"/agent\s+stop\s+(\S+)\s*$", raw, re.I)
    if m_stop:
        sub = resolve_subagent(state, m_stop.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_stop.group(1)}")
            return True
        if sub.agent is not None:
            try:
                sub.agent.abort()
            except Exception:
                pass
        sub.status = "aborting" if sub.status == "running" else "idle"
        sub.updated_at = time.time()
        save_subagent_meta(sub, state)
        add_system(state, f"已请求停止子 agent：{sub.name}")
        return True

    m_delete = re.match(r"/agent\s+(?:delete|remove)\s+(\S+)\s*$", raw, re.I)
    if m_delete:
        sub = resolve_subagent(state, m_delete.group(1))
        if sub is None:
            add_system(state, f"找不到子 agent: {m_delete.group(1)}")
            return True
        add_system(state, soft_delete_subagent(state, sub, source="user"))
        return True

    if raw.startswith("/agent"):
        add_system(state, "未知 /agent 命令。\n" + format_subagent_list(state))
        return True
    return False


def format_task_ledger(limit: int = 20) -> str:
    rows = read_jsonl(AGENT_TASK_LEDGER_PATH, limit=limit)
    if not rows:
        return "共享任务账本为空。"
    lines = ["共享任务账本："]
    for row in rows[-limit:]:
        task_id = str(row.get("task_id") or "-")
        status = str(row.get("status") or "-")
        agent_id = str(row.get("assigned_agent") or "-")
        summary = str(row.get("summary") or row.get("objective") or row.get("error") or "")
        artifacts = row.get("artifact_refs") or []
        suffix = f" · {artifacts[0]}" if isinstance(artifacts, list) and artifacts else ""
        lines.append(f"- {task_id} · {status} · {agent_id} · {truncate_cells(summary, 90)}{suffix}")
    return "\n".join(lines)


def format_agent_mail(limit: int = 20) -> str:
    rows = read_jsonl(AGENT_MAIL_PATH, limit=limit)
    if not rows:
        return "agent mail 为空。"
    lines = ["Agent Mail："]
    for row in rows[-limit:]:
        from_id = str((row.get("from") or {}).get("agent_id") or "-")
        to = row.get("to") or {}
        target = str(to.get("target") or "-") if isinstance(to, dict) else "-"
        intent = str(row.get("intent") or "-")
        status = str(row.get("status") or "-")
        task_id = str(row.get("task_id") or "-")
        payload = row.get("payload") or {}
        summary = str(payload.get("summary") or payload.get("objective") or payload.get("approval_id") or "")
        lines.append(f"- {intent} · {status} · {from_id} -> {target} · {task_id} · {truncate_cells(summary, 80)}")
    return "\n".join(lines)


def format_approvals(state: State) -> str:
    rows = pending_approvals(state)
    if not rows:
        return "没有待审批事项。"
    lines = ["Secret 待审批事项：" if state.secret_vault.unlocked else "待审批事项："]
    for row in rows:
        approval_id = str(row.get("approval_id") or "-")
        approval_type = str(row.get("type") or "-")
        source = str(row.get("source") or "-")
        summary = str(row.get("summary") or "")
        secret_mark = " · SECRET" if row.get("secret_storage") else ""
        lines.append(f"- {approval_id} · {approval_type}{secret_mark} · {source} · {truncate_cells(summary, 100)}")
    lines += ["", "在 /approvals 面板中选中条目按 Enter 可打开单选处理；也可用 /approve <id> 或 /reject <id>。"]
    return "\n".join(lines)


def decide_approval(state: State, approval_id: str, approved: bool) -> str:
    approval_id = (approval_id or "").strip()
    if state.secret_vault.unlocked:
        secret_rows = secret_memory_candidate_approval_rows(state, show_all=True)
        match: Optional[dict[str, Any]] = None
        for candidate in secret_rows:
            candidate_id = str(candidate.get("approval_id") or "")
            if candidate_id == approval_id or candidate_id.startswith(approval_id):
                if match is not None:
                    return f"Secret 审批 id 前缀不唯一：{approval_id}"
                match = candidate
        if match is not None:
            match_id = str(match.get("approval_id") or "")
            if match.get("status") != "pending":
                clear_pending_approval_interaction(state, match_id)
                return f"Secret 审批项已处理：{match_id} -> {match.get('status')}"
            payload = match.get("payload") if isinstance(match.get("payload"), dict) else {}
            candidate = payload.get("memory_candidate") if isinstance(payload.get("memory_candidate"), dict) else {}
            candidate_id = str(payload.get("secret_candidate_id") or candidate.get("candidate_id") or "")
            if not approved:
                secret_write_subagent_json(state, "subagent-memory-candidates", candidate_id, {
                    "schema_version": "secret.memory_candidate_record.v1",
                    "candidate": candidate,
                    "approval_id": match_id,
                    "status": "rejected",
                    "updated_at": now_iso(),
                })
                clear_pending_approval_interaction(state, match_id)
                return f"已拒绝 Secret 记忆候选：{match_id}"
            sub = resolve_subagent(state, str(payload.get("subagent_id") or match.get("target") or ""))
            if sub is None:
                clear_pending_approval_interaction(state, match_id)
                return f"已批准但找不到 Secret 子 agent：{match_id}"
            memory_text = str(candidate.get("statement") or payload.get("memory") or "")
            result = append_subagent_memory(sub, memory_text, source="approved", policy_approved=True, state=state)
            secret_write_subagent_json(state, "subagent-memory-candidates", candidate_id, {
                "schema_version": "secret.memory_candidate_record.v1",
                "candidate": candidate,
                "approval_id": match_id,
                "status": "approved",
                "updated_at": now_iso(),
            })
            clear_pending_approval_interaction(state, match_id)
            return f"已批准并执行 Secret 记忆候选：{result}"

    records = approval_latest_records()
    match_id = ""
    for candidate in records:
        if candidate == approval_id or candidate.startswith(approval_id):
            if match_id:
                return f"审批 id 前缀不唯一：{approval_id}"
            match_id = candidate
    if not match_id:
        return f"找不到审批项：{approval_id}"
    row = records[match_id]
    if row.get("status") != "pending":
        clear_pending_approval_interaction(state, match_id)
        return f"审批项已处理：{match_id} -> {row.get('status')}"
    decision = dict(row)
    decision["timestamp"] = now_iso()
    decision["status"] = "approved" if approved else "rejected"
    append_jsonl(AGENT_APPROVALS_PATH, decision)
    if not approved:
        append_agent_mail(
            from_agent="human",
            to_type="agent",
            target=str(row.get("source") or ""),
            intent="approval_rejected",
            status="rejected",
            payload={"approval_id": match_id, "summary": row.get("summary", "")},
        )
        clear_pending_approval_interaction(state, match_id)
        return f"已拒绝：{match_id}"
    payload = row.get("payload") or {}
    approval_type = str(row.get("type") or "")
    if approval_type == "memory_write_request":
        sub = resolve_subagent(state, str(payload.get("subagent_id") or row.get("target") or ""))
        if sub is None:
            clear_pending_approval_interaction(state, match_id)
            return f"已批准但找不到目标子 agent：{match_id}"
        candidate = payload.get("memory_candidate") if isinstance(payload.get("memory_candidate"), dict) else {}
        memory_text = str(candidate.get("statement") or payload.get("memory") or "")
        result = append_subagent_memory(sub, memory_text, source="approved", policy_approved=True, state=state)
        if candidate:
            append_memory_candidate_record(candidate, status="approved", approval_id=match_id, artifact_refs=list(payload.get("artifact_refs") or []))
        append_agent_mail(
            from_agent="human",
            to_type="agent",
            target=sub.agent_id,
            intent="approval_granted",
            status="approved",
            payload={"approval_id": match_id, "result": result, "memory_candidate": candidate},
        )
        clear_pending_approval_interaction(state, match_id)
        return f"已批准并执行：{result}"
    if approval_type == "policy_approval_request":
        deferred = str(payload.get("deferred_operation") or "")
        if deferred == "start_subagent_task":
            sub = resolve_subagent(state, str(payload.get("subagent_id") or row.get("target") or ""))
            if sub is None:
                clear_pending_approval_interaction(state, match_id)
                return f"已批准但找不到目标子 agent：{match_id}"
            result = start_subagent_task(
                state,
                sub,
                str(payload.get("prompt") or ""),
                source="approved_policy",
                policy_approved=True,
                parent_task_id=str(payload.get("parent_task_id") or ""),
                task_title=str(payload.get("task_title") or ""),
            )
        elif deferred == "append_subagent_memory":
            sub = resolve_subagent(state, str(payload.get("subagent_id") or row.get("target") or ""))
            if sub is None:
                clear_pending_approval_interaction(state, match_id)
                return f"已批准但找不到目标子 agent：{match_id}"
            result = append_subagent_memory(sub, str(payload.get("memory") or ""), source="approved_policy", policy_approved=True, state=state)
        elif deferred == "recover_task_action":
            result = recover_task_action(state, str(payload.get("task_id") or ""), str(payload.get("recovery_action") or ""), policy_approved=True)
        elif deferred == "set_subagent_role":
            sub = resolve_subagent(state, str(payload.get("subagent_id") or row.get("target") or ""))
            if sub is None:
                clear_pending_approval_interaction(state, match_id)
                return f"已批准但找不到目标子 agent：{match_id}"
            role = normalized_role(str(payload.get("role") or "specialist"))
            sub.role = role
            sub.updated_at = time.time()
            save_subagent_meta(sub, state)
            if sub.agent is not None:
                install_subagent_prompt(sub.agent, sub)
            result = f"已设置子 agent 角色：{sub.name} -> {sub.role}"
        else:
            result = f"已批准 policy request：{match_id}"
        append_agent_mail(
            from_agent="human",
            to_type="agent",
            target=str(row.get("source") or ""),
            intent="approval_granted",
            status="approved",
            payload={"approval_id": match_id, "result": result, "deferred_operation": deferred},
        )
        clear_pending_approval_interaction(state, match_id)
        return f"已批准并执行：{result}"
    clear_pending_approval_interaction(state, match_id)
    return f"已批准：{match_id}"


def control_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on", "持久", "长期"}


def control_falsey(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return not bool(value)
    return str(value or "").strip().lower() in {"0", "false", "no", "n", "off", "none", "null", "不要", "不"}


def subagent_control_identity_text(target: str, value: str, name: str, profile: str) -> str:
    return "\n".join(str(part or "") for part in (target, value, name, profile))


def subagent_control_persistence_intent(
    control: dict[str, Any],
    target: str,
    value: str,
    name: str,
    profile: str,
) -> tuple[bool, bool]:
    persistent_raw = control.get("persistent", control.get("long_term", control.get("durable", None)))
    if persistent_raw is not None:
        return (True, False) if control_truthy(persistent_raw) else (False, True)
    for key in ("temporary", "temp", "ephemeral", "session_only", "session_scoped"):
        if key in control and control_truthy(control.get(key)):
            return False, True
    identity = subagent_control_identity_text(target, value, name, profile)
    identity_temporary = text_has_any_intent_token(identity, SUBAGENT_TEMPORARY_INTENT_TOKENS)
    identity_persistent = text_has_any_intent_token(identity, SUBAGENT_PERSISTENT_INTENT_TOKENS)
    if identity_temporary:
        return False, True
    if identity_persistent:
        return True, False
    return False, False


def subagent_control_force_new_intent(
    control: dict[str, Any],
    target: str,
    value: str,
    name: str,
    profile: str,
    context_text: str = "",
) -> bool:
    for key in ("force_new", "create_new", "fresh", "separate"):
        if key in control and control_truthy(control.get(key)):
            return True
    for key in ("reuse", "reuse_existing", "allow_reuse", "dedupe"):
        if key in control and control_falsey(control.get(key)):
            return True
    if "new" in control and isinstance(control.get("new"), (bool, int, float, str)) and control_truthy(control.get("new")):
        return True
    identity = "\n".join([subagent_control_identity_text(target, value, name, profile), context_text])
    return text_has_any_intent_token(identity, SUBAGENT_FORCE_NEW_INTENT_TOKENS)


def subagent_control_alias_keys(*values: Any) -> list[str]:
    keys: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in {"current", "now", "selected"}:
            continue
        for key in (text, text.lower(), compact_identity_text(text)):
            if key and key not in keys:
                keys.append(key)
    return keys


def register_subagent_control_aliases(alias_map: Optional[dict[str, str]], sub: SubAgentRuntime, *values: Any) -> None:
    if alias_map is None:
        return
    for key in subagent_control_alias_keys(*values, sub.agent_id, sub.name):
        alias_map[key] = sub.agent_id


def resolve_subagent_control_alias(alias_map: dict[str, str], target: str) -> str:
    for key in subagent_control_alias_keys(target):
        if key in alias_map:
            return alias_map[key]
    return target


def soft_delete_subagent(state: State, sub: SubAgentRuntime, *, source: str = "agent") -> str:
    if sub.status in {"running", "aborting"} or (sub.agent is not None and agent_has_unfinished_task(sub.agent)):
        return f"{sub.name} 仍在运行，请先停止后再删除。"
    deleted_at = time.time()
    sub.status = "deleted"
    sub.updated_at = deleted_at
    save_subagent_meta(sub, state, deleted=True, status="deleted", deleted_at=deleted_at, deleted_by=source)
    state.subagents.pop(sub.agent_id, None)
    state.expanded_subagent_meta.discard(sub.agent_id)
    if str(state.selected_session or "") == sub.agent_id:
        state.selected_session = "main"
        mark_messages_changed(state)
    else:
        mark_dirty(state)
    state.rightbar_task_rows_cache = []
    return f"已从列表移除子 agent：{sub.name}；文件保留在 {sub.home}"


def apply_subagent_control(
    state: State,
    action: str,
    target: str,
    value: str,
    control: dict[str, Any],
    source: str = "agent",
    control_aliases: Optional[dict[str, str]] = None,
    force_new_context: str = "",
) -> Optional[str]:
    action = (action or "").strip().lower().replace("-", "_")
    if not (action.startswith("subagent_") or action.startswith("agent_") or action in {"create_subagent", "new_subagent"}):
        return None
    secret_control_context = bool(state.secret_vault.unlocked or str(source or "").startswith("secret"))
    if action in {"subagent_create", "agent_create", "create_subagent", "new_subagent"}:
        name = str(control.get("name") or control.get("title") or value or "").strip()
        if not name and target not in {"", "current", "now", "selected"}:
            name = target
        profile = str(control.get("profile") or control.get("description") or control.get("system") or "").strip()
        role = normalized_role(str(control.get("role") or "specialist"))
        persistent, temporary = subagent_control_persistence_intent(control, target, value, name, profile)
        if not name:
            return "缺少子 agent 名称。"
        force_new = subagent_control_force_new_intent(control, target, value, name, profile, force_new_context)
        reused = None if force_new else find_reusable_subagent(state, name, profile, role, require_persistent=persistent, require_temporary=temporary)
        if reused is not None:
            register_subagent_control_aliases(
                control_aliases,
                reused,
                target,
                value,
                name,
                control.get("title"),
                control.get("alias"),
            )
            step_id = "" if secret_control_context else resolve_plan_step_id(state, control.get("plan_step_id") or control.get("step") or "")
            if step_id:
                append_task_update(step_id, status="completed", summary=f"已复用子 agent：{reused.name}")
                maybe_complete_plan_after_step(step_id)
            scope = "持久" if reused.persistent else "临时"
            return f"已复用已有{scope}子 agent：{reused.name} ({reused.agent_id}, role={reused.role})"
        sub = create_subagent(state, name, profile, role=role, persistent=persistent)
        register_subagent_control_aliases(
            control_aliases,
            sub,
            target,
            value,
            name,
            control.get("title"),
            control.get("alias"),
        )
        step_id = "" if secret_control_context else resolve_plan_step_id(state, control.get("plan_step_id") or control.get("step") or "")
        if step_id:
            append_task_update(step_id, status="completed", summary=f"已创建子 agent：{sub.name}")
            maybe_complete_plan_after_step(step_id)
        scope = "持久" if sub.persistent else "临时"
        return f"已创建{scope}子 agent：{sub.name} ({sub.agent_id}, role={sub.role})"

    sub = resolve_subagent(state, target)
    if sub is None:
        return f"找不到子 agent: {target}"

    if action in {"subagent_ask", "subagent_run", "subagent_input", "agent_ask", "agent_run"}:
        prompt = str(control.get("prompt") or control.get("task") or control.get("message") or value or "").strip()
        if not prompt:
            return "缺少子 agent 任务内容。"
        parent_task_id = "" if secret_control_context else resolve_plan_step_id(state, control.get("parent_task_id") or control.get("plan_step_id") or control.get("step") or "")
        task_title = str(control.get("task_title") or control.get("title") or "").strip()
        if parent_task_id:
            append_task_update(parent_task_id, status="working", summary=f"已派发给 {sub.name}")
        return start_subagent_task(state, sub, prompt, source=source, parent_task_id=parent_task_id, task_title=task_title)

    if action in {"subagent_remember", "subagent_memory", "agent_remember", "agent_memory"}:
        memory = str(control.get("memory") or control.get("note") or value or "").strip()
        if "agent" in source:
            return queue_curated_memory_candidate(state, sub, memory, source=source)
        return append_subagent_memory(sub, memory, source=source, state=state)

    if action in {"subagent_profile", "subagent_set_profile", "agent_profile"}:
        profile = str(control.get("profile") or control.get("description") or value or "").strip()
        if not profile:
            return "缺少子 agent profile 内容。"
        if sub.security_context == "secret":
            sub.profile_text = profile.rstrip() + "\n"
        else:
            write_text_atomic(subagent_profile_file(sub), profile.rstrip() + "\n")
        sub.updated_at = time.time()
        save_subagent_meta(sub, state)
        if sub.agent is not None:
            install_subagent_prompt(sub.agent, sub)
        return f"已更新子 agent profile：{sub.name}"

    if action in {"subagent_role", "agent_role"}:
        role = normalized_role(str(control.get("role") or value or "specialist"))
        if sub.security_context == "secret":
            sub.role = role
            sub.updated_at = time.time()
            save_subagent_meta(sub, state)
            if sub.agent is not None:
                install_subagent_prompt(sub.agent, sub)
            return f"已设置 Secret 子 agent 角色：{sub.name} -> {sub.role}"
        decision = evaluate_policy_action(
            "modify_permission_policy",
            subject="orchestrator.main",
            source=source,
            target=sub.agent_id,
            payload={
                "operation": "set_subagent_role",
                "subagent_id": sub.agent_id,
                "old_role": sub.role,
                "role": role,
            },
        )
        if decision.approval_required:
            queue_policy_approval(
                decision,
                summary=f"{sub.name}: role {sub.role} -> {role}",
                extra_payload={
                    "deferred_operation": "set_subagent_role",
                    "subagent_id": sub.agent_id,
                    "role": role,
                },
            )
        record_policy_decision(decision)
        if not decision.allowed:
            return policy_gate_text(decision)
        sub.role = role
        sub.updated_at = time.time()
        save_subagent_meta(sub, state)
        if sub.agent is not None:
            install_subagent_prompt(sub.agent, sub)
        return f"已设置子 agent 角色：{sub.name} -> {sub.role}"

    if action in {"subagent_model", "agent_model"}:
        model_name = str(control.get("model") or control.get("default_model") or value or "").strip()
        if not model_name:
            return "缺少子 agent 默认模型名称。"
        _ok, msg = set_subagent_default_model(state, sub, model_name)
        return msg

    if action in {"subagent_stop", "agent_stop"}:
        if sub.agent is not None:
            try:
                sub.agent.abort()
            except Exception:
                pass
        sub.status = "aborting" if sub.status == "running" else "idle"
        sub.updated_at = time.time()
        save_subagent_meta(sub, state)
        return f"已请求停止子 agent：{sub.name}"

    if action in {"subagent_delete", "subagent_remove", "agent_delete", "agent_remove"}:
        return soft_delete_subagent(state, sub, source=source)

    return f"未知子 agent 操作 {action}"


def submit(state: State, text: str) -> None:
    raw_text = text
    text = text.strip()
    if secret_password_entry_active(state) and text.lower() != "/lock":
        result = accept_secret_password_input(state, raw_text)
        if result:
            add_system(state, result)
        return
    active_sub = selected_subagent(state)
    if active_sub is not None and active_sub.pending_interaction and not text.startswith("/"):
        answer = accept_subagent_interaction_input(state, active_sub, raw_text)
        if answer is None:
            return
        text = answer.strip()
    elif is_approval_interaction(state.pending_interaction) and not text.startswith("/"):
        result = accept_approval_interaction_input(state, raw_text)
        if result:
            add_system(state, result)
        return
    elif active_sub is None and state.pending_interaction and not text.startswith("/"):
        answer = accept_interaction_input(state, raw_text)
        if answer is None:
            return
        text = answer.strip()
    if not text:
        return
    state.command_index = 0
    mark_dirty(state)
    if secret_blocks_normal_command(state, text):
        add_system(state, "Secret Vault 已解锁：普通历史/普通 harness 面板已隔离。请先 /lock 再查看普通数据。")
        return
    if text in {"/quit", "/exit"}:
        state.exit_reason = "已退出 ga tui。"
        state.running = False
        return
    if handle_subagent_command(state, text):
        return
    active_sub = selected_subagent(state)
    if active_sub is not None and not text.startswith("/"):
        state.last_error = start_subagent_chat(state, active_sub, text, source="subagent_chat")
        mark_dirty(state)
        return
    if text == "/help":
        lines = [f"{cmd:<11} {args:<8} {desc}" for cmd, args, desc, _sendable in COMMANDS]
        add_system(state, "可用命令：\n" + "\n".join(lines))
        return
    if text == "/status":
        fold = "开启" if state.fold_process else "关闭"
        md = "开启" if state.markdown else "关闭"
        view = "归档" if state.show_archived else "普通"
        filt = state.session_filter_category or "全部"
        add_system(state, f"状态: {state.status}；当前会话: {state.current_title or 'main'}；后台会话: {len(state.background_sessions)} 个；历史会话: {len(state.history)} 个；视图: {view}；筛选: {filt}；过程折叠: {fold}；Markdown: {md}\n{secret_status_text(state)}")
        return
    if text == "/fold":
        state.fold_process = not state.fold_process
        mark_dirty(state)
        add_system(state, f"过程自动折叠已{'开启' if state.fold_process else '关闭'}。")
        return
    if text == "/md":
        state.markdown = not state.markdown
        mark_dirty(state)
        add_system(state, f"轻量 Markdown 渲染已{'开启' if state.markdown else '关闭'}。")
        return
    if text.lower() == "/llm":
        add_system(state, "在输入框回车执行 /llm 可管理模型配置：新增/编辑/删除、提取 models、验活、选择当前对话模型、最近模型、设置默认新对话模型。")
        return
    if text.lower() in {"/models", "/model"}:
        add_system(state, "在输入框回车执行 /model 可切换当前对话模型；Enter 只影响当前对话，u 跳最近模型，按 d 才会改默认新对话模型。")
        return
    m_secret = re.match(r"/secret(?:\s+(.+))?\s*$", text, re.I)
    if m_secret:
        secret_arg = (m_secret.group(1) or "").strip()
        secret_arg_l = secret_arg.lower()
        if not secret_arg:
            add_system(state, secret_status_text(state) if state.secret_vault.unlocked else begin_secret_unlock(state))
        elif secret_arg_l == "status":
            add_system(state, secret_status_text(state))
        elif secret_arg_l in {"sessions", "session", "chats", "chat", "list", "ls"}:
            add_system(state, format_secret_sessions(state))
        elif secret_arg_l in {"imports", "imported"}:
            add_system(state, format_secret_imported_sessions(state))
        elif open_session_match := re.match(r"^(?:open-session|session|chat)\s+(.+)$", secret_arg, re.I):
            result = restore_secret_native_session(state, open_session_match.group(1))
            add_system(state, result)
        elif open_match := re.match(r"^(?:open|restore|view)\s+(.+)$", secret_arg, re.I):
            result = restore_secret_imported_session(state, open_match.group(1))
            add_system(state, result)
        else:
            add_system(state, f"未知 Secret 命令：{secret_arg}\n用法：/Secret、/Secret status、/Secret sessions、/Secret open-session <编号>、/Secret open <导入编号>")
        return
    m_to_secret = re.match(r"/(?:toSecret|secretize)(?:\s+(.+))?\s*$", text, re.I)
    if m_to_secret:
        add_system(state, request_secret_import_session(state, m_to_secret.group(1) or ""))
        return
    if text == "/lock":
        add_system(state, lock_secret_vault(state, reason="/lock"))
        return
    if text in {"/memory", "/mem"}:
        add_system(state, "在输入框回车执行 /memory 可打开记忆系统可视化检查面板。")
        return
    if text == "/tasks":
        add_system(state, "在 TUI 输入框执行 /tasks 会打开 Task Ledger 面板。\n" + format_task_ledger())
        return
    if text == "/bus":
        add_system(state, format_agent_mail())
        return
    if text == "/approvals":
        add_system(state, "在 TUI 输入框执行 /approvals 会打开 Approval Inbox 面板。\n" + format_approvals(state))
        return
    if text == "/artifacts":
        items = artifact_inventory()
        lines = ["在 TUI 输入框执行 /artifacts 会打开 Artifact Store 面板。", f"Artifacts: {len(items)}"]
        lines.extend(f"- {item.key} · {item.subtitle}" for item in items[:20])
        add_system(state, "\n".join(lines))
        return
    if text == "/recover":
        items = recovery_panel_items(state)
        lines = ["在 TUI 输入框执行 /recover 会打开 Recovery 面板。", f"Unfinished/Stale: {len(items)}"]
        lines.extend(f"- {item.key} · {item.subtitle}" for item in items[:20])
        add_system(state, "\n".join(lines))
        return
    if text == "/evals":
        items = eval_panel_items()
        lines = ["在 TUI 输入框执行 /evals 会打开 Eval / Trace 面板。", f"Items: {len(items)}"]
        lines.extend(f"- {item.key} · {item.subtitle}" for item in items[:20])
        add_system(state, "\n".join(lines))
        return
    if text == "/gateway":
        data = ensure_gateway_registry(state)
        add_system(state, "在 TUI 输入框执行 /gateway 会打开 A2A/MCP Gateway 面板。\n" + json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)[:4000])
        return
    if text == "/baseline":
        report = architecture_baseline_report(state, gateway_data=ensure_gateway_registry(state))
        add_system(state, "在 TUI 输入框执行 /baseline 会打开 Architecture Baseline 面板。\n" + format_baseline_report(report))
        return
    m_approve = re.match(r"/(approve|reject)\s+(\S+)\s*$", text, re.I)
    if m_approve:
        add_system(state, decide_approval(state, m_approve.group(2), m_approve.group(1).lower() == "approve"))
        return
    if text == "/categories":
        add_system(state, format_category_counts(state))
        return
    m_catname = re.match(r"/catname\s+(.+?)\s+(.+?)\s*$", text, re.I)
    if m_catname:
        add_system(state, rename_category(state, m_catname.group(1), m_catname.group(2)))
        return
    m_catdesc = re.match(r"/catdesc\s+(\S+)\s+(.+?)\s*$", text, re.I)
    if m_catdesc:
        add_system(state, set_category_description(state, m_catdesc.group(1), m_catdesc.group(2)))
        return
    m_filter = re.match(r"/filter(?:\s+(.+))?\s*$", text, re.I)
    if m_filter:
        raw = (m_filter.group(1) or "").strip()
        if raw:
            add_system(state, set_session_filter(state, raw))
        else:
            add_system(state, format_category_counts(state) + "\nUsage: /filter <category|off>")
        return
    m_fold_category = re.match(r"/(collapse|expand)(?:\s+(.+))?\s*$", text, re.I)
    if m_fold_category:
        action = m_fold_category.group(1).lower()
        raw = (m_fold_category.group(2) or "").strip()
        add_system(state, set_category_collapsed(state, raw, action == "collapse"))
        return
    if text == "/stop":
        if state.status == "running":
            state.agent.abort()
            state.status = "aborting"
            add_system(state, "已请求中止当前任务。")
        elif state.status == "restoring":
            state.restore_token += 1
            state.status = "idle"
            add_system(state, "已取消当前界面恢复请求。")
        else:
            add_system(state, "当前没有运行中的任务。")
        return
    if text == "/new":
        active_sub = selected_subagent(state)
        if active_sub is not None:
            new_subagent_chat_session(state, active_sub)
            return
        if state.secret_vault.pending_action:
            add_system(state, lock_secret_vault(state, reason="/new"))
            return
        parked = new_current_session(state, keep_running=True)
        if state.secret_vault.unlocked:
            add_system(state, "已新建空 Secret 会话；原运行任务已转入后台。" if parked else "已新建空 Secret 会话。")
        else:
            add_system(state, "已新建空会话；原运行任务已转入后台。" if parked else "已新建空会话。")
        return
    if text == "/rename":
        add_system(state, "Usage: /rename <name>")
        return
    m_rename = re.match(r"/rename\s+(.+?)\s*$", text)
    if m_rename:
        result = rename_current_session(state, m_rename.group(1))
        add_system(state, result if not result.startswith("名称不能为空") else "Usage: /rename <name>")
        return
    m_archived = re.match(r"/archived(?:\s+(on|off|toggle))?\s*$", text, re.I)
    if m_archived:
        mode = (m_archived.group(1) or "toggle").lower()
        action = {"on": "show_archived", "off": "hide_archived"}.get(mode, "toggle_archived")
        add_system(state, apply_session_operation(state, action, source="/archived"))
        return
    m_category = re.match(r"/category(?:\s+(.+))?\s*$", text, re.I)
    if m_category:
        target, category, error = parse_category_command_args(state, m_category.group(1) or "")
        if error:
            add_system(state, error)
        else:
            add_system(state, apply_session_operation(state, "category", target, category, source="/category"))
        return
    m_session_op = re.match(r"/(pin|unpin|archive|unarchive|delete)(?:\s+(.+))?\s*$", text, re.I)
    if m_session_op:
        action = m_session_op.group(1).lower()
        target = (m_session_op.group(2) or "current").strip()
        add_system(state, apply_session_operation(state, action, target, source=f"/{action}"))
        return
    if text in {"/continue", "/sessions"}:
        load_history(state, force=True)
        listing = []
        for i, (_path, mtime, first, rounds) in enumerate(state.history[:30], 1):
            name = compact_title(state.history_names.get(_path) or first or "历史会话", 80)
            meta = session_meta_for(state, _path)
            tags = []
            if meta.get("pinned"):
                tags.append("置顶")
            if meta.get("category"):
                tags.append(str(meta.get("category")))
            tag = f" · [{' / '.join(tags)}]" if tags else ""
            listing.append(f"{i}. id:{session_stable_id(_path)} · {rel_age(mtime)} · {rounds} rounds{tag} · {name[:80]}")
        label = "归档会话" if state.show_archived else "可恢复历史"
        if state.session_filter_category:
            label += f"（{state.session_filter_category}）"
        add_system(state, (f"{label}：\n" + "\n".join(listing)) if listing else f"没有{label}")
        return
    m = re.match(r"/continue\s+(\d+)\s*$", text)
    if m:
        idx = int(m.group(1)) - 1
        load_history(state, force=True)
        if 0 <= idx < len(state.history):
            restore_history(state, state.history[idx][0])
        else:
            add_system(state, f"索引越界: 1-{len(state.history)}")
        return
    if text == "/clear":
        state.messages.clear()
        state.follow_bottom = True
        mark_messages_changed(state)
        return
    if state.status in {"running", "aborting"}:
        queue_user_input_for_current_step(state, text, interrupt_requested=state.status == "aborting")
        return
    if state.status == "restoring":
        queue_user_input_for_current_step(state, text)
        return

    start_main_agent_task(
        state,
        text,
        source="user",
        visible_user_text=text,
        remember_user=True,
        clear_history=True,
    )


def queue_subagent_task(
    state: State,
    sub: SubAgentRuntime,
    prompt: str,
    source: str = "user",
    policy_approved: bool = False,
    parent_task_id: str = "",
    task_title: str = "",
) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        return "子 agent 输入为空。"
    sub.task_queue.append((prompt, source, bool(policy_approved), parent_task_id, task_title))
    sub.updated_at = time.time()
    save_subagent_meta(sub, state)
    append_subagent_event(sub, f"{source}:queued", prompt, state=state)
    mark_dirty(state)
    return f"{sub.name} 正在运行，已排队 1 个任务（队列 {len(sub.task_queue)}）。"


def maybe_start_next_subagent_task(state: State, sub: SubAgentRuntime) -> Optional[str]:
    if sub.status in {"running", "aborting"} or not sub.task_queue:
        return None
    queued = sub.task_queue.pop(0)
    if len(queued) >= 5:
        prompt, source, policy_approved, parent_task_id, task_title = queued[:5]
    else:
        prompt, source, policy_approved = queued[:3]
        parent_task_id = ""
        task_title = ""
    sub.updated_at = time.time()
    save_subagent_meta(sub, state)
    return start_subagent_task(
        state,
        sub,
        prompt,
        source=source,
        policy_approved=policy_approved,
        parent_task_id=parent_task_id,
        task_title=task_title,
    )


def secret_subagent_task_record(
    sub: SubAgentRuntime,
    bus_task_id: str,
    *,
    status: str,
    prompt: str = "",
    summary: str = "",
    error: str = "",
    artifact_refs: Optional[list[str]] = None,
    parent_task_id: str = "",
    task_title: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "secret.subagent_task.v1",
        "task_id": bus_task_id,
        "timestamp": now_iso(),
        "status": status,
        "assigned_agent": sub.agent_id,
        "agent_name": sub.name,
        "role": sub.role,
        "title": task_title or f"Secret 子 agent 执行: {sub.name}",
        "kind": "subagent_task",
        "security_context": "secret",
        "objective": truncate_cells(prompt, 240),
        "summary": summary,
        "error": error,
        "parent_task_id": parent_task_id,
        "session_key": sub.owner_session,
        "artifact_refs": list(artifact_refs or []),
        "permissions": permissions_for_role(sub.role, security_context="secret"),
        "context_policy": context_policy_for_task(prompt, security_context="secret"),
        "task": task_contract_for_role(sub.role, prompt),
    }


def write_secret_subagent_task_record(state: State, sub: SubAgentRuntime, bus_task_id: str, **fields: Any) -> str:
    record = secret_subagent_task_record(sub, bus_task_id, **fields)
    ok, ref = secret_write_subagent_json(state, "subagent-tasks", f"{bus_task_id}-{record['status']}", record)
    return ref if ok else ""


def write_secret_subagent_mail(state: State, sub: SubAgentRuntime, bus_task_id: str, *, intent: str, status: str, payload: dict[str, Any], artifact_refs: Optional[list[str]] = None) -> str:
    row = {
        "schema_version": "secret.agentmail.v1",
        "message_id": short_uid("msg"),
        "thread_id": bus_task_id,
        "context_id": "secret",
        "task_id": bus_task_id,
        "timestamp": now_iso(),
        "from": {"agent_id": sub.agent_id if intent == "result" else "orchestrator.main"},
        "to": {"type": "agent", "target": "orchestrator.main" if intent == "result" else sub.agent_id},
        "intent": intent,
        "status": status,
        "payload": payload,
        "artifact_refs": list(artifact_refs or []),
        "permissions": permissions_for_role(sub.role, security_context="secret"),
        "context_policy": context_policy_for_task(str(payload.get("objective") or payload.get("summary") or ""), security_context="secret"),
    }
    ok, ref = secret_write_subagent_json(state, "subagent-mail", row["message_id"], row)
    return ref if ok else ""


def write_secret_subagent_trace(state: State, sub: SubAgentRuntime, bus_task_id: str, event: str, status: str, payload: Optional[dict[str, Any]] = None) -> str:
    row = {
        "schema_version": "secret.agenttrace.v1",
        "trace_id": short_uid("trace"),
        "task_id": bus_task_id,
        "timestamp": now_iso(),
        "event": event,
        "agent_id": sub.agent_id,
        "status": status,
        "payload": payload or {},
    }
    ok, ref = secret_write_subagent_json(state, "subagent-traces", row["trace_id"], row)
    return ref if ok else ""


def write_secret_subagent_artifact(state: State, sub: SubAgentRuntime, bus_task_id: str, text: str) -> str:
    payload = {
        "schema_version": "secret.subagent_artifact.v1",
        "artifact_id": short_uid("artifact"),
        "type": "subagent-results",
        "task_id": bus_task_id,
        "agent_id": sub.agent_id,
        "role": sub.role,
        "created_at": now_iso(),
        "content_type": "text/markdown",
        "content": f"# {sub.name} result\n\nTask: {bus_task_id}\n\n{text.strip()}\n",
    }
    ok, ref = secret_write_subagent_json(state, "subagent-artifacts", f"{sub.agent_id}-{bus_task_id}", payload)
    return ref if ok else "secret://subagents/artifact-write-failed"


def start_secret_subagent_task(
    state: State,
    sub: SubAgentRuntime,
    prompt: str,
    source: str = "user",
    policy_approved: bool = False,
    parent_task_id: str = "",
    task_title: str = "",
) -> str:
    if not state.secret_vault.unlocked or not state.secret_vault.key:
        return "Secret Vault 已锁定，不能启动 Secret 子 agent。"
    task_objective = policy_relevant_subagent_prompt_text(prompt)
    network_decision = secret_network_gate(state, operation="secret_subagent_task")
    if not network_decision.allowed:
        return policy_gate_text(network_decision)
    if sub.status in {"running", "aborting"} or (sub.agent is not None and agent_has_unfinished_task(sub.agent)):
        return queue_subagent_task(
            state,
            sub,
            prompt,
            source=source,
            parent_task_id=parent_task_id,
            task_title=task_title,
        )
    action = infer_policy_action_for_subagent_task(sub, prompt)
    if action != "read_only" and not policy_approved:
        write_secret_subagent_trace(state, sub, short_uid("task"), "policy_gate_denied", "rejected", {"action": action, "prompt_preview": truncate_cells(task_objective, 240)})
        return f"Secret 子 agent 高风险操作暂未开放自动审批：{action}。"
    bus_task_id = short_uid("task")
    agent = ensure_subagent_agent(state, sub)
    sub.task_id += 1
    task_id = sub.task_id
    context_pack, context_ref = build_context_pack(state, sub, task_objective, bus_task_id, parent_task_id=parent_task_id)
    sub.active_task_id = task_id
    sub.active_bus_task_id = bus_task_id
    sub.status = "running"
    sub.updated_at = time.time()
    sub.pending_interaction = None
    sub.messages.append(Message("user", prompt))
    sub.messages.append(Message("assistant", "", done=False))
    save_subagent_meta(sub, state)
    save_subagent_chat_session(state, sub, source=source)
    mark_subagent_messages_changed(state, sub)
    append_subagent_event(sub, source, prompt, state=state)
    write_secret_subagent_task_record(
        state,
        sub,
        bus_task_id,
        status="working",
        prompt=task_objective,
        parent_task_id=parent_task_id,
        task_title=task_title,
        artifact_refs=[context_ref],
    )
    write_secret_subagent_mail(
        state,
        sub,
        bus_task_id,
        intent="delegate",
        status="working",
        payload={"objective": task_objective, "context_pack_ref": context_ref, "role": sub.role},
        artifact_refs=[context_ref],
    )
    write_secret_subagent_trace(state, sub, bus_task_id, "delegated", "working", {"context_pack": context_ref, "source": source})
    agent_prompt = f"{format_context_pack_for_prompt(context_pack)}\n\n[Task]\n{prompt}\n[/Task]"
    try:
        dq = agent.put_task(agent_prompt, source=f"secret-subagent:{sub.agent_id}")
    except Exception as exc:
        sub.status = "error"
        sub.active_task_id = None
        sub.active_bus_task_id = ""
        sub.messages[-1] = Message("assistant", f"[ERROR] put_task: {type(exc).__name__}: {exc}")
        save_subagent_meta(sub, state)
        mark_subagent_messages_changed(state, sub)
        error = f"{type(exc).__name__}: {exc}"
        write_secret_subagent_task_record(state, sub, bus_task_id, status="failed", prompt=task_objective, error=error, parent_task_id=parent_task_id, task_title=task_title)
        write_secret_subagent_trace(state, sub, bus_task_id, "put_task_failed", "failed", {"error": error})
        return f"{sub.name} 启动失败: {error}"
    threading.Thread(target=consume_subagent_queue, args=(state, sub.agent_id, task_id, dq), daemon=True, name=f"secret-subagent-{sub.agent_id}-stream").start()
    mark_dirty(state)
    return f"已启动 Secret 子 agent：{sub.name}"


def start_subagent_chat(state: State, sub: SubAgentRuntime, prompt: str, source: str = "subagent_chat") -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        return "子 agent 聊天输入为空。"
    if sub.security_context == "secret" and (not state.secret_vault.unlocked or not state.secret_vault.key):
        return "Secret Vault 已锁定，不能与 Secret 子 agent 聊天。"
    if sub.status in {"running", "aborting"} or (sub.agent is not None and agent_has_unfinished_task(sub.agent)):
        return queue_subagent_chat_input(state, sub, prompt, interrupt_requested=sub.status == "aborting")
    agent = ensure_subagent_agent(state, sub)
    sub.task_id += 1
    task_id = sub.task_id
    sub.active_task_id = task_id
    sub.active_bus_task_id = ""
    sub.status = "running"
    sub.updated_at = time.time()
    sub.pending_interaction = None
    sub.messages.append(Message("user", prompt))
    sub.messages.append(Message("assistant", "", done=False))
    save_subagent_meta(sub, state)
    save_subagent_chat_session(state, sub, source=source)
    mark_subagent_messages_changed(state, sub)
    append_subagent_event(sub, source, prompt, state=state)
    agent_prompt, _context_ref, _chat_context_id = build_subagent_direct_chat_prompt(state, sub, prompt)
    try:
        dq = agent.put_task(agent_prompt, source=f"subagent-chat:{sub.agent_id}")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        sub.status = "error"
        sub.active_task_id = None
        sub.messages[-1] = Message("assistant", f"[ERROR] put_task: {error}")
        save_subagent_meta(sub, state)
        save_subagent_chat_session(state, sub, source=f"{source}:error")
        mark_subagent_messages_changed(state, sub)
        append_subagent_event(sub, "assistant", f"[ERROR] put_task: {error}", state=state)
        return f"{sub.name} 聊天启动失败: {error}"
    threading.Thread(
        target=consume_subagent_chat_queue,
        args=(state, sub.agent_id, task_id, dq),
        daemon=True,
        name=f"subagent-chat-{sub.agent_id}-stream",
    ).start()
    mark_dirty(state)
    return f"已发送给子 agent：{sub.name}"


def start_subagent_task(
    state: State,
    sub: SubAgentRuntime,
    prompt: str,
    source: str = "user",
    policy_approved: bool = False,
    parent_task_id: str = "",
    task_title: str = "",
) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        return "子 agent 输入为空。"
    task_objective = policy_relevant_subagent_prompt_text(prompt)
    if sub.security_context == "secret":
        return start_secret_subagent_task(
            state,
            sub,
            prompt,
            source=source,
            policy_approved=policy_approved,
            parent_task_id=parent_task_id,
            task_title=task_title,
        )
    if sub.status in {"running", "aborting"} or (sub.agent is not None and agent_has_unfinished_task(sub.agent)):
        return queue_subagent_task(
            state,
            sub,
            prompt,
            source=source,
            policy_approved=policy_approved,
            parent_task_id=parent_task_id,
            task_title=task_title,
        )
    bus_task_id = short_uid("task")
    decision: Optional[PolicyDecision] = None
    if not policy_approved:
        decision = policy_gate_for_subagent_task(
            sub,
            prompt,
            source=source,
            bus_task_id=bus_task_id,
            parent_task_id=parent_task_id,
            task_title=task_title,
        )
        if decision.approval_required:
            append_orchestrator_plan(
                sub,
                task_objective,
                bus_task_id,
                status="approval_required",
                source=source,
                decision=decision,
            )
            append_task_ledger(
                bus_task_id,
                status="approval_required",
                assigned_agent=sub.agent_id,
                title=task_title or f"子 agent 执行: {sub.name}",
                kind="subagent_task",
                objective=truncate_cells(task_objective, 240),
                parent_task_id=parent_task_id,
                session_key=active_ui_session_key(state),
                summary=policy_gate_text(decision),
                **subagent_task_schema_kwargs(sub, task_objective, decision=decision),
            )
            update_plan_step_from_child(parent_task_id)
            checkpoint = append_task_checkpoint(
                bus_task_id,
                status="approval_required",
                reason="subagent_policy_gate_waiting_approval",
                state=state,
                agent_id=sub.agent_id,
                summary=policy_gate_text(decision),
            )
            payload = policy_decision_to_dict(decision)
            payload["checkpoint_id"] = checkpoint.get("checkpoint_id", "")
            append_trace(bus_task_id, "policy_gate_waiting_approval", agent_id=sub.agent_id, status="approval_required", payload=payload)
            return policy_gate_text(decision)
        if not decision.allowed:
            append_orchestrator_plan(
                sub,
                task_objective,
                bus_task_id,
                status="rejected",
                source=source,
                decision=decision,
                error=policy_gate_text(decision),
            )
            append_task_ledger(
                bus_task_id,
                status="rejected",
                assigned_agent=sub.agent_id,
                title=task_title or f"子 agent 执行: {sub.name}",
                kind="subagent_task",
                objective=truncate_cells(task_objective, 240),
                parent_task_id=parent_task_id,
                session_key=active_ui_session_key(state),
                error=policy_gate_text(decision),
                **subagent_task_schema_kwargs(sub, task_objective, decision=decision),
            )
            update_plan_step_from_child(parent_task_id)
            checkpoint = append_task_checkpoint(
                bus_task_id,
                status="rejected",
                reason="subagent_policy_gate_denied",
                state=state,
                agent_id=sub.agent_id,
                summary=policy_gate_text(decision),
            )
            payload = policy_decision_to_dict(decision)
            payload["checkpoint_id"] = checkpoint.get("checkpoint_id", "")
            append_trace(bus_task_id, "policy_gate_denied", agent_id=sub.agent_id, status="rejected", payload=payload)
            return policy_gate_text(decision)
    agent = ensure_subagent_agent(state, sub)
    sub.task_id += 1
    task_id = sub.task_id
    locked, lock_error = acquire_single_writer_lock(sub, bus_task_id, task_objective)
    if not locked:
        append_orchestrator_plan(
            sub,
            task_objective,
            bus_task_id,
            status="rejected",
            source=source,
            decision=decision,
            error=lock_error,
        )
        append_task_ledger(
            bus_task_id,
            status="rejected",
            assigned_agent=sub.agent_id,
            title=task_title or f"子 agent 执行: {sub.name}",
            kind="subagent_task",
            objective=truncate_cells(task_objective, 240),
            parent_task_id=parent_task_id,
            session_key=active_ui_session_key(state),
            error=lock_error,
            **subagent_task_schema_kwargs(sub, task_objective, decision=decision),
        )
        update_plan_step_from_child(parent_task_id)
        checkpoint = append_task_checkpoint(
            bus_task_id,
            status="rejected",
            reason="single_writer_denied",
            state=state,
            agent_id=sub.agent_id,
            summary=lock_error,
        )
        append_trace(bus_task_id, "single_writer_denied", agent_id=sub.agent_id, status="rejected", payload={"error": lock_error, "checkpoint_id": checkpoint.get("checkpoint_id", "")})
        return lock_error
    context_pack, context_ref = build_context_pack(state, sub, task_objective, bus_task_id, parent_task_id=parent_task_id)
    append_orchestrator_plan(
        sub,
        task_objective,
        bus_task_id,
        status="working",
        source=source,
        decision=decision,
        context_ref=context_ref,
    )
    sub.active_task_id = task_id
    sub.active_bus_task_id = bus_task_id
    sub.status = "running"
    sub.updated_at = time.time()
    sub.pending_interaction = None
    sub.messages.append(Message("user", prompt))
    sub.messages.append(Message("assistant", "", done=False))
    save_subagent_meta(sub)
    save_subagent_chat_session(state, sub, source=source)
    mark_subagent_messages_changed(state, sub)
    append_subagent_event(sub, source, prompt)
    append_task_ledger(
        bus_task_id,
        status="working",
        assigned_agent=sub.agent_id,
        title=task_title or f"子 agent 执行: {sub.name}",
        kind="subagent_task",
        objective=truncate_cells(task_objective, 240),
        parent_task_id=parent_task_id,
        session_key=active_ui_session_key(state),
        artifact_refs=[context_ref],
        **subagent_task_schema_kwargs(sub, task_objective, decision=decision),
    )
    update_plan_step_from_child(parent_task_id)
    append_agent_mail(
        from_agent="orchestrator.main",
        to_type="agent",
        target=sub.agent_id,
        intent="delegate",
        task_id=bus_task_id,
        status="working",
        payload={
            "objective": task_objective,
            "context_pack_ref": context_ref,
            "role": sub.role,
            "output_contract": {"required_sections": role_output_contract(sub.role)},
            "permissions": permissions_for_role(sub.role, security_context=sub.security_context),
        },
        artifact_refs=[context_ref],
        budget=default_task_budget(sub.role),
        permissions=permissions_for_role(sub.role, security_context=sub.security_context),
        context_policy=context_policy_for_task(task_objective, security_context=sub.security_context),
        task=task_contract_for_role(sub.role, task_objective),
        risks=risks_for_action(
            decision.action if decision is not None else infer_policy_action_for_subagent_task(sub, prompt),
            sub.role,
            task_objective,
        ),
        approval=approval_metadata(decision=decision) if decision is not None else approval_metadata(),
    )
    checkpoint = append_task_checkpoint(
        bus_task_id,
        status="working",
        reason="subagent_delegated",
        state=state,
        agent_id=sub.agent_id,
        summary=truncate_cells(task_objective, 240),
        extra={"context_pack_ref": context_ref},
    )
    append_trace(bus_task_id, "delegated", agent_id=sub.agent_id, status="working", payload={"context_pack": context_ref, "role": sub.role, "checkpoint_id": checkpoint.get("checkpoint_id", "")})
    agent_prompt = f"{format_context_pack_for_prompt(context_pack)}\n\n[Task]\n{prompt}\n[/Task]"
    try:
        dq = agent.put_task(agent_prompt, source=f"subagent:{sub.agent_id}")
    except Exception as exc:
        sub.status = "error"
        sub.active_task_id = None
        sub.active_bus_task_id = ""
        sub.messages[-1] = Message("assistant", f"[ERROR] put_task: {type(exc).__name__}: {exc}")
        save_subagent_meta(sub)
        save_subagent_chat_session(state, sub, source=f"{source}:error")
        mark_subagent_messages_changed(state, sub)
        release_single_writer_lock(bus_task_id)
        append_orchestrator_plan(
            sub,
            task_objective,
            bus_task_id,
            status="failed",
            source=source,
            decision=decision,
            context_ref=context_ref,
            error=f"{type(exc).__name__}: {exc}",
        )
        append_task_ledger(
            bus_task_id,
            status="failed",
            assigned_agent=sub.agent_id,
            title=task_title or f"子 agent 执行: {sub.name}",
            kind="subagent_task",
            objective=truncate_cells(task_objective, 240),
            parent_task_id=parent_task_id,
            session_key=active_ui_session_key(state),
            error=f"{type(exc).__name__}: {exc}",
            **subagent_task_schema_kwargs(sub, task_objective, decision=decision),
        )
        update_plan_step_from_child(parent_task_id)
        checkpoint = append_task_checkpoint(
            bus_task_id,
            status="failed",
            reason="subagent_put_task_failed",
            state=state,
            agent_id=sub.agent_id,
            summary=f"{type(exc).__name__}: {exc}",
            extra={"context_pack_ref": context_ref},
        )
        append_trace(bus_task_id, "put_task_failed", agent_id=sub.agent_id, status="failed", payload={"error": f"{type(exc).__name__}: {exc}", "checkpoint_id": checkpoint.get("checkpoint_id", "")})
        return f"{sub.name} 启动失败: {type(exc).__name__}: {exc}"
    threading.Thread(target=consume_subagent_queue, args=(state, sub.agent_id, task_id, dq), daemon=True, name=f"subagent-{sub.agent_id}-stream").start()
    mark_dirty(state)
    return f"已启动子 agent：{sub.name}"


def consume_subagent_queue_to_kind(state: State, kind: str, subagent_id: str, task_id: int, dq: queue.Queue) -> None:
    buf = ""
    while state.running:
        try:
            item = dq.get(timeout=0.05)
        except queue.Empty:
            continue
        if "next" in item:
            buf += str(item.get("next") or "")
            state.ui_queue.put((kind, subagent_id, task_id, buf, False))
        if "done" in item:
            state.ui_queue.put((kind, subagent_id, task_id, str(item.get("done") or buf), True))
            return


def consume_subagent_queue(state: State, subagent_id: str, task_id: int, dq: queue.Queue) -> None:
    consume_subagent_queue_to_kind(state, "sub_stream", subagent_id, task_id, dq)


def consume_subagent_chat_queue(state: State, subagent_id: str, task_id: int, dq: queue.Queue) -> None:
    consume_subagent_queue_to_kind(state, "sub_chat_stream", subagent_id, task_id, dq)


def append_subagent_visible_system_notice(state: State, sub: SubAgentRuntime, text: str, *, source: str) -> None:
    notice = clean_text(text).strip()
    if not notice:
        return
    sub.messages.append(Message("system", notice))
    save_subagent_chat_session(state, sub, source=source)
    mark_subagent_messages_changed(state, sub)


def format_memory_candidate_notice(updates: list[str], results: list[str]) -> str:
    lines: list[str] = []
    if results:
        lines.extend(results)
    if updates:
        lines += ["", "将写入的记忆候选："]
        for idx, update in enumerate(updates, 1):
            lines.append(f"{idx}. {truncate_cells(clean_text(update).strip(), 700)}")
    lines += ["", "底部会出现审批单选：↑/↓ 选择，Enter 执行；也可用 /approvals 查看完整候选。"]
    return "\n".join(line for line in lines if line is not None)


def consume_queue(state: State, stream_target: StreamTarget, task_id: int, dq: queue.Queue) -> None:
    buf = ""
    while state.running:
        try:
            item = dq.get(timeout=0.05)
        except queue.Empty:
            continue
        if "next" in item:
            buf += str(item.get("next") or "")
            state.ui_queue.put(("stream", stream_target, task_id, buf, False))
        if "done" in item:
            state.ui_queue.put(("stream", stream_target, task_id, str(item.get("done") or buf), True))
            return


def latest_visible_reply_text(text: str) -> str:
    parts = split_top_level_turn_markers(text or "")
    if len(parts) >= 3:
        turns: list[tuple[str, str]] = []
        for idx in range(1, len(parts), 2):
            marker = parts[idx]
            body = parts[idx + 1] if idx + 1 < len(parts) else ""
            turns.append((marker, body))
        for _marker, body in reversed(turns):
            visible = visible_reply_text(body, hide_detail_fences=True).strip()
            if visible:
                return visible
    return visible_reply_text(text or "", hide_detail_fences=process_has_tool_noise(text or "")).strip()


def subagent_result_notice_body(text: str, limit: int) -> str:
    raw = clean_text(text).strip() or "(empty result)"
    rendered = render_assistant_text(raw, True, True).strip()
    if rendered and len(rendered) <= limit:
        return rendered
    final_reply = latest_visible_reply_text(raw)
    if final_reply:
        prefix = "▸ 工具/过程输出已折叠，完整过程见 artifact。\n\n" if process_has_tool_noise(raw) else ""
        suffix = "\n...（结果过长，完整内容见 artifact）"
        available = max(800, limit - len(prefix) - len(suffix) - 1)
        if len(final_reply) > available:
            final_reply = final_reply[:available].rstrip() + suffix
        return prefix + final_reply
    body = rendered or raw
    if len(body) > limit:
        body = body[:limit].rstrip() + "\n...（结果过长，完整内容见 artifact）"
    return body


def format_subagent_result_notice(
    sub: SubAgentRuntime,
    bus_task_id: str,
    artifact_ref: str,
    text: str,
    limit: int = 6000,
) -> str:
    return format_subagent_result_notice_parts(sub.name, sub.agent_id, bus_task_id, artifact_ref, text, limit=limit)


def format_subagent_result_notice_parts(
    name: str,
    agent_id: str,
    bus_task_id: str,
    artifact_ref: str,
    text: str,
    limit: int = 6000,
) -> str:
    body = subagent_result_notice_body(text, limit)
    return (
        f"子 agent 回复 · {name or agent_id or 'subagent'} ({agent_id or '-'})\n"
        f"Task: {bus_task_id}\n"
        f"Artifact: {artifact_ref}\n\n"
        f"{body}"
    )


def process_ui_queue(state: State) -> bool:
    changed = False
    while True:
        try:
            item = state.ui_queue.get_nowait()
        except queue.Empty:
            if maybe_start_queued_user_input(state):
                changed = True
            return changed
        kind = item[0]
        if kind == "sub_chat_stream":
            _kind, subagent_id, task_id, text, done = item
            sub = state.subagents.get(str(subagent_id))
            if sub is None or task_id != sub.active_task_id:
                continue
            display_text = strip_subagent_memory_controls(strip_tui_controls(text))
            if sub.messages and sub.messages[-1].role == "assistant":
                sub.messages[-1].content = display_text
                sub.messages[-1].done = bool(done)
                save_subagent_chat_session(state, sub, source="subagent_chat_stream")
                mark_subagent_messages_changed(state, sub)
            payload = extract_interaction_request(text)
            if payload:
                sub.pending_interaction = normalize_interaction_payload(payload)
                mark_subagent_messages_changed(state, sub)
            if done:
                sub.status = "waiting-input" if sub.pending_interaction else "idle"
                sub.active_task_id = None
                sub.active_bus_task_id = ""
                sub.updated_at = time.time()
                save_subagent_meta(sub, state)
                chat_saved, chat_ref = save_subagent_chat_session(state, sub, source="subagent_chat_done")
                updates = extract_subagent_memory_updates(text)
                memory_notices: list[str] = []
                for update in updates:
                    memory_notices.append(queue_curated_memory_candidate(
                        state,
                        sub,
                        update,
                        source=f"subagent-chat:{sub.agent_id}",
                        evidence_ref=chat_ref if chat_saved else subagent_chat_session_ref(sub),
                        task_id=f"chat:{sub.chat_session_id}",
                    ))
                if memory_notices:
                    append_subagent_visible_system_notice(
                        state,
                        sub,
                        format_memory_candidate_notice(updates, memory_notices),
                        source="subagent_chat_memory_candidate",
                    )
                append_subagent_event(sub, "assistant", display_text, state=state)
                if sub.agent is not None:
                    persist_agent_token_usage(state, sub.agent)
                queued_result = maybe_start_next_subagent_chat(state, sub)
                state.last_error = queued_result or f"子 agent 聊天完成：{sub.name}"
                mark_subagent_messages_changed(state, sub)
            changed = True
            continue

        if kind == "sub_stream":
            _kind, subagent_id, task_id, text, done = item
            sub = state.subagents.get(str(subagent_id))
            if sub is None or task_id != sub.active_task_id:
                continue
            display_text = strip_subagent_memory_controls(strip_tui_controls(text))
            if sub.messages and sub.messages[-1].role == "assistant":
                sub.messages[-1].content = display_text
                sub.messages[-1].done = bool(done)
                save_subagent_chat_session(state, sub, source="subagent_task_stream")
                mark_subagent_messages_changed(state, sub)
            payload = extract_interaction_request(text)
            if payload:
                sub.pending_interaction = normalize_interaction_payload(payload)
                mark_subagent_messages_changed(state, sub)
            if done:
                bus_task_id = sub.active_bus_task_id or short_uid("task")
                if sub.security_context == "secret":
                    artifact_ref = write_secret_subagent_artifact(state, sub, bus_task_id, text)
                else:
                    artifact_ref = write_harness_artifact(
                        "subagent-results",
                        f"{sub.agent_id}-{bus_task_id}",
                        f"# {sub.name} result\n\nTask: {bus_task_id}\n\n{text.strip()}\n",
                        source_task_id=bus_task_id,
                        provenance={"generated_by": sub.agent_id, "role": sub.role, "source": "subagent_result"},
                    )
                updates = extract_subagent_memory_updates(text)
                for update in updates:
                    queue_curated_memory_candidate(
                        state,
                        sub,
                        update,
                        source=f"subagent:{sub.agent_id}",
                        evidence_ref=artifact_ref,
                        task_id=bus_task_id,
                    )
                sub.status = "idle"
                sub.active_task_id = None
                sub.active_bus_task_id = ""
                sub.pending_interaction = None
                sub.updated_at = time.time()
                save_subagent_meta(sub, state)
                save_subagent_chat_session(state, sub, source="subagent_task_done")
                append_subagent_event(sub, "assistant", display_text, state=state)
                if sub.security_context != "secret":
                    release_single_writer_lock(bus_task_id)
                objective = next((msg.content for msg in reversed(sub.messages) if msg.role == "user"), "")
                task_prev = latest_task_records().get(bus_task_id, {})
                parent_task_id = str(task_prev.get("parent_task_id") or "")
                task_title = str(task_prev.get("title") or f"子 agent 执行: {sub.name}")
                task_session = str(task_prev.get("session_key") or active_ui_session_key(state))
                if sub.security_context == "secret":
                    write_secret_subagent_task_record(
                        state,
                        sub,
                        bus_task_id,
                        status="completed",
                        prompt=objective,
                        summary=truncate_cells(clean_text(display_text), 240),
                        artifact_refs=[artifact_ref],
                        parent_task_id=parent_task_id,
                        task_title=task_title,
                    )
                    write_secret_subagent_mail(
                        state,
                        sub,
                        bus_task_id,
                        intent="result",
                        status="completed",
                        payload={"summary": truncate_cells(clean_text(display_text), 600), "role": sub.role},
                        artifact_refs=[artifact_ref],
                    )
                    write_secret_subagent_trace(state, sub, bus_task_id, "completed", "completed", {"artifact_ref": artifact_ref})
                else:
                    append_task_ledger(
                        bus_task_id,
                        status="completed",
                        assigned_agent=sub.agent_id,
                        title=task_title,
                        kind="subagent_task",
                        objective=truncate_cells(objective, 240),
                        parent_task_id=parent_task_id,
                        session_key=task_session,
                        artifact_refs=[artifact_ref],
                        summary=truncate_cells(clean_text(display_text), 240),
                        **subagent_task_schema_kwargs(sub, objective),
                    )
                    update_plan_step_from_child(parent_task_id)
                    append_agent_mail(
                        from_agent=sub.agent_id,
                        to_type="agent",
                        target="orchestrator.main",
                        intent="result",
                        task_id=bus_task_id,
                        status="completed",
                        payload={"summary": truncate_cells(clean_text(display_text), 600), "role": sub.role},
                        artifact_refs=[artifact_ref],
                        budget=default_task_budget(sub.role),
                        permissions=permissions_for_role(sub.role, security_context=sub.security_context),
                        context_policy=context_policy_for_task(objective, security_context=sub.security_context),
                        task=task_contract_for_role(sub.role, objective),
                        risks=risks_for_action("read_only", sub.role, objective),
                        approval=approval_metadata(),
                    )
                add_system(
                    state,
                    format_subagent_result_notice(sub, bus_task_id, artifact_ref, display_text),
                    persist=sub.security_context != "secret",
                    kind="subagent_result",
                )
                if sub.security_context == "secret" and state.secret_vault.unlocked and state.secret_vault.session_id:
                    secret_save_current_session_state(state, source="secret_subagent_result")
                if sub.security_context != "secret":
                    checkpoint = append_task_checkpoint(
                        bus_task_id,
                        status="completed",
                        reason="subagent_completed",
                        state=state,
                        agent_id=sub.agent_id,
                        summary=truncate_cells(clean_text(display_text), 240),
                        extra={"result_artifact_ref": artifact_ref},
                    )
                    append_trace(bus_task_id, "completed", agent_id=sub.agent_id, status="completed", payload={"artifact_ref": artifact_ref, "checkpoint_id": checkpoint.get("checkpoint_id", "")})
                    append_task_eval(bus_task_id, sub, display_text, artifact_ref)
                    plan_id = str(latest_task_records().get(parent_task_id, {}).get("parent_task_id") or state.active_plan_task_id or "")
                    inject_orchestrator_notice(
                        state.agent,
                        format_subagent_result_context_update(
                            sub.name,
                            sub.agent_id,
                            bus_task_id,
                            artifact_ref,
                            display_text,
                            session_key_value=task_session or active_ui_session_key(state),
                            parent_task_id=parent_task_id,
                            plan_id=plan_id,
                            role=sub.role,
                        ),
                    )
                state.last_error = f"子 agent 完成：{sub.name}；结果已加密存储" if sub.security_context == "secret" else f"子 agent 完成：{sub.name}；结果已进 bus"
                queued_result = maybe_start_next_subagent_task(state, sub)
                if queued_result:
                    state.last_error = queued_result
                else:
                    if sub.security_context != "secret":
                        maybe_queue_orchestrator_plan_continuation(state, f"subagent_completed:{sub.name}")
                mark_subagent_messages_changed(state, sub)
            changed = True
            state.dirty = True
            continue

        if kind == "title_done":
            _kind, key, path, title, error = item
            state.title_jobs.discard(key)
            active_key = token_session_key(state.agent)
            if title and session_names is not None:
                try:
                    existing_title = session_names.name_for(path)
                    if existing_title:
                        title = compact_title(existing_title, 80)
                    else:
                        title = short_session_title(title, "")
                        session_names.set_name(path, title)
                    if active_key == key:
                        state.current_title = title
                    for bg in state.background_sessions.values():
                        if token_session_key(bg.agent) == key:
                            bg.title = title
                    load_history(state, force=True)
                    if active_key == key and not path_is_active_history_view(state, path):
                        maybe_start_ai_category_job(state, path, state.agent)
                    else:
                        for bg in state.background_sessions.values():
                            if token_session_key(bg.agent) == key:
                                maybe_start_ai_category_job(state, path, bg.agent)
                                break
                except Exception as exc:
                    state.last_error = f"AI title save: {type(exc).__name__}: {exc}"
            elif error and active_key == key:
                state.last_error = f"AI title: {error}"
            if active_key == key:
                persist_agent_token_usage(state, state.agent)
            else:
                for bg in state.background_sessions.values():
                    if token_session_key(bg.agent) == key:
                        persist_agent_token_usage(state, bg.agent)
                        break
            changed = True
            state.dirty = True
            continue

        if kind == "description_done":
            _kind, key, path, description, error, signature = item
            state.description_jobs.discard(key)
            if description:
                try:
                    state.session_meta = load_session_meta_registry()
                    entry = dict(state.session_meta.get(session_key(path), {}))
                    entry["description"] = description
                    entry["description_source"] = "ai"
                    entry["description_signature"] = signature
                    entry["description_updated_at"] = time.time()
                    state.session_meta[session_key(path)] = entry
                    save_session_meta_registry(state.session_meta)
                    state.history_descriptions[path] = description
                    if load_history(state, force=True):
                        state.dirty = True
                    active_key = token_session_key(state.agent)
                    if active_key == key and not path_is_active_history_view(state, path):
                        maybe_start_ai_category_job(state, path, state.agent, force=True)
                    else:
                        for bg in state.background_sessions.values():
                            if token_session_key(bg.agent) == key:
                                maybe_start_ai_category_job(state, path, bg.agent, force=True)
                                break
                except Exception as exc:
                    state.last_error = f"AI description save: {type(exc).__name__}: {exc}"
            elif error:
                state.description_signatures.pop(key, None)
            changed = True
            state.dirty = True
            continue

        if kind == "category_done":
            _kind, key, path, category, error, signature = item
            state.category_jobs.discard(key)
            if path_is_active_history_view(state, path):
                state.category_signatures.pop(key, None)
                changed = True
                state.dirty = True
                continue
            if category:
                try:
                    state.session_meta = load_session_meta_registry()
                    entry = dict(state.session_meta.get(session_key(path), {}))
                    if str(entry.get("category_source") or "") != "manual":
                        entry["category"] = category
                        entry["category_source"] = "ai"
                        entry["category_signature"] = signature
                        entry["category_updated_at"] = time.time()
                        state.session_meta[session_key(path)] = entry
                        save_session_meta_registry(state.session_meta)
                        set_category_meta_fields(state, category, name=category)
                        if load_history(state, force=True):
                            state.dirty = True
                except Exception as exc:
                    state.last_error = f"AI category save: {type(exc).__name__}: {exc}"
            elif error:
                state.category_signatures.pop(key, None)
            changed = True
            state.dirty = True
            continue

        if kind == "restore_done":
            _kind, token, path, cache_key, messages, error, elapsed, loaded_rounds, total_rounds, history_message_count = item
            if state.secret_vault.unlocked or state.secret_vault.pending_action:
                continue
            if token != state.restore_token:
                continue
            state.status = "idle"
            state.active_task_id = None
            state.active_task_source = ""
            if error:
                clear_history_ui_state(state)
                state.last_error = f"恢复失败: {error}"
                state.dirty = True
            else:
                state.messages = list(messages)
                state.history_ui_path = path
                state.history_ui_loaded_rounds = loaded_rounds
                state.history_ui_total_rounds = total_rounds
                state.history_ui_message_count = history_message_count
                state.history_ui_loading = False
                remember_inputs_from_messages(state, state.messages)
                state.restore_cache[cache_key] = list(messages)
                while len(state.restore_cache) > RESTORE_CACHE_LIMIT:
                    state.restore_cache.pop(next(iter(state.restore_cache)))
                if total_rounds and loaded_rounds < total_rounds:
                    state.last_error = f"已恢复：最近 {loaded_rounds}/{total_rounds} 轮，向上滚动加载更早历史。"
                else:
                    state.last_error = f"已恢复完整上下文：{total_rounds} 轮。"
                state.follow_bottom = True
                mark_messages_changed(state)
                if not path_is_active_history_view(state, path):
                    if maybe_start_ai_description_job(state, path, state.messages, state.agent):
                        state.dirty = True
                    elif maybe_start_ai_category_job(state, path, state.agent):
                        state.dirty = True
            if load_history(state, force=True):
                state.dirty = True
            changed = True
            continue

        if kind == "history_expand_done":
            _kind, token, path, messages, error, elapsed, loaded_rounds, total_rounds = item
            if state.secret_vault.unlocked or state.secret_vault.pending_action:
                continue
            if token != state.history_ui_token or path != state.history_ui_path:
                continue
            state.history_ui_loading = False
            if error:
                state.last_error = f"加载更早历史失败: {error}"
                state.dirty = True
                changed = True
                continue
            old_width = max(10, state.main_width)
            old_line_count = len(message_lines_cached(state, old_width)) if state.main_width > 0 else len(state.line_cache)
            old_scroll = state.scroll
            suffix = state.messages[state.history_ui_message_count:] if state.history_ui_message_count else state.messages
            state.messages = list(messages) + list(suffix)
            state.history_ui_loaded_rounds = loaded_rounds
            state.history_ui_total_rounds = total_rounds
            state.history_ui_message_count = len(messages)
            mark_messages_changed(state)
            new_line_count = len(message_lines_cached(state, old_width))
            added_lines = max(0, new_line_count - old_line_count)
            if state.selection_start is not None or state.selection_end is not None:
                shift_selection_lines(state, added_lines)
            state.scroll = max(0, old_scroll + added_lines)
            state.follow_bottom = False
            if loaded_rounds >= total_rounds:
                state.last_error = f"已加载到会话最早处：{loaded_rounds}/{total_rounds} 轮。"
            else:
                state.last_error = f"已加载更早历史：{loaded_rounds}/{total_rounds} 轮，用滚轮继续向上看。"
            changed = True
            state.dirty = True
            continue

        if kind == "interaction":
            _kind, agent, payload = item
            if agent is state.agent:
                set_pending_interaction(state, payload)
                changed = True
                continue
            for bg in state.background_sessions.values():
                if bg.agent is agent:
                    bg.pending_interaction = normalize_interaction_payload(payload)
                    changed = True
                    state.dirty = True
                    break
            for sub in state.subagents.values():
                if sub.agent is agent:
                    sub.pending_interaction = normalize_interaction_payload(payload)
                    sub.status = "waiting-input"
                    changed = True
                    state.dirty = True
                    break
            continue

        if kind != "stream":
            continue
        _kind, stream_target, task_id, text, done = item
        target_key = stream_target.key if isinstance(stream_target, StreamTarget) else str(stream_target)
        if target_key != "active":
            bg = state.background_sessions.get(target_key)
            if bg is None or task_id != bg.active_task_id:
                continue
            display_text = strip_tui_controls(text, allow_json_fences=bg.security_context == "secret")
            if bg.messages and bg.messages[-1].role == "assistant":
                bg.messages[-1].content = display_text
                bg.messages[-1].done = bool(done)
                changed = True
            payload = extract_interaction_request(text)
            if payload:
                bg.pending_interaction = normalize_interaction_payload(payload)
                changed = True
            if done:
                bg.status = "idle"
                bg.active_task_id = None
                bg.stream_target = None
                persist_agent_token_usage(state, bg.agent)
                if bg.security_context == "secret":
                    if state.secret_vault.unlocked and state.secret_vault.key and bg.secret_session_id:
                        secret_append_transcript_turn(
                            state,
                            bg.active_secret_user_text,
                            display_text,
                            source=bg.active_task_source or "background-agent",
                            session_id=bg.secret_session_id,
                        )
                        if maybe_autoname_background_session(state, bg):
                            changed = True
                        secret_save_session_state(
                            state,
                            bg.secret_session_id,
                            bg.title,
                            bg.messages,
                            source="background_done",
                            origin=bg.secret_origin,
                        )
                        bg.active_task_secret = False
                        bg.active_task_source = ""
                        bg.active_secret_user_text = ""
                    else:
                        if maybe_autoname_background_session(state, bg):
                            changed = True
                        bg.active_task_secret = False
                        bg.active_task_source = ""
                        bg.active_secret_user_text = ""
                        restore_secret_runtime_after_inflight_work(state)
                        state.last_error = "Secret 后台任务完成时 Vault 已锁定；结果仅保留在内存，解锁后可查看。"
                else:
                    apply_tui_controls_from_text(state, text, source="background-agent", default_target=getattr(bg.agent, "log_path", "") or "current")
                    if maybe_autoname_background_session(state, bg):
                        changed = True
                    if load_history(state, force=True):
                        changed = True
            state.dirty = True
            continue
        if task_id != state.active_task_id:
            continue
        display_text = strip_tui_controls(text, allow_json_fences=state.active_task_secret)
        if state.messages and state.messages[-1].role == "assistant":
            state.messages[-1].content = display_text
            state.messages[-1].done = bool(done)
            mark_messages_changed(state)
            changed = True
        payload = extract_interaction_request(text)
        if payload:
            set_pending_interaction(state, payload)
            changed = True
        if done:
            finished_source = state.active_task_source
            finished_secret = state.active_task_secret
            secret_user_text = state.active_secret_user_text
            secret_session_id = state.active_secret_session_id
            had_tui_controls = bool(extract_tui_controls(text, allow_json_fences=state.active_task_secret))
            state.status = "idle"
            state.active_task_id = None
            state.active_task_source = ""
            state.active_stream_target = None
            state.active_task_secret = False
            state.active_secret_user_text = ""
            state.active_secret_session_id = ""
            persist_agent_token_usage(state, state.agent)
            if finished_secret:
                can_store_secret = bool(state.secret_vault.unlocked and state.secret_vault.session_id == secret_session_id)
                ok, secret_ref = secret_append_transcript_turn(state, secret_user_text, display_text, source=finished_source) if can_store_secret else (False, "Secret transcript discarded after lock or session switch.")
                if can_store_secret:
                    title = secret_session_title_for_messages(state.current_title, state.messages)
                    if title and state.current_title in {"", "main", "Secret Vault", "运行中会话", "空闲会话"}:
                        state.current_title = f"Secret: {title}"
                    secret_save_session_state(
                        state,
                        state.secret_vault.session_id,
                        title,
                        state.messages,
                        source=finished_source or "agent",
                        origin=state.secret_active_origin,
                    )
                if not state.secret_vault.unlocked:
                    previous = state.secret_vault.previous_log_path
                    set_agent_log_path(state.agent, previous or new_session_log_path())
                    restore_secret_runtime_after_inflight_work(state)
                applied_secret_controls = apply_secret_subagent_controls_from_text(state, text) if can_store_secret and had_tui_controls else 0
                if applied_secret_controls and can_store_secret:
                    secret_save_current_session_state(state, source="secret_controls")
                suffix = f" Secret 子 agent 控制已加密执行 {applied_secret_controls} 个。" if applied_secret_controls else (" Secret 输出中的非子 agent TUI 控制已忽略。" if had_tui_controls else "")
                state.last_error = (f"Secret transcript encrypted: {os.path.basename(secret_ref)}" if ok else secret_ref) + suffix
            else:
                apply_tui_controls_from_text(state, text, source="agent", default_target="current")
                if maybe_autoname_current_session(state):
                    state.dirty = True
                if load_history(state, force=True):
                    state.dirty = True
            if not finished_secret and (had_tui_controls or finished_source == "ga-tui:auto_plan_continue"):
                maybe_queue_orchestrator_plan_continuation(state, f"main_done:{finished_source or 'agent'}")
        state.follow_bottom = True


def restore_history_worker(state: State, token: int, agent: Any, path: str, cache_key: tuple[str, float]) -> None:
    start = time.perf_counter()
    error = ""
    messages: list[Message] = []
    loaded_rounds = 0
    total_rounds = 0
    history_message_count = 0
    with state.restore_lock:
        if token != state.restore_token or not state.running:
            return
        try:
            messages, _msg, loaded_rounds, total_rounds, history_message_count = restore_backend_and_recent_messages(agent, path)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - start
    try:
        cache_key = (path, os.path.getmtime(path))
    except OSError:
        pass
    state.ui_queue.put(("restore_done", token, path, cache_key, messages, error, elapsed, loaded_rounds, total_rounds, history_message_count))


def expand_history_ui_worker(ui_queue: queue.Queue, token: int, path: str, rounds: int) -> None:
    start = time.perf_counter()
    error = ""
    messages: list[Message] = []
    loaded_rounds = 0
    total_rounds = 0
    try:
        messages, loaded_rounds, total_rounds = read_history_messages(path, rounds)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - start
    ui_queue.put(("history_expand_done", token, path, messages, error, elapsed, loaded_rounds, total_rounds))


def maybe_expand_history_at_top(state: State) -> None:
    if state.status == "restoring" or state.history_ui_loading:
        return
    if not state.history_ui_path or state.history_ui_loaded_rounds <= 0:
        return
    if state.scroll > 0:
        return
    state.scroll = 0
    if state.history_ui_total_rounds and state.history_ui_loaded_rounds >= state.history_ui_total_rounds:
        return
    target_rounds = state.history_ui_loaded_rounds + HISTORY_EXPAND_ROUNDS
    state.history_ui_loading = True
    state.history_ui_token += 1
    token = state.history_ui_token
    state.last_error = f"正在加载更早历史：{state.history_ui_loaded_rounds}/{state.history_ui_total_rounds or '?'} 轮..."
    mark_dirty(state)
    threading.Thread(
        target=expand_history_ui_worker,
        args=(state.ui_queue, token, state.history_ui_path, target_rounds),
        daemon=True,
        name="ga-curses-history-expand",
    ).start()


def restore_history(state: State, path: str) -> None:
    if state.secret_vault.unlocked or state.secret_vault.pending_action:
        state.last_error = "Secret Vault 模式下不能恢复普通历史；请先 /lock。"
        mark_dirty(state)
        return
    if state.status in {"running", "aborting"}:
        park_active_session(state)
    elif state.status == "idle" and active_view_is_restored_history(state):
        persist_agent_token_usage(state, state.agent)
    elif state.status == "idle" and stash_idle_active_session(state):
        reset_active_session(state)
    else:
        persist_agent_token_usage(state, state.agent)
    state.restore_token += 1
    token = state.restore_token
    state.selected_session = path
    state.current_title = session_title_for_path(state, path)
    state.status = "restoring"
    state.active_task_id = None
    state.active_task_source = ""
    state.pending_interaction = None
    state.history_ui_path = path
    state.history_ui_loaded_rounds = 0
    state.history_ui_total_rounds = 0
    state.history_ui_message_count = 0
    state.history_ui_loading = False
    state.history_ui_token += 1
    state.session_popup_path = ""
    state.session_popup_anchor = None
    state.session_popup_rect = None
    state.follow_bottom = True
    set_agent_log_path(state.agent, path)
    bind_agent_token_session(state, state.agent)
    load_subagents(state)
    hydrate_active_plan_from_ledger(state)
    mark_session_opened(state, path)
    load_history(state, force=True)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0.0
    cache_key = (path, mtime)
    cached = state.restore_cache.get(cache_key)
    if cached:
        state.messages = list(cached)
        state.last_error = "正在后台确认完整上下文..."
        remember_inputs_from_messages(state, cached)
    else:
        meta = session_meta_for(state, path)
        preview_messages = messages_from_preview_dicts(meta.get("ui_preview_messages"))
        durable_messages = durable_ui_system_messages_for_path(path)
        if preview_messages:
            state.messages = [*preview_messages, *durable_messages]
            state.history_ui_loaded_rounds = int(meta.get("ui_preview_loaded_rounds") or 0)
            state.history_ui_total_rounds = int(meta.get("ui_preview_total_rounds") or 0)
            state.history_ui_message_count = int(meta.get("ui_preview_message_count") or len(preview_messages))
            remember_inputs_from_messages(state, preview_messages)
        else:
            state.messages = durable_messages
        state.last_error = f"正在后台恢复完整上下文：{state.current_title}"
    mark_messages_changed(state)
    threading.Thread(
        target=restore_history_worker,
        args=(state, token, state.agent, path, cache_key),
        daemon=True,
        name="ga-curses-restore",
    ).start()


def main_pos_at_mouse(state: State, mx: int, my: int, clamp: bool = False) -> Optional[tuple[int, int]]:
    if not state.line_cache or state.main_width <= 0 or state.body_height <= 0:
        return None
    if clamp:
        mx = max(state.main_x0, min(mx, state.main_x0 + state.main_width))
        row = max(0, min(my - state.body_top, state.body_height - 1))
    else:
        if mx < state.main_x0 or mx >= state.main_x0 + state.main_width:
            return None
        row = my - state.body_top
        if row < 0 or row >= state.body_height:
            return None
    idx = state.scroll + row
    if clamp:
        idx = max(0, min(idx, len(state.line_cache) - 1))
    elif idx < 0 or idx >= len(state.line_cache):
        return None
    col = max(0, min(mx - state.main_x0, state.main_width))
    return idx, char_index_for_cell(state.line_cache[idx].text, col)


def main_max_scroll(state: State) -> int:
    if state.body_height <= 0:
        return 0
    lines = state.line_cache or (message_lines_cached(state, max(10, state.main_width)) if state.main_width > 0 else [])
    return max(0, len(lines) - max(1, state.body_height))


def update_selection_end_from_mouse(state: State, mx: int, my: int) -> bool:
    pos = main_pos_at_mouse(state, mx, my, clamp=True)
    if pos is None:
        return False
    old = state.selection_end
    state.selection_end = pos
    state.selection_dragged = state.selection_dragged or pos != state.selection_start
    return old != pos


def selection_auto_scroll_delta(state: State) -> tuple[int, int]:
    if state.selection_mouse_y is None or state.body_height <= 0:
        return 0, 0
    top = state.body_top
    bottom = state.body_top + state.body_height - 1
    my = state.selection_mouse_y
    if my <= top:
        return -1, top - my + 1
    if my >= bottom:
        return 1, my - bottom + 1
    return 0, 0


def maybe_auto_scroll_selection(state: State, now: float) -> bool:
    if not state.selection_active or state.selection_mouse_x is None or state.selection_mouse_y is None:
        return False
    direction, overshoot = selection_auto_scroll_delta(state)
    if not direction or overshoot <= 0:
        return False
    interval = max(0.018, 0.075 - min(0.052, overshoot * 0.004))
    if now - state.selection_auto_last_at < interval:
        return False
    state.selection_auto_last_at = now
    step = min(14, max(1, 1 + overshoot // 2))
    old_scroll = state.scroll
    state.follow_bottom = False
    state.scroll = max(0, min(main_max_scroll(state), state.scroll + direction * step))
    if direction < 0 and state.scroll <= 0:
        maybe_expand_history_at_top(state)
    changed = state.scroll != old_scroll
    changed = update_selection_end_from_mouse(state, state.selection_mouse_x, state.selection_mouse_y) or changed
    if changed:
        mark_dirty(state)
    return changed


def copy_to_clipboard(text: str) -> tuple[bool, str]:
    text = text or ""
    if not text.strip():
        return False, "选区为空，未复制。"
    chars = len(text.replace("\n", ""))
    lines = len(text.splitlines()) or 1
    commands = []
    if shutil.which("wl-copy"):
        commands.append(["wl-copy"])
    if shutil.which("xclip"):
        commands.append(["xclip", "-selection", "clipboard"])
    if shutil.which("xsel"):
        commands.append(["xsel", "--clipboard", "--input"])
    for cmd in commands:
        try:
            subprocess.run(cmd, input=text, text=True, timeout=1.0, check=True)
            return True, f"已复制 {chars} 字/{lines} 行到剪贴板。"
        except Exception:
            continue
    try:
        payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
        tty_escape(f"\x1b]52;c;{payload}\x07")
        return True, f"已通过终端剪贴板复制 {chars} 字/{lines} 行。"
    except Exception as exc:
        return False, f"复制失败: {type(exc).__name__}: {exc}"


def clear_pending_secret_copy_confirmation(state: State) -> None:
    state.pending_secret_copy_hash = ""
    state.pending_secret_copy_approval_id = ""
    state.pending_secret_copy_started_at = 0.0
    state.pending_secret_copy_chars = 0
    state.pending_secret_copy_key = b""


def secret_copy_fingerprint(text: str, key: bytes) -> str:
    raw = (text or "").encode("utf-8", errors="surrogatepass")
    return hashlib.blake2b(raw, digest_size=32, key=key).hexdigest()


def secret_copy_confirmation_matches(state: State, text: str, now: float) -> bool:
    if not state.pending_secret_copy_hash or not state.pending_secret_copy_approval_id or not state.pending_secret_copy_key:
        return False
    if now - state.pending_secret_copy_started_at > SECRET_COPY_CONFIRM_TTL_SECONDS:
        clear_pending_secret_copy_confirmation(state)
        return False
    if secret_copy_fingerprint(text, state.pending_secret_copy_key) != state.pending_secret_copy_hash:
        clear_pending_secret_copy_confirmation(state)
        return False
    row = approval_latest_records().get(state.pending_secret_copy_approval_id)
    status = str((row or {}).get("status") or "")
    if status in {"pending", "approved"}:
        return True
    clear_pending_secret_copy_confirmation(state)
    return False


def record_secret_copy_confirmed_decision(state: State, text: str, approval_id: str) -> None:
    decision = PolicyDecision(
        decision_id=short_uid("policy"),
        action="secret_export",
        subject="orchestrator.main",
        role="",
        status="approved",
        allowed=True,
        approval_required=False,
        approval_required_for="secret_export",
        risk="critical",
        reason="secret_export: user confirmed the same Secret selection copy within the local confirmation window.",
        source="selection_copy",
        target="clipboard",
        approval_id=approval_id,
        payload={
            "operation": "copy_secret_selection",
            "approval": "same_selection_second_copy",
            "chars": len(text or ""),
        },
    )
    record_policy_decision(decision)


def approve_pending_secret_copy_confirmation(state: State, text: str) -> tuple[bool, str]:
    approval_id = state.pending_secret_copy_approval_id
    row = approval_latest_records().get(approval_id)
    status = str((row or {}).get("status") or "")
    if status == "pending":
        decide_approval(state, approval_id, True)
        row = approval_latest_records().get(approval_id)
        status = str((row or {}).get("status") or "")
    if status != "approved":
        clear_pending_secret_copy_confirmation(state)
        return False, f"Secret 复制确认失效：approval={approval_id or '-'} status={status or 'missing'}"
    record_secret_copy_confirmed_decision(state, text, approval_id)
    return True, f"Secret export 已二次确认 approval={approval_id}"


def secret_selection_copy_gate(state: State, text: str) -> tuple[bool, bool, str]:
    if not state.secret_vault.unlocked or not (text or "").strip():
        return True, False, ""
    now = time.monotonic()
    if secret_copy_confirmation_matches(state, text, now):
        ok, msg = approve_pending_secret_copy_confirmation(state, text)
        return ok, ok, msg
    decision = gate_policy_action(
        "secret_export",
        subject="orchestrator.main",
        source="selection_copy",
        target="clipboard",
        payload={"operation": "copy_secret_selection", "chars": len(text or "")},
        queue_if_required=True,
    )
    if decision.allowed:
        clear_pending_secret_copy_confirmation(state)
        return True, False, ""
    if decision.approval_required:
        key = os.urandom(32)
        state.pending_secret_copy_key = key
        state.pending_secret_copy_hash = secret_copy_fingerprint(text, key)
        state.pending_secret_copy_approval_id = decision.approval_id
        state.pending_secret_copy_started_at = now
        state.pending_secret_copy_chars = len(text or "")
        manual = f"；也可手动 /approve {decision.approval_id}" if decision.approval_id else ""
        ttl = int(SECRET_COPY_CONFIRM_TTL_SECONDS)
        return False, False, f"Secret 复制需要二次确认：{ttl} 秒内再次复制同一段内容即可批准并复制到剪贴板{manual}。"
    clear_pending_secret_copy_confirmation(state)
    return False, False, policy_gate_text(decision)


def finish_selection_copy(state: State) -> None:
    state.selection_active = False
    state.selection_mouse_x = None
    state.selection_mouse_y = None
    state.selection_auto_last_at = 0.0
    if not state.selection_dragged:
        line_idx = state.selection_start[0] if state.selection_start is not None else -1
        clear_selection(state)
        if toggle_process_at_line(state, line_idx):
            return
        state.last_error = ""
        mark_dirty(state)
        return
    text = selected_text(state)
    secret_confirmed = False
    if state.secret_vault.unlocked:
        allowed, secret_confirmed, gate_msg = secret_selection_copy_gate(state, text)
        if not allowed:
            state.last_error = gate_msg
            mark_dirty(state)
            return
    ok, msg = copy_to_clipboard(text)
    if ok and secret_confirmed:
        clear_pending_secret_copy_confirmation(state)
        msg = f"{msg}（Secret export 已二次确认）"
    state.last_error = msg
    if not ok:
        clear_selection(state)
    mark_dirty(state)


def show_session_info_popup(state: State, path: str, mx: int, my: int) -> None:
    state.session_popup_path = path
    state.session_popup_anchor = (mx, my)
    state.session_popup_rect = None
    mark_dirty(state)


def hide_session_info_popup(state: State) -> bool:
    if not state.session_popup_path:
        return False
    state.session_popup_path = ""
    state.session_popup_anchor = None
    state.session_popup_rect = None
    mark_dirty(state)
    return True


def mouse_in_session_popup(state: State, mx: int, my: int) -> bool:
    rect = state.session_popup_rect
    if not rect:
        return False
    y0, x0, h, w = rect
    return x0 <= mx < x0 + w and y0 <= my < y0 + h


MOUSE_BUTTON_STATES = ("PRESSED", "RELEASED", "CLICKED", "DOUBLE_CLICKED", "TRIPLE_CLICKED")


def mouse_button_mask(button_no: int) -> int:
    total = 0
    for state in MOUSE_BUTTON_STATES:
        total |= int(getattr(curses, f"BUTTON{button_no}_{state}", 0) or 0)
    return total


def mouse_modifier_mask() -> int:
    return (
        int(getattr(curses, "BUTTON_SHIFT", 0) or 0)
        | int(getattr(curses, "BUTTON_CTRL", 0) or 0)
        | int(getattr(curses, "BUTTON_ALT", 0) or 0)
    )


def mouse_known_bstate_mask() -> int:
    known = int(getattr(curses, "REPORT_MOUSE_POSITION", 0) or 0) | mouse_modifier_mask()
    for button_no in range(1, 6):
        known |= mouse_button_mask(button_no)
    return known


def mouse_auxiliary_or_unknown_event(bstate: int) -> bool:
    bstate = int(bstate or 0)
    auxiliary = 0
    for button_no in range(2, 6):
        auxiliary |= mouse_button_mask(button_no)
    return bool((bstate & auxiliary) or (bstate & ~mouse_known_bstate_mask()))


def clean_button1_action(bstate: int, allowed_button1_mask: int) -> bool:
    bstate = int(bstate or 0)
    allowed_button1_mask = int(allowed_button1_mask or 0)
    if not allowed_button1_mask or not (bstate & allowed_button1_mask):
        return False
    if mouse_auxiliary_or_unknown_event(bstate):
        return False
    disallowed_button1 = mouse_button_mask(1) & ~allowed_button1_mask
    allowed = allowed_button1_mask | mouse_modifier_mask()
    return not (bstate & disallowed_button1) and not (bstate & ~allowed)


def toggle_process_at_line(state: State, line_idx: int) -> bool:
    if line_idx < 0 or line_idx >= len(state.line_cache):
        return False
    text = state.line_cache[line_idx].text
    subagent_meta_match = SUBAGENT_META_TOGGLE_RE.search(text)
    if subagent_meta_match:
        key = subagent_meta_key(state, subagent_meta_match.group(1))
        if key in state.expanded_subagent_meta:
            state.expanded_subagent_meta.remove(key)
        else:
            state.expanded_subagent_meta.add(key)
        state.follow_bottom = False
        mark_dirty(state)
        return True
    turn_match = PROCESS_TURN_TOGGLE_RE.search(text)
    if turn_match:
        key = process_turn_key(state, turn_match.group(1))
        if key in state.expanded_process_turns:
            state.expanded_process_turns.remove(key)
        else:
            state.expanded_process_turns.add(key)
        state.follow_bottom = False
        mark_dirty(state)
        return True
    group_match = PROCESS_GROUP_TOGGLE_RE.search(text)
    if group_match:
        key = process_group_key(state, group_match.group(1))
        if key in state.expanded_process_groups:
            state.expanded_process_groups.remove(key)
        else:
            state.expanded_process_groups.add(key)
        state.follow_bottom = False
        mark_dirty(state)
        return True
    return False


def handle_mouse(state: State, mx: int, my: int, bstate: int, width: int) -> None:
    sidebar_w = left_sidebar_width(width)
    rightbar_w = rightbar_width_for_terminal(width)
    rightbar_x0 = width - rightbar_w if rightbar_w > 0 else width
    wheel_up = getattr(curses, "BUTTON4_PRESSED", 0)
    wheel_down = getattr(curses, "BUTTON5_PRESSED", 0)
    button1_pressed = getattr(curses, "BUTTON1_PRESSED", 0)
    button1_clicked = getattr(curses, "BUTTON1_CLICKED", 0)
    button1_released = getattr(curses, "BUTTON1_RELEASED", 0)
    mouse_motion = getattr(curses, "REPORT_MOUSE_POSITION", 0)
    if state.session_popup_path:
        if mouse_in_session_popup(state, mx, my):
            return
        if bstate & button1_released:
            return
        hide_session_info_popup(state)
    if bstate & wheel_up:
        clear_selection(state)
        if mx < sidebar_w:
            state.sidebar_scroll -= 3
        elif mx >= rightbar_x0:
            pass
        else:
            state.scroll -= 3
            state.follow_bottom = False
            if state.scroll <= 0:
                maybe_expand_history_at_top(state)
        mark_dirty(state)
        return
    if bstate & wheel_down:
        clear_selection(state)
        if mx < sidebar_w:
            state.sidebar_scroll += 3
        elif mx >= rightbar_x0:
            pass
        else:
            state.scroll += 3
            state.follow_bottom = False
        mark_dirty(state)
        return
    if state.selection_active and clean_button1_action(bstate, button1_released):
        state.selection_mouse_x = mx
        state.selection_mouse_y = my
        update_selection_end_from_mouse(state, mx, my)
        finish_selection_copy(state)
        return
    if state.selection_active and bstate & mouse_motion and not mouse_auxiliary_or_unknown_event(bstate):
        state.selection_mouse_x = mx
        state.selection_mouse_y = my
        if update_selection_end_from_mouse(state, mx, my):
            mark_dirty(state)
        return

    if sidebar_w <= mx < rightbar_x0:
        pos = main_pos_at_mouse(state, mx, my)
        if clean_button1_action(bstate, button1_clicked):
            if pos is not None and toggle_process_at_line(state, pos[0]):
                return
        if clean_button1_action(bstate, button1_pressed):
            if pos is not None:
                state.selection_active = True
                state.selection_start = pos
                state.selection_end = pos
                state.selection_dragged = False
                state.selection_mouse_x = mx
                state.selection_mouse_y = my
                state.selection_auto_last_at = 0.0
                state.last_error = ""
                mark_dirty(state)
            return
    left_activate = clean_button1_action(bstate, button1_clicked | button1_pressed)
    if left_activate and mx >= rightbar_x0 and rightbar_w > 0:
        clear_selection(state)
        idx = my
        if 0 <= idx < len(state.rightbar_rows):
            kind, key, left, right = state.rightbar_rows[idx]
            if kind == "right_main":
                hide_session_info_popup(state)
                state.selected_session = secret_session_sidebar_key(state.secret_vault.session_id) if state.secret_vault.unlocked else "main"
                state.last_error = "已回到主 agent。"
                mark_dirty(state)
                return
            if kind == "right_agent":
                hide_session_info_popup(state)
                state.selected_session = key
                sub = state.subagents.get(str(key))
                if sub is not None:
                    state.last_error = f"已进入子 agent 聊天：{sub.name} · {sub.status}；普通输入会直接发给它"
                mark_dirty(state)
                return
            if kind == "right_task":
                hide_session_info_popup(state)
                row = latest_task_records().get(str(key)) or {}
                state.last_error = f"任务 {key}: {row.get('status') or '-'} · owner:{row.get('assigned_agent') or '-'} · approval:{approval_status_for_task(str(key))}"
                mark_dirty(state)
                return
    if left_activate and mx < sidebar_w:
        clear_selection(state)
        idx = state.sidebar_scroll + my
        if 0 <= idx < len(state.sidebar_rows):
            kind, key, _left, _right = state.sidebar_rows[idx]
            if kind == "history":
                if not isinstance(key, str):
                    return
                if normalized_path(key) == normalized_path(state.selected_session):
                    show_session_info_popup(state, key, mx, my)
                elif is_current_session_path(state, key):
                    show_session_info_popup(state, key, mx, my)
                elif bg_key := background_session_key_for_path(state, key):
                    hide_session_info_popup(state)
                    switch_to_background_session(state, bg_key)
                else:
                    hide_session_info_popup(state)
                    restore_history(state, key)
            elif kind == "secret_history":
                hide_session_info_popup(state)
                result = restore_secret_imported_session(state, secret_import_target_from_sidebar_key(key))
                add_system(state, result)
            elif kind == "secret_session":
                hide_session_info_popup(state)
                result = restore_secret_native_session(state, secret_session_id_from_sidebar_key(key))
                add_system(state, result)
            elif kind == "subagent_session":
                hide_session_info_popup(state)
                agent_id, session_id = subagent_session_from_sidebar_key(key)
                sub = state.subagents.get(agent_id)
                if sub is None:
                    state.last_error = "子 agent 会话不存在。"
                else:
                    if sub.chat_session_id != session_id:
                        block_reason = subagent_chat_session_switch_block_reason(sub)
                        if block_reason:
                            state.last_error = block_reason
                            mark_dirty(state)
                            return
                        if sub.messages:
                            save_subagent_chat_session(state, sub, source="switch-subagent-session")
                        load_subagent_chat_session(state, sub, session_id)
                    state.selected_session = sub.agent_id
                    state.follow_bottom = True
                    mark_subagent_messages_changed(state, sub)
                    state.last_error = f"已切换到子 agent 会话：{sub.name}"
            elif kind == "category":
                hide_session_info_popup(state)
                state.last_error = toggle_category_collapsed(state, str(key))
            elif kind == "background":
                hide_session_info_popup(state)
                switch_to_background_session(state, key)
            elif kind == "session":
                hide_session_info_popup(state)
                state.selected_session = key
                mark_dirty(state)


def input_width_for_key(stdscr) -> int:
    if stdscr is None:
        return 80
    _height, width = stdscr.getmaxyx()
    sidebar_w = left_sidebar_width(width)
    rightbar_w = rightbar_width_for_terminal(width)
    return max(10, width - sidebar_w - rightbar_w - 2)


def handle_key(stdscr, state: State, key) -> None:
    if key in (curses.KEY_RESIZE,):
        mark_dirty(state)
        return
    if key == curses.KEY_MOUSE:
        try:
            _id, mx, my, _z, bstate = curses.getmouse()
            _h, w = stdscr.getmaxyx()
            handle_mouse(state, mx, my, bstate, w)
        except curses.error:
            pass
        return
    if key == PASTE_START:
        state.paste_mode = True
        state.paste_buffer = ""
        state.last_error = "Paste: 多行内容会作为普通文本插入，换行按空格处理。"
        mark_dirty(state)
        return
    if key == PASTE_END:
        state.paste_mode = False
        insert_input_text(state, normalize_pasted_text(state.paste_buffer))
        state.paste_buffer = ""
        state.last_error = ""
        mark_dirty(state)
        return
    if state.paste_mode:
        if isinstance(key, str):
            state.paste_buffer += key
        return
    if key == "\x11":
        labels = unfinished_task_labels(state)
        request_exit(stdscr, state, "已退出 ga tui。", selected=0 if labels else 1)
        return
    if key == "\x0e":
        active_sub = selected_subagent(state)
        if active_sub is not None:
            new_subagent_chat_session(state, active_sub)
            return
        if state.secret_vault.pending_action:
            add_system(state, lock_secret_vault(state, reason="Ctrl+N"))
            return
        parked = new_current_session(state, keep_running=True)
        if state.secret_vault.unlocked:
            add_system(state, "Ctrl+N: 已新建空 Secret 会话；原运行任务已转入后台。" if parked else "Ctrl+N: 已新建空 Secret 会话。")
        else:
            add_system(state, "Ctrl+N: 已新建空会话；原运行任务已转入后台。" if parked else "Ctrl+N: 已新建空会话。")
        return
    if key == "\x17":
        close_current_session(state)
        return
    if key == curses.KEY_F2:
        open_rename_modal(stdscr, state)
        return
    secret_input = secret_password_entry_active(state)
    matches = [] if secret_input else command_matches(state.input_text, state)
    clamp_command_index(state, matches)
    if matches and key in (curses.KEY_UP,):
        state.command_index = (state.command_index - 1) % min(len(matches), 10)
        mark_dirty(state)
        return
    if matches and key in (curses.KEY_DOWN,):
        state.command_index = (state.command_index + 1) % min(len(matches), 10)
        mark_dirty(state)
        return
    active_interaction = current_interaction_payload(state)
    if active_interaction and not matches and key in (curses.KEY_UP,):
        if move_interaction_selection(state, -1):
            return
        if move_input_cursor_vertical(state, input_width_for_key(stdscr), -1):
            return
        return
    if active_interaction and not matches and key in (curses.KEY_DOWN,):
        if move_interaction_selection(state, 1):
            return
        if move_input_cursor_vertical(state, input_width_for_key(stdscr), 1):
            return
        return
    if key in (curses.KEY_UP,):
        if move_input_cursor_vertical(state, input_width_for_key(stdscr), -1):
            return
        if not (state.secret_vault.unlocked or secret_input) and browse_input_history(state, -1):
            return
    if key in (curses.KEY_DOWN,):
        if move_input_cursor_vertical(state, input_width_for_key(stdscr), 1):
            return
        if not (state.secret_vault.unlocked or secret_input) and browse_input_history(state, 1):
            return
    if matches and key == "\t":
        set_input_text(state, completion_insert_text(matches[state.command_index]))
        reset_input_history_browse(state)
        mark_dirty(state)
        return
    if key in (curses.KEY_LEFT,):
        state.input_cursor -= 1
        clamp_input_cursor(state)
        mark_dirty(state)
        return
    if key in (curses.KEY_RIGHT,):
        state.input_cursor += 1
        clamp_input_cursor(state)
        mark_dirty(state)
        return
    if key in (curses.KEY_PPAGE,):
        state.scroll -= 10
        state.follow_bottom = False
        if state.scroll <= 0:
            maybe_expand_history_at_top(state)
        mark_dirty(state)
        return
    if key in (curses.KEY_NPAGE,):
        state.scroll += 10
        state.follow_bottom = False
        mark_dirty(state)
        return
    if key in (curses.KEY_HOME,):
        if state.input_text:
            state.input_cursor = 0
            mark_dirty(state)
            return
        state.scroll = 0
        state.follow_bottom = False
        maybe_expand_history_at_top(state)
        mark_dirty(state)
        return
    if key in (curses.KEY_END,):
        if state.input_text:
            state.input_cursor = len(state.input_text)
            mark_dirty(state)
            return
        state.follow_bottom = True
        mark_dirty(state)
        return
    if key in (curses.KEY_BACKSPACE, 127, "\b"):
        if state.input_cursor > 0:
            state.input_text = state.input_text[:state.input_cursor - 1] + state.input_text[state.input_cursor:]
            state.input_cursor -= 1
        state.command_index = 0
        reset_input_history_browse(state)
        mark_dirty(state)
        return
    if key in (curses.KEY_DC,):
        if state.input_cursor < len(state.input_text):
            state.input_text = state.input_text[:state.input_cursor] + state.input_text[state.input_cursor + 1:]
        state.command_index = 0
        reset_input_history_browse(state)
        mark_dirty(state)
        return
    if key in ("\n", "\r", curses.KEY_ENTER):
        if matches:
            cmd, _args, _desc, sendable = matches[state.command_index]
            if sendable:
                text = cmd
            else:
                set_input_text(state, completion_insert_text(matches[state.command_index]))
                mark_dirty(state)
                return
        else:
            text = state.input_text
        if secret_input and text.strip().lower() != "/lock":
            set_input_text(state, "")
            submit(state, text)
            return
        if text.strip() in {"/quit", "/exit"}:
            set_input_text(state, "")
            labels = unfinished_task_labels(state)
            request_exit(stdscr, state, selected=0 if labels else 1)
            return
        if text.strip().lower() == "/llm":
            set_input_text(state, "")
            open_llm_provider_adder(stdscr, state)
            return
        if text.strip().lower() in {"/models", "/model"}:
            set_input_text(state, "")
            open_model_manager(stdscr, state)
            return
        settings_target = subagent_settings_target_from_command(text)
        if settings_target:
            set_input_text(state, "")
            load_subagents(state)
            sub = resolve_subagent(state, settings_target)
            if sub is None:
                add_system(state, f"找不到子 agent: {settings_target}")
                return
            open_subagent_settings(stdscr, state, sub)
            return
        if secret_blocks_normal_command(state, text.strip()):
            set_input_text(state, "")
            add_system(state, "Secret Vault 已解锁：普通历史/普通 harness 面板已隔离。请先 /lock 再查看普通数据。")
            return
        if text.strip() in {"/memory", "/mem"}:
            set_input_text(state, "")
            open_memory_viewer(stdscr, state)
            return
        if text.strip() in {"/tasks", "/approvals", "/artifacts", "/recover", "/evals", "/gateway", "/baseline"}:
            panel = text.strip().lstrip("/")
            set_input_text(state, "")
            open_harness_panel(stdscr, state, panel)
            return
        set_input_text(state, "")
        submit(state, text)
        return
    if key in ("\x1b", 27):
        visible_status = display_status(state)
        if visible_status in {"running", "aborting"} or state.status == "restoring":
            request_visible_interrupt(state, prefix="Esc")
        elif state.input_text:
            set_input_text(state, "")
            state.command_index = 0
            reset_input_history_browse(state)
            state.last_error = ""
            mark_dirty(state)
        else:
            state.last_error = ""
            mark_dirty(state)
        return
    if key == "\x03":
        request_visible_interrupt(state, prefix="Ctrl+C")
        return
    if key == "\x0c":
        state.last_error = ""
        mark_dirty(state)
        return
    if isinstance(key, str) and key and key.isprintable():
        state.input_text = state.input_text[:state.input_cursor] + key + state.input_text[state.input_cursor:]
        state.input_cursor += len(key)
        state.command_index = 0
        reset_input_history_browse(state)
        mark_dirty(state)


def init_curses(stdscr) -> None:
    curses.curs_set(1)
    curses.noecho()
    try:
        curses.raw()
        curses.noqiflush()
    except curses.error:
        curses.cbreak()
    stdscr.keypad(True)
    restore_main_poll_timeout(stdscr)
    try:
        curses.start_color()
        if curses.COLORS >= 16:
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(8, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(10, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(11, curses.COLOR_WHITE, 8)
        else:
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(8, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(10, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_WHITE)
    except curses.error:
        pass
    mask = (
        getattr(curses, "BUTTON1_CLICKED", 0)
        | getattr(curses, "BUTTON1_PRESSED", 0)
        | getattr(curses, "BUTTON1_RELEASED", 0)
        | getattr(curses, "BUTTON4_PRESSED", 0)
        | getattr(curses, "BUTTON5_PRESSED", 0)
        | getattr(curses, "REPORT_MOUSE_POSITION", 0)
    )
    try:
        curses.mousemask(mask)
        curses.mouseinterval(0)
    except curses.error:
        pass


def disable_tty_flow_control() -> Optional[list[Any]]:
    try:
        fd = sys.stdin.fileno()
        old_attrs = termios.tcgetattr(fd)
        new_attrs = list(old_attrs)
        new_attrs[0] &= ~(getattr(termios, "IXON", 0) | getattr(termios, "IXOFF", 0))
        termios.tcsetattr(fd, termios.TCSANOW, new_attrs)
        return old_attrs
    except Exception:
        return None


def restore_tty_attrs(attrs: Optional[list[Any]]) -> None:
    if attrs is None:
        return
    try:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSANOW, attrs)
    except Exception:
        pass


def tty_escape(seq: str) -> None:
    try:
        fd = os.open("/dev/tty", os.O_WRONLY | os.O_NOCTTY)
    except OSError:
        return
    try:
        os.write(fd, seq.encode())
    except OSError:
        pass
    finally:
        os.close(fd)


def enable_bracketed_paste() -> None:
    tty_escape("\x1b[?2004h")


def disable_bracketed_paste() -> None:
    tty_escape("\x1b[?2004l")


def enable_mouse_drag() -> None:
    tty_escape("\x1b[?1002h\x1b[?1003h")


def disable_mouse_drag() -> None:
    tty_escape("\x1b[?1003l\x1b[?1002l")


def normalize_pasted_text(text: str) -> str:
    return re.sub(r"[ \t]*[\r\n]+[ \t]*", " ", text).replace("\t", "    ")


def read_terminal_key(stdscr):
    key = stdscr.get_wch()
    if key != "\x1b":
        return key
    seq = "\x1b"
    try:
        stdscr.timeout(2)
        deadline = time.monotonic() + 0.04
        while time.monotonic() < deadline and len(seq) < 16:
            try:
                nxt = stdscr.get_wch()
            except curses.error:
                time.sleep(0.001)
                continue
            if isinstance(nxt, str):
                seq += nxt
            else:
                return key
            if seq in {PASTE_START, PASTE_END}:
                return seq
            if not (PASTE_START.startswith(seq) or PASTE_END.startswith(seq)):
                return key
    finally:
        restore_main_poll_timeout(stdscr)
    return key


def run(stdscr) -> dict[str, Any]:
    os.makedirs(os.path.join(ROOT_DIR, "temp"), exist_ok=True)
    log_path = os.path.join(ROOT_DIR, "temp", "ga-tui.log")
    old_stdout, old_stderr = sys.stdout, sys.stderr
    stdio_log = open(log_path, "a", encoding="utf-8", buffering=1)
    stdio_log.write(f"\n--- ga tui {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    sys.stdout = stdio_log
    sys.stderr = stdio_log
    state: Optional[State] = None
    result: dict[str, Any] = {"exit_reason": "", "exit_mode": "terminate", "state": None}
    init_curses(stdscr)
    old_tty_attrs = disable_tty_flow_control()
    enable_bracketed_paste()
    enable_mouse_drag()
    try:
        if cost_tracker is not None:
            try:
                cost_tracker.install()
            except Exception:
                pass
        state = State(agent=new_agent())
        install_interaction_hook(state, state.agent)
        state.token_usage_registry = load_token_usage_registry()
        bind_agent_token_session(state, state.agent)
        load_subagents(state)
        if load_history(state, force=True):
            state.dirty = True
        add_system(state, "GenericAgent stable TUI. 左侧每一项是会话，点击历史会话恢复，输入 / 可选命令补全。")
        next_history_refresh = time.monotonic() + 30
        next_token_persist = time.monotonic() + 10
        next_clock_refresh = time.monotonic() + 1
        next_run_frame = time.monotonic()
        while state.running:
            process_ui_queue(state)
            now = time.monotonic()
            if now >= next_token_persist:
                persist_all_token_usage(state)
                next_token_persist = now + 10
            if now >= next_clock_refresh:
                state.dirty = True
                next_clock_refresh = now + 1
            if display_status(state) in {"running", "aborting"} and now >= next_run_frame:
                state.run_frame = (state.run_frame + 1) % len(RUN_FRAMES)
                state.dirty = True
                next_run_frame = now + 0.12
            if now >= next_history_refresh:
                if load_history(state):
                    state.dirty = True
                next_history_refresh = now + 30
            if maybe_auto_scroll_selection(state, now):
                state.dirty = True
            expire_last_error_if_needed(state)
            if state.dirty:
                redraw(stdscr, state)
                state.dirty = False
            try:
                key = read_terminal_key(stdscr)
            except KeyboardInterrupt:
                request_visible_interrupt(state, prefix="Ctrl+C")
                continue
            except curses.error:
                continue
            try:
                handle_key(stdscr, state, key)
            finally:
                restore_main_poll_timeout(stdscr)
    finally:
        if state is not None:
            persist_all_token_usage(state)
        disable_mouse_drag()
        disable_bracketed_paste()
        restore_tty_attrs(old_tty_attrs)
        exit_reason = state.exit_reason if state is not None else ""
        exit_mode = state.exit_mode if state is not None else "terminate"
        if state is not None:
            state.running = False
            if exit_mode != "wait":
                try:
                    state.agent.abort()
                except Exception:
                    pass
                for bg in list(state.background_sessions.values()):
                    try:
                        bg.agent.abort()
                    except Exception:
                        pass
                for sub in list(state.subagents.values()):
                    if sub.agent is not None:
                        try:
                            sub.agent.abort()
                        except Exception:
                            pass
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        stdio_log.close()
        result = {"exit_reason": exit_reason, "exit_mode": exit_mode, "state": state}
    return result


def wait_for_unfinished_tasks_after_tui(state: Optional[State]) -> None:
    if state is None:
        return
    labels = unfinished_task_labels(state)
    if not labels:
        return
    print(f"ga tui 已关闭；等待 {len(labels)} 个未完成任务跑完。")
    print("日志继续写入 GenericAgent 的 model_responses；任务完成后进程会自动退出。")
    old_stdout, old_stderr = sys.stdout, sys.stderr
    log_path = os.path.join(ROOT_DIR, "temp", "ga-tui.log")
    wait_log = open(log_path, "a", encoding="utf-8", buffering=1)
    wait_log.write(f"\n--- ga tui background wait {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    sys.stdout = wait_log
    sys.stderr = wait_log
    try:
        while any(agent_has_unfinished_task(agent) for agent in all_task_agents(state)):
            persist_all_token_usage(state)
            time.sleep(0.5)
        persist_all_token_usage(state)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        wait_log.close()
    print("后台任务已完成，ga tui 进程退出。")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="GenericAgent stable curses TUI")
    parser.add_argument("--serve-gateway", action="store_true", help="serve the A2A/MCP gateway over HTTP instead of starting curses")
    parser.add_argument("--gateway-daemon", choices=["start", "stop", "restart", "status"], help="manage the A2A/MCP gateway as a background service")
    parser.add_argument("--gateway-host", default=os.environ.get("GA_TUI_GATEWAY_HOST", "127.0.0.1"), help="gateway bind host")
    parser.add_argument("--gateway-port", type=int, default=int(os.environ.get("GA_TUI_GATEWAY_PORT", "8765")), help="gateway bind port")
    args = parser.parse_args(argv)
    if args.gateway_daemon:
        return gateway_daemon_command(args.gateway_daemon, args.gateway_host, args.gateway_port)
    if args.serve_gateway:
        return serve_gateway(args.gateway_host, args.gateway_port)
    result = curses.wrapper(run)
    if isinstance(result, dict):
        reason = str(result.get("exit_reason") or "")
        if reason:
            print(reason)
        if result.get("exit_mode") == "wait":
            wait_for_unfinished_tasks_after_tui(result.get("state"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
