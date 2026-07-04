"""Legacy GenericAgent provider glue for the Shuheng control plane.

This module owns GenericAgent-specific tool schema injection, handler patching,
control-hint installation, and adapter lifecycle hooks. TUI state access stays
in app-layer callbacks injected at configuration time.
"""
from __future__ import annotations

import copy
import re
import threading
from dataclasses import dataclass
from typing import Any, Callable

try:
    from .runtime import RuntimeAdapter
except Exception:
    from runtime import RuntimeAdapter  # type: ignore


ToolHandler = Callable[[Any, dict[str, Any]], dict[str, Any]]
StatePredicate = Callable[[Any], bool]
ThreadFactory = Callable[..., Any]


TUI_AGENT_CONTROL_HINT = """

[Shuheng ga-control v2]
当用户要求你管理 TUI、拆任务或调度子 agent 时，当前唯一控制协议是 `ga-control.v2`，只能输出隐藏 `<ga-control>` 控制块。
只有用户明确要求实际执行创建、委派、修改会话、更新计划等操作时才输出真实 `<ga-control>`。
用户只是询问“能做什么 / 怎么用 / 举个例子 / 讲讲能力 / 演示一下概念”时属于能力说明，不要创建计划或子 agent，不要输出真实 `<ga-control>`。
如果需要展示协议示例，必须使用可见的转义文本，例如 `&lt;ga-control&gt;...&lt;/ga-control&gt;`，或者只展示 JSON payload；不要在示例、教程或解释中包含可执行 `<ga-control>` 标签。
真实 `<ga-control>` 必须放在所有用户可见正文之后，作为回复末尾隐藏块；不要把它夹在段落、列表或示例中间，否则可见正文会被隐藏块移除后截断。

在决定创建、复用、停止、委派子 agent 或更新任务前，优先调用只读查询工具获取当前事实：`agent_list`、`agent_get`、`agent_match`、`task_list`、`task_get`、`approval_list`、`artifact_list`、`capability_list`。这些工具只读取 TUI 仪表盘/账本，不会修改状态；查清后才在回复末尾输出真实 `<ga-control>`。
当用户要求创建或查看定时任务时，优先调用 TUI 调度工具：`schedule_create`、`schedule_list`。`schedule_create` 是受 TUI 控制面治理的状态变更工具；`schedule_list` 只读取 TUI 调度注册表。
会话标题维护是上述规则的一个例外，并且持久标题只由当前主控 runtime 自己通过 `session.rename` 写入：每轮正常回复结束前，静默评估当前会话标题是否仍准确；如果本轮让主题或目标明显变化，回复末尾追加 `session.rename` 控制块把当前会话改成简短中文标题；如果标题已经准确，不要输出控制块，也不要在正文解释标题维护。

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
- `schedule.create`, `schedule.update`, `schedule.enable`, `schedule.disable`, `schedule.delete`
- `dashboard.update`
- `agent.create`, `agent.profile.update`, `agent.role.update`, `agent.model.update`, `agent.skill.update`, `agent.stop`, `agent.delete`
- `delegate.create`
- `memory.candidate`

规则：
- `delegate.create` 是异步委派：发出后等待子 agent 结果进入 bus/系统消息，再汇总或完成计划步骤。
- `delegate.create` 必须带 `routing`、`work_order`、`capability_contract`、`context_contract`、`output_contract`，让能力匹配、工作安排和输出契约完整可审计。
- 默认创建临时会话 agent；如果用户意图是长期、持久、周期性或专职职责，主控必须在 `agent.create` 中显式写 `lifecycle:"persistent"` 或 `persistent:true`。TUI 不会从 name/profile 自然语言里猜生命周期。
- `main_orchestrator` 是当前主控 runtime 专属 role，不能用于 `agent.create` 或 `agent.role.update` 的子 agent；创建/更新子 agent 时请选择 `researcher`、`specialist`、`coder`、`reviewer` 等受限角色。
- 给单个子 agent 配置专属 skill 时，使用 `agent.skill.update`，带 `target` 和 `skills`/`skill_refs`，`op` 可为 `add`、`remove`、`set`、`clear`；这些 skill 只注入目标 agent 的上下文，不属于全局 skill。
- 用户明确要求删除/移除子 agent 时使用 `agent.delete`，不要只使用 `agent.stop`；删除会从 TUI agent 列表移除并保留原目录作为可审计文件。
- 用户明确要求全新/不要复用时，使用 `reuse_policy:"force_new"` 或 `force_new:true`；TUI 不会从可见正文里猜复用策略。
- 如果当前控制块只是一个中间步骤，且需要主控继续生成后续控制，在本次 `ga-control.v2` 批量 envelope 或最后一个 action 上显式写 `continue_after:true` 或 `workflow_state:"in_progress"`。
- 如果控制动作属于某个计划步骤，必须显式提供 `plan_step_id` 或 `parent_task_id`。TUI 不会按“自我介绍/互相聊天/汇总”等词自动绑定步骤。
- Secret Vault 已解锁时仍使用同样的 `ga-control.v2` / `agent.create` / `delegate.create` 控制；持久 Secret agent 写入加密 `secret_subagents`，不要检查或推断普通 Shuheng `SUBAGENTS_DIR` 目录。
- 定时任务由 TUI 顶层登记和治理；用户只需要表达自然意图，不需要说 `schedule_id`、`cron`、`interval`、`at` 这些术语。你负责把“每天早上八点”“每分钟”“明天上午九点”等自然语言翻译成当前 `ScheduleCreate` 结构。
- 创建定时任务时不要读取、修改或启动外部 scheduler 文件、外部定时任务 SOP 或其他程序的调度目录；当前有效调度状态只来自 TUI 调度工具和 `schedule.create` 控制动作。
- `ScheduleCreate` 的触发器 schema 只由 `cron`、`interval`、`at`，或标准化 `trigger` 前缀定义（例如 `cron:0 8 * * *`、`interval:1m`、`at:YYYY-MM-DDT09:00:00+08:00`）。schema 外字段由通用边界处理，不在当前协议里枚举历史字段。
- 用户说“每天 8 点”时输出 `cron:"0 8 * * *"`；说“工作日 8 点半”时输出 `cron:"30 8 * * 1-5"`；说“每 1 分钟”时输出 `interval:"1m"`；说“明天 9 点”时按当前日期和时区输出 ISO `at`。
- `ScheduleCreate` 必须带 `execution` 判别式执行对象。`execution.mode:"tui_action"` 表示 TUI 本地动作；`execution.mode:"agent_task"` 表示通过 `agenttask.v2` 委派给子 agent；`execution.mode:"workflow_run"` 表示按时启动已登记的 workflow；`execution.mode:"workflow_autopilot"` 表示按时推进已经安全可继续的 workflow runs。
- 用户要求“响一声蜂鸣/提醒我一下”这类 TUI 本地提醒时，不需要创建子 agent；设置 `execution:{"mode":"tui_action","action":"beep","message":"..."}`，由 TUI 调度器到点直接执行并写入 schedule-run 审计。
- 用户要求“每天自动跑这个 workflow / 定时执行某个工作流”时，设置 `execution:{"mode":"workflow_run","workflow_ref":"<plugin-id>/<workflow-id>","inputs":{...}}`；scheduler 只触发 app-owned workflow runner，不直接执行 workflow 步骤。
- 用户要求“自动继续/自动推进已卡住后变 ready 的 workflow runs”时，设置 `execution:{"mode":"workflow_autopilot","run_ids":["<run-id>"],"limit":25,"dry_run":false}`；scheduler 只触发 app-owned workflow autopilot tick，不自批 approval，不重复派发未完成 task。
- 除 TUI 本地提醒和已登记 workflow run 外，用户没有指定 `schedule_id` 时可以省略，让 TUI 自动生成；但必须在 `execution.mode:"agent_task"` 中提供明确目标 agent（优先先用 `agent_match` / `agent_list` 查询）和完整 `routing` / `work_order` / capability / context / output contracts，并通过 `agenttask.v2` 派发，不允许绕过任务账本和审批门。
- 你是主控 Orchestrator；读任务可并行，写任务保持单写者；子 agent 返回 artifact/证据/摘要，不要无结构自由聊天。
- 批量操作历史会话时优先用 `/sessions` 输出的稳定 `id:xxxxxx` 或完整文件名作为 target；不要用 `S01`/`1` 这种当前视图相对编号，除非同时提供 `expected_title`。
[/Shuheng ga-control v2]
"""
TUI_CONTROL_HINT_MARKER = "[Shuheng ga-control v2]"
LEGACY_TUI_IDENTITY = "GenericAgent" + "-TUI"
LEGACY_TUI_SESSION_CONTROL_MARKER = f"{LEGACY_TUI_IDENTITY} session control"
LEGACY_TUI_GA_CONTROL_MARKER = f"{LEGACY_TUI_IDENTITY} ga-control v2"
LEGACY_TUI_CONTROL_HINT_MARKER_PATTERN = "|".join(
    re.escape(marker)
    for marker in (
        LEGACY_TUI_SESSION_CONTROL_MARKER,
        LEGACY_TUI_GA_CONTROL_MARKER,
    )
)
# Keep historical injected control-hint blocks removable without exposing their
# old product identity in the active Shuheng prompt.
LEGACY_TUI_CONTROL_HINT_BLOCK_RE = re.compile(
    rf"\n?\[(?:{LEGACY_TUI_CONTROL_HINT_MARKER_PATTERN})\]"
    rf"[\s\S]*?\[/(?:{LEGACY_TUI_CONTROL_HINT_MARKER_PATTERN})\]\s*",
    re.IGNORECASE,
)
TUI_QUERY_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "agent_list",
            "description": "Read-only Shuheng dashboard query. Lists current Shuheng subagents before deciding whether to create, reuse, stop, or delegate. User-facing name: agent.list.",
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
            "description": "Read-only Shuheng dashboard query. Gets one subagent's profile, permissions, queues, current task refs, and bounded memory/profile summaries. User-facing name: agent.get.",
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
            "description": "Read-only Shuheng dashboard query. Scores reusable subagents for an objective and recommends reuse vs create-new before emitting ga-control. User-facing name: agent.match.",
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
            "description": "Read-only Shuheng dashboard query. Lists the shared task ledger with status/agent filters before updating plans or delegating. User-facing name: task.list.",
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
            "description": "Read-only Shuheng dashboard query. Gets one task with latest ledger row, recent history, child tasks, traces, artifacts, and approval refs. User-facing name: task.get.",
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
            "description": "Read-only Shuheng dashboard query. Lists pending approval gates without executing decisions. User-facing name: approval.list.",
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
            "description": "Read-only Shuheng dashboard query. Lists artifact refs and metadata; does not inline artifact contents. User-facing name: artifact.list.",
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
            "description": "Read-only Shuheng dashboard query. Lists role templates, capabilities, write policies, and currently registered agents. User-facing name: capability.list.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
TUI_QUERY_TOOL_NAMES = {
    str(tool.get("function", {}).get("name") or "")
    for tool in TUI_QUERY_TOOL_SCHEMAS
    if tool.get("function")
}
TUI_SCHEDULE_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "schedule_create",
            "description": "Governed Shuheng scheduling mutation. Creates a scheduled task in the Shuheng schedule registry through the same scheduledtask.v1 path as schedule.create controls. User-facing name: schedule.create.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string", "description": "Optional stable schedule id. Omit to let TUI generate one."},
                    "name": {"type": "string", "description": "Human-readable schedule name."},
                    "cron": {"type": "string", "description": "Five-field cron expression, e.g. 0 8 * * *."},
                    "interval": {"type": "string", "description": "Interval duration, e.g. 1m, 30s, 2h."},
                    "at": {"type": "string", "description": "ISO timestamp for a one-shot run."},
                    "trigger": {"type": "string", "description": "Standardized trigger string prefixed with cron:, interval:, or at:."},
                    "timezone": {"type": "string", "description": "Optional timezone label."},
                    "provider_id": {"type": "string", "description": "Optional runtime provider id."},
                    "execution": {
                        "type": "object",
                        "description": "Discriminated execution object for scheduled work.",
                        "properties": {
                            "mode": {
                                "type": "string",
                                "enum": ["tui_action", "agent_task", "workflow_run", "workflow_autopilot"],
                                "description": "tui_action runs a local TUI action; agent_task dispatches through agenttask.v2; workflow_run starts an existing workflow; workflow_autopilot advances ready existing workflow runs.",
                            },
                            "action": {
                                "type": "string",
                                "enum": ["beep"],
                                "description": "Required when mode=tui_action. Current supported action: beep.",
                            },
                            "message": {"type": "string", "description": "Optional message for the TUI action audit row."},
                            "payload": {"type": "object", "description": "Optional bounded payload for the TUI action."},
                            "workflow_ref": {"type": "string", "description": "Required when mode=workflow_run. Plugin workflow ref or shorthand such as research-pack/compare-sources."},
                            "inputs": {"type": "object", "description": "Optional workflow inputs when mode=workflow_run."},
                            "run_ids": {"type": "array", "items": {"type": "string"}, "description": "Optional workflow run ids when mode=workflow_autopilot."},
                            "limit": {"type": "integer", "description": "Maximum workflow run ids considered when mode=workflow_autopilot."},
                            "dry_run": {"type": "boolean", "description": "When mode=workflow_autopilot, report eligible runs without mutating workflow ledgers."},
                            "routing": {"type": "object", "description": "Required when mode=agent_task. agenttask.v2 routing contract with selected_agent."},
                            "work_order": {"type": "object", "description": "Required when mode=agent_task. Must include objective."},
                            "capability_contract": {"type": "object", "description": "agenttask.v2 capability contract."},
                            "context_contract": {"type": "object", "description": "agenttask.v2 context contract."},
                            "output_contract": {"type": "object", "description": "agenttask.v2 output contract."},
                        },
                        "required": ["mode"],
                    },
                    "status": {"type": "string", "enum": ["enabled", "disabled"], "description": "Initial schedule status.", "default": "enabled"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_list",
            "description": "Read-only TUI scheduling query. Lists TUI scheduled tasks, due state, run count, and audit refs without touching external scheduler files. User-facing name: schedule.list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_inactive": {"type": "boolean", "description": "Include disabled, deleted, or cancelled schedules.", "default": False},
                    "limit": {"type": "integer", "description": "Maximum schedules to return.", "default": 50},
                },
            },
        },
    },
]
TUI_SCHEDULE_TOOL_NAMES = {
    str(tool.get("function", {}).get("name") or "")
    for tool in TUI_SCHEDULE_TOOL_SCHEMAS
    if tool.get("function")
}
TUI_TOOL_SCHEMAS = TUI_QUERY_TOOL_SCHEMAS + TUI_SCHEDULE_TOOL_SCHEMAS
TUI_TOOL_NAMES = tuple(
    str(tool.get("function", {}).get("name") or "")
    for tool in TUI_TOOL_SCHEMAS
    if tool.get("function")
)


@dataclass
class GenericAgentProviderRuntimeConfig:
    agentmain: Any
    generic_agent_cls: Any
    step_outcome_cls: Any
    is_state: StatePredicate
    tool_handlers: dict[str, ToolHandler]
    thread_factory: ThreadFactory = threading.Thread


_runtime_config: GenericAgentProviderRuntimeConfig | None = None


def configure_genericagent_provider_runtime(
    *,
    agentmain: Any,
    generic_agent_cls: Any,
    step_outcome_cls: Any,
    is_state: StatePredicate,
    tool_handlers: dict[str, ToolHandler],
    thread_factory: ThreadFactory = threading.Thread,
) -> GenericAgentProviderRuntimeConfig:
    """Configure app-layer dependencies required by the GenericAgent adapter."""
    global _runtime_config
    _runtime_config = GenericAgentProviderRuntimeConfig(
        agentmain=agentmain,
        generic_agent_cls=generic_agent_cls,
        step_outcome_cls=step_outcome_cls,
        is_state=is_state,
        tool_handlers=dict(tool_handlers),
        thread_factory=thread_factory,
    )
    return _runtime_config


def genericagent_provider_config() -> GenericAgentProviderRuntimeConfig:
    if _runtime_config is None:
        raise RuntimeError("GenericAgent provider runtime is not configured.")
    return _runtime_config


def install_tui_query_tool_schema() -> None:
    config = genericagent_provider_config()
    schema = getattr(config.agentmain, "TOOLS_SCHEMA", None)
    if not isinstance(schema, list):
        return
    existing = {
        str(item.get("function", {}).get("name") or "")
        for item in schema
        if isinstance(item, dict) and isinstance(item.get("function"), dict)
    }
    for tool in TUI_TOOL_SCHEMAS:
        name = str(tool.get("function", {}).get("name") or "")
        if name and name not in existing:
            schema.append(copy.deepcopy(tool))
            existing.add(name)


def wrap_agentmain_tool_schema_loader() -> None:
    config = genericagent_provider_config()
    agentmain = config.agentmain
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


def tui_query_state_for_handler(handler: Any) -> Any | None:
    config = genericagent_provider_config()
    parent = getattr(handler, "parent", None)
    state = getattr(parent, "_ga_tui_state", None)
    return state if config.is_state(state) else None


def _unknown_tool_response(kind: str) -> dict[str, Any]:
    return {
        "schema_version": "ga-tui.query.v1",
        "status": "error",
        "error": f"Unknown TUI query tool: {kind}",
    }


def tui_query_tool_outcome(kind: str, handler: Any, args: dict[str, Any]) -> Any:
    config = genericagent_provider_config()
    state = tui_query_state_for_handler(handler)
    func = config.tool_handlers.get(kind)
    data = func(state, args) if func is not None else _unknown_tool_response(kind)
    return config.step_outcome_cls(data, next_prompt="\n")


def install_tui_query_handler_methods() -> None:
    config = genericagent_provider_config()
    handler_cls = getattr(config.agentmain, "GenericAgentHandler", None)
    if handler_cls is None or bool(getattr(handler_cls, "_ga_tui_query_tools_patched", False)):
        return

    def make_handler(kind: str) -> Callable[[Any, dict[str, Any], Any], Any]:
        def _handler(self: Any, args: dict[str, Any], response: Any) -> Any:
            del response
            return tui_query_tool_outcome(kind, self, args)

        _handler.__name__ = f"do_{kind}"
        return _handler

    for name in TUI_TOOL_NAMES:
        setattr(handler_cls, f"do_{name}", make_handler(name))
    setattr(handler_cls, "_ga_tui_query_tools_patched", True)


def install_tui_query_runtime(agent: Any = None, state: Any = None) -> None:
    config = genericagent_provider_config()
    wrap_agentmain_tool_schema_loader()
    install_tui_query_tool_schema()
    install_tui_query_handler_methods()
    if agent is not None and state is not None and config.is_state(state):
        try:
            setattr(agent, "_ga_tui_state", state)
        except Exception:
            pass


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


class GenericAgentRuntimeAdapter(RuntimeAdapter):
    def create_agent(self) -> Any:
        config = genericagent_provider_config()
        install_tui_query_runtime()
        agent = config.generic_agent_cls()
        agent.inc_out = True
        return agent

    def prepare_agent(self, agent: Any, *, state: Any = None) -> None:
        config = genericagent_provider_config()
        install_tui_query_runtime(agent, state if config.is_state(state) else None)
        install_tui_control_hint(agent)

    def start_agent(self, agent: Any, *, thread_name: str = "") -> Any:
        config = genericagent_provider_config()
        if not thread_name:
            thread_name = "ga-tui-agent"
        agent._ga_tui_thread_name = thread_name
        thread = config.thread_factory(target=agent.run, daemon=True, name=thread_name)
        agent._ga_tui_thread = thread
        thread.start()
        return thread


__all__ = [
    "GenericAgentProviderRuntimeConfig",
    "GenericAgentRuntimeAdapter",
    "LEGACY_TUI_CONTROL_HINT_BLOCK_RE",
    "TUI_AGENT_CONTROL_HINT",
    "TUI_CONTROL_HINT_MARKER",
    "TUI_QUERY_TOOL_NAMES",
    "TUI_QUERY_TOOL_SCHEMAS",
    "TUI_SCHEDULE_TOOL_NAMES",
    "TUI_SCHEDULE_TOOL_SCHEMAS",
    "TUI_TOOL_NAMES",
    "TUI_TOOL_SCHEMAS",
    "configure_genericagent_provider_runtime",
    "genericagent_provider_config",
    "install_tui_control_hint",
    "install_tui_query_handler_methods",
    "install_tui_query_runtime",
    "install_tui_query_tool_schema",
    "tui_query_state_for_handler",
    "tui_query_tool_outcome",
    "wrap_agentmain_tool_schema_loader",
]
