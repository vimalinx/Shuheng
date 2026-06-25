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
from dataclasses import dataclass, field
from typing import Any, Callable

try:
    from .runtime import RuntimeAdapter, RuntimeProviderSpec, RuntimeTaskEvent, RuntimeTaskRequest
except Exception:
    from runtime import RuntimeAdapter, RuntimeProviderSpec, RuntimeTaskEvent, RuntimeTaskRequest  # type: ignore


ProcessFactory = Callable[..., Any]
ThreadFactory = Callable[..., Any]
MemoryCandidateSink = Callable[[dict[str, Any]], None]
HostToolHandler = Callable[[str, dict[str, Any]], dict[str, Any]]
RuntimeEventSink = Callable[[RuntimeTaskEvent], None]

GA_TUI_MEMORY_PROMPT_FILENAME = "ohmypi-ga-tui-memory.md"
GA_TUI_MEMORY_PROMPT_HEADER = "Shuheng Layered Memory Guidance"
OHMYPI_RUNTIME_DIRNAME = "ohmypi"
OHMYPI_AGENT_DIRNAME = "agent"
MAX_HOST_TOOL_RESULT_CHARS = 12000
MAX_PROCESS_ARGS_CHARS = 4000
MAX_PROCESS_RESULT_CHARS = 6000
_PROCESS_TURN_MARKER_RE = re.compile(r"(?m)^[ \t]*\**LLM Running \(Turn \d+\) \.\.\.\**[ \t\r]*$")
_PROCESS_META_BLOCK_RE = re.compile(r"<(?:summary|thinking|think)>[\s\S]*?</(?:summary|thinking|think)>", re.IGNORECASE)
_PROCESS_TOOL_ARGS_BLOCK_RE = re.compile(
    r"🛠️\s*Tool:\s*`[^`]+`\s*📥\s*args:\s*\n`{4}text\n[\s\S]*?^`{4}\s*",
    re.IGNORECASE | re.MULTILINE,
)
_PROCESS_TOOL_HEADER_RE = re.compile(r"🛠️\s*Tool:\s*`[^`]+`\s*📥\s*args:\s*", re.IGNORECASE)
_PROCESS_TOOL_RESULT_FENCE_RE = re.compile(r"`{5}\s*\n[\s\S]*?\n`{5}", re.MULTILINE)
_PROCESS_FINAL_RESPONSE_INFO_RE = re.compile(r"^\s*\[Info\]\s+Final response to user\.\s*$", re.IGNORECASE | re.MULTILINE)
_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"),
    re.compile(r"\b(api[_-]?key|secret|token|password|passwd|密码|密钥)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_\-]{24,}\.[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{12,}\b"),
)
_APPROVAL_SELECT_OPTIONS = {"approve", "deny"}
_APPROVAL_RISK_RE = re.compile(
    r"\b("
    r"rm\s+-rf|sudo|su\s+-|chmod\s+777|chown\s+|mkfs|dd\s+if=|shutdown|reboot|systemctl|pacman|apt\s+|dnf\s+|"
    r"deploy|release|publish|email|mail|send\s+to|curl\s+.*\|\s*(sh|bash)|wget\s+.*\|\s*(sh|bash)|"
    r"delete|remove|unlink|secret|credential|password|passwd|api[_-]?key|token|payment|purchase|charge"
    r")\b",
    re.IGNORECASE,
)
_FULL_APPROVAL_TOOL_MAP = {
    "ask": {"ask"},
    "bash": {"bash", "shell"},
    "browser": {"browser"},
    "edit": {"edit", "repo.write", "write"},
    "eval": {"eval", "python", "javascript"},
    "find": {"find", "search", "repo.read"},
    "grep": {"grep", "search", "repo.read"},
    "inspect_image": {"inspect_image", "read"},
    "lsp": {"lsp", "repo.read", "repo.write"},
    "notebook": {"notebook", "edit", "write"},
    "python": {"python", "eval"},
    "read": {"read", "repo.read"},
    "task": {"task", "subagent.delegate"},
    "todo": {"todo", "write"},
    "web_search": {"web_search", "web.search"},
    "write": {"write", "repo.write"},
}
_OHMYPI_APPROVAL_MODES = {"always-ask", "write", "yolo"}
TOKEN_USAGE_KEYS = ("requests", "input", "output", "cache_create", "cache_read")
MAX_INCOMPLETE_FINAL_CONTINUATIONS = 2
INCOMPLETE_FINAL_NOTICE = (
    "\n\n[Oh My Pi] 输出疑似在半句处中断；已达到自动续写上限。"
    "当前回复保留为 incomplete，请继续追问“继续”或切换模型重试。"
)
INCOMPLETE_FINAL_CONTINUATION_PROMPT = (
    "Your previous visible assistant reply appears to have stopped in the middle of a sentence. "
    "Continue exactly from the last visible words. Do not restart the answer, do not summarize, "
    "do not apologize, and do not mention this instruction. Finish the user-facing reply naturally "
    "in the same language."
)
_FINAL_TERMINAL_CHARS = set("。.!！?？…)]}）】』」”'\"`")
_FINAL_SOFT_BREAK_CHARS = set(",，、:：;；-—")
_INCOMPLETE_FINAL_SUFFIX_RE = re.compile(
    r"(用于|作为|因为|所以|但是|不过|如果|虽然|以及|或者|包括|通过|对于|关于|相比|"
    r"需要|应该|可以|不能|没有|不是|属于|适合|依赖|意味着|核心是|关键是|实际|真实|具体|最终)$"
)


def _empty_token_usage() -> dict[str, int]:
    return {key: 0 for key in TOKEN_USAGE_KEYS}


def _positive_int(value: Any) -> int:
    try:
        number = int(str(value).strip())
    except Exception:
        return 0
    return number if number > 0 else 0


def _normalize_context_usage(raw: Any) -> dict[str, int | float]:
    if not isinstance(raw, dict):
        return {}
    tokens = _positive_int(raw.get("tokens") or raw.get("used") or raw.get("inputTokens") or 0)
    context_window = _positive_int(raw.get("contextWindow") or raw.get("context_window") or raw.get("size") or 0)
    try:
        percent = float(raw.get("percent", 0) or 0)
    except (TypeError, ValueError):
        percent = 0.0
    if tokens <= 0 and context_window <= 0:
        return {}
    if percent <= 0 and tokens > 0 and context_window > 0:
        percent = tokens / context_window * 100.0
    return {
        "tokens": tokens,
        "contextWindow": context_window,
        "percent": max(0.0, percent),
    }


def normalized_ohmypi_approval_mode(value: str = "") -> str:
    raw = str(value or "").strip().lower().replace("_", "-")
    return raw if raw in _OHMYPI_APPROVAL_MODES else "yolo"


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
    supports_raw_ask: bool = False
    name: str = "Oh My Pi"
    model: str = "unknown"
    api_base: str = ""
    apibase: str = ""
    log_path: str = ""
    provider: str = ""
    model_id: str = ""

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
    runtime_request: RuntimeTaskRequest | None = None
    buffer: str = ""
    final_text: str = ""
    finished: bool = False
    process_turn_no: int = 0
    pending_thinking: str = ""
    pending_standalone_dot_delta: str = ""
    pending_terminal_text: str | None = None
    pending_terminal_fallback_text: str = ""
    terminal_grace_started: bool = False
    host_tool_followup_generation: int = 0
    host_tool_followup_started_generation: int = 0
    host_tool_result_fallback_text: str = ""
    host_tool_result_buffer_len: int = 0
    host_tool_followup_last_activity_at: float = 0.0
    token_usage: dict[str, int] = field(default_factory=_empty_token_usage)
    token_usage_signatures: set[str] = field(default_factory=set)
    session_usage_baseline_signatures: set[str] = field(default_factory=set)
    incomplete_final_continuations: int = 0


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


@dataclass(frozen=True)
class OhMyPiRuntimeModel:
    provider: str
    model_id: str
    display_name: str = ""
    base_url: str = ""
    api: str = ""
    context_window: int = 0
    max_tokens: int = 0

    @property
    def selector(self) -> str:
        if self.provider and self.model_id:
            return f"{self.provider}/{self.model_id}"
        return self.model_id or self.provider


@dataclass(frozen=True)
class OhMyPiRuntimeConfig:
    agent_dir: str
    env: dict[str, str] = field(default_factory=dict)
    models: list[OhMyPiRuntimeModel] = field(default_factory=list)
    default_model: str = ""
    config_path: str = ""
    models_path: str = ""
    approval_mode: str = "yolo"


def ohmypi_runtime_root(harness_dir: str) -> str:
    return os.path.join(harness_dir, "runtime", OHMYPI_RUNTIME_DIRNAME)


def ohmypi_isolated_agent_dir(harness_dir: str) -> str:
    return os.path.join(ohmypi_runtime_root(harness_dir), OHMYPI_AGENT_DIRNAME)


def ohmypi_config_path(agent_dir: str) -> str:
    return os.path.join(agent_dir, "config.yml")


def ohmypi_models_path(agent_dir: str) -> str:
    return os.path.join(agent_dir, "models.yml")


def _json_yaml_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_text_atomic(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(tmp_path, path)


def write_ohmypi_runtime_files(
    *,
    agent_dir: str,
    config: dict[str, Any],
    models: dict[str, Any],
) -> dict[str, str]:
    os.makedirs(agent_dir, exist_ok=True)
    config_path = ohmypi_config_path(agent_dir)
    models_path = ohmypi_models_path(agent_dir)
    _write_text_atomic(config_path, _json_yaml_text(config))
    _write_text_atomic(models_path, _json_yaml_text(models))
    return {"agent_dir": agent_dir, "config_path": config_path, "models_path": models_path}


def ohmypi_subprocess_env(
    *,
    agent_dir: str,
    env_overrides: dict[str, str] | None = None,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    env = dict(os.environ if base_env is None else base_env)
    env["PI_CODING_AGENT_DIR"] = agent_dir
    for key, value in (env_overrides or {}).items():
        if key:
            env[str(key)] = str(value)
    return env


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


def _bounded_process_text(text: str, *, max_chars: int = MAX_HOST_TOOL_RESULT_CHARS) -> str:
    result = _redact_memory_text(str(text or "")).strip()
    if len(result) > max_chars:
        result = result[:max_chars].rstrip() + "\n...[truncated]"
    return result


def _compact_process_summary(text: str, *, max_chars: int = 140) -> str:
    summary = re.sub(r"\s+", " ", str(text or "")).strip()
    summary = summary.replace("<summary>", "").replace("</summary>", "")
    summary = summary.replace("<thinking>", "").replace("</thinking>", "")
    summary = summary.strip(" \t\r\n\"'“”‘’")
    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "..."
    return summary or "runtime event"


def _thinking_process_summary(thinking: str) -> str:
    return _compact_process_summary(thinking, max_chars=120) or "思考"


def _is_standalone_dot_delta(delta: str) -> bool:
    return str(delta or "").strip() == "."


def _safe_process_tool_name(tool_name: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.:-]+", "_", str(tool_name or "").strip())
    return clean.strip("_") or "unknown_tool"


def _thinking_text_from_payload(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_thinking_text_from_payload(item) for item in value)
    if not isinstance(value, dict):
        return ""
    parts: list[str] = []
    item_type = str(value.get("type") or "")
    seen_values: set[str] = set()
    if item_type in {"thinking", "reasoning", "thought", "redacted_thinking"}:
        for key in ("delta", "thinking", "thought", "reasoning", "text"):
            raw = value.get(key)
            if isinstance(raw, str) and raw not in seen_values:
                seen_values.add(raw)
                parts.append(raw)
    for key in ("delta", "thinking", "thought", "reasoning"):
        raw = value.get(key)
        if isinstance(raw, str) and raw not in seen_values:
            seen_values.add(raw)
            parts.append(raw)
    for key in ("content", "message", "assistantMessage", "assistantMessageEvent"):
        text = _thinking_text_from_payload(value.get(key))
        if text:
            parts.append(text)
    return "".join(parts)


def _strip_ohmypi_process_noise_for_memory(text: str) -> str:
    clean = str(text or "")
    clean = _PROCESS_META_BLOCK_RE.sub(" ", clean)
    clean = _PROCESS_TOOL_ARGS_BLOCK_RE.sub(" ", clean)
    clean = _PROCESS_TOOL_RESULT_FENCE_RE.sub(" ", clean)
    clean = _PROCESS_FINAL_RESPONSE_INFO_RE.sub(" ", clean)
    clean = _PROCESS_TOOL_HEADER_RE.sub(" ", clean)
    clean = _PROCESS_TURN_MARKER_RE.sub(" ", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean.strip()


def _host_tool_agent_result(value: Any) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": _bounded_host_tool_text(value),
            }
        ]
    }


def _host_tool_fallback_text(tool_name: str, result: Any, *, is_error: bool = False) -> str:
    tool = _safe_process_tool_name(tool_name)
    status = "失败" if is_error else "完成"
    result_text = _bounded_host_tool_text(result, max_chars=1600)
    return (
        f"[Oh My Pi] Shuheng host tool `{tool}` 已{status}，但模型没有继续生成最终回复。\n\n"
        "工具结果摘要：\n"
        "```json\n"
        f"{result_text}\n"
        "```"
    )


def _visible_non_process_text(text: str) -> str:
    clean = _strip_ohmypi_process_noise_for_memory(text)
    clean = re.sub(r"^[.\s]+$", "", clean).strip()
    return clean


def _visible_text_from_payload(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_visible_text_from_payload(item) for item in value)
    if not isinstance(value, dict):
        return ""
    item_type = str(value.get("type") or "")
    raw_text = value.get("text")
    if isinstance(raw_text, str) and (not item_type or item_type in {"text", "output_text", "text_end"}):
        return raw_text
    parts: list[str] = []
    for key in ("content", "message", "assistantMessage", "assistantMessageEvent"):
        text = _visible_text_from_payload(value.get(key))
        if text:
            parts.append(text)
    return "".join(parts)


_TERMINAL_DEDUPE_PUNCT_TRANSLATION = str.maketrans({
    "。": ".",
    "．": ".",
    "，": ",",
    "：": ":",
    "；": ";",
    "！": "!",
    "？": "?",
})


def _terminal_dedupe_text(text: str) -> str:
    clean = str(text or "").translate(_TERMINAL_DEDUPE_PUNCT_TRANSLATION)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _should_append_terminal_final_tail(buffer: str, final_tail: str) -> bool:
    if not final_tail:
        return False
    if final_tail in buffer:
        return False
    normalized_tail = _terminal_dedupe_text(final_tail)
    if not normalized_tail:
        return False
    return normalized_tail not in _terminal_dedupe_text(buffer)


def _has_unclosed_markdown_tail(text: str) -> bool:
    if len(re.findall(r"```+", text)) % 2 == 1:
        return True
    if text.count("**") % 2 == 1:
        return True
    if text.count("`") % 2 == 1 and "```" not in text:
        return True
    return False


def _looks_like_incomplete_final_reply(text: str) -> bool:
    visible = _visible_non_process_text(text)
    visible = re.sub(r"\s+", " ", visible).strip()
    if len(visible) < 18:
        return False
    if visible.startswith("[Oh My Pi]"):
        return False
    if INCOMPLETE_FINAL_NOTICE.strip() in visible:
        return False
    if _has_unclosed_markdown_tail(visible):
        return True
    tail = visible.rstrip()
    if not tail:
        return False
    last_char = tail[-1]
    if last_char in _FINAL_TERMINAL_CHARS:
        return False
    if last_char in _FINAL_SOFT_BREAK_CHARS:
        return True
    compact_tail = re.sub(r"[\s`*_~）】)}]+$", "", tail)
    compact_tail = re.sub(r"\s+", "", compact_tail)
    if _INCOMPLETE_FINAL_SUFFIX_RE.search(compact_tail[-32:]):
        return True
    return bool(re.search(
        r"\b(to|for|from|because|although|while|but|and|or|with|without|into|onto|as|is|are|was|were|"
        r"be|being|been|can|could|should|would|will|must|the|a|an|of|in|on|at|by)$",
        tail,
        re.IGNORECASE,
    ))


def _token_usage_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _token_usage_add(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return {key: _token_usage_int(left.get(key)) + _token_usage_int(right.get(key)) for key in TOKEN_USAGE_KEYS}


def _has_token_usage(usage: dict[str, int]) -> bool:
    return any(_token_usage_int(usage.get(key)) > 0 for key in ("input", "output", "cache_create", "cache_read"))


def _normalize_ohmypi_token_usage(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    known_keys = {
        "input",
        "inputTokens",
        "input_tokens",
        "output",
        "outputTokens",
        "output_tokens",
        "cacheRead",
        "cache_read",
        "cacheWrite",
        "cacheCreate",
        "cache_create",
        "cacheCreation",
        "cache_creation",
    }
    if not any(key in raw for key in known_keys):
        return {}
    usage = _empty_token_usage()
    usage["requests"] = 1
    usage["input"] = _token_usage_int(raw.get("input", raw.get("inputTokens", raw.get("input_tokens", 0))))
    usage["output"] = _token_usage_int(raw.get("output", raw.get("outputTokens", raw.get("output_tokens", 0))))
    usage["cache_read"] = _token_usage_int(raw.get("cacheRead", raw.get("cache_read", 0)))
    usage["cache_create"] = (
        _token_usage_int(raw.get("cacheWrite"))
        + _token_usage_int(raw.get("cacheCreate"))
        + _token_usage_int(raw.get("cache_create"))
        + _token_usage_int(raw.get("cacheCreation"))
        + _token_usage_int(raw.get("cache_creation"))
    )
    return usage


def _token_usage_signature(container: dict[str, Any], usage: dict[str, int], fallback_index: int) -> str:
    for key in ("responseId", "response_id", "messageId", "message_id", "id"):
        value = str(container.get(key) or "").strip()
        if value:
            return f"id:{value}"
    timestamp = str(container.get("timestamp") or container.get("createdAt") or container.get("created_at") or "").strip()
    model = str(container.get("model") or container.get("provider") or container.get("api") or "").strip()
    usage_blob = json.dumps(usage, sort_keys=True, separators=(",", ":"))
    if timestamp:
        return f"ts:{timestamp}:{model}:{usage_blob}"
    return f"anon:{fallback_index}:{model}:{usage_blob}"


def _frame_token_usage_entries(frame: dict[str, Any]) -> list[tuple[str, dict[str, int]]]:
    entries: list[tuple[str, dict[str, int]]] = []
    seen_containers: set[int] = set()

    def visit(value: Any) -> None:
        if not isinstance(value, dict):
            return
        container_id = id(value)
        if container_id in seen_containers:
            return
        seen_containers.add(container_id)
        usage = _normalize_ohmypi_token_usage(value.get("usage"))
        if _has_token_usage(usage):
            entries.append((_token_usage_signature(value, usage, len(entries)), usage))
        for key in ("message", "assistantMessage", "assistantMessageEvent"):
            child = value.get(key)
            if isinstance(child, dict):
                visit(child)
        messages = value.get("messages")
        if isinstance(messages, list):
            for item in messages:
                if isinstance(item, dict):
                    visit(item)

    visit(frame)
    return entries


def _usage_entries_from_session_file(path: str) -> list[tuple[str, dict[str, int]]]:
    entries: list[tuple[str, dict[str, int]]] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue
                message = row.get("message")
                if not isinstance(message, dict) or str(message.get("role") or "") != "assistant":
                    continue
                usage = _normalize_ohmypi_token_usage(message.get("usage"))
                if not _has_token_usage(usage):
                    continue
                signature = _token_usage_signature(message, usage, line_no)
                entries.append((signature, usage))
    except OSError:
        return []
    return entries


def _session_usage_entries(agent_dir: str) -> list[tuple[str, dict[str, int]]]:
    sessions_dir = os.path.join(agent_dir, "sessions")
    if not os.path.isdir(sessions_dir):
        return []
    entries: list[tuple[str, dict[str, int]]] = []
    for root, _dirs, files in os.walk(sessions_dir):
        for name in files:
            if not name.endswith(".jsonl"):
                continue
            entries.extend(_usage_entries_from_session_file(os.path.join(root, name)))
    return entries


class OhMyPiRpcAgent:
    """Small queue-compatible wrapper around `omp --mode rpc`."""

    def __init__(
        self,
        *,
        command: list[str] | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        process_factory: ProcessFactory | None = None,
        thread_factory: ThreadFactory = threading.Thread,
        memory_candidate_sink: MemoryCandidateSink | None = None,
        host_tool_definitions: list[RpcHostToolDefinition | dict[str, Any]] | None = None,
        host_tool_handler: HostToolHandler | None = None,
        runtime_event_sink: RuntimeEventSink | None = None,
        configured_models: list[OhMyPiRuntimeModel] | None = None,
        default_model: str | None = None,
        startup_timeout: float = 10.0,
        stop_timeout: float = 3.0,
        terminal_grace_timeout: float = 1.0,
        host_tool_followup_timeout: float = 45.0,
        session_usage_flush_timeout: float = 1.0,
        session_usage_stable_interval: float = 0.08,
    ) -> None:
        self.command = list(command or ohmypi_rpc_command())
        self.cwd = cwd or os.getcwd()
        self.env = dict(env) if env is not None else None
        self.process_factory = process_factory or subprocess.Popen
        self.thread_factory = thread_factory
        self.memory_candidate_sink = memory_candidate_sink
        self.host_tool_definitions = [
            item
            for item in (_host_tool_definition_to_rpc(definition) for definition in (host_tool_definitions or []))
            if item.get("name")
        ]
        self.host_tool_handler = host_tool_handler
        self.runtime_event_sink = runtime_event_sink
        self.startup_timeout = startup_timeout
        self.stop_timeout = stop_timeout
        self.terminal_grace_timeout = terminal_grace_timeout
        self.host_tool_followup_timeout = max(0.05, float(host_tool_followup_timeout))
        self.session_usage_flush_timeout = max(0.0, float(session_usage_flush_timeout))
        self.session_usage_stable_interval = max(0.0, float(session_usage_stable_interval))
        self.task_queue = _TaskCounter()
        self.is_running = False
        self.log_path = ""
        self.history: list[str] = []
        self.handler = None
        self.configured_models = list(configured_models or [])
        self.llmclients = self._clients_from_models(self.configured_models)
        self.llm_no = self._model_index_for_selector(default_model or "")
        self.llmclient = self.llmclients[0]
        if 0 <= self.llm_no < len(self.llmclients):
            self.llmclient = self.llmclients[self.llm_no]
        self._process: Any = None
        self._ready = threading.Event()
        self._send_lock = threading.Lock()
        self._active_lock = threading.Lock()
        self._active: _ActivePrompt | None = None
        self._request_no = 0
        self._response_waiters: dict[str, queue.Queue] = {}
        self._response_waiters_lock = threading.Lock()
        self._stderr_tail: list[str] = []
        self._closed = False
        self._host_tools_registered = False
        self._pending_model: OhMyPiRuntimeModel | None = None
        self.native_session_file = ""
        self.native_session_id = ""
        self.native_session_name = ""
        self.native_message_count = 0
        self.native_auto_compaction_enabled = False
        self.native_context_usage: dict[str, int | float] = {}

    def _clients_from_models(self, models: list[OhMyPiRuntimeModel]) -> list[_OhMyPiClient]:
        if not models:
            return [_OhMyPiClient(_OhMyPiBackend())]
        clients: list[_OhMyPiClient] = []
        for model in models:
            backend = _OhMyPiBackend(
                name=model.display_name or model.selector or "Oh My Pi",
                model=model.model_id or "unknown",
                api_base=model.base_url,
                apibase=model.base_url,
                provider=model.provider,
                model_id=model.model_id,
            )
            if model.context_window > 0:
                setattr(backend, "context_win", model.context_window)
                setattr(backend, "contextWindow", model.context_window)
            if model.max_tokens > 0:
                setattr(backend, "max_tokens", model.max_tokens)
                setattr(backend, "maxTokens", model.max_tokens)
            clients.append(_OhMyPiClient(backend))
        return clients

    def _model_index_for_selector(self, selector: str) -> int:
        selector = str(selector or "").strip()
        if not selector or not self.configured_models:
            return 0
        for idx, model in enumerate(self.configured_models):
            if model.selector == selector:
                return idx
        return 0

    def _model_index_for_runtime_model(self, model: dict[str, Any]) -> int:
        if not self.configured_models:
            return -1
        provider = str(model.get("provider") or "").strip()
        model_id = str(model.get("id") or model.get("modelId") or "").strip()
        base_url = str(model.get("baseUrl") or model.get("base_url") or "").strip().rstrip("/")
        fallback = -1
        for idx, configured in enumerate(self.configured_models):
            configured_base = str(configured.base_url or "").strip().rstrip("/")
            if provider and model_id and configured.provider == provider and configured.model_id == model_id:
                return idx
            if (
                fallback < 0
                and model_id
                and configured.model_id == model_id
                and (not base_url or not configured_base or base_url == configured_base)
            ):
                fallback = idx
        return fallback

    def refresh_configured_models(
        self,
        models: list[OhMyPiRuntimeModel],
        *,
        env: dict[str, str] | None = None,
        command: list[str] | None = None,
        default_model: str | None = None,
    ) -> None:
        """Refresh the Shuheng-owned OMP model projection without importing app state."""
        if env is not None:
            self.env = dict(env)
        if command is not None:
            self.command = list(command)
        backend = getattr(self.llmclient, "backend", None)
        current_selector = (
            self.configured_models[self.llm_no].selector
            if self.configured_models and 0 <= self.llm_no < len(self.configured_models)
            else ""
        )
        current_name = str(getattr(backend, "name", "") or "")
        current_provider = str(getattr(backend, "provider", "") or "")
        current_model = str(getattr(backend, "model_id", "") or getattr(backend, "model", "") or "")
        current_base = str(getattr(backend, "apibase", "") or getattr(backend, "base_url", "") or "").rstrip("/")
        self.configured_models = list(models or [])
        self.llmclients = self._clients_from_models(self.configured_models)
        self.llm_no = self._model_index_for_selector(default_model or "")
        for idx, model in enumerate(self.configured_models):
            model_base = str(model.base_url or "").rstrip("/")
            if current_selector and model.selector == current_selector:
                self.llm_no = idx
                break
            if current_name and model.display_name == current_name:
                self.llm_no = idx
                break
            if current_provider and current_model and model.provider == current_provider and model.model_id == current_model:
                self.llm_no = idx
                break
            if current_model and model.model_id == current_model and (not current_base or not model_base or current_base == model_base):
                self.llm_no = idx
                break
        self.llmclient = self.llmclients[self.llm_no]
        self._pending_model = self.configured_models[self.llm_no] if self.configured_models else None

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
            if not self.configured_models:
                self._send({"id": self._next_request_id("models"), "type": "get_available_models"})
            self.request_runtime_state()

    def request_runtime_state(self, *, wait: bool = False, timeout: float = 5.0) -> bool:
        request = {"id": self._next_request_id("state"), "type": "get_state"}
        try:
            if wait:
                frame = self._send_and_wait(request, timeout=timeout)
                return bool(frame.get("success") is not False)
            process = self._process
            if process is None or process.poll() is not None or not self._ready.is_set():
                return False
            self._send(request)
            return True
        except Exception:
            return False

    def switch_runtime_session(self, session_path: str, *, timeout: float = 8.0) -> bool:
        session_path = str(session_path or "").strip()
        if not session_path:
            return False
        try:
            self._ensure_process()
            frame = self._send_and_wait(
                {"id": self._next_request_id("switch-session"), "type": "switch_session", "sessionPath": session_path},
                timeout=timeout,
            )
        except Exception as exc:
            self._remember_stderr(f"switch session failed: {type(exc).__name__}: {exc}")
            return False
        if frame.get("success") is False:
            self._remember_stderr(f"switch session failed: {frame.get('error') or 'unknown RPC error'}")
            return False
        data = frame.get("data")
        if isinstance(data, dict) and bool(data.get("cancelled")):
            return False
        return self.request_runtime_state(wait=True, timeout=timeout)

    def compact_runtime_session(self, custom_instructions: str = "", *, timeout: float = 30.0) -> bool:
        request: dict[str, Any] = {"id": self._next_request_id("compact"), "type": "compact"}
        if str(custom_instructions or "").strip():
            request["customInstructions"] = str(custom_instructions).strip()
        try:
            self._ensure_process()
            frame = self._send_and_wait(request, timeout=timeout)
        except Exception as exc:
            self._remember_stderr(f"compact session failed: {type(exc).__name__}: {exc}")
            return False
        if frame.get("success") is False:
            self._remember_stderr(f"compact session failed: {frame.get('error') or 'unknown RPC error'}")
            return False
        return self.request_runtime_state(wait=True, timeout=timeout)

    def next_llm(self, index: int = -1) -> None:
        if self.configured_models:
            if index < 0:
                index = (self.llm_no + 1) % len(self.configured_models)
            if index < 0 or index >= len(self.configured_models):
                return
            self.llm_no = index
            self.llmclient = self.llmclients[index]
            self._pending_model = self.configured_models[index]
            if self._process is not None and self._process.poll() is None and self._ready.is_set():
                self._apply_pending_model()
            return
        if self._process is not None and self._process.poll() is None:
            self._send({"id": self._next_request_id("cycle"), "type": "cycle_model"})

    def list_llms(self) -> list[tuple[int, str, bool]]:
        return [
            (idx, f"OhMyPi/{getattr(client.backend, 'name', 'Oh My Pi')}", idx == self.llm_no)
            for idx, client in enumerate(self.llmclients)
        ]

    def get_llm_name(self, b: Any = None, model: bool = False) -> str:
        client = self.llmclient if b is None else b
        backend = getattr(client, "backend", self.llmclient.backend)
        if model:
            return str(getattr(backend, "model", "") or "unknown")
        return f"OhMyPi/{getattr(backend, 'name', 'Oh My Pi')}"

    def put_runtime_task(self, request: RuntimeTaskRequest) -> queue.Queue:
        return self._put_prompt(request.prompt, source=request.source, runtime_request=request)

    def put_task(self, prompt: str, source: str = "", images: Any = None) -> queue.Queue:
        del images
        return self._put_prompt(prompt, source=source, runtime_request=None)

    def _put_prompt(
        self,
        prompt: str,
        *,
        source: str = "",
        runtime_request: RuntimeTaskRequest | None = None,
    ) -> queue.Queue:
        display_queue: queue.Queue = queue.Queue()
        session_usage_baseline = self._session_usage_signature_set()
        with self._active_lock:
            if self._active is not None and not self._active.finished:
                display_queue.put({"done": "[Oh My Pi] 当前 RPC 会话仍在运行，不能并发启动新任务。", "source": source})
                return display_queue
            request_id = self._next_request_id("prompt")
            self._active = _ActivePrompt(
                request_id=request_id,
                display_queue=display_queue,
                source=source,
                runtime_request=runtime_request,
                session_usage_baseline_signatures=session_usage_baseline,
            )
            self.is_running = True
            self.task_queue.start()
        self._emit_runtime_event(
            "runtime_task_requested",
            status="starting",
            request=runtime_request,
            source=source,
            payload={"request_id": request_id},
        )

        def _runner() -> None:
            try:
                self._ensure_process()
                self._send({"id": request_id, "type": "prompt", "message": prompt})
            except Exception as exc:
                self._finish_active(
                    f"[Oh My Pi] 启动失败: {type(exc).__name__}: {exc}",
                    source=source,
                    wait_for_session_usage=False,
                )

        self.thread_factory(target=_runner, daemon=True, name="ohmypi-rpc-submit").start()
        return display_queue

    def abort(self) -> None:
        try:
            self._send({"id": self._next_request_id("abort"), "type": "abort"})
        except Exception:
            pass
        self._finish_active("[Oh My Pi] 已请求中止。", wait_for_session_usage=False)

    def reset_runtime_session(self) -> None:
        self.history = []
        self.native_session_file = ""
        self.native_session_id = ""
        self.native_session_name = ""
        self.native_message_count = 0
        self.native_context_usage = {}
        with self._active_lock:
            self._active = None
            self.is_running = False
        self.task_queue.done()
        process = self._process
        if process is None or process.poll() is not None or not self._ready.is_set():
            return
        try:
            self._send({"id": self._next_request_id("new-session"), "type": "new_session"})
        except Exception:
            pass

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
                self._apply_pending_model()
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
            env=self.env,
        )
        self.thread_factory(target=self._read_stdout, daemon=True, name="ohmypi-rpc-stdout").start()
        self.thread_factory(target=self._read_stderr, daemon=True, name="ohmypi-rpc-stderr").start()
        if not self._ready.wait(self.startup_timeout):
            self._terminate_process(self._process)
            raise RuntimeError("RPC ready timeout")
        self._apply_pending_model()

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
                self._finish_active("[Oh My Pi] RPC 进程已退出。", wait_for_session_usage=False)

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
        self._remember_frame_token_usage(frame)
        frame_type = str(frame.get("type") or "")
        if frame_type == "ready":
            self._register_host_tools()
            self._ready.set()
            self.request_runtime_state()
            return
        if frame_type == "turn_start":
            self._note_active_host_tool_followup_activity()
            self._cancel_active_terminal_grace()
            return
        if frame_type == "response":
            self._handle_response(frame)
            self._notify_response_waiter(frame)
            return
        if frame_type == "host_tool_call":
            self._note_active_host_tool_followup_activity()
            self._handle_host_tool_call(frame)
            return
        if frame_type == "host_tool_cancel":
            self._handle_host_tool_cancel(frame)
            return
        if frame_type in {"tool_execution_start", "tool_execution_update", "tool_execution_end"}:
            self._note_active_host_tool_followup_activity()
            self._handle_tool_execution_event(frame)
            return
        if frame_type == "message_update":
            self._note_active_host_tool_followup_activity()
            event = frame.get("assistantMessageEvent")
            if isinstance(event, dict):
                self._handle_message_update_event(event)
            return
        if frame_type == "message_end":
            self._note_active_host_tool_followup_activity()
            error_text = self._frame_error_text(frame)
            if error_text:
                self._finish_active(error_text, wait_for_session_usage=False)
            else:
                self._remember_active_final_text(self._frame_visible_text(frame))
            return
        if frame_type in {"agent_end", "turn_end"}:
            self._note_active_host_tool_followup_activity()
            error_text = self._frame_error_text(frame)
            fallback_text = self._frame_visible_text(frame)
            if frame_type == "turn_end":
                expects_followup = self._turn_end_expects_followup(frame)
                self._defer_active_terminal(
                    error_text,
                    fallback_text=fallback_text,
                    start_grace=not expects_followup,
                )
                if expects_followup:
                    self._expect_active_host_tool_followup()
            else:
                pending_text, pending_fallback = self._active_pending_terminal()
                self._finish_active(
                    error_text or pending_text,
                    fallback_text=fallback_text or pending_fallback,
                    wait_for_session_usage=not bool(error_text or pending_text),
                )
            return
        if frame_type == "extension_ui_request":
            self._answer_extension_ui(frame)
            return

    def _handle_message_update_event(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("type") or "")
        if event_type == "text_delta":
            self._append_active_delta(str(event.get("delta") or ""))
            return
        if event_type in {"thinking_delta", "reasoning_delta", "thought_delta", "thinking", "reasoning", "thought"}:
            self._remember_active_thinking_delta(_thinking_text_from_payload(event))
            return
        if event_type == "done":
            self._flush_active_thinking()
            self._remember_active_final_text(_visible_text_from_payload(event.get("message") or event))
            return
        if event_type == "error":
            self._flush_active_thinking()
            error_payload = event.get("error")
            error_text = ""
            if isinstance(error_payload, dict):
                error_text = str(error_payload.get("errorMessage") or error_payload.get("message") or error_payload.get("error") or "")
            else:
                error_text = str(error_payload or event.get("errorMessage") or event.get("message") or "")
            if error_text:
                self._finish_active(f"[Oh My Pi] {error_text}", wait_for_session_usage=False)
            return
        text = _visible_text_from_payload(event)
        if text:
            self._remember_active_final_text(text)

    def _handle_tool_execution_event(self, frame: dict[str, Any]) -> None:
        frame_type = str(frame.get("type") or "")
        if frame_type == "tool_execution_update":
            return
        tool_name = _safe_process_tool_name(str(frame.get("toolName") or frame.get("name") or ""))
        tool_call_id = str(frame.get("toolCallId") or frame.get("id") or "")
        if frame_type == "tool_execution_start":
            args = frame.get("args")
            if args is None:
                args = frame.get("arguments") if "arguments" in frame else frame.get("input")
            if frame.get("intent"):
                args = {"intent": frame.get("intent"), "args": args if args is not None else {}}
            self._append_active_tool_call_process(tool_name, args if args is not None else {}, summary=f"调用 OMP 工具: {tool_name}")
            self._emit_runtime_event(
                "runtime_tool_execution_start",
                status="started",
                tool_call_refs=[tool_call_id] if tool_call_id else [],
                payload={"tool_name": tool_name, "tool_call_id": tool_call_id},
            )
            return
        if frame_type == "tool_execution_end":
            result = frame.get("result")
            if result is None and frame.get("error") is not None:
                result = {"error": frame.get("error")}
            is_error = bool(frame.get("isError"))
            self._append_active_tool_result_process(tool_name, result, tool_call_id=tool_call_id, is_error=is_error)
            self._emit_runtime_event(
                "runtime_tool_execution_result",
                status="failed" if is_error else "completed",
                error=_bounded_host_tool_text(result, max_chars=1000) if is_error else "",
                tool_call_refs=[tool_call_id] if tool_call_id else [],
                payload={"tool_name": tool_name, "tool_call_id": tool_call_id},
            )

    def _handle_response(self, frame: dict[str, Any]) -> None:
        command = str(frame.get("command") or "")
        if frame.get("success") is False:
            error = str(frame.get("error") or "unknown RPC error")
            if command in {"prompt", "abort_and_prompt"}:
                self._finish_active(f"[Oh My Pi] RPC prompt failed: {error}", wait_for_session_usage=False)
            return
        data = frame.get("data")
        if command in {"get_state", "set_model"} and isinstance(data, dict):
            self._update_session_state(data)
            model = data.get("model")
            if isinstance(model, dict) and (command != "get_state" or not self.configured_models):
                self._update_model(model)
        if command in {"new_session", "switch_session", "compact"} and isinstance(data, dict):
            if not bool(data.get("cancelled")):
                self.request_runtime_state()
        if command == "cycle_model" and isinstance(data, dict):
            model = data.get("model")
            if isinstance(model, dict):
                self._update_model(model)
        if command == "get_available_models" and isinstance(data, dict):
            models = data.get("models")
            if isinstance(models, list) and models:
                self._replace_models_from_rpc(models)

    def _update_session_state(self, data: dict[str, Any]) -> None:
        self.native_session_file = str(data.get("sessionFile") or data.get("session_file") or "").strip()
        self.native_session_id = str(data.get("sessionId") or data.get("session_id") or "").strip()
        self.native_session_name = str(data.get("sessionName") or data.get("session_name") or "").strip()
        self.native_message_count = _positive_int(data.get("messageCount") or data.get("message_count") or 0)
        self.native_auto_compaction_enabled = bool(data.get("autoCompactionEnabled"))
        context_usage = _normalize_context_usage(data.get("contextUsage") or data.get("context_usage"))
        self.native_context_usage = context_usage
        context_window = _positive_int(context_usage.get("contextWindow") if context_usage else 0)
        backend = getattr(self.llmclient, "backend", None)
        if backend is not None and context_window > 0:
            setattr(backend, "context_win", context_window)
            setattr(backend, "contextWindow", context_window)
            setattr(backend, "current_context_tokens", _positive_int(context_usage.get("tokens")))
            setattr(backend, "current_context_percent", float(context_usage.get("percent") or 0.0))

    def _update_model(self, model: dict[str, Any]) -> None:
        if self.configured_models:
            idx = self._model_index_for_runtime_model(model)
            if idx < 0:
                self._remember_stderr(f"runtime model not in Shuheng projection: {model}")
                return
            self.llm_no = idx
            self.llmclient = self.llmclients[idx]
            context_window = _positive_int(model.get("contextWindow") or model.get("context_window") or 0)
            if context_window > 0:
                setattr(self.llmclient.backend, "context_win", context_window)
                setattr(self.llmclient.backend, "contextWindow", context_window)
            return
        provider = str(model.get("provider") or self.llmclient.backend.name or "Oh My Pi")
        model_id = str(model.get("id") or model.get("modelId") or self.llmclient.backend.model or "unknown")
        name = str(model.get("name") or provider or "Oh My Pi")
        self.llmclient.backend.name = provider or name
        self.llmclient.backend.model = model_id
        self.llmclient.backend.provider = provider
        self.llmclient.backend.model_id = model_id
        context_window = _positive_int(model.get("contextWindow") or model.get("context_window") or 0)
        if context_window > 0:
            setattr(self.llmclient.backend, "context_win", context_window)
            setattr(self.llmclient.backend, "contextWindow", context_window)

    def _replace_models_from_rpc(self, models: list[Any]) -> None:
        configured: list[OhMyPiRuntimeModel] = []
        for item in models:
            if not isinstance(item, dict):
                continue
            provider = str(item.get("provider") or "").strip()
            model_id = str(item.get("id") or item.get("modelId") or "").strip()
            if not provider or not model_id:
                continue
            configured.append(OhMyPiRuntimeModel(
                provider=provider,
                model_id=model_id,
                display_name=str(item.get("name") or f"{provider}/{model_id}"),
                base_url=str(item.get("baseUrl") or item.get("base_url") or ""),
                api=str(item.get("api") or ""),
                context_window=_positive_int(item.get("contextWindow") or item.get("context_window") or 0),
                max_tokens=_positive_int(item.get("maxTokens") or item.get("max_tokens") or 0),
            ))
        if not configured:
            return
        current_selector = self.configured_models[self.llm_no].selector if self.configured_models and self.llm_no < len(self.configured_models) else ""
        self.configured_models = configured
        self.llmclients = self._clients_from_models(configured)
        self.llm_no = 0
        for idx, model in enumerate(configured):
            if model.selector == current_selector:
                self.llm_no = idx
                break
        self.llmclient = self.llmclients[self.llm_no]

    def _apply_pending_model(self) -> None:
        model = self._pending_model
        if model is None or not model.provider or not model.model_id:
            return
        self._pending_model = None
        self._send({
            "id": self._next_request_id("set-model"),
            "type": "set_model",
            "provider": model.provider,
            "modelId": model.model_id,
        })

    def _frame_error_text(self, frame: dict[str, Any]) -> str | None:
        objects: list[dict[str, Any]] = [frame]
        for key in ("message", "assistantMessage", "assistantMessageEvent", "error"):
            value = frame.get(key)
            if isinstance(value, dict):
                objects.append(value)
        stop_reason = ""
        status = ""
        message = ""
        for item in objects:
            stop_reason = stop_reason or str(item.get("stopReason") or item.get("stop_reason") or "")
            status = status or str(item.get("errorStatus") or item.get("status") or "")
            raw_message = item.get("errorMessage") or item.get("error")
            if raw_message and not isinstance(raw_message, dict):
                message = message or str(raw_message)
        if not message and stop_reason != "error":
            return None
        parts = [part for part in (status, message or "Unknown OMP runtime error") if part]
        return "[Oh My Pi] " + ": ".join(parts)

    def _frame_visible_text(self, frame: dict[str, Any]) -> str:
        messages = frame.get("messages")
        if isinstance(messages, list):
            for message in reversed(messages):
                if not isinstance(message, dict):
                    continue
                if str(message.get("role") or "") != "assistant":
                    continue
                text = _visible_text_from_payload(message)
                if text:
                    return text
        parts: list[str] = []
        message = frame.get("message")
        if isinstance(message, dict) and str(message.get("role") or "") == "assistant":
            text = _visible_text_from_payload(message)
            if text:
                parts.append(text)
        for key in ("assistantMessage", "assistantMessageEvent"):
            text = _visible_text_from_payload(frame.get(key))
            if text:
                parts.append(text)
        return "".join(parts)

    def _turn_end_expects_followup(self, frame: dict[str, Any]) -> bool:
        objects: list[dict[str, Any]] = [frame]
        message = frame.get("message")
        if isinstance(message, dict):
            objects.append(message)
        for item in objects:
            stop_reason = str(item.get("stopReason") or item.get("stop_reason") or "")
            if stop_reason == "toolUse":
                return True
        return bool(frame.get("toolResults"))

    def _append_active_process_block(self, summary: str, body: str) -> None:
        body_text = str(body or "").strip()
        if not body_text:
            return
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            active.pending_standalone_dot_delta = ""
            active.process_turn_no += 1
            block = (
                f"\n\n**LLM Running (Turn {active.process_turn_no}) ...**\n"
                f"<summary>{_compact_process_summary(summary)}</summary>\n"
                f"{body_text}\n\n"
            )
            active.buffer += block
            active.display_queue.put({"next": block, "source": "ohmypi"})

    def _remember_active_thinking_delta(self, delta: str) -> None:
        if not delta:
            return
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            active.pending_thinking += delta

    def _flush_active_thinking(self) -> None:
        with self._active_lock:
            active = self._active
            if active is None or active.finished or not active.pending_thinking:
                return
            thinking = active.pending_thinking
            active.pending_thinking = ""
        thinking_text = _bounded_process_text(thinking, max_chars=MAX_PROCESS_RESULT_CHARS)
        body = "<thinking>\n" + thinking_text + "\n</thinking>"
        self._append_active_process_block(_thinking_process_summary(thinking_text), body)

    def _flush_active_pending_standalone_dot_delta(self) -> None:
        with self._active_lock:
            active = self._active
            if active is None or active.finished or not active.pending_standalone_dot_delta:
                return
            delta = active.pending_standalone_dot_delta
            active.pending_standalone_dot_delta = ""
            active.buffer += delta
            active.display_queue.put({"next": delta, "source": "ohmypi"})

    def _append_active_tool_call_process(self, tool_name: str, args: Any, *, summary: str = "") -> None:
        self._flush_active_thinking()
        tool = _safe_process_tool_name(tool_name)
        args_text = _bounded_host_tool_text(args if args is not None else {}, max_chars=MAX_PROCESS_ARGS_CHARS)
        body = (
            f"🛠️ Tool: `{tool}` 📥 args:\n"
            "````text\n"
            f"{args_text}\n"
            "````"
        )
        self._append_active_process_block(summary or f"调用 OMP 工具: {tool}", body)

    def _append_active_tool_result_process(
        self,
        tool_name: str,
        result: Any,
        *,
        tool_call_id: str = "",
        is_error: bool = False,
    ) -> None:
        self._flush_active_thinking()
        tool = _safe_process_tool_name(tool_name)
        status = "error" if is_error else "ok"
        args = {"toolCallId": tool_call_id, "status": status}
        args_text = _bounded_host_tool_text(args, max_chars=MAX_PROCESS_ARGS_CHARS)
        result_text = _bounded_host_tool_text(result if result is not None else {}, max_chars=MAX_PROCESS_RESULT_CHARS)
        body = (
            f"🛠️ Tool: `{tool}` 📥 args:\n"
            "````text\n"
            f"{args_text}\n"
            "````\n"
            "`````\n"
            f"{result_text}\n"
            "`````"
        )
        summary = f"OMP 工具{'失败' if is_error else '结果'}: {tool}"
        self._append_active_process_block(summary, body)

    def _append_active_delta(self, delta: str) -> None:
        if not delta:
            return
        if _is_standalone_dot_delta(delta):
            with self._active_lock:
                active = self._active
                if active is None or active.finished:
                    return
                active.pending_standalone_dot_delta += delta
            return
        self._flush_active_thinking()
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            if active.pending_standalone_dot_delta:
                delta = active.pending_standalone_dot_delta + delta
                active.pending_standalone_dot_delta = ""
            active.buffer += delta
            active.display_queue.put({"next": delta, "source": "ohmypi"})

    def _remember_active_final_text(self, text: str) -> None:
        if not text:
            return
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            active.final_text = text

    def _remember_frame_token_usage(self, frame: dict[str, Any]) -> None:
        entries = _frame_token_usage_entries(frame)
        if not entries:
            return
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            for signature, usage in entries:
                if signature in active.token_usage_signatures:
                    continue
                active.token_usage_signatures.add(signature)
                active.token_usage = _token_usage_add(active.token_usage, usage)

    def _session_agent_dir(self) -> str:
        env = self.env if self.env is not None else os.environ
        return str(env.get("PI_CODING_AGENT_DIR") or "").strip()

    def _session_usage_signature_set(self) -> set[str]:
        agent_dir = self._session_agent_dir()
        if not agent_dir:
            return set()
        return {signature for signature, _usage in _session_usage_entries(agent_dir)}

    def _new_active_session_usage_entries(self, active: _ActivePrompt) -> list[tuple[str, dict[str, int]]]:
        agent_dir = self._session_agent_dir()
        if not agent_dir:
            return []
        entries = _session_usage_entries(agent_dir)
        if not entries:
            return []
        return [
            (signature, usage)
            for signature, usage in entries
            if signature not in active.session_usage_baseline_signatures
            and signature not in active.token_usage_signatures
            and _has_token_usage(usage)
        ]

    def _wait_for_active_session_file_token_usage(self, active: _ActivePrompt) -> list[tuple[str, dict[str, int]]]:
        timeout = self.session_usage_flush_timeout
        deadline = time.monotonic() + timeout
        last_signatures: tuple[str, ...] = ()
        stable_since = 0.0
        while True:
            entries = self._new_active_session_usage_entries(active)
            signatures = tuple(signature for signature, _usage in entries)
            now = time.monotonic()
            if signatures:
                if signatures != last_signatures:
                    last_signatures = signatures
                    stable_since = now
                elif now - stable_since >= self.session_usage_stable_interval:
                    return entries
            if now >= deadline:
                return entries
            if timeout <= 0:
                return entries
            time.sleep(0.05)

    def _merge_active_session_file_token_usage(self, *, wait: bool = False) -> None:
        agent_dir = self._session_agent_dir()
        if not agent_dir:
            return
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            if _has_token_usage(active.token_usage):
                return
        entries = self._wait_for_active_session_file_token_usage(active) if wait else self._new_active_session_usage_entries(active)
        if not entries:
            return
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            for signature, usage in entries:
                if signature in active.token_usage_signatures:
                    continue
                active.token_usage_signatures.add(signature)
                active.token_usage = _token_usage_add(active.token_usage, usage)

    def _active_pending_terminal(self) -> tuple[str | None, str]:
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return None, ""
            return active.pending_terminal_text, active.pending_terminal_fallback_text

    def _active_done_text_candidate(self, text: str | None, fallback_text: str = "") -> str:
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return text or fallback_text or ""
            if text is not None:
                return text
            if active.buffer:
                done_text = active.buffer
                final_tail = fallback_text or active.final_text
                if _should_append_terminal_final_tail(done_text, final_tail):
                    done_text = done_text.rstrip() + "\n\n" + final_tail
                return done_text
            return fallback_text or active.final_text

    def _materialize_active_done_text_candidate(self, done_text: str) -> None:
        if not done_text:
            return
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            delta = ""
            if not active.buffer:
                delta = done_text
                active.buffer = done_text
            elif done_text.startswith(active.buffer):
                delta = done_text[len(active.buffer) :]
                active.buffer = done_text
            elif done_text not in active.buffer:
                delta = "\n\n" + done_text
                active.buffer = active.buffer.rstrip() + delta
            active.final_text = ""
            active.pending_terminal_text = None
            active.pending_terminal_fallback_text = ""
            active.terminal_grace_started = False
            active.pending_standalone_dot_delta = ""
            if delta:
                active.display_queue.put({"next": delta, "source": "ohmypi"})

    def _continue_incomplete_final_reply(self, done_text: str) -> bool:
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return False
            if active.incomplete_final_continuations >= MAX_INCOMPLETE_FINAL_CONTINUATIONS:
                return False
            active.incomplete_final_continuations += 1
            continuation_no = active.incomplete_final_continuations
        self._materialize_active_done_text_candidate(done_text)
        request_id = self._next_request_id("continue-final")
        try:
            self._send({
                "id": request_id,
                "type": "prompt",
                "message": INCOMPLETE_FINAL_CONTINUATION_PROMPT,
            })
        except Exception as exc:
            self._finish_active(
                done_text
                + "\n\n"
                + f"[Oh My Pi] 输出疑似中断，自动续写请求发送失败：{type(exc).__name__}: {exc}",
                wait_for_session_usage=False,
                allow_incomplete_final_check=False,
            )
            return True
        self._emit_runtime_event(
            "runtime_incomplete_final_continuation",
            status="continuing",
            source="ohmypi",
            message=done_text[-1200:],
            payload={"request_id": request_id, "continuation_no": continuation_no},
        )
        return True

    def _cancel_active_terminal_grace(self) -> None:
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            active.pending_terminal_text = None
            active.pending_terminal_fallback_text = ""
            active.terminal_grace_started = False

    def _mark_active_host_tool_result(self, tool_name: str, result: Any, *, is_error: bool = False) -> None:
        generation = 0
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            active.host_tool_result_fallback_text = _host_tool_fallback_text(tool_name, result, is_error=is_error)
            active.host_tool_result_buffer_len = len(active.buffer)
            active.host_tool_followup_generation += 1
            generation = active.host_tool_followup_generation
            active.host_tool_followup_last_activity_at = time.monotonic()
        self._start_active_host_tool_followup_watchdog(generation)

    def _note_active_host_tool_followup_activity(self) -> None:
        with self._active_lock:
            active = self._active
            if active is None or active.finished or active.host_tool_followup_generation <= 0:
                return
            active.host_tool_followup_last_activity_at = time.monotonic()

    def _expect_active_host_tool_followup(self) -> None:
        generation = 0
        should_start = False
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            generation = active.host_tool_followup_generation
            should_start = bool(active.host_tool_result_fallback_text)
        if should_start:
            self._start_active_host_tool_followup_watchdog(generation)

    def _start_active_host_tool_followup_watchdog(self, generation: int) -> None:
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            if generation <= 0 or active.host_tool_followup_started_generation == generation:
                return
            active.host_tool_followup_started_generation = generation
        self.thread_factory(
            target=self._finish_active_after_host_tool_followup_timeout,
            args=(generation,),
            daemon=True,
            name="ohmypi-rpc-host-tool-followup",
        ).start()

    def _finish_active_after_host_tool_followup_timeout(self, generation: int) -> None:
        while True:
            time.sleep(self.host_tool_followup_timeout)
            fallback_text = ""
            visible_text_after_host_tool = ""
            with self._active_lock:
                active = self._active
                if (
                    active is None
                    or active.finished
                    or active.host_tool_followup_generation != generation
                ):
                    return
                idle_for = time.monotonic() - active.host_tool_followup_last_activity_at
                if idle_for < self.host_tool_followup_timeout:
                    continue
                fallback_text = active.host_tool_result_fallback_text
                host_tool_suffix = active.buffer[active.host_tool_result_buffer_len :]
                visible_text_after_host_tool = _visible_non_process_text(host_tool_suffix)
            self._finish_active(None, fallback_text="" if visible_text_after_host_tool else fallback_text)
            return

    def _defer_active_terminal(self, text: str | None = None, *, fallback_text: str = "", start_grace: bool = True) -> None:
        should_start_grace = False
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return
            if text is not None:
                active.pending_terminal_text = text
            if fallback_text:
                active.pending_terminal_fallback_text = fallback_text
            if not start_grace:
                active.terminal_grace_started = False
                return
            if not active.terminal_grace_started:
                active.terminal_grace_started = True
                should_start_grace = True
        if should_start_grace:
            self.thread_factory(target=self._finish_active_after_terminal_grace, daemon=True, name="ohmypi-rpc-terminal-grace").start()

    def _finish_active_after_terminal_grace(self) -> None:
        time.sleep(max(0.05, self.terminal_grace_timeout))
        text, fallback_text = self._active_pending_terminal()
        with self._active_lock:
            active = self._active
            if active is None or active.finished or not active.terminal_grace_started:
                return
        self._finish_active(text, fallback_text=fallback_text)

    def _finish_active(
        self,
        text: str | None = None,
        *,
        source: str = "ohmypi",
        fallback_text: str = "",
        wait_for_session_usage: bool = True,
        allow_incomplete_final_check: bool = True,
    ) -> None:
        if text is None:
            self._flush_active_thinking()
            self._flush_active_pending_standalone_dot_delta()
        done_text_candidate = self._active_done_text_candidate(text, fallback_text)
        if (
            allow_incomplete_final_check
            and done_text_candidate
            and not done_text_candidate.startswith("[Oh My Pi]")
            and _looks_like_incomplete_final_reply(done_text_candidate)
        ):
            with self._active_lock:
                active = self._active
                continuation_count = active.incomplete_final_continuations if active is not None else 0
            if continuation_count < MAX_INCOMPLETE_FINAL_CONTINUATIONS:
                if self._continue_incomplete_final_reply(done_text_candidate):
                    return
            else:
                text = done_text_candidate.rstrip() + INCOMPLETE_FINAL_NOTICE
                fallback_text = ""
                wait_for_session_usage = False
        self._merge_active_session_file_token_usage(wait=wait_for_session_usage)
        done_text = ""
        signal_source = source
        request_id = ""
        runtime_request: RuntimeTaskRequest | None = None
        token_usage = _empty_token_usage()
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                self.is_running = False
                return
            active.finished = True
            if text is not None:
                done_text = text
            elif active.buffer:
                done_text = active.buffer
                final_tail = fallback_text or active.final_text
                if _should_append_terminal_final_tail(done_text, final_tail):
                    done_text = done_text.rstrip() + "\n\n" + final_tail
            else:
                done_text = fallback_text or active.final_text
            signal_source = active.source or source
            request_id = active.request_id
            runtime_request = active.runtime_request
            token_usage = dict(active.token_usage)
            done_item: dict[str, Any] = {"done": done_text, "source": source}
            if _has_token_usage(token_usage):
                done_item["usage"] = token_usage
            active.display_queue.put(done_item)
            self._active = None
            self.is_running = False
            self.task_queue.done()
        event_type = "runtime_task_completed"
        status = "completed"
        error = ""
        if done_text.startswith("[Oh My Pi] 已请求中止"):
            event_type = "runtime_task_aborted"
            status = "aborted"
        elif done_text.startswith("[Oh My Pi]") and ("失败" in done_text or "error" in done_text.lower() or "退出" in done_text):
            event_type = "runtime_task_failed"
            status = "failed"
            error = done_text
        elif INCOMPLETE_FINAL_NOTICE.strip() in done_text:
            event_type = "runtime_task_failed"
            status = "incomplete"
            error = "OMP final reply remained structurally incomplete after bounded continuation."
        event_payload: dict[str, Any] = {"request_id": request_id}
        if _has_token_usage(token_usage):
            event_payload["token_usage"] = token_usage
        self._emit_runtime_event(
            event_type,
            status=status,
            request=runtime_request,
            source=signal_source,
            message=done_text[:1200],
            error=error,
            payload=event_payload,
        )
        self._emit_memory_candidate_signal(done_text, source=signal_source, request_id=request_id)
        self.request_runtime_state()

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

    def _active_runtime_request(self) -> RuntimeTaskRequest | None:
        with self._active_lock:
            active = self._active
            if active is None or active.finished:
                return None
            return active.runtime_request

    def _emit_runtime_event(
        self,
        event_type: str,
        *,
        status: str = "",
        request: RuntimeTaskRequest | None = None,
        source: str = "",
        message: str = "",
        delta: str = "",
        error: str = "",
        artifact_refs: list[str] | None = None,
        tool_call_refs: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self.runtime_event_sink is None:
            return
        runtime_request = request or self._active_runtime_request()
        try:
            event = RuntimeTaskEvent(
                task_id=runtime_request.task_id if runtime_request is not None else "",
                provider_id=runtime_request.provider_id if runtime_request is not None else "ohmypi",
                event_type=event_type,
                status=status,
                agent_id=runtime_request.agent_id if runtime_request is not None else "",
                source=source or (runtime_request.source if runtime_request is not None else "ohmypi"),
                message=message,
                delta=delta,
                error=error,
                artifact_refs=list(artifact_refs or (runtime_request.artifact_refs if runtime_request is not None else [])),
                tool_call_refs=list(tool_call_refs or []),
                request=runtime_request,
                payload=dict(payload or {}),
            )
            self.runtime_event_sink(event)
        except Exception as exc:
            self._remember_stderr(f"runtime event sink failed: {type(exc).__name__}: {exc}")

    def _active_permissions(self) -> dict[str, Any]:
        request = self._active_runtime_request()
        if request is None or not isinstance(request.permissions, dict):
            return {}
        return request.permissions

    def _approval_tool_name(self, frame: dict[str, Any]) -> str:
        title = str(frame.get("title") or "")
        match = re.search(r"(?im)^Allow tool:\s*([A-Za-z0-9_.:-]+)\s*$", title)
        return match.group(1).strip() if match else ""

    def _tool_allowed_by_permissions(self, tool_name: str, permissions: dict[str, Any]) -> bool:
        if not tool_name:
            return False
        tools_allowed = {str(item) for item in (permissions.get("tools_allowed") or [])}
        if tool_name in tools_allowed:
            return True
        aliases = _FULL_APPROVAL_TOOL_MAP.get(tool_name) or {tool_name}
        return bool(aliases & tools_allowed)

    def _should_auto_approve_extension_select(self, frame: dict[str, Any]) -> tuple[bool, str]:
        options = [str(item).strip().lower() for item in (frame.get("options") or [])]
        if set(options) != _APPROVAL_SELECT_OPTIONS:
            return False, "not_tool_approval_select"
        permissions = self._active_permissions()
        if str(permissions.get("permission_profile") or "") != "full":
            return False, "permission_profile_not_full"
        prompt_text = "\n".join(str(frame.get(key) or "") for key in ("title", "message"))
        if permissions.get("approval_required_for") and _APPROVAL_RISK_RE.search(prompt_text):
            return False, "risky_tool_prompt"
        tool_name = self._approval_tool_name(frame)
        if not self._tool_allowed_by_permissions(tool_name, permissions):
            return False, f"tool_not_allowed:{tool_name or '<unknown>'}"
        return True, f"approved:{tool_name}"

    def _answer_extension_ui(self, frame: dict[str, Any]) -> None:
        request_id = frame.get("id")
        if not request_id:
            return
        method = str(frame.get("method") or "")
        if method == "confirm":
            self._send({"type": "extension_ui_response", "id": request_id, "confirmed": False})
        elif method == "select":
            approved, reason = self._should_auto_approve_extension_select(frame)
            self._emit_runtime_event(
                "runtime_extension_ui_response",
                status="approved" if approved else "denied",
                payload={
                    "request_id": str(request_id),
                    "method": "select",
                    "reason": reason,
                    "title": str(frame.get("title") or "")[:500],
                },
            )
            if approved:
                self._send({"type": "extension_ui_response", "id": request_id, "value": "Approve"})
            else:
                self._send({"type": "extension_ui_response", "id": request_id, "value": "Deny"})
        elif method in {"input", "editor"}:
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
        tool_call_id = str(frame.get("toolCallId") or request_id)
        args = frame.get("arguments")
        arguments = args if isinstance(args, dict) else {}
        if not request_id:
            self._remember_stderr("host tool call missing id")
            return
        self._append_active_tool_call_process(
            tool_name or "unknown_tool",
            arguments,
            summary=f"调用 Shuheng host tool: {tool_name or 'unknown_tool'}",
        )
        allowed_names = {str(tool.get("name") or "") for tool in self.host_tool_definitions}
        if not tool_name or tool_name not in allowed_names:
            result = {
                "schema_version": "ga-tui.host_tool.v1",
                "status": "error",
                "error": f"Unknown or unregistered host tool: {tool_name or '<missing>'}",
            }
            self._send_host_tool_result(request_id, result, is_error=True)
            self._append_active_tool_result_process(tool_name or "unknown_tool", result, tool_call_id=tool_call_id, is_error=True)
            self._mark_active_host_tool_result(tool_name or "unknown_tool", result, is_error=True)
            return
        if self.host_tool_handler is None:
            result = {
                "schema_version": "ga-tui.host_tool.v1",
                "status": "error",
                "tool_name": tool_name,
                "error": "No host tool handler is configured.",
            }
            self._send_host_tool_result(request_id, result, is_error=True)
            self._append_active_tool_result_process(tool_name, result, tool_call_id=tool_call_id, is_error=True)
            self._mark_active_host_tool_result(tool_name, result, is_error=True)
            return
        try:
            self._emit_runtime_event(
                "runtime_host_tool_call",
                status="started",
                tool_call_refs=[tool_call_id],
                payload={"request_id": request_id, "tool_name": tool_name, "arguments": arguments},
            )
            result = self.host_tool_handler(tool_name, dict(arguments))
        except Exception as exc:
            self._emit_runtime_event(
                "runtime_host_tool_result",
                status="failed",
                error=f"{type(exc).__name__}: {exc}",
                tool_call_refs=[tool_call_id],
                payload={"request_id": request_id, "tool_name": tool_name},
            )
            result = {
                "schema_version": "ga-tui.host_tool.v1",
                "status": "error",
                "tool_name": tool_name,
                "error": f"{type(exc).__name__}: {exc}",
            }
            self._send_host_tool_result(request_id, result, is_error=True)
            self._append_active_tool_result_process(tool_name, result, tool_call_id=tool_call_id, is_error=True)
            self._mark_active_host_tool_result(tool_name, result, is_error=True)
            return
        self._emit_runtime_event(
            "runtime_host_tool_result",
            status="completed",
            tool_call_refs=[tool_call_id],
            payload={"request_id": request_id, "tool_name": tool_name},
        )
        self._send_host_tool_result(request_id, result)
        self._append_active_tool_result_process(tool_name, result, tool_call_id=tool_call_id)
        self._mark_active_host_tool_result(tool_name, result)

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

    def _send_and_wait(self, obj: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        request_id = str(obj.get("id") or self._next_request_id("request"))
        obj["id"] = request_id
        waiter: queue.Queue = queue.Queue(maxsize=1)
        with self._response_waiters_lock:
            self._response_waiters[request_id] = waiter
        try:
            self._send(obj)
            frame = waiter.get(timeout=max(0.1, timeout))
            return frame if isinstance(frame, dict) else {}
        finally:
            with self._response_waiters_lock:
                self._response_waiters.pop(request_id, None)

    def _notify_response_waiter(self, frame: dict[str, Any]) -> None:
        request_id = str(frame.get("id") or "")
        if not request_id:
            return
        with self._response_waiters_lock:
            waiter = self._response_waiters.get(request_id)
        if waiter is None:
            return
        try:
            waiter.put_nowait(frame)
        except queue.Full:
            pass

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
        runtime_event_sink: RuntimeEventSink | None = None,
        env: dict[str, str] | None = None,
        configured_models: list[OhMyPiRuntimeModel] | None = None,
        default_model: str | None = None,
    ) -> None:
        super().__init__(spec)
        self.command = command
        self.cwd = cwd
        self.env = dict(env) if env is not None else None
        self.process_factory = process_factory
        self.thread_factory = thread_factory
        self.memory_candidate_sink = memory_candidate_sink
        self.host_tool_definitions = list(host_tool_definitions or [])
        self.host_tool_handler = host_tool_handler
        self.runtime_event_sink = runtime_event_sink
        self.configured_models = list(configured_models or [])
        self.default_model = str(default_model or "")

    def create_agent(self) -> OhMyPiRpcAgent:
        return OhMyPiRpcAgent(
            command=self.command,
            cwd=self.cwd,
            env=self.env,
            process_factory=self.process_factory,
            thread_factory=self.thread_factory,
            memory_candidate_sink=self.memory_candidate_sink,
            host_tool_definitions=self.host_tool_definitions,
            host_tool_handler=self.host_tool_handler,
            runtime_event_sink=self.runtime_event_sink,
            configured_models=self.configured_models,
            default_model=self.default_model,
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


def resolve_ohmypi_binary(binary: str | None = None) -> str:
    explicit = str(binary or os.environ.get("GA_TUI_OHMYPI_BIN") or "").strip()
    if explicit:
        return explicit
    discovered = shutil.which("omp")
    if discovered:
        return discovered
    for candidate in (
        os.path.join(os.path.expanduser("~"), ".bun", "bin", "omp"),
    ):
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return "omp"


def ohmypi_rpc_command(
    binary: str | None = None,
    extra_args: list[str] | None = None,
    append_system_prompt: str | None = None,
    model: str | None = None,
    approval_mode: str | None = None,
) -> list[str]:
    binary = resolve_ohmypi_binary(binary)
    env_args = shlex.split(os.environ.get("GA_TUI_OHMYPI_ARGS", ""))
    appended_args = list(extra_args or env_args)
    approval_mode = normalized_ohmypi_approval_mode(approval_mode or os.environ.get("GA_TUI_OMP_APPROVAL_MODE") or "yolo")
    args = [
        binary,
        "--mode",
        "rpc",
        "--no-title",
        "--approval-mode",
        approval_mode,
    ]
    if model and not _has_cli_flag(appended_args, "--model"):
        args.extend(["--model", model])
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


def redact_memory_text(text: str) -> str:
    return _redact_memory_text(text)


def _bounded_section(title: str, path: str, text: str, *, max_chars: int = 2200) -> str:
    text = _redact_memory_text(text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n...[truncated]"
    if not text:
        text = "(not available)"
    return f"## {title}\n\nSource: `{path}`\n\n{text}\n"


def _shuheng_memory_structure(*, memory_dir: str, harness_dir: str) -> str:
    user_profile_path = os.path.join(memory_dir, "user_profile.md")
    global_path = os.path.join(memory_dir, "global_mem.txt")
    sop_path = os.path.join(memory_dir, "memory_management_sop.md")
    l4_path = os.path.join(memory_dir, "L4_raw_sessions")
    return (
        f"Shared user profile/state: {user_profile_path} | "
        f"Facts(L2): {global_path} | "
        f"SOPs(L3): {memory_dir}/*.md or *.py | "
        f"META-SOP(L0): {sop_path}\n"
        f"L4: {l4_path} historical sessions; use refs/indexes, do not mine directly.\n"
        f"Harness: {harness_dir}; memory writes are candidate-only through Shuheng governance."
    )


def build_ohmypi_memory_prompt(*, root_dir: str, harness_dir: str) -> str:
    memory_dir = os.path.join(root_dir, "memory")
    user_profile_path = os.path.join(memory_dir, "user_profile.md")
    insight_path = os.path.join(memory_dir, "global_mem_insight.txt")
    global_path = os.path.join(memory_dir, "global_mem.txt")
    sop_path = os.path.join(memory_dir, "memory_management_sop.md")
    insight = _redact_memory_text(_read_text_if_exists(insight_path, max_chars=3500)).strip()
    if not insight:
        insight = "(not available)"
    sections = [
        f"# {GA_TUI_MEMORY_PROMPT_HEADER}",
        "",
        "You are running as the Oh My Pi execution runtime inside Shuheng.",
        "Shuheng remains the Orchestrator: it owns task ledgers, approvals, artifact refs, and long-term memory governance.",
        "Use this GenericAgent-style layered memory as routing context. Read referenced files only when needed and verify current repository state before acting when memory could be stale.",
        "Do not write long-term memory directly. If execution reveals a durable, verified lesson, submit or report a memory candidate with evidence refs.",
        "Always finish each user turn with a concise normal user-facing final reply in the user's language. Tool results, \"Result:\" summaries, and memory-candidate submit/deferred notices are not a substitute for that reply.",
        "Treat Shuheng context packs and context refs as internal execution metadata, not user-visible conversation objects. User pronouns such as this, that, it, 这个, 这个东西, or 它 refer to the recent visible conversation/task topic unless the user explicitly names the context pack/ref.",
        "If the user explicitly asks to create a persistent/long-term Shuheng agent, success requires agent.create with lifecycle:\"persistent\" or persistent:true for a dedicated matching agent, or reuse of an existing matching persistent agent id. Scripts, schedules, or future suggestions alone do not satisfy that request.",
        "Never expose or store secrets. Treat redacted or credential-looking content as unavailable.",
        "",
        f"cwd = {os.path.join(harness_dir, 'runtime')} (./)",
        "",
        f"[Memory] ({memory_dir})",
        _shuheng_memory_structure(memory_dir=memory_dir, harness_dir=harness_dir),
        f"{insight_path}:",
        insight,
        "",
        _bounded_section("Shared User Profile", user_profile_path, _read_text_if_exists(user_profile_path, max_chars=3200), max_chars=2600),
        _bounded_section("L0 Memory Governance Preview", sop_path, _read_text_if_exists(sop_path, max_chars=2800), max_chars=2200),
        "## Layer References",
        "",
        f"- Shared user profile/current state: `{user_profile_path}`",
        f"- L1 global memory index: `{insight_path}`",
        f"- L2 global facts: `{global_path}`",
        f"- L3 SOPs/tools: `{memory_dir}`",
        f"- L4 raw sessions: `{os.path.join(memory_dir, 'L4_raw_sessions')}`",
        "",
        "## Shuheng Governance Refs",
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
    if str(source or "").startswith("secret-"):
        return None
    statement = _redact_memory_text(_strip_ohmypi_process_noise_for_memory(str(text or ""))).strip()
    if not statement or len(statement) < 80:
        return None
    if statement.startswith("[Oh My Pi]"):
        return None
    if "[Oh My Pi] Shuheng host tool" in statement and "模型没有继续生成最终回复" in statement:
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
    runtime_config: OhMyPiRuntimeConfig | None = None,
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
            "tui_typed_host_tools": True,
            "runtime_task_requests": True,
            "runtime_task_events": True,
            "artifact_refs": True,
            "memory_candidates": True,
            "memory_candidate_signals": True,
            "human_approval": False,
            "subagents": True,
            "provider_owned_subagents": True,
        },
        model_routing={
            "owner": "ga-tui.control_plane",
            "supports_runtime_switch": True,
            "supports_default_model": True,
            "supports_per_agent_default": False,
            "recent_models_path": recent_models_path,
            "selection_contract": "Shuheng /model entries projected into isolated OMP config.yml and models.yml",
            "isolated_agent_dir": runtime_config.agent_dir if runtime_config else "",
            "config_path": runtime_config.config_path if runtime_config else "",
            "models_path": runtime_config.models_path if runtime_config else "",
            "default_model": runtime_config.default_model if runtime_config else "",
            "configured_model_count": len(runtime_config.models) if runtime_config else 0,
            "tool_approval_mode": runtime_config.approval_mode if runtime_config else "",
        },
        scheduler={
            "owner": "ga-tui.control_plane",
            "status": "registry_ready",
            "schedules_path": schedules_path,
            "dispatch_contract": "agenttask.v2",
            "runtime_provider_id": "ohmypi",
        },
        policy={
            "approval_gate_owner": "ga-tui.policy",
            "tool_permissions": "tui_readonly_and_governed_proposal_tools_only",
            "runtime_tool_approval_mode": runtime_config.approval_mode if runtime_config else "yolo",
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
            "Embedded Oh My Pi uses a Shuheng-owned PI_CODING_AGENT_DIR instead of ~/.omp/agent.",
            "GenericAgent/TUI memory is injected through --append-system-prompt.",
            "Shuheng emits provider-neutral runtime.task_request.v1 and runtime.task_event.v1 records around OMP execution.",
            "Oh My Pi completion text can emit memory candidate signals; TUI remains the approval owner.",
            "Default isolated OMP approval mode is yolo: runtime tools run without OMP approval prompts inside the Shuheng-owned isolated agent directory.",
            "Only app-injected TUI query, typed read-only, and governed proposal host tools are enabled; unrestricted host tools, host URI schemes, and direct TUI approval mapping stay disabled.",
            f"runtime_root={root_dir}",
            f"harness_dir={harness_dir}",
            f"command={' '.join(command)}",
        ],
    )


__all__ = [
    "OhMyPiRpcAgent",
    "OhMyPiRuntimeAdapter",
    "OhMyPiRuntimeConfig",
    "OhMyPiRuntimeModel",
    "RuntimeEventSink",
    "build_ohmypi_memory_prompt",
    "normalized_ohmypi_approval_mode",
    "ohmypi_config_path",
    "ohmypi_isolated_agent_dir",
    "ohmypi_memory_candidate_signal",
    "ohmypi_memory_prompt_path",
    "ohmypi_models_path",
    "ohmypi_provider_spec",
    "ohmypi_rpc_command",
    "ohmypi_runtime_root",
    "ohmypi_subprocess_env",
    "redact_memory_text",
    "resolve_ohmypi_binary",
    "write_ohmypi_runtime_files",
    "write_ohmypi_memory_prompt",
]
