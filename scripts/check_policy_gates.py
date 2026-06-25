#!/usr/bin/env python3
"""Function-level smoke checks for the governed agent harness policy gates."""

from __future__ import annotations

import os
import queue
import shutil
import sys
import tempfile
import time
import json
import hashlib
import threading
import urllib.request
import curses
import zipfile
import contextlib
import io
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ga_tui import app as a  # noqa: E402
from ga_tui import agent_bridge as bridge  # noqa: E402
from ga_tui import control_protocol as cp  # noqa: E402
from ga_tui import genericagent_provider as gap  # noqa: E402
from ga_tui import integration as integ  # noqa: E402
from ga_tui import ohmypi_provider as omp  # noqa: E402
from ga_tui import scheduler as sched  # noqa: E402


def retarget_harness(root: str) -> None:
    a.SHUHENG_HOME = root
    a.SHUHENG_MEMORY_DIR = os.path.join(root, "memory")
    a.SHUHENG_TEMP_DIR = os.path.join(root, "temp")
    a.SHUHENG_LOG_DIR = os.path.join(root, "logs")
    a.SHUHENG_LOG_PATH = os.path.join(a.SHUHENG_LOG_DIR, "shuheng.log")
    a.MODEL_RESPONSES_DIR = os.path.join(root, "model_responses")
    a.TOKEN_USAGE_PATH = os.path.join(a.MODEL_RESPONSES_DIR, "session_token_usage.json")
    a.SESSION_META_PATH = os.path.join(a.MODEL_RESPONSES_DIR, "session_meta.json")
    a.SHUHENG_WORKSPACES_DIR = os.path.join(root, "workspaces")
    a.SHUHENG_WORKSPACE_STATE_PATH = os.path.join(a.SHUHENG_WORKSPACES_DIR, "active.json")
    a.SHUHENG_SKILLS_DIR = os.path.join(a.SHUHENG_MEMORY_DIR, "skills")
    a.L4_RAW_SESSIONS_DIR = os.path.join(a.SHUHENG_MEMORY_DIR, "L4_raw_sessions")
    a.SESSION_TRASH_DIR = os.path.join(a.MODEL_RESPONSES_DIR, ".trash")
    a.configure_frontend_history_storage()
    a.AGENT_HARNESS_DIR = os.path.join(a.SHUHENG_MEMORY_DIR, "agent_harness")
    a.AGENT_TASK_LEDGER_PATH = os.path.join(a.AGENT_HARNESS_DIR, "tasks.jsonl")
    a.AGENT_MAIL_PATH = os.path.join(a.AGENT_HARNESS_DIR, "messages.jsonl")
    a.AGENT_APPROVALS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "approvals.jsonl")
    a.AGENT_ARTIFACTS_DIR = os.path.join(a.AGENT_HARNESS_DIR, "artifacts")
    a.AGENT_ARTIFACT_INDEX_PATH = os.path.join(a.AGENT_HARNESS_DIR, "artifacts.jsonl")
    a.AGENT_CONTEXT_PACKS_DIR = os.path.join(a.AGENT_HARNESS_DIR, "context_packs")
    a.AGENT_TRACES_PATH = os.path.join(a.AGENT_HARNESS_DIR, "traces.jsonl")
    a.AGENT_EVALS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "evals.jsonl")
    a.AGENT_LOCKS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "locks.json")
    a.AGENT_GATEWAY_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway.json")
    a.AGENT_POLICY_PATH = os.path.join(a.AGENT_HARNESS_DIR, "policy.json")
    a.AGENT_POLICY_DECISIONS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "policy_decisions.jsonl")
    a.AGENT_ORCHESTRATOR_PLANS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "orchestrator_plans.jsonl")
    a.AGENT_MEMORY_CANDIDATES_PATH = os.path.join(a.AGENT_HARNESS_DIR, "memory_candidates.jsonl")
    a.AGENT_CHECKPOINTS_DIR = os.path.join(a.AGENT_HARNESS_DIR, "checkpoints")
    a.AGENT_CHECKPOINT_INDEX_PATH = os.path.join(a.AGENT_HARNESS_DIR, "checkpoints.jsonl")
    a.AGENT_RECOVERY_PATH = os.path.join(a.AGENT_HARNESS_DIR, "recovery.jsonl")
    a.AGENT_RECOVERY_PLANS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "recovery_plans.jsonl")
    a.AGENT_BASELINE_REPORT_PATH = os.path.join(a.AGENT_HARNESS_DIR, "baseline_report.json")
    a.AGENT_GOVERNANCE_PATH = os.path.join(a.AGENT_HARNESS_DIR, "governance_components.json")
    a.AGENT_RUNTIME_REGISTRY_PATH = os.path.join(a.AGENT_HARNESS_DIR, "runtime_providers.json")
    a.AGENT_SCHEDULES_PATH = os.path.join(a.AGENT_HARNESS_DIR, "schedules.jsonl")
    a.AGENT_SCHEDULE_RUNS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "schedule_runs.jsonl")
    a.AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_push_subscriptions.jsonl")
    a.AGENT_GATEWAY_PUSH_DELIVERIES_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_push_deliveries.jsonl")
    a.AGENT_GATEWAY_DAEMON_PID_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_daemon.pid")
    a.AGENT_GATEWAY_DAEMON_STATUS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_daemon.json")
    a.AGENT_GATEWAY_DAEMON_LOG_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_daemon.log")
    a.AGENT_BRIDGE_REGISTRY_PATH = os.path.join(a.AGENT_HARNESS_DIR, "bridge_registry.json")
    a.LLM_RECENT_MODELS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "recent_models.json")
    a.SECRET_VAULT_DIR = os.path.join(a.SHUHENG_MEMORY_DIR, "secret_vault")
    a.SECRET_VAULT_META_PATH = os.path.join(a.SECRET_VAULT_DIR, "vault.json")
    a.SECRET_VAULT_DATA_DIR = os.path.join(a.SECRET_VAULT_DIR, "data")
    a.SECRET_VAULT_SESSIONS_DIR = os.path.join(a.SECRET_VAULT_DATA_DIR, "sessions")
    a.SUBAGENTS_DIR = os.path.join(a.SHUHENG_MEMORY_DIR, "subagents")
    a.TEMP_SUBAGENTS_DIR = os.path.join(a.SHUHENG_TEMP_DIR, "subagents")
    os.makedirs(a.AGENT_HARNESS_DIR, exist_ok=True)
    os.makedirs(a.SUBAGENTS_DIR, exist_ok=True)
    os.makedirs(a.TEMP_SUBAGENTS_DIR, exist_ok=True)
    os.makedirs(a.SHUHENG_WORKSPACES_DIR, exist_ok=True)
    os.makedirs(a.SHUHENG_SKILLS_DIR, exist_ok=True)
    a.configure_scheduler_runtime(
        schedules_path=a.AGENT_SCHEDULES_PATH,
        runs_path=a.AGENT_SCHEDULE_RUNS_PATH,
        task_ledger_path=a.AGENT_TASK_LEDGER_PATH,
        agent_mail_path=a.AGENT_MAIL_PATH,
        read_jsonl=a.read_jsonl,
        append_jsonl=a.append_jsonl,
        now_iso=a.now_iso,
        json_safe=a.tui_query_json_safe,
        default_provider_id=lambda: str(a.agent_runtime_registry().to_record().get("default_provider_id") or "ohmypi"),
        truncate_cells=a.truncate_cells,
        emit_tui_beep=lambda: a.emit_tui_beep(),
        resolve_subagent=a.resolve_subagent,
        dispatch_subagent_task=lambda state, sub, mapped, source, schedule_id, row: sched.SchedulerDispatchResult(
            **a.start_subagent_task_structured(
                state,
                sub,
                str(mapped.get("prompt") or ""),
                source=f"{source}:{schedule_id}",
                parent_task_id=str(mapped.get("parent_task_id") or ""),
                task_title=str(mapped.get("task_title") or row.get("name") or schedule_id),
            ).__dict__
        ),
    )


class FakeAgent:
    def __init__(self) -> None:
        self.prompts: list[tuple[str, str]] = []

    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        self.prompts.append((prompt, source))
        dq: queue.Queue = queue.Queue()
        dq.put({"done": "ok"})
        return dq


class BlockingFakeAgent:
    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        del prompt, source
        return queue.Queue()


class BlockingAbortFakeAgent:
    def __init__(self) -> None:
        self.prompts: list[tuple[str, str]] = []
        self.abort_count = 0
        self.log_path = ""

    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        self.prompts.append((prompt, source))
        return queue.Queue()

    def abort(self) -> None:
        self.abort_count += 1


class SequencedFakeAgent:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.prompts: list[tuple[str, str]] = []
        self.log_path = ""

    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        self.prompts.append((prompt, source))
        response = self.responses.pop(0) if self.responses else ""
        dq: queue.Queue = queue.Queue()
        dq.put({"done": response})
        return dq


class ContextFakeAgent:
    log_path = ""


def assert_scheduler_module_boundary() -> None:
    scheduler_names = (
        "scheduled_task_registry",
        "latest_schedule_records",
        "append_schedule_record",
        "latest_schedule_run_records",
        "latest_schedule_runs_by_schedule_id",
        "latest_schedule_attempt_runs_by_schedule_id",
        "schedule_run_idempotency_keys",
        "append_schedule_run",
        "schedule_record_trigger",
        "parse_schedule_timestamp",
        "parse_schedule_interval_seconds",
        "split_schedule_trigger",
        "cron_field_matches",
        "cron_matches_now",
        "schedule_active",
        "schedule_due_info",
        "schedule_trigger_from_control",
        "schedule_execution_from_control",
        "schedule_execution_target",
        "schedule_execution_error",
        "schedule_record_from_control",
        "schedule_record_updates_from_control",
        "apply_schedule_control",
        "schedule_agenttask_control",
        "update_schedule_last_run",
        "append_schedule_skip_run",
        "dispatch_schedule_tui_action",
        "dispatch_schedule_run",
        "scheduler_tick",
        "format_scheduler_tick_result",
        "format_scheduled_task_registry",
    )
    for name in scheduler_names:
        assert getattr(a, name) is getattr(sched, name), name
        assert getattr(sched, name).__module__ == "ga_tui.scheduler", name
    assert a.SCHEDULER_TICK_SECONDS == sched.SCHEDULER_TICK_SECONDS
    assert a.SCHEDULE_RUN_ATTEMPT_STATUSES is sched.SCHEDULE_RUN_ATTEMPT_STATUSES
    source = Path(sched.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "import curses",
        "from curses",
        "ga_tui.app",
        "from .app",
        "import app",
        "GenericAgent",
        "GenericAgentHandler",
        "StepOutcome",
        "State",
    ):
        assert forbidden not in source, forbidden


def assert_genericagent_provider_module_boundary() -> None:
    provider_names = (
        "TUI_AGENT_CONTROL_HINT",
        "TUI_CONTROL_HINT_MARKER",
        "LEGACY_TUI_CONTROL_HINT_BLOCK_RE",
        "TUI_QUERY_TOOL_SCHEMAS",
        "TUI_SCHEDULE_TOOL_SCHEMAS",
        "TUI_TOOL_SCHEMAS",
        "TUI_QUERY_TOOL_NAMES",
        "TUI_SCHEDULE_TOOL_NAMES",
        "TUI_TOOL_NAMES",
        "configure_genericagent_provider_runtime",
        "genericagent_provider_config",
        "install_tui_query_tool_schema",
        "wrap_agentmain_tool_schema_loader",
        "tui_query_state_for_handler",
        "tui_query_tool_outcome",
        "install_tui_query_handler_methods",
        "install_tui_query_runtime",
        "install_tui_control_hint",
        "GenericAgentRuntimeAdapter",
    )
    for name in provider_names:
        assert getattr(a, name) is getattr(gap, name), name
    for name in (
        "install_tui_query_tool_schema",
        "wrap_agentmain_tool_schema_loader",
        "tui_query_state_for_handler",
        "tui_query_tool_outcome",
        "install_tui_query_handler_methods",
        "install_tui_query_runtime",
        "install_tui_control_hint",
    ):
        assert getattr(gap, name).__module__ == "ga_tui.genericagent_provider", name
    assert gap.GenericAgentRuntimeAdapter.__module__ == "ga_tui.genericagent_provider"
    provider_source = Path(gap.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "import curses",
        "from curses",
        "ga_tui.app",
        "from .app",
        "import app",
        "from app import State",
        "from .app import State",
    ):
        assert forbidden not in provider_source, forbidden
    app_source = Path(a.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "def install_tui_query_tool_schema",
        "def wrap_agentmain_tool_schema_loader",
        "def tui_query_state_for_handler",
        "def tui_query_tool_outcome",
        "def install_tui_query_handler_methods",
        "def install_tui_query_runtime",
        "def install_tui_control_hint",
        "class GenericAgentRuntimeAdapter",
    ):
        assert forbidden not in app_source, forbidden
    assert "configure_genericagent_provider_runtime(" in app_source


class FakeRpcStdout:
    def __init__(self) -> None:
        self.frames: queue.Queue[str] = queue.Queue()

    def push(self, obj: dict) -> None:
        self.frames.put(json.dumps(obj, ensure_ascii=False) + "\n")

    def __iter__(self):
        return self

    def __next__(self) -> str:
        return self.frames.get()


class FakeRpcStderr:
    def __iter__(self):
        return self

    def __next__(self) -> str:
        raise StopIteration


class FakeRpcStdin:
    def __init__(self, stdout: FakeRpcStdout, *, auto_finish: bool = True) -> None:
        self.stdout = stdout
        self.auto_finish = auto_finish
        self.writes: list[dict] = []
        self.session_path = "/tmp/omp-session.jsonl"
        self.session_id = "omp-session-1"
        self.session_name = "OMP Native Session"
        self.message_count = 4
        self.context_tokens = 123456
        self.context_window = 1000000

    def write(self, payload: str) -> int:
        for line in payload.splitlines():
            if not line.strip():
                continue
            frame = json.loads(line)
            self.writes.append(frame)
            if frame.get("type") == "prompt":
                self.stdout.push({"id": frame.get("id"), "type": "response", "command": "prompt", "success": True})
                if self.auto_finish:
                    self.stdout.push({
                        "type": "message_update",
                        "assistantMessageEvent": {
                            "type": "text_delta",
                            "delta": "Validated durable lesson: ",
                        },
                    })
                    self.stdout.push({
                        "type": "message_update",
                        "assistantMessageEvent": {
                            "type": "text_delta",
                            "delta": "TUI owns memory approval while Oh My Pi emits candidates.",
                        },
                    })
                    self.stdout.push({"type": "agent_end"})
            elif frame.get("type") == "get_state":
                self.stdout.push({
                    "id": frame.get("id"),
                    "type": "response",
                    "command": "get_state",
                    "success": True,
                    "data": {
                        "model": {"provider": "token52", "id": "gpt-5.5", "contextWindow": self.context_window},
                        "sessionFile": self.session_path,
                        "sessionId": self.session_id,
                        "sessionName": self.session_name,
                        "autoCompactionEnabled": True,
                        "messageCount": self.message_count,
                        "contextUsage": {
                            "tokens": self.context_tokens,
                            "contextWindow": self.context_window,
                            "percent": self.context_tokens / self.context_window * 100,
                        },
                    },
                })
            elif frame.get("type") == "switch_session":
                self.session_path = str(frame.get("sessionPath") or self.session_path)
                self.session_id = "omp-session-switched"
                self.session_name = "Switched OMP Session"
                self.message_count = 9
                self.stdout.push({
                    "id": frame.get("id"),
                    "type": "response",
                    "command": "switch_session",
                    "success": True,
                    "data": {"cancelled": False},
                })
            elif frame.get("type") == "new_session":
                self.session_path = "/tmp/omp-new-session.jsonl"
                self.session_id = "omp-session-new"
                self.session_name = "New OMP Session"
                self.message_count = 0
                self.stdout.push({
                    "id": frame.get("id"),
                    "type": "response",
                    "command": "new_session",
                    "success": True,
                    "data": {"cancelled": False},
                })
            elif frame.get("type") == "compact":
                self.context_tokens = 45678
                self.stdout.push({
                    "id": frame.get("id"),
                    "type": "response",
                    "command": "compact",
                    "success": True,
                    "data": {"summary": "compacted"},
                })
            elif frame.get("type") == "set_host_tools":
                tools = frame.get("tools") if isinstance(frame.get("tools"), list) else []
                self.stdout.push({
                    "id": frame.get("id"),
                    "type": "response",
                    "command": "set_host_tools",
                    "success": True,
                    "data": {"toolNames": [str(tool.get("name") or "") for tool in tools if isinstance(tool, dict)]},
                })
            elif frame.get("type") == "abort":
                self.stdout.push({"id": frame.get("id"), "type": "response", "command": "abort", "success": True})
        return len(payload)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None


class FakeRpcProcess:
    def __init__(self, *, auto_finish: bool = True) -> None:
        self.stdout = FakeRpcStdout()
        self.stderr = FakeRpcStderr()
        self.stdin = FakeRpcStdin(self.stdout, auto_finish=auto_finish)
        self.returncode = None
        self.stdout.push({"type": "ready"})

    def poll(self):
        return self.returncode

    def terminate(self) -> None:
        self.returncode = 0

    def kill(self) -> None:
        self.returncode = -9

    def wait(self, timeout: float | None = None):
        del timeout
        self.returncode = 0
        return self.returncode


def wait_for_rpc_write(process: FakeRpcProcess, predicate, *, timeout: float = 2.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        for frame in process.stdin.writes:
            if predicate(frame):
                return frame
        time.sleep(0.01)
    raise AssertionError(process.stdin.writes)


def wait_for_process(processes: list[FakeRpcProcess], *, timeout: float = 2.0) -> FakeRpcProcess:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if processes:
            return processes[0]
        time.sleep(0.01)
    raise AssertionError("fake RPC process was not started")


def wait_for_queue_done(dq: queue.Queue, *, timeout: float = 2.0) -> tuple[dict, str]:
    deadline = time.time() + timeout
    chunks: list[str] = []
    while time.time() < deadline:
        try:
            item = dq.get(timeout=0.05)
        except queue.Empty:
            continue
        if "next" in item:
            chunks.append(str(item.get("next") or ""))
        if "done" in item:
            return item, "".join(chunks)
    raise AssertionError("queue did not receive a done item")


def assert_queue_has_no_done(dq: queue.Queue, *, timeout: float = 0.2) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            item = dq.get(timeout=0.02)
        except queue.Empty:
            continue
        assert "done" not in item, item


def assert_ohmypi_provider_module_boundary() -> None:
    assert omp.OhMyPiRuntimeAdapter.__module__ == "ga_tui.ohmypi_provider"
    provider_source = Path(omp.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "import curses",
        "from curses",
        "ga_tui.app",
        "from .app",
        "import app",
        "from app import State",
        "from .app import State",
    ):
        assert forbidden not in provider_source, forbidden


def assert_shuheng_brand_entrypoints() -> None:
    pyproject = Path(ROOT, "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "shuheng"' in pyproject, pyproject
    for script in (
        "shuheng",
        "shuheng-agent-bridge",
        "shuheng-check",
        "shuheng-install-core-shim",
        "shuheng-integration",
    ):
        assert f"{script} =" in pyproject, script
    for removed_script in (
        "ga-tui",
        "ga-tui-agent-bridge",
        "ga-tui-check",
        "ga-tui-install-core-shim",
        "ga-tui-integration",
    ):
        assert f"{removed_script} =" not in pyproject, removed_script
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        assert integ._print_report(ROOT, []) == 0
    report = buffer.getvalue()
    assert "Shuheng root:" in report, report
    assert "Launch without core patches: shuheng" in report, report
    assert "ga-tui" not in report, report
    app_source = Path(a.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "ga tui",
        "GenericAgent stable TUI",
        "GenericAgent stable curses TUI",
    ):
        assert forbidden not in app_source, forbidden
    assert "已退出枢衡" in app_source, app_source
    assert "确认退出枢衡" in app_source, app_source


def assert_shuheng_history_storage_owned() -> None:
    expected_home = os.path.abspath(os.path.expanduser(os.environ.get("SHUHENG_HOME") or os.environ.get("GA_TUI_HOME") or "~/.shuheng"))
    assert a.SHUHENG_HOME == expected_home, a.SHUHENG_HOME
    assert a.SHUHENG_MEMORY_DIR == os.path.join(a.SHUHENG_HOME, "memory"), a.SHUHENG_MEMORY_DIR
    assert a.SHUHENG_TEMP_DIR == os.path.join(a.SHUHENG_HOME, "temp"), a.SHUHENG_TEMP_DIR
    assert a.SHUHENG_WORKSPACES_DIR == os.path.join(a.SHUHENG_HOME, "workspaces"), a.SHUHENG_WORKSPACES_DIR
    assert a.SHUHENG_WORKSPACE_STATE_PATH == os.path.join(a.SHUHENG_WORKSPACES_DIR, "active.json"), a.SHUHENG_WORKSPACE_STATE_PATH
    assert a.path_is_within(a.MODEL_RESPONSES_DIR, a.SHUHENG_HOME), a.MODEL_RESPONSES_DIR
    assert a.path_is_within(a.TOKEN_USAGE_PATH, a.SHUHENG_HOME), a.TOKEN_USAGE_PATH
    assert a.path_is_within(a.SESSION_META_PATH, a.SHUHENG_HOME), a.SESSION_META_PATH
    assert a.path_is_within(a.SHUHENG_WORKSPACES_DIR, a.SHUHENG_HOME), a.SHUHENG_WORKSPACES_DIR
    assert a.path_is_within(a.SHUHENG_WORKSPACE_STATE_PATH, a.SHUHENG_HOME), a.SHUHENG_WORKSPACE_STATE_PATH
    assert a.path_is_within(a.L4_RAW_SESSIONS_DIR, a.SHUHENG_HOME), a.L4_RAW_SESSIONS_DIR
    assert a.path_is_within(a.SESSION_TRASH_DIR, a.SHUHENG_HOME), a.SESSION_TRASH_DIR
    assert a.path_is_within(a.AGENT_HARNESS_DIR, a.SHUHENG_HOME), a.AGENT_HARNESS_DIR
    assert a.path_is_within(a.SUBAGENTS_DIR, a.SHUHENG_HOME), a.SUBAGENTS_DIR
    assert a.path_is_within(a.TEMP_SUBAGENTS_DIR, a.SHUHENG_HOME), a.TEMP_SUBAGENTS_DIR
    assert a.path_is_within(a.SECRET_VAULT_DIR, a.SHUHENG_HOME), a.SECRET_VAULT_DIR
    assert a.path_is_within(omp.ohmypi_isolated_agent_dir(a.AGENT_HARNESS_DIR), a.SHUHENG_HOME)
    assert a.path_is_within(omp.ohmypi_memory_prompt_path(a.AGENT_HARNESS_DIR), a.SHUHENG_HOME)
    genericagent_history = os.path.join(a.ROOT_DIR, "temp", "model_responses")
    genericagent_memory = os.path.join(a.ROOT_DIR, "memory")
    assert not a.path_is_within(a.MODEL_RESPONSES_DIR, genericagent_history), a.MODEL_RESPONSES_DIR
    assert not a.path_is_within(a.AGENT_HARNESS_DIR, genericagent_memory), a.AGENT_HARNESS_DIR
    assert not a.path_is_within(a.SUBAGENTS_DIR, genericagent_memory), a.SUBAGENTS_DIR
    assert not a.path_is_within(a.SECRET_VAULT_DIR, genericagent_memory), a.SECRET_VAULT_DIR
    assert a.continue_cmd_module._LOG_DIR == a.MODEL_RESPONSES_DIR
    assert a.continue_cmd_module._LOG_GLOB == os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_*.txt")
    assert a.path_is_within(a.continue_cmd_module._ROUNDS_CACHE_PATH, a.SHUHENG_HOME), a.continue_cmd_module._ROUNDS_CACHE_PATH
    if a.session_names is not None:
        assert a.session_names._LOG_DIR == a.MODEL_RESPONSES_DIR
        assert a.session_names._REG_PATH == os.path.join(a.MODEL_RESPONSES_DIR, "session_names.json")
    assert "GenericAgent 的 model_responses" not in Path(a.__file__).read_text(encoding="utf-8")


def assert_token_usage_registry_prunes_removed_history() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_token_usage_")
    retarget_harness(root)
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)

    live_key = "model_responses_live.txt"
    deleted_key = "model_responses_deleted.txt"
    hidden_key = "model_responses_hidden.txt"
    missing_key = "model_responses_missing.txt"
    external_key = "external-session-key"
    live_path = os.path.join(a.MODEL_RESPONSES_DIR, live_key)
    Path(live_path).write_text("live", encoding="utf-8")
    a.write_text_atomic(a.SESSION_META_PATH, json.dumps({
        live_key: {},
        deleted_key: {"deleted": True},
        hidden_key: {"hidden_subagent_log": True},
        missing_key: {},
    }, ensure_ascii=False))
    a.write_text_atomic(a.TOKEN_USAGE_PATH, json.dumps({
        live_key: {"requests": 1, "input": 10, "output": 5, "cache_create": 0, "cache_read": 0},
        deleted_key: {"requests": 2, "input": 20, "output": 6, "cache_create": 0, "cache_read": 0},
        hidden_key: {"requests": 3, "input": 30, "output": 7, "cache_create": 0, "cache_read": 0},
        missing_key: {"requests": 4, "input": 40, "output": 8, "cache_create": 0, "cache_read": 0},
        external_key: {"requests": 5, "input": 50, "output": 9, "cache_create": 0, "cache_read": 0},
    }, ensure_ascii=False))

    registry = a.load_token_usage_registry()
    assert live_key in registry, registry
    assert external_key in registry, registry
    assert deleted_key not in registry, registry
    assert hidden_key not in registry, registry
    assert missing_key not in registry, registry

    state = a.State(agent=FakeAgent())
    state.token_usage_registry = registry
    a.remove_session_token_usage(state, live_path)
    persisted = json.loads(Path(a.TOKEN_USAGE_PATH).read_text(encoding="utf-8"))
    assert live_key not in persisted, persisted
    assert external_key in persisted, persisted
    a.write_text_atomic(a.TOKEN_USAGE_PATH, "{}\n")
    state.token_usage_registry = {live_key: {"requests": 7, "input": 70, "output": 11, "cache_create": 0, "cache_read": 0}}
    state.token_usage_registry_signature = (0.0, -1)
    assert a.refresh_state_token_usage_registry(state) is True
    assert state.token_usage_registry == {}, state.token_usage_registry

    class TokenAgent:
        def __init__(self, path: str, thread_name: str) -> None:
            self.log_path = path
            self._ga_tui_thread_name = thread_name

        def abort(self) -> None:
            return None

    class FakeTokenStats:
        def __init__(self, requests: int = 0, input: int = 0, output: int = 0, cache_create: int = 0, cache_read: int = 0) -> None:
            self.requests = requests
            self.input = input
            self.output = output
            self.cache_create = cache_create
            self.cache_read = cache_read
            self.last_input = input
            self.last_output = output

        def total_input_side(self) -> int:
            return self.input + self.cache_create + self.cache_read

        def total_tokens(self) -> int:
            return self.input + self.output + self.cache_create + self.cache_read

        def cache_hit_rate(self) -> float:
            side = self.total_input_side()
            return (self.cache_read / side * 100.0) if side else 0.0

    class FakeCostTracker:
        TokenStats = FakeTokenStats

        def __init__(self) -> None:
            self.stats = FakeTokenStats(requests=1, input=100, output=50)
            self.reset_calls: list[str] = []

        def get(self, _thread_name: str) -> FakeTokenStats:
            return self.stats

        def reset(self, thread_name: str) -> None:
            self.reset_calls.append(thread_name)
            self.stats = FakeTokenStats()

        def context_window_chars(self, _backend: object) -> int:
            return 0

        def current_input_chars(self, _backend: object) -> int:
            return 0

    current_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_current.txt")
    Path(current_path).write_text("current", encoding="utf-8")
    current_key = os.path.basename(current_path)
    token_state = a.State(agent=TokenAgent(current_path, "token-current"))
    token_state.token_usage_registry = {current_key: {"requests": 9, "input": 900, "output": 90, "cache_create": 0, "cache_read": 0}}
    a.save_state_token_usage_registry(token_state)

    old_cost_tracker = a.cost_tracker
    fake_tracker = FakeCostTracker()
    try:
        a.cost_tracker = fake_tracker
        result = a.apply_session_operation(token_state, "delete", "current", source="/delete")
        assert "已删除到回收站" in result, result
        after_delete = json.loads(Path(a.TOKEN_USAGE_PATH).read_text(encoding="utf-8"))
        assert current_key not in after_delete, after_delete
        assert fake_tracker.reset_calls == ["token-current"], fake_tracker.reset_calls
        assert token_state.token_live_offsets["token-current"] == a.empty_token_stats_dict(), token_state.token_live_offsets

        next_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_next.txt")
        Path(next_path).write_text("next", encoding="utf-8")
        fake_tracker.stats = FakeTokenStats(requests=2, input=200, output=80)
        next_state = a.State(agent=TokenAgent(next_path, "token-next"))
        next_state.token_live_offsets["token-next"] = a.empty_token_stats_dict()
        assert a.new_current_session(next_state, keep_running=False) is False
        assert fake_tracker.reset_calls[-1] == "token-next", fake_tracker.reset_calls
        assert next_state.token_live_offsets["token-next"] == a.empty_token_stats_dict(), next_state.token_live_offsets
        assert a.session_token_stats(next_state, next_state.agent).total_tokens() == 0

        omp_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_omp.txt")
        Path(omp_path).write_text("omp", encoding="utf-8")
        omp_key = os.path.basename(omp_path)
        omp_state = a.State(agent=TokenAgent(omp_path, "token-omp"))
        assert a.persist_runtime_token_usage(omp_state, omp_state.agent, {
            "requests": 2,
            "input": 120,
            "output": 30,
            "cache_create": 4,
            "cache_read": 400,
        }) is True
        assert omp_state.token_usage_registry[omp_key] == {
            "requests": 2,
            "input": 120,
            "output": 30,
            "cache_create": 4,
            "cache_read": 400,
        }, omp_state.token_usage_registry
        assert a.session_token_stats(omp_state, omp_state.agent).total_tokens() == 554

        ui_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_ui_usage.txt")
        Path(ui_path).write_text("ui", encoding="utf-8")
        ui_key = os.path.basename(ui_path)
        ui_state = a.State(agent=TokenAgent(ui_path, "token-ui"))
        ui_state.active_task_id = 77
        ui_state.ui_queue.put((
            "token_usage",
            "stream",
            a.StreamTarget("active"),
            77,
            {"requests": 1, "input": 7, "output": 8, "cache_create": 0, "cache_read": 9},
        ))
        assert a.process_ui_queue(ui_state) is True
        assert ui_state.token_usage_registry[ui_key] == {
            "requests": 1,
            "input": 7,
            "output": 8,
            "cache_create": 0,
            "cache_read": 9,
        }, ui_state.token_usage_registry

        temp_state = a.State(agent=TokenAgent(os.devnull, "token-temp"))
        assert a.persist_runtime_token_usage(temp_state, temp_state.agent, {
            "requests": 1,
            "input": 10,
            "output": 5,
            "cache_create": 0,
            "cache_read": 0,
        }) is False
        assert temp_state.token_usage_registry == {}, temp_state.token_usage_registry
    finally:
        a.cost_tracker = old_cost_tracker


def assert_shuheng_workspace_memory_context() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_workspaces_")
    retarget_harness(root)
    old_cwd = os.getcwd()
    project_root = os.path.join(root, "Project Alpha")
    project_child = os.path.join(project_root, "nested")
    os.makedirs(os.path.join(project_root, ".git"), exist_ok=True)
    os.makedirs(project_child, exist_ok=True)

    os.makedirs(a.L4_RAW_SESSIONS_DIR, exist_ok=True)
    archive_path = os.path.join(a.L4_RAW_SESSIONS_DIR, "2026-06.zip")
    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("0619_1200-session.txt", "archived session")
    before = Path(archive_path).read_bytes()

    try:
        os.chdir(project_child)
        state = a.State(agent=FakeLLMAgent())
        expected_id = a.workspace_id_for_root(project_root)
        assert a.current_workspace_root() == project_root, a.current_workspace_root()
        assert not os.path.exists(a.SHUHENG_WORKSPACE_STATE_PATH)

        pack, _context_ref = a.build_main_runtime_context_pack(state, "read project memory", "task_workspace_auto")
        assert pack["workspace_context"]["included"] is True, pack["workspace_context"]
        assert pack["workspace_context"]["workspace"]["workspace_id"] == expected_id, pack["workspace_context"]
        assert pack["workspace_context"]["workspace"]["selection_mode"] == "auto", pack["workspace_context"]
        assert project_root in pack["workspace_context"]["workspace"]["root_aliases"], pack["workspace_context"]
        prompt = a.format_context_pack_for_prompt(pack)
        assert "Workspace context:" in prompt and expected_id in prompt, prompt

        state_file = a.read_json_dict_file(a.SHUHENG_WORKSPACE_STATE_PATH)
        assert state_file["active_workspace_id"] == expected_id, state_file
        assert state_file["selection_mode"] == "auto", state_file
        manifest = a.load_workspace_manifest(expected_id)
        assert manifest["selection_mode"] == "auto", manifest
        assert project_root in manifest["root_aliases"], manifest
        a.write_text_atomic(a.workspace_memory_path(expected_id), "# Project Alpha\n\nUse this auto project fact.\n")

        pack_with_memory, _ref_with_memory = a.build_main_runtime_context_pack(state, "use project memory", "task_workspace_auto_memory")
        assert "Use this auto project fact." in str(pack_with_memory["layers"]["L2_project_memory"]["items"]), pack_with_memory["layers"]["L2_project_memory"]
        layered_entries = [row for row in pack_with_memory["memory_pack"]["included"] if row.get("scope") == "shuheng.layered-memory"]
        assert layered_entries, pack_with_memory["memory_pack"]
        workspace_memory_entries = [row for row in pack_with_memory["memory_pack"]["included"] if row.get("scope") == "workspace.project-provenance"]
        assert workspace_memory_entries, pack_with_memory["memory_pack"]
        assert workspace_memory_entries[-1]["refs"], workspace_memory_entries[-1]

        l4_index = a.read_json_dict_file(a.workspace_l4_index_path(expected_id))
        assert l4_index["refs_count"] == 1, l4_index
        assert l4_index["refs"][0]["ref"] == "l4://2026-06.zip/0619_1200-session.txt", l4_index
        assert Path(archive_path).read_bytes() == before, "L4 indexing must not rewrite archive content"

        assert any(row[0] == "/workspace" for row in a.command_matches("/work", state)), a.command_matches("/work", state)
        assert any(row[0] == "/workspace refresh" for row in a.command_matches("/workspace r", state)), a.command_matches("/workspace r", state)
        assert not any("select" in row[0] for row in a.command_matches("/workspace s", state)), a.command_matches("/workspace s", state)
        assert a.handle_workspace_command(state, "/workspace current") is True
        assert a.handle_workspace_command(state, "/workspace list") is True
        assert a.handle_workspace_command(state, "/workspace refresh") is True

        inventory = a.memory_inventory()
        workspace_entries = [row for row in inventory if row.layer == "Workspace"]
        assert any(row.label.endswith("manifest.json") for row in workspace_entries), workspace_entries
        assert any(row.label.endswith("memory.md") for row in workspace_entries), workspace_entries

        secret_state = a.State(agent=FakeLLMAgent())
        secret_state.secret_vault.unlocked = True
        secret_pack, _secret_ref = a.build_main_runtime_context_pack(secret_state, "secret", "task_workspace_secret")
        assert secret_pack["workspace_context"]["included"] is False, secret_pack["workspace_context"]
        assert "Secret context" in secret_pack["workspace_context"]["reason"], secret_pack["workspace_context"]
    finally:
        os.chdir(old_cwd)


def assert_shared_user_profile_context_is_global() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_shared_profile_")
    retarget_harness(root)
    install_fake_agent_runtime()
    state = a.State(agent=FakeLLMAgent())
    state.running = True

    a.record_shared_user_profile_interaction(
        "请把 Shuheng 的所有 agent 都共享同一个用户画像，并持续跟踪工作重心",
        source="user",
        state=state,
    )
    profile_path = a.shared_user_profile_path()
    profile_state_path = a.shared_user_profile_state_path()
    assert os.path.exists(profile_path), profile_path
    assert os.path.exists(profile_state_path), profile_state_path
    profile_text = Path(profile_path).read_text(encoding="utf-8")
    assert "Shared User Profile" in profile_text, profile_text
    assert "Shuheng" in profile_text, profile_text
    profile_state = a.read_json_dict_file(profile_state_path)
    assert profile_state["interaction_count"] == 1, profile_state

    sub = a.create_subagent(state, "Profile Aware Agent", role="researcher", persistent=True)
    sub_pack, _sub_ref = a.build_context_pack(state, sub, "Use shared user state", "task_shared_profile_sub")
    assert sub_pack["shared_user_profile"]["path"] == profile_path, sub_pack["shared_user_profile"]
    assert sub_pack["layers"]["L1_user_profile"]["included"] is True, sub_pack["layers"]["L1_user_profile"]
    assert any(row.get("scope") == "user.shared-profile" for row in sub_pack["memory_pack"]["included"]), sub_pack["memory_pack"]
    sub_prompt = a.format_context_pack_for_prompt(sub_pack)
    assert "Shared user profile:" in sub_prompt and profile_path in sub_prompt, sub_prompt

    main_pack, _main_ref = a.build_main_runtime_context_pack(state, "Main should see shared user state", "task_shared_profile_main")
    assert main_pack["shared_user_profile"]["path"] == profile_path, main_pack["shared_user_profile"]
    assert main_pack["layers"]["L1_user_profile"]["refs"] == [profile_path, profile_state_path], main_pack["layers"]["L1_user_profile"]

    omp_prompt = omp.build_ohmypi_memory_prompt(root_dir=root, harness_dir=a.AGENT_HARNESS_DIR)
    assert "Shared User Profile" in omp_prompt and profile_path in omp_prompt, omp_prompt

    temp_state = a.State(agent=FakeLLMAgent())
    temp_state.temporary_session = True
    a.record_shared_user_profile_interaction("临时会话不要写入共享画像", source="user", state=temp_state)
    profile_state_after_temp = a.read_json_dict_file(profile_state_path)
    assert profile_state_after_temp["interaction_count"] == 1, profile_state_after_temp


def assert_shuheng_bootstraps_legacy_state_without_mutating_source() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_legacy_bootstrap_")
    legacy_root = os.path.join(root, "GenericAgent")
    shuheng_root = os.path.join(root, "ShuhengHome")
    legacy_history = os.path.join(legacy_root, "temp", "model_responses")
    legacy_memory = os.path.join(legacy_root, "memory")
    os.makedirs(legacy_history, exist_ok=True)
    os.makedirs(os.path.join(legacy_memory, "subagents", "researcher"), exist_ok=True)
    os.makedirs(os.path.join(legacy_memory, "agent_harness", "runtime", "ohmypi", "agent"), exist_ok=True)

    legacy_session = os.path.join(legacy_history, "model_responses_legacy.txt")
    a.write_text_atomic(
        legacy_session,
        "=== Prompt === 2026-06-18 09:00:00\n"
        + json.dumps({"role": "user", "content": [{"type": "text", "text": "legacy question"}]}, ensure_ascii=False)
        + "\n\n=== Response === 2026-06-18 09:00:01\n"
        + repr([{"type": "text", "text": "legacy answer"}])
        + "\n",
    )
    a.write_text_atomic(
        os.path.join(legacy_history, "session_meta.json"),
        json.dumps({
            "model_responses_legacy.txt": {"preview": "legacy question"},
            "model_responses_conflict.txt": {"preview": "old conflict"},
        }, ensure_ascii=False),
    )
    a.write_text_atomic(
        os.path.join(legacy_history, "session_names.json"),
        json.dumps({"model_responses_legacy.txt": "Legacy Session"}, ensure_ascii=False),
    )
    a.write_text_atomic(os.path.join(legacy_memory, "global_mem.txt"), "legacy global memory\n")
    a.write_text_atomic(os.path.join(legacy_memory, "global_mem_insight.txt"), "legacy index\n")
    a.write_text_atomic(os.path.join(legacy_memory, "subagents", "researcher", "memory.md"), "legacy researcher memory\n")
    a.write_text_atomic(os.path.join(legacy_memory, "agent_harness", "runtime", "ohmypi", "agent", "config.yml"), "stale runtime\n")

    old_root = a.ROOT_DIR
    old_import = os.environ.get("SHUHENG_IMPORT_LEGACY")
    old_disable = os.environ.pop("SHUHENG_DISABLE_LEGACY_IMPORT", None)
    old_done = a._LEGACY_STATE_BOOTSTRAP_DONE
    try:
        a.ROOT_DIR = legacy_root
        retarget_harness(shuheng_root)
        os.environ["SHUHENG_IMPORT_LEGACY"] = "1"
        a._LEGACY_STATE_BOOTSTRAP_DONE = False
        os.makedirs(a.SHUHENG_MEMORY_DIR, exist_ok=True)
        a.write_text_atomic(os.path.join(a.SHUHENG_MEMORY_DIR, "global_mem.txt"), "new global memory wins\n")
        a.save_session_meta_registry({
            "model_responses_conflict.txt": {"preview": "new conflict wins"},
        })

        state = a.State(agent=None)
        assert a.load_history(state, force=True) is True
        imported_session = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_legacy.txt")
        assert os.path.exists(imported_session), imported_session
        assert any(path == imported_session for path, _mtime, _preview, _rounds in state.history), state.history
        registry = a.load_session_meta_registry()
        assert registry["model_responses_conflict.txt"]["preview"] == "new conflict wins", registry
        assert os.path.exists(legacy_session), legacy_session
        assert a.read_text_file(os.path.join(a.SHUHENG_MEMORY_DIR, "global_mem.txt")) == "new global memory wins\n"
        assert a.read_text_file(os.path.join(a.SHUHENG_MEMORY_DIR, "global_mem_insight.txt")) == "legacy index\n"
        assert "legacy researcher memory" in a.read_text_file(os.path.join(a.SUBAGENTS_DIR, "researcher", "memory.md"))
        assert not os.path.exists(os.path.join(a.AGENT_HARNESS_DIR, "runtime", "ohmypi", "agent", "config.yml"))
        marker = json.loads(a.read_text_file(a.legacy_import_marker_path()))
        assert marker["mode"] == "copy_missing_only", marker
        assert marker["history"]["copied_files"] >= 2, marker
        assert marker["memory"]["copied_files"] >= 2, marker
    finally:
        a.ROOT_DIR = old_root
        a._LEGACY_STATE_BOOTSTRAP_DONE = old_done
        if old_import is None:
            os.environ.pop("SHUHENG_IMPORT_LEGACY", None)
        else:
            os.environ["SHUHENG_IMPORT_LEGACY"] = old_import
        if old_disable is not None:
            os.environ["SHUHENG_DISABLE_LEGACY_IMPORT"] = old_disable


def assert_ohmypi_runtime_registry() -> None:
    old = os.environ.pop("GA_TUI_RUNTIME_PROVIDER", None)
    try:
        registry = a.agent_runtime_registry()
        data = registry.to_record()
        assert data["default_provider_id"] == "ohmypi", data
        assert {"genericagent", "ohmypi"} <= set(data["provider_ids"]), data
        providers = {item["provider_id"]: item for item in data["providers"]}
        ohmypi = providers["ohmypi"]
        assert ohmypi["schema_version"] == "agentruntime.provider.v1", ohmypi
        assert ohmypi["transport"] == "jsonl_stdio_rpc", ohmypi
        assert ohmypi["capabilities"]["streaming"] is True, ohmypi
        assert ohmypi["capabilities"]["host_tools"] is False, ohmypi
        assert ohmypi["capabilities"]["tui_readonly_host_tools"] is True, ohmypi
        assert ohmypi["capabilities"]["tui_governed_proposal_tools"] is True, ohmypi
        assert ohmypi["capabilities"]["tui_typed_host_tools"] is True, ohmypi
        assert ohmypi["capabilities"]["runtime_task_requests"] is True, ohmypi
        assert ohmypi["capabilities"]["runtime_task_events"] is True, ohmypi
        assert ohmypi["capabilities"]["memory_candidates"] is True, ohmypi
        assert ohmypi["capabilities"]["memory_candidate_signals"] is True, ohmypi
        assert ohmypi["scheduler"]["status"] == "registry_ready", ohmypi
        assert ohmypi["policy"]["approval_gate_owner"] == "ga-tui.policy", ohmypi
        assert ohmypi["policy"]["tool_permissions"] == "tui_readonly_and_governed_proposal_tools_only", ohmypi
        assert ohmypi["policy"]["runtime_tool_approval_mode"] == "yolo", ohmypi
        assert ohmypi["policy"]["memory_write"] == "candidate_only", ohmypi
        os.environ["GA_TUI_RUNTIME_PROVIDER"] = "genericagent"
        assert a.agent_runtime_registry().default().provider_id == "genericagent"
    finally:
        if old is None:
            os.environ.pop("GA_TUI_RUNTIME_PROVIDER", None)
        else:
            os.environ["GA_TUI_RUNTIME_PROVIDER"] = old


def assert_ohmypi_memory_prompt_and_command() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_omp_root_")
    harness = tempfile.mkdtemp(prefix="ga_tui_omp_harness_")
    memory_dir = os.path.join(root, "memory")
    os.makedirs(memory_dir, exist_ok=True)
    Path(memory_dir, "global_mem_insight.txt").write_text("api_key: SHOULD_NOT_LEAK\nremember useful path\n", encoding="utf-8")
    Path(memory_dir, "global_mem.txt").write_text("api_key: SHOULD_NOT_LEAK\nvalidated fact\n", encoding="utf-8")
    Path(memory_dir, "memory_management_sop.md").write_text("No Execution, No Memory.\n", encoding="utf-8")
    prompt_path = omp.write_ohmypi_memory_prompt(root_dir=root, harness_dir=harness)
    prompt_text = Path(prompt_path).read_text(encoding="utf-8")
    assert "Shuheng Layered Memory Guidance" in prompt_text, prompt_text
    assert "normal user-facing final reply" in prompt_text, prompt_text
    assert "memory-candidate submit/deferred notices are not a substitute" in prompt_text, prompt_text
    assert "context packs and context refs as internal execution metadata" in prompt_text, prompt_text
    assert "这个东西" in prompt_text and "recent visible conversation/task topic" in prompt_text, prompt_text
    assert "agent.create with lifecycle:\"persistent\"" in prompt_text, prompt_text
    assert "Scripts, schedules, or future suggestions alone do not satisfy" in prompt_text, prompt_text
    assert "remember useful path" in prompt_text, prompt_text
    assert "global_mem.txt" in prompt_text, prompt_text
    assert "SHOULD_NOT_LEAK" not in prompt_text, prompt_text
    assert "[REDACTED]" in prompt_text, prompt_text
    command = omp.ohmypi_rpc_command(binary="/fake/omp", append_system_prompt=prompt_path)
    assert command[:3] == ["/fake/omp", "--mode", "rpc"], command
    assert "--approval-mode" in command, command
    assert command[command.index("--approval-mode") + 1] == "yolo", command
    assert "--append-system-prompt" in command, command
    assert command[command.index("--append-system-prompt") + 1] == prompt_path, command
    old_approval_mode = os.environ.get("GA_TUI_OMP_APPROVAL_MODE")
    try:
        os.environ["GA_TUI_OMP_APPROVAL_MODE"] = "always-ask"
        command_with_approval_override = omp.ohmypi_rpc_command(binary="/fake/omp")
        assert command_with_approval_override[command_with_approval_override.index("--approval-mode") + 1] == "always-ask", command_with_approval_override
    finally:
        if old_approval_mode is None:
            os.environ.pop("GA_TUI_OMP_APPROVAL_MODE", None)
        else:
            os.environ["GA_TUI_OMP_APPROVAL_MODE"] = old_approval_mode
    command_with_user_append = omp.ohmypi_rpc_command(
        binary="/fake/omp",
        extra_args=["--append-system-prompt", "/user/append.md"],
        append_system_prompt=prompt_path,
    )
    assert command_with_user_append.count("--append-system-prompt") == 1, command_with_user_append
    assert "/user/append.md" in command_with_user_append, command_with_user_append


def assert_ohmypi_rpc_command_discovers_user_bun_binary() -> None:
    temp_home = tempfile.mkdtemp(prefix="ga_tui_omp_home_")
    bun_bin = Path(temp_home, ".bun", "bin")
    bun_bin.mkdir(parents=True)
    omp_binary = bun_bin / "omp"
    omp_binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    omp_binary.chmod(0o755)
    old_home = os.environ.get("HOME")
    old_path = os.environ.get("PATH")
    old_bin = os.environ.pop("GA_TUI_OHMYPI_BIN", None)
    try:
        os.environ["HOME"] = temp_home
        os.environ["PATH"] = ""
        command = omp.ohmypi_rpc_command()
        assert command[0] == str(omp_binary), command

        os.environ["GA_TUI_OHMYPI_BIN"] = "/custom/omp"
        explicit_command = omp.ohmypi_rpc_command()
        assert explicit_command[0] == "/custom/omp", explicit_command
    finally:
        if old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old_home
        if old_path is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = old_path
        if old_bin is None:
            os.environ.pop("GA_TUI_OHMYPI_BIN", None)
        else:
            os.environ["GA_TUI_OHMYPI_BIN"] = old_bin


def assert_ohmypi_isolated_runtime_settings() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_omp_isolated_")
    retarget_harness(root)
    mykey_file = os.path.join(root, "mykey.py")
    Path(mykey_file).write_text(
        "\n".join([
            "mixin_config = {'llm_nos': ['beta'], 'max_retries': 10, 'base_delay': 0.5}",
            "native_oai_config = {'name': 'alpha', 'apikey': 'key-alpha', 'apibase': 'https://alpha.example.invalid/v1', 'model': 'model-alpha'}",
            "native_oai_config_1 = {'name': 'beta', 'apikey': 'key-beta', 'apibase': 'https://beta.example.invalid/v1', 'model': 'model-beta', 'api_mode': 'responses', 'context_win': 1050000, 'max_tokens': 128000}",
            "",
        ]),
        encoding="utf-8",
    )
    old_mykey_path = a.mykey_path
    old_approval_mode = os.environ.pop("GA_TUI_OMP_APPROVAL_MODE", None)
    system_config = Path.home() / ".omp" / "agent" / "config.yml"
    before_hash = hashlib.sha256(system_config.read_bytes()).hexdigest() if system_config.exists() else ""
    try:
        a.mykey_path = lambda: mykey_file
        runtime_config = a.build_ohmypi_runtime_config(base_env={})
        assert runtime_config.agent_dir == os.path.join(a.AGENT_HARNESS_DIR, "runtime", "ohmypi", "agent"), runtime_config
        assert not runtime_config.agent_dir.startswith(str(Path.home() / ".omp")), runtime_config.agent_dir
        assert runtime_config.env["PI_CODING_AGENT_DIR"] == runtime_config.agent_dir, runtime_config.env
        assert len(runtime_config.models) == 2, runtime_config.models
        assert runtime_config.default_model.endswith("/model-beta"), runtime_config.default_model
        assert runtime_config.models[1].context_window == 1050000, runtime_config.models[1]
        assert runtime_config.models[1].max_tokens == 128000, runtime_config.models[1]
        assert runtime_config.approval_mode == "yolo", runtime_config
        config_data = json.loads(Path(runtime_config.config_path).read_text(encoding="utf-8"))
        models_data = json.loads(Path(runtime_config.models_path).read_text(encoding="utf-8"))
        assert config_data["autoResume"] is False, config_data
        assert config_data["modelRoles"]["default"] == runtime_config.default_model, config_data
        assert config_data["todo"]["eager"] == "default", config_data
        assert config_data["tools"]["approvalMode"] == "yolo", config_data
        assert "providers" in models_data and len(models_data["providers"]) == 2, models_data
        beta_provider = next(
            provider for provider in models_data["providers"].values()
            if provider["models"][0]["id"] == "model-beta"
        )
        assert beta_provider["api"] == "openai-responses", beta_provider
        assert beta_provider["apiKey"].startswith("GA_TUI_OMP_API_KEY_"), beta_provider
        assert beta_provider["models"][0]["contextWindow"] == 1050000, beta_provider
        assert beta_provider["models"][0]["maxTokens"] == 128000, beta_provider
        assert "key-beta" not in Path(runtime_config.models_path).read_text(encoding="utf-8")

        registry = a.agent_runtime_registry(write_memory_prompt_file=False)
        adapter = registry.get("ohmypi")
        assert adapter is not None
        assert getattr(adapter, "cwd") == a.APP_ROOT_DIR, getattr(adapter, "cwd")
        assert getattr(adapter, "env")["PI_CODING_AGENT_DIR"] == runtime_config.agent_dir
        ohmypi_agent = adapter.create_agent()
        setattr(ohmypi_agent, "_ga_tui_runtime_provider_id", "ohmypi")
        assert ohmypi_agent.llm_no == 1, ohmypi_agent.llm_no
        assert ohmypi_agent.get_llm_name(model=True) == "model-beta", ohmypi_agent.get_llm_name(model=True)
        Path(mykey_file).write_text(
            "\n".join([
                "mixin_config = {'llm_nos': ['gamma'], 'max_retries': 10, 'base_delay': 0.5}",
                "native_oai_config = {'name': 'alpha', 'apikey': 'key-alpha', 'apibase': 'https://alpha.example.invalid/v1', 'model': 'model-alpha'}",
                "native_oai_config_1 = {'name': 'beta', 'apikey': 'key-beta', 'apibase': 'https://beta.example.invalid/v1', 'model': 'model-beta', 'api_mode': 'responses', 'context_win': 1050000, 'max_tokens': 128000}",
                "native_oai_config_2 = {'name': 'gamma', 'apikey': 'key-gamma', 'apibase': 'https://gamma.example.invalid/v1', 'model': 'model-gamma'}",
                "",
            ]),
            encoding="utf-8",
        )
        refresh_msg = a.refresh_agent_runtime_model_config(ohmypi_agent)
        assert "3 个模型" in refresh_msg, refresh_msg
        assert len(ohmypi_agent.configured_models) == 3, ohmypi_agent.configured_models
        assert ohmypi_agent.configured_models[2].model_id == "model-gamma", ohmypi_agent.configured_models
        metadata_state = a.State(agent=ohmypi_agent)
        metadata_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_ohmypi_metadata.txt")
        a.set_agent_log_path(ohmypi_agent, metadata_path)
        metadata_messages = [a.Message("user", "给这个会话维护简介"), a.Message("assistant", "这是回答")]
        assert a.agent_supports_inline_ai_metadata(ohmypi_agent) is False
        assert a.maybe_start_ai_description_job(metadata_state, metadata_path, metadata_messages, ohmypi_agent) is False
        assert metadata_state.description_jobs == set(), metadata_state.description_jobs
        record = adapter.spec.to_record()
        assert record["model_routing"]["isolated_agent_dir"] == runtime_config.agent_dir, record
        assert record["model_routing"]["configured_model_count"] == 2, record
        assert record["model_routing"]["tool_approval_mode"] == "yolo", record
        assert record["policy"]["runtime_tool_approval_mode"] == "yolo", record
        command = getattr(adapter, "command")
        assert "--model" in command and runtime_config.default_model in command, command
        Path(mykey_file).write_text(
            "\n".join([
                "mixin_config = {'llm_nos': ['zhipu-glm'], 'max_retries': 10, 'base_delay': 0.5}",
                "native_claude_config = {'name': 'zhipu-glm', 'apikey': 'key-zhipu', 'apibase': 'https://open.bigmodel.cn/api/coding/paas/v4', 'model': 'glm-5.2'}",
                "native_claude_config_1 = {'name': 'zhipu-anthropic', 'apikey': 'key-zhipu', 'apibase': 'https://open.bigmodel.cn/api/anthropic', 'model': 'GLM-5.1-Cloud'}",
                "",
            ]),
            encoding="utf-8",
        )
        zhipu_runtime_config = a.build_ohmypi_runtime_config(base_env={})
        zhipu_provider = next(
            provider for provider in json.loads(Path(zhipu_runtime_config.models_path).read_text(encoding="utf-8"))["providers"].values()
            if provider["models"][0]["id"] == "glm-5.2"
        )
        assert zhipu_provider["api"] == "openai-completions", zhipu_provider
        assert a.models_endpoint_for_config(
            "native_claude",
            "https://open.bigmodel.cn/api/coding/paas/v4",
            {"apibase": "https://open.bigmodel.cn/api/coding/paas/v4"},
        ) == "https://open.bigmodel.cn/api/coding/paas/v4/models"
        assert a.models_endpoint_for_config(
            "native_claude",
            "https://open.bigmodel.cn/api/anthropic",
            {"apibase": "https://open.bigmodel.cn/api/anthropic"},
        ) == "https://open.bigmodel.cn/api/anthropic/v1/models"
        zhipu_entry = a.LLMConfigEntry(
            "native_claude_config",
            "native_claude",
            {"name": "zhipu-glm", "apikey": "key-zhipu", "apibase": "https://open.bigmodel.cn/api/coding/paas/v4", "model": "glm-5.2"},
        )
        calls: list[tuple[str, dict[str, str], dict[str, object]]] = []
        old_post_json = a.post_json_for_validation
        try:
            def fake_post_json(url, headers, payload, timeout):
                calls.append((url, dict(headers), dict(payload)))
                return True, "ok"

            a.post_json_for_validation = fake_post_json
            ok_validate, validate_msg = a.validate_model_entry(zhipu_entry)
        finally:
            a.post_json_for_validation = old_post_json
        assert ok_validate, validate_msg
        assert calls and calls[0][0] == "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions", calls
        assert "Authorization" in calls[0][1] and "x-api-key" not in calls[0][1], calls
        if before_hash:
            after_hash = hashlib.sha256(system_config.read_bytes()).hexdigest()
            assert after_hash == before_hash, (before_hash, after_hash)
    finally:
        a.mykey_path = old_mykey_path
        if old_approval_mode is None:
            os.environ.pop("GA_TUI_OMP_APPROVAL_MODE", None)
        else:
            os.environ["GA_TUI_OMP_APPROVAL_MODE"] = old_approval_mode


def assert_ohmypi_permission_profiles() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_omp_permissions_")
    retarget_harness(root)
    old_profile = os.environ.pop("GA_TUI_OMP_PERMISSION_PROFILE", None)
    old_default_profile = os.environ.pop("GA_TUI_DEFAULT_PERMISSION_PROFILE", None)
    try:
        state = a.State(agent=FakeLLMAgent())
        pack, context_ref = a.build_main_runtime_context_pack(state, "Can you edit code?", "task_omp_full")
        assert context_ref.startswith("artifact://"), context_ref
        assert pack["for_agent"]["role"] == "main_orchestrator", pack["for_agent"]
        assert pack["role_template"]["write_policy"] == "single_writer", pack["role_template"]
        assert "受限专家子 agent" not in str(pack["role_template"]), pack["role_template"]
        assert pack["permission_profile"] == "full", pack
        assert pack["permissions"]["permission_profile"] == "full", pack["permissions"]
        assert pack["permissions"]["write_policy"] == "single_writer", pack["permissions"]
        assert pack["permissions"]["tools_forbidden"] == [], pack["permissions"]
        assert pack["permissions"]["approval_required_for"] == [], pack["permissions"]
        assert pack["permissions"]["memory_write"] == "candidate_only", pack["permissions"]
        assert {"bash", "edit", "write", "browser", "task", "host_tools", "subagent.delegate", "memory.candidate"} <= set(pack["permissions"]["tools_allowed"]), pack["permissions"]
        prompt = a.format_context_pack_for_prompt(pack)
        assert "permission_profile: full" in prompt, prompt
        assert "role: main_orchestrator" in prompt, prompt
        assert "role: specialist" not in prompt, prompt
        assert "tools_allowed: " in prompt and "bash" in prompt and "memory.candidate" in prompt, prompt
        assert "output_contract: summary, actions_taken, tool_results" in prompt, prompt

        runtime_agent = RuntimeCaptureFakeAgent()
        runtime_state = a.State(agent=runtime_agent)
        assert a.start_main_agent_task(
            runtime_state,
            "Test all available tools",
            source="user",
            visible_user_text="Test all available tools",
        )
        assert len(runtime_agent.runtime_requests) == 1, runtime_agent.runtime_requests
        request = runtime_agent.runtime_requests[0]
        request_tools = set(request.permissions.get("tools_allowed") or [])
        assert request.role == "main_orchestrator", request
        assert request.agent_id == "orchestrator.main", request
        assert request.permissions["permission_profile"] == "full", request.permissions
        assert request.permissions["write_policy"] == "single_writer", request.permissions
        assert request.permissions["tools_forbidden"] == [], request.permissions
        assert request.permissions["approval_required_for"] == [], request.permissions
        assert {"bash", "write", "host_tools", "subagent.delegate", "memory.candidate"} <= request_tools, request.permissions
        assert "permission_profile: full" in request.prompt, request.prompt
        assert "role: main_orchestrator" in request.prompt, request.prompt
        assert "role: specialist" not in request.prompt, request.prompt
        assert request.output_contract["required_sections"] == a.role_output_contract("main_orchestrator"), request.output_contract

        sub = a.create_subagent(state, "Role Bounded Researcher", role="researcher", persistent=False)
        sub_pack, _sub_ref = a.build_context_pack(state, sub, "Read only research", "task_sub_standard")
        assert sub_pack["permission_profile"] == "standard", sub_pack
        assert sub_pack["permissions"]["write_policy"] == "none", sub_pack["permissions"]
        assert sub_pack["permissions"]["tools_allowed"] == ["web", "read"], sub_pack["permissions"]

        os.environ["GA_TUI_OMP_PERMISSION_PROFILE"] = "read_only"
        read_only_pack, _read_only_ref = a.build_main_runtime_context_pack(state, "Compatibility mode", "task_omp_read_only")
        assert read_only_pack["permission_profile"] == "read_only", read_only_pack
        assert read_only_pack["permissions"]["write_policy"] == "none", read_only_pack["permissions"]
        assert "bash" not in read_only_pack["permissions"]["tools_allowed"], read_only_pack["permissions"]
    finally:
        if old_profile is None:
            os.environ.pop("GA_TUI_OMP_PERMISSION_PROFILE", None)
        else:
            os.environ["GA_TUI_OMP_PERMISSION_PROFILE"] = old_profile
        if old_default_profile is None:
            os.environ.pop("GA_TUI_DEFAULT_PERMISSION_PROFILE", None)
        else:
            os.environ["GA_TUI_DEFAULT_PERMISSION_PROFILE"] = old_default_profile


def assert_model_context_window_surface() -> None:
    fields = [field for field, _label, _kind in a.model_form_fields("native_oai")]
    assert "context_win" in fields, fields
    assert fields.index("context_win") > fields.index("model"), fields

    root = tempfile.mkdtemp(prefix="ga_tui_model_context_")
    mykey_file = os.path.join(root, "mykey.py")
    old_mykey_path = a.mykey_path
    try:
        a.mykey_path = lambda: mykey_file
        entry = a.LLMConfigEntry(
            "native_oai_config",
            "native_oai",
            {
                "name": "ctx-model",
                "apikey": "key",
                "apibase": "https://ctx.example.invalid/v1",
                "model": "gpt-5.5",
                "context_win": 1050000,
            },
        )
        ok, message = a.save_llm_config_entries([entry], {"llm_nos": ["ctx-model"]}, [])
        assert ok, message
        loaded_entries, loaded_mixin, _preserved, load_error = a.load_llm_config_entries()
        assert load_error == "", load_error
        assert loaded_mixin["llm_nos"] == ["ctx-model"], loaded_mixin
        assert loaded_entries[0].cfg["context_win"] == 1050000, loaded_entries[0]
    finally:
        a.mykey_path = old_mykey_path


def assert_ohmypi_runtime_context_pack_is_not_repeated() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_omp_context_once_")
    retarget_harness(root)
    runtime_agent = RuntimeCaptureFakeAgent()
    runtime_state = a.State(agent=runtime_agent)
    assert a.start_main_agent_task(
        runtime_state,
        "first task",
        source="user",
        visible_user_text="first task",
    )
    first = runtime_agent.runtime_requests[-1]
    assert "[GA TUI Context Pack]" in first.prompt, first.prompt
    assert "[GA TUI Context Ref]" not in first.prompt, first.prompt
    assert "subagent_identity_rule:" in first.prompt, first.prompt
    assert "copied profile, OMP native task spawn, or IRC demo participant is only a clone" in first.prompt, first.prompt
    assert "final_reply_rule:" in first.prompt, first.prompt
    assert "memory-candidate submitted/deferred notices are not a substitute" in first.prompt, first.prompt
    assert "deictic_reference_rule:" in first.prompt, first.prompt
    assert "not as a user-visible conversation object" in first.prompt, first.prompt
    assert "这个东西" in first.prompt and "most recent visible user-facing topic" in first.prompt, first.prompt
    assert "persistent_agent_request_rule:" in first.prompt, first.prompt
    assert "agent.create with lifecycle:\"persistent\"" in first.prompt, first.prompt
    assert "scripts, schedules, memory candidates" in first.prompt, first.prompt

    runtime_state.status = "idle"
    runtime_state.active_task_id = None
    runtime_state.active_task_source = ""
    assert a.start_main_agent_task(
        runtime_state,
        "second task",
        source="user",
        visible_user_text="second task",
    )
    second = runtime_agent.runtime_requests[-1]
    assert "[GA TUI Context Pack]" not in second.prompt, second.prompt
    assert "[GA TUI Context Ref]" in second.prompt, second.prompt
    assert "final_reply_rule:" in second.prompt, second.prompt
    assert "memory-candidate notices" in second.prompt, second.prompt
    assert "deictic_reference_rule:" in second.prompt, second.prompt
    assert "recent visible conversation/task topic, not to this context ref" in second.prompt, second.prompt
    assert "persistent_agent_request_rule:" in second.prompt, second.prompt
    assert "scripts/schedules alone are not enough" in second.prompt, second.prompt
    assert second.context_pack_ref.startswith("artifact://"), second.context_pack_ref

    a.reset_agent_runtime_context_no_snapshot(runtime_agent)
    runtime_state.status = "idle"
    runtime_state.active_task_id = None
    runtime_state.active_task_source = ""
    assert a.start_main_agent_task(
        runtime_state,
        "third task",
        source="user",
        visible_user_text="third task",
    )
    third = runtime_agent.runtime_requests[-1]
    assert "[GA TUI Context Pack]" in third.prompt, third.prompt


def assert_ohmypi_rpc_extension_approval_bridge() -> None:
    sent: list[dict] = []
    agent = omp.OhMyPiRpcAgent(command=["/fake/omp"])
    agent._send = lambda obj: sent.append(obj)  # type: ignore[method-assign]

    full_request = a.RuntimeTaskRequest(
        task_id="task_approval_full",
        provider_id="ohmypi",
        agent_id="orchestrator.main",
        role="orchestrator",
        objective="run safe bash",
        prompt="",
        permissions={"permission_profile": "full", "tools_allowed": ["bash", "shell"], "memory_write": "candidate_only"},
    )
    agent._active = omp._ActivePrompt(  # type: ignore[attr-defined]
        request_id="prompt-1",
        display_queue=queue.Queue(),
        source="test",
        runtime_request=full_request,
    )
    agent._answer_extension_ui({  # type: ignore[attr-defined]
        "id": "ui-safe",
        "method": "select",
        "title": "Allow tool: bash\nCommand: pwd",
        "options": ["Approve", "Deny"],
    })
    assert sent[-1] == {"type": "extension_ui_response", "id": "ui-safe", "value": "Approve"}, sent[-1]

    agent._answer_extension_ui({  # type: ignore[attr-defined]
        "id": "ui-risky",
        "method": "select",
        "title": "Allow tool: bash\nCommand: rm -rf /tmp/ga-tui-test",
        "options": ["Approve", "Deny"],
    })
    assert sent[-1] == {"type": "extension_ui_response", "id": "ui-risky", "value": "Approve"}, sent[-1]

    standard_request = a.RuntimeTaskRequest(
        task_id="task_approval_standard",
        provider_id="ohmypi",
        agent_id="orchestrator.main",
        role="orchestrator",
        objective="standard mode",
        prompt="",
        permissions={"permission_profile": "standard", "tools_allowed": ["bash"]},
    )
    agent._active = omp._ActivePrompt(  # type: ignore[attr-defined]
        request_id="prompt-2",
        display_queue=queue.Queue(),
        source="test",
        runtime_request=standard_request,
    )
    agent._answer_extension_ui({  # type: ignore[attr-defined]
        "id": "ui-standard",
        "method": "select",
        "title": "Allow tool: bash\nCommand: pwd",
        "options": ["Approve", "Deny"],
    })
    assert sent[-1] == {"type": "extension_ui_response", "id": "ui-standard", "value": "Deny"}, sent[-1]


def assert_ohmypi_rpc_queue_mapping() -> None:
    processes: list[FakeRpcProcess] = []
    memory_signals: list[dict[str, object]] = []
    runtime_events: list[dict[str, object]] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess()
        processes.append(process)
        return process

    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        memory_candidate_sink=lambda signal: memory_signals.append(signal),
        runtime_event_sink=lambda event: runtime_events.append(event.to_record()),
        startup_timeout=1,
    )
    request = a.RuntimeTaskRequest(
        task_id="task_omp_runtime",
        provider_id="ohmypi",
        agent_id="researcher-1",
        role="researcher",
        objective="Validate structured OMP runtime request.",
        prompt="hello",
        source="test",
        context_pack_ref="artifact://context_packs/researcher-1/task_omp_runtime.json",
        artifact_refs=["artifact://context_packs/researcher-1/task_omp_runtime.json"],
    )
    dq = agent.put_runtime_task(request)
    first = dq.get(timeout=2)
    second = dq.get(timeout=2)
    done = dq.get(timeout=2)
    expected_done = "Validated durable lesson: TUI owns memory approval while Oh My Pi emits candidates."
    assert first["next"] == "Validated durable lesson: ", first
    assert second["next"] == "TUI owns memory approval while Oh My Pi emits candidates.", second
    assert done["done"] == expected_done, done
    assert agent.is_running is False
    assert agent.task_queue.unfinished_tasks == 0
    assert any(item.get("type") == "prompt" and item.get("message") == "hello" for item in processes[0].stdin.writes)
    assert memory_signals
    assert memory_signals[-1]["schema_version"] == "ohmypi.memory_candidate_signal.v1", memory_signals[-1]
    assert memory_signals[-1]["statement"] == expected_done, memory_signals[-1]
    assert runtime_events[0]["schema_version"] == "runtime.task_event.v1", runtime_events
    assert runtime_events[0]["event_type"] == "runtime_task_requested", runtime_events
    assert runtime_events[0]["request"]["schema_version"] == "runtime.task_request.v1", runtime_events[0]
    assert "prompt" not in runtime_events[0]["request"], runtime_events[0]
    assert runtime_events[0]["request"]["prompt_preview"] == "hello", runtime_events[0]
    assert runtime_events[0]["request"]["prompt_chars"] == 5, runtime_events[0]
    assert runtime_events[0]["request"]["context_pack_ref"].startswith("artifact://context_packs/"), runtime_events[0]
    assert runtime_events[-1]["event_type"] == "runtime_task_completed", runtime_events
    assert runtime_events[-1]["artifact_refs"] == ["artifact://context_packs/researcher-1/task_omp_runtime.json"], runtime_events[-1]
    agent.close()


def assert_ohmypi_rpc_usage_tracking() -> None:
    processes: list[FakeRpcProcess] = []
    runtime_events: list[dict[str, object]] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        runtime_event_sink=lambda event: runtime_events.append(event.to_record()),
        startup_timeout=1,
    )
    request = a.RuntimeTaskRequest(
        task_id="task_omp_usage",
        provider_id="ohmypi",
        agent_id="orchestrator.main",
        role="main_orchestrator",
        objective="Count usage.",
        prompt="usage",
        source="test",
    )
    dq = agent.put_runtime_task(request)
    process = wait_for_process(processes)
    first_message = {
        "id": "message-usage-1",
        "role": "assistant",
        "content": [{"type": "text", "text": "intermediate"}],
        "usage": {"input": 100, "output": 20, "cacheRead": 300, "cacheWrite": 7, "totalTokens": 427},
        "timestamp": 1780000000,
    }
    final_message = {
        "id": "message-usage-2",
        "role": "assistant",
        "content": [{"type": "text", "text": "usage done"}],
        "usage": {"input": 8, "output": 3, "cacheRead": 50, "cacheWrite": 0, "totalTokens": 61},
        "timestamp": 1780000001,
    }
    process.stdout.push({"type": "message_end", "message": first_message})
    process.stdout.push({"type": "agent_end", "messages": [first_message, final_message]})
    done, _streamed = wait_for_queue_done(dq)
    assert done["done"] == "usage done", done
    assert done["usage"] == {
        "requests": 2,
        "input": 108,
        "output": 23,
        "cache_create": 7,
        "cache_read": 350,
    }, done
    assert runtime_events[-1]["event_type"] == "runtime_task_completed", runtime_events
    assert runtime_events[-1]["payload"]["token_usage"] == done["usage"], runtime_events[-1]
    agent.close()

    fallback_processes: list[FakeRpcProcess] = []
    agent_dir = tempfile.mkdtemp(prefix="ga_tui_omp_usage_agent_")
    sessions_dir = os.path.join(agent_dir, "sessions", "-Programs-Shuheng")
    os.makedirs(sessions_dir, exist_ok=True)
    session_path = os.path.join(sessions_dir, "session.jsonl")
    Path(session_path).write_text("", encoding="utf-8")

    def append_session_usage(message_id: str, input_tokens: int, output_tokens: int, cache_read: int, cache_write: int, text: str) -> None:
        with open(session_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "type": "message",
                "id": f"row-{message_id}",
                "message": {
                    "id": message_id,
                    "role": "assistant",
                    "content": [{"type": "text", "text": text}],
                    "usage": {
                        "input": input_tokens,
                        "output": output_tokens,
                        "cacheRead": cache_read,
                        "cacheWrite": cache_write,
                        "totalTokens": input_tokens + output_tokens + cache_read + cache_write,
                    },
                },
            }, ensure_ascii=False) + "\n")

    append_session_usage("session-message-old", 1000, 1000, 1000, 1000, "old usage")

    def fallback_process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        fallback_processes.append(process)
        return process

    fallback_agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        env={"PI_CODING_AGENT_DIR": agent_dir},
        process_factory=fallback_process_factory,
        startup_timeout=1,
        session_usage_flush_timeout=0.5,
        session_usage_stable_interval=0.02,
    )
    dq = fallback_agent.put_task("usage from session file", source="test")
    process = wait_for_process(fallback_processes)
    append_session_usage("session-message-1", 11, 12, 13, 14, "fallback done")
    process.stdout.push({
        "type": "agent_end",
        "messages": [{"role": "assistant", "content": [{"type": "text", "text": "fallback done"}]}],
    })
    fallback_done, _fallback_streamed = wait_for_queue_done(dq)
    assert fallback_done["done"] == "fallback done", fallback_done
    assert fallback_done["usage"] == {
        "requests": 1,
        "input": 11,
        "output": 12,
        "cache_create": 14,
        "cache_read": 13,
    }, fallback_done

    second_q = fallback_agent.put_task("delayed usage from session file", source="test")

    def append_delayed_usage() -> None:
        time.sleep(0.1)
        append_session_usage("session-message-2", 21, 22, 23, 24, "delayed fallback done")

    threading.Thread(target=append_delayed_usage, daemon=True).start()
    process.stdout.push({
        "type": "agent_end",
        "messages": [{"role": "assistant", "content": [{"type": "text", "text": "delayed fallback done"}]}],
    })
    second_done, _second_streamed = wait_for_queue_done(second_q)
    assert second_done["done"] == "delayed fallback done", second_done
    assert second_done["usage"] == {
        "requests": 1,
        "input": 21,
        "output": 22,
        "cache_create": 24,
        "cache_read": 23,
    }, second_done
    fallback_agent.close()


def assert_ohmypi_native_session_state_and_restore() -> None:
    processes: list[FakeRpcProcess] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        startup_timeout=1,
    )
    target_session = "/tmp/omp-restored-session.jsonl"
    assert agent.switch_runtime_session(target_session) is True
    process = wait_for_process(processes)
    assert any(item.get("type") == "switch_session" and item.get("sessionPath") == target_session for item in process.stdin.writes), process.stdin.writes
    assert agent.native_session_file == target_session, agent.native_session_file
    assert agent.native_session_id == "omp-session-switched", agent.native_session_id
    assert agent.native_message_count == 9, agent.native_message_count
    assert agent.native_context_usage["contextWindow"] == 1000000, agent.native_context_usage
    assert getattr(agent.llmclient.backend, "contextWindow", 0) == 1000000
    assert agent.compact_runtime_session("keep current task") is True
    assert agent.native_context_usage["tokens"] == 45678, agent.native_context_usage
    agent.close()

    class NativeRestoreAgent:
        def __init__(self) -> None:
            self._ga_tui_runtime_provider_id = "ohmypi"
            self.switches: list[str] = []
            self.reset_calls = 0
            self.log_path = ""

        def switch_runtime_session(self, session_path: str) -> bool:
            self.switches.append(session_path)
            return True

        def reset_runtime_session(self) -> None:
            self.reset_calls += 1

        def abort(self) -> None:
            return None

    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)
    shuheng_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_omp_native_restore.txt")
    native_session_path = os.path.join(a.MODEL_RESPONSES_DIR, "omp-native-session.jsonl")
    Path(native_session_path).write_text("", encoding="utf-8")
    a.write_text_atomic(a.SESSION_META_PATH, json.dumps({
        os.path.basename(shuheng_path): {"runtime_provider": "ohmypi", "ohmypi_session_file": native_session_path},
    }, ensure_ascii=False))
    a.append_model_response_transcript_turn(shuheng_path, "恢复这个 OMP 会话", "已完成。")
    restore_agent = NativeRestoreAgent()
    messages, restore_msg, loaded_rounds, total_rounds, _history_message_count = a.restore_backend_and_recent_messages(restore_agent, shuheng_path)
    assert restore_agent.switches == [native_session_path], restore_agent.switches
    assert restore_agent.reset_calls == 0, restore_agent.reset_calls
    assert "已切换到 OMP 原生会话" in restore_msg, restore_msg
    assert loaded_rounds == 1 and total_rounds == 1, (loaded_rounds, total_rounds)
    assert [msg.role for msg in messages[:2]] == ["user", "assistant"], messages

    class NativeTokenAgent:
        def __init__(self) -> None:
            self._ga_tui_runtime_provider_id = "ohmypi"
            self.native_context_usage = {"tokens": 123456, "contextWindow": 1000000, "percent": 12.3456}
            self.native_message_count = 8

    old_cost_tracker = a.cost_tracker
    try:
        a.cost_tracker = None
        token_state = a.State(agent=NativeTokenAgent())
        rendered = [text for text, _attr in a.current_token_lines(token_state, 80)]
        assert any("ctx 123k/1.00M" in line and "12%" in line for line in rendered), rendered
        assert "omp msgs 8" in rendered, rendered
    finally:
        a.cost_tracker = old_cost_tracker


def assert_ohmypi_rpc_final_text_fallback() -> None:
    def make_agent(processes: list[FakeRpcProcess]) -> omp.OhMyPiRpcAgent:
        def process_factory(*_args, **_kwargs):
            process = FakeRpcProcess(auto_finish=False)
            processes.append(process)
            return process

        return omp.OhMyPiRpcAgent(
            command=["/fake/omp", "--mode", "rpc"],
            cwd=str(ROOT),
            process_factory=process_factory,
            startup_timeout=1,
        )

    processes_from_message_end: list[FakeRpcProcess] = []
    agent = make_agent(processes_from_message_end)
    dq = agent.put_task("hello", source="test")
    process = wait_for_process(processes_from_message_end)
    process.stdout.push({
        "type": "message_end",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": "测试成功。"}],
        },
    })
    process.stdout.push({"type": "turn_end"})
    done = dq.get(timeout=2)
    assert done["done"] == "测试成功。", done
    assert agent.is_running is False
    assert agent.task_queue.unfinished_tasks == 0
    agent.close()

    processes_from_turn_end: list[FakeRpcProcess] = []
    agent = make_agent(processes_from_turn_end)
    dq = agent.put_task("hello", source="test")
    process = wait_for_process(processes_from_turn_end)
    process.stdout.push({
        "type": "turn_end",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": "直接成功。"}],
        },
    })
    done = dq.get(timeout=2)
    assert done["done"] == "直接成功。", done
    assert agent.is_running is False
    assert agent.task_queue.unfinished_tasks == 0
    agent.close()


def assert_ohmypi_rpc_streamed_final_text_dedupes_terminal_message() -> None:
    processes: list[FakeRpcProcess] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        startup_timeout=1,
    )
    dq = agent.put_task("segmented punctuation", source="test")
    process = wait_for_process(processes)
    final_text = "明白了。\n1. 注册个体工商户（0.6%费率）\n2. 对接 webhook。"
    for delta in ["明白了", ".", "\n1", ".", " 注册个体工商户（0", ".", "6%费率）\n2", ".", " 对接 webhook", "."]:
        process.stdout.push({
            "type": "message_update",
            "assistantMessageEvent": {"type": "text_delta", "delta": delta},
        })
    process.stdout.push({
        "type": "agent_end",
        "messages": [{"role": "assistant", "content": [{"type": "text", "text": final_text}]}],
    })
    done, streamed = wait_for_queue_done(dq)
    assert done["done"] == streamed, done
    assert done["done"].count("明白了") == 1, done
    assert done["done"].count("注册个体工商户") == 1, done
    assert "0.6%费率" in done["done"], done
    assert "06%费率" not in done["done"], done
    agent.close()


def assert_ohmypi_rpc_waits_for_agent_end_before_next_prompt() -> None:
    processes: list[FakeRpcProcess] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        startup_timeout=1,
        terminal_grace_timeout=1,
    )
    first_q = agent.put_task("first", source="test")
    process = wait_for_process(processes)
    process.stdout.push({
        "type": "message_update",
        "assistantMessageEvent": {"type": "text_delta", "delta": "first done"},
    })
    process.stdout.push({"type": "turn_end"})
    second_q = agent.put_task("second", source="test")
    rejected = second_q.get(timeout=2)
    assert "不能并发启动新任务" in rejected["done"], rejected

    deadline = time.time() + 0.15
    while time.time() < deadline:
        try:
            item = first_q.get(timeout=0.02)
        except queue.Empty:
            continue
        assert "done" not in item, item

    process.stdout.push({"type": "agent_end"})
    first_done = first_q.get(timeout=2)
    assert first_done["done"] == "first done", first_done
    assert agent.is_running is False
    assert agent.task_queue.unfinished_tasks == 0

    third_q = agent.put_task("third", source="test")
    wait_for_rpc_write(process, lambda frame: frame.get("type") == "prompt" and frame.get("message") == "third")
    process.stdout.push({
        "type": "message_update",
        "assistantMessageEvent": {"type": "text_delta", "delta": "third done"},
    })
    process.stdout.push({"type": "agent_end"})
    third_done, _third_streamed = wait_for_queue_done(third_q)
    assert third_done["done"] == "third done", third_done
    agent.close()


def assert_ohmypi_rpc_tool_use_turn_end_waits_for_final_answer() -> None:
    processes: list[FakeRpcProcess] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        startup_timeout=1,
        terminal_grace_timeout=0.05,
    )
    dq = agent.put_task("tool smoke", source="test")
    process = wait_for_process(processes)
    process.stdout.push({
        "type": "tool_execution_start",
        "toolCallId": "tool-read-1",
        "toolName": "read",
        "args": {"path": "README.md"},
    })
    process.stdout.push({
        "type": "tool_execution_end",
        "toolCallId": "tool-read-1",
        "toolName": "read",
        "result": {"content": [{"type": "text", "text": "tool output should not become the final answer"}]},
    })
    tool_use_message = {
        "role": "assistant",
        "content": [{"type": "text", "text": "."}],
        "stopReason": "toolUse",
    }
    process.stdout.push({"type": "message_end", "message": tool_use_message})
    process.stdout.push({
        "type": "turn_end",
        "message": tool_use_message,
        "toolResults": [{"toolCallId": "tool-read-1", "content": "tool output should not become the final answer"}],
    })

    deadline = time.time() + 0.15
    while time.time() < deadline:
        try:
            item = dq.get(timeout=0.02)
        except queue.Empty:
            continue
        assert "done" not in item, item

    process.stdout.push({
        "type": "agent_end",
        "messages": [
            {"role": "toolResult", "content": [{"type": "text", "text": "tool output should not become the final answer"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "TOOL_FINAL_DONE"}], "stopReason": "stop"},
        ],
    })
    done, _streamed = wait_for_queue_done(dq)
    assert "TOOL_FINAL_DONE" in done["done"], done
    assert done["done"].rstrip().endswith("TOOL_FINAL_DONE"), done
    assert agent.is_running is False
    assert agent.task_queue.unfinished_tasks == 0
    agent.close()


def assert_ohmypi_rpc_host_tool_followup_timeout_finishes_stalled_turn() -> None:
    processes: list[FakeRpcProcess] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    def handler(tool_name: str, args: dict[str, object]) -> dict[str, object]:
        return {
            "schema_version": "ga-tui.query.v1",
            "status": "ok",
            "kind": "test.host_tool",
            "tool_name": tool_name,
            "endpoint": str(args.get("endpoint") or ""),
        }

    tool = omp.RpcHostToolDefinition(
        name="ga_tui_query",
        label="GA/TUI Query",
        description="Read-only test query",
        parameters={"type": "object", "properties": {"endpoint": {"type": "string"}}},
    )
    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        host_tool_definitions=[tool],
        host_tool_handler=handler,
        startup_timeout=1,
        terminal_grace_timeout=0.05,
        host_tool_followup_timeout=0.05,
    )
    dq = agent.put_task("host tool stall", source="test")
    process = wait_for_process(processes)
    wait_for_rpc_write(process, lambda frame: frame.get("type") == "prompt")

    process.stdout.push({
        "type": "host_tool_call",
        "id": "call-stalled",
        "toolCallId": "tc-stalled",
        "toolName": "ga_tui_query",
        "arguments": {"endpoint": "runtime_registry"},
    })
    result_frame = wait_for_rpc_write(
        process,
        lambda frame: frame.get("type") == "host_tool_result" and frame.get("id") == "call-stalled",
    )
    assert result_frame["result"]["content"][0]["type"] == "text", result_frame

    done, streamed = wait_for_queue_done(dq)
    assert "Shuheng host tool `ga_tui_query` 已完成" in done["done"], done
    assert "模型没有继续生成最终回复" in done["done"], done
    assert "runtime_registry" in done["done"], done
    assert "ga_tui_query" in streamed, streamed
    assert agent.is_running is False
    assert agent.task_queue.unfinished_tasks == 0
    signal = omp.ohmypi_memory_candidate_signal(done["done"], source="test", request_id="host-tool-stall")
    assert signal is None, signal
    agent.close()


def assert_ohmypi_rpc_host_tool_followup_activity_waits_for_final_answer() -> None:
    processes: list[FakeRpcProcess] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    def handler(tool_name: str, args: dict[str, object]) -> dict[str, object]:
        return {
            "schema_version": "ga-tui.query.v1",
            "status": "ok",
            "kind": "test.large_agent_list",
            "tool_name": tool_name,
            "agents": [
                {"id": f"agent-{index}", "name": f"Agent {index}", "status": "idle"}
                for index in range(40)
            ],
            "endpoint": str(args.get("endpoint") or ""),
        }

    tool = omp.RpcHostToolDefinition(
        name="agent_list",
        label="Agent List",
        description="Read-only test agent listing",
        parameters={"type": "object", "properties": {"endpoint": {"type": "string"}}},
    )
    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        host_tool_definitions=[tool],
        host_tool_handler=handler,
        startup_timeout=1,
        terminal_grace_timeout=0.05,
        host_tool_followup_timeout=0.1,
    )
    dq = agent.put_task("communicate with other models", source="test")
    process = wait_for_process(processes)
    wait_for_rpc_write(process, lambda frame: frame.get("type") == "prompt")

    progress = "Started. Let me discover who's available - Shuheng agents and IRC peers."
    process.stdout.push({
        "type": "message_update",
        "assistantMessageEvent": {"type": "text_delta", "delta": progress},
    })
    process.stdout.push({
        "type": "host_tool_call",
        "id": "call-agent-list",
        "toolCallId": "tc-agent-list",
        "toolName": "agent_list",
        "arguments": {"endpoint": "agents"},
    })
    wait_for_rpc_write(
        process,
        lambda frame: frame.get("type") == "host_tool_result" and frame.get("id") == "call-agent-list",
    )

    time.sleep(0.03)
    process.stdout.push({
        "type": "tool_execution_start",
        "toolCallId": "tool-irc-1",
        "toolName": "irc",
        "args": {"message": "check peers"},
    })
    assert_queue_has_no_done(dq, timeout=0.09)

    final_reply = "我查过了：当前没有其他可用代理，无法继续 IRC 通信。"
    process.stdout.push({
        "type": "message_update",
        "assistantMessageEvent": {"type": "text_delta", "delta": final_reply},
    })
    process.stdout.push({"type": "agent_end"})
    done, _streamed = wait_for_queue_done(dq)
    assert final_reply in done["done"], done
    assert "模型没有继续生成最终回复" not in done["done"], done
    assert agent.is_running is False
    assert agent.task_queue.unfinished_tasks == 0
    agent.close()


def assert_ohmypi_rpc_host_tool_followup_ignores_pre_tool_progress_for_fallback() -> None:
    processes: list[FakeRpcProcess] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    def handler(tool_name: str, args: dict[str, object]) -> dict[str, object]:
        return {
            "schema_version": "ga-tui.query.v1",
            "status": "ok",
            "kind": "test.agent_list",
            "tool_name": tool_name,
            "endpoint": str(args.get("endpoint") or ""),
        }

    tool = omp.RpcHostToolDefinition(
        name="agent_list",
        label="Agent List",
        description="Read-only test agent listing",
        parameters={"type": "object", "properties": {"endpoint": {"type": "string"}}},
    )
    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        host_tool_definitions=[tool],
        host_tool_handler=handler,
        startup_timeout=1,
        terminal_grace_timeout=0.05,
        host_tool_followup_timeout=0.05,
    )
    dq = agent.put_task("host tool with pre-tool progress", source="test")
    process = wait_for_process(processes)
    wait_for_rpc_write(process, lambda frame: frame.get("type") == "prompt")

    progress = "Started. Let me discover who's available - Shuheng agents and IRC peers."
    process.stdout.push({
        "type": "message_update",
        "assistantMessageEvent": {"type": "text_delta", "delta": progress},
    })
    process.stdout.push({
        "type": "host_tool_call",
        "id": "call-pre-tool-progress",
        "toolCallId": "tc-pre-tool-progress",
        "toolName": "agent_list",
        "arguments": {"endpoint": "agents"},
    })
    wait_for_rpc_write(
        process,
        lambda frame: frame.get("type") == "host_tool_result" and frame.get("id") == "call-pre-tool-progress",
    )

    done, _streamed = wait_for_queue_done(dq)
    assert progress in done["done"], done
    assert "Shuheng host tool `agent_list` 已完成" in done["done"], done
    assert "模型没有继续生成最终回复" in done["done"], done
    assert "agents" in done["done"], done
    assert agent.is_running is False
    assert agent.task_queue.unfinished_tasks == 0
    signal = omp.ohmypi_memory_candidate_signal(done["done"], source="test", request_id="host-tool-pre-progress")
    assert signal is None, signal
    agent.close()


def assert_ohmypi_rpc_process_blocks_fold_like_genericagent() -> None:
    processes: list[FakeRpcProcess] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        startup_timeout=1,
    )
    dq = agent.put_task("hello", source="test")
    process = wait_for_process(processes)
    process.stdout.push({
        "type": "message_update",
        "assistantMessageEvent": {
            "type": "thinking_delta",
            "delta": "Hidden OMP reasoning should be folded, not shown as final speech.",
        },
    })
    process.stdout.push({
        "type": "message_update",
        "assistantMessageEvent": {"type": "text_delta", "delta": "."},
    })
    process.stdout.push({
        "type": "tool_execution_start",
        "toolCallId": "tool-read-1",
        "toolName": "read",
        "args": {"path": "README.md"},
    })
    process.stdout.push({
        "type": "tool_execution_end",
        "toolCallId": "tool-read-1",
        "toolName": "read",
        "result": {"content": [{"type": "text", "text": "README contents that should stay folded."}]},
    })
    final_reply = (
        "Validated durable lesson: OMP process blocks should fold in GA-TUI while final replies "
        "stay visible for memory approval and restored sessions."
    )
    process.stdout.push({
        "type": "message_update",
        "assistantMessageEvent": {"type": "text_delta", "delta": final_reply},
    })
    process.stdout.push({"type": "agent_end"})

    done, streamed = wait_for_queue_done(dq)
    text = done["done"]
    assert "**LLM Running (Turn 1) ...**" in text, text
    assert "<summary>Hidden OMP reasoning should be folded, not shown as final speech.</summary>" in text, text
    assert "OMP 思考" not in text, text
    assert "\n.\n" not in text, text
    assert "🛠️ Tool: `read` 📥 args:" in text, text
    assert final_reply in text, text
    assert streamed and streamed in text, streamed

    rendered = a.render_assistant_text(text, done=True, fold_process=True, message_index=20)
    assert "过程组 G21" in rendered, rendered
    assert "Hidden OMP reasoning should be folded" in rendered, rendered
    assert "OMP 思考" not in rendered, rendered
    assert final_reply in rendered, rendered
    assert "README.md" not in rendered, rendered
    assert "README contents that should stay folded" not in rendered, rendered
    assert "\n.\n" not in rendered, rendered

    signal = omp.ohmypi_memory_candidate_signal(text, source="test", request_id="fold-1")
    assert signal is not None, signal
    assert signal["statement"] == final_reply, signal
    agent.close()

    fallback_processes: list[FakeRpcProcess] = []

    def fallback_process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        fallback_processes.append(process)
        return process

    fallback_agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=fallback_process_factory,
        startup_timeout=1,
    )
    fallback_q = fallback_agent.put_task("hello", source="test")
    fallback_process = wait_for_process(fallback_processes)
    fallback_process.stdout.push({
        "type": "message_update",
        "assistantMessageEvent": {"type": "thinking_delta", "delta": "fold this fallback thought"},
    })
    fallback_process.stdout.push({
        "type": "message_end",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": "fallback final reply stays visible"}],
        },
    })
    fallback_process.stdout.push({"type": "turn_end"})
    fallback_done, _fallback_streamed = wait_for_queue_done(fallback_q)
    fallback_text = fallback_done["done"]
    assert "OMP 思考" not in fallback_text, fallback_text
    assert "fold this fallback thought" in fallback_text, fallback_text
    assert "fallback final reply stays visible" in fallback_text, fallback_text
    fallback_rendered = a.render_assistant_text(fallback_text, done=True, fold_process=True, message_index=21)
    assert "fallback final reply stays visible" in fallback_rendered, fallback_rendered
    assert "fold this fallback thought" in fallback_rendered, fallback_rendered
    fallback_agent.close()

    legacy_text = (
        "**LLM Running (Turn 1) ...**\n"
        "<summary>OMP 思考</summary>\n"
        "<thinking>\nold hidden thought\n</thinking>\n\n"
        ".\n\n"
        "**LLM Running (Turn 2) ...**\n"
        "<summary>调用 OMP 工具: read</summary>\n"
        "🛠️ Tool: `read` 📥 args:\n````text\n{\"path\":\"README.md\"}\n````"
    )
    legacy_rendered = a.render_assistant_text(legacy_text, done=True, fold_process=True, message_index=22)
    assert "old hidden thought" in legacy_rendered, legacy_rendered
    assert "OMP 思考" not in legacy_rendered, legacy_rendered
    assert "\n.\n" not in legacy_rendered, legacy_rendered


def assert_ohmypi_rpc_env_model_switch_and_error_mapping() -> None:
    processes: list[FakeRpcProcess] = []
    popen_args: list[list[str]] = []
    popen_kwargs: list[dict[str, object]] = []

    def process_factory(*_args, **kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        popen_args.append(list(_args[0]) if _args else [])
        popen_kwargs.append(dict(kwargs))
        return process

    models = [
        omp.OhMyPiRuntimeModel(provider="ga-tui-alpha", model_id="model-alpha", display_name="alpha", base_url="https://alpha.example.invalid/v1"),
        omp.OhMyPiRuntimeModel(provider="ga-tui-beta", model_id="model-beta", display_name="beta", base_url="https://beta.example.invalid/v1"),
    ]
    env = {"PI_CODING_AGENT_DIR": "/tmp/ga-tui-omp-agent", "GA_TUI_OMP_API_KEY_TEST": "key"}
    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        env=env,
        process_factory=process_factory,
        configured_models=models,
        startup_timeout=1,
    )
    assert agent.list_llms() == [(0, "OhMyPi/alpha", True), (1, "OhMyPi/beta", False)], agent.list_llms()
    switch_state = a.State(agent=agent)
    switch_state.running = True
    ok_switch, switch_msg = a.switch_agent_to_entry(
        switch_state,
        a.LLMConfigEntry(
            "native_oai_config_1",
            "native_oai",
            {"name": "beta", "apikey": "k", "apibase": "https://beta.example.invalid/v1", "model": "model-beta"},
        ),
    )
    assert ok_switch, switch_msg
    assert agent.llm_no == 1
    assert agent.get_llm_name(model=True) == "model-beta"
    pending_model = getattr(agent, "_pending_model", None)
    assert pending_model is not None and pending_model.provider == "ga-tui-beta" and pending_model.model_id == "model-beta", pending_model
    agent._handle_response({
        "type": "response",
        "command": "get_state",
        "success": True,
        "data": {
            "model": {"provider": "ga-tui-alpha", "id": "model-alpha"},
            "contextUsage": {"tokens": 10, "contextWindow": 100, "percent": 10},
        },
    })
    assert agent.llm_no == 1
    assert agent.get_llm_name(model=True) == "model-beta"
    assert agent.get_llm_name(model=False) == "OhMyPi/beta"
    assert getattr(agent.llmclient.backend, "apibase", "") == "https://beta.example.invalid/v1"
    agent._handle_response({
        "type": "response",
        "command": "set_model",
        "success": True,
        "data": {
            "model": {"provider": "ga-tui-beta", "id": "model-beta", "contextWindow": 200},
        },
    })
    assert agent.llm_no == 1
    assert agent.get_llm_name(model=True) == "model-beta"
    assert agent.get_llm_name(model=False) == "OhMyPi/beta"
    assert getattr(agent.llmclient.backend, "apibase", "") == "https://beta.example.invalid/v1"
    assert getattr(agent.llmclient.backend, "contextWindow", 0) == 200
    refreshed_models = [
        omp.OhMyPiRuntimeModel(provider="ga-tui-gamma", model_id="model-gamma", display_name="gamma", base_url="https://gamma.example.invalid/v1"),
        omp.OhMyPiRuntimeModel(provider="ga-tui-beta-new", model_id="model-beta", display_name="beta-new", base_url="https://beta.example.invalid/v1"),
    ]
    refreshed_env = {"PI_CODING_AGENT_DIR": "/tmp/ga-tui-omp-agent-refreshed", "GA_TUI_OMP_API_KEY_TEST_2": "key2"}
    agent.refresh_configured_models(refreshed_models, env=refreshed_env, command=["/fake/omp-new", "--mode", "rpc"])
    assert agent.llm_no == 1
    assert agent.list_llms() == [(0, "OhMyPi/gamma", False), (1, "OhMyPi/beta-new", True)], agent.list_llms()
    dq = agent.put_task("hello", source="test")
    process = wait_for_process(processes)
    assert popen_args[0] == ["/fake/omp-new", "--mode", "rpc"], popen_args
    assert popen_kwargs[0]["env"] == refreshed_env, popen_kwargs
    set_model = wait_for_rpc_write(process, lambda frame: frame.get("type") == "set_model")
    prompt = wait_for_rpc_write(process, lambda frame: frame.get("type") == "prompt")
    assert set_model["provider"] == "ga-tui-beta-new", set_model
    assert set_model["modelId"] == "model-beta", set_model
    assert process.stdin.writes.index(set_model) < process.stdin.writes.index(prompt), process.stdin.writes

    process.stdout.push({
        "type": "message_end",
        "message": {
            "role": "assistant",
            "stopReason": "error",
            "errorMessage": "Incorrect API key provided",
            "errorStatus": "401",
        },
    })
    done = dq.get(timeout=2)
    assert "[Oh My Pi] 401: Incorrect API key provided" == done["done"], done
    assert agent.is_running is False
    assert agent.task_queue.unfinished_tasks == 0
    agent.close()


def assert_ohmypi_host_tool_bridge() -> None:
    processes: list[FakeRpcProcess] = []
    calls: list[tuple[str, dict[str, object]]] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    def handler(tool_name: str, args: dict[str, object]) -> dict[str, object]:
        calls.append((tool_name, args))
        if args.get("endpoint") == "explode":
            raise RuntimeError("boom")
        return {
            "schema_version": "ga-tui.query.v1",
            "status": "ok",
            "kind": "test.host_tool",
            "endpoint": str(args.get("endpoint") or ""),
        }

    tool = omp.RpcHostToolDefinition(
        name="ga_tui_query",
        label="GA/TUI Query",
        description="Read-only test query",
        parameters={"type": "object", "properties": {"endpoint": {"type": "string"}}},
    )
    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        host_tool_definitions=[tool],
        host_tool_handler=handler,
        startup_timeout=1,
    )
    dq = agent.put_task("hello", source="test")
    process = wait_for_process(processes)
    set_host_tools = wait_for_rpc_write(process, lambda frame: frame.get("type") == "set_host_tools")
    prompt = wait_for_rpc_write(process, lambda frame: frame.get("type") == "prompt")
    assert process.stdin.writes.index(set_host_tools) < process.stdin.writes.index(prompt), process.stdin.writes
    assert set_host_tools["tools"][0]["name"] == "ga_tui_query", set_host_tools
    assert set_host_tools["tools"][0]["parameters"]["type"] == "object", set_host_tools

    process.stdout.push({
        "type": "host_tool_call",
        "id": "call-1",
        "toolCallId": "tc-1",
        "toolName": "ga_tui_query",
        "arguments": {"endpoint": "runtime_registry"},
    })
    success = wait_for_rpc_write(process, lambda frame: frame.get("type") == "host_tool_result" and frame.get("id") == "call-1")
    success_text = success["result"]["content"][0]["text"]
    success_payload = json.loads(success_text)
    assert success_payload["schema_version"] == "ga-tui.query.v1", success_payload
    assert success_payload["status"] == "ok", success_payload
    assert calls[-1] == ("ga_tui_query", {"endpoint": "runtime_registry"}), calls

    process.stdout.push({
        "type": "host_tool_call",
        "id": "call-unknown",
        "toolCallId": "tc-unknown",
        "toolName": "unknown_tool",
        "arguments": {},
    })
    unknown = wait_for_rpc_write(
        process,
        lambda frame: frame.get("type") == "host_tool_result" and frame.get("id") == "call-unknown",
    )
    assert unknown["isError"] is True, unknown
    assert "Unknown or unregistered host tool" in unknown["result"]["content"][0]["text"], unknown

    process.stdout.push({
        "type": "host_tool_call",
        "id": "call-error",
        "toolCallId": "tc-error",
        "toolName": "ga_tui_query",
        "arguments": {"endpoint": "explode"},
    })
    failed = wait_for_rpc_write(
        process,
        lambda frame: frame.get("type") == "host_tool_result" and frame.get("id") == "call-error",
    )
    assert failed["isError"] is True, failed
    assert "RuntimeError: boom" in failed["result"]["content"][0]["text"], failed

    process.stdout.push({"type": "host_tool_cancel", "id": "cancel-1", "targetId": "call-1"})
    deadline = time.time() + 2
    while time.time() < deadline and not any("host tool cancel requested: call-1" in item for item in agent._stderr_tail):
        time.sleep(0.01)
    assert any("host tool cancel requested: call-1" in item for item in agent._stderr_tail), agent._stderr_tail

    agent.abort()
    done, _streamed = wait_for_queue_done(dq)
    assert "中止" in done["done"], done
    agent.close()


def assert_ohmypi_tui_query_host_tool_contract() -> None:
    tools = a.ohmypi_tui_readonly_host_tool_definitions()
    assert len(tools) == 1, tools
    tool = tools[0].to_rpc()
    assert tool["name"] == "ga_tui_query", tool
    assert "runtime_registry" in tool["parameters"]["properties"]["endpoint"]["enum"], tool
    assert "artifact_list" in tool["parameters"]["properties"]["endpoint"]["enum"], tool

    handler = a.ohmypi_tui_query_host_tool_handler(None)
    runtime = handler("ga_tui_query", {"endpoint": "runtime_registry"})
    assert runtime["schema_version"] == "ga-tui.query.v1", runtime
    assert runtime["status"] == "ok", runtime
    assert runtime["runtime_registry"]["default_provider_id"] == "ohmypi", runtime
    assert runtime["runtime_registry"]["providers"], runtime
    provider = {item["provider_id"]: item for item in runtime["runtime_registry"]["providers"]}["ohmypi"]
    assert provider["capabilities"]["tui_typed_host_tools"] is True, provider

    tasks = handler("ga_tui_query", {"endpoint": "task_list", "args": {"limit": 1}})
    assert tasks["schema_version"] == "ga-tui.query.v1", tasks
    assert tasks["kind"] == "task.list", tasks

    agent_list = handler("ga_tui_query", {"endpoint": "agent_list"})
    assert agent_list["status"] == "error", agent_list
    assert "TUI state is not bound" in agent_list["error"], agent_list

    unknown = handler("ga_tui_query", {"endpoint": "not-real"})
    assert unknown["status"] == "error", unknown
    assert "runtime_registry" in unknown["supported_endpoints"], unknown
    assert "memory_context_get" in unknown["supported_endpoints"], unknown

    root = tempfile.mkdtemp(prefix="ga_tui_omp_typed_tools_")
    retarget_harness(root)
    state = a.State(agent=FakeLLMAgent())
    steward = a.create_subagent(
        state,
        "Obsidiam管家",
        role="memory_curator",
        persistent=True,
        profile="整理 Obsidiam 知识库；只提交记忆候选。",
    )
    all_tools = [item.to_rpc() for item in a.ohmypi_tui_host_tool_definitions()]
    tool_names = {str(item.get("name") or "") for item in all_tools}
    assert {"ga_tui_query", "agent_list", "schedule_list", "memory_context_get", "memory_candidate_submit"} <= tool_names, all_tools
    query_tool = next(item for item in all_tools if item["name"] == "ga_tui_query")
    assert "or sends messages to agents" in query_tool["description"], query_tool
    typed_agent_get_tool = next(item for item in all_tools if item["name"] == "agent_get")
    assert "identity/interaction rules" in typed_agent_get_tool["description"], typed_agent_get_tool
    typed_agent_match_tool = next(item for item in all_tools if item["name"] == "agent_match")
    assert "not clone its persona" in typed_agent_match_tool["description"], typed_agent_match_tool
    typed_memory_candidate_tool = next(item for item in all_tools if item["name"] == "memory_candidate_submit")
    assert "only when a concrete persistent subagent target is known" in typed_memory_candidate_tool["description"], typed_memory_candidate_tool
    assert "target_role, scope, or responsibility" in typed_memory_candidate_tool["description"], typed_memory_candidate_tool
    assert "Submitted/deferred status must never replace the final user reply" in typed_memory_candidate_tool["description"], typed_memory_candidate_tool
    typed_handler = a.ohmypi_tui_host_tool_handler(state)
    typed_agents = typed_handler("agent_list", {"limit": 5})
    assert typed_agents["schema_version"] == "ga-tui.query.v1", typed_agents
    assert typed_agents["kind"] == "agent.list", typed_agents
    typed_agent = next(row for row in typed_agents["agents"] if row["agent_id"] == steward.agent_id)
    assert typed_agent["runtime_loaded"] is False, typed_agent
    assert typed_agent["interaction_modes"]["same_agent_task"]["command"] == f"/agent ask {steward.agent_id} <prompt>", typed_agent
    assert "not this persistent agent" in typed_agent["identity_contract"]["clone_or_spawn_warning"], typed_agent
    steward_detail = typed_handler("agent_get", {"target": steward.agent_id})
    assert steward_detail["status"] == "ok", steward_detail
    assert steward_detail["agent"]["identity_contract"]["canonical_agent_id"] == steward.agent_id, steward_detail
    assert any(
        f"source=subagent-chat:{steward.agent_id}" in item
        for item in steward_detail["agent"]["identity_contract"]["valid_same_agent_paths"]
    ), steward_detail
    steward_match = typed_handler(
        "agent_match",
        {
            "objective": "跟 Obsidiam 管家说一句话",
            "target": steward.agent_id,
            "reuse_policy": "reuse_only",
            "lifecycle": "persistent",
        },
    )
    assert steward_match["recommended_action"] == "reuse_existing", steward_match
    assert steward_match["recommended_agent"]["agent_id"] == steward.agent_id, steward_match
    assert "clone_or_spawn_warning" in steward_match["recommended_agent"]["identity_contract"], steward_match
    typed_schedule = typed_handler("schedule_list", {})
    assert typed_schedule["status"] == "ok", typed_schedule
    memory_context = typed_handler(
        "memory_context_get",
        {"objective": "Prepare OMP with GA-TUI context.", "task_id": "task_omp_memory_context"},
    )
    assert memory_context["status"] == "ok", memory_context
    assert memory_context["kind"] == "memory.context", memory_context
    assert memory_context["context_pack_ref"].startswith("artifact://"), memory_context
    artifact_rows = a.read_jsonl(a.AGENT_ARTIFACT_INDEX_PATH)
    assert artifact_rows and artifact_rows[-1]["type"] == "context_pack", artifact_rows


def assert_ohmypi_tui_proposal_host_tool_contract() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_omp_proposal_")
    retarget_harness(root)
    state = a.State(agent=FakeLLMAgent())
    target = a.create_subagent(
        state,
        "OMP Proposal Target",
        "Receives durable project memory candidates from governed OMP proposals.",
        role="researcher",
        persistent=True,
    )

    tools = [tool.to_rpc() for tool in a.ohmypi_tui_host_tool_definitions()]
    tool_names = {str(tool.get("name") or "") for tool in tools}
    assert {"ga_tui_query", "ga_tui_propose"} <= tool_names, tools
    propose_tool = next(tool for tool in tools if tool["name"] == "ga_tui_propose")
    assert "ga_control" in propose_tool["parameters"]["properties"]["proposal_type"]["enum"], propose_tool
    assert "memory_candidate" in propose_tool["parameters"]["properties"]["proposal_type"]["enum"], propose_tool

    handler = a.ohmypi_tui_host_tool_handler(state)
    memory_result = handler("ga_tui_propose", {
        "proposal_type": "memory_candidate",
        "target": target.agent_id,
        "statement": (
            "type: project\n"
            "Validated durable lesson: OMP proposal host tools must route long-term memory "
            "through GenericAgent-TUI human approval gates instead of writing memory directly."
        ),
        "evidence_ref": "runtime://provider/ohmypi/test-proposal",
        "task_id": "task_omp_proposal_memory",
    })
    assert memory_result["schema_version"] == "ga-tui.proposal.v1", memory_result
    assert memory_result["status"] == "ok", memory_result
    assert memory_result["kind"] == "memory_candidate", memory_result
    assert memory_result["result_status"] == "queued", memory_result
    assert memory_result["target_subagent"] == target.agent_id, memory_result
    assert memory_result["candidate_ids"], memory_result
    assert memory_result["approval_ids"], memory_result
    assert memory_result["artifact_refs"], memory_result

    candidate_rows = a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)
    approval_rows = a.read_jsonl(a.AGENT_APPROVALS_PATH)
    artifact_rows = a.read_jsonl(a.AGENT_ARTIFACT_INDEX_PATH)
    assert candidate_rows, "missing OMP proposal memory candidate row"
    assert approval_rows, "missing OMP proposal approval row"
    assert artifact_rows, "missing OMP proposal memory artifact row"
    latest_candidate = candidate_rows[-1]
    assert latest_candidate["status"] == "pending", latest_candidate
    assert latest_candidate["approval_id"] == memory_result["approval_ids"][-1], latest_candidate
    assert_memory_candidate_schema(latest_candidate["memory_candidate"])
    latest_approval = approval_rows[-1]
    assert latest_approval["type"] == "memory_write_request", latest_approval
    assert latest_approval["target"] == target.agent_id, latest_approval
    assert latest_approval["approval_id"] == latest_candidate["approval_id"], latest_approval
    latest_artifact = artifact_rows[-1]
    assert_artifact_schema(latest_artifact, artifact_type="memory-candidates")
    assert latest_artifact["uri"] in memory_result["artifact_refs"], (latest_artifact, memory_result)

    typed_memory = handler("memory_candidate_submit", {
        "target": target.agent_id,
        "statement": (
            "type: project\n"
            "Typed OMP memory_candidate_submit must queue a GA-TUI approval record instead of "
            "writing long-term memory directly."
        ),
        "evidence_ref": "runtime://provider/ohmypi/typed-memory",
        "task_id": "task_omp_typed_memory",
    })
    assert typed_memory["schema_version"] == "ga-tui.proposal.v1", typed_memory
    assert typed_memory["status"] == "ok", typed_memory
    assert typed_memory["kind"] == "memory_candidate", typed_memory
    assert typed_memory["approval_ids"], typed_memory

    before_bad_approval_count = len(a.read_jsonl(a.AGENT_APPROVALS_PATH))
    mismatched_memory = handler("memory_candidate_submit", {
        "target": target.agent_id,
        "statement": (
            "type: project\n"
            "target_role: ops\n"
            "scope: ops.monitoring\n"
            "responsibility: recurring service telemetry analysis\n"
            "Durable lesson: a recurring monitoring responsibility must be stored on a matching owner."
        ),
        "evidence_ref": "runtime://provider/ohmypi/target-mismatch",
        "task_id": "task_omp_target_mismatch_memory",
    })
    assert mismatched_memory["schema_version"] == "ga-tui.proposal.v1", mismatched_memory
    assert mismatched_memory["status"] == "ok", mismatched_memory
    assert mismatched_memory["result_status"] == "rejected", mismatched_memory
    assert "target_mismatch_candidate_responsibility" in mismatched_memory["result_message"], mismatched_memory
    mismatch_candidate_rows = a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)
    assert mismatch_candidate_rows[-1]["status"] == "rejected", mismatch_candidate_rows[-1]
    assert mismatch_candidate_rows[-1]["memory_candidate"]["rejected_reason"] == "target_mismatch_candidate_responsibility", mismatch_candidate_rows[-1]
    assert len(a.read_jsonl(a.AGENT_APPROVALS_PATH)) == before_bad_approval_count, a.read_jsonl(a.AGENT_APPROVALS_PATH)

    ops_target = a.create_subagent(
        state,
        "Monitoring Owner",
        "Owns recurring service telemetry analysis and approval-gated operations.",
        role="ops",
        persistent=True,
    )
    matched_memory = handler("memory_candidate_submit", {
        "target": ops_target.agent_id,
        "statement": (
            "type: project\n"
            "target_role: ops\n"
            "scope: ops.monitoring\n"
            "responsibility: recurring service telemetry analysis\n"
            "Durable lesson: a recurring monitoring responsibility must be stored on a matching owner."
        ),
        "evidence_ref": "runtime://provider/ohmypi/target-match",
        "task_id": "task_omp_target_match_memory",
    })
    assert matched_memory["schema_version"] == "ga-tui.proposal.v1", matched_memory
    assert matched_memory["status"] == "ok", matched_memory
    assert matched_memory["result_status"] == "queued", matched_memory
    assert matched_memory["target_subagent"] == ops_target.agent_id, matched_memory

    stale_text = (
        "type: project\n"
        "target_role: ops\n"
        "scope: ops.monitoring\n"
        "responsibility: recurring service telemetry analysis\n"
        "stale-target-mismatch-should-not-land: recurring telemetry ownership belongs to a matching owner."
    )
    stale_candidate = a.build_memory_candidate(target, stale_text, source="agent:ohmypi_host_tool")
    stale_approval_id = a.queue_approval(
        approval_type="memory_write_request",
        summary="stale mismatched responsibility candidate",
        payload={"subagent_id": target.agent_id, "memory": stale_text, "memory_candidate": stale_candidate},
        source="Memory Curator",
        target=target.agent_id,
        approval_required_for="write_long_term_memory",
    )
    stale_decision = a.decide_approval(state, stale_approval_id, True)
    assert "已批准但未写入记忆" in stale_decision, stale_decision
    assert "target_mismatch_candidate_responsibility" in stale_decision, stale_decision
    assert "stale-target-mismatch-should-not-land" not in a.subagent_memory_text(target), a.subagent_memory_text(target)
    stale_rows = a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)
    assert stale_rows[-1]["status"] == "rejected", stale_rows[-1]
    assert stale_rows[-1]["approval_id"] == stale_approval_id, stale_rows[-1]

    typed_schedule = handler("schedule_create", {
        "schedule_id": "sched_omp_typed_digest",
        "name": "OMP Typed Digest",
        "interval": "5m",
        "execution": {
            "mode": "agent_task",
            "routing": {"selected_agent": target.name},
            "work_order": {"objective": "Produce a typed OMP scheduled digest."},
            "capability_contract": {"tools_allowed": ["read"], "write_policy": "none"},
            "context_contract": {"history_mode": "summary", "artifact_reference_only": True},
            "output_contract": {"format": "structured_markdown", "required_sections": ["summary"]},
        },
    })
    assert typed_schedule["schema_version"] == "ga-tui.tool.v1", typed_schedule
    assert typed_schedule["status"] == "ok", typed_schedule
    assert typed_schedule["schedule"]["provider_id"] == "ohmypi", typed_schedule

    control_result = handler("ga_tui_propose", {
        "proposal_type": "ga_control",
        "control": {
            "schema_version": "ga-control.v2",
            "actions": [
                {
                    "action": "task.plan.create",
                    "title": "OMP Proposal Plan",
                    "steps": ["Inspect governed proposal", "Verify policy gate result"],
                }
            ],
        },
    })
    assert control_result["schema_version"] == "ga-tui.proposal.v1", control_result
    assert control_result["status"] == "ok", control_result
    assert control_result["kind"] == "ga_control", control_result
    assert control_result["control_count"] == 1, control_result
    assert any("已创建任务计划：OMP Proposal Plan" in line for line in control_result["result_lines"]), control_result
    assert any("OMP Proposal Plan" in str(row.get("objective") or "") for row in a.read_jsonl(a.AGENT_TASK_LEDGER_PATH))

    invalid_type = handler("ga_tui_propose", {"proposal_type": "not-real"})
    assert invalid_type["status"] == "error", invalid_type
    assert "memory_candidate" in invalid_type["supported_proposal_types"], invalid_type
    invalid_control = handler("ga_tui_propose", {"proposal_type": "ga_control", "control": {"actions": []}})
    assert invalid_control["status"] == "error", invalid_control
    missing_state = a.ohmypi_tui_host_tool_handler(None)("ga_tui_propose", {
        "proposal_type": "memory_candidate",
        "target": target.agent_id,
        "statement": "This should fail because no TUI state is bound.",
    })
    assert missing_state["status"] == "error", missing_state
    assert "TUI state is not bound" in missing_state["error"], missing_state


def assert_agent_bridge_contract_and_omp_plugin() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_agent_bridge_")
    retarget_harness(root)
    state = a.State(agent=FakeLLMAgent())
    target = a.create_subagent(
        state,
        "Bridge Memory Target",
        "Receives memory candidates from external agent bridge clients.",
        role="researcher",
        persistent=True,
    )
    service = bridge.AgentBridgeService(app=a, state=state)
    metadata = service.handle({"action": "metadata"})
    assert metadata["schema_version"] == "ga-tui.agent_bridge.v1", metadata
    assert metadata["owner"] == "ga-tui.control_plane", metadata
    assert "memory_context_get" in metadata["supported_actions"], metadata
    assert metadata["policy"]["provider_direct_writes"] is False, metadata
    assert metadata["paths"]["shuheng_home"] == a.SHUHENG_HOME, metadata
    assert metadata["paths"]["shuheng_memory_dir"] == a.SHUHENG_MEMORY_DIR, metadata
    assert metadata["paths"]["harness_dir"] == a.AGENT_HARNESS_DIR, metadata
    assert metadata["paths"]["subagents_dir"] == a.SUBAGENTS_DIR, metadata
    assert metadata["paths"]["secret_vault_dir"] == a.SECRET_VAULT_DIR, metadata
    assert a.path_is_within(metadata["paths"]["harness_dir"], a.SHUHENG_HOME), metadata
    assert a.path_is_within(metadata["paths"]["subagents_dir"], a.SHUHENG_HOME), metadata

    context = service.handle({
        "action": "memory_context_get",
        "args": {
            "target": target.agent_id,
            "objective": "Hydrate OMP with GA-TUI-owned bridge context.",
            "task_id": "task_agent_bridge_context",
        },
    })
    assert context["schema_version"] == "ga-tui.query.v1", context
    assert context["status"] == "ok", context
    assert context["context_pack_ref"].startswith("artifact://"), context
    artifact_rows = a.read_jsonl(a.AGENT_ARTIFACT_INDEX_PATH)
    assert artifact_rows and artifact_rows[-1]["type"] == "context_pack", artifact_rows

    memory = service.handle({
        "action": "memory_candidate_submit",
        "args": {
            "target": target.agent_id,
            "statement": (
                "type: project\n"
                "Bridge clients must submit durable memories through GA-TUI "
                "approval gates instead of writing provider-owned memory."
            ),
            "evidence_ref": "runtime://provider/ohmypi/plugin-test",
            "task_id": "task_agent_bridge_memory",
        },
    })
    assert memory["schema_version"] == "ga-tui.proposal.v1", memory
    assert memory["status"] == "ok", memory
    assert memory["kind"] == "memory_candidate", memory
    assert memory["result_status"] == "queued", memory
    assert memory["approval_ids"], memory
    candidate = a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)[-1]["memory_candidate"]
    assert_memory_candidate_schema(candidate)
    assert candidate["source"] == "agent:omp_plugin", candidate
    assert candidate["target_subagent"] == target.agent_id, candidate

    missing = service.handle({"action": "does_not_exist"})
    assert missing["schema_version"] == "ga-tui.agent_bridge.v1", missing
    assert missing["status"] == "error", missing
    assert "memory_context_get" in missing["supported_actions"], missing

    plugin_dir = ROOT / "integrations" / "omp-ga-tui-plugin"
    package_json = json.loads((plugin_dir / "package.json").read_text(encoding="utf-8"))
    manifest = package_json["omp"]
    assert manifest["tools"] == "tools/index.ts", manifest
    assert manifest["settings"]["repoRoot"]["env"] == "GA_TUI_REPO", manifest
    tool_source = (plugin_dir / "tools" / "index.ts").read_text(encoding="utf-8")
    assert "ga_tui_context_get" in tool_source, tool_source
    assert "ga_tui_memory_candidate_submit" in tool_source, tool_source
    assert "ga_tui.agent_bridge" in tool_source, tool_source
    assert "PYTHONPATH=" in tool_source, tool_source


def assert_ohmypi_memory_candidate_signal_filters() -> None:
    assert omp.ohmypi_memory_candidate_signal("", source="test") is None
    assert omp.ohmypi_memory_candidate_signal("too short", source="test") is None
    secret_durable = "Secret durable lesson should not leave the Secret Vault boundary even if it is long enough for candidate extraction."
    assert omp.ohmypi_memory_candidate_signal(secret_durable, source="secret-main:user") is None
    secret = "This output contains api_key: SHOULD_NOT_LEAK and must not be retained long term."
    assert omp.ohmypi_memory_candidate_signal(secret, source="test") is None
    mixed_host_tool_fallback = (
        "Started. Let me discover agents.\n\n"
        "[Oh My Pi] Shuheng host tool `agent_list` 已完成，但模型没有继续生成最终回复。\n\n"
        "工具结果摘要：{}"
    )
    assert omp.ohmypi_memory_candidate_signal(mixed_host_tool_fallback, source="test") is None
    durable = (
        "Validated durable lesson: when Oh My Pi runs under GenericAgent-TUI, "
        "the TUI must remain the memory approval owner and OMP should only emit candidates."
    )
    signal = omp.ohmypi_memory_candidate_signal(durable, source="test", request_id="req-1")
    assert signal is not None, signal
    assert signal["statement"].startswith("Validated durable lesson"), signal
    assert signal["evidence_ref"] == "runtime://provider/ohmypi/req-1", signal


def assert_ohmypi_missing_binary_and_abort() -> None:
    missing_agent = omp.OhMyPiRpcAgent(command=["ga-tui-definitely-missing-omp"], startup_timeout=0.1)
    missing_q = missing_agent.put_task("hello", source="test")
    missing = missing_q.get(timeout=2)
    assert "not found" in missing["done"], missing
    assert missing_agent.is_running is False
    assert missing_agent.task_queue.unfinished_tasks == 0

    processes: list[FakeRpcProcess] = []

    def process_factory(*_args, **_kwargs):
        process = FakeRpcProcess(auto_finish=False)
        processes.append(process)
        return process

    agent = omp.OhMyPiRpcAgent(
        command=["/fake/omp", "--mode", "rpc"],
        cwd=str(ROOT),
        process_factory=process_factory,
        startup_timeout=1,
    )
    dq = agent.put_task("long", source="test")
    deadline = time.time() + 2
    while time.time() < deadline and not any(item.get("type") == "prompt" for item in processes[0].stdin.writes):
        time.sleep(0.01)
    agent.abort()
    done = dq.get(timeout=2)
    assert "中止" in done["done"], done
    assert any(item.get("type") == "abort" for item in processes[0].stdin.writes), processes[0].stdin.writes
    assert agent.task_queue.unfinished_tasks == 0
    agent.close()


def ga_control(*actions: dict) -> str:
    return "<ga-control>" + json.dumps({"schema_version": "ga-control.v2", "actions": list(actions)}, ensure_ascii=False) + "</ga-control>"


def plan_action(title: str, steps: list[str]) -> dict:
    return {"action": "task.plan.create", "title": title, "steps": steps}


def create_agent_action(
    name: str,
    *,
    profile: str = "",
    role: str = "specialist",
    persistent: bool | None = None,
    temporary: bool | None = None,
    force_new: bool = False,
    default_model: str = "",
    parent_task_id: str = "",
    plan_step_id: str = "",
) -> dict:
    action = {"action": "agent.create", "name": name, "role": role, "profile": profile}
    if persistent is not None:
        action["lifecycle"] = "persistent" if persistent else "ephemeral"
        action["persistent"] = persistent
    if temporary is not None:
        action["lifecycle"] = "ephemeral" if temporary else "persistent"
        action["temporary"] = temporary
    if force_new:
        action["reuse_policy"] = "force_new"
        action["force_new"] = True
    if default_model:
        action["default_model"] = default_model
    if parent_task_id:
        action["parent_task_id"] = parent_task_id
    if plan_step_id:
        action["plan_step_id"] = plan_step_id
    return action


def delegate_action(target: str, objective: str, *, parent_task_id: str = "", role: str = "researcher", task_title: str = "") -> dict:
    return {
        "schema_version": "agenttask.v2",
        "action": "delegate.create",
        "parent_task_id": parent_task_id,
        "task_title": task_title,
        "routing": {
            "mode": "agent_as_tool",
            "selected_agent": target,
            "target_selector": {
                "role": role,
                "capabilities_required": ["read"],
                "reuse_policy": "prefer_existing",
                "security_context": "standard",
            },
        },
        "work_order": {
            "objective": objective,
            "background": "policy gate regression test",
            "non_goals": ["do not exceed delegated scope"],
            "success_criteria": ["return a bounded structured result"],
            "stop_condition": "return summary, evidence refs, risks, artifact refs, and confidence",
        },
        "capability_contract": {
            "tools_allowed": ["read"],
            "tools_forbidden": ["repo.write", "deploy", "email.send"],
            "write_policy": "none",
            "network_policy": "none",
            "memory_write": "candidate_only",
            "max_subagents": 0,
        },
        "context_contract": {
            "history_mode": "summary",
            "artifact_reference_only": True,
            "include_raw_logs": False,
        },
        "output_contract": {
            "format": "structured_markdown",
            "required_sections": ["summary", "findings", "evidence_refs", "risks", "artifact_refs", "confidence"],
            "schema_validation": "strict",
            "on_invalid_output": "request_repair_once",
        },
    }


class FakeBackend:
    def __init__(self, name: str, model: str, apibase: str = "https://example.invalid/v1") -> None:
        self.name = name
        self.model = model
        self.apibase = apibase
        self.history: list[str] = []
        self.extra_sys_prompt = ""
        self.log_path = ""


class ScriptedMetadataBackend(FakeBackend):
    def __init__(self, titles: list[str]) -> None:
        super().__init__("metadata", "model-metadata")
        self.title_queue = titles
        self.raw_prompts: list[str] = []

    def raw_ask(self, request):
        prompt = ""
        try:
            content = request[0]["content"][0]
            prompt = str(content.get("text") or "")
        except Exception:
            prompt = str(request)
        self.raw_prompts.append(prompt)
        if "生成一个简短标题" in prompt:
            text = self.title_queue.pop(0) if self.title_queue else "默认会话标题"
        elif "维护一个简介" in prompt:
            text = "这是会话简介，说明主题和当前进展。"
        elif "选择一个分类" in prompt:
            text = "Shuheng"
        else:
            text = ""
        if False:
            yield ""
        return [{"type": "text", "text": text}]


class FakeLLMClient:
    def __init__(self, name: str, model: str, apibase: str = "https://example.invalid/v1") -> None:
        self.backend = FakeBackend(name, model, apibase)
        self.last_tools = ""


class FakeLLMAgent:
    def __init__(self) -> None:
        self.log_path = ""
        self.history: list[str] = []
        self.handler = None
        self.prompts: list[tuple[str, str]] = []
        self.llm_no = 0
        self.llmclients = [
            FakeLLMClient("default", "model-default"),
            FakeLLMClient("alpha", "model-alpha"),
            FakeLLMClient("beta", "model-beta"),
        ]
        self.llmclient = self.llmclients[0]

    def load_llm_sessions(self) -> None:
        return None

    def next_llm(self, index: int = -1) -> None:
        self.llm_no = ((self.llm_no + 1) if index < 0 else index) % len(self.llmclients)
        self.llmclient = self.llmclients[self.llm_no]

    def get_llm_name(self, b=None, model: bool = False) -> str:
        client = self.llmclient if b is None else b
        return client.backend.model if model else f"Fake/{client.backend.name}"

    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        self.prompts.append((prompt, source))
        dq: queue.Queue = queue.Queue()
        dq.put({"done": "ok"})
        return dq

    def abort(self) -> None:
        return None


class ScriptedMetadataAgent(FakeLLMAgent):
    def __init__(self, titles: list[str]) -> None:
        super().__init__()
        self.llmclient = FakeLLMClient("metadata", "model-metadata")
        self.llmclient.backend = ScriptedMetadataBackend(titles)
        self.llmclients = [self.llmclient]


class RuntimeCaptureFakeAgent(FakeLLMAgent):
    def __init__(self) -> None:
        super().__init__()
        self.runtime_requests: list[a.RuntimeTaskRequest] = []
        self._ga_tui_runtime_provider_id = "ohmypi"

    def put_runtime_task(self, request: a.RuntimeTaskRequest) -> queue.Queue:
        self.runtime_requests.append(request)
        dq: queue.Queue = queue.Queue()
        dq.put({"done": "runtime ok"})
        return dq


class AbortCountingFakeAgent(FakeLLMAgent):
    def __init__(self) -> None:
        super().__init__()
        self.abort_count = 0

    def abort(self) -> None:
        self.abort_count += 1


class ContextCheckingFakeAgent(FakeLLMAgent):
    def __init__(self, marker: str) -> None:
        super().__init__()
        self.marker = marker

    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        self.prompts.append((prompt, source))
        dq: queue.Queue = queue.Queue()
        ok = False
        for item in getattr(self.llmclient.backend, "history", []) or []:
            content = item.get("content") if isinstance(item, dict) else None
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and self.marker in str(block.get("text") or ""):
                    ok = True
        dq.put({"done": "context ok" if ok else "missing restored context"})
        return dq


class TimeoutFakeScreen:
    def __init__(self) -> None:
        self.timeouts: list[int] = []

    def timeout(self, value: int) -> None:
        self.timeouts.append(value)


class FakeDrawScreen:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int, str, int]] = []
        self.moves: list[tuple[int, int]] = []
        self.refresh_count = 0

    def getmaxyx(self) -> tuple[int, int]:
        return (40, 120)

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        self.calls.append((y, x, text, attr))

    def move(self, y: int, x: int) -> None:
        self.moves.append((y, x))

    def refresh(self) -> None:
        self.refresh_count += 1
        return None


def install_fake_agent_runtime() -> None:
    def fake_ensure(state: a.State, sub: a.SubAgentRuntime) -> FakeAgent:
        del state
        if sub.agent is None:
            sub.agent = FakeAgent()
        return sub.agent

    a.ensure_subagent_agent = fake_ensure


def latest_approval(*, approval_type: str = "", deferred: str = "") -> dict:
    rows = list(a.approval_latest_records().values())
    rows.sort(key=lambda row: str(row.get("timestamp") or ""))
    for row in reversed(rows):
        payload = row.get("payload") or {}
        if approval_type and row.get("type") != approval_type:
            continue
        if deferred and payload.get("deferred_operation") != deferred:
            continue
        return row
    raise AssertionError(f"approval not found type={approval_type!r} deferred={deferred!r}")


def backend_history_text(agent: FakeLLMAgent) -> str:
    return json.dumps([client.backend.history for client in agent.llmclients], ensure_ascii=False, default=str)


def seed_agent_context(agent: FakeLLMAgent, marker: str) -> None:
    agent.history = [marker]
    agent.handler = type("FakeHandler", (), {"working": {"key_info": marker}})()
    setattr(agent, "_ga_tui_pending_key_info", marker)
    for client in agent.llmclients:
        client.backend.history = [{"role": "user", "content": marker}]
        client.last_tools = marker


def drain_ui(state: a.State) -> None:
    time.sleep(0.1)
    a.process_ui_queue(state)


TASK_SCHEMA_KEYS = {"priority", "budget", "permissions", "context_policy", "task", "risks", "approval"}
MAIL_SCHEMA_KEYS = {
    "parent_task_id",
    "priority",
    "project_pool",
    "budget",
    "permissions",
    "context_policy",
    "task",
    "risks",
    "approval",
    "assumptions",
    "open_questions",
}
ARTIFACT_SCHEMA_KEYS = {
    "artifact_id",
    "type",
    "uri",
    "path",
    "preview_path",
    "hash",
    "size_bytes",
    "source_task_id",
    "provenance",
}
ORCHESTRATOR_PLAN_KEYS = {
    "plan_id",
    "route_id",
    "task_understanding",
    "should_split_agents",
    "split_reason",
    "architecture_pattern",
    "task_plan",
    "routing_decision",
    "subagent_delegations",
    "delegation_contract",
    "approval_required",
    "context_plan",
    "memory_plan",
    "evaluation_plan",
    "stop_conditions",
}
MEMORY_CANDIDATE_KEYS = {
    "candidate_id",
    "scope",
    "type",
    "statement",
    "evidence_refs",
    "confidence",
    "ttl",
    "dedupe_key",
    "duplicate_of",
    "conflicts_with",
    "conflict_check",
    "requires_human_approval",
}
TRACE_SCHEMA_KEYS = {
    "context_id",
    "phase",
    "actor",
    "severity",
    "audit_refs",
    "metrics",
    "policy",
}
EVAL_SCORE_KEYS = {
    "completion",
    "factual_accuracy",
    "citation_accuracy",
    "source_quality",
    "tool_efficiency",
    "policy_compliance",
    "human_takeover_cost",
}
AUDIT_REF_KEYS = {
    "plan_versions",
    "messages",
    "tool_calls",
    "artifacts",
    "checkpoints",
    "approvals",
    "memory_candidates",
    "traces",
}
CHECKPOINT_SCHEMA_KEYS = {
    "checkpoint_id",
    "task_id",
    "status",
    "reason",
    "path",
    "uri",
    "hash",
    "audit_refs",
}
RECOVERY_SCHEMA_KEYS = {
    "recovery_id",
    "task_id",
    "action",
    "status",
    "before_checkpoint_id",
    "after_checkpoint_id",
    "audit_refs",
    "recovery_plan_id",
    "recovery_plan_ref",
}
RECOVERY_PLAN_SCHEMA_KEYS = {
    "recovery_plan_id",
    "task_id",
    "action",
    "status",
    "source_checkpoint",
    "replayable",
    "replay_steps",
    "state_patch",
    "approval",
    "rollback",
    "artifact_refs",
}
BASELINE_ITEM_IDS = {
    "strong_orchestrator",
    "restricted_subagents",
    "shared_ledgers",
    "artifact_store",
    "approval_gates",
    "governance_components",
    "single_writer",
    "context_engineering",
    "external_memory",
    "eval_trace",
    "checkpoint_recovery",
    "a2a_mcp_gateway",
    "external_bridges",
}


def assert_task_schema(row: dict, *, status: str = "") -> None:
    missing = TASK_SCHEMA_KEYS - set(row)
    assert not missing, f"task schema missing {missing}: {row}"
    assert isinstance(row["budget"].get("max_tokens"), int), row
    assert "role" in row["permissions"], row
    assert "write_policy" in row["permissions"], row
    assert "history_mode" in row["context_policy"], row
    assert "stop_condition" in row["task"], row
    assert "approval_status" in row["approval"], row
    if status:
        assert row.get("status") == status, row


def assert_mail_schema(row: dict, *, intent: str = "") -> None:
    missing = MAIL_SCHEMA_KEYS - set(row)
    assert not missing, f"mail schema missing {missing}: {row}"
    assert isinstance(row["budget"].get("max_tool_calls"), int), row
    assert "role" in row["permissions"], row
    assert "tools_allowed" in row["permissions"], row
    assert "artifact_reference_only" in row["context_policy"], row
    assert "output_contract" in row["task"], row
    assert "approval_status" in row["approval"], row
    if intent:
        assert row.get("intent") == intent, row


def assert_artifact_schema(row: dict, *, artifact_type: str = "") -> None:
    missing = ARTIFACT_SCHEMA_KEYS - set(row)
    assert not missing, f"artifact schema missing {missing}: {row}"
    assert str(row["artifact_id"]).startswith("art_"), row
    assert str(row["uri"]).startswith("artifact://"), row
    assert str(row["hash"]).startswith("sha256:"), row
    assert os.path.exists(str(row["preview_path"])), row
    assert isinstance(row["provenance"], dict), row
    if artifact_type:
        assert row.get("type") == artifact_type, row


def assert_orchestrator_plan_schema(row: dict, *, status: str = "") -> None:
    missing = ORCHESTRATOR_PLAN_KEYS - set(row)
    assert not missing, f"orchestrator plan schema missing {missing}: {row}"
    assert row["architecture_pattern"] == "orchestrator_worker", row
    assert row["should_split_agents"] is True, row
    assert row["task_plan"], row
    route = row["routing_decision"]
    assert route["mode"] in {"agent_as_tool", "single_writer_code_squad"}, row
    assert route["selected_agent"], row
    contract = row["delegation_contract"]
    assert contract["objective"], row
    assert isinstance(contract["budget"].get("max_tokens"), int), row
    assert "role" in contract["permissions"], row
    assert contract["context_policy"]["artifact_reference_only"] is True, row
    assert contract["source_policy"]["allowed_sources"], row
    assert contract["task"]["boundaries"], row
    assert contract["task"]["output_contract"]["required_sections"], row
    assert row["memory_plan"]["write_policy"] == "candidate_only", row
    assert "policy_compliance" in row["evaluation_plan"]["checks"], row
    assert row["stop_conditions"], row
    if status:
        assert row.get("status") == status, row


def assert_memory_candidate_schema(candidate: dict) -> None:
    missing = MEMORY_CANDIDATE_KEYS - set(candidate)
    assert not missing, f"memory candidate schema missing {missing}: {candidate}"
    assert candidate["candidate_id"].startswith("memcand_"), candidate
    assert candidate["scope"].startswith("subagent."), candidate
    assert candidate["type"] in {"preference", "project", "procedural", "episodic", "semantic"}, candidate
    assert candidate["statement"], candidate
    assert candidate["evidence_refs"], candidate
    assert isinstance(candidate["confidence"], float), candidate
    assert candidate["ttl"] in {"short", "medium", "long"}, candidate
    assert candidate["dedupe_key"].startswith("sha256:"), candidate
    assert isinstance(candidate["duplicate_of"], list), candidate
    assert isinstance(candidate["conflicts_with"], list), candidate
    assert candidate["conflict_check"]["existing_memory_checked"] is True, candidate
    assert candidate["conflict_check"]["pending_candidates_checked"] is True, candidate
    assert candidate["requires_human_approval"] is True, candidate


def assert_trace_schema(row: dict) -> None:
    missing = TRACE_SCHEMA_KEYS - set(row)
    assert not missing, f"trace schema missing {missing}: {row}"
    assert row["schema_version"] == "agenttrace.v2", row
    assert row["trace_id"].startswith("trace_"), row
    assert isinstance(row["actor"], dict), row
    assert row["severity"] in {"info", "warning", "error"}, row
    for key in ("artifacts", "approvals", "memory_candidates", "messages", "tool_calls", "checkpoints"):
        assert key in row["audit_refs"], row
        assert isinstance(row["audit_refs"][key], list), row
    for key in ("tool_calls_delta", "artifact_refs_delta", "approval_refs_delta", "memory_candidate_refs_delta"):
        assert key in row["metrics"], row
    assert "policy_compliance" in row["policy"], row


def assert_eval_schema(row: dict) -> None:
    assert row["schema_version"] == "agenteval.v2", row
    scores = row["scores"]
    missing_scores = EVAL_SCORE_KEYS - set(scores)
    assert not missing_scores, f"eval scores missing {missing_scores}: {row}"
    for key in EVAL_SCORE_KEYS:
        assert isinstance(scores[key], float), row
        assert 0.0 <= scores[key] <= 1.0, row
    missing_refs = AUDIT_REF_KEYS - set(row["audit_refs"])
    assert not missing_refs, f"eval audit refs missing {missing_refs}: {row}"
    assert row["audit_refs"]["traces"], row
    assert row["audit_refs"]["artifacts"], row
    assert row["coverage"]["trace_count"] >= 1, row
    assert row["coverage"]["artifact_count"] >= 1, row
    assert row["final_state"]["status"] in {"completed", "empty_result"}, row
    assert isinstance(row["policy"]["human_takeover_cost"], float), row


def assert_checkpoint_schema(row: dict, *, status: str = "") -> None:
    missing = CHECKPOINT_SCHEMA_KEYS - set(row)
    assert not missing, f"checkpoint schema missing {missing}: {row}"
    assert row["schema_version"] == "agentcheckpoint.index.v1", row
    assert row["checkpoint_id"].startswith("ckpt_"), row
    assert row["uri"].startswith("artifact://checkpoints/"), row
    assert row["hash"].startswith("sha256:"), row
    assert os.path.exists(row["path"]), row
    if status:
        assert row["status"] == status, row


def assert_recovery_schema(row: dict, *, action: str = "") -> None:
    missing = RECOVERY_SCHEMA_KEYS - set(row)
    assert not missing, f"recovery schema missing {missing}: {row}"
    assert row["schema_version"] == "agentrecovery.v1", row
    assert row["recovery_id"].startswith("recovery_"), row
    assert row["before_checkpoint_id"].startswith("ckpt_"), row
    if row.get("after_checkpoint_id"):
        assert row["after_checkpoint_id"].startswith("ckpt_"), row
    if action:
        assert row["action"] == action, row


def assert_recovery_plan_schema(row: dict, *, action: str = "") -> None:
    missing = RECOVERY_PLAN_SCHEMA_KEYS - set(row)
    assert not missing, f"recovery plan schema missing {missing}: {row}"
    assert row["schema_version"] == "agentrecovery.plan.v1", row
    assert row["recovery_plan_id"].startswith("recoveryplan_"), row
    assert row["replayable"] is True, row
    assert row["replay_steps"], row
    assert row["source_checkpoint"]["checkpoint_id"].startswith("ckpt_"), row
    assert row["source_checkpoint"]["hash"].startswith("sha256:"), row
    assert row["rollback"]["source_checkpoint_id"] == row["source_checkpoint"]["checkpoint_id"], row
    assert row["artifact_refs"] and row["artifact_refs"][0].startswith("artifact://artifacts/recovery-plans/"), row
    if action:
        assert row["action"] == action, row


def assert_gateway_schema(registry: dict) -> None:
    assert registry["schema_version"] == "agentgateway.v1", registry
    assert registry["internal_agent_mail"]["governance"] == a.AGENT_GOVERNANCE_PATH, registry
    service = registry["gateway_service"]
    assert service["schema_version"] == "agentgateway.service.v1", service
    assert service["status"] == "network_capable", service
    assert service["request_response"]["registry"].endswith("/gateway"), service
    assert service["sse"]["endpoint"].endswith("/a2a/events"), service
    assert service["push_notifications"]["subscriptions_path"] == a.AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH, service
    assert {"start", "stop", "restart", "status"} <= set(service["daemon"]["commands"]), service
    assert service["daemon"]["status_path"] == a.AGENT_GATEWAY_DAEMON_STATUS_PATH, service
    a2a = registry["a2a_gateway"]
    assert a2a["schema_version"] == "a2a.gateway.v1", a2a
    assert a2a["status"] == "network_capable", a2a
    assert a2a["contextId"] == "ga-tui", a2a
    for key in ("AgentCard", "Task", "Message", "Part", "Artifact", "contextId"):
        assert key in a2a["objects"], a2a
    for key in ("agent_cards", "tasks", "messages", "artifacts"):
        assert isinstance(a2a[key], list), a2a
    assert a2a["request_response"]["task_query"] == "/a2a/tasks/query", a2a
    assert a2a["subscriptions"]["streaming"] == "/a2a/events", a2a
    assert a2a["subscriptions"]["push_notifications"] == "/a2a/push-subscriptions", a2a
    mcp = registry["mcp_gateway"]
    assert mcp["schema_version"] == "mcp.gateway.v1", mcp
    assert mcp["status"] == "network_capable", mcp
    assert mcp["tools"], mcp
    assert mcp["resources"], mcp
    assert mcp["request_response"]["resource_read"] == "/mcp/resource?uri={uri}", mcp
    assert any(item["uri"] == "resource://agent-mail/checkpoints" for item in mcp["resources"]), mcp
    assert any(item["uri"] == "resource://agent-mail/recovery-plans" for item in mcp["resources"]), mcp
    assert any(item["uri"] == "resource://agent-mail/runtime-providers" for item in mcp["resources"]), mcp
    assert any(item["uri"] == "resource://agent-mail/schedules" for item in mcp["resources"]), mcp
    assert any(item["uri"] == "resource://agent-mail/schedule-runs" for item in mcp["resources"]), mcp
    assert any(item["uri"] == "resource://agent-mail/gateway-daemon" for item in mcp["resources"]), mcp
    assert any(item["uri"] == "resource://agent-mail/bridges" for item in mcp["resources"]), mcp
    assert any(item["name"] == "repo.read" for item in mcp["tools"]), mcp
    capabilities = registry["capability_registry"]
    assert capabilities["schema_version"] == "agentcapabilities.v1", capabilities
    assert "researcher" in capabilities["roles"], capabilities
    assert capabilities["roles"]["researcher"]["permissions"]["write_policy"] == "none", capabilities
    assert capabilities["runtime_registry_ref"] == a.AGENT_RUNTIME_REGISTRY_PATH, capabilities
    capability_provider_ids = {item["provider_id"] for item in capabilities["runtime_providers"]}
    assert {"genericagent", "ohmypi"} <= capability_provider_ids, capabilities
    runtime_registry = registry["runtime_registry"]
    assert runtime_registry["schema_version"] == "agentruntime.registry.v1", runtime_registry
    assert runtime_registry["default_provider_id"] == "ohmypi", runtime_registry
    assert "genericagent" in runtime_registry["provider_ids"], runtime_registry
    assert "ohmypi" in runtime_registry["provider_ids"], runtime_registry
    providers_by_id = {item["provider_id"]: item for item in runtime_registry["providers"]}
    runtime_provider = providers_by_id["genericagent"]
    assert runtime_provider["schema_version"] == "agentruntime.provider.v1", runtime_provider
    assert runtime_provider["capabilities"]["streaming"] is True, runtime_provider
    assert runtime_provider["model_routing"]["owner"] == "ga-tui.control_plane", runtime_provider
    assert runtime_provider["scheduler"]["dispatch_contract"] == "agenttask.v2", runtime_provider
    ohmypi_provider = providers_by_id["ohmypi"]
    assert ohmypi_provider["transport"] == "jsonl_stdio_rpc", ohmypi_provider
    assert ohmypi_provider["capabilities"]["streaming"] is True, ohmypi_provider
    assert ohmypi_provider["capabilities"]["host_tools"] is False, ohmypi_provider
    assert ohmypi_provider["capabilities"]["tui_readonly_host_tools"] is True, ohmypi_provider
    assert ohmypi_provider["capabilities"]["tui_governed_proposal_tools"] is True, ohmypi_provider
    assert ohmypi_provider["capabilities"]["tui_typed_host_tools"] is True, ohmypi_provider
    assert ohmypi_provider["capabilities"]["runtime_task_requests"] is True, ohmypi_provider
    assert ohmypi_provider["capabilities"]["runtime_task_events"] is True, ohmypi_provider
    assert ohmypi_provider["capabilities"]["memory_candidate_signals"] is True, ohmypi_provider
    assert ohmypi_provider["scheduler"]["status"] == "registry_ready", ohmypi_provider
    assert ohmypi_provider["policy"]["tool_permissions"] == "tui_readonly_and_governed_proposal_tools_only", ohmypi_provider
    assert ohmypi_provider["policy"]["runtime_tool_approval_mode"] == "yolo", ohmypi_provider
    assert ohmypi_provider["policy"]["memory_write"] == "candidate_only", ohmypi_provider
    assert os.path.exists(a.AGENT_RUNTIME_REGISTRY_PATH), a.AGENT_RUNTIME_REGISTRY_PATH
    model_orchestration = registry["model_orchestration"]
    assert model_orchestration["schema_version"] == "model_orchestration.v1", model_orchestration
    assert model_orchestration["owner"] == "ga-tui.control_plane", model_orchestration
    assert model_orchestration["capabilities"]["set_subagent_default_model"] is True, model_orchestration
    scheduled = registry["scheduled_task_registry"]
    assert scheduled["schema_version"] == "scheduledtask.registry.v1", scheduled
    assert scheduled["owner"] == "ga-tui.control_plane", scheduled
    assert scheduled["dispatch"]["contract"] == "agenttask.v2", scheduled
    assert scheduled["job_count"] >= 1, scheduled
    bridges = registry["bridge_registry"]
    assert bridges["schema_version"] == "agentbridge.registry.v1", bridges
    assert {"feishu", "openclaw", "codex", "claude_code", "deer_flow", "cli", "dashboard", "approval_inbox"} <= set(bridges["bridge_ids"]), bridges
    assert all((item["policy"] or {}).get("approval_required_for") for item in bridges["bridges"]), bridges
    assert_governance_schema(registry["governance_components"])
    assert_baseline_report_schema(registry["baseline_comparison"])


def assert_governance_schema(registry: dict) -> None:
    assert registry["schema_version"] == "agentgovernance.components.v1", registry
    required = {
        "meta_orchestrator",
        "planner",
        "router",
        "context_engineer",
        "approval_controller",
        "risk_guard",
        "memory_curator",
        "eval_controller",
        "recovery_controller",
        "protocol_gateway",
    }
    assert required <= set(registry["component_ids"]), registry
    components = {item["component_id"]: item for item in registry["components"]}
    for component_id in required:
        item = components[component_id]
        assert item["status"] == "complete", item
        assert item["functions"], item
        assert all(fn["present"] for fn in item["functions"]), item
        assert item["stores"], item
        assert all(store["configured"] for store in item["stores"]), item
        assert item["memory_write_policy"] == "candidate_only", item
    assert registry["principles"]["single_orchestrator"] is True, registry
    assert registry["principles"]["unstructured_swarm"] is False, registry
    assert os.path.exists(a.AGENT_GOVERNANCE_PATH), a.AGENT_GOVERNANCE_PATH


def assert_baseline_report_schema(report: dict) -> None:
    assert report["schema_version"] == "architecture.baseline_report.v1", report
    assert report["baseline_refs"], report
    assert all(item.get("exists") for item in report["baseline_refs"]), report["baseline_refs"]
    assert report["report_path"] == a.AGENT_BASELINE_REPORT_PATH, report
    summary = report["summary"]
    assert summary["items"] >= len(BASELINE_ITEM_IDS), summary
    assert summary["complete"] + summary["partial"] + summary["missing"] == summary["items"], summary
    assert summary["partial"] == 0 and summary["missing"] == 0, summary
    assert 0.0 <= summary["completion_ratio"] <= 1.0, summary
    item_ids = {item.get("id") for item in report["items"]}
    missing_ids = BASELINE_ITEM_IDS - item_ids
    assert not missing_ids, f"baseline report missing {missing_ids}: {item_ids}"
    for item in report["items"]:
        assert item["status"] in {"complete", "partial", "missing"}, item
        assert item["requirement"], item
        assert isinstance(item["evidence"], list), item
        assert isinstance(item["missing_evidence"], list), item
        assert isinstance(item["gaps"], list), item
    assert isinstance(report["remaining_gaps"], list), report
    assert report["next_actions"], report
    assert os.path.exists(a.AGENT_BASELINE_REPORT_PATH), a.AGENT_BASELINE_REPORT_PATH
    with open(a.AGENT_BASELINE_REPORT_PATH, encoding="utf-8") as fh:
        saved = json.load(fh)
    assert saved["schema_version"] == report["schema_version"], saved


def assert_agent_card_schema(card: dict) -> None:
    assert card["schema_version"] == "a2a.agent_card.v1", card
    assert card["agent_id"], card
    assert card["endpoint"]["transport"] == "internal-agent-mail", card
    assert card["capabilities"]["artifact_refs"] is True, card
    assert card["capabilities"]["human_approval"] is True, card
    assert card["auth"]["type"] == "local_runtime", card
    assert "text/plain" in card["input_modes"], card
    assert "artifact_refs" in card["output_modes"], card


def assert_a2a_task_schema(task: dict) -> None:
    assert task["schema_version"] == "a2a.task.v1", task
    assert task["id"], task
    assert task["contextId"] == "ga-tui", task
    assert task["status"]["state"], task
    assert isinstance(task["history"], list), task
    assert isinstance(task["artifacts"], list), task


def assert_a2a_message_schema(message: dict) -> None:
    assert message["schema_version"] == "a2a.message.v1", message
    assert message["messageId"], message
    assert message["contextId"] == "ga-tui", message
    assert message["role"] in {"agent", "user"}, message
    assert message["parts"], message


def assert_a2a_artifact_schema(artifact: dict) -> None:
    assert artifact["schema_version"] == "a2a.artifact.v1", artifact
    assert artifact["artifactId"], artifact
    assert artifact["contextId"] == "ga-tui", artifact
    assert artifact["parts"], artifact
    assert artifact["parts"][0]["file"]["uri"].startswith("artifact://"), artifact


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
    assert isinstance(data, dict), data
    return data


def post_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
    assert isinstance(data, dict), data
    return data


def run_gateway_server_checks() -> None:
    server = a.make_gateway_http_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    base = f"http://{host}:{port}"
    try:
        health = get_json(f"{base}/health")
        assert health["ok"] is True, health
        assert health["service"]["schema_version"] == "agentgateway.service.v1", health
        gateway = get_json(f"{base}/gateway")
        assert_gateway_schema(gateway)
        a2a = get_json(f"{base}/a2a")
        assert a2a["schema_version"] == "a2a.gateway.v1", a2a
        mcp = get_json(f"{base}/mcp")
        assert mcp["schema_version"] == "mcp.gateway.v1", mcp
        resource = get_json(f"{base}/mcp/resource?uri=resource%3A%2F%2Fagent-mail%2Ftasks")
        assert resource["schema_version"] == "mcp.resource.contents.v1", resource
        query = post_json(f"{base}/a2a/tasks/query", {"task_id": "task_direct_schema"})
        assert query["schema_version"] == "a2a.query_response.v1", query
        with urllib.request.urlopen(f"{base}/a2a/events?once=1", timeout=5) as response:
            frame = response.read().decode("utf-8")
        assert "event:" in frame and "data:" in frame, frame
        subscription = post_json(
            f"{base}/a2a/push-subscriptions",
            {"endpoint": f"{base}/health", "event_types": ["gateway"]},
        )
        assert subscription["subscription"]["schema_version"] == "agentgateway.push_subscription.v1", subscription
        delivery = post_json(f"{base}/a2a/push-test", {"event": "gateway", "payload": {"check": True}})
        assert delivery["schema_version"] == "agentgateway.push_delivery_response.v1", delivery
        assert delivery["deliveries"], delivery
        assert delivery["deliveries"][-1]["status"] == "delivered", delivery
        assert a.read_jsonl(a.AGENT_GATEWAY_PUSH_DELIVERIES_PATH), a.AGENT_GATEWAY_PUSH_DELIVERIES_PATH
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def run_gateway_daemon_checks() -> None:
    status = a.start_gateway_daemon("127.0.0.1", 0, extra_env={"GA_TUI_HARNESS_DIR": a.AGENT_HARNESS_DIR})
    try:
        assert status["schema_version"] == "agentgateway.daemon.v1", status
        assert status["status"] == "running", status
        assert status["alive"] is True, status
        assert int(status["port"]) > 0, status
        health = get_json(f"{status['base_url']}/health")
        assert health["ok"] is True, health
        assert os.path.exists(a.AGENT_GATEWAY_DAEMON_STATUS_PATH), a.AGENT_GATEWAY_DAEMON_STATUS_PATH
        assert os.path.exists(a.AGENT_GATEWAY_DAEMON_PID_PATH), a.AGENT_GATEWAY_DAEMON_PID_PATH
    finally:
        stopped = a.stop_gateway_daemon()
    assert stopped["status"] == "stopped", stopped
    assert stopped["alive"] is False, stopped


def assert_context_pack_schema(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        pack = json.load(fh)
    for key in ("layers", "memory_pack", "task_brief", "source_policy", "context_policy"):
        assert key in pack, f"context pack missing {key}: {pack}"
    expected_layers = {
        "L0_system_constitution",
        "L1_user_profile",
        "L2_project_memory",
        "L3_task_brief",
        "L4_plan_ledger",
        "L5_progress_ledger",
        "L6_working_notes",
        "L7_artifacts",
        "L8_raw_trace",
    }
    assert expected_layers <= set(pack["layers"]), pack["layers"]
    assert pack["context_policy"]["artifact_reference_only"] is True, pack["context_policy"]
    assert pack["context_policy"]["include_raw_logs"] is False, pack["context_policy"]
    assert pack["layers"]["L8_raw_trace"]["include_raw_logs"] is False, pack["layers"]["L8_raw_trace"]
    assert pack["memory_pack"]["included"], pack["memory_pack"]
    assert pack["memory_pack"]["excluded"], pack["memory_pack"]
    assert pack["task_brief"]["non_goals"], pack["task_brief"]
    assert pack["task_brief"]["success_criteria"], pack["task_brief"]
    assert pack["layers"]["L0_system_constitution"]["items"], pack["layers"]["L0_system_constitution"]
    assert pack["layers"]["L1_user_profile"]["included"] is True, pack["layers"]["L1_user_profile"]
    assert pack["shared_user_profile"]["path"] in pack["layers"]["L1_user_profile"]["refs"], pack["layers"]["L1_user_profile"]
    assert any(row.get("scope") == "user.shared-profile" for row in pack["memory_pack"]["included"]), pack["memory_pack"]
    assert pack["layers"]["L3_task_brief"]["source_policy"]["allowed_sources"], pack["layers"]["L3_task_brief"]
    assert "memory_pack_ref" in pack["layers"]["L6_working_notes"], pack["layers"]["L6_working_notes"]
    assert isinstance(pack["layers"]["L7_artifacts"]["items"], list), pack["layers"]["L7_artifacts"]
    assert pack["source_policy"]["allowed_sources"], pack["source_policy"]
    prompt = a.format_context_pack_for_prompt(pack)
    assert "Source policy:" in prompt, prompt
    assert "Memory hydration pack:" in prompt, prompt
    assert "Recent artifact refs:" in prompt, prompt
    return pack


def assert_restored_process_group_folds_intermediate_speech() -> None:
    restored = (
        "**LLM Running (Turn 1) ...**\n"
        "<summary>检查已有子代理</summary>\n"
        "第一段主代理说明：先检查已有子代理。\n\n"
        "🛠️ Tool: `webscan` 📥 args:\n"
        "````text\n"
        "{\"query\":\"hidden lookup\"}\n"
        "````\n"
        "`````\n"
        "hidden tool output one\n"
        "`````\n\n"
        "**LLM Running (Turn 2) ...**\n"
        "<summary>派发任务并等待回复</summary>\n"
        "第二段主代理说明：现在派发任务并等待回复。\n\n"
        "🛠️ Tool: `fileread` 📥 args:\n"
        "````text\n"
        "{\"path\":\"hidden.txt\"}\n"
        "````\n"
        "`````\n"
        "hidden tool output two\n"
        "`````\n\n"
        "**LLM Running (Turn 3) ...**\n"
        "最终主代理总结：两个步骤都已处理。\n"
    )
    rendered = a.render_assistant_text(restored, done=True, fold_process=True, message_index=2)
    assert "过程组 G3" in rendered, rendered
    assert "检查已有子代理 / 派发任务并等待回复" in rendered, rendered
    assert "第一段主代理说明：先检查已有子代理。" not in rendered, rendered
    assert "第二段主代理说明：现在派发任务并等待回复。" not in rendered, rendered
    assert "最终主代理总结：两个步骤都已处理。" in rendered, rendered
    assert rendered.count("最终主代理总结：两个步骤都已处理。") == 1, rendered
    assert "· 过程 Turn 1" not in rendered, rendered
    assert "· 过程 Turn 2" not in rendered, rendered
    assert "hidden lookup" not in rendered, rendered
    assert "hidden.txt" not in rendered, rendered
    assert "hidden tool output" not in rendered, rendered

    expanded = a.render_assistant_text(restored, done=True, fold_process=True, message_index=2, expanded_groups={"G3"})
    assert "▸ 过程 G3T1 Turn 1" in expanded, expanded
    assert "▸ 过程 G3T2 Turn 2" in expanded, expanded
    assert "▸ 过程 G3T3 Turn 3" in expanded, expanded


def assert_mixed_omp_process_turns_fold_into_single_group() -> None:
    restored = (
        "**LLM Running (Turn 1) ...**\n"
        "<summary>The user wants market research.</summary>\n"
        "<thinking>\nplan research\n</thinking>\n"
        "好，我来从整个链路做调研。\n\n"
        "**LLM Running (Turn 4) ...**\n"
        "<summary>Let me start researching each area.</summary>\n"
        "先调研市场和竞品。\n\n"
        "**LLM Running (Turn 5) ...**\n"
        "<summary>调用 OMP 工具: web_search</summary>\n"
        "🛠️ Tool: `web_search` 📥 args:\n"
        "````text\n"
        "{\"query\":\"photo homework solver market\"}\n"
        "````\n"
        "`````\n"
        "search noise\n"
        "`````\n\n"
        "**LLM Running (Turn 41) ...**\n"
        "<summary>Now compile the comprehensive report.</summary>\n"
        "# 完整链路报告\n\n这是最终用户可见报告。\n"
    )
    rendered = a.render_assistant_text(restored, done=True, fold_process=True, message_index=6)
    assert "过程组 G7" in rendered, rendered
    assert "完整链路报告" in rendered, rendered
    assert "这是最终用户可见报告。" in rendered, rendered
    assert "· 过程 Turn 1" not in rendered, rendered
    assert "· 过程 Turn 4" not in rendered, rendered
    assert "· 过程 Turn 41" not in rendered, rendered
    assert "好，我来从整个链路做调研。" not in rendered, rendered
    assert "先调研市场和竞品。" not in rendered, rendered
    assert "search noise" not in rendered, rendered


def assert_process_group_keeps_substantive_reply_before_housekeeping() -> None:
    restored = (
        "**LLM Running (Turn 11) ...**\n"
        "<summary>调用 OMP 工具: irc</summary>\n"
        "🛠️ Tool: `irc` 📥 args:\n"
        "````text\n"
        '{"args":{"await":true,"message":"hello","op":"send","to":"DemoBeta"}}\n'
        "````\n\n"
        "**LLM Running (Turn 12) ...**\n"
        "<summary>OMP 工具结果: irc</summary>\n"
        "🛠️ Tool: `irc` 📥 args:\n"
        "````text\n"
        '{"status":"ok","toolCallId":"call_beta"}\n'
        "````\n"
        "`````\n"
        '{"content":[{"text":"Delivered to 1 peer(s):\\n- DemoBeta: injected\\n\\nReply from DemoBeta:\\nHello Main! DemoBeta here, I can hear you loud and clear.","type":"text"}],"details":{"waited":{"from":"DemoBeta","body":"Hello Main! DemoBeta here, I can hear you loud and clear."}}}\n'
        "`````\n\n"
        "**LLM Running (Turn 13) ...**\n"
        "<summary>OMP 工具结果: irc</summary>\n"
        "🛠️ Tool: `irc` 📥 args:\n"
        "````text\n"
        '{"status":"ok","toolCallId":"call_alpha"}\n'
        "````\n"
        "`````\n"
        '{"content":[{"text":"Delivered to 1 peer(s):\\n- DemoAlpha: injected\\n\\nReply from DemoAlpha:\\n你好 Main！我是 DemoAlpha，能听到你说话。","type":"text"}],"details":{"waited":{"from":"DemoAlpha","body":"你好 Main！我是 DemoAlpha，能听到你说话。"}}}\n'
        "`````\n\n"
        "## 能和代理说话吗 — 结论\n\n"
        "能。刚才通过 IRC 分别向 DemoAlpha 和 DemoBeta 发了消息，并收到了回复。"
        "这个结论应该保留在过程组外面，而不是被后续收尾思考覆盖。\n\n"
        "**LLM Running (Turn 14) ...**\n"
        "<summary>Both demo agents have completed. Nothing further to do.</summary>\n"
        "<thinking>Both demo agents have completed. Nothing further to do.</thinking>\n"
        "两个子 agent 都已完成并关闭。IRC 多 agent 通信功能验证通过。\n"
    )
    rendered = a.render_assistant_text(restored, done=True, fold_process=True, message_index=12)
    assert "过程组 G13" in rendered, rendered
    assert "能和代理说话吗" in rendered, rendered
    assert "这个结论应该保留" in rendered, rendered
    assert "IRC 回复" in rendered, rendered
    assert "DemoBeta: Hello Main! DemoBeta here" in rendered, rendered
    assert "DemoAlpha: 你好 Main！我是 DemoAlpha" in rendered, rendered
    assert "Delivered to 1 peer" not in rendered, rendered
    assert "toolCallId" not in rendered, rendered


def assert_process_group_keeps_enumeration_before_summary_housekeeping() -> None:
    numbers = ", ".join(str(index) for index in range(1, 101))
    restored = (
        "**LLM Running (Turn 1) ...**\n"
        "<summary>The user wants me to count from 1 to 100.</summary>\n"
        "<thinking>Plan the simple counting task.</thinking>\n\n"
        "**LLM Running (Turn 2) ...**\n"
        "<summary>调用 OMP 工具: todo</summary>\n"
        "🛠️ Tool: `todo` 📥 args:\n"
        "````text\n"
        '{"args":{"ops":[{"op":"init"}]}}\n'
        "````\n\n"
        "**LLM Running (Turn 3) ...**\n"
        "<summary>OMP 工具结果: todo</summary>\n"
        "🛠️ Tool: `todo` 📥 args:\n"
        "````text\n"
        '{"status":"ok","toolCallId":"call_todo"}\n'
        "````\n"
        "`````\n"
        '{"content":[{"text":"Remaining items: count","type":"text"}]}\n'
        "`````\n\n"
        "**LLM Running (Turn 4) ...**\n"
        "<summary>Now I'll count from 1 to 100.</summary>\n"
        f"{numbers}\n\n"
        "**LLM Running (Turn 5) ...**\n"
        "<summary>调用 OMP 工具: todo</summary>\n"
        "🛠️ Tool: `todo` 📥 args:\n"
        "````text\n"
        '{"args":{"ops":[{"op":"done"}]}}\n'
        "````\n\n"
        "**LLM Running (Turn 6) ...**\n"
        "<summary>OMP 工具结果: todo</summary>\n"
        "🛠️ Tool: `todo` 📥 args:\n"
        "````text\n"
        '{"status":"ok","toolCallId":"call_done"}\n'
        "````\n"
        "`````\n"
        '{"content":[{"text":"Remaining items: none","type":"text"}]}\n'
        "`````\n\n"
        "**LLM Running (Turn 7) ...**\n"
        "<summary>Task complete.</summary>\n"
        "**Summary** | 从 1 到 100 已完整数完，共计 100 个自然数，无遗漏。任务完成。\n\n"
        "**Confidence**: 1.0 - 枚举结果可直接验证，无歧义。"
    )
    rendered = a.render_assistant_text(restored, done=True, fold_process=True, message_index=4)
    assert "过程组 G5" in rendered, rendered
    assert numbers in rendered, rendered
    assert "Summary | 从 1 到 100 已完整数完" not in rendered, rendered
    assert "toolCallId" not in rendered, rendered
    assert "Remaining items" not in rendered, rendered


def assert_process_detail_line_not_swallowed_by_code_fence() -> None:
    restored = (
        "**LLM Running (Turn 1) ...**\n"
        "<summary>运行代码块示例</summary>\n"
        "主代理给出一段带代码块的说明：\n"
        "```python\n"
        "print('visible example')\n\n"
        "🛠️ Tool: `code_run` 📥 args:\n"
        "````text\n"
        "{\"cmd\":\"hidden\"}\n"
        "````\n"
    )
    rendered = a.render_assistant_text(restored, done=True, fold_process=True, message_index=9)
    assert "▸ 细节 Turn 1: 运行代码块示例" in rendered, rendered
    render_lines = a.markdown_blocks(rendered, 100)
    flattened = "\n".join(line.text for line in render_lines)
    assert "│ ▸ 细节 Turn 1" not in flattened, flattened
    assert "▸ 细节 Turn 1: 运行代码块示例" in flattened, flattened


def assert_single_search_turn_keeps_final_reply_visible() -> None:
    restored = (
        "**LLM Running (Turn 1) ...**\n"
        "<summary>查询 GenericAgent TUI 能力</summary>\n"
        "🛠️ Tool: `web_search` 📥 args:\n"
        "````text\n"
        "{\"query\":\"GenericAgent TUI 能力\"}\n"
        "````\n"
        "`````\n"
        "search results noise\n"
        "`````\n"
        "[Info] Final response to user.\n"
        "在这个 TUI 里，我可以帮你管理会话、拆任务、调度子 Agent。\n"
    )
    rendered = a.render_assistant_text(restored, done=True, fold_process=True, message_index=11)
    assert "在这个 TUI 里，我可以帮你管理会话、拆任务、调度子 Agent。" in rendered, rendered
    assert rendered.index("在这个 TUI 里") < rendered.index("▸ 过程 Turn 1"), rendered
    assert "▸ 过程 Turn 1: 查询 GenericAgent TUI 能力" in rendered, rendered
    assert "搜索/浏览输出已折叠" not in rendered, rendered
    assert "<summary>" not in rendered, rendered
    assert "search results noise" not in rendered, rendered
    assert "{\"query\"" not in rendered, rendered


def assert_ask_user_tool_use_input_payload_visible() -> None:
    restored = (
        "**LLM Running (Turn 76) ...**\n"
        "[{'type': 'text', 'text': '## 逆向进展总结'}, "
        "{'type': 'tool_result', 'input': {'path': 'noise-only.txt'}}, "
        "{'type': 'tool_use', 'id': 'call_00', 'name': 'ask_user', "
        "'input': {'question': '我已经破解了APK的字符串混淆，但目前卡在config.txt解密上。\\n\\n"
        "请问你想让我继续哪个方向？', "
        "'candidates': ['继续破解config.txt', '分析plugin.apk中的代码', '告诉我CTF具体目标']}}]"
    )
    payload = a.extract_interaction_request(restored)
    assert payload, restored
    assert payload["tool"] == "ask_user", payload
    assert "config.txt解密" in payload["question"], payload
    assert payload["candidates"] == ["继续破解config.txt", "分析plugin.apk中的代码", "告诉我CTF具体目标"], payload
    assert a.process_tools(restored) == ["ask_user"], a.process_tools(restored)
    rendered = a.render_assistant_text(restored, done=False, fold_process=True, message_index=75)
    assert "需要你输入 · ask_user" in rendered, rendered
    assert "config.txt解密" in rendered, rendered
    assert "继续破解config.txt" in rendered, rendered
    assert "工具正在等待你的输入。" not in rendered, rendered


def assert_ask_user_multiline_tool_args_payload_visible() -> None:
    restored = (
        "**LLM Running (Turn 2) ...**\n"
        "Lint 已完成。现在让我确认 proposal 清理的范围。\n\n"
        "🛠️ Tool: `ask_user`  📥 args:\n"
        "````text\n"
        "{\n"
        '  "question": "✅ **Lint 完成**（报告保存到 Personal/outputs/reports/wiki-lint-20260529-220533.md）\n'
        "\n"
        "关于 **P0: Proposal 清理**，需要你决定清理策略：\n"
        "\n"
        "`Personal/outputs/proposals/` 下有 **1567 个文件**，其中：\n"
        "- **1548 个 workflow harvester 自动快照**\n"
        "\n"
        '你的选择?",\n'
        '  "candidates": [\n'
        '    "A) 激进清理：删全部1548个workflow快照",\n'
        '    "B) 保守清理：只删5/3当天的重复快照",\n'
        '    "C) 让我自己看看再决定"\n'
        "  ]\n"
        "}\n"
        "````\n"
        "`````\n"
        "Waiting for your answer ...\n"
        "`````\n"
    )
    payload = a.extract_interaction_request(restored)
    assert payload, restored
    assert "P0: Proposal 清理" in payload["question"], payload
    assert payload["candidates"][0].startswith("A) 激进清理"), payload
    rendered = a.render_assistant_text(restored, done=False, fold_process=True, message_index=76)
    assert "P0: Proposal 清理" in rendered, rendered
    assert "删全部1548个workflow快照" in rendered, rendered
    assert "工具正在等待你的输入。" not in rendered, rendered


def assert_aux_mouse_buttons_do_not_start_selection() -> None:
    width = 120
    sidebar_w = a.left_sidebar_width(width)
    rightbar_w = a.rightbar_width_for_terminal(width)
    state = a.State(agent=None)
    state.line_cache = [a.RenderLine("selectable text")]
    state.main_x0 = sidebar_w
    state.main_width = width - sidebar_w - rightbar_w
    state.body_top = 1
    state.body_height = 3
    mx = state.main_x0 + 2
    my = state.body_top

    a.handle_mouse(state, mx, my, a.curses.BUTTON1_PRESSED, width)
    assert state.selection_active is True, state

    a.clear_selection(state)
    a.handle_mouse(state, mx, my, a.curses.BUTTON1_PRESSED | a.curses.BUTTON2_PRESSED, width)
    assert state.selection_active is False, state

    a.handle_mouse(state, mx, my, a.curses.BUTTON1_PRESSED | (1 << 30), width)
    assert state.selection_active is False, state


def assert_subagent_result_context_update_from_notice() -> None:
    notice = a.format_subagent_result_notice_parts(
        "恢复代理",
        "agent-restore",
        "task_restore",
        "artifact://artifacts/subagent-results/restore.md",
        "恢复后的当前会话回复。\n\n**Confidence:** 高",
    )
    context = a.subagent_result_context_update_from_notice(
        notice,
        session_key_value="model_responses_restore.txt",
    )
    assert "Subagent result available in current session context" in context, context
    assert "model_responses_restore.txt" in context, context
    assert "恢复代理 (agent-restore)" in context, context
    assert "task_restore" in context, context
    assert "artifact://artifacts/subagent-results/restore.md" in context, context
    assert "恢复后的当前会话回复。" in context, context
    assert "confidence: 高" in context, context
    many = [
        a.Message(
            "system",
            a.format_subagent_result_notice_parts(
                f"恢复代理{i}",
                f"agent-restore-{i}",
                f"task_restore_{i}",
                f"artifact://artifacts/subagent-results/restore-{i}.md",
                f"恢复回复 {i}",
            ),
        )
        for i in range(a.SUBAGENT_CONTEXT_UPDATE_LIMIT + 3)
    ]
    bounded = a.subagent_context_updates_from_messages(many, "/tmp/model_responses_restore.txt")
    assert "恢复代理0" not in bounded, bounded
    assert f"恢复代理{a.SUBAGENT_CONTEXT_UPDATE_LIMIT + 2}" in bounded, bounded


def assert_live_subagent_result_reaches_main_context() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_subagent_context_")
    retarget_harness(root)
    install_fake_agent_runtime()
    state = a.State(agent=ContextFakeAgent())
    state.running = True
    sub = a.create_subagent(state, "Context Agent", role="researcher")
    sub.agent = BlockingFakeAgent()
    started = a.start_subagent_task(state, sub, "report current state", source="user")
    assert started.startswith("已启动子 agent"), started
    assert sub.active_task_id is not None
    assert sub.active_bus_task_id
    state.ui_queue.put((
        "sub_stream",
        sub.agent_id,
        sub.active_task_id,
        "当前会话子代理已经回复。\n\n**Confidence:** 高",
        True,
    ))
    a.process_ui_queue(state)
    prompt = a.agent_text_with_pending_bus(state.agent, "如何了")
    assert "[Agent Bus Updates]" in prompt, prompt
    assert "Subagent result available in current session context" in prompt, prompt
    assert "Context Agent" in prompt, prompt
    assert "当前会话子代理已经回复。" in prompt, prompt
    assert "artifact://artifacts/subagent-results/" in prompt, prompt
    assert "do not search historical session logs" in prompt, prompt


def assert_subagent_runtime_errors_fail_and_release_model_switch() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_subagent_runtime_error_")
    retarget_harness(root)
    install_fake_agent_runtime()
    state = a.State(agent=ContextFakeAgent())
    state.running = True

    omp_error = "[Oh My Pi] 429: 429 该模型当前访问量过大，请您稍后再试"
    sub = a.create_subagent(state, "Runtime Error Agent", role="researcher")
    sub.agent = SequencedFakeAgent([omp_error])
    started = a.start_subagent_task(state, sub, "read local data", source="user")
    assert started.startswith("已启动子 agent"), started
    drain_ui(state)

    assert sub.status == "idle", sub.status
    assert sub.active_task_id is None, sub.active_task_id
    assert sub.active_bus_task_id == "", sub.active_bus_task_id
    assert "子 agent 失败" in state.last_error and "429" in state.last_error, state.last_error
    task_rows = [row for row in a.read_jsonl(a.AGENT_TASK_LEDGER_PATH) if row.get("assigned_agent") == sub.agent_id]
    assert [row.get("status") for row in task_rows] == ["working", "failed"], task_rows
    failed_task = task_rows[-1]
    assert_task_schema(failed_task, status="failed")
    assert "429" in failed_task.get("error", ""), failed_task
    assert not any(row.get("status") == "completed" for row in task_rows), task_rows
    mail_rows = [row for row in a.read_jsonl(a.AGENT_MAIL_PATH) if row.get("task_id") == failed_task["task_id"] and row.get("intent") == "result"]
    assert mail_rows and mail_rows[-1]["status"] == "failed", mail_rows
    assert_mail_schema(mail_rows[-1], intent="result")
    assert "429" in (mail_rows[-1].get("payload") or {}).get("error", ""), mail_rows[-1]
    checkpoints = [row for row in a.read_jsonl(a.AGENT_CHECKPOINT_INDEX_PATH) if row.get("task_id") == failed_task["task_id"]]
    assert any(row.get("status") == "failed" and row.get("reason") == "subagent_runtime_failed" for row in checkpoints), checkpoints
    traces = [row for row in a.read_jsonl(a.AGENT_TRACES_PATH) if row.get("task_id") == failed_task["task_id"]]
    assert any(row.get("event") == "runtime_failed" and row.get("status") == "failed" for row in traces), traces
    assert not a.read_jsonl(a.AGENT_EVALS_PATH), a.read_jsonl(a.AGENT_EVALS_PATH)
    artifacts = [row for row in a.read_jsonl(a.AGENT_ARTIFACT_INDEX_PATH) if row.get("source_task_id") == failed_task["task_id"]]
    assert any(row.get("type") == "subagent-results" for row in artifacts), artifacts
    assert any(msg.role == "system" and "子 agent 失败" in msg.content and "429" in msg.content for msg in state.messages), state.messages

    chat_sub = a.create_subagent(state, "Runtime Error Chat Agent", role="researcher")
    chat_agent = BlockingAbortFakeAgent()
    chat_sub.agent = chat_agent
    chat_started = a.start_subagent_chat(state, chat_sub, "first chat", source="subagent_chat")
    assert chat_started.startswith("已发送给子 agent"), chat_started
    first_chat_task_id = chat_sub.active_task_id
    queued = a.start_subagent_chat(state, chat_sub, "queued after rpc failure", source="subagent_chat")
    assert "已排队" in queued, queued
    state.ui_queue.put(("sub_chat_stream", chat_sub.agent_id, first_chat_task_id, "[Oh My Pi] RPC prompt failed: Agent is already processing.", True))
    assert a.process_ui_queue(state) is True
    assert chat_sub.status == "running", chat_sub.status
    assert chat_sub.active_task_id is not None and chat_sub.active_task_id != first_chat_task_id, chat_sub.active_task_id
    assert len(chat_agent.prompts) == 2, chat_agent.prompts
    assert "queued after rpc failure" in chat_agent.prompts[-1][0], chat_agent.prompts[-1]

    model_root = tempfile.mkdtemp(prefix="ga_tui_subagent_model_block_")
    retarget_harness(model_root)
    model_state = a.State(agent=ContextFakeAgent())
    model_state.running = True
    model_sub = a.create_subagent(model_state, "Model Block Agent", role="researcher")
    model_sub.default_model = "beta"
    old_apply = a.apply_subagent_default_model
    try:
        a.apply_subagent_default_model = lambda _state, _sub: (False, "missing runtime model")
        blocked = a.start_subagent_task(model_state, model_sub, "should not run on old model", source="user")
        assert "默认模型未应用，已阻止启动" in blocked, blocked
        assert model_sub.status == "idle", model_sub.status
        assert model_sub.agent is not None
        assert getattr(model_sub.agent, "prompts", []) == [], getattr(model_sub.agent, "prompts", [])
        assert not a.read_jsonl(a.AGENT_TASK_LEDGER_PATH), a.read_jsonl(a.AGENT_TASK_LEDGER_PATH)
    finally:
        a.apply_subagent_default_model = old_apply


def assert_selected_subagent_chat_is_direct_session() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_subagent_chat_")
    retarget_harness(root)
    state = a.State(agent=ContextFakeAgent())
    state.running = True
    blocking_sub = a.create_subagent(state, "Blocking Chat Agent", role="researcher")
    blocking_agent = BlockingAbortFakeAgent()
    blocking_sub.agent = blocking_agent
    state.selected_session = blocking_sub.agent_id

    a.submit(state, "persist before first token")
    assert blocking_agent.prompts, "direct chat prompt was not sent"
    assert blocking_agent.prompts[0][1] == f"subagent-chat:{blocking_sub.agent_id}", blocking_agent.prompts
    assert "[GA TUI Context Pack]" in blocking_agent.prompts[0][0], blocking_agent.prompts[0][0]
    assert "Memory hydration pack:" in blocking_agent.prompts[0][0], blocking_agent.prompts[0][0]
    assert "[GA TUI Direct SubAgent Chat]" in blocking_agent.prompts[0][0], blocking_agent.prompts[0][0]
    assert "name: Blocking Chat Agent" in blocking_agent.prompts[0][0], blocking_agent.prompts[0][0]
    assert "context_pack_ref:" in blocking_agent.prompts[0][0], blocking_agent.prompts[0][0]
    assert "do not introduce yourself as the main GenericAgent" in blocking_agent.prompts[0][0], blocking_agent.prompts[0][0]
    assert "persist before first token" in blocking_agent.prompts[0][0], blocking_agent.prompts[0][0]
    blocking_entries = a.subagent_chat_session_entries(state, blocking_sub)
    assert blocking_entries and blocking_entries[0]["message_count"] == 2, blocking_entries
    reloaded_blocking = a.State(agent=ContextFakeAgent())
    reloaded_blocking.running = True
    assert a.load_subagents(reloaded_blocking) is True
    reloaded_blocking_sub = reloaded_blocking.subagents.get(blocking_sub.agent_id)
    assert reloaded_blocking_sub is not None
    assert [msg.role for msg in reloaded_blocking_sub.messages] == ["user", "assistant"], reloaded_blocking_sub.messages
    assert reloaded_blocking_sub.messages[0].content == "persist before first token", reloaded_blocking_sub.messages
    assert reloaded_blocking_sub.messages[-1].done is True, reloaded_blocking_sub.messages[-1]
    assert "输出中断" in reloaded_blocking_sub.messages[-1].content, reloaded_blocking_sub.messages[-1]

    sub = a.create_subagent(state, "Chat Agent", role="researcher")
    a.append_text_file(a.subagent_memory_file(sub), "\n## Seed [test]\nChat Agent memory marker\n")
    chat_agent = SequencedFakeAgent(["direct reply\n<ga-subagent-memory>\n- direct chat stable memory\n</ga-subagent-memory>"])
    sub.agent = chat_agent
    state.selected_session = sub.agent_id

    a.submit(state, "hello direct")
    drain_ui(state)

    assert len(chat_agent.prompts) == 1, chat_agent.prompts
    assert chat_agent.prompts[0][1] == f"subagent-chat:{sub.agent_id}", chat_agent.prompts
    assert "[GA TUI Context Pack]" in chat_agent.prompts[0][0], chat_agent.prompts[0][0]
    assert "Memory hydration pack:" in chat_agent.prompts[0][0], chat_agent.prompts[0][0]
    assert "Chat Agent memory marker" in chat_agent.prompts[0][0], chat_agent.prompts[0][0]
    assert "[GA TUI Direct SubAgent Chat]" in chat_agent.prompts[0][0], chat_agent.prompts[0][0]
    assert "name: Chat Agent" in chat_agent.prompts[0][0], chat_agent.prompts[0][0]
    assert "Prefer this subagent's own profile, memory, chat session, and context pack" in chat_agent.prompts[0][0], chat_agent.prompts[0][0]
    assert "hello direct" in chat_agent.prompts[0][0], chat_agent.prompts[0][0]
    assert [msg.role for msg in sub.messages] == ["user", "assistant", "system"], sub.messages
    assert sub.messages[0].content == "hello direct", sub.messages
    assert sub.messages[1].content == "direct reply", sub.messages
    memory_request = latest_approval(approval_type="memory_write_request")
    assert memory_request["payload"]["subagent_id"] == sub.agent_id, memory_request
    assert "direct chat stable memory" in memory_request["payload"]["memory"], memory_request
    assert memory_request["payload"]["memory_candidate"]["evidence_refs"], memory_request
    assert any("等待审批" in msg.content and memory_request["approval_id"] in msg.content and "direct chat stable memory" in msg.content for msg in sub.messages if msg.role == "system"), sub.messages
    normal_approval_items = a.approval_panel_items(show_all=False, state=state)
    assert any(item.key == memory_request["approval_id"] for item in normal_approval_items), normal_approval_items
    normal_memory_approval = next(item for item in normal_approval_items if item.key == memory_request["approval_id"])
    assert "Memory Candidate:" in normal_memory_approval.detail, normal_memory_approval.detail
    assert "direct chat stable memory" in normal_memory_approval.detail, normal_memory_approval.detail
    assert a.is_approval_interaction(state.pending_interaction), state.pending_interaction
    assert state.pending_interaction["approval_id"] == memory_request["approval_id"], state.pending_interaction
    assert state.pending_interaction["candidates"][0].startswith("批准"), state.pending_interaction
    assert "将写入的记忆" in state.pending_interaction["question"], state.pending_interaction
    assert "direct chat stable memory" in state.pending_interaction["question"], state.pending_interaction
    assert "direct chat stable memory" in a.render_interaction_card(state.pending_interaction), state.pending_interaction
    assert a.current_interaction_payload(state) is state.pending_interaction
    assert a.move_interaction_selection(state, 1)
    assert state.pending_interaction["_selection"] == 1, state.pending_interaction
    state.pending_interaction["_selection"] = 0
    a.submit(state, "")
    assert state.pending_interaction is None, state.pending_interaction
    assert "已批准并执行" in state.messages[-1].content, state.messages[-1]
    assert "direct chat stable memory" in a.read_text_file(a.subagent_memory_path(sub.agent_id), "")
    assert sub.status == "idle", sub.status
    assert not a.read_jsonl(a.AGENT_TASK_LEDGER_PATH), a.read_jsonl(a.AGENT_TASK_LEDGER_PATH)
    mail_rows = a.read_jsonl(a.AGENT_MAIL_PATH)
    assert mail_rows and all(row.get("intent") in {"approval_request", "memory_candidate_curated", "approval_granted"} for row in mail_rows), mail_rows
    artifact_rows = a.read_jsonl(a.AGENT_ARTIFACT_INDEX_PATH)
    assert any(row.get("type") == "context_pack" for row in artifact_rows), artifact_rows
    assert not any(row.get("type") == "subagent-results" for row in artifact_rows), artifact_rows
    assert not any(msg.content.startswith("子 agent 回复") for msg in state.messages), state.messages
    session_entries = a.subagent_chat_session_entries(state, sub)
    assert session_entries, session_entries
    assert session_entries[0]["message_count"] == 3, session_entries[0]
    reloaded = a.State(agent=ContextFakeAgent())
    reloaded.running = True
    assert a.load_subagents(reloaded) is True
    reloaded_sub = reloaded.subagents.get(sub.agent_id)
    assert reloaded_sub is not None
    assert [msg.content for msg in reloaded_sub.messages[:2]] == ["hello direct", "direct reply"], reloaded_sub.messages
    reloaded.selected_session = reloaded_sub.agent_id
    header = a.top_bar_header(reloaded, timestamp=0)
    assert "子 agent: Chat Agent" in header, header
    rendered_lines = a.message_lines_cached(reloaded, 80)
    assert any(line.text.startswith("AI:") for line in rendered_lines), [line.text for line in rendered_lines]
    assert not any(line.text.startswith("Chat Agent:") for line in rendered_lines), [line.text for line in rendered_lines]
    rows = a.subagent_sidebar_rows(reloaded, reloaded_sub, 44)
    assert any(row[0] == "subagent_session" and "hello direct" in row[2] for row in rows), rows
    previous_chat_session_id = reloaded_sub.chat_session_id
    reloaded_sub.status = "running"
    a.new_subagent_chat_session(reloaded, reloaded_sub)
    assert reloaded_sub.chat_session_id == previous_chat_session_id, reloaded_sub.chat_session_id
    assert "正在运行" in reloaded.last_error, reloaded.last_error
    reloaded_sub.status = "idle"
    a.new_subagent_chat_session(reloaded, reloaded_sub)
    assert reloaded_sub.chat_session_id != previous_chat_session_id, reloaded_sub.chat_session_id
    new_chat_session_id = reloaded_sub.chat_session_id
    assert reloaded_sub.messages == [], reloaded_sub.messages
    rows = a.subagent_sidebar_rows(reloaded, reloaded_sub, 44)
    assert any(row[0] == "subagent_session" and "hello direct" in row[2] for row in rows), rows
    session_entries = a.subagent_chat_session_entries(reloaded, reloaded_sub)
    assert any(entry["session_id"] == new_chat_session_id and entry["message_count"] == 0 for entry in session_entries), session_entries
    reloaded_empty = a.State(agent=ContextFakeAgent())
    reloaded_empty.running = True
    assert a.load_subagents(reloaded_empty) is True
    reloaded_empty_sub = reloaded_empty.subagents.get(sub.agent_id)
    assert reloaded_empty_sub is not None
    assert reloaded_empty_sub.chat_session_id == new_chat_session_id, reloaded_empty_sub.chat_session_id
    assert reloaded_empty_sub.messages == [], reloaded_empty_sub.messages
    reloaded.selected_session = reloaded_sub.agent_id
    screen = FakeDrawScreen()
    a.draw_rightbar(screen, reloaded, 18, 140)
    assert any(row[0] == "right_main" for row in reloaded.rightbar_rows), reloaded.rightbar_rows
    a.handle_mouse(reloaded, 139, 1, getattr(curses, "BUTTON1_CLICKED", 0), 140)
    assert a.selected_subagent(reloaded) is None
    assert reloaded.selected_session == a.MAIN_HOME_SESSION_KEY, reloaded.selected_session
    reloaded.selected_session = reloaded_sub.agent_id

    state.pending_interaction = {"tool": "ask_user", "question": "Main pending", "candidates": ["Main"]}
    chat_agent.responses.append("main pending ignored")
    a.submit(state, "still direct")
    drain_ui(state)
    assert "still direct" in chat_agent.prompts[-1][0], chat_agent.prompts[-1]
    assert "name: Chat Agent" in chat_agent.prompts[-1][0], chat_agent.prompts[-1]
    assert chat_agent.prompts[-1][1] == f"subagent-chat:{sub.agent_id}", chat_agent.prompts[-1]
    assert state.pending_interaction is not None, state.pending_interaction
    assert sub.messages[-1].content == "main pending ignored", sub.messages[-1]

    state.pending_interaction = {"tool": "ask_user", "question": "Main pending", "candidates": ["Main", "Other"], "_selection": 0}
    sub.pending_interaction = {"tool": "ask_user", "question": "Sub pending", "candidates": ["Fast", "Slow"], "_selection": 0}
    assert a.move_interaction_selection(state, 1)
    assert sub.pending_interaction["_selection"] == 1, sub.pending_interaction
    assert state.pending_interaction["_selection"] == 0, state.pending_interaction

    sub.pending_interaction = {
        "tool": "ask_user",
        "questions": [{"header": "Mode", "question": "Pick mode", "options": ["Fast"]}],
    }
    chat_agent.responses.append("answer reply")
    a.submit(state, "1")
    drain_ui(state)
    assert sub.pending_interaction is None, sub.pending_interaction
    assert state.pending_interaction is not None, state.pending_interaction
    assert "答案：Fast" in chat_agent.prompts[-1][0], chat_agent.prompts[-1]
    assert chat_agent.prompts[-1][1] == f"subagent-chat:{sub.agent_id}", chat_agent.prompts[-1]
    assert sub.messages[-1].content == "answer reply", sub.messages[-1]

    sub.agent = BlockingFakeAgent()
    state.follow_bottom = False
    state.dirty = False
    before_version = state.message_version
    started = a.start_subagent_chat(state, sub, "stream please", source="subagent_chat")
    assert started.startswith("已发送给子 agent"), started
    assert state.follow_bottom is True
    assert state.message_version > before_version
    assert a.display_status(state) == "running"
    stream_task_id = sub.active_task_id
    assert stream_task_id is not None

    state.follow_bottom = False
    before_version = state.message_version
    state.ui_queue.put(("sub_chat_stream", sub.agent_id, stream_task_id, "partial direct reply", False))
    assert a.process_ui_queue(state) is True
    assert state.follow_bottom is True
    assert state.message_version > before_version
    assert sub.messages[-1].content == "partial direct reply", sub.messages[-1]
    assert any("partial direct reply" in line.text for line in a.message_lines_cached(state, 80))

    state.follow_bottom = False
    state.ui_queue.put(("sub_chat_stream", sub.agent_id, stream_task_id, "final direct reply", True))
    assert a.process_ui_queue(state) is True
    assert state.follow_bottom is True
    assert sub.status == "idle", sub.status
    assert sub.active_task_id is None
    assert sub.messages[-1].content == "final direct reply", sub.messages[-1]

    sub.agent = BlockingAbortFakeAgent()
    started = a.start_subagent_chat(state, sub, "busy sub chat", source="subagent_chat")
    assert started.startswith("已发送给子 agent"), started
    sub_busy_task_id = sub.active_task_id
    assert sub.status == "running", sub.status
    a.submit(state, "queued direct chat")
    assert sub.chat_queue == ["queued direct chat"], sub.chat_queue
    assert not a.read_jsonl(a.AGENT_TASK_LEDGER_PATH), a.read_jsonl(a.AGENT_TASK_LEDGER_PATH)
    hint = a.queued_user_input_hint_lines(state, 100)
    assert hint and "queued direct chat" in hint[0][0], hint
    state.ui_queue.put(("sub_chat_stream", sub.agent_id, sub_busy_task_id, "busy done", True))
    assert a.process_ui_queue(state) is True
    assert sub.chat_queue == [], sub.chat_queue
    assert sub.status == "running", sub.status
    assert "queued direct chat" in sub.agent.prompts[-1][0], sub.agent.prompts
    assert "name: Chat Agent" in sub.agent.prompts[-1][0], sub.agent.prompts
    assert sub.agent.prompts[-1][1] == f"subagent-chat:{sub.agent_id}", sub.agent.prompts
    assert sub.messages[-2].role == "user"
    assert sub.messages[-2].content == "queued direct chat", sub.messages[-2]

    sub_second_task_id = sub.active_task_id
    a.set_input_text(state, "sub draft ctrl c")
    a.handle_key(None, state, "\x03")
    assert sub.agent.abort_count == 1, sub.agent.abort_count
    assert sub.status == "aborting", sub.status
    assert state.input_text == "", state.input_text
    assert sub.chat_queue == ["sub draft ctrl c"], sub.chat_queue
    assert sub.chat_queue_interrupt_requested is True
    state.ui_queue.put(("sub_chat_stream", sub.agent_id, sub_second_task_id, "sub aborted", True))
    assert a.process_ui_queue(state) is True
    assert "sub draft ctrl c" in sub.agent.prompts[-1][0], sub.agent.prompts
    assert "name: Chat Agent" in sub.agent.prompts[-1][0], sub.agent.prompts
    assert sub.agent.prompts[-1][1] == f"subagent-chat:{sub.agent_id}", sub.agent.prompts


def assert_running_main_input_is_queued_and_interruptible() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_queued_input_")
    retarget_harness(root)
    state = a.State(agent=BlockingAbortFakeAgent())
    state.running = True

    a.submit(state, "initial task")
    assert state.status == "running", state.status
    assert state.agent.prompts == [("initial task", "user")], state.agent.prompts
    first_target = state.active_stream_target
    first_task_id = state.active_task_id
    a.submit(state, "queued while running")
    assert state.queued_user_inputs == ["queued while running"], state.queued_user_inputs
    assert not any(msg.role == "system" and "当前任务还在运行" in msg.content for msg in state.messages), state.messages
    hint = a.queued_user_input_hint_lines(state, 100)
    assert hint and "等待这一步完成后发送" in hint[0][0], hint
    assert "queued while running" in hint[0][0], hint

    state.ui_queue.put(("stream", first_target, first_task_id, "initial done", True))
    assert a.process_ui_queue(state) is True
    assert state.status == "running", state.status
    assert state.agent.prompts[-1] == ("queued while running", "user:queued"), state.agent.prompts
    assert state.queued_user_inputs == [], state.queued_user_inputs
    assert [msg.role for msg in state.messages] == ["user", "assistant", "user", "assistant"], state.messages
    assert state.messages[2].content == "queued while running", state.messages[2]

    second_target = state.active_stream_target
    second_task_id = state.active_task_id
    a.handle_key(None, state, "\x03")
    assert state.agent.abort_count == 1, state.agent.abort_count
    assert state.status == "aborting", state.status
    a.submit(state, "after ctrl c")
    assert state.queued_user_inputs == ["after ctrl c"], state.queued_user_inputs
    assert state.queued_user_input_interrupt_requested is True
    hint = a.queued_user_input_hint_lines(state, 100)
    assert hint and "已请求打断" in hint[0][0], hint

    state.ui_queue.put(("stream", second_target, second_task_id, "aborted output", True))
    assert a.process_ui_queue(state) is True
    assert state.status == "running", state.status
    assert state.agent.prompts[-1] == ("after ctrl c", "user:queued_after_interrupt"), state.agent.prompts
    assert state.messages[-2].role == "user"
    assert state.messages[-2].content == "after ctrl c", state.messages[-2]

    third_target = state.active_stream_target
    third_task_id = state.active_task_id
    a.set_input_text(state, "draft ctrl c")
    a.handle_key(None, state, "\x03")
    assert state.agent.abort_count == 2, state.agent.abort_count
    assert state.input_text == "", state.input_text
    assert state.queued_user_inputs == ["draft ctrl c"], state.queued_user_inputs
    state.ui_queue.put(("stream", third_target, third_task_id, "third aborted", True))
    assert a.process_ui_queue(state) is True
    assert state.agent.prompts[-1] == ("draft ctrl c", "user:queued_after_interrupt"), state.agent.prompts


def assert_agent_create_respects_explicit_lifecycle_and_reuse_policy() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_agent_create_")
    retarget_harness(root)
    state = a.State(agent=ContextFakeAgent())
    state.running = True
    assert a.extract_tui_controls is cp.extract_tui_controls
    assert a.strip_tui_controls is cp.strip_tui_controls
    assert a.lifecycle_is_persistent is cp.lifecycle_is_persistent
    assert cp.extract_tui_controls.__module__ == "ga_tui.control_protocol"
    assert "curses" not in cp.__dict__
    existing = a.create_subagent(
        state,
        "Obsidiam知识库管家",
        "负责整理 Obsidiam 知识库、笔记索引和长期记忆候选。",
        role="memory_curator",
        persistent=True,
    )

    state.messages.append(a.Message("user", "你给我创建一个用来管理falsesocial的持久代理"))
    a.apply_tui_controls_from_text(
        state,
        ga_control(create_agent_action("FalseSocial 管理代理", persistent=True, profile="专门管理 falsesocial 的账号、内容和运维事项。")),
        source="agent",
    )
    falsesocial_agents = [sub for sub in state.subagents.values() if "falsesocial" in sub.agent_id]
    assert len(falsesocial_agents) == 1, [(sub.agent_id, sub.name) for sub in state.subagents.values()]
    assert falsesocial_agents[0].agent_id != existing.agent_id
    assert falsesocial_agents[0].persistent is True
    assert a.resolve_subagent(state, existing.agent_id) is existing

    state.messages.append(a.Message("user", "不不，单独弄一个管理falsesocial的持久代理，不要复用"))
    a.apply_tui_controls_from_text(
        state,
        "明白，单独新建，不引用已有代理。\n" + ga_control(create_agent_action("FalseSocial 管理代理", persistent=True, profile="专门管理 falsesocial 的账号、内容和运维事项。")),
        source="agent",
    )
    falsesocial_agents = [sub for sub in state.subagents.values() if "falsesocial" in sub.agent_id]
    assert len(falsesocial_agents) == 1, [(sub.agent_id, sub.name) for sub in state.subagents.values()]

    a.apply_tui_controls_from_text(
        state,
        ga_control(create_agent_action("FalseSocial 管理代理", persistent=True, force_new=True, profile="专门管理 falsesocial 的账号、内容和运维事项。")),
        source="agent",
    )
    falsesocial_agents = [sub for sub in state.subagents.values() if "falsesocial" in sub.agent_id]
    assert len(falsesocial_agents) == 2, [(sub.agent_id, sub.name) for sub in state.subagents.values()]

    security_agent = a.SubAgentRuntime(
        agent_id="agent-network-security",
        name="网络安全专家",
        home="secret://subagents/agent-network-security",
        role="specialist",
        persistent=True,
        security_context="secret",
        profile_text="负责网络安全、风险分析和安全建议。",
    )
    false_reuse_score = a.reusable_subagent_score(
        security_agent,
        "网络搜索员",
        "专门负责公开网络搜索、网页信息抓取、摘要整理和交叉验证。",
        "researcher",
    )
    assert false_reuse_score < 40, false_reuse_score
    exact_reuse_score = a.reusable_subagent_score(
        security_agent,
        "网络安全专家",
        "负责网络安全、风险分析和安全建议。",
        "specialist",
    )
    assert exact_reuse_score >= 40, exact_reuse_score

    a.apply_tui_controls_from_text(
        state,
        ga_control(create_agent_action("Lifecycle 默认检查", persistent=True, role="researcher")),
        source="agent",
    )
    assert len([sub for sub in state.subagents.values() if sub.name == "Lifecycle 默认检查" and sub.persistent]) == 1
    a.apply_tui_controls_from_text(
        state,
        ga_control({"action": "agent.create", "name": "Lifecycle 默认检查", "role": "researcher"}),
        source="agent",
    )
    lifecycle_matches = [sub for sub in state.subagents.values() if sub.name == "Lifecycle 默认检查"]
    assert len(lifecycle_matches) == 2, [(sub.agent_id, sub.persistent) for sub in lifecycle_matches]
    assert {sub.persistent for sub in lifecycle_matches} == {False, True}, lifecycle_matches

    old_mykey_path = a.mykey_path
    try:
        mykey_file = os.path.join(root, "mykey.py")
        Path(mykey_file).write_text(
            "\n".join([
                "mixin_config = {'llm_nos': ['beta'], 'max_retries': 10, 'base_delay': 0.5}",
                "native_oai_config = {'name': 'alpha', 'apikey': 'k', 'apibase': 'https://example.invalid/v1', 'model': 'model-alpha'}",
                "native_oai_config_1 = {'name': 'beta', 'apikey': 'k', 'apibase': 'https://example.invalid/v1', 'model': 'model-beta'}",
                "",
            ]),
            encoding="utf-8",
        )
        a.mykey_path = lambda: mykey_file
        a.apply_tui_controls_from_text(
            state,
            ga_control(create_agent_action("Model Routed Agent", persistent=True, role="researcher", default_model="beta")),
            source="agent",
        )
        model_agent = a.resolve_subagent(state, "Model Routed Agent")
        assert model_agent is not None, state.subagents
        assert model_agent.default_model == "beta", model_agent
        assert a.load_subagent_meta(model_agent.agent_id).get("default_model") == "beta"
    finally:
        a.mykey_path = old_mykey_path

    assert a.normalized_role("main_orchestrator") == "main_orchestrator"
    assert a.normalized_subagent_role("main_orchestrator") == "specialist"
    parsed_name, parsed_profile, parsed_role, parsed_persistent, parsed_note = a.parse_subagent_new_body(
        "persistent:main_orchestrator:留学生获客运营官 | 负责留学生获客运营。"
    )
    assert parsed_name == "留学生获客运营官", (parsed_name, parsed_role, parsed_note)
    assert parsed_profile == "负责留学生获客运营。", parsed_profile
    assert parsed_role == "specialist", parsed_role
    assert parsed_persistent is True
    assert "主 agent 专属角色" in parsed_note, parsed_note

    a.apply_tui_controls_from_text(
        state,
        ga_control(create_agent_action("主控误用检查", persistent=True, role="main_orchestrator")),
        source="agent",
    )
    bad_role_agent = a.resolve_subagent(state, "主控误用检查")
    assert bad_role_agent is not None, state.subagents
    assert bad_role_agent.role == "specialist", bad_role_agent
    assert "主 agent 专属角色" in state.messages[-1].content, state.messages[-1].content
    bad_role_meta = a.load_subagent_meta(bad_role_agent.agent_id)
    assert bad_role_meta.get("role") == "specialist", bad_role_meta

    secret_role_agent = a.SubAgentRuntime(
        agent_id="agent-secret-role-check",
        name="Secret Role Check",
        home="secret://subagents/agent-secret-role-check",
        role="researcher",
        persistent=True,
        security_context="secret",
        profile_text="role update check",
    )
    state.subagents[secret_role_agent.agent_id] = secret_role_agent
    role_result = a.apply_subagent_control(
        state,
        "subagent_role",
        secret_role_agent.agent_id,
        "",
        {"role": "main_orchestrator"},
        source="agent",
    )
    assert secret_role_agent.role == "specialist", secret_role_agent
    assert role_result and "主 agent 专属角色" in role_result, role_result

    bad_role_agent.role = "main_orchestrator"
    a.save_subagent_meta(bad_role_agent)
    polluted_meta = a.load_subagent_meta(bad_role_agent.agent_id)
    polluted_meta["role"] = "main_orchestrator"
    a.write_text_atomic(a.subagent_meta_file(bad_role_agent), json.dumps(polluted_meta, ensure_ascii=False))
    state.subagents = {}
    assert a.load_subagents(state) is True
    reloaded_bad_role_agent = a.resolve_subagent(state, bad_role_agent.agent_id)
    assert reloaded_bad_role_agent is not None, state.subagents
    assert reloaded_bad_role_agent.role == "specialist", reloaded_bad_role_agent
    dirty_runtime_agent = a.SubAgentRuntime(
        agent_id="agent-dirty-main-role",
        name="Dirty Main Role",
        home="/tmp/agent-dirty-main-role",
        role="main_orchestrator",
        persistent=True,
    )
    dirty_record = a.tui_query_agent_record(dirty_runtime_agent, detail=True)
    assert dirty_record["role"] == "specialist", dirty_record
    assert dirty_record["permissions"]["role"] == "specialist", dirty_record
    dirty_card = a.a2a_agent_card_for_subagent(dirty_runtime_agent)
    assert dirty_card["role"] == "specialist", dirty_card
    assert dirty_card["permissions"]["role"] == "specialist", dirty_card

    assert "schema_version:\"ga-control.v2\"" in a.TUI_AGENT_CONTROL_HINT
    assert "agent.delete" in a.TUI_AGENT_CONTROL_HINT
    assert "当前主控 runtime 专属 role" in a.TUI_AGENT_CONTROL_HINT
    assert "TUI 不会从 name/profile 自然语言里猜生命周期" in a.TUI_AGENT_CONTROL_HINT
    assert "TUI 不会从可见正文里猜复用策略" in a.TUI_AGENT_CONTROL_HINT
    assert "delegate.create" in a.TUI_AGENT_CONTROL_HINT
    assert "能力说明" in a.TUI_AGENT_CONTROL_HINT
    assert "不要在示例、教程或解释中包含可执行 `<ga-control>` 标签" in a.TUI_AGENT_CONTROL_HINT
    assert "回复末尾隐藏块" in a.TUI_AGENT_CONTROL_HINT
    assert "会话标题维护" in a.TUI_AGENT_CONTROL_HINT
    assert "持久标题只由当前主控 runtime 自己通过 `session.rename` 写入" in a.TUI_AGENT_CONTROL_HINT
    assert "session.rename" in a.TUI_AGENT_CONTROL_HINT
    assert "secret_subagents" in a.TUI_AGENT_CONTROL_HINT
    assert "Shuheng `SUBAGENTS_DIR`" in a.TUI_AGENT_CONTROL_HINT
    assert "agent_list" in a.TUI_AGENT_CONTROL_HINT
    assert "task_get" in a.TUI_AGENT_CONTROL_HINT
    assert_retired_control_vocabulary_is_quarantined(state)
    hint_agent = FakeLLMAgent()
    for client in hint_agent.llmclients:
        client.backend.extra_sys_prompt = "prefix\n[GenericAgent-TUI session control]\nold\n[/GenericAgent-TUI session control]\n"
    a.install_tui_control_hint(hint_agent)
    a.install_tui_control_hint(hint_agent)
    for client in hint_agent.llmclients:
        prompt = client.backend.extra_sys_prompt
        assert "prefix" in prompt, prompt
        assert "GenericAgent-TUI session control" not in prompt, prompt
        assert prompt.count(a.TUI_CONTROL_HINT_MARKER) == 1, prompt
        assert "不要在示例、教程或解释中包含可执行 `<ga-control>` 标签" in prompt, prompt
    fenced_control = (
        "现在重新发送：\n"
        "```json\n"
        + json.dumps({"schema_version": "agenttask.v2", **create_agent_action("网络搜索员", persistent=True, role="researcher")}, ensure_ascii=False)
        + "\n"
        "```"
    )
    assert a.extract_tui_controls(fenced_control) == []
    fenced_controls = a.extract_tui_controls(fenced_control, allow_json_fences=True)
    assert len(fenced_controls) == 1, fenced_controls
    assert fenced_controls[0]["name"] == "网络搜索员", fenced_controls
    assert a.strip_tui_controls(fenced_control, allow_json_fences=True) == "现在重新发送："
    non_control_json = "```json\n{\"note\":\"not a TUI action\"}\n```"
    assert a.extract_tui_controls(non_control_json, allow_json_fences=True) == []
    assert a.strip_tui_controls(non_control_json, allow_json_fences=True) == non_control_json
    code_snippet_with_control_example = (
        "搜索结果里出现源码示例：\n"
        "```python\n"
        "example = f'<ga-control>{{\"schema_version\":\"ga-control.v2\",\"actions\":[{{\"action\":\"agent.create\"}}]}}</ga-control>'\n"
        "```\n"
        "这只是展示，不是执行。"
    )
    assert a.extract_tui_controls(code_snippet_with_control_example) == []
    assert a.tui_control_parse_errors(code_snippet_with_control_example) == []
    assert "<ga-control>" in a.strip_tui_controls(code_snippet_with_control_example), code_snippet_with_control_example
    code_snippet_message_count = len(state.messages)
    a.apply_tui_controls_from_text(state, code_snippet_with_control_example, source="agent")
    assert len(state.messages) == code_snippet_message_count, state.messages[-3:]

    long_running_create = ga_control({
        "action": "agent.create",
        "name": "RSS日报编辑",
        "role": "researcher",
        "profile": "负责对接各种 RSS 信息源，每天拉取新闻、持续积累资料并输出日报。",
    })
    long_running_controls = a.extract_tui_controls(long_running_create)
    assert len(long_running_controls) == 1, long_running_controls
    a.apply_tui_controls_from_text(state, long_running_create, source="agent")
    long_running_agent = a.resolve_subagent(state, "RSS日报编辑")
    assert long_running_agent is not None, state.subagents
    assert long_running_agent.persistent is False, long_running_agent
    assert os.path.commonpath([a.TEMP_SUBAGENTS_DIR, long_running_agent.home]) == a.TEMP_SUBAGENTS_DIR, long_running_agent.home

    truncated_create = (
        '<ga-control>{"schema_version":"ga-control.v2","actions":['
        '{"action":"agent.create","name":"新闻主编","role":"researcher","lifecycle":"persistent","profile":"RSS新闻采集与日报排版"}]'
        '</ga-control>'
    )
    repaired_controls = a.extract_tui_controls(truncated_create)
    assert len(repaired_controls) == 1, repaired_controls
    a.apply_tui_controls_from_text(state, truncated_create, source="agent")
    news_agent = a.resolve_subagent(state, "新闻主编")
    assert news_agent is not None, state.subagents
    assert news_agent.persistent is True, news_agent
    delete_control = ga_control({"action": "agent.delete", "target": news_agent.agent_id})
    delete_controls = a.extract_tui_controls(delete_control)
    assert len(delete_controls) == 1, delete_controls
    assert delete_controls[0]["action"] == "subagent_delete", delete_controls
    a.apply_tui_controls_from_text(state, delete_control, source="agent")
    assert a.resolve_subagent(state, news_agent.agent_id) is None, state.subagents
    deleted_meta = a.load_subagent_meta(news_agent.agent_id)
    assert deleted_meta.get("deleted") is True, deleted_meta
    assert deleted_meta.get("status") == "deleted", deleted_meta
    assert "已从列表移除子 agent：新闻主编" in state.messages[-1].content, state.messages[-1].content

    bad_control_count = len(state.messages)
    a.apply_tui_controls_from_text(state, '<ga-control>{"schema_version":</ga-control>', source="agent")
    assert len(state.messages) == bad_control_count + 1, [msg.content for msg in state.messages]
    assert "控制块解析失败" in state.messages[-1].content, state.messages[-1].content

    inline_control_label_then_real_control = (
        "上次我发的 `<ga-control>` 标签没正确闭合，所以没执行。让我重新发一次。\n\n"
        + ga_control({"action": "agent.create", "name": "Inline Label Safe", "role": "researcher"})
    )
    inline_controls = a.extract_tui_controls(inline_control_label_then_real_control)
    assert len(inline_controls) == 1, inline_controls
    assert inline_controls[0]["name"] == "Inline Label Safe", inline_controls
    assert a.tui_control_parse_errors(inline_control_label_then_real_control) == []
    inline_visible = a.strip_tui_controls(inline_control_label_then_real_control)
    assert "`<ga-control>` 标签没正确闭合" in inline_visible, inline_visible
    assert "Inline Label Safe" not in inline_visible, inline_visible
    a.apply_tui_controls_from_text(state, inline_control_label_then_real_control, source="agent")
    assert a.resolve_subagent(state, "Inline Label Safe") is not None
    assert "parse_error" not in state.messages[-1].content, state.messages[-1].content


def assert_subagent_dedicated_skills_are_agent_scoped() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_subagent_skills_")
    retarget_harness(root)
    state = a.State(agent=ContextFakeAgent())
    state.running = True
    skill_dir = Path(a.SHUHENG_SKILLS_DIR, "custom-sop")
    skill_dir.mkdir(parents=True, exist_ok=True)
    unique_marker = "UNIQUE_CUSTOM_SOP_MARKER_FOR_TARGET_AGENT_ONLY"
    skill_dir.joinpath("SKILL.md").write_text(
        "\n".join([
            "---",
            "name: custom-sop",
            "description: Target-only SOP for the policy gate.",
            "---",
            "# Custom SOP",
            "",
            f"Always preserve {unique_marker} when this dedicated skill is loaded.",
            "Use this only for the one subagent that explicitly owns the skill ref.",
            "",
        ]),
        encoding="utf-8",
    )
    skilled = a.create_subagent(
        state,
        "Skill Scoped Agent",
        "Owns the custom SOP and should be the only agent hydrated with it.",
        role="researcher",
        persistent=True,
    )
    plain = a.create_subagent(
        state,
        "Plain Agent",
        "Has no dedicated skill and must not receive custom SOP instructions.",
        role="researcher",
        persistent=True,
    )

    assert a.handle_subagent_command(state, f"/agent skill {skilled.agent_id} add custom-sop") is True
    assert a.normalize_subagent_skill_refs(skilled.skill_refs) == ["custom-sop"], skilled.skill_refs
    assert a.normalize_subagent_skill_refs(plain.skill_refs) == [], plain.skill_refs
    assert "专属 skill" in state.messages[-1].content, state.messages[-1].content
    assert "skill" in {cmd for cmd, _args, _desc, _sendable in a.AGENT_SUBCOMMANDS}
    assert "agent.skill.update" in a.TUI_AGENT_CONTROL_HINT, a.TUI_AGENT_CONTROL_HINT

    a.handle_subagent_command(state, f"/agent skill list {skilled.agent_id}")
    assert "custom-sop" in state.messages[-1].content and "Target-only SOP" in state.messages[-1].content, state.messages[-1].content

    reloaded = a.State(agent=ContextFakeAgent())
    reloaded.running = True
    assert a.load_subagents(reloaded) is True
    loaded_skilled = a.resolve_subagent(reloaded, skilled.agent_id)
    loaded_plain = a.resolve_subagent(reloaded, plain.agent_id)
    assert loaded_skilled is not None and loaded_plain is not None, reloaded.subagents
    assert a.normalize_subagent_skill_refs(loaded_skilled.skill_refs) == ["custom-sop"], loaded_skilled.skill_refs
    assert a.normalize_subagent_skill_refs(loaded_plain.skill_refs) == [], loaded_plain.skill_refs

    target_pack, _target_ref = a.build_context_pack(reloaded, loaded_skilled, "Use custom SOP", "task_skill_target")
    plain_pack, _plain_ref = a.build_context_pack(reloaded, loaded_plain, "Do not use custom SOP", "task_skill_plain")
    target_prompt = a.format_context_pack_for_prompt(target_pack)
    plain_prompt = a.format_context_pack_for_prompt(plain_pack)
    assert target_pack["skill_refs"] == ["custom-sop"], target_pack
    assert target_pack["skill_pack"]["included"][0]["resolved"] is True, target_pack
    assert "Dedicated skills for this agent only" in target_prompt, target_prompt
    assert unique_marker in target_prompt, target_prompt
    assert plain_pack["skill_refs"] == [], plain_pack
    assert unique_marker not in plain_prompt, plain_prompt
    assert "Dedicated skills for this agent only:\n- (none)" in plain_prompt, plain_prompt
    assert unique_marker in a.build_subagent_direct_chat_prompt(reloaded, loaded_skilled, "hello")[0]
    assert unique_marker not in a.build_subagent_direct_chat_prompt(reloaded, loaded_plain, "hello")[0]

    outside_marker = "OUTSIDE_SKILL_FILE_MUST_NOT_BE_INJECTED"
    outside_file = Path(root, "outside-skill.md")
    outside_file.write_text(outside_marker, encoding="utf-8")
    assert a.subagent_skill_file_for_ref(str(outside_file)) == ""
    a.set_subagent_skill_refs(reloaded, loaded_plain, [str(outside_file)], mode="replace")
    outside_pack, _outside_ref = a.build_context_pack(reloaded, loaded_plain, "Reject outside skill path", "task_skill_outside")
    outside_prompt = a.format_context_pack_for_prompt(outside_pack)
    assert outside_pack["skill_pack"]["included"][0]["resolved"] is False, outside_pack
    assert outside_marker not in outside_prompt, outside_prompt
    a.set_subagent_skill_refs(reloaded, loaded_plain, [], mode="clear")

    bulk_refs: list[str] = []
    long_tail_marker = "LONG_SKILL_BODY_AFTER_3500_CHARS_MUST_SURVIVE"
    for index in range(21):
        ref = f"bulk-skill-{index:02d}"
        bulk_refs.append(ref)
        bulk_skill_dir = Path(a.SHUHENG_SKILLS_DIR, ref)
        bulk_skill_dir.mkdir(parents=True, exist_ok=True)
        body = f"# {ref}\n\nSkill body marker {ref}.\n"
        if index == 20:
            body += ("x" * 3800) + long_tail_marker + "\n"
        bulk_skill_dir.joinpath("SKILL.md").write_text(body, encoding="utf-8")
    a.set_subagent_skill_refs(reloaded, loaded_plain, bulk_refs, mode="replace")
    bulk_pack, _bulk_ref = a.build_context_pack(reloaded, loaded_plain, "Use every dedicated skill", "task_skill_bulk")
    bulk_prompt = a.format_context_pack_for_prompt(bulk_pack)
    assert bulk_pack["skill_refs"] == bulk_refs, bulk_pack
    assert len(bulk_pack["skill_pack"]["included"]) == len(bulk_refs), bulk_pack
    assert "bulk-skill-20" in bulk_prompt, bulk_prompt
    assert long_tail_marker in bulk_prompt, bulk_prompt
    a.set_subagent_skill_refs(reloaded, loaded_plain, [], mode="clear")

    prompt_block = a.subagent_prompt_block(loaded_skilled)
    assert "Dedicated skills: custom-sop" in prompt_block, prompt_block
    home_text = "\n".join(line.text for line in a.subagent_home_lines(reloaded, loaded_skilled, 100))
    assert "专属技能" in home_text and "custom-sop" in home_text, home_text
    plain_home_text = "\n".join(line.text for line in a.subagent_home_lines(reloaded, loaded_plain, 100))
    assert "专属技能" in plain_home_text and unique_marker not in plain_home_text, plain_home_text

    agent_record = a.tui_query_agent_record(loaded_skilled, detail=True)
    assert agent_record["skill_refs"] == ["custom-sop"], agent_record
    assert agent_record["dedicated_skills"][0]["resolved"] is True, agent_record
    plain_record = a.tui_query_agent_record(loaded_plain, detail=True)
    assert plain_record["skill_refs"] == [], plain_record
    card = a.a2a_agent_card_for_subagent(loaded_skilled)
    assert card["skill_refs"] == ["custom-sop"], card
    assert card["dedicated_skills"][0]["summary"], card
    registry = a.gateway_capability_registry(reloaded)
    registry_agent = next(row for row in registry["agents"] if row["agent_id"] == loaded_skilled.agent_id)
    assert registry_agent["skill_refs"] == ["custom-sop"], registry_agent

    match = a.tui_tool_agent_match(
        reloaded,
        {
            "objective": "Run a target-only custom SOP",
            "role": "researcher",
            "capabilities_required": ["custom-sop"],
            "reuse_policy": "reuse_only",
        },
    )
    assert match["recommended_action"] == "reuse_existing", match
    assert match["recommended_agent"]["agent_id"] == loaded_skilled.agent_id, match

    create_text = ga_control({
        "action": "agent.create",
        "name": "Skill Control Agent",
        "role": "researcher",
        "lifecycle": "persistent",
        "skills": ["custom-sop"],
        "profile": "Created through ga-control with a dedicated skill.",
    })
    create_controls = a.extract_tui_controls(create_text)
    assert len(create_controls) == 1 and create_controls[0]["skill_refs"] == ["custom-sop"], create_controls
    a.apply_tui_controls_from_text(reloaded, create_text, source="agent")
    control_agent = a.resolve_subagent(reloaded, "Skill Control Agent")
    assert control_agent is not None, reloaded.subagents
    assert a.normalize_subagent_skill_refs(control_agent.skill_refs) == ["custom-sop"], control_agent.skill_refs

    remove_text = ga_control({
        "action": "agent.skill.update",
        "target": control_agent.agent_id,
        "op": "remove",
        "skills": ["custom-sop"],
    })
    remove_controls = a.extract_tui_controls(remove_text)
    assert len(remove_controls) == 1 and remove_controls[0]["action"] == "agent_skill", remove_controls
    a.apply_tui_controls_from_text(reloaded, remove_text, source="agent")
    assert a.normalize_subagent_skill_refs(control_agent.skill_refs) == [], control_agent.skill_refs
    persisted = a.load_subagent_meta(control_agent.agent_id)
    assert persisted.get("skill_refs") == [], persisted


def assert_persistent_agent_dashboard_home_pages() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_dashboard_home_")
    retarget_harness(root)
    state = a.State(agent=FakeAgent())
    state.running = True
    main_session_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_dashboard_home.txt")
    assert a.append_model_response_transcript_turn(main_session_path, "主控最近对话", "主控最近回复")
    state.agent.log_path = main_session_path
    if a.session_names is not None:
        a.session_names.set_name(main_session_path, "主控最近对话")

    assert state.selected_session == a.MAIN_HOME_SESSION_KEY, state.selected_session
    main_render_lines = a.home_lines(state, 100)
    main_lines = [line.text for line in main_render_lines]
    assert any("Shuheng 主 agent 主页" in line for line in main_lines), main_lines
    assert any("╭─ 主控运行概览" in line for line in main_lines), main_lines
    assert any("├─ 核心指标" in line and "已折叠" not in line for line in main_lines), main_lines
    assert not any("▸ 核心指标" in line or "▾ 核心指标" in line for line in main_lines), main_lines
    assert any("活跃任务" in line and "待审批" in line and "定时任务" in line for line in main_lines), main_lines
    old_latest_task_records = a.latest_task_records
    try:
        def fail_latest_task_records():
            raise AssertionError("home_lines should reuse the cached home render before rereading task ledger")

        a.latest_task_records = fail_latest_task_records
        cached_main_lines = [line.text for line in a.home_lines(state, 100)]
    finally:
        a.latest_task_records = old_latest_task_records
    assert cached_main_lines == main_lines, cached_main_lines
    assert any("├─ 运行详情" in line for line in main_lines), main_lines
    assert not any("| 状态" in line or "| ----" in line for line in main_lines[:14]), main_lines[:14]
    assert not any(line.startswith("- 状态:") for line in main_lines[:14]), main_lines[:14]
    main_home_text = "\n".join(main_lines)
    assert "╭─ 详情入口" in main_home_text, main_home_text
    assert "## 功能描述" in main_home_text, main_home_text
    assert "## 当前状态" in main_home_text, main_home_text
    assert "## 待办事项" in main_home_text, main_home_text
    assert "## 最近会话" in main_home_text and "主控最近对话" in main_home_text, main_home_text
    main_session_line = next(line for line in main_render_lines if "主控最近对话" in line.text)
    assert main_session_line.payload["action"] == "open_session", main_session_line
    assert main_session_line.payload["session_type"] == "history", main_session_line
    assert main_session_line.payload["path"] == main_session_path, main_session_line
    assert "## 最近定时任务" in main_home_text, main_home_text
    assert "## 最近任务" in main_home_text, main_home_text
    assert "## 待审批" not in main_home_text, main_home_text
    assert a.display_scope_key(state) == "home:main"
    main_screen = FakeDrawScreen()
    click_width = 90
    click_sidebar_w = a.left_sidebar_width(click_width)
    a.draw_main(main_screen, state, height=50, width=click_width, sidebar_w=click_sidebar_w, rightbar_w=0)
    main_line_idx = next(idx for idx, line in enumerate(state.line_cache) if "主控最近对话" in line.text)
    a.handle_mouse(state, state.main_x0 + 2, state.body_top + main_line_idx - state.scroll, getattr(curses, "BUTTON1_CLICKED", 0), click_width)
    assert state.selected_session == "main", state.selected_session
    assert "已打开当前会话" in state.last_error, state.last_error
    a.show_main_home(state)
    assert a.switch_home_to_chat(state) == "已切到主 agent 聊天。"
    assert state.selected_session == "main", state.selected_session
    assert a.show_home_for_current_scope(state) == "已打开主 agent 主页。"
    assert state.selected_session == a.MAIN_HOME_SESSION_KEY, state.selected_session

    a.submit(state, "hello from main home")
    assert state.selected_session == "main", state.selected_session
    assert state.agent.prompts == [("hello from main home", "user")], state.agent.prompts
    assert a.display_scope_key(state) == "session:main"
    drain_ui(state)
    assert state.status == "idle", state.status
    assert state.selected_session == "main", state.selected_session
    assert a.display_scope_key(state) == "session:main"
    assert a.show_home_for_current_scope(state) == "已打开主 agent 主页。"
    assert state.selected_session == a.MAIN_HOME_SESSION_KEY, state.selected_session

    sub = a.create_subagent(
        state,
        "Dashboard Agent",
        "负责整理主页状态、定时任务摘要和待办事项。",
        role="researcher",
        persistent=True,
    )
    sub.agent = SequencedFakeAgent(["should not run from home"])
    a.append_task_ledger("task_dashboard_agent", status="working", assigned_agent=sub.agent_id, title="主页任务", objective="Show dashboard task")
    a.append_schedule_record({
        "schedule_id": "sched_dashboard_agent",
        "name": "主页巡检",
        "status": "enabled",
        "target": sub.agent_id,
        "trigger": "daily",
    })
    a.append_schedule_run({
        "schedule_id": "sched_dashboard_agent",
        "status": "failed",
        "timestamp": "2026-06-25T09:00:00+08:00",
        "task_id": "task_dashboard_agent_run_record",
    })
    artifact_path = Path(a.AGENT_ARTIFACTS_DIR, "dashboard-agent.md")
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("dashboard artifact", encoding="utf-8")
    a.append_artifact_index(str(artifact_path), artifact_type="subagent-results", source_task_id="task_dashboard_agent")
    approval_id = a.queue_approval(
        approval_type="policy_approval_request",
        summary="Dashboard approval",
        payload={"subagent_id": sub.agent_id, "task_id": "task_dashboard_agent"},
        source="test",
        target=sub.agent_id,
    )

    a.show_subagent_home(state, sub)
    assert state.selected_session == a.subagent_home_session_key(sub.agent_id), state.selected_session
    assert a.active_subagent_view(state) is sub
    assert a.display_scope_key(state) == f"home:sub:{sub.agent_id}"
    home_render_lines = a.home_lines(state, 100)
    home_text = "\n".join(line.text for line in home_render_lines)
    assert "Dashboard Agent 主页" in home_text, home_text
    assert "固定状态卡" in home_text, home_text
    assert "╭─ Dashboard Agent / researcher" in home_text, home_text
    top_card = home_text.split("## 功能描述", 1)[0]
    assert "核心指标" in top_card and "├─ 运行详情" in top_card, home_text
    assert "▸ 核心指标" not in top_card and "▾ 核心指标" not in top_card and "已折叠" not in top_card, home_text
    assert "生命周期 persistent" in top_card and "任务队列 0" in top_card, home_text
    assert "| 状态" not in top_card and "| ----" not in top_card, home_text
    assert "- ID:" not in top_card, home_text
    assert "╭─ 详情入口" in home_text, home_text
    assert "## 最近定时任务" in home_text and "主页巡检" in home_text, home_text
    assert "last:" not in home_text and "task_dashboard_agent_run_record" not in home_text, home_text
    assert "## 最近任务" in home_text and "主页任务" in home_text, home_text
    assert "artifact://" not in home_text, home_text
    assert approval_id not in home_text, home_text

    a.submit(state, "hello from home")
    assert state.selected_session == sub.agent_id, state.selected_session
    assert len(sub.agent.prompts) == 1, sub.agent.prompts
    assert sub.agent.prompts[0][1] == f"subagent-chat:{sub.agent_id}", sub.agent.prompts
    assert "hello from home" in sub.agent.prompts[0][0], sub.agent.prompts
    drain_ui(state)
    assert state.status == "idle", state.status
    assert a.show_home_for_current_scope(state) == f"已打开代理主页：{sub.name}"
    sub_home_lines = a.home_lines(state, 100)
    sub_home_text = "\n".join(line.text for line in sub_home_lines)
    assert "## 最近会话" in sub_home_text and "hello from home" in sub_home_text, sub_home_text
    sub_session_line = next(line for line in sub_home_lines if "hello from home" in line.text)
    assert sub_session_line.payload["action"] == "open_session", sub_session_line
    assert sub_session_line.payload["session_type"] == "subagent", sub_session_line
    assert sub_session_line.payload["agent_id"] == sub.agent_id, sub_session_line
    sub_screen = FakeDrawScreen()
    a.draw_main(sub_screen, state, height=50, width=click_width, sidebar_w=click_sidebar_w, rightbar_w=0)
    sub_line_idx = next(idx for idx, line in enumerate(state.line_cache) if "hello from home" in line.text)
    a.handle_mouse(state, state.main_x0 + 2, state.body_top + sub_line_idx - state.scroll, getattr(curses, "BUTTON1_CLICKED", 0), click_width)
    assert state.selected_session == sub.agent_id, state.selected_session
    assert a.selected_subagent(state) is sub, state.selected_session

    dashboard_control = ga_control({
        "action": "dashboard.update",
        "target": sub.agent_id,
        "dashboard": {
            "sections": [
                {"type": "markdown", "title": "声明区", "markdown": "安全主页内容"},
                {"type": "unsupported-widget", "title": "ignored", "script": "ignored"},
                {"type": "todos", "title": "自定义待办"},
            ],
            "status_narrative": "正在维护自己的主页。",
            "todos": [{"text": "复核共享账本"}, "同步 artifact refs"],
            "markdown": "全局声明备用内容",
            "script": "ignored",
        },
        "artifact_refs": ["artifact://artifacts/dashboard-agent.md"],
    })
    extracted = a.extract_tui_controls(dashboard_control)
    assert len(extracted) == 1, extracted
    assert extracted[0]["action"] == "dashboard_update", extracted
    a.apply_tui_controls_from_text(state, dashboard_control, source="agent")
    assert sub.dashboard["schema_version"] == "dashboard.v1", sub.dashboard
    assert sub.dashboard["target"] == sub.agent_id, sub.dashboard
    assert [section["type"] for section in sub.dashboard["sections"]] == ["markdown", "todos"], sub.dashboard
    assert "script" not in json.dumps(sub.dashboard, ensure_ascii=False), sub.dashboard
    assert sub.dashboard["provenance"]["artifact_refs"] == ["artifact://artifacts/dashboard-agent.md"], sub.dashboard
    persisted = a.load_subagent_meta(sub.agent_id)
    assert persisted["dashboard"]["status_narrative"] == "正在维护自己的主页。", persisted
    updated_home_text = "\n".join(line.text for line in a.subagent_home_lines(state, sub, 100))
    assert "声明区" in updated_home_text and "安全主页内容" in updated_home_text, updated_home_text
    assert "自定义待办" in updated_home_text and "复核共享账本" in updated_home_text, updated_home_text
    assert "unsupported-widget" not in updated_home_text, updated_home_text

    main_control = {
        "action": "dashboard_update",
        "target": "main",
        "sections": [
            {"type": "markdown", "title": "主声明", "markdown": "主 agent 自定义主页"},
            {"type": "tasks", "title": "任务流"},
        ],
        "todos": ["检查 orchestrator 面板"],
    }
    assert "已更新主 agent 主页声明" in a.apply_dashboard_control(state, "dashboard_update", "main", "", main_control, source="test")
    a.show_main_home(state)
    main_updated_text = "\n".join(line.text for line in a.home_lines(state, 100))
    assert "主声明" in main_updated_text and "主 agent 自定义主页" in main_updated_text, main_updated_text
    assert "任务流" in main_updated_text, main_updated_text

    temp = a.create_subagent(state, "Temporary Dashboard", role="researcher", persistent=False)
    temp_result = a.show_home_for_current_scope(state, temp.agent_id)
    assert "没有持久主页" in temp_result, temp_result
    temp_update = a.apply_dashboard_control(state, "dashboard_update", temp.agent_id, "", {"target": temp.agent_id, "sections": [{"type": "markdown"}]}, source="test")
    assert "不持久化主页" in temp_update, temp_update
    assert temp.dashboard == {}, temp.dashboard

    sub_fields = set(a.SubAgentRuntime.__dataclass_fields__)
    assert "dashboard" in sub_fields, sub_fields
    registry = a.scheduled_task_registry(state)
    assert registry["owner"] == "ga-tui.control_plane", registry
    assert any(row.get("schedule_id") == "sched_dashboard_agent" for row in registry.get("jobs", [])), registry


def assert_temp_subagent_current_fallback_is_reloadable() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_temp_subagent_current_")
    retarget_harness(root)
    state = a.State(agent=ContextFakeAgent())
    state.running = True
    assert a.active_ui_session_key(state) == ""

    sub = a.create_subagent(state, "TUI-Smoke", role="reviewer", persistent=False)
    assert sub.persistent is False
    assert os.path.commonpath([a.TEMP_SUBAGENTS_DIR, sub.home]) == a.TEMP_SUBAGENTS_DIR, sub.home
    assert os.path.relpath(sub.home, a.TEMP_SUBAGENTS_DIR).split(os.sep)[0] == "current", sub.home

    state.subagents = {}
    assert a.load_subagents(state) is True
    assert a.resolve_subagent(state, sub.agent_id) is not None, state.subagents
    assert a.resolve_subagent(state, "TUI-Smoke") is not None, state.subagents

    keyed_agent = FakeLLMAgent()
    a.set_agent_log_path(keyed_agent, a.new_session_log_path())
    keyed_state = a.State(agent=keyed_agent)
    keyed_state.running = True
    assert a.active_ui_session_key(keyed_state) != ""
    a.load_subagents(keyed_state)
    assert a.resolve_subagent(keyed_state, sub.agent_id) is None, keyed_state.subagents


def assert_tui_query_tools_expose_dashboard_state() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_query_tools_")
    retarget_harness(root)
    state = a.State(agent=FakeLLMAgent())
    state.running = True
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)
    state.agent.log_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_query_tools.txt")
    a.install_tui_query_runtime(state.agent, state)
    a.install_tui_query_runtime(state.agent, state)
    schema_names = [
        str(item.get("function", {}).get("name") or "")
        for item in a.agentmain.TOOLS_SCHEMA
        if isinstance(item, dict) and isinstance(item.get("function"), dict)
    ]
    for name in a.TUI_QUERY_TOOL_NAMES:
        assert schema_names.count(name) == 1, (name, schema_names)
        assert hasattr(a.agentmain.GenericAgentHandler, f"do_{name}"), name
    for name in a.TUI_SCHEDULE_TOOL_NAMES:
        assert schema_names.count(name) == 1, (name, schema_names)
        assert hasattr(a.agentmain.GenericAgentHandler, f"do_{name}"), name

    researcher = a.create_subagent(
        state,
        "Query Researcher",
        "Find sources, compare evidence, and return artifact refs.",
        role="researcher",
        persistent=True,
    )
    coder = a.create_subagent(
        state,
        "Query Coder",
        "Implement approved single-writer changes.",
        role="coder",
        persistent=False,
    )
    a.append_task_ledger("task_query_research", status="working", assigned_agent=researcher.agent_id, objective="Research dashboard tools")
    a.append_task_ledger("task_query_done", status="completed", assigned_agent=coder.agent_id, objective="Completed write task")
    artifact_ref = a.write_harness_artifact("query-tools", "result", "query tool artifact", source_task_id="task_query_research")
    approval_id = a.queue_approval(
        approval_type="policy_approval_request",
        summary="Need approval for query test",
        payload={"task_id": "task_query_research", "deferred_operation": "query_test"},
        source="orchestrator.main",
        target=researcher.agent_id,
        approval_required_for="modify_permission_policy",
    )

    agent_list = a.tui_tool_agent_list(state, {})
    assert agent_list["status"] == "ok", agent_list
    assert {item["agent_id"] for item in agent_list["agents"]} >= {researcher.agent_id, coder.agent_id}
    persistent_only = a.tui_tool_agent_list(state, {"include_ephemeral": False})
    assert coder.agent_id not in {item["agent_id"] for item in persistent_only["agents"]}, persistent_only

    agent_get = a.tui_tool_agent_get(state, {"target": "Query Researcher"})
    assert agent_get["agent"]["agent_id"] == researcher.agent_id, agent_get
    assert agent_get["agent"]["permissions"]["write_policy"] == "none", agent_get

    match = a.tui_tool_agent_match(
        state,
        {
            "objective": "Research dashboard tools",
            "role": "researcher",
            "capabilities_required": ["web.search", "read"],
        },
    )
    assert match["recommended_action"] == "reuse_existing", match
    assert match["recommended_agent"]["agent_id"] == researcher.agent_id, match
    force_new = a.tui_tool_agent_match(state, {"objective": "Research dashboard tools", "reuse_policy": "force_new"})
    assert force_new["recommended_action"] == "create_new", force_new

    task_list = a.tui_tool_task_list(state, {})
    assert [item["task_id"] for item in task_list["tasks"]] == ["task_query_research"], task_list
    task_all = a.tui_tool_task_list(state, {"include_completed": True})
    assert {item["task_id"] for item in task_all["tasks"]} >= {"task_query_research", "task_query_done"}, task_all
    task_get = a.tui_tool_task_get(state, {"task_id": "task_query_research"})
    assert task_get["task"]["assigned_agent"] == researcher.agent_id, task_get
    assert task_get["approvals"][-1]["approval_id"] == approval_id, task_get

    approvals = a.tui_tool_approval_list(state, {})
    assert approvals["approvals"][0]["approval_id"] == approval_id, approvals
    assert "payload" not in approvals["approvals"][0], approvals
    artifacts = a.tui_tool_artifact_list(state, {"source_task_id": "task_query_research"})
    assert artifacts["artifacts"][0]["uri"] == artifact_ref, artifacts
    capabilities = a.tui_tool_capability_list(state, {})
    assert "researcher" in capabilities["capabilities"]["roles"], capabilities
    schedule_tool = a.tui_tool_schedule_create(
        state,
        {
            "schedule_id": "sched_tool_digest",
            "name": "Tool Digest",
            "interval": "1m",
            "execution": {
                "mode": "agent_task",
                "routing": {"selected_agent": researcher.name},
                "work_order": {"objective": "Produce a short tool-created digest."},
                "capability_contract": {"tools_allowed": ["read"], "write_policy": "none"},
                "context_contract": {"history_mode": "summary", "artifact_reference_only": True},
                "output_contract": {"format": "structured_markdown", "required_sections": ["summary"]},
            },
        },
    )
    assert schedule_tool["schema_version"] == "ga-tui.tool.v1", schedule_tool
    assert schedule_tool["status"] == "ok", schedule_tool
    assert schedule_tool["schedule"]["schedule_id"] == "sched_tool_digest", schedule_tool
    assert schedule_tool["schedule"]["source"] == "tool:schedule_create", schedule_tool
    assert schedule_tool["schedule"]["dispatch_contract"] == "agenttask.v2", schedule_tool
    assert schedule_tool["schedule"]["execution"]["mode"] == "agent_task", schedule_tool
    schema = next(tool for tool in a.TUI_SCHEDULE_TOOL_SCHEMAS if tool["function"]["name"] == "schedule_create")
    execution_schema = schema["function"]["parameters"]["properties"]["execution"]
    assert execution_schema["required"] == ["mode"], execution_schema
    assert set(execution_schema["properties"]["mode"]["enum"]) == {"tui_action", "agent_task"}, execution_schema
    schedule_list = a.tui_tool_schedule_list(state, {})
    assert schedule_list["status"] == "ok", schedule_list
    assert any(job["schedule_id"] == "sched_tool_digest" for job in schedule_list["registry"]["jobs"]), schedule_list

    handler = a.agentmain.GenericAgentHandler(state.agent, [], root)
    outcome = handler.do_agent_list({}, None)
    assert outcome.data["status"] == "ok", outcome.data
    assert outcome.next_prompt == "\n", outcome.next_prompt
    schedule_outcome = handler.do_schedule_list({}, None)
    assert schedule_outcome.data["status"] == "ok", schedule_outcome.data
    assert schedule_outcome.next_prompt == "\n", schedule_outcome.next_prompt


def assert_retired_control_vocabulary_is_quarantined(state: a.State) -> None:
    retired_tokens = ("<ga-tui>", "subagent_ask", "subagent_create", "task_update")
    for token in retired_tokens:
        assert token not in a.TUI_AGENT_CONTROL_HINT, token
    for relative_path in (
        "README.md",
        "docs/runtime-provider-control-plane.md",
        ".trellis/spec/backend/agent-control-protocol.md",
    ):
        text = a.read_text_file(os.path.join(a.APP_ROOT_DIR, relative_path), "")
        for token in retired_tokens:
            assert token not in text, (relative_path, token)

    before_count = len(state.subagents)
    old_external_action = ga_control({"action": "subagent_create", "name": "Retired External Action"})
    assert a.extract_tui_controls(old_external_action) == []
    a.apply_tui_controls_from_text(state, old_external_action, source="agent")
    assert len(state.subagents) == before_count, state.subagents
    assert a.strip_tui_controls('visible\n<ga-tui>{"action":"subagent_create","name":"Hidden"}</ga-tui>') == "visible"


def assert_historical_subagent_result_quarantine_backfill() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_historical_subagent_restore_")
    old_model_dir = a.MODEL_RESPONSES_DIR
    old_session_meta = a.SESSION_META_PATH
    try:
        retarget_harness(root)
        a.MODEL_RESPONSES_DIR = os.path.join(root, "model_responses")
        a.SESSION_META_PATH = os.path.join(a.MODEL_RESPONSES_DIR, "session_meta.json")
        os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)

        objective = "请小艾自我介绍并给一句总结。"
        response_text = (
            "我会派发给小艾。\n"
            f'<ga-tui>{{"action":"subagent_ask","target":"小艾","prompt":"{objective}"}}</ga-tui>'
        )
        session_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_legacy.txt")
        prompt = {"role": "user", "content": [{"type": "text", "text": "叫小艾聊一句"}]}
        response = [{"type": "text", "text": response_text}]
        a.write_text_atomic(
            session_path,
            "=== Prompt === 2026-05-23 10:49:12\n"
            + json.dumps(prompt, ensure_ascii=False, indent=2)
            + "\n\n=== Response === 2026-05-23 10:49:33\n"
            + repr(response)
            + "\n",
        )

        artifact_ref = a.write_harness_artifact(
            "subagent-results",
            "agent-legacy-task_legacy",
            "# 小艾 result\n\nTask: task_legacy\n\n"
            "**LLM Running (Turn 1) ...**\n\n"
            "先查资料。\n\n"
            "🛠️ Tool: `file_read`  📥 args:\n"
            "````text\n{\"path\":\"secret.txt\"}\n````\n"
            "`````\nsecret raw tool output\n`````\n\n"
            "**LLM Running (Turn 2) ...**\n\n"
            "小艾完整回复正文。\n",
            source_task_id="task_legacy",
            provenance={"generated_by": "agent-legacy", "role": "researcher", "source": "subagent_result"},
        )
        unrelated_ref = a.write_harness_artifact(
            "subagent-results",
            "agent-other-task_other",
            "# Other result\n\nTask: task_other\n\n不该出现在恢复会话里。\n",
            source_task_id="task_other",
            provenance={"generated_by": "agent-other", "role": "researcher", "source": "subagent_result"},
        )
        a.append_jsonl(a.AGENT_TASK_LEDGER_PATH, {
            "task_id": "task_legacy",
            "status": "working",
            "assigned_agent": "agent-legacy",
            "objective": objective,
            "artifact_refs": [],
            "timestamp": "2026-05-23T10:49:34+0800",
        })
        a.append_jsonl(a.AGENT_TASK_LEDGER_PATH, {
            "task_id": "task_legacy",
            "status": "completed",
            "assigned_agent": "agent-legacy",
            "objective": objective,
            "artifact_refs": [artifact_ref],
            "timestamp": "2026-05-23T10:49:40+0800",
        })
        a.append_jsonl(a.AGENT_TASK_LEDGER_PATH, {
            "task_id": "task_other",
            "status": "completed",
            "assigned_agent": "agent-other",
            "objective": "另一个没有出现在控制块里的任务。",
            "artifact_refs": [unrelated_ref],
            "timestamp": "2026-05-23T10:49:41+0800",
        })

        assert a.backfill_durable_subagent_result_messages_for_path(session_path) == 1
        assert a.backfill_durable_subagent_result_messages_for_path(session_path) == 0
        restored = a.durable_ui_system_messages_for_path(session_path, backfill=False)
        assert len(restored) == 1, restored
        assert "小艾完整回复正文。" in restored[0].content, restored[0].content
        assert "secret raw tool output" not in restored[0].content, restored[0].content
        assert "不该出现在恢复会话里。" not in restored[0].content, restored[0].content
    finally:
        a.MODEL_RESPONSES_DIR = old_model_dir
        a.SESSION_META_PATH = old_session_meta
        a.configure_frontend_history_storage()


def assert_recent_sessions_use_last_message_activity() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_recent_sessions_")
    retarget_harness(root)
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)

    def write_session(name: str, prompt_time: str, response_time: str, text: str) -> str:
        session_path = os.path.join(a.MODEL_RESPONSES_DIR, name)
        prompt = {"role": "user", "content": [{"type": "text", "text": text}]}
        response = [{"type": "text", "text": f"reply to {text}"}]
        a.write_text_atomic(
            session_path,
            f"=== Prompt === {prompt_time}\n"
            + json.dumps(prompt, ensure_ascii=False, indent=2)
            + f"\n\n=== Response === {response_time}\n"
            + repr(response)
            + "\n",
        )
        return session_path

    old_path = write_session(
        "model_responses_old.txt",
        "2026-05-30 10:00:00",
        "2026-05-30 10:00:03",
        "old message",
    )
    new_path = write_session(
        "model_responses_new.txt",
        "2026-05-30 11:00:00",
        "2026-05-30 11:00:03",
        "new message",
    )
    a.save_session_meta_registry({
        a.session_key(old_path): {"last_opened_at": time.mktime(time.strptime("2026-05-30 12:00:00", "%Y-%m-%d %H:%M:%S"))},
    })

    state = a.State(agent=None)
    assert a.load_history(state, force=True) is True
    history_entries = list(enumerate(state.history, 1))
    recent = a.recent_history_items(history_entries, set(), limit=2)
    assert [os.path.basename(item[0]) for _idx, item in recent] == [
        "model_responses_new.txt",
        "model_responses_old.txt",
    ], recent
    assert not a.session_meta_for(state, new_path).get("last_opened_at"), a.session_meta_for(state, new_path)

    used_paths = {a.normalized_path(new_path)}
    deduped_recent = a.recent_history_items(history_entries, used_paths, limit=2)
    assert all(a.normalized_path(item[0]) not in used_paths for _idx, item in deduped_recent), deduped_recent


def assert_history_curator_skill_uses_progressive_disclosure() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_history_curator_")
    retarget_harness(root)
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)

    shuheng_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_shuheng_skill.txt")
    other_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_other_skill.txt")
    assert a.append_model_response_transcript_turn(
        shuheng_path,
        "修复左栏 token",
        "已修复 token registry 刷新和 live tracker 重置。",
    )
    assert a.append_model_response_transcript_turn(
        other_path,
        "写一个小游戏",
        "这是另一个分类里的临时任务。",
    )
    a.save_session_meta_registry({
        os.path.basename(shuheng_path): {
            "category": "Shuheng",
            "description": "修复左栏 token；长期经验是历史侧栏异常先查 Shuheng-owned sidecars。",
            "last_user_at": time.time(),
        },
        os.path.basename(other_path): {
            "category": "Games",
            "description": "一次性小游戏讨论。",
            "last_user_at": time.time() - 60,
        },
    })
    if a.session_names is not None:
        a.session_names.set_name(shuheng_path, "Shuheng token 修复")
        a.session_names.set_name(other_path, "小游戏")

    state = a.State(agent=FakeLLMAgent())
    state.running = True
    prompt, artifact_ref, rows = a.history_curator_skill_prompt(state, "cat:Shuheng limit=5")
    assert artifact_ref.startswith("artifact://artifacts/history-curation-index/"), artifact_ref
    assert len(rows) == 1, rows
    assert rows[0]["category"] == "Shuheng", rows
    assert rows[0]["stable_id"] == "shuheng_skill", rows
    assert "[Shuheng History Curator Skill]" in prompt, prompt
    assert "Progressive disclosure protocol" in prompt, prompt
    assert "Nested subskills" in prompt, prompt
    assert "Do not write long-term memory directly" in prompt, prompt
    assert "Do not create persistent subagents directly" in prompt, prompt
    assert "Memory Candidates (candidate only" in prompt, prompt
    assert "Persistent Subagent Recommendations (recommendation only" in prompt, prompt
    assert "id:shuheng_skill" in prompt, prompt
    assert "model_responses_shuheng_skill.txt" in prompt, prompt
    assert "model_responses_other_skill.txt" not in prompt, prompt

    a.submit(state, "/curate-history cat:Shuheng limit=5")
    assert state.agent.prompts, state.agent.prompts
    submitted_prompt, submitted_source = state.agent.prompts[-1]
    assert submitted_source == "user:history_curator_skill", state.agent.prompts
    assert "Index artifact: artifact://artifacts/history-curation-index/" in submitted_prompt, submitted_prompt
    assert state.messages[0].role == "user" and state.messages[0].content == "/curate-history cat:Shuheng limit=5", state.messages

    runtime_agent = RuntimeCaptureFakeAgent()
    runtime_state = a.State(agent=runtime_agent)
    runtime_state.running = True
    a.submit(runtime_state, "/curate-history cat:Shuheng limit=5")
    assert runtime_agent.runtime_requests, runtime_agent.runtime_requests
    runtime_request = runtime_agent.runtime_requests[-1]
    assert runtime_request.source == "user:history_curator_skill", runtime_request
    assert runtime_request.metadata.get("runtime_context_mode") == "lean", runtime_request.metadata
    assert runtime_request.context_pack_ref == "", runtime_request
    assert runtime_request.artifact_refs == [], runtime_request
    assert "[GA TUI Context Pack]" not in runtime_request.prompt, runtime_request.prompt
    assert runtime_request.prompt.startswith("[Shuheng History Curator Skill]"), runtime_request.prompt
    assert "Index artifact: artifact://artifacts/history-curation-index/" in runtime_request.prompt, runtime_request.prompt

    empty_state = a.State(agent=FakeLLMAgent())
    empty_state.running = True
    assert a.start_history_curator_skill(empty_state, "cat:Missing", "/curate-history cat:Missing") is False
    assert empty_state.agent.prompts == [], empty_state.agent.prompts
    assert any("没有可策展的历史会话" in msg.content for msg in empty_state.messages), empty_state.messages


def assert_model_owned_session_rename_is_title_path() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_model_title_")
    retarget_harness(root)
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)
    if a.session_names is None:
        return

    agent = ScriptedMetadataAgent(["后台标题不应消费"])
    path = a.new_session_log_path()
    a.set_agent_log_path(agent, path)
    state = a.State(agent=agent)
    state.running = True
    state.messages = [
        a.Message("user", "第一轮：整理 Shuheng 历史会话标题。"),
        a.Message("assistant", "先修复历史标题。"),
    ]

    assert a.maybe_autoname_current_session(state) is True
    drain_ui(state)
    assert a.session_names.name_for(path) != "后台标题不应消费", a.session_names._load()
    assert agent.llmclient.backend.title_queue == ["后台标题不应消费"], agent.llmclient.backend.title_queue
    assert not any("生成一个简短标题" in prompt for prompt in agent.llmclient.backend.raw_prompts), agent.llmclient.backend.raw_prompts

    state.messages.extend([
        a.Message("user", "第二轮：现在由主 runtime 自己维护标题。"),
        a.Message("assistant", "我会在需要时用 session.rename 维护标题。"),
    ])
    assert a.maybe_autoname_current_session(state) is True
    drain_ui(state)
    assert agent.llmclient.backend.title_queue == ["后台标题不应消费"], agent.llmclient.backend.title_queue
    assert not any("生成一个简短标题" in prompt for prompt in agent.llmclient.backend.raw_prompts), agent.llmclient.backend.raw_prompts

    a.apply_tui_controls_from_text(
        state,
        ga_control({"action": "session.rename", "target": "current", "value": "智能控制标题"}),
        source="agent",
    )
    assert a.session_names.name_for(path) == "智能控制标题", a.session_names._load()
    control_meta = a.load_session_meta_registry()[os.path.basename(path)]
    assert control_meta["title_source"] == "ai", control_meta
    assert not control_meta.get("title_signature"), control_meta

    rename_result = a.rename_current_session(state, "固定手动标题")
    assert "已持久化" in rename_result, rename_result
    state.messages.extend([
        a.Message("user", "第三轮：这个手动标题不要被自动覆盖。"),
        a.Message("assistant", "手动标题应保持。"),
    ])
    assert a.maybe_autoname_current_session(state) is True
    drain_ui(state)
    a.apply_tui_controls_from_text(
        state,
        ga_control({"action": "session.rename", "target": "current", "value": "不应覆盖手动"}),
        source="agent",
    )
    assert a.session_names.name_for(path) == "固定手动标题", a.session_names._load()
    manual_meta = a.load_session_meta_registry()[os.path.basename(path)]
    assert manual_meta["title_source"] == "manual", manual_meta


def assert_ohmypi_process_summary_does_not_title_history() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_omp_title_")
    retarget_harness(root)
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)
    path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_omp_title.txt")
    user_text = "修复左栏历史会话标题"
    final_text = "已完成历史会话标题修复，左侧会显示用户任务。"
    assistant_text = (
        "**LLM Running (Turn 1) ...**\n"
        "<summary>OMP 思考</summary>\n"
        "<thinking>Hidden OMP reasoning must stay out of history titles.</thinking>\n\n"
        f"{final_text}"
    )
    prompt = {"role": "user", "content": [{"type": "text", "text": user_text}]}
    response = [{"type": "text", "text": assistant_text}]
    a.write_text_atomic(
        path,
        "=== Prompt === 2026-06-22 09:19:20\n"
        + json.dumps(prompt, ensure_ascii=False, indent=2)
        + "\n\n=== Response === 2026-06-22 09:19:30\n"
        + repr(response)
        + "\n",
    )
    stat = os.stat(path)
    a.save_session_meta_registry({
        os.path.basename(path): {
            "cache_mtime": stat.st_mtime,
            "cache_size": stat.st_size,
            "preview": "OMP 思考",
            "rounds": 1,
            "last_user_at": time.mktime(time.strptime("2026-06-22 09:19:20", "%Y-%m-%d %H:%M:%S")),
            "description": "开始：修复左栏历史会话标题；摘要：OMP 思考",
            "ui_preview_messages": [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": "（预览）OMP 思考"},
            ],
        }
    })

    state = a.State(agent=None)
    assert a.load_history(state, force=True) is True
    assert state.history_names[path] == user_text, state.history_names
    assert "OMP 思考" not in state.history_names[path], state.history_names[path]
    assert "OMP 思考" not in state.history_descriptions[path], state.history_descriptions[path]
    assert "已完成历史会话标题修复" in state.history_descriptions[path], state.history_descriptions[path]

    meta = a.load_session_meta_registry()[os.path.basename(path)]
    assert meta["preview"] == user_text, meta
    preview_messages = meta["ui_preview_messages"]
    assert preview_messages[-1]["role"] == "assistant", preview_messages
    assert "已完成历史会话标题修复" in preview_messages[-1]["content"], preview_messages
    assert "OMP 思考" not in preview_messages[-1]["content"], preview_messages

    messages = [a.Message("user", user_text), a.Message("assistant", assistant_text)]
    assert a.suggested_session_title(messages) == user_text
    metadata_context = a.ai_metadata_context(messages)
    assert user_text in metadata_context, metadata_context
    assert final_text in metadata_context, metadata_context
    assert "OMP 思考" not in metadata_context, metadata_context
    assert "Hidden OMP reasoning" not in metadata_context, metadata_context


def assert_ohmypi_local_category_fallback_for_sidebar() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_omp_category_")
    retarget_harness(root)
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)
    agent = FakeLLMAgent()
    setattr(agent, "_ga_tui_runtime_provider_id", "ohmypi")
    setattr(agent.llmclient.backend, "supports_raw_ask", False)

    def forbidden_raw_ask(_request):
        raise AssertionError("OMP local category fallback must not call raw_ask")
        yield ""  # pragma: no cover

    agent.llmclient.backend.raw_ask = forbidden_raw_ask
    state = a.State(agent=agent)
    path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_category_local.txt")
    a.set_agent_log_path(agent, path)
    assistant_text = (
        "**LLM Running (Turn 1) ...**\n"
        "<summary>OMP 思考</summary>\n"
        "<thinking>这里故意写支付、暗网、收款，不能影响左栏分类。</thinking>\n\n"
        "左栏分类兜底已改成 Shuheng 自己落盘。"
    )
    state.messages = [
        a.Message("user", "左栏会话的自动分类呢？"),
        a.Message("assistant", assistant_text),
    ]
    assert a.append_model_response_transcript_turn(path, state.messages[0].content, assistant_text)
    assert a.agent_supports_inline_ai_metadata(agent) is False
    assert a.maybe_start_ai_category_job(state, path, agent, messages=state.messages) is True
    assert state.category_jobs == set(), state.category_jobs
    meta = a.load_session_meta_registry()[os.path.basename(path)]
    assert meta["category"] == "Shuheng", meta
    assert meta["category_source"] == "local", meta
    assert meta.get("category_signature"), meta

    a.set_session_meta_fields(state, path, category="手动类", category_source="manual")
    assert a.maybe_start_ai_category_job(state, path, agent, messages=state.messages) is False
    manual_meta = a.load_session_meta_registry()[os.path.basename(path)]
    assert manual_meta["category"] == "手动类", manual_meta
    assert manual_meta["category_source"] == "manual", manual_meta

    game_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_category_game.txt")
    a.set_agent_log_path(agent, game_path)
    game_state = a.State(agent=agent)
    game_state.messages = [
        a.Message("user", "写一个小游戏地图"),
        a.Message(
            "assistant",
            "**LLM Running (Turn 1) ...**\n"
            "<summary>Shuheng 左栏分类</summary>\n"
            "<thinking>Hidden Shuheng metadata must stay out of category fallback.</thinking>\n\n"
            "地图逻辑已完成。",
        ),
    ]
    assert a.append_model_response_transcript_turn(game_path, game_state.messages[0].content, game_state.messages[1].content)
    assert a.maybe_start_ai_category_job(game_state, game_path, agent, messages=game_state.messages) is True
    game_meta = a.load_session_meta_registry()[os.path.basename(game_path)]
    assert game_meta["category"] != "Shuheng", game_meta
    assert "思考" not in game_meta["category"], game_meta


def assert_missing_source_history_rows_restore_from_l4_archive() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_missing_source_history_")
    retarget_harness(root)
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)
    os.makedirs(a.L4_RAW_SESSIONS_DIR, exist_ok=True)
    missing_path = os.path.join(a.MODEL_RESPONSES_DIR, "model_responses_missing_source.txt")
    archive_text = (
        "=== Prompt === 2026-01-01 12:00:00\n"
        "=== USER ===\n"
        "archived user turn\n"
        "=== Response === 2026-01-01 12:01:00\n"
        "archived assistant turn\n"
    )
    archive_path = os.path.join(a.L4_RAW_SESSIONS_DIR, "2026-01.zip")
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("0101_1200-0101_1201.txt", archive_text)
    a.save_session_meta_registry({
        os.path.basename(missing_path): {
            "preview": "archived session preview",
            "description": "Missing raw source retained in TUI registry",
            "last_user_at": time.mktime(time.strptime("2026-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")),
            "rounds": 1,
            "ui_preview_messages": [
                {"role": "user", "content": "archived user turn"},
            ],
            "ui_preview_loaded_rounds": 1,
            "ui_preview_total_rounds": 1,
        },
    })
    state = a.State(agent=FakeLLMAgent())
    assert a.load_history(state, force=True) is True
    assert any(path == missing_path for path, _mtime, _preview, _rounds in state.history), state.history
    meta = a.session_meta_for(state, missing_path)
    assert meta["source_missing"] is True, meta
    assert meta["archive_backed"] is True, meta
    assert meta["source_state"] == "missing", meta
    assert state.history_descriptions[missing_path] == "Missing raw source retained in TUI registry", state.history_descriptions
    state.status = "idle"
    a.restore_history(state, missing_path)
    assert os.path.exists(missing_path), missing_path
    assert "archived user turn" in a.read_text_file(missing_path)
    assert "已从 L4 归档恢复源文件" in state.last_error, state.last_error
    assert state.history_ui_path == missing_path, state.history_ui_path
    assert getattr(state.agent, "log_path", "") == missing_path, getattr(state.agent, "log_path", "")
    restored_meta = a.load_session_meta_registry().get(os.path.basename(missing_path), {})
    assert restored_meta.get("source_restored_archive") == "2026-01.zip", restored_meta
    assert restored_meta.get("source_restored_member") == "0101_1200-0101_1201.txt", restored_meta


def assert_self_intro_does_not_consume_mutual_chat_step() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_policy_check_")
    retarget_harness(root)
    install_fake_agent_runtime()
    main_agent = SequencedFakeAgent(["我没有发出新的控制块。"])
    state = a.State(agent=main_agent)
    state.running = True
    orchestration_text = ga_control(
        plan_action("缺少自我介绍步骤的双代理对话", ["创建正式子代理", "创建临时子代理", "两个代理互相聊天对话", "汇总所有内容到我这里"]),
        create_agent_action("正式丙", persistent=True, profile="你是正式永久子代理，名叫正式丙。稍后和临时子代理临时丁交流。", plan_step_id="创建正式子代理"),
        create_agent_action("临时丁", temporary=True, profile="你是临时子代理，名叫临时丁。稍后和正式子代理正式丙交流。", plan_step_id="创建临时子代理"),
        delegate_action("正式丙", "请先向主控说一句话自我介绍，说完了告诉我。"),
        delegate_action("临时丁", "请先向主控说一句话自我介绍，说完了告诉我。"),
    )
    a.apply_tui_controls_from_text(state, orchestration_text, source="agent")
    plan_id = state.active_plan_task_id
    steps = sorted(
        [
            (task_id, row)
            for task_id, row in a.latest_task_records().items()
            if row.get("parent_task_id") == plan_id
            and row.get("kind") in {"plan_step", "plan_summary"}
        ],
        key=lambda item: item[1].get("order", 0),
    )
    assert [row["status"] for _task_id, row in steps] == ["completed", "completed", "created", "created"], steps
    mutual_step_id = steps[2][0]
    intro_children_on_mutual = [
        row for row in a.latest_task_records().values()
        if row.get("parent_task_id") == mutual_step_id and row.get("kind") == "subagent_task"
    ]
    assert intro_children_on_mutual == [], intro_children_on_mutual
    for _ in range(6):
        drain_ui(state)
    latest = a.latest_task_records()
    assert latest[mutual_step_id]["status"] == "created", latest[mutual_step_id]
    assert latest[steps[3][0]]["status"] == "created", latest[steps[3][0]]
    assert main_agent.prompts, main_agent.prompts
    continuation_prompt, continuation_source = main_agent.prompts[0]
    assert continuation_source == "ga-tui:auto_plan_continue", main_agent.prompts
    next_line = next(line for line in continuation_prompt.splitlines() if line.startswith("Next unblocked step:"))
    assert "两个代理互相聊天对话" in next_line, continuation_prompt


def assert_control_result_continues_intermediate_workflow_step() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_control_continue_")
    retarget_harness(root)
    install_fake_agent_runtime()
    main_agent = SequencedFakeAgent([
        (
            "开始执行计划。第1步：创建新闻管家持久 agent。\n"
            + ga_control(create_agent_action(
                "新闻管家",
                persistent=True,
                profile="负责 RSS 信息源、每日新闻拉取、质量筛选和报纸排版。",
            ) | {"continue_after": True})
        ),
        "收到控制结果，继续后续阶段，本测试不再发控制块。",
    ])
    state = a.State(agent=main_agent)
    state.running = True
    assert a.start_main_agent_task(
        state,
        "做吧",
        source="user",
        visible_user_text="做吧",
        remember_user=True,
        clear_history=True,
    )
    for _ in range(5):
        drain_ui(state)
    assert len(main_agent.prompts) == 2, main_agent.prompts
    continuation_prompt, continuation_source = main_agent.prompts[1]
    assert continuation_source == "ga-tui:auto_control_continue", main_agent.prompts
    assert "Control results:" in continuation_prompt, continuation_prompt
    assert "新闻管家" in continuation_prompt, continuation_prompt
    assert "Continue the user-approved workflow yourself" in continuation_prompt, continuation_prompt
    assert any("自动续跑主控：控制块已执行" in msg.content for msg in state.messages if msg.role == "system"), state.messages
    news_agent = a.resolve_subagent(state, "新闻管家")
    assert news_agent is not None, state.subagents
    assert news_agent.persistent is True, news_agent


def assert_top_bar_header_requested_fields() -> None:
    agent = ContextFakeAgent()
    agent.log_path = "/tmp/model_responses/session-alpha.jsonl"
    state = a.State(agent=agent)
    state.messages = [
        a.Message("system", "boot"),
        a.Message("user", "first"),
        a.Message("assistant", "reply"),
        a.Message("user", "second"),
    ]
    expected_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(0))
    home_header = a.top_bar_header(state, timestamp=0)
    assert "主 agent 主页" in home_header, home_header
    assert "当前轮次: 2" in home_header, home_header
    state.selected_session = "main"
    header = a.top_bar_header(state, timestamp=0)
    assert header == f"当前时间: {expected_time} | 会话ID: session-alpha.jsonl | 当前轮次: 2", header
    for removed_field in ("GenericAgent", "curses TUI", "open:", "view:", "hist:", "fold:", "md:"):
        assert removed_field not in header, header

    state.history_ui_path = "/tmp/model_responses/restored-session.jsonl"
    state.history_ui_loaded_rounds = 3
    state.history_ui_total_rounds = 9
    state.history_ui_loading = True
    restored_header = a.top_bar_header(state, timestamp=0)
    assert "会话ID: restored-session.jsonl" in restored_header, restored_header
    assert "当前轮次: 3/9..." in restored_header, restored_header

    sub = a.SubAgentRuntime(agent_id="agent-123", name="Verifier", home="/tmp/subagent", role="verifier")
    sub.messages = [a.Message("user", "check this"), a.Message("assistant", "done")]
    state.subagents[sub.agent_id] = sub
    state.selected_session = sub.agent_id
    subagent_header = a.top_bar_header(state, timestamp=0)
    assert "子 agent: Verifier" in subagent_header, subagent_header
    assert "会话ID: agent-123" in subagent_header, subagent_header
    assert "当前轮次: 1" in subagent_header, subagent_header
    rendered = a.message_lines_cached(state, 80)
    assert any(line.text.startswith("AI:") for line in rendered), [line.text for line in rendered]
    assert not any(line.text.startswith("Verifier:") for line in rendered), [line.text for line in rendered]


def assert_long_secret_render_reuses_stable_message_blocks() -> None:
    state = a.State(agent=None)
    state.secret_vault.unlocked = True
    state.secret_vault.session_id = "long_secret"
    state.selected_session = a.secret_session_sidebar_key("long_secret")
    for idx in range(80):
        state.messages.append(a.Message("user", f"secret user {idx} " + ("x" * 120)))
        state.messages.append(a.Message("assistant", f"secret assistant {idx} " + ("y" * 160)))
    state.messages.append(a.Message("assistant", "streaming response", done=False))

    a.message_lines_cached(state, 80)
    scope = a.display_scope_key(state)
    scoped_meta = a.scoped_subagent_meta_keys(scope, state.expanded_subagent_meta)
    stable_key = a.message_render_cache_key(
        state.messages[0],
        0,
        80,
        state.fold_process,
        state.markdown,
        0,
        scope,
        state.expanded_process_groups,
        state.expanded_process_turns,
        scoped_meta,
    )
    streaming_key_frame0 = a.message_render_cache_key(
        state.messages[-1],
        len(state.messages) - 1,
        80,
        state.fold_process,
        state.markdown,
        0,
        scope,
        state.expanded_process_groups,
        state.expanded_process_turns,
        scoped_meta,
    )
    stable_block = state.message_block_cache[stable_key]
    streaming_block = state.message_block_cache[streaming_key_frame0]
    assert streaming_key_frame0 in state.message_block_cache, state.message_block_cache.keys()

    state.run_frame = 1
    a.message_lines_cached(state, 80)
    assert state.message_block_cache[stable_key] is stable_block
    streaming_key_frame1 = a.message_render_cache_key(
        state.messages[-1],
        len(state.messages) - 1,
        80,
        state.fold_process,
        state.markdown,
        1,
        scope,
        state.expanded_process_groups,
        state.expanded_process_turns,
        scoped_meta,
    )
    assert streaming_key_frame1 == streaming_key_frame0
    assert streaming_key_frame1 in state.message_block_cache, state.message_block_cache.keys()
    assert state.message_block_cache[streaming_key_frame1] is streaming_block


def assert_running_indicator_uses_lightweight_row_refresh() -> None:
    state = a.State(agent=None)
    state.selected_session = "main"
    state.status = "running"
    state.messages.append(a.Message("assistant", "streaming response", done=False))
    screen = FakeDrawScreen()

    a.draw_main(screen, state, height=40, width=120, sidebar_w=30, rightbar_w=0)
    assert state.running_indicator_rect is not None
    assert state.input_cursor_screen is not None
    assert any(call[2].strip() == a.running_indicator(0) for call in screen.calls), screen.calls

    line_cache_key = state.line_cache_key
    block_cache_ids = {key: id(value) for key, value in state.message_block_cache.items()}
    screen.calls.clear()
    screen.moves.clear()
    screen.refresh_count = 0

    state.run_frame = 1
    assert a.draw_running_indicator_frame(screen, state) is True
    assert state.line_cache_key == line_cache_key
    assert {key: id(value) for key, value in state.message_block_cache.items()} == block_cache_ids
    assert len(screen.calls) == 1, screen.calls
    assert screen.calls[0][2].strip() == a.running_indicator(1), screen.calls
    assert screen.refresh_count == 1
    assert screen.moves[-1] == state.input_cursor_screen


def assert_stream_queue_coalesces_burst_updates() -> None:
    state = a.State(agent=None)
    target = a.StreamTarget("active")
    dq: queue.Queue = queue.Queue()
    for chunk in ("a", "b", "c", "d", "e"):
        dq.put({"next": chunk})
    dq.put({
        "done": "abcde",
        "usage": {"requests": 1, "input": 2, "output": 3, "cache_create": 0, "cache_read": 0},
    })
    old_interval = a.STREAM_UI_FLUSH_INTERVAL
    try:
        a.STREAM_UI_FLUSH_INTERVAL = 3600.0
        a.consume_queue(state, target, 7, dq)
    finally:
        a.STREAM_UI_FLUSH_INTERVAL = old_interval
    items: list[tuple] = []
    while not state.ui_queue.empty():
        items.append(state.ui_queue.get_nowait())
    stream_items = [item for item in items if item[0] == "stream"]
    usage_items = [item for item in items if item[0] == "token_usage"]
    assert len(stream_items) == 2, stream_items
    assert stream_items[0] == ("stream", target, 7, "a", False), stream_items
    assert stream_items[-1] == ("stream", target, 7, "abcde", True), stream_items
    assert usage_items and usage_items[0][1:4] == ("stream", target, 7), items


def assert_secret_native_restore_hydrates_backend_context_blocks() -> None:
    marker = "restart-secret-context-marker"
    agent = ContextCheckingFakeAgent(marker)
    state = a.State(agent=agent)
    state.running = True
    state.secret_vault.unlocked = True
    state.secret_vault.session_id = "secret_restart"
    state.secret_vault.key = b"x" * 32
    state.messages = [a.Message("user", marker), a.Message("assistant", "previous secret answer")]

    a.restore_backend_from_secret_messages(state.agent, state.messages)
    for client in state.agent.llmclients:
        history = client.backend.history
        assert history and marker in json.dumps(history, ensure_ascii=False), history
        assert all(isinstance(row.get("content"), list) for row in history), history
        assert all(
            isinstance(block, dict) and block.get("type") == "text"
            for row in history
            for block in row.get("content", [])
        ), history

    old_secret_network_gate = a.secret_network_gate
    try:
        a.secret_network_gate = lambda _state=None, operation="secret_network": a.PolicyDecision(
            decision_id="policy_secret_restart_allowed",
            action="secret_network",
            subject="orchestrator.main",
            role="orchestrator",
            status="allowed",
            allowed=True,
            approval_required=False,
            approval_required_for="",
            risk="low",
            reason="test",
            source=operation,
            target="secret_vault",
        )
        assert a.start_main_agent_task(state, "继续", source="user", visible_user_text="继续")
        drain_ui(state)
        assert state.messages[-1].content == "context ok", state.messages[-1].content
    finally:
        a.secret_network_gate = old_secret_network_gate


def assert_temp_session_is_non_persistent() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_temp_session_")
    retarget_harness(root)
    install_fake_agent_runtime()
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)
    agent = FakeLLMAgent()
    normal_path = a.new_session_log_path()
    a.set_agent_log_path(agent, normal_path)
    state = a.State(agent=agent)
    state.running = True
    a.bind_agent_token_session(state, agent)

    a.submit(state, "/temp")
    assert state.temporary_session is True
    assert state.current_title == "临时会话"
    assert state.selected_session == "temp"
    assert a.agent_log_path_is_devnull(state.agent)
    assert a.agent_log_path(state.agent) == os.devnull
    assert state.agent.llmclient.log_path == os.devnull
    assert state.agent.llmclient.backend.log_path == os.devnull
    assert a.active_ui_session_path(state) == ""
    assert a.active_ui_session_key(state) == ""
    assert "会话ID: temp" in a.top_bar_header(state, timestamp=0)
    assert a.display_scope_key(state) == "session:temp"
    assert any(cmd == "/temp" for cmd, _args, _desc, _sendable in a.command_matches("/te", state))

    a.add_system(state, "Agent 控制结果：\n- temp control result", persist=True, kind="agent_control_result")
    assert a.load_session_meta_registry() == {}
    rename_result = a.rename_current_session(state, "Scratch")
    assert "不会持久化" in rename_result, rename_result
    assert state.current_title == "Scratch"
    assert a.load_session_meta_registry() == {}

    target = a.create_subagent(state, "Temp Memory Target", role="memory_curator", persistent=True)
    memory_result = a.queue_curated_memory_candidate(state, target, "stable long-term preference", source="temp-test")
    assert "临时会话" in memory_result, memory_result
    assert a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH) == []
    assert a.read_jsonl(a.AGENT_APPROVALS_PATH) == []

    a.submit(state, "/new")
    assert state.temporary_session is False
    assert state.selected_session == a.MAIN_HOME_SESSION_KEY
    assert not a.agent_log_path_is_devnull(state.agent)
    assert os.path.basename(a.agent_log_path(state.agent)).startswith("model_responses_")


def assert_new_agent_uses_shuheng_history_dir() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_new_agent_history_")
    retarget_harness(root)
    old_registry = a.agent_runtime_registry

    class FakeAdapter:
        provider_id = "fake"

        def create_agent(self) -> FakeLLMAgent:
            return FakeLLMAgent()

        def prepare_agent(self, agent: FakeLLMAgent, *, state=None) -> None:
            del agent, state

        def start_agent(self, agent: FakeLLMAgent, *, thread_name: str = "") -> None:
            del agent, thread_name

    def fake_registry(*, write_memory_prompt_file: bool = True) -> a.RuntimeRegistry:
        del write_memory_prompt_file
        registry = a.RuntimeRegistry(default_provider_id="fake")
        registry.register(FakeAdapter())
        return registry

    try:
        a.agent_runtime_registry = fake_registry
        agent = a.new_agent()
    finally:
        a.agent_runtime_registry = old_registry
    path = a.agent_log_path(agent)
    assert a.path_is_within(path, a.MODEL_RESPONSES_DIR), path
    assert os.path.basename(path).startswith("model_responses_"), path
    assert agent.llmclient.log_path == path
    assert agent.llmclient.backend.log_path == path


def assert_ohmypi_main_turn_persists_model_response_history() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_omp_history_")
    retarget_harness(root)
    os.makedirs(a.MODEL_RESPONSES_DIR, exist_ok=True)
    agent = RuntimeCaptureFakeAgent()
    path = a.new_session_log_path()
    a.set_agent_log_path(agent, path)
    if a.session_names is not None:
        a.session_names.set_name(path, "OMP Transcript Smoke")
    state = a.State(agent=agent)
    state.running = True

    assert a.start_main_agent_task(
        state,
        "今天的历史会话应该出现",
        source="user",
        visible_user_text="今天的历史会话应该出现",
        remember_user=True,
        clear_history=True,
    )
    drain_ui(state)

    assert state.status == "idle", state.status
    assert state.messages[-1].content == "runtime ok", state.messages[-1]
    content = Path(path).read_text(encoding="utf-8")
    pairs = a._pairs(content)
    assert pairs, content
    assert a._user_text(pairs[-1][0]) == "今天的历史会话应该出现", pairs[-1][0]
    assert "runtime ok" in a._format_response_segment(pairs[-1][1], {}), pairs[-1][1]
    assert any(row[0] == path for row in state.history), state.history
    meta = a.load_session_meta_registry().get(os.path.basename(path), {})
    assert meta.get("rounds") == 1, meta
    assert meta.get("last_user_at"), meta


def run_checks() -> None:
    assert_scheduler_module_boundary()
    assert_genericagent_provider_module_boundary()
    assert_ohmypi_provider_module_boundary()
    assert_shuheng_brand_entrypoints()
    assert_shuheng_history_storage_owned()
    assert_token_usage_registry_prunes_removed_history()
    assert_shuheng_workspace_memory_context()
    assert_shared_user_profile_context_is_global()
    assert_shuheng_bootstraps_legacy_state_without_mutating_source()
    assert_ohmypi_runtime_registry()
    assert_ohmypi_memory_prompt_and_command()
    assert_ohmypi_rpc_command_discovers_user_bun_binary()
    assert_ohmypi_isolated_runtime_settings()
    assert_model_context_window_surface()
    assert_ohmypi_permission_profiles()
    assert_ohmypi_runtime_context_pack_is_not_repeated()
    assert_ohmypi_rpc_extension_approval_bridge()
    assert_ohmypi_rpc_queue_mapping()
    assert_ohmypi_rpc_usage_tracking()
    assert_ohmypi_native_session_state_and_restore()
    assert_ohmypi_rpc_final_text_fallback()
    assert_ohmypi_rpc_streamed_final_text_dedupes_terminal_message()
    assert_ohmypi_rpc_waits_for_agent_end_before_next_prompt()
    assert_ohmypi_rpc_tool_use_turn_end_waits_for_final_answer()
    assert_ohmypi_rpc_host_tool_followup_timeout_finishes_stalled_turn()
    assert_ohmypi_rpc_host_tool_followup_activity_waits_for_final_answer()
    assert_ohmypi_rpc_host_tool_followup_ignores_pre_tool_progress_for_fallback()
    assert_ohmypi_rpc_process_blocks_fold_like_genericagent()
    assert_ohmypi_rpc_env_model_switch_and_error_mapping()
    assert_ohmypi_host_tool_bridge()
    assert_ohmypi_tui_query_host_tool_contract()
    assert_ohmypi_tui_proposal_host_tool_contract()
    assert_agent_bridge_contract_and_omp_plugin()
    assert_ohmypi_memory_candidate_signal_filters()
    assert_ohmypi_missing_binary_and_abort()
    assert_top_bar_header_requested_fields()
    assert_long_secret_render_reuses_stable_message_blocks()
    assert_running_indicator_uses_lightweight_row_refresh()
    assert_stream_queue_coalesces_burst_updates()
    assert_secret_native_restore_hydrates_backend_context_blocks()
    assert_restored_process_group_folds_intermediate_speech()
    assert_mixed_omp_process_turns_fold_into_single_group()
    assert_process_group_keeps_substantive_reply_before_housekeeping()
    assert_process_group_keeps_enumeration_before_summary_housekeeping()
    assert_process_detail_line_not_swallowed_by_code_fence()
    assert_single_search_turn_keeps_final_reply_visible()
    assert_ask_user_tool_use_input_payload_visible()
    assert_ask_user_multiline_tool_args_payload_visible()
    assert_model_owned_session_rename_is_title_path()
    assert_aux_mouse_buttons_do_not_start_selection()
    assert_subagent_result_context_update_from_notice()
    assert_live_subagent_result_reaches_main_context()
    assert_subagent_runtime_errors_fail_and_release_model_switch()
    assert_selected_subagent_chat_is_direct_session()
    assert_running_main_input_is_queued_and_interruptible()
    assert_agent_create_respects_explicit_lifecycle_and_reuse_policy()
    assert_subagent_dedicated_skills_are_agent_scoped()
    assert_persistent_agent_dashboard_home_pages()
    assert_temp_subagent_current_fallback_is_reloadable()
    assert_tui_query_tools_expose_dashboard_state()
    assert_historical_subagent_result_quarantine_backfill()
    assert_recent_sessions_use_last_message_activity()
    assert_history_curator_skill_uses_progressive_disclosure()
    assert_ohmypi_process_summary_does_not_title_history()
    assert_ohmypi_local_category_fallback_for_sidebar()
    assert_missing_source_history_rows_restore_from_l4_archive()
    assert_self_intro_does_not_consume_mutual_chat_step()
    assert_control_result_continues_intermediate_workflow_step()
    assert_temp_session_is_non_persistent()
    assert_new_agent_uses_shuheng_history_dir()
    assert_ohmypi_main_turn_persists_model_response_history()

    root = tempfile.mkdtemp(prefix="ga_tui_policy_check_")
    retarget_harness(root)
    install_fake_agent_runtime()
    state = a.State(agent=None)
    state.running = True

    llm_entries = [
        a.LLMConfigEntry("native_oai_config", "native_oai", {"name": "alpha", "apikey": "k", "apibase": "https://example.invalid/v1", "model": "model-alpha"}),
        a.LLMConfigEntry("native_oai_config_1", "native_oai", {"name": "beta", "apikey": "k", "apibase": "https://example.invalid/v1", "model": "model-beta"}),
    ]
    llm_state = a.State(agent=FakeLLMAgent())
    llm_state.running = True
    ok_switch, switch_msg = a.switch_agent_to_entry(llm_state, llm_entries[1])
    assert ok_switch, switch_msg
    assert llm_state.agent.llm_no == 2
    assert llm_state.agent.get_llm_name(model=True) == "model-beta"
    a.new_current_session(llm_state, keep_running=False)
    assert llm_state.agent.llm_no == 0
    assert llm_state.agent.get_llm_name(model=True) == "model-default"

    old_mykey_path = a.mykey_path
    try:
        mykey_file = os.path.join(root, "mykey.py")
        a.mykey_path = lambda: mykey_file
        mixin = {"llm_nos": ["alpha"], "max_retries": 10, "base_delay": 0.5}
        ok_default, default_msg = a.save_default_model(llm_entries, mixin, [], 1)
        assert ok_default, default_msg
        loaded_entries, loaded_mixin, _preserved, load_error = a.load_llm_config_entries()
        assert load_error == "", load_error
        assert [a.config_display_name(entry) for entry in loaded_entries] == ["alpha", "beta"]
        assert loaded_mixin["llm_nos"] == ["beta"], loaded_mixin
        old_save_llm_config_entries = a.save_llm_config_entries
        old_reload_agent_llms = a.reload_agent_llms
        try:
            calls: list[str] = []

            def fake_save_llm_config_entries(_entries, _mixin, _preserved):
                calls.append("save")
                return True, "saved"

            def fake_reload_agent_llms(_state, *, preserve_current: bool = False):
                calls.append(f"reload:{preserve_current}")
                return True, "reloaded"

            a.save_llm_config_entries = fake_save_llm_config_entries
            a.reload_agent_llms = fake_reload_agent_llms
            ok_manager_save, manager_save_msg = a.save_model_manager_entries(llm_state, llm_entries, mixin, [])
            assert ok_manager_save, manager_save_msg
            assert manager_save_msg == "reloaded"
            assert calls == ["save", "reload:True"], calls

            calls = []

            def fake_failed_save_llm_config_entries(_entries, _mixin, _preserved):
                calls.append("save")
                return False, "save failed"

            a.save_llm_config_entries = fake_failed_save_llm_config_entries
            ok_manager_save, manager_save_msg = a.save_model_manager_entries(llm_state, llm_entries, mixin, [])
            assert not ok_manager_save
            assert manager_save_msg == "save failed"
            assert calls == ["save"], calls
        finally:
            a.save_llm_config_entries = old_save_llm_config_entries
            a.reload_agent_llms = old_reload_agent_llms
        ok_recent, recent_msg = a.remember_recent_model_entry(llm_entries[1], llm_entries)
        assert ok_recent, recent_msg
        ok_recent, recent_msg = a.remember_recent_model_entry(llm_entries[0], llm_entries)
        assert ok_recent, recent_msg
        assert a.load_recent_model_names(llm_entries)[:2] == ["alpha", "beta"]
        assert a.recent_model_entry_indices(llm_entries, ["alpha", "beta"]) == [0, 1]
        assert a.next_recent_entry_index(llm_entries, ["alpha", "beta"], 0) == 1
        sub_state = a.State(agent=FakeLLMAgent())
        sub = a.create_subagent(sub_state, "Persistent Model Agent", role="researcher", persistent=True)
        sub.agent = FakeLLMAgent()
        ok_sub_model, sub_model_msg = a.set_subagent_default_model(sub_state, sub, "beta")
        assert ok_sub_model, sub_model_msg
        assert sub.default_model == "beta"
        assert sub.agent.llm_no == 2
        assert sub.agent.get_llm_name(model=True) == "model-beta"
        assert a.load_subagent_meta(sub.agent_id).get("default_model") == "beta"
        reloaded = a.State(agent=FakeLLMAgent())
        assert a.load_subagents(reloaded) is True
        reloaded_sub = a.resolve_subagent(reloaded, sub.agent_id)
        assert reloaded_sub is not None
        assert reloaded_sub.default_model == "beta"
        ok_sub_model, sub_model_msg = a.set_subagent_default_model(sub_state, sub, "inherit")
        assert ok_sub_model, sub_model_msg
        assert sub.default_model == ""
        assert sub.agent.llm_no == 2

        temp_sub = a.create_subagent(sub_state, "Temp Model Agent", role="researcher", persistent=False)
        temp_sub.agent = FakeLLMAgent()
        ok_temp_model, temp_model_msg = a.set_subagent_default_model(sub_state, temp_sub, "alpha")
        assert ok_temp_model, temp_model_msg
        assert temp_sub.default_model == "alpha"
        assert temp_sub.agent.llm_no == 1
        assert a.load_subagent_meta_file(os.path.join(temp_sub.home, "meta.json")).get("default_model") == "alpha"
        temp_reloaded = a.State(agent=FakeLLMAgent())
        assert a.load_subagents(temp_reloaded) is True
        temp_reloaded_sub = a.resolve_subagent(temp_reloaded, temp_sub.agent_id)
        assert temp_reloaded_sub is not None
        assert temp_reloaded_sub.default_model == "alpha"

        panel_state = a.State(agent=FakeLLMAgent())
        panel_state.running = True
        panel_first = a.create_subagent(panel_state, "Panel First", role="researcher", persistent=True)
        panel_second = a.create_subagent(panel_state, "Panel Second", role="researcher", persistent=True)
        panel_state.selected_session = panel_first.agent_id
        panel_targets = a.model_manager_subagent_targets(panel_state)
        assert [sub.agent_id for sub in panel_targets[:2]] == [panel_first.agent_id, panel_second.agent_id], panel_targets

        old_redraw = a.redraw
        old_modal_read_key = a.modal_read_key
        old_draw_model_manager = a.draw_model_manager
        try:
            pressed = iter(["g", "o", "g", "c", "q"])
            drawn_targets: list[str] = []

            def fake_modal_read_key(_stdscr):
                return next(pressed)

            def fake_draw_model_manager(*_args, **kwargs):
                target = kwargs.get("subagent_target")
                drawn_targets.append(target.agent_id if target is not None else "")

            a.redraw = lambda _stdscr, _state: None
            a.modal_read_key = fake_modal_read_key
            a.draw_model_manager = fake_draw_model_manager
            a.open_model_manager(TimeoutFakeScreen(), panel_state, manage_configs=True)
        finally:
            a.redraw = old_redraw
            a.modal_read_key = old_modal_read_key
            a.draw_model_manager = old_draw_model_manager
        assert drawn_targets[:3] == [panel_first.agent_id, panel_first.agent_id, panel_second.agent_id], drawn_targets
        assert panel_first.default_model == "alpha"
        assert panel_second.default_model == ""
        assert a.load_subagent_meta(panel_first.agent_id).get("default_model") == "alpha"
        assert a.load_subagent_meta(panel_second.agent_id).get("default_model") == ""
    finally:
        a.mykey_path = old_mykey_path

    old_probe_models = a.probe_models_for_config
    try:
        a.probe_models_for_config = lambda _cfg_type, _cfg, timeout=12.0: (True, ["model-alpha", "model-gamma"], "ok")
        ok_probe, added_models, probe_msg = a.probe_and_merge_models(llm_entries[0], llm_entries)
        assert ok_probe, probe_msg
        assert [entry.cfg["model"] for entry in added_models] == ["model-gamma"], added_models
        manual_entry = a.LLMConfigEntry(
            "native_oai_config_2",
            "native_oai",
            {"name": "manual", "apikey": "k", "apibase": "https://manual.example.invalid/v1", "model": "model-manual"},
        )
        ok_manual, saved_manual, manual_msg = a.manual_entry_after_probe_failure(manual_entry, llm_entries, "HTTP 404")
        assert ok_manual, manual_msg
        assert saved_manual is not None
        assert saved_manual.cfg["model"] == "model-manual", saved_manual
        assert "/models 提取失败" in manual_msg, manual_msg
        ok_manual, saved_manual, manual_msg = a.manual_entry_after_probe_failure(llm_entries[0], llm_entries, "HTTP 404")
        assert not ok_manual
        assert saved_manual is None
        assert "已存在" in manual_msg, manual_msg
    finally:
        a.probe_models_for_config = old_probe_models
    old_config_providers = a.CONFIG_PROVIDERS
    try:
        a.CONFIG_PROVIDERS = [
            {"id": "anthropic", "name": "Anthropic Claude", "type": "native_claude", "template": {"name": "anthropic-direct", "apibase": "https://api.anthropic.com", "model": "claude-sonnet"}},
            {"id": "openai", "name": "OpenAI GPT", "type": "native_oai", "template": {"name": "gpt-native", "apibase": "https://api.openai.com/v1", "model": "gpt-5.5"}},
            {"id": "deepseek", "name": "DeepSeek", "type": "native_oai", "template": {"name": "deepseek", "apibase": "https://api.deepseek.com", "model": "deepseek-v4-flash"}},
            {"id": "qwen", "name": "阿里通义千问", "type": "native_oai", "template": {"name": "qwen", "apibase": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"}},
            {"id": "minimax", "name": "MiniMax", "type": "native_claude", "template": {"name": "minimax", "apibase": "https://api.minimaxi.com/anthropic", "model": "MiniMax-M2.7"}},
        ]
        openai_entry = a.LLMConfigEntry("native_oai_config", "native_oai", {"name": "gpt-native", "apikey": "k", "apibase": "https://api.openai.com/v1", "model": "gpt-5.5"})
        deepseek_entry = a.LLMConfigEntry("native_oai_config_1", "native_oai", {"name": "deepseek", "apikey": "k", "apibase": "https://api.deepseek.com", "model": "deepseek-v4-flash"})
        custom_entry = a.LLMConfigEntry("native_oai_config_2", "native_oai", {"name": "alpha", "apikey": "k", "apibase": "https://api.example.invalid/v1", "model": "model-alpha"})
        minimax_entry = a.LLMConfigEntry("native_claude_config", "native_claude", {"name": "minimax", "apikey": "k", "apibase": "https://api.minimaxi.com/anthropic", "model": "MiniMax-M2.7"})
        assert a.model_entry_category(openai_entry) == "OpenAI"
        assert a.model_entry_category(deepseek_entry) == "DeepSeek"
        assert a.model_entry_category(custom_entry) == "example.invalid"
        provider_tabs = a.model_entry_categories([deepseek_entry, custom_entry])
        assert provider_tabs == ["Anthropic", "OpenAI", "DeepSeek", "Qwen", "example.invalid"]
        assert "MiniMax" not in provider_tabs
        assert "MiniMax" in a.model_entry_categories([minimax_entry])
        mixed_entries = [deepseek_entry, custom_entry, openai_entry]
        assert a.model_entry_indices_for_category(mixed_entries, "DeepSeek") == [0]
        assert a.model_entry_indices_for_category(mixed_entries, "example.invalid") == [1]
        assert a.model_entry_indices_for_category(mixed_entries, "OpenAI") == [2]
        recent_names = ["alpha", "deepseek"]
        manager_tabs = a.model_manager_categories(mixed_entries, recent_names)
        assert manager_tabs == ["常用", "Anthropic", "OpenAI", "DeepSeek", "Qwen", "example.invalid"], manager_tabs
        assert a.model_manager_entry_indices_for_category(mixed_entries, "常用", recent_names) == [1, 0]
        assert a.model_manager_category_for_index(mixed_entries, 1, recent_names) == "常用"
        health = {a.model_health_key(deepseek_entry): (False, "offline")}
        assert a.model_manager_category_status(mixed_entries, "Anthropic", health, recent_names) == "empty"
        assert a.model_manager_category_status(mixed_entries, "OpenAI", health, recent_names) == "configured"
        assert a.model_manager_category_status(mixed_entries, "DeepSeek", health, recent_names) == "warning"
        assert a.model_manager_category_status(mixed_entries, "常用", health, recent_names) == "warning"
        manager_index = a.model_manager_category_index(mixed_entries, recent_names, health)
        assert manager_index.indices_by_category["常用"] == [1, 0]
        assert manager_index.status_by_category["DeepSeek"] == "warning"
        model_draw_screen = FakeDrawScreen()
        model_draw_state = a.State(agent=FakeLLMAgent())
        a.draw_model_manager(
            model_draw_screen,
            model_draw_state,
            mixed_entries,
            {"llm_nos": ["deepseek"]},
            2,
            "",
            health,
            recent_names=recent_names,
            active_category="OpenAI",
            category_index=manager_index,
        )
        draw_texts = [text for _y, _x, text, _attr in model_draw_screen.calls]
        assert any(text == "供应商" for text in draw_texts), draw_texts
        assert not any("供应商 Tabs:" in text for text in draw_texts), draw_texts
        assert any("子代理默认:" in text for text in draw_texts), draw_texts
        assert any("g子代理默认" in text and "o目标" in text for text in draw_texts), draw_texts
        assert any("  常用 (2)" in text for text in draw_texts), draw_texts
        assert any("  DeepSeek (1)" in text for text in draw_texts), draw_texts
        assert any("› OpenAI (1)" in text for text in draw_texts), draw_texts
        provider_rows = [(y, x, text) for y, x, text, _attr in model_draw_screen.calls if text in {"  常用 (2)", "› OpenAI (1)", "  DeepSeek (1)"}]
        row_attrs = {text: attr for _y, _x, text, attr in model_draw_screen.calls if text in {"  常用 (2)", "  Anthropic", "  DeepSeek (1)"}}
        assert len(provider_rows) == 3, provider_rows
        assert len({x for _y, x, _text in provider_rows}) == 1, provider_rows
        assert len({y for y, _x, _text in provider_rows}) == 3, provider_rows
        assert row_attrs["  Anthropic"] == a.model_manager_category_attr(mixed_entries, "Anthropic", health, recent_names), row_attrs
        assert row_attrs["  DeepSeek (1)"] == a.model_manager_category_attr(mixed_entries, "DeepSeek", health, recent_names), row_attrs
        assert row_attrs["  常用 (2)"] == a.model_manager_category_attr(mixed_entries, "常用", health, recent_names), row_attrs
        old_model_entry_category = a.model_entry_category
        try:
            def fail_model_entry_category(_entry):
                raise AssertionError("draw_model_manager recalculated provider categories despite a supplied index")

            a.model_entry_category = fail_model_entry_category
            indexed_screen = FakeDrawScreen()
            a.draw_model_manager(
                indexed_screen,
                model_draw_state,
                mixed_entries,
                {"llm_nos": ["deepseek"]},
                2,
                "",
                health,
                recent_names=recent_names,
                active_category="OpenAI",
                category_index=manager_index,
            )
        finally:
            a.model_entry_category = old_model_entry_category
    finally:
        a.CONFIG_PROVIDERS = old_config_providers
    visible_commands = [cmd for cmd, _args, _desc, _sendable in a.COMMANDS]
    assert "/model" in visible_commands
    assert "/llm" not in visible_commands
    assert "/models" not in visible_commands
    assert [cmd for cmd, _args, _desc, _sendable in a.command_matches("/mo", state)] == ["/model"]
    assert a.command_matches("/ll", state) == []
    assert a.command_matches("/models", state) == []
    help_state = a.State(agent=ContextFakeAgent())
    a.submit(help_state, "/LlM")
    assert "管理模型配置" in help_state.messages[-1].content
    assert "/model" in help_state.messages[-1].content
    assert "兼容别名" in help_state.messages[-1].content
    a.submit(help_state, "/MODEL")
    assert "供应商" in help_state.messages[-1].content
    assert "默认新对话模型" in help_state.messages[-1].content
    a.submit(help_state, "/models")
    assert "兼容别名" in help_state.messages[-1].content
    old_open_model_manager = a.open_model_manager
    try:
        routed_manage_flags: list[bool] = []

        def fake_open_model_manager(_stdscr, _state: a.State, *, manage_configs: bool = False) -> None:
            routed_manage_flags.append(manage_configs)

        a.open_model_manager = fake_open_model_manager
        for command in ("/llm", "/model", "/models"):
            route_state = a.State(agent=ContextFakeAgent())
            route_state.input_text = command
            route_state.input_cursor = len(command)
            a.handle_key(object(), route_state, "\n")
            assert route_state.input_text == ""
        assert routed_manage_flags == [True, True, True]
    finally:
        a.open_model_manager = old_open_model_manager

    old_choose_exit_mode = a.choose_exit_mode
    try:
        def fake_choose_exit_mode(stdscr: TimeoutFakeScreen, _state: a.State, _labels: list[str], _selected: int = 0) -> str:
            stdscr.timeout(-1)
            return "cancel"

        exit_state = a.State(agent=ContextFakeAgent())
        exit_screen = TimeoutFakeScreen()
        a.choose_exit_mode = fake_choose_exit_mode
        a.request_exit(exit_screen, exit_state, selected=0)
        assert exit_state.running is True
        assert exit_state.last_error == "已取消退出。"
        assert exit_screen.timeouts[-1] == a.TUI_POLL_TIMEOUT_MS, exit_screen.timeouts
    finally:
        a.choose_exit_mode = old_choose_exit_mode

    assert any(cmd == "/Secret" for cmd, _args, _desc, _sendable in a.command_matches("/Sec", state))
    assert a.SECRET_VAULT_MIN_PASSWORD_CHARS == 8
    assert a.secret_password_policy_error("Aa1!aaaa") == ""
    assert "特殊字符" in a.secret_password_policy_error("Aa1aaaaa")
    assert a.parse_secret_import_args("") == ("delete", "current")
    assert a.parse_secret_import_args("archive 2") == ("archive", "2")
    assert a.parse_secret_import_args("删除 id:abc") == ("delete", "id:abc")
    assert any(cmd == "/toSecret" for cmd, _args, _desc, _sendable in a.command_matches("/toS", state))
    normal_busy_state = a.State(agent=ContextFakeAgent())
    normal_busy_state.running = True
    normal_busy_state.status = "running"
    normal_busy_state.active_task_id = 99
    busy_secret = a.begin_secret_unlock(normal_busy_state)
    assert "普通任务仍在运行" in busy_secret, busy_secret
    assert normal_busy_state.secret_vault.pending_action == ""
    lock_normal = a.lock_secret_vault(normal_busy_state, reason="normal-running")
    assert "已锁定" in lock_normal, lock_normal
    assert normal_busy_state.status == "running"
    assert normal_busy_state.active_task_id == 99
    assert "secret_enter" in a.default_policy_config()["rules"]
    assert "secret_decrypt" in a.default_policy_config()["rules"]
    assert "secret_import" in a.default_policy_config()["rules"]
    assert "secret_export" in a.default_policy_config()["rules"]
    old_proxy_env = {key: os.environ.get(key) for key in a.SECRET_PROXY_ENV_KEYS}
    proxy_state = a.State(agent=ContextFakeAgent())
    try:
        a.activate_secret_proxy_env(proxy_state, {"chain": ["tor"]})
        assert os.environ["ALL_PROXY"] == "socks5h://127.0.0.1:9050"
        assert os.environ["HTTPS_PROXY"] == "socks5h://127.0.0.1:9050"
        assert os.environ["NO_PROXY"] == ""
        a.restore_secret_proxy_env(proxy_state)
        for key, value in old_proxy_env.items():
            assert os.environ.get(key) == value, (key, os.environ.get(key), value)
    finally:
        for key, value in old_proxy_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    assert a.secret_write_json(state, "test", "locked", {"secret": "plaintext"})[0] is False
    begin_secret = a.begin_secret_unlock(state)
    assert state.secret_vault.pending_action in {"setup_password", "unlock"}, begin_secret
    short_secret = a.accept_secret_password_input(state, "short")
    assert "至少" in short_secret or "解锁失败" in short_secret, short_secret
    weak_secret = a.accept_secret_password_input(state, "lowercase1!")
    assert "大写字母" in weak_secret, weak_secret
    state.secret_vault.pending_action = "setup_password"
    slash_secret = a.accept_secret_password_input(state, "/Slash123!")
    assert "再次输入" in slash_secret, slash_secret
    slash_key_state = a.State(agent=ContextFakeAgent())
    slash_key_state.running = True
    slash_key_state.secret_vault.pending_action = "setup_password"
    a.set_input_text(slash_key_state, "/memory")
    opened_memory = False
    original_open_memory_viewer = a.open_memory_viewer
    try:
        def mark_memory_opened(*_args: object) -> None:
            nonlocal opened_memory
            opened_memory = True

        a.open_memory_viewer = mark_memory_opened
        a.handle_key(None, slash_key_state, "\n")
    finally:
        a.open_memory_viewer = original_open_memory_viewer
    assert opened_memory is False
    assert slash_key_state.secret_vault.pending_action == "setup_password"
    assert any("至少" in msg.content for msg in slash_key_state.messages), slash_key_state.messages
    state.secret_vault.pending_action = "unlock"
    decrypt_attempt = a.accept_secret_password_input(state, "not-the-right-secret-password")
    assert "解锁失败" in decrypt_attempt or "尚未初始化" in decrypt_attempt, decrypt_attempt
    assert any(row.get("action") == "secret_decrypt" for row in a.read_jsonl(a.AGENT_POLICY_DECISIONS_PATH))
    state.secret_vault.pending_action = ""
    old_chain = os.environ.pop(a.SECRET_NETWORK_CHAIN_ENV, None)
    old_tor = os.environ.pop(a.SECRET_TOR_SOCKS_ENV, None)
    old_auto_tor = os.environ.get(a.SECRET_AUTO_TOR_ENV)
    try:
        os.environ[a.SECRET_AUTO_TOR_ENV] = "0"
        network_decision = a.secret_network_gate(state, operation="test_secret_fail_closed")
        assert network_decision.allowed is False, network_decision
        assert "fail-closed" in network_decision.reason, network_decision.reason
        secret_agent = SequencedFakeAgent(["should not run"])
        secret_state = a.State(agent=secret_agent)
        secret_state.secret_vault.unlocked = True
        secret_state.secret_vault.session_id = "secret_fail_closed"
        started_secret = a.start_main_agent_task(
            secret_state,
            "secret prompt",
            source="user",
            visible_user_text="secret prompt",
            clear_history=True,
        )
        assert started_secret is False
        assert not secret_agent.prompts, secret_agent.prompts
        assert "APPROVAL_REQUIRED" not in secret_state.last_error, secret_state.last_error
        assert "fail-closed" in secret_state.last_error, secret_state.last_error
    finally:
        if old_chain is not None:
            os.environ[a.SECRET_NETWORK_CHAIN_ENV] = old_chain
        if old_tor is not None:
            os.environ[a.SECRET_TOR_SOCKS_ENV] = old_tor
        if old_auto_tor is None:
            os.environ.pop(a.SECRET_AUTO_TOR_ENV, None)
        else:
            os.environ[a.SECRET_AUTO_TOR_ENV] = old_auto_tor
    old_proxy_health = a.secret_proxy_endpoint_healthy
    old_chain = os.environ.pop(a.SECRET_NETWORK_CHAIN_ENV, None)
    old_tor = os.environ.pop(a.SECRET_TOR_SOCKS_ENV, None)
    old_auto_tor = os.environ.pop(a.SECRET_AUTO_TOR_ENV, None)
    auto_secret_state = a.State(agent=FakeLLMAgent())
    try:
        a.secret_proxy_endpoint_healthy = lambda endpoint, timeout=1.0: (True, f"ok:{endpoint}")
        assert a.secret_configured_proxy_chain() == ["tor"]
        auto_secret_state.running = True
        auto_secret_state.secret_vault.unlocked = True
        auto_secret_state.secret_vault.session_id = "secret_auto_network"
        auto_secret_state.agent.next_llm(2)
        auto_started = a.start_main_agent_task(
            auto_secret_state,
            "secret should use inherited llm",
            source="user",
            visible_user_text="secret should use inherited llm",
            remember_user=True,
            clear_history=True,
        )
        assert auto_started is True, auto_secret_state.last_error
        assert auto_secret_state.agent.prompts, auto_secret_state.agent.prompts
        assert auto_secret_state.agent.llm_no == 2
        assert auto_secret_state.agent.get_llm_name(model=True) == "model-beta"
        assert auto_secret_state.agent.log_path == os.devnull
        assert "secret should use inherited llm" not in auto_secret_state.input_history
        assert os.environ["ALL_PROXY"] == a.SECRET_DEFAULT_TOR_SOCKS
        assert os.environ["HTTPS_PROXY"] == a.SECRET_DEFAULT_TOR_SOCKS
        assert os.environ["NO_PROXY"] == ""
    finally:
        a.secret_proxy_endpoint_healthy = old_proxy_health
        a.restore_secret_proxy_env(auto_secret_state)
        if old_chain is not None:
            os.environ[a.SECRET_NETWORK_CHAIN_ENV] = old_chain
        if old_tor is not None:
            os.environ[a.SECRET_TOR_SOCKS_ENV] = old_tor
        if old_auto_tor is not None:
            os.environ[a.SECRET_AUTO_TOR_ENV] = old_auto_tor
        else:
            os.environ.pop(a.SECRET_AUTO_TOR_ENV, None)
    state.secret_vault.unlocked = True
    assert a.secret_blocks_normal_command(state, "") is False
    assert a.secret_blocks_normal_command(state, "   ") is False
    assert a.secret_blocks_normal_command(state, "/tasks") is True
    assert a.secret_blocks_normal_command(state, "/agent new leak | plaintext profile") is False

    stale_restore_state = a.State(agent=FakeLLMAgent())
    stale_restore_state.restore_token = 17
    stale_restore_state.secret_vault.unlocked = True
    stale_restore_state.secret_vault.session_id = "secret_visible"
    stale_restore_state.current_title = "Secret: Visible"
    stale_restore_state.selected_session = a.secret_session_sidebar_key("secret_visible")
    stale_restore_state.messages = [a.Message("user", "secret-visible-message")]
    stale_restore_state.ui_queue.put((
        "restore_done",
        17,
        "/tmp/normal-game-session.txt",
        ("/tmp/normal-game-session.txt", 0.0),
        [a.Message("user", "ordinary-game-message")],
        "",
        0.0,
        1,
        1,
        1,
    ))
    a.process_ui_queue(stale_restore_state)
    assert [msg.content for msg in stale_restore_state.messages] == ["secret-visible-message"]
    assert stale_restore_state.current_title == "Secret: Visible"
    assert stale_restore_state.selected_session == a.secret_session_sidebar_key("secret_visible")
    assert stale_restore_state.history_ui_path == ""
    if a.secret_crypto_available():
        ok, secret_key, secret_created = a.secret_create_vault("Aa1!aaaa")
        assert ok and secret_key, secret_created
        state.secret_vault.unlocked = True
        state.secret_vault.key = secret_key
        state.secret_vault.session_id = "secret_subagents"
        state.subagents = {}
        old_secret_network_gate = a.secret_network_gate
        old_ensure_subagent_agent = a.ensure_subagent_agent
        secret_agent = SequencedFakeAgent(["child result marker"])
        try:
            a.secret_network_gate = lambda _state=None, operation="secret_network": a.PolicyDecision(
                decision_id="policy_secret_subagent_allowed",
                action="secret_network",
                subject="orchestrator.main",
                role="",
                status="allowed",
                allowed=True,
                approval_required=False,
                approval_required_for="",
                risk="critical",
                reason=f"test allow {operation}",
            )
            a.ensure_subagent_agent = lambda _state, sub: secret_agent
            ledger_before = list(a.read_jsonl(a.AGENT_TASK_LEDGER_PATH))
            mail_before = list(a.read_jsonl(a.AGENT_MAIL_PATH))
            artifact_before = sorted(str(path) for path in Path(a.AGENT_ARTIFACTS_DIR).glob("**/*")) if Path(a.AGENT_ARTIFACTS_DIR).exists() else []
            secret_subagent = a.create_subagent(state, "Secret Worker", "secret profile marker", role="researcher", persistent=True)
            assert secret_subagent.security_context == "secret"
            assert secret_subagent.home.startswith("secret://subagents/")
            assert not (Path(a.SUBAGENTS_DIR) / secret_subagent.agent_id).exists()
            secret_subagent_result = a.start_subagent_task(state, secret_subagent, "child task marker", source="test")
            assert "已启动 Secret 子 agent" in secret_subagent_result, secret_subagent_result
            drain_ui(state)
            assert secret_subagent.status == "idle"
            assert any("child result marker" in msg.content for msg in state.messages), state.messages
            assert a.read_jsonl(a.AGENT_TASK_LEDGER_PATH) == ledger_before
            assert a.read_jsonl(a.AGENT_MAIL_PATH) == mail_before
            artifact_after = sorted(str(path) for path in Path(a.AGENT_ARTIFACTS_DIR).glob("**/*")) if Path(a.AGENT_ARTIFACTS_DIR).exists() else []
            assert artifact_after == artifact_before
            secret_files = list((Path(a.SECRET_VAULT_SESSIONS_DIR) / a.SECRET_SUBAGENT_SESSION_ID).glob("**/*.secret"))
            assert secret_files, "missing encrypted Secret subagent records"
            for item in secret_files:
                raw = item.read_bytes()
                assert b"secret profile marker" not in raw
                assert b"child task marker" not in raw
                assert b"child result marker" not in raw
            state.subagents = {}
            assert a.load_subagents(state) is True
            loaded_secret_subagent = a.resolve_subagent(state, secret_subagent.agent_id)
            assert loaded_secret_subagent is not None
            assert loaded_secret_subagent.profile_text.strip() == "secret profile marker"
            assert "Secret Worker Memory" in loaded_secret_subagent.memory_text
            memory_result = a.append_subagent_memory(loaded_secret_subagent, "secret persistent memory marker", source="test", state=state)
            assert "已写入 Secret 子 agent 加密记忆" in memory_result, memory_result
            memory_files = list((Path(a.SECRET_VAULT_SESSIONS_DIR) / a.SECRET_SUBAGENT_SESSION_ID / a.SECRET_SUBAGENT_MEMORY_KIND).glob("*.secret"))
            assert memory_files, "missing encrypted Secret subagent memory"
            secret_agent.responses.append("secret direct reply marker\n<ga-subagent-memory>\n- secret approved memory candidate\n</ga-subagent-memory>")
            chat_result = a.start_subagent_chat(state, loaded_secret_subagent, "secret direct chat marker", source="test_chat")
            assert chat_result.startswith("已发送给子 agent"), chat_result
            drain_ui(state)
            assert any("secret direct reply marker" in msg.content for msg in loaded_secret_subagent.messages), loaded_secret_subagent.messages
            assert any("Secret 子 agent 加密记忆候选" in msg.content and "secret approved memory candidate" in msg.content for msg in loaded_secret_subagent.messages if msg.role == "system"), loaded_secret_subagent.messages
            assert a.secret_blocks_normal_command(state, "/approvals") is False
            secret_approval_items = a.approval_panel_items(show_all=False, state=state)
            secret_memory_approval = next((item for item in secret_approval_items if item.payload.get("secret_storage")), None)
            assert secret_memory_approval is not None, secret_approval_items
            assert "Memory Candidate:" in secret_memory_approval.detail, secret_memory_approval.detail
            assert "secret approved memory candidate" in secret_memory_approval.detail, secret_memory_approval.detail
            formatted_secret_approvals = a.format_approvals(state)
            assert secret_memory_approval.key in formatted_secret_approvals, formatted_secret_approvals
            assert a.is_approval_interaction(state.pending_interaction), state.pending_interaction
            assert state.pending_interaction["approval_id"] == secret_memory_approval.key, state.pending_interaction
            assert "secret approved memory candidate" in state.pending_interaction["question"], state.pending_interaction
            assert "secret approved memory candidate" in a.render_interaction_card(state.pending_interaction), state.pending_interaction
            a.submit(state, "")
            assert state.pending_interaction is None, state.pending_interaction
            assert "已批准并执行 Secret 记忆候选" in state.messages[-1].content, state.messages[-1]
            assert "secret approved memory candidate" in loaded_secret_subagent.memory_text
            chat_files = list((Path(a.SECRET_VAULT_SESSIONS_DIR) / a.SECRET_SUBAGENT_SESSION_ID / a.SECRET_SUBAGENT_CHAT_KIND).glob("*.secret"))
            assert chat_files, "missing encrypted Secret subagent chat"
            candidate_files = list((Path(a.SECRET_VAULT_SESSIONS_DIR) / a.SECRET_SUBAGENT_SESSION_ID / "subagent-memory-candidates").glob("*.secret"))
            assert candidate_files, "missing encrypted Secret subagent memory candidate"
            for item in memory_files + chat_files + candidate_files:
                raw = item.read_bytes()
                assert b"secret persistent memory marker" not in raw
                assert b"secret direct chat marker" not in raw
                assert b"secret direct reply marker" not in raw
                assert b"secret approved memory candidate" not in raw
            state.subagents = {}
            assert a.load_subagents(state) is True
            reloaded_secret_subagent = a.resolve_subagent(state, secret_subagent.agent_id)
            assert reloaded_secret_subagent is not None
            assert "secret persistent memory marker" in reloaded_secret_subagent.memory_text
            assert "secret approved memory candidate" in reloaded_secret_subagent.memory_text
            assert any("secret direct reply marker" in msg.content for msg in reloaded_secret_subagent.messages), reloaded_secret_subagent.messages
            ledger_before_controls = list(a.read_jsonl(a.AGENT_TASK_LEDGER_PATH))
            mail_before_controls = list(a.read_jsonl(a.AGENT_MAIL_PATH))
            hidden_create = ga_control(create_agent_action("zzq xxy", profile="abc def marker", persistent=True, plan_step_id="normal-ledger-leak"))
            assert a.apply_secret_subagent_controls_from_text(state, hidden_create) == 1
            hidden_secret_subagent = a.resolve_subagent(state, "zzq xxy")
            assert hidden_secret_subagent is not None
            assert hidden_secret_subagent.security_context == "secret"
            assert not (Path(a.SUBAGENTS_DIR) / hidden_secret_subagent.agent_id).exists()
            assert a.read_jsonl(a.AGENT_TASK_LEDGER_PATH) == ledger_before_controls
            assert a.read_jsonl(a.AGENT_MAIL_PATH) == mail_before_controls
            secret_agent.responses.append("hidden child result marker")
            hidden_ask = ga_control(delegate_action(secret_subagent.agent_id, "hidden child task marker", parent_task_id="normal-ledger-leak"))
            assert a.apply_secret_subagent_controls_from_text(state, hidden_ask) == 1
            drain_ui(state)
            assert any("hidden child result marker" in msg.content for msg in state.messages), state.messages
            assert a.read_jsonl(a.AGENT_TASK_LEDGER_PATH) == ledger_before_controls
            assert a.read_jsonl(a.AGENT_MAIL_PATH) == mail_before_controls
            for item in (Path(a.SECRET_VAULT_SESSIONS_DIR) / a.SECRET_SUBAGENT_SESSION_ID).glob("**/*.secret"):
                raw = item.read_bytes()
                assert b"abc def marker" not in raw
                assert b"hidden child task marker" not in raw
                assert b"hidden child result marker" not in raw
            state.secret_vault.unlocked = False
            state.secret_vault.key = b""
            state.subagents = {secret_subagent.agent_id: loaded_secret_subagent}
            assert a.load_subagents(state) is True
            assert a.resolve_subagent(state, secret_subagent.agent_id) is None
        finally:
            a.secret_network_gate = old_secret_network_gate
            a.ensure_subagent_agent = old_ensure_subagent_agent
            shutil.rmtree(a.SECRET_VAULT_DIR, ignore_errors=True)
            state.secret_vault = a.SecretVaultState()
    state.secret_vault.pending_action = "unlock"
    state.secret_vault.pending_first_password = "do-not-keep"
    state.secret_vault.key = b"x" * 32
    state.secret_vault.session_id = "secret_cleanup"
    state.secret_vault.previous_log_path = os.path.join(root, "normal.jsonl")
    state.messages.append(a.Message("assistant", "secret plaintext"))
    lock_msg = a.lock_secret_vault(state, reason="test")
    assert "已锁定" in lock_msg, lock_msg
    assert state.secret_vault.unlocked is False
    assert state.secret_vault.pending_action == ""
    assert state.secret_vault.pending_first_password == ""
    assert state.secret_vault.key is None
    assert state.secret_vault.session_id == ""
    assert state.input_history == []
    assert not any(msg.content == "secret plaintext" for msg in state.messages)

    old_secret_network_gate = a.secret_network_gate
    try:
        a.secret_network_gate = lambda _state=None, operation="secret_network": a.PolicyDecision(
            decision_id="policy_secret_allowed",
            action="secret_network",
            subject="orchestrator.main",
            role="",
            status="allowed",
            allowed=True,
            approval_required=False,
            approval_required_for="",
            risk="critical",
            reason=f"test allow {operation}",
        )
        secret_history_agent = SequencedFakeAgent(["secret response"])
        secret_history_state = a.State(agent=secret_history_agent)
        secret_history_state.running = True
        secret_history_state.secret_vault.unlocked = True
        secret_history_state.secret_vault.session_id = "secret_history"
        started_secret_history = a.start_main_agent_task(
            secret_history_state,
            "do not remember this secret prompt",
            source="user",
            visible_user_text="do not remember this secret prompt",
            remember_user=True,
            clear_history=True,
        )
        assert started_secret_history is True
        assert "do not remember this secret prompt" not in secret_history_state.input_history
    finally:
        a.secret_network_gate = old_secret_network_gate
    old_cost_tracker = a.cost_tracker
    try:
        class FakeTokenStats:
            requests = 3
            input = 100
            output = 50
            cache_create = 0
            cache_read = 0

        class FakeCostTracker:
            def get(self, _thread_name: str) -> FakeTokenStats:
                return FakeTokenStats()

        a.cost_tracker = FakeCostTracker()
        token_agent = ContextFakeAgent()
        token_agent.log_path = os.devnull
        token_agent._ga_tui_thread_name = "secret-token-thread"
        token_state = a.State(agent=token_agent)
        assert a.persist_agent_token_usage(token_state, token_agent) is False
        assert token_state.token_live_offsets["secret-token-thread"]["input"] == 100
        assert not os.path.exists(a.TOKEN_USAGE_PATH)
    finally:
        a.cost_tracker = old_cost_tracker

    control_state = a.State(agent=ContextFakeAgent())
    control_state.running = True
    control_state.status = "running"
    control_state.active_task_id = 42
    control_state.active_task_secret = True
    control_state.active_secret_user_text = "secret request"
    control_state.active_secret_session_id = "secret_controls"
    control_state.secret_vault.unlocked = False
    control_state.secret_vault.previous_log_path = os.path.join(root, "normal-after-lock.jsonl")
    a.set_agent_log_path(control_state.agent, os.devnull)
    control_state.ui_queue.put(("stream", a.StreamTarget(), 42, ga_control(create_agent_action("secret-leak", profile="plaintext")), True))
    a.process_ui_queue(control_state)
    assert "secret-leak" not in control_state.subagents
    assert "TUI 控制已忽略" in control_state.last_error, control_state.last_error
    assert a.agent_log_path(control_state.agent) == os.path.join(root, "normal-after-lock.jsonl")

    secret_agent = AbortCountingFakeAgent()
    normal_agent = FakeLLMAgent()
    running_lock_state = a.State(agent=secret_agent)
    running_lock_state.running = True
    running_lock_state.status = "running"
    running_lock_state.active_task_id = 7
    running_lock_state.active_stream_target = a.StreamTarget()
    running_lock_state.active_task_secret = True
    running_lock_state.active_secret_user_text = "clear me"
    running_lock_state.active_secret_session_id = "secret_running"
    running_lock_state.messages = [a.Message("user", "clear me"), a.Message("assistant", "", done=False)]
    running_lock_state.secret_vault.unlocked = True
    running_lock_state.secret_vault.session_id = "secret_running"
    running_lock_state.secret_vault.key = b"x" * 32
    running_lock_state.secret_vault.previous_log_path = os.path.join(root, "normal-running.jsonl")
    a.set_agent_log_path(secret_agent, os.devnull)
    a.activate_secret_proxy_env(running_lock_state, {"chain": ["tor"]})
    assert os.environ["ALL_PROXY"] == "socks5h://127.0.0.1:9050"
    old_new_agent = a.new_agent
    try:
        a.new_agent = lambda: normal_agent
        lock_text = a.lock_secret_vault(running_lock_state, reason="running-test")
    finally:
        a.new_agent = old_new_agent
    assert "后台继续执行" in lock_text
    assert secret_agent.abort_count == 0
    assert running_lock_state.status == "idle"
    assert running_lock_state.active_task_id is None
    assert running_lock_state.active_secret_user_text == ""
    assert a.agent_log_path(running_lock_state.agent) == os.path.join(root, "normal-running.jsonl")
    assert os.environ["ALL_PROXY"] == "socks5h://127.0.0.1:9050"
    secret_bg_keys = a.secret_background_session_keys(running_lock_state)
    assert len(secret_bg_keys) == 1
    bg = running_lock_state.background_sessions[secret_bg_keys[0]]
    assert bg.agent is secret_agent
    assert bg.status == "running"
    assert bg.active_task_id == 7
    assert bg.active_task_secret is True
    assert bg.stream_target is not None and bg.stream_target.key == bg.key
    assert a.agent_log_path(bg.agent) == os.devnull
    running_lock_state.ui_queue.put(("stream", bg.stream_target, 7, "late secret output", True))
    a.process_ui_queue(running_lock_state)
    assert bg.status == "idle"
    assert bg.active_task_secret is False
    assert bg.messages[-1].content == "late secret output"
    assert "结果仅保留在内存" in running_lock_state.last_error, running_lock_state.last_error
    assert running_lock_state.secret_vault.previous_log_path == ""
    saved_secret_backgrounds: list[tuple[str, str, list[a.Message]]] = []
    old_secret_save_session_state = a.secret_save_session_state
    try:
        def fake_secret_save_session_state(_state, session_id, title, messages, **_kwargs):
            saved_secret_backgrounds.append((session_id, title, list(messages)))
            return True, "secret://saved-background"

        a.secret_save_session_state = fake_secret_save_session_state
        running_lock_state.secret_vault.unlocked = True
        running_lock_state.secret_vault.key = b"x" * 32
        assert a.save_unlocked_secret_background_sessions(running_lock_state, source="test-unlock") == 1
    finally:
        a.secret_save_session_state = old_secret_save_session_state
        running_lock_state.secret_vault.unlocked = False
        running_lock_state.secret_vault.key = None
    assert saved_secret_backgrounds
    assert saved_secret_backgrounds[0][0] == "secret_running"
    assert saved_secret_backgrounds[0][2][-1].content == "late secret output"
    for key, value in old_proxy_env.items():
        assert os.environ.get(key) == value, (key, os.environ.get(key), value)
    export_decision = a.gate_policy_action(
        "secret_export",
        subject="orchestrator.main",
        source="test",
        target="clipboard",
        payload={"operation": "test_secret_export"},
        queue_if_required=True,
    )
    assert export_decision.approval_required is True, export_decision
    assert latest_approval(approval_type="policy_approval_request")["approval_required_for"] == "secret_export"

    copied_secret_text: list[str] = []
    old_copy_to_clipboard = a.copy_to_clipboard
    try:
        def fake_copy_to_clipboard(text: str) -> tuple[bool, str]:
            copied_secret_text.append(text)
            return True, "copied"

        copy_state = a.State(agent=ContextFakeAgent())
        copy_state.secret_vault.unlocked = True
        copy_state.line_cache = [a.RenderLine("copy secret marker")]
        copy_state.selection_start = (0, 0)
        copy_state.selection_end = (0, len("copy secret marker"))
        copy_state.selection_dragged = True
        a.copy_to_clipboard = fake_copy_to_clipboard
        a.finish_selection_copy(copy_state)
        assert copied_secret_text == []
        assert "再次复制同一段" in copy_state.last_error, copy_state.last_error
        copy_approval = latest_approval(approval_type="policy_approval_request")
        assert copy_approval["approval_required_for"] == "secret_export"
        approval_id = str(copy_approval["approval_id"])
        assert copy_state.pending_secret_copy_approval_id == approval_id
        assert copy_state.pending_secret_copy_hash
        assert copy_state.pending_secret_copy_key
        a.finish_selection_copy(copy_state)
        assert copied_secret_text == ["copy secret marker"]
        assert "二次确认" in copy_state.last_error, copy_state.last_error
        assert copy_state.pending_secret_copy_approval_id == ""
        assert a.approval_latest_records()[approval_id]["status"] == "approved"
        persisted_gate_data = (
            Path(a.AGENT_APPROVALS_PATH).read_text(encoding="utf-8")
            + Path(a.AGENT_POLICY_DECISIONS_PATH).read_text(encoding="utf-8")
        )
        assert "copy secret marker" not in persisted_gate_data
    finally:
        a.copy_to_clipboard = old_copy_to_clipboard
    state.secret_vault.unlocked = False
    if a.secret_crypto_available():
        setup_session_path = Path(a.MODEL_RESPONSES_DIR) / "model_responses_secret_move_setup.txt"
        setup_session_path.parent.mkdir(parents=True, exist_ok=True)
        setup_session_path.write_text("ordinary-secret-marker-setup", encoding="utf-8")
        setup_state = a.State(agent=ContextFakeAgent())
        setup_state.agent.log_path = str(setup_session_path)
        setup_state.running = True
        setup_msg = a.request_secret_import_session(setup_state, "delete current")
        assert "准备单向迁移到 Secret" in setup_msg, setup_msg
        assert "尚未初始化" in setup_msg, setup_msg
        assert setup_state.secret_vault.pending_import_path == str(setup_session_path)
        assert setup_state.secret_vault.pending_import_disposition == "delete"
        assert setup_state.secret_vault.pending_action == "setup_password"
        a.lock_secret_vault(setup_state, reason="cancel-setup-import")
        assert setup_state.secret_vault.pending_import_path == ""
        assert setup_session_path.exists()

        ok, key, created = a.secret_create_vault("Aa1!aaaa")
        assert ok and key, created
        state.secret_vault.unlocked = True
        state.secret_vault.key = key
        state.secret_vault.session_id = "secret_test"
        wrote, path = a.secret_write_json(state, "checks", "cipher", {"secret": "plaintext-marker"})
        assert wrote, path
        raw_cipher = Path(path).read_bytes()
        assert b"plaintext-marker" not in raw_cipher, raw_cipher
        state.secret_vault.unlocked = False
        state.secret_vault.key = None

        delete_session_path = Path(a.MODEL_RESPONSES_DIR) / "model_responses_secret_move_delete.txt"
        delete_session_path.parent.mkdir(parents=True, exist_ok=True)
        delete_session_path.write_text("ordinary-secret-marker-delete", encoding="utf-8")
        delete_state = a.State(agent=FakeLLMAgent())
        delete_state.agent.log_path = str(delete_session_path)
        delete_state.session_meta = a.load_session_meta_registry()
        ok, key, created = a.secret_create_vault("Aa1!aaaa")
        assert ok and key, created
        delete_state.secret_vault.unlocked = True
        delete_state.secret_vault.key = key
        delete_state.secret_vault.session_id = "secret_migrate_delete"
        delete_state.secret_vault.previous_log_path = str(delete_session_path)
        delete_msg = a.secret_import_normal_session(delete_state, str(delete_session_path), disposition="delete", title="Delete Session")
        assert "普通侧明文源已删除" in delete_msg, delete_msg
        assert not delete_session_path.exists()
        delete_imports = list((Path(a.SECRET_VAULT_SESSIONS_DIR) / "secret_migrate_delete" / "imported-sessions").glob("*.secret"))
        assert delete_imports, "missing encrypted imported session"
        assert all(b"ordinary-secret-marker-delete" not in item.read_bytes() for item in delete_imports)
        imported_list = a.format_secret_imported_sessions(delete_state)
        assert "Delete Session" in imported_list, imported_list
        sidebar_entries = a.load_secret_import_sidebar_entries(delete_state, force=True)
        assert sidebar_entries and "payload" not in sidebar_entries[0], sidebar_entries
        sidebar_rows = a.secret_import_sidebar_rows(delete_state, 44)
        secret_sidebar_rows = [row for row in sidebar_rows if row[0] == "secret_history"]
        assert secret_sidebar_rows and "Delete Session" in secret_sidebar_rows[0][2], sidebar_rows
        assert str(secret_sidebar_rows[0][1]).startswith(a.SECRET_IMPORT_SESSION_PREFIX), secret_sidebar_rows[0]
        a.submit(delete_state, "/Secret sessions")
        assert "Delete Session" in delete_state.messages[-1].content
        seed_agent_context(delete_state.agent, "normal-game-context-before-import-restore")
        restored_import = a.restore_secret_imported_session(delete_state, "1")
        assert "已在 Secret 内打开导入会话" in restored_import, restored_import
        assert any("ordinary-secret-marker-delete" in msg.content for msg in delete_state.messages), delete_state.messages
        assert delete_state.agent.log_path == os.devnull
        imported_backend_text = backend_history_text(delete_state.agent)
        assert "ordinary-secret-marker-delete" in imported_backend_text, imported_backend_text
        assert "normal-game-context-before-import-restore" not in imported_backend_text, imported_backend_text
        assert delete_state.agent.history == []
        assert delete_state.agent.handler is None
        assert getattr(delete_state.agent, "_ga_tui_pending_key_info", "") == ""
        assert all(client.last_tools == "" for client in delete_state.agent.llmclients)
        assert all(client.log_path == os.devnull for client in delete_state.agent.llmclients)
        assert all(client.backend.log_path == os.devnull for client in delete_state.agent.llmclients)
        restored_from_sidebar = a.restore_secret_imported_session(delete_state, secret_sidebar_rows[0][1])
        assert "已经是当前 Secret 会话" in restored_from_sidebar, restored_from_sidebar
        assert str(delete_state.selected_session).startswith(a.SECRET_NATIVE_SESSION_PREFIX), delete_state.selected_session
        native_entries = a.load_secret_session_sidebar_entries(delete_state, force=True)
        assert native_entries and "Delete Session" in native_entries[0]["title"], native_entries
        native_state_path = Path(native_entries[0]["path"])
        assert native_state_path.exists(), native_entries[0]
        assert b"ordinary-secret-marker-delete" not in native_state_path.read_bytes()
        active_rows = a.secret_sidebar_history_rows(delete_state, 44)
        assert not any("Delete Session" in row[2] for row in active_rows), active_rows
        old_secret_session_id = delete_state.secret_vault.session_id
        a.submit(delete_state, "/new")
        assert delete_state.secret_vault.unlocked is True
        assert delete_state.secret_vault.session_id != old_secret_session_id
        assert delete_state.agent.log_path == os.devnull
        assert "ordinary-secret-marker-delete" not in backend_history_text(delete_state.agent)
        assert "空 Secret 会话" in delete_state.messages[-1].content
        native_rows = a.secret_native_sidebar_rows(delete_state, 44)
        assert any(row[0] == "secret_session" and "Delete Session" in row[2] for row in native_rows), native_rows
        combined_rows = a.secret_sidebar_history_rows(delete_state, 44)
        assert sum(1 for row in combined_rows if "Delete Session" in row[2]) == 1, combined_rows
        assert not any(row[0] == "secret_history" and "Delete Session" in row[2] for row in combined_rows), combined_rows
        seed_agent_context(delete_state.agent, "normal-game-context-before-native-restore")
        opened_native = a.restore_secret_native_session(delete_state, "1")
        assert "已切换到 Secret 会话" in opened_native, opened_native
        assert any("ordinary-secret-marker-delete" in msg.content for msg in delete_state.messages), delete_state.messages
        native_backend_text = backend_history_text(delete_state.agent)
        assert "ordinary-secret-marker-delete" in native_backend_text, native_backend_text
        assert "normal-game-context-before-native-restore" not in native_backend_text, native_backend_text
        assert getattr(delete_state.agent, "_ga_tui_pending_key_info", "") == ""
        lock_result = a.lock_secret_vault(delete_state, reason="backend-isolation-test")
        assert "已锁定" in lock_result, lock_result
        locked_backend_text = backend_history_text(delete_state.agent)
        assert "ordinary-secret-marker-delete" not in locked_backend_text, locked_backend_text
        assert delete_state.agent.history == []
        assert delete_state.agent.handler is None
        assert getattr(delete_state.agent, "_ga_tui_pending_key_info", "") == ""
        delete_meta = a.load_session_meta_registry().get(a.session_key(str(delete_session_path)), {})
        assert delete_meta.get("secret_migrated") is True, delete_meta
        assert delete_meta.get("deleted") is True, delete_meta
        assert delete_meta.get("secret_migrated_disposition") == "delete", delete_meta
        assert delete_state.secret_vault.previous_log_path == ""

        archive_session_path = Path(a.MODEL_RESPONSES_DIR) / "model_responses_secret_move_archive.txt"
        archive_session_path.write_text("ordinary-secret-marker-archive", encoding="utf-8")
        archive_state = a.State(agent=ContextFakeAgent())
        archive_state.session_meta = a.load_session_meta_registry()
        ok, key, created = a.secret_create_vault("Aa1!aaaa")
        assert ok and key, created
        archive_state.secret_vault.unlocked = True
        archive_state.secret_vault.key = key
        archive_state.secret_vault.session_id = "secret_migrate_archive"
        archive_msg = a.secret_import_normal_session(archive_state, str(archive_session_path), disposition="archive", title="Archive Session")
        assert "普通侧已归档" in archive_msg, archive_msg
        assert archive_session_path.exists()
        archive_imports = list((Path(a.SECRET_VAULT_SESSIONS_DIR) / "secret_migrate_archive" / "imported-sessions").glob("*.secret"))
        assert archive_imports, "missing archived encrypted imported session"
        assert all(b"ordinary-secret-marker-archive" not in item.read_bytes() for item in archive_imports)
        archive_meta = a.load_session_meta_registry().get(a.session_key(str(archive_session_path)), {})
        assert archive_meta.get("secret_migrated") is True, archive_meta
        assert archive_meta.get("archived") is True, archive_meta
        assert archive_meta.get("secret_migrated_disposition") == "archive", archive_meta

        outside_file = Path(root) / "not_a_session.txt"
        outside_file.write_text("ordinary-secret-marker-outside", encoding="utf-8")
        outside_state = a.State(agent=ContextFakeAgent())
        outside_state.secret_vault.unlocked = True
        outside_state.secret_vault.key = key
        outside_state.secret_vault.session_id = "secret_migrate_outside"
        outside_msg = a.secret_import_normal_session(outside_state, str(outside_file), disposition="delete", title="Outside")
        assert "会话目录外" in outside_msg, outside_msg
        assert outside_file.exists()

        request_session_path = Path(a.MODEL_RESPONSES_DIR) / "model_responses_secret_move_request.txt"
        request_session_path.write_text("ordinary-secret-marker-request", encoding="utf-8")
        request_state = a.State(agent=ContextFakeAgent())
        request_state.agent.log_path = str(request_session_path)
        request_state.running = True
        request_imports_before = set((Path(a.SECRET_VAULT_SESSIONS_DIR)).glob("*/imported-sessions/*.secret"))
        request_msg = a.request_secret_import_session(request_state, "archive current")
        assert "普通侧已归档" in request_msg, request_msg
        assert request_state.secret_vault.pending_action == "", request_state.secret_vault.pending_action
        assert request_state.secret_vault.pending_import_path == ""
        assert request_session_path.exists()
        request_imports_after = set((Path(a.SECRET_VAULT_SESSIONS_DIR)).glob("*/imported-sessions/*.secret"))
        request_new_imports = list(request_imports_after - request_imports_before)
        assert len(request_new_imports) == 1, request_new_imports
        assert b"ordinary-secret-marker-request" not in request_new_imports[0].read_bytes()
        ok, unlocked_key, unlocked_msg = a.secret_unlock_vault("Aa1!aaaa")
        assert ok and unlocked_key, unlocked_msg
        request_state.secret_vault.unlocked = True
        request_state.secret_vault.key = unlocked_key
        request_state.secret_vault.import_private_key, import_key_msg = a.secret_load_or_create_import_private_key(unlocked_key)
        assert request_state.secret_vault.import_private_key, import_key_msg
        listed_dropbox = a.format_secret_imported_sessions(request_state)
        assert "secret_move_request" in listed_dropbox, listed_dropbox
        a.lock_secret_vault(request_state, reason="dropbox-list-complete")

        flow_session_path = Path(a.MODEL_RESPONSES_DIR) / "model_responses_secret_move_flow.txt"
        flow_session_path.write_text("ordinary-secret-marker-flow", encoding="utf-8")
        flow_state = a.State(agent=ContextFakeAgent())
        flow_state.agent.log_path = str(flow_session_path)
        flow_state.running = True
        flow_msg = a.request_secret_import_session(flow_state, "delete current")
        assert "普通侧明文源已删除" in flow_msg, flow_msg
        assert flow_state.secret_vault.pending_action == ""
        assert flow_state.secret_vault.pending_import_path == ""
        assert not flow_session_path.exists()
        flow_meta = a.load_session_meta_registry().get(a.session_key(str(flow_session_path)), {})
        assert flow_meta.get("secret_migrated") is True, flow_meta
        assert flow_meta.get("deleted") is True, flow_meta

    partial_agent = SequencedFakeAgent(
        [
            ga_control(
                plan_action("自动续跑计划", ["创建正式子代理", "创建临时子代理"]),
                create_agent_action("续跑正式", persistent=True, profile="正式测试子代理", plan_step_id="创建正式子代理"),
            ),
            ga_control(create_agent_action("续跑临时", temporary=True, profile="临时测试子代理", plan_step_id="创建临时子代理")),
        ]
    )
    partial_state = a.State(agent=partial_agent)
    partial_state.running = True
    assert a.start_main_agent_task(
        partial_state,
        "run partial plan",
        source="user",
        visible_user_text="run partial plan",
        remember_user=True,
        clear_history=True,
    )
    for _ in range(4):
        drain_ui(partial_state)
    assert len(partial_agent.prompts) == 2, partial_agent.prompts
    assert partial_agent.prompts[1][1] == "ga-tui:auto_plan_continue", partial_agent.prompts
    continuation_prompt = partial_agent.prompts[1][0]
    assert "创建临时子代理" in continuation_prompt, continuation_prompt
    assert "control-emission continuation" in continuation_prompt, continuation_prompt
    assert "Do not call browser/search/file/code tools" in continuation_prompt, continuation_prompt
    assert "web_scan" in continuation_prompt, continuation_prompt
    assert '<ga-control>{"schema_version":"ga-control.v2"' in continuation_prompt, continuation_prompt
    assert '"action":"agent.create"' in continuation_prompt, continuation_prompt
    assert '"action":"delegate.create"' in continuation_prompt, continuation_prompt
    assert '"action":"task.update"' in continuation_prompt, continuation_prompt
    assert '"parent_task_id":"' in continuation_prompt, continuation_prompt
    assert any("自动续跑主控" in msg.content for msg in partial_state.messages if msg.role == "system"), partial_state.messages
    partial_agents = {sub.name: sub for sub in partial_state.subagents.values()}
    assert partial_agents["续跑正式"].persistent is True, partial_agents
    assert partial_agents["续跑临时"].persistent is False, partial_agents
    assert a.latest_task_records()[partial_state.active_plan_task_id]["status"] == "completed"

    blocked_agent = SequencedFakeAgent(
        [
            ga_control(
                plan_action("自动续跑阻塞计划", ["创建正式子代理", "创建临时子代理"]),
                create_agent_action("阻塞正式", persistent=True, profile="正式测试子代理", plan_step_id="创建正式子代理"),
            ),
            "我没有发出新的控制块。",
        ]
    )
    blocked_state = a.State(agent=blocked_agent)
    blocked_state.running = True
    assert a.start_main_agent_task(
        blocked_state,
        "run blocked partial plan",
        source="user",
        visible_user_text="run blocked partial plan",
        remember_user=True,
        clear_history=True,
    )
    for _ in range(4):
        drain_ui(blocked_state)
    assert len(blocked_agent.prompts) == 2, blocked_agent.prompts
    assert any("自动续跑已停止" in msg.content for msg in blocked_state.messages if msg.role == "system"), blocked_state.messages

    root = tempfile.mkdtemp(prefix="ga_tui_policy_check_")
    retarget_harness(root)
    install_fake_agent_runtime()
    state = a.State(agent=None)
    state.running = True

    direct_task = a.append_task_ledger("task_direct_schema", status="working", objective="direct schema check")
    assert_task_schema(direct_task, status="working")
    direct_mail = a.append_agent_mail(
        from_agent="orchestrator.main",
        to_type="agent",
        target="debug.target",
        intent="debug_loop_2",
        task_id="task_direct_schema",
        status="working",
        payload={"objective": "direct mail schema check", "role": "researcher"},
    )
    assert_mail_schema(direct_mail, intent="debug_loop_2")
    direct_ref = a.write_harness_artifact(
        "debug-loop",
        "schema-artifact",
        "# Debug Artifact\n\nschema check\n",
        source_task_id="task_direct_schema",
        provenance={"generated_by": "debug_loop_2"},
    )
    direct_artifact = a.artifact_index_latest()[direct_ref]
    assert_artifact_schema(direct_artifact, artifact_type="debug-loop")
    inventory = [item for item in a.artifact_inventory() if item.key == direct_ref]
    assert inventory and "Hash:" in inventory[-1].detail and "Provenance:" in inventory[-1].detail, inventory
    daily_worker = a.create_subagent(state, "Daily Digest Worker", role="researcher")
    schedule_control = ga_control({
        "action": "schedule.create",
        "schedule_id": "sched_daily_digest",
        "name": "Daily Digest",
        "cron": "0 8 * * *",
        "provider_id": "genericagent",
        "execution": {
            "mode": "agent_task",
            "routing": {"selected_agent": daily_worker.name},
            "work_order": {"objective": "Generate a daily digest."},
            "capability_contract": {"tools_allowed": ["read"], "write_policy": "none"},
            "context_contract": {"history_mode": "summary", "artifact_reference_only": True},
            "output_contract": {"format": "structured_markdown", "required_sections": ["summary"]},
        },
    })
    a.apply_tui_controls_from_text(state, schedule_control, source="agent")
    schedule_records = a.latest_schedule_records()
    assert schedule_records["sched_daily_digest"]["dispatch_contract"] == "agenttask.v2", schedule_records
    assert schedule_records["sched_daily_digest"]["provider_id"] == "genericagent", schedule_records
    assert schedule_records["sched_daily_digest"]["cron"] == "0 8 * * *", schedule_records
    a.apply_tui_controls_from_text(state, ga_control({"action": "schedule.update", "target": "sched_daily_digest", "interval": "10m"}), source="agent")
    updated_daily = a.latest_schedule_records()["sched_daily_digest"]
    assert updated_daily["dispatch_contract"] == "agenttask.v2", updated_daily
    assert updated_daily["execution"]["mode"] == "agent_task", updated_daily
    assert updated_daily["interval"] == "10m", updated_daily
    assert not str(updated_daily.get("cron") or "").strip(), updated_daily
    assert a.split_schedule_trigger(updated_daily) == ("interval", "10m"), updated_daily
    a.apply_tui_controls_from_text(state, ga_control({"action": "schedule.disable", "target": "sched_daily_digest"}), source="agent")
    assert a.latest_schedule_records()["sched_daily_digest"]["status"] == "disabled"
    for prompt_token in ("ScheduleCreate", "schedule_create", "schedule_list", "execution", "tui_action", "agent_task"):
        assert prompt_token in a.TUI_AGENT_CONTROL_HINT, prompt_token
    assert a.split_schedule_trigger({"cron": "0 8 * * *"}) == ("cron", "0 8 * * *")
    assert a.split_schedule_trigger({"interval": "1m"}) == ("interval", "1m")
    assert a.split_schedule_trigger({"at": "2026-01-01T00:00:00+0800"}) == ("at", "2026-01-01T00:00:00+0800")
    assert a.split_schedule_trigger({"trigger": "interval:1m"}) == ("interval", "1m")
    assert a.schedule_trigger_from_control({"unsupported_field": "x"}) == ""
    assert a.split_schedule_trigger({"trigger": "free form words"}) == ("unknown", "free form words")
    assert a.parse_schedule_interval_seconds("free form words") is None
    interval_anchor_row = a.append_schedule_record({
        "schedule_id": "sched_interval_anchor",
        "name": "Interval Anchor",
        "status": "enabled",
        "trigger": "interval:60s",
        "created_at": "1970-01-01T00:00:00+00:00",
        "work_order": {"objective": "Interval anchor probe."},
    })
    a.append_schedule_run({
        "schedule_id": "sched_interval_anchor",
        "status": "dispatched",
        "timestamp": "1970-01-01T00:16:40+00:00",
        "idempotency_key": "sched_interval_anchor:interval:1060",
    })
    a.append_schedule_run({
        "schedule_id": "sched_interval_anchor",
        "status": "skipped",
        "timestamp": "1970-01-01T00:17:30+00:00",
        "idempotency_key": "sched_interval_anchor:skipped:probe",
    })
    assert a.latest_schedule_runs_by_schedule_id()["sched_interval_anchor"]["status"] == "skipped"
    assert a.latest_schedule_attempt_runs_by_schedule_id()["sched_interval_anchor"]["status"] == "dispatched"
    interval_info = a.schedule_due_info(
        interval_anchor_row,
        now_epoch=1060.0,
        last_run=a.latest_schedule_attempt_runs_by_schedule_id()["sched_interval_anchor"],
        seen_keys=set(),
    )
    assert interval_info["due"] and interval_info["due_at_epoch"] == 1060.0, interval_info
    beep_calls: list[str] = []
    old_emit_beep = a.emit_tui_beep
    try:
        a.emit_tui_beep = lambda: beep_calls.append("beep") or "beep emitted"
        tui_beep_control = ga_control({
            "action": "schedule.create",
            "schedule_id": "sched_tui_beep",
            "name": "TUI Beep",
            "at": "2026-01-01T00:00:00+0800",
            "execution": {"mode": "tui_action", "action": "beep", "message": "test beep"},
        })
        a.apply_tui_controls_from_text(state, tui_beep_control, source="agent")
        tui_record = a.latest_schedule_records()["sched_tui_beep"]
        assert tui_record["dispatch_contract"] == "tui_action.v1", tui_record
        assert tui_record["execution"]["mode"] == "tui_action", tui_record
        assert tui_record["execution"]["action"] == "beep", tui_record
        a.apply_tui_controls_from_text(state, ga_control({"action": "schedule.update", "target": "sched_tui_beep", "name": "Renamed TUI Beep"}), source="agent")
        tui_record = a.latest_schedule_records()["sched_tui_beep"]
        assert tui_record["name"] == "Renamed TUI Beep", tui_record
        assert tui_record["dispatch_contract"] == "tui_action.v1", tui_record
        assert tui_record["execution"]["mode"] == "tui_action", tui_record
        tui_tick = a.scheduler_tick(state, now_epoch=1780000000.0, source="test:scheduler_tui_beep", target_schedule_id="sched_tui_beep")
        assert tui_tick["due"] == 1 and tui_tick["dispatched"] == 1 and tui_tick["failed"] == 0, tui_tick
        assert beep_calls == ["beep"], beep_calls
        tui_runs = [row for row in a.read_jsonl(a.AGENT_SCHEDULE_RUNS_PATH) if row.get("schedule_id") == "sched_tui_beep"]
        assert any(row.get("status") == "starting" for row in tui_runs), tui_runs
        assert any(row.get("status") == "completed" and row.get("result") == "beep emitted" for row in tui_runs), tui_runs
        assert all("task_id" not in row for row in tui_runs if row.get("status") == "completed"), tui_runs
    finally:
        a.emit_tui_beep = old_emit_beep
    scheduler_worker = a.create_subagent(state, "Scheduler Worker", role="researcher")
    due_schedule_control = ga_control({
        "action": "schedule.create",
        "schedule_id": "sched_due_once",
        "name": "Due Once",
        "at": "2026-01-01T00:00:00+0800",
        "execution": {
            "mode": "agent_task",
            "routing": {
                "selected_agent": scheduler_worker.name,
                "target_selector": {"role": "researcher", "reuse_policy": "prefer_existing"},
            },
            "work_order": {
                "objective": "Read local docs and produce a short scheduled digest.",
                "success_criteria": ["return a concise digest"],
                "stop_condition": "return scheduled digest and stop",
            },
            "capability_contract": {"tools_allowed": ["read"], "tools_forbidden": ["repo.write"], "write_policy": "none"},
            "context_contract": {"history_mode": "summary", "artifact_reference_only": True},
            "output_contract": {"format": "structured_markdown", "required_sections": ["summary", "artifact_refs"]},
        },
    })
    a.apply_tui_controls_from_text(state, due_schedule_control, source="agent")
    assert a.latest_schedule_records()["sched_due_once"]["at"] == "2026-01-01T00:00:00+0800"
    assert a.latest_schedule_records()["sched_due_once"]["provider_id"] == "ohmypi"
    due_info = a.schedule_due_info(a.latest_schedule_records()["sched_due_once"], now_epoch=1780000000.0)
    assert due_info["due"] and due_info["idempotency_key"], due_info
    tick = a.scheduler_tick(state, now_epoch=1780000000.0, source="test:scheduler")
    assert tick["checked"] >= 2 and tick["due"] >= 1 and tick["dispatched"] >= 1, tick
    schedule_runs = a.read_jsonl(a.AGENT_SCHEDULE_RUNS_PATH)
    due_runs = [row for row in schedule_runs if row.get("schedule_id") == "sched_due_once"]
    assert any(row.get("status") == "starting" for row in due_runs), due_runs
    assert any(row.get("status") == "dispatched" for row in due_runs), due_runs
    assert any(row.get("task_id") for row in due_runs if row.get("status") == "dispatched"), due_runs
    assert all(row.get("provider_id") == "ohmypi" for row in due_runs), due_runs
    assert any(row.get("runtime_provider_id") == "ohmypi" for row in due_runs if row.get("status") == "dispatched"), due_runs
    scheduled_task_rows = [
        row for row in a.read_jsonl(a.AGENT_TASK_LEDGER_PATH)
        if row.get("assigned_agent") == scheduler_worker.agent_id and row.get("status") == "working"
    ]
    assert scheduled_task_rows, a.read_jsonl(a.AGENT_TASK_LEDGER_PATH)
    visible_scheduler_prompts = [msg.content for msg in scheduler_worker.messages if msg.role == "user"]
    assert any("╭─ 子 Agent 工作单" in content for content in visible_scheduler_prompts), scheduler_worker.messages
    assert all("[GA TUI AgentTask Envelope v2]" not in content for content in visible_scheduler_prompts), scheduler_worker.messages
    assert all('"tools_forbidden": [' not in content for content in visible_scheduler_prompts), scheduler_worker.messages
    assert scheduler_worker.agent.prompts, scheduler_worker.agent
    assert "[GA TUI AgentTask Envelope v2]" in scheduler_worker.agent.prompts[-1][0], scheduler_worker.agent.prompts
    assert '"tools_forbidden": [' in scheduler_worker.agent.prompts[-1][0], scheduler_worker.agent.prompts[-1][0]
    scheduled_ops = a.create_subagent(state, "Scheduled Ops Agent", role="ops")
    approval_schedule_control = ga_control({
        "action": "schedule.create",
        "schedule_id": "sched_ops_approval",
        "name": "Scheduled Ops Approval",
        "at": "2026-01-01T00:00:00+0800",
        "execution": {
            "mode": "agent_task",
            "routing": {
                "selected_agent": scheduled_ops.name,
                "target_selector": {"role": "ops", "reuse_policy": "prefer_existing"},
            },
            "work_order": {
                "objective": "deploy production with sudo",
                "success_criteria": ["deployment is approved first"],
                "stop_condition": "wait for approval before deployment",
            },
            "capability_contract": {"tools_allowed": ["shell"], "tools_forbidden": ["deploy"], "write_policy": "approved_only"},
            "context_contract": {"history_mode": "summary", "artifact_reference_only": True},
            "output_contract": {"format": "structured_markdown", "required_sections": ["summary", "approval_refs"]},
        },
    })
    a.apply_tui_controls_from_text(state, approval_schedule_control, source="agent")
    approval_tick = a.scheduler_tick(state, now_epoch=1780000100.0, source="test:scheduler_approval", target_schedule_id="sched_ops_approval")
    approval_runs = [row for row in approval_tick["runs"] if row.get("schedule_id") == "sched_ops_approval"]
    approval_final = [row for row in approval_runs if row.get("status") == "approval_required"][-1]
    assert approval_final["task_id"], approval_final
    assert approval_final["approval_id"], approval_final
    assert approval_final["provider_id"] == "ohmypi", approval_final
    assert approval_final["runtime_provider_id"] == "ohmypi", approval_final
    approval_task = a.latest_task_records()[approval_final["task_id"]]
    assert approval_task["status"] == "approval_required", approval_task
    assert approval_task["approval"]["approval_id"] == approval_final["approval_id"], approval_task
    duplicate_tick = a.scheduler_tick(state, now_epoch=1780000000.0, source="test:scheduler_duplicate")
    assert duplicate_tick["dispatched"] == 0 and duplicate_tick["duplicates"] >= 1, duplicate_tick
    disabled_tick = a.scheduler_tick(state, now_epoch=1780000000.0, source="test:scheduler_disabled", target_schedule_id="sched_daily_digest", record_skips=True)
    assert disabled_tick["dispatched"] == 0 and disabled_tick["skipped"] == 1, disabled_tick
    invalid_schedule = a.append_schedule_record({
        "schedule_id": "sched_invalid",
        "name": "Invalid Schedule",
        "status": "enabled",
        "trigger": "not a schedule",
        "provider_id": "genericagent",
        "dispatch_contract": "agenttask.v2",
        "work_order": {"objective": "Should not run."},
    })
    invalid_info = a.schedule_due_info(invalid_schedule, now_epoch=1780000000.0)
    assert invalid_info["status"] == "invalid", invalid_info
    invalid_tick = a.scheduler_tick(state, now_epoch=1780000000.0, source="test:scheduler_invalid")
    assert invalid_tick["invalid"] >= 1, invalid_tick
    assert any(row.get("schedule_id") == "sched_invalid" and row.get("status") == "invalid" for row in a.read_jsonl(a.AGENT_SCHEDULE_RUNS_PATH))
    registry = a.ensure_gateway_registry(state)
    assert registry["internal_agent_mail"]["artifact_index"] == a.AGENT_ARTIFACT_INDEX_PATH, registry
    assert registry["internal_agent_mail"]["policy_decisions"] == a.AGENT_POLICY_DECISIONS_PATH, registry
    assert registry["internal_agent_mail"]["orchestrator_plans"] == a.AGENT_ORCHESTRATOR_PLANS_PATH, registry
    assert registry["internal_agent_mail"]["memory_candidates"] == a.AGENT_MEMORY_CANDIDATES_PATH, registry
    assert registry["internal_agent_mail"]["traces"] == a.AGENT_TRACES_PATH, registry
    assert registry["internal_agent_mail"]["evals"] == a.AGENT_EVALS_PATH, registry
    assert registry["internal_agent_mail"]["checkpoints"] == a.AGENT_CHECKPOINT_INDEX_PATH, registry
    assert registry["internal_agent_mail"]["checkpoint_store"] == a.AGENT_CHECKPOINTS_DIR, registry
    assert registry["internal_agent_mail"]["recovery"] == a.AGENT_RECOVERY_PATH, registry
    assert registry["internal_agent_mail"]["recovery_plans"] == a.AGENT_RECOVERY_PLANS_PATH, registry
    assert registry["internal_agent_mail"]["runtime_providers"] == a.AGENT_RUNTIME_REGISTRY_PATH, registry
    assert registry["internal_agent_mail"]["schedules"] == a.AGENT_SCHEDULES_PATH, registry
    assert registry["internal_agent_mail"]["schedule_runs"] == a.AGENT_SCHEDULE_RUNS_PATH, registry
    assert_gateway_schema(registry)
    baseline_report = registry["baseline_comparison"]
    assert_baseline_report_schema(baseline_report)
    baseline_items = a.baseline_panel_items(state)
    assert baseline_items and baseline_items[0].key == "summary", baseline_items
    assert any(item.key == "a2a_mcp_gateway" for item in baseline_items), baseline_items
    formatted_baseline = a.format_baseline_report(baseline_report)
    assert "Architecture Baseline Comparison" in formatted_baseline, formatted_baseline
    assert a.AGENT_BASELINE_REPORT_PATH in formatted_baseline, formatted_baseline
    runtime_text = a.format_runtime_registry(registry["runtime_registry"])
    assert "Agent Runtime Providers" in runtime_text and "genericagent" in runtime_text, runtime_text
    schedule_text = a.format_scheduled_task_registry(registry["scheduled_task_registry"])
    assert "Scheduled Tasks" in schedule_text and "agenttask.v2" in schedule_text and "schedule_runs.jsonl" in schedule_text, schedule_text
    model_text = a.format_model_orchestration_registry(registry["model_orchestration"])
    assert "Model Orchestration" in model_text, model_text
    gateway_panel_keys = {item.key for item in a.gateway_panel_items(state)}
    assert {"runtime_registry", "model_orchestration", "scheduled_task_registry"} <= gateway_panel_keys, gateway_panel_keys
    direct_a2a_task = [item for item in registry["a2a_gateway"]["tasks"] if item["id"] == "task_direct_schema"]
    assert direct_a2a_task
    assert_a2a_task_schema(direct_a2a_task[-1])
    direct_a2a_message = [item for item in registry["a2a_gateway"]["messages"] if item["messageId"] == direct_mail["message_id"]]
    assert direct_a2a_message
    assert_a2a_message_schema(direct_a2a_message[-1])
    direct_a2a_artifact = [item for item in registry["a2a_gateway"]["artifacts"] if item["artifactId"] == direct_artifact["artifact_id"]]
    assert direct_a2a_artifact
    assert_a2a_artifact_schema(direct_a2a_artifact[-1])
    run_gateway_server_checks()
    run_gateway_daemon_checks()

    ops = a.create_subagent(state, "Ops Agent", role="ops")
    blocked = a.start_subagent_task(state, ops, "deploy production with sudo", source="user")
    assert blocked.startswith("APPROVAL_REQUIRED"), blocked
    queued_task = latest_approval(approval_type="policy_approval_request", deferred="start_subagent_task")
    queued_payload = queued_task.get("payload") or {}
    assert queued_payload.get("action") in {"deploy", "long_running_privilege_escalation"}, queued_task
    approval_task_rows = [row for row in a.read_jsonl(a.AGENT_TASK_LEDGER_PATH) if row.get("status") == "approval_required"]
    assert approval_task_rows
    assert_task_schema(approval_task_rows[-1], status="approval_required")
    assert approval_task_rows[-1]["approval"]["approval_status"] == "approval_required"
    approval_plans = [row for row in a.read_jsonl(a.AGENT_ORCHESTRATOR_PLANS_PATH) if row.get("status") == "approval_required"]
    assert approval_plans
    assert_orchestrator_plan_schema(approval_plans[-1], status="approval_required")
    assert approval_plans[-1]["task_id"] == approval_task_rows[-1]["task_id"], approval_plans[-1]
    assert approval_plans[-1]["approval_required"], approval_plans[-1]
    approval_checkpoints = [row for row in a.read_jsonl(a.AGENT_CHECKPOINT_INDEX_PATH) if row.get("task_id") == approval_task_rows[-1]["task_id"]]
    assert approval_checkpoints
    assert_checkpoint_schema(approval_checkpoints[-1], status="approval_required")
    approval_mail = [row for row in a.read_jsonl(a.AGENT_MAIL_PATH) if row.get("intent") == "approval_request"][-1]
    assert_mail_schema(approval_mail, intent="approval_request")
    assert approval_mail["approval"]["approval_id"] == queued_task["approval_id"]

    approvals_before_contract_delegate = len(a.read_jsonl(a.AGENT_APPROVALS_PATH))
    contract_objective = "整理项目结构，输出证据引用。"
    a.apply_tui_controls_from_text(
        state,
        ga_control(
            create_agent_action("Contract Researcher", role="researcher", profile="只读整理证据，不执行写操作。"),
            delegate_action("Contract Researcher", contract_objective, task_title="contract-safe-delegate"),
        ),
        source="agent",
    )
    assert len(a.read_jsonl(a.AGENT_APPROVALS_PATH)) == approvals_before_contract_delegate
    contract_sub = a.resolve_subagent(state, "Contract Researcher")
    assert contract_sub is not None
    visible_contract_prompts = [msg.content for msg in contract_sub.messages if msg.role == "user"]
    assert any(
        "╭─ 子 Agent 工作单" in content
        and "整理项目结构，输出证据引用。" in content
        and "内部协议与工具权限已隐藏" in content
        for content in visible_contract_prompts
    ), contract_sub.messages
    assert all("[GA TUI AgentTask Envelope v2]" not in content for content in visible_contract_prompts), contract_sub.messages
    assert all('"tools_forbidden": [' not in content for content in visible_contract_prompts), contract_sub.messages
    assert contract_sub.agent.prompts, contract_sub.agent
    assert "[GA TUI AgentTask Envelope v2]" in contract_sub.agent.prompts[-1][0], contract_sub.agent.prompts
    assert '"tools_forbidden": [' in contract_sub.agent.prompts[-1][0], contract_sub.agent.prompts[-1][0]
    assert '"deploy"' in contract_sub.agent.prompts[-1][0], contract_sub.agent.prompts[-1][0]
    contract_task_rows = [
        row
        for row in a.read_jsonl(a.AGENT_TASK_LEDGER_PATH)
        if row.get("assigned_agent") == contract_sub.agent_id and row.get("status") == "working"
    ]
    assert contract_task_rows, a.read_jsonl(a.AGENT_TASK_LEDGER_PATH)
    assert contract_task_rows[-1]["objective"] == contract_objective
    assert "deploy" not in contract_task_rows[-1]["objective"]
    contract_mail_rows = [
        row
        for row in a.read_jsonl(a.AGENT_MAIL_PATH)
        if (row.get("to") or {}).get("target") == contract_sub.agent_id and row.get("intent") == "delegate"
    ]
    assert contract_mail_rows
    assert (contract_mail_rows[-1]["payload"] or {}).get("objective") == contract_objective

    memory_blocked = a.append_subagent_memory(ops, "Stable operational preference", source="manual")
    assert memory_blocked.startswith("APPROVAL_REQUIRED"), memory_blocked
    memory_policy = latest_approval(approval_type="policy_approval_request", deferred="append_subagent_memory")
    memory_result = a.decide_approval(state, str(memory_policy["approval_id"]), True)
    assert "已写入子 agent 记忆" in memory_result, memory_result
    assert "Stable operational preference" in a.read_text_file(a.subagent_memory_path(ops.agent_id), "")

    reader = a.create_subagent(state, "Reader", role="researcher")
    registry_with_agents = a.ensure_gateway_registry(state)
    assert_gateway_schema(registry_with_agents)
    reader_cards = [item for item in registry_with_agents["a2a_gateway"]["agent_cards"] if item["agent_id"] == reader.agent_id]
    assert reader_cards
    assert_agent_card_schema(reader_cards[-1])
    capability_agents = [item for item in registry_with_agents["capability_registry"]["agents"] if item["agent_id"] == reader.agent_id]
    assert capability_agents and capability_agents[-1]["capabilities_ref"] == "capability://role/researcher", capability_agents
    safe = a.start_subagent_task(state, reader, "read local docs and summarize", source="user")
    assert safe.startswith("已启动子 agent"), safe
    delegate_mail = [row for row in a.read_jsonl(a.AGENT_MAIL_PATH) if row.get("intent") == "delegate" and (row.get("to") or {}).get("target") == reader.agent_id][-1]
    assert_mail_schema(delegate_mail, intent="delegate")
    assert delegate_mail["task"]["boundaries"], delegate_mail
    assert delegate_mail["permissions"]["write_policy"] == "none", delegate_mail
    drain_ui(state)
    assert reader.status == "idle", reader.status
    completed_rows = [row for row in a.read_jsonl(a.AGENT_TASK_LEDGER_PATH) if row.get("status") == "completed" and row.get("assigned_agent") == reader.agent_id]
    assert completed_rows
    assert_task_schema(completed_rows[-1], status="completed")
    completed_task_id = str(completed_rows[-1]["task_id"])
    artifact_rows = a.read_jsonl(a.AGENT_ARTIFACT_INDEX_PATH)
    assert artifact_rows
    context_rows = [row for row in artifact_rows if row.get("type") == "context_pack" and row.get("source_task_id") == completed_task_id]
    result_rows = [row for row in artifact_rows if row.get("type") == "subagent-results" and row.get("source_task_id") == completed_task_id]
    assert context_rows, artifact_rows
    assert result_rows, artifact_rows
    working_plans = [row for row in a.read_jsonl(a.AGENT_ORCHESTRATOR_PLANS_PATH) if row.get("status") == "working" and row.get("task_id") == completed_task_id]
    assert working_plans
    assert_orchestrator_plan_schema(working_plans[-1], status="working")
    assert working_plans[-1]["artifact_refs"] == [context_rows[-1]["uri"]], working_plans[-1]
    assert working_plans[-1]["delegation_contract"]["agent_id"] == reader.agent_id, working_plans[-1]
    completed_checkpoints = [row for row in a.read_jsonl(a.AGENT_CHECKPOINT_INDEX_PATH) if row.get("task_id") == completed_task_id]
    assert len(completed_checkpoints) >= 2, completed_checkpoints
    for checkpoint in completed_checkpoints:
        assert_checkpoint_schema(checkpoint)
    assert any(row["status"] == "working" for row in completed_checkpoints), completed_checkpoints
    assert any(row["status"] == "completed" for row in completed_checkpoints), completed_checkpoints
    assert_artifact_schema(context_rows[-1], artifact_type="context_pack")
    assert_artifact_schema(result_rows[-1], artifact_type="subagent-results")
    context_pack = assert_context_pack_schema(str(context_rows[-1]["path"]))
    assert context_pack["memory_pack"]["for_task_id"] == completed_task_id, context_pack
    result_mail = [row for row in a.read_jsonl(a.AGENT_MAIL_PATH) if row.get("intent") == "result" and row.get("task_id") == completed_rows[-1]["task_id"]][-1]
    assert_mail_schema(result_mail, intent="result")
    trace_rows = [row for row in a.read_jsonl(a.AGENT_TRACES_PATH) if row.get("task_id") == completed_task_id]
    assert trace_rows
    for trace in trace_rows:
        assert_trace_schema(trace)
    delegated_trace = [row for row in trace_rows if row.get("event") == "delegated"][-1]
    assert delegated_trace["audit_refs"]["artifacts"] == [context_rows[-1]["uri"]], delegated_trace
    assert delegated_trace["audit_refs"]["checkpoints"], delegated_trace
    completed_trace = [row for row in trace_rows if row.get("event") == "completed"][-1]
    assert completed_trace["audit_refs"]["artifacts"] == [result_rows[-1]["uri"]], completed_trace
    assert completed_trace["audit_refs"]["checkpoints"], completed_trace
    eval_rows = [row for row in a.read_jsonl(a.AGENT_EVALS_PATH) if row.get("task_id") == completed_task_id]
    assert eval_rows
    assert_eval_schema(eval_rows[-1])
    assert working_plans[-1]["plan_id"] in eval_rows[-1]["audit_refs"]["plan_versions"], eval_rows[-1]
    assert delegate_mail["message_id"] in eval_rows[-1]["audit_refs"]["messages"], eval_rows[-1]
    assert result_mail["message_id"] in eval_rows[-1]["audit_refs"]["messages"], eval_rows[-1]
    assert context_rows[-1]["uri"] in eval_rows[-1]["audit_refs"]["artifacts"], eval_rows[-1]
    assert result_rows[-1]["uri"] in eval_rows[-1]["audit_refs"]["artifacts"], eval_rows[-1]
    assert eval_rows[-1]["audit_refs"]["checkpoints"], eval_rows[-1]
    assert eval_rows[-1]["final_state"]["has_evidence"] is True, eval_rows[-1]
    assert working_plans[-1]["delegation_contract"]["budget"] == delegate_mail["budget"], (working_plans[-1], delegate_mail)
    assert working_plans[-1]["delegation_contract"]["permissions"] == delegate_mail["permissions"], (working_plans[-1], delegate_mail)
    assert completed_rows[-1]["artifact_refs"] == [result_rows[-1]["uri"]], completed_rows[-1]
    registry_after_task = a.ensure_gateway_registry(state)
    assert_baseline_report_schema(registry_after_task["baseline_comparison"])
    assert registry_after_task["baseline_comparison"]["summary"]["complete"] >= baseline_report["summary"]["complete"], registry_after_task["baseline_comparison"]
    completed_a2a_task = [item for item in registry_after_task["a2a_gateway"]["tasks"] if item["id"] == completed_task_id]
    assert completed_a2a_task
    assert_a2a_task_schema(completed_a2a_task[-1])
    assert completed_a2a_task[-1]["status"]["state"] == "completed", completed_a2a_task[-1]
    result_a2a_message = [item for item in registry_after_task["a2a_gateway"]["messages"] if item["messageId"] == result_mail["message_id"]]
    assert result_a2a_message
    assert_a2a_message_schema(result_a2a_message[-1])
    result_a2a_artifact = [item for item in registry_after_task["a2a_gateway"]["artifacts"] if item["artifactId"] == result_rows[-1]["artifact_id"]]
    assert result_a2a_artifact
    assert_a2a_artifact_schema(result_a2a_artifact[-1])

    cache_agent = a.create_subagent(state, "Cache Lifecycle Agent", role="researcher")
    cache_agent.agent = BlockingFakeAgent()
    _cache_plan_id, cache_steps = a.create_task_plan(
        state,
        "Cache Lifecycle Plan",
        ["Delegate to cache lifecycle agent"],
        expected_children={1: 1},
    )
    cache_step_id = cache_steps["1"]
    created_cache_rows = a.rightbar_task_rows(state, 10)
    assert [row for row in created_cache_rows if row[1] == cache_step_id and row[3] == "created"], created_cache_rows
    cache_started = a.start_subagent_task(
        state,
        cache_agent,
        "read cache lifecycle fixture",
        source="user",
        parent_task_id=cache_step_id,
        task_title="Delegate to cache lifecycle agent",
    )
    assert cache_started.startswith("已启动子 agent"), cache_started
    cache_bus_task_id = cache_agent.active_bus_task_id
    cache_stream_task_id = cache_agent.active_task_id
    working_cache_rows = a.rightbar_task_rows(state, 10)
    cache_visible_ids = {cache_step_id, cache_bus_task_id}
    assert [row for row in working_cache_rows if row[1] in cache_visible_ids and row[3] == "working"], working_cache_rows
    assert a.latest_task_records()[cache_step_id]["status"] == "working"
    assert cache_bus_task_id and cache_stream_task_id is not None
    state.ui_queue.put(("sub_stream", cache_agent.agent_id, cache_stream_task_id, "cached lifecycle result", True))
    a.process_ui_queue(state)
    completed_cache_rows = a.rightbar_task_rows(state, 10)
    assert [row for row in completed_cache_rows if row[1] in cache_visible_ids and row[3] == "done"], completed_cache_rows
    assert a.latest_task_records()[cache_step_id]["status"] == "completed"
    cache_child_row = a.latest_task_records()[cache_bus_task_id]
    assert cache_child_row["status"] == "completed", cache_child_row
    assert cache_child_row["summary"], cache_child_row
    assert any("/subagent-results/" in str(ref) for ref in cache_child_row["artifact_refs"]), cache_child_row

    orchestration_text = ga_control(
        plan_action("双代理对话演示", ["创建正式子代理(永久)", "创建临时子代理", "两个代理各自先向我说话", "两个代理互相聊天交流", "汇总所有对话内容"]),
        create_agent_action("正式甲", persistent=True, profile="你是正式永久子代理，名叫正式甲。稍后和临时子代理临时乙交流。", plan_step_id="创建正式子代理(永久)"),
        create_agent_action("临时乙", temporary=True, profile="你是临时子代理，名叫临时乙。稍后和正式子代理正式甲交流。", plan_step_id="创建临时子代理"),
        delegate_action("正式甲", "请先向主控说一句话自我介绍，说完了告诉我。", parent_task_id="两个代理各自先向我说话"),
        delegate_action("临时乙", "请先向主控说一句话自我介绍，说完了告诉我。", parent_task_id="两个代理各自先向我说话"),
    )
    a.apply_tui_controls_from_text(state, orchestration_text, source="agent")
    formal = next(sub for sub in state.subagents.values() if sub.name == "正式甲")
    temporary = next(sub for sub in state.subagents.values() if sub.name == "临时乙")
    assert formal.persistent is True, formal
    assert temporary.persistent is False, temporary
    assert formal.agent_id != temporary.agent_id
    orchestration_plan_id = state.active_plan_task_id
    orchestration_steps = sorted(
        [
            (task_id, row)
            for task_id, row in a.latest_task_records().items()
            if row.get("parent_task_id") == orchestration_plan_id
            and row.get("kind") in {"plan_step", "plan_summary"}
        ],
        key=lambda item: item[1].get("order", 0),
    )
    assert [row["status"] for _task_id, row in orchestration_steps[:3]] == ["completed", "completed", "working"], orchestration_steps
    assert [row["status"] for _task_id, row in orchestration_steps[3:]] == ["created", "created"], orchestration_steps
    speak_step_id = orchestration_steps[2][0]
    speak_children = [
        row for row in a.latest_task_records().values()
        if row.get("parent_task_id") == speak_step_id and row.get("kind") == "subagent_task"
    ]
    assert {row["assigned_agent"] for row in speak_children} == {formal.agent_id, temporary.agent_id}, speak_children
    drain_ui(state)
    orchestration_latest = a.latest_task_records()
    assert orchestration_latest[speak_step_id]["status"] == "completed", orchestration_latest[speak_step_id]
    assert [orchestration_latest[task_id]["status"] for task_id, _row in orchestration_steps[3:]] == ["created", "created"]

    role_result = a.apply_subagent_control(state, "subagent_role", reader.agent_id, "ops", {"role": "ops"}, source="agent-control")
    assert role_result.startswith("APPROVAL_REQUIRED"), role_result
    role_policy = latest_approval(approval_type="policy_approval_request", deferred="set_subagent_role")
    role_approved = a.decide_approval(state, str(role_policy["approval_id"]), True)
    assert "已设置子 agent 角色" in role_approved, role_approved
    assert reader.role == "ops", reader.role

    cancel_agent = a.create_subagent(state, "Cancel Agent", role="researcher")
    cancel_task = "task_cancel_test"
    a.append_task_ledger(cancel_task, status="working", assigned_agent=cancel_agent.agent_id, objective="cancel me")
    cancelled = a.recover_task_action(state, cancel_task, "cancelled")
    assert "cancelled" in cancelled, cancelled
    cancel_recovery = [row for row in a.read_jsonl(a.AGENT_RECOVERY_PATH) if row.get("task_id") == cancel_task and row.get("action") == "cancelled"]
    assert cancel_recovery
    assert_recovery_schema(cancel_recovery[-1], action="cancelled")
    cancel_checkpoints = [row for row in a.read_jsonl(a.AGENT_CHECKPOINT_INDEX_PATH) if row.get("task_id") == cancel_task]
    assert len(cancel_checkpoints) >= 2, cancel_checkpoints
    assert any(row.get("reason") == "recovery_before_cancelled" for row in cancel_checkpoints), cancel_checkpoints
    assert any(row.get("reason") == "recovery_after_cancelled" for row in cancel_checkpoints), cancel_checkpoints
    cancel_plans = [row for row in a.read_jsonl(a.AGENT_RECOVERY_PLANS_PATH) if row.get("task_id") == cancel_task and row.get("action") == "cancelled"]
    assert cancel_plans
    assert_recovery_plan_schema(cancel_plans[-1], action="cancelled")
    assert cancel_recovery[-1]["recovery_plan_id"] == cancel_plans[-1]["recovery_plan_id"], cancel_recovery[-1]
    assert cancel_recovery[-1]["recovery_plan_ref"] == cancel_plans[-1]["artifact_refs"][0], cancel_recovery[-1]
    recovery_plan_artifacts = [row for row in a.read_jsonl(a.AGENT_ARTIFACT_INDEX_PATH) if row.get("type") == "recovery-plans"]
    assert recovery_plan_artifacts
    assert_artifact_schema(recovery_plan_artifacts[-1], artifact_type="recovery-plans")

    retry_agent = a.create_subagent(state, "Retry Agent", role="researcher")
    retry_task = "task_retry_test"
    a.append_task_ledger(retry_task, status="working", assigned_agent=retry_agent.agent_id, objective="read docs again")
    retry_blocked = a.recover_task_action(state, retry_task, "retry")
    assert retry_blocked.startswith("APPROVAL_REQUIRED"), retry_blocked
    retry_policy = latest_approval(approval_type="policy_approval_request", deferred="recover_task_action")
    assert retry_policy["payload"]["recovery_plan_id"], retry_policy
    assert str(retry_policy["payload"]["recovery_plan_ref"]).startswith("artifact://artifacts/recovery-plans/"), retry_policy
    retry_recovery_wait = [row for row in a.read_jsonl(a.AGENT_RECOVERY_PATH) if row.get("task_id") == retry_task and row.get("action") == "retry" and row.get("status") == "approval_required"]
    assert retry_recovery_wait
    assert_recovery_schema(retry_recovery_wait[-1], action="retry")
    retry_wait_plan = [row for row in a.read_jsonl(a.AGENT_RECOVERY_PLANS_PATH) if row.get("recovery_plan_id") == retry_policy["payload"]["recovery_plan_id"]]
    assert retry_wait_plan
    assert_recovery_plan_schema(retry_wait_plan[-1], action="retry")
    assert retry_wait_plan[-1]["approval"]["approval_required"] is True, retry_wait_plan[-1]
    retry_approved = a.decide_approval(state, str(retry_policy["approval_id"]), True)
    assert "已启动子 agent" in retry_approved, retry_approved
    retry_recovery = [row for row in a.read_jsonl(a.AGENT_RECOVERY_PATH) if row.get("task_id") == retry_task and row.get("action") == "retry" and row.get("status") == "restarted"]
    assert retry_recovery
    assert_recovery_schema(retry_recovery[-1], action="retry")
    retry_approved_plans = [
        row for row in a.read_jsonl(a.AGENT_RECOVERY_PLANS_PATH)
        if row.get("task_id") == retry_task and row.get("action") == "retry" and row.get("status") == "approved_replay"
    ]
    assert retry_approved_plans
    assert_recovery_plan_schema(retry_approved_plans[-1], action="retry")
    assert retry_recovery[-1]["recovery_plan_id"] == retry_approved_plans[-1]["recovery_plan_id"], retry_recovery[-1]
    retry_checkpoints = [row for row in a.read_jsonl(a.AGENT_CHECKPOINT_INDEX_PATH) if row.get("task_id") == retry_task]
    assert any(row.get("reason") == "recovery_before_retry" for row in retry_checkpoints), retry_checkpoints
    assert any(row.get("reason") == "recovery_retry_superseded" for row in retry_checkpoints), retry_checkpoints

    curated = a.queue_curated_memory_candidate(
        state,
        retry_agent,
        "Useful validated memory",
        source="subagent:test",
        evidence_ref="trace://x",
        task_id="task_mem",
    )
    assert "等待审批" in curated, curated
    memory_artifacts = [row for row in a.read_jsonl(a.AGENT_ARTIFACT_INDEX_PATH) if row.get("type") == "memory-candidates"]
    assert memory_artifacts
    assert_artifact_schema(memory_artifacts[-1], artifact_type="memory-candidates")
    assert memory_artifacts[-1]["provenance"].get("target_subagent") == retry_agent.agent_id, memory_artifacts[-1]
    assert memory_artifacts[-1]["provenance"].get("memory_candidate_id"), memory_artifacts[-1]
    candidate_rows = a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)
    assert candidate_rows
    candidate = candidate_rows[-1]["memory_candidate"]
    assert_memory_candidate_schema(candidate)
    assert candidate["target_subagent"] == retry_agent.agent_id, candidate
    assert candidate["task_id"] == "task_mem", candidate
    assert candidate["artifact_refs"] == [memory_artifacts[-1]["uri"]], candidate
    memory_request = latest_approval(approval_type="memory_write_request")
    assert memory_request.get("approval_required_for") == "write_long_term_memory", memory_request
    assert_memory_candidate_schema(memory_request["payload"]["memory_candidate"])
    assert memory_request["payload"]["memory_candidate"]["candidate_id"] == candidate["candidate_id"], memory_request
    candidate_traces = [row for row in a.read_jsonl(a.AGENT_TRACES_PATH) if row.get("event") == "memory_candidate_curated" and row.get("task_id") == "task_mem"]
    assert candidate_traces
    assert_trace_schema(candidate_traces[-1])
    assert candidate_traces[-1]["audit_refs"]["artifacts"] == [memory_artifacts[-1]["uri"]], candidate_traces[-1]
    assert candidate_traces[-1]["audit_refs"]["memory_candidates"] == [candidate["candidate_id"]], candidate_traces[-1]
    assert candidate_traces[-1]["payload"]["dedupe_key"] == candidate["dedupe_key"], candidate_traces[-1]
    approved_memory = a.decide_approval(state, str(memory_request["approval_id"]), True)
    assert "已批准并执行" in approved_memory, approved_memory
    approved_candidates = [
        row for row in a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)
        if row.get("status") == "approved" and row.get("candidate_id") == candidate["candidate_id"]
    ]
    assert approved_candidates, a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)
    assert candidate["statement"] in a.read_text_file(a.subagent_memory_path(retry_agent.agent_id), ""), candidate
    duplicate = a.queue_curated_memory_candidate(
        state,
        retry_agent,
        "Useful validated memory",
        source="subagent:test",
        evidence_ref="trace://x",
        task_id="task_mem_duplicate",
    )
    assert "等待审批" in duplicate, duplicate
    duplicate_candidate = a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)[-1]["memory_candidate"]
    assert_memory_candidate_schema(duplicate_candidate)
    assert duplicate_candidate["dedupe_key"] == candidate["dedupe_key"], duplicate_candidate
    assert duplicate_candidate["duplicate_of"], duplicate_candidate
    assert any(str(ref).startswith("memory-candidate://") for ref in duplicate_candidate["duplicate_of"]), duplicate_candidate
    approval_count_before_reject = len(a.read_jsonl(a.AGENT_APPROVALS_PATH))
    rejected = a.queue_curated_memory_candidate(
        state,
        retry_agent,
        "api_key: REDACTED_TEST_CREDENTIAL",
        source="subagent:test",
        evidence_ref="trace://secret",
        task_id="task_secret_reject",
    )
    assert "已拒绝记忆候选" in rejected, rejected
    assert len(a.read_jsonl(a.AGENT_APPROVALS_PATH)) == approval_count_before_reject, a.read_jsonl(a.AGENT_APPROVALS_PATH)
    rejected_row = a.read_jsonl(a.AGENT_MEMORY_CANDIDATES_PATH)[-1]
    assert rejected_row["status"] == "rejected", rejected_row
    rejected_candidate = rejected_row["memory_candidate"]
    assert_memory_candidate_schema(rejected_candidate)
    assert rejected_candidate["rejected_reason"] == "privacy_risk_secret_or_credential", rejected_candidate
    rejection_mail = [
        row for row in a.read_jsonl(a.AGENT_MAIL_PATH)
        if row.get("intent") == "memory_candidate_rejected" and row.get("task_id") == "task_secret_reject"
    ]
    assert rejection_mail, a.read_jsonl(a.AGENT_MAIL_PATH)
    assert_mail_schema(rejection_mail[-1], intent="memory_candidate_rejected")
    rejection_traces = [
        row for row in a.read_jsonl(a.AGENT_TRACES_PATH)
        if row.get("event") == "memory_candidate_rejected" and row.get("task_id") == "task_secret_reject"
    ]
    assert rejection_traces, a.read_jsonl(a.AGENT_TRACES_PATH)
    assert_trace_schema(rejection_traces[-1])
    assert rejected_candidate["candidate_id"] in rejection_traces[-1]["audit_refs"]["memory_candidates"], rejection_traces[-1]
    assert os.path.exists(a.AGENT_POLICY_DECISIONS_PATH)
    state.running = False


def main() -> int:
    run_checks()
    print("policy gate checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
