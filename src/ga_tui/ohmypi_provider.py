"""Oh My Pi runtime provider for the GA TUI control plane.

The integration uses Oh My Pi's JSONL stdio RPC mode as a process boundary.
The wrapper intentionally presents the small GenericAgent-shaped surface that
the current TUI still consumes while keeping Oh My Pi protocol details local to
this module.
"""
from __future__ import annotations

import json
import re
import os
import queue
import shlex
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

try:
    from .runtime import RuntimeAdapter, RuntimeProviderSpec
except Exception:
    from runtime import RuntimeAdapter, RuntimeProviderSpec  # type: ignore


ProcessFactory = Callable[..., Any]
ThreadFactory = Callable[..., Any]
MemoryCandidateSink = Callable[[dict[str, Any]], None]
HostToolHandler = Callable[[str, dict[str, Any]], dict[str, Any]]

GA_TUI_MEMORY_PROMPT_FILENAME = "ohmypi-ga-tui-memory.md"
GA_TUI_MEMORY_PROMPT_HEADER = "GA/TUI Memory Guidance"
MAX_HOST_TOOL_RESULT_CHARS = 12000
_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"),
    re.compile(r"\b(api[_-]?key|secret|token|password|passwd|密码|密钥)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_\-]{24,}\.[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{12,}\b"),
)


class _TaskCounter:
    def __init__(self) -> None:
        self._unfinished_tasks = 0
        self._lock = threading.Lock()

    @property
    def unfinished_tasks(self) -> int:
        with self._lock:
            return self._unfinished_tasks

    def start(self) -> None:
        with self._lock:
            self._unfinished_tasks += 1

    def done(self) -> None:
        with self._lock:
            self._unfinished_tasks = max(0, self._unfinished_tasks - 1)


@dataclass
class _OhMyPiBackend:
    name: str = "Oh My Pi"
    model: str = "unknown"
    api_base: str = ""
    apibase: str = ""
    log_path: str = ""

    def __post_init__(self) -> None:
        self.history: list[dict[str, Any]] = []

    def raw_ask(self, _request: Any) -> Any:
        raise RuntimeError("Oh My Pi RPC provider does not expose raw_ask.")
        yield  # pragma: no cover


@dataclass
class _OhMyPiClient:
    backend: _OhMyPiBackend
    log_path: str = ""
    last_tools: str = ""


@dataclass
class _ActivePrompt:
    request_id: str
    display_queue: queue.Queue
    source: str = ""
    buffer: str = ""
    finished: bool = False


@dataclass(frozen=True)
class RpcHostToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    label: str = ""
    hidden: bool = False

    def to_rpc(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
        if self.label:
            data["label"] = self.label
        if self.hidden:
            data["hidden"] = True
        return data


def _host_tool_definition_to_rpc(definition: RpcHostToolDefinition | dict[str, Any]) -> dict[str, Any]:
    if isinstance(definition, RpcHostToolDefinition):
        return definition.to_rpc()
    if isinstance(definition, dict):
        return dict(definition)
    return {}


def _bounded_host_tool_text(value: Any, *, max_chars: int = MAX_HOST_TOOL_RESULT_CHARS) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        text = json.dumps(str(value), ensure_ascii=False)
    text = _redact_memory_text(text)
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n...[truncated]"
    return text


def _host_tool_agent_result(value: Any) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": _bounded_host_tool_text(value),
            }
        ]
    }


class OhMyPiRpcAgent:
    """Small queue-compatible wrapper around `omp --mode rpc`."""

    def __init__(
        self,
        *,
        command: list[str] | None = None,
        cwd: str | None = None,
        process_factory: ProcessFactory | None = None,
        thread_factory: ThreadFactory = threading.Thread,
        memory_candidate_sink: MemoryCandidateSink | None = None,
        host_tool_definitions: list[RpcHostToolDefinition | dict[str, Any]] | None = None,
        host_tool_handler: HostToolHandler | None = None,
        startup_timeout: float = 10.0,
        stop_timeout: float = 3.0,
    ) -> None:
        self.command = list(command or ohmypi_rpc_command())
        self.cwd = cwd or os.getcwd()
        self.process_factory = process_factory or subprocess.Popen
        self.thread_factory = thread_factory
        self.memory_candidate_sink = memory_candidate_sink
        self.host_tool_definitions = [
            item
            for item in (_host_tool_definition_to_rpc(definition) for definition in (host_tool_definitions or []))
            if item.get("name")
        ]
        self.host_tool_handler = host_tool_handler
        self.startup_timeout = startup_timeout
        self.stop_timeout = stop_timeout
        self.task_queue = _TaskCounter()
        self.is_running = False
        self.log_path = ""
        self.history: list[str] = []
        self.handler = None
        self.llm_no = 0
        self.llmclient = _OhMyPiClient(_OhMyPiBackend())
        self.llmclients = [self.llmclient]
        self._process: Any = None
        self._ready = threading.Event()
        self._send_lock = threading.Lock()
        self._active_lock = threading.Lock()
        self._active: _ActivePrompt | None = None
        self._request_no = 0
        self._stderr_tail: list[str] = []
        self._closed = False
        self._host_tools_registered = False

    def configure_host_tools(
        self,
        *,
        host_tool_definitions: list[RpcHostToolDefinition | dict[str, Any]] | None = None,
        host_tool_handler: HostToolHandler | None = None,
    ) -> None:
        if host_tool_definitions is not None:
            self.host_tool_definitions = [
                item
                for item in (_host_tool_definition_to_rpc(definition) for definition in host_tool_definitions)
                if item.get("name")
            ]
            self._host_tools_registered = False
        if host_tool_handler is not None:
            self.host_tool_handler = host_tool_handler
        if self._process is not None and self._process.poll() is None and self._ready.is_set():
            self._register_host_tools()

    def run(self) -> None:
        return None

    def load_llm_sessions(self) -> None:
        if self._process is not None:
            self._send({"id": self._next_request_id("models"), "type": "get_available_models"})

    def next_llm(self, index: int = -1) -> None:
        del index
        if self._process is not None:
            self._send({"id": self._next_request_id("cycle"), "type": "cycle_model"})

    def list_llms(self) -> list[tuple[int, str, bool]]:
        return [(0, self.get_llm_name(model=False), True)]

    def get_llm_name(self, b: Any = None, model: bool = False) -> str:
        client = self.llmclient if b is None else b
        backend = getattr(client, "backend", self.llmclient.backend)
        if model:
            return str(getattr(backend, "model", "") or "unknown")
        return f"OhMyPi/{getattr(backend, 'name', 'Oh My Pi')}"

    def put_task(self, prompt: str, source: str = "", images: Any = None) -> queue.Queue:
        del images
        display_queue: queue.Queue = queue.Queue()
        with self._active_lock:
            if self._active is not None and not self._active.finished:
                display_queue.put({"done": "[Oh My Pi] 当前 RPC 会话仍在运行，不能并发启动新任务。", "source": source})
                return display_queue
            request_id = self._next_request_id("prompt")
            self._active = _ActivePrompt(request_id=request_id, display_queue=display_queue, source=source)
            self.is_running = True
            self.task_queue.start()

        def _runner() -> None:
            try:
                self._ensure_process()
                self._send({"id": request_id, "type": "prompt", "message": prompt})
            except Exception as exc:
                self._finish_active(f"[Oh My Pi] 启动失败: {type(exc).__name__}: {exc}", source=source)

        self.thread_factory(target=_runner, daemon=True, name="ohmypi-rpc-submit").start()
        return display_queue

    def abort(self) -> None:
        try:
            self._send({"id": self._next_request_id("abort"), "type": "abort"})
        except Exception:
            pass
        self._finish_active("[Oh My Pi] 已请求中止。")

    def close(self) -> None:
        self._closed = True
        process = self._process
        if process is None:
            return
        try:
            stdin = getattr(process, "stdin", None)
            if stdin is not None:
                stdin.close()
        except Exception:
            pass
        self._terminate_process(process)

    def _next_request_id(self, prefix: str) -> str:
        self._request_no += 1
        return f"ga-tui-{prefix}-{self._request_no}"

    def _ensure_process(self) -> None:
        if self._process is not None and self._process.poll() is None:
            if self._ready.wait(self.startup_timeout):
                return
            raise RuntimeError("RPC ready timeout")
        binary = self.command[0] if self.command else "omp"
        if os.path.sep not in binary and shutil.which(binary) is None:
            raise FileNotFoundError(f"`{binary}` executable not found")
        self._ready.clear()
        self._host_tools_registered = False
        self._process = self.process_factory(
            self.command,
            cwd=self.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self.thread_factory(target=self._read_stdout, daemon=True, name="ohmypi-rpc-stdout").start()
        self.thread_factory(target=self._read_stderr, daemon=True, name="ohmypi-rpc-stderr").start()
        if not self._ready.wait(self.startup_timeout):
            self._terminate_process(self._process)
            raise RuntimeError("RPC ready timeout")

    def _read_stdout(self) -> None:
        process = self._process
        stdout = getattr(process, "stdout", None)
        if stdout is None:
            return
        try:
            for raw_line in stdout:
                if self._closed:
                    return
                line = str(raw_line or "").strip()
                if not line:
                    continue
                try:
                    frame = json.loads(line)
                except json.JSONDecodeError:
                    self._remember_stderr(f"non-json stdout: {line[:200]}")
                    continue
                if isinstance(frame, dict):
                    self._handle_frame(frame)
        finally:
            if not self._closed:
                self._finish_active("[Oh My Pi] RPC 进程已退出。")

    def _read_stderr(self) -> None:
        process = self._process
        stderr = getattr(process, "stderr", None)
        if stderr is None:
            return
        try:
            for raw_line in stderr:
                line = str(raw_line or "").strip()
                if line:
                    self._remember_stderr(line)
        except Exception:
            return

    def _handle_frame(self, frame: dict[str, Any]) -> None:
        frame_type = str(frame.get("type") or "")
        if frame_type == "ready":
            self._register_host_tools()
            self._ready.set()
            return
        if frame_type == "response":
            self._handle_response(frame)
            return
        if frame_type == "host_tool_call":
            self._handle_host_tool_call(frame)
            return
        if frame_type == "host_tool_cancel":
            self._handle_host_tool_cancel(frame)
            return
        if frame_type == "message_update":
            event = frame.get("assistantMessageEvent")
            if isinstance(event, dict) and event.get("type") == "text_delta":
                self._append_active_delta(str(event.get("delta") or ""))
            return
        if frame_type in {"agent_end", "turn_end"}:
            self._finish_active()
            return
        if frame_type == "extension_ui_request":
            self._answer_extension_ui(frame)
            return

    def _handle_response(self, frame: dict[str, Any]) -> None:
        command = str(frame.get("command") or "")
        if frame.get("success") is False:
            error = str(frame.get("error") or "unknown RPC error")
            if command in {"prompt", "abort_and_prompt"}:
                self._finish_active(f"[Oh My Pi] RPC prompt failed: {error}")
            return
        data = frame.get("data")
        if command in {"get_state", "set_model"} and isinstance(data, dict):
            model = data.get("model")
            if isinstance(model, dict):
                self._update_model(model)
        if command == "cycle_model" and isinstance(data, dict):
            model = data.get("model")
            if isinstance(model, dict):
                self._update_model(model)
        if command == "get_available_models" and isinstance(data, dict):
            models = data.get("models")
            if isinstance(models, list) and models:
                first = models[0]
                if isinstance(first, dict):
                    self._update_model(first)

    def _update_model(self, model: dict[str, Any]) -> None:
        provider = str(model.get("provider") or self.llmclient.backend.name or "Oh My Pi")
        model_id = str(model.get("id") or model.get("modelId") or self.llmclient.backend.model or "unknown")
        name = str(model.get("name") or provider or "Oh My Pi")
        self.llmclient.backend.name = provider or name
        self.llmclient.backend.model = model_id

    def _append_active_delta(self, delta: str) -> None:
        if not delta:
            return
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            active.buffer += delta
            active.display_queue.put({"next": delta, "source": "ohmypi"})

    def _finish_active(self, text: str | None = None, *, source: str = "ohmypi") -> None:
        done_text = ""
        signal_source = source
        request_id = ""
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                self.is_running = False
                return
            active.finished = True
            done_text = active.buffer if text is None else text
            signal_source = active.source or source
            request_id = active.request_id
            active.display_queue.put({"done": done_text, "source": source})
            self._active = None
            self.is_running = False
            self.task_queue.done()
        self._emit_memory_candidate_signal(done_text, source=signal_source, request_id=request_id)

    def _emit_memory_candidate_signal(self, text: str, *, source: str, request_id: str) -> None:
        if self.memory_candidate_sink is None:
            return
        signal = ohmypi_memory_candidate_signal(text, source=source, request_id=request_id)
        if signal is None:
            return
        try:
            self.memory_candidate_sink(signal)
        except Exception as exc:
            self._remember_stderr(f"memory candidate sink failed: {type(exc).__name__}: {exc}")

    def _answer_extension_ui(self, frame: dict[str, Any]) -> None:
        request_id = frame.get("id")
        if not request_id:
            return
        method = str(frame.get("method") or "")
        if method == "confirm":
            self._send({"type": "extension_ui_response", "id": request_id, "confirmed": False})
        elif method in {"select", "input", "editor"}:
            self._send({"type": "extension_ui_response", "id": request_id, "cancelled": True})

    def _register_host_tools(self) -> None:
        if self._host_tools_registered or not self.host_tool_definitions:
            return
        try:
            self._send({
                "id": self._next_request_id("host-tools"),
                "type": "set_host_tools",
                "tools": list(self.host_tool_definitions),
            })
            self._host_tools_registered = True
        except Exception as exc:
            self._remember_stderr(f"host tool registration failed: {type(exc).__name__}: {exc}")

    def _handle_host_tool_call(self, frame: dict[str, Any]) -> None:
        request_id = str(frame.get("id") or "")
        tool_name = str(frame.get("toolName") or "")
        args = frame.get("arguments")
        arguments = args if isinstance(args, dict) else {}
        if not request_id:
            self._remember_stderr("host tool call missing id")
            return
        allowed_names = {str(tool.get("name") or "") for tool in self.host_tool_definitions}
        if not tool_name or tool_name not in allowed_names:
            self._send_host_tool_result(
                request_id,
                {
                    "schema_version": "ga-tui.host_tool.v1",
                    "status": "error",
                    "error": f"Unknown or unregistered host tool: {tool_name or '<missing>'}",
                },
                is_error=True,
            )
            return
        if self.host_tool_handler is None:
            self._send_host_tool_result(
                request_id,
                {
                    "schema_version": "ga-tui.host_tool.v1",
                    "status": "error",
                    "tool_name": tool_name,
                    "error": "No host tool handler is configured.",
                },
                is_error=True,
            )
            return
        try:
            result = self.host_tool_handler(tool_name, dict(arguments))
        except Exception as exc:
            self._send_host_tool_result(
                request_id,
                {
                    "schema_version": "ga-tui.host_tool.v1",
                    "status": "error",
                    "tool_name": tool_name,
                    "error": f"{type(exc).__name__}: {exc}",
                },
                is_error=True,
            )
            return
        self._send_host_tool_result(request_id, result)

    def _handle_host_tool_cancel(self, frame: dict[str, Any]) -> None:
        target_id = str(frame.get("targetId") or "")
        if target_id:
            self._remember_stderr(f"host tool cancel requested: {target_id}")

    def _send_host_tool_result(self, request_id: str, result: Any, *, is_error: bool = False) -> None:
        frame: dict[str, Any] = {
            "type": "host_tool_result",
            "id": request_id,
            "result": _host_tool_agent_result(result),
        }
        if is_error:
            frame["isError"] = True
        try:
            self._send(frame)
        except Exception as exc:
            self._remember_stderr(f"host tool result failed: {type(exc).__name__}: {exc}")

    def _send(self, obj: dict[str, Any]) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            raise RuntimeError("Oh My Pi RPC process is not running")
        stdin = getattr(process, "stdin", None)
        if stdin is None:
            raise RuntimeError("Oh My Pi RPC stdin is unavailable")
        payload = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._send_lock:
            stdin.write(payload)
            stdin.flush()

    def _remember_stderr(self, line: str) -> None:
        self._stderr_tail.append(line)
        if len(self._stderr_tail) > 20:
            del self._stderr_tail[:-20]

    def _terminate_process(self, process: Any) -> None:
        try:
            if process.poll() is not None:
                return
        except Exception:
            return
        try:
            process.terminate()
            process.wait(timeout=self.stop_timeout)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


class OhMyPiRuntimeAdapter(RuntimeAdapter):
    def __init__(
        self,
        spec: RuntimeProviderSpec,
        *,
        command: list[str] | None = None,
        cwd: str | None = None,
        process_factory: ProcessFactory | None = None,
        thread_factory: ThreadFactory = threading.Thread,
        memory_candidate_sink: MemoryCandidateSink | None = None,
        host_tool_definitions: list[RpcHostToolDefinition | dict[str, Any]] | None = None,
        host_tool_handler: HostToolHandler | None = None,
    ) -> None:
        super().__init__(spec)
        self.command = command
        self.cwd = cwd
        self.process_factory = process_factory
        self.thread_factory = thread_factory
        self.memory_candidate_sink = memory_candidate_sink
        self.host_tool_definitions = list(host_tool_definitions or [])
        self.host_tool_handler = host_tool_handler

    def create_agent(self) -> OhMyPiRpcAgent:
        return OhMyPiRpcAgent(
            command=self.command,
            cwd=self.cwd,
            process_factory=self.process_factory,
            thread_factory=self.thread_factory,
            memory_candidate_sink=self.memory_candidate_sink,
            host_tool_definitions=self.host_tool_definitions,
            host_tool_handler=self.host_tool_handler,
        )

    def prepare_agent(self, agent: Any, *, state: Any = None) -> None:
        del state
        if hasattr(agent, "load_llm_sessions"):
            try:
                agent.load_llm_sessions()
            except Exception:
                pass

    def start_agent(self, agent: Any, *, thread_name: str = "") -> Any:
        if not thread_name:
            thread_name = "ga-tui-ohmypi"
        setattr(agent, "_ga_tui_thread_name", thread_name)
        return None


def _has_cli_flag(args: list[str], flag: str) -> bool:
    return any(item == flag or item.startswith(flag + "=") for item in args)


def ohmypi_rpc_command(
    binary: str | None = None,
    extra_args: list[str] | None = None,
    append_system_prompt: str | None = None,
) -> list[str]:
    binary = binary or os.environ.get("GA_TUI_OHMYPI_BIN", "omp")
    env_args = shlex.split(os.environ.get("GA_TUI_OHMYPI_ARGS", ""))
    appended_args = list(extra_args or env_args)
    args = [
        binary,
        "--mode",
        "rpc",
        "--no-title",
        "--approval-mode",
        "always-ask",
    ]
    if append_system_prompt and not _has_cli_flag(appended_args, "--append-system-prompt"):
        args.extend(["--append-system-prompt", append_system_prompt])
    args.extend(appended_args)
    return args


def ohmypi_memory_prompt_path(harness_dir: str) -> str:
    return os.path.join(harness_dir, "runtime", GA_TUI_MEMORY_PROMPT_FILENAME)


def _read_text_if_exists(path: str, *, max_chars: int = 4000) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(max_chars)
    except OSError:
        return ""


def _redact_memory_text(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _bounded_section(title: str, path: str, text: str, *, max_chars: int = 2200) -> str:
    text = _redact_memory_text(text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n...[truncated]"
    if not text:
        text = "(not available)"
    return f"## {title}\n\nSource: `{path}`\n\n{text}\n"


def build_ohmypi_memory_prompt(*, root_dir: str, harness_dir: str) -> str:
    memory_dir = os.path.join(root_dir, "memory")
    insight_path = os.path.join(memory_dir, "global_mem_insight.txt")
    global_path = os.path.join(memory_dir, "global_mem.txt")
    sop_path = os.path.join(memory_dir, "memory_management_sop.md")
    sections = [
        f"# {GA_TUI_MEMORY_PROMPT_HEADER}",
        "",
        "You are running as the Oh My Pi execution runtime inside GenericAgent-TUI.",
        "GenericAgent-TUI remains the Orchestrator: it owns task ledgers, approvals, artifact refs, and long-term memory governance.",
        "Use the memory below as heuristic context. Verify current repository state before acting when memory could be stale.",
        "Do not write long-term memory directly. If execution reveals a durable, verified lesson, include it in your final answer under `Memory candidates` with evidence refs.",
        "Never expose or store secrets. Treat redacted or credential-looking content as unavailable.",
        "",
        _bounded_section("L1 Global Memory Index", insight_path, _read_text_if_exists(insight_path, max_chars=3500), max_chars=2600),
        _bounded_section("L2 Global Memory Facts", global_path, _read_text_if_exists(global_path, max_chars=3500), max_chars=2600),
        _bounded_section("L0 Memory Governance", sop_path, _read_text_if_exists(sop_path, max_chars=2800), max_chars=2200),
        "## TUI Governance Refs",
        "",
        f"- Runtime harness dir: `{harness_dir}`",
        "- Architecture baseline: `docs/agent-harness-architecture.md`",
        "- Runtime provider contract: `docs/runtime-provider-control-plane.md`",
        "- Control protocol spec: `.trellis/spec/backend/agent-control-protocol.md`",
        "",
    ]
    return "\n".join(sections).rstrip() + "\n"


def write_ohmypi_memory_prompt(*, root_dir: str, harness_dir: str) -> str:
    path = ohmypi_memory_prompt_path(harness_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = build_ohmypi_memory_prompt(root_dir=root_dir, harness_dir=harness_dir)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(tmp_path, path)
    return path


def ohmypi_memory_candidate_signal(text: str, *, source: str = "", request_id: str = "") -> dict[str, Any] | None:
    statement = _redact_memory_text(str(text or "")).strip()
    if not statement or len(statement) < 80:
        return None
    if statement.startswith("[Oh My Pi]"):
        return None
    if "[REDACTED]" in statement:
        return None
    return {
        "schema_version": "ohmypi.memory_candidate_signal.v1",
        "source": source or "ohmypi",
        "request_id": request_id,
        "statement": statement[:2400].rstrip(),
        "evidence_ref": f"runtime://provider/ohmypi/{request_id}" if request_id else "runtime://provider/ohmypi",
        "requires_human_approval": True,
    }


def ohmypi_provider_spec(
    *,
    root_dir: str,
    harness_dir: str,
    recent_models_path: str,
    schedules_path: str,
    binary: str | None = None,
    command: list[str] | None = None,
) -> RuntimeProviderSpec:
    command = list(command or ohmypi_rpc_command(binary=binary))
    executable = command[0]
    exists = shutil.which(executable) is not None if os.path.sep not in executable else os.path.exists(executable)
    return RuntimeProviderSpec(
        provider_id="ohmypi",
        name="Oh My Pi",
        runtime_type="local_bun_agent",
        status="active" if exists else "missing",
        transport="jsonl_stdio_rpc",
        entrypoints=["omp --mode rpc", "packages/coding-agent/src/modes/rpc/rpc-mode.ts"],
        capabilities={
            "streaming": True,
            "interrupt": True,
            "session_restore": True,
            "tool_calling": True,
            "host_tools": False,
            "tui_readonly_host_tools": True,
            "tui_governed_proposal_tools": True,
            "artifact_refs": True,
            "memory_candidates": True,
            "memory_candidate_signals": True,
            "human_approval": False,
            "subagents": True,
            "provider_owned_subagents": True,
        },
        model_routing={
            "owner": "ohmypi.rpc",
            "supports_runtime_switch": False,
            "supports_default_model": False,
            "supports_per_agent_default": False,
            "recent_models_path": recent_models_path,
            "selection_contract": "Oh My Pi model registry via RPC get_state/get_available_models",
        },
        scheduler={
            "owner": "ga-tui.control_plane",
            "status": "not_enabled",
            "schedules_path": schedules_path,
            "dispatch_contract": "agenttask.v2",
            "runtime_provider_id": "ohmypi",
        },
        policy={
            "approval_gate_owner": "ga-tui.policy",
            "tool_permissions": "tui_readonly_and_governed_proposal_tools_only",
            "memory_write": "candidate_only",
            "risky_actions": ["deploy", "external_send", "delete_file", "spend_money", "access_secret"],
        },
        a2a={
            "agent_card": "runtime://provider/ohmypi",
            "task_transport": "jsonl_stdio_rpc",
            "artifact_transport": "provider_artifact_ref",
        },
        mcp={
            "tool_gateway": "not_exposed",
            "resource_gateway": "not_exposed",
        },
        notes=[
            "Experiment branch default provider; GenericAgent remains available via GA_TUI_RUNTIME_PROVIDER=genericagent.",
            "Oh My Pi runs out-of-process through JSONL stdio RPC.",
            "GenericAgent/TUI memory is injected through --append-system-prompt.",
            "Oh My Pi completion text can emit memory candidate signals; TUI remains the approval owner.",
            "Only app-injected TUI query and governed proposal host tools are enabled; unrestricted host tools, host URI schemes, and direct TUI approval mapping stay disabled.",
            f"runtime_root={root_dir}",
            f"harness_dir={harness_dir}",
            f"command={' '.join(command)}",
        ],
    )


__all__ = [
    "OhMyPiRpcAgent",
    "OhMyPiRuntimeAdapter",
    "build_ohmypi_memory_prompt",
    "ohmypi_memory_candidate_signal",
    "ohmypi_memory_prompt_path",
    "ohmypi_provider_spec",
    "ohmypi_rpc_command",
    "write_ohmypi_memory_prompt",
]
