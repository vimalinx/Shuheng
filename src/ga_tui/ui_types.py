"""Shared UI state dataclasses for Shuheng."""
from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional


HOME_SESSION_PREFIX = "__home__:"
MAIN_HOME_SESSION_KEY = HOME_SESSION_PREFIX + "main"
SCHEDULED_REPORTS_SESSION_KEY = HOME_SESSION_PREFIX + "scheduled_reports"
SUBAGENT_HOME_SESSION_PREFIX = HOME_SESSION_PREFIX + "sub:"


@dataclass
class Message:
    role: str
    content: str
    done: bool = True


@dataclass
class RenderLine:
    text: str
    attr: int = 0
    kind: str = ""
    prefix_cells: int = 0
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMConfigEntry:
    var_name: str
    cfg_type: str
    cfg: dict[str, Any]


@dataclass
class ModelManagerCategoryIndex:
    categories: list[str]
    indices_by_category: dict[str, list[int]]
    preferred_category_by_index: dict[int, str]
    status_by_category: dict[str, str]


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
    temporary_session: bool = False


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
    dashboard: dict[str, Any] = field(default_factory=dict)
    skill_refs: list[str] = field(default_factory=list)
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
class SubagentDispatchResult:
    status: str
    message: str
    task_id: str = ""
    approval_id: str = ""
    error: str = ""
    provider_id: str = ""


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
    workflow_draft_payload: dict[str, Any] | None = None
    workflow_draft_goal: str = ""
    workflow_draft_ref: str = ""
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
    selected_session: Any = MAIN_HOME_SESSION_KEY
    temporary_session: bool = False
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
    home_line_cache_key: tuple[Any, ...] = ()
    home_line_cache: list[RenderLine] = field(default_factory=list)
    home_line_cache_loaded_at: float = 0.0
    main_x0: int = 0
    main_width: int = 0
    body_top: int = 1
    body_height: int = 0
    running_indicator_rect: Optional[tuple[int, int, int, int]] = None
    input_cursor_screen: Optional[tuple[int, int]] = None
    active_plan_task_id: str = ""
    active_plan_steps: dict[str, str] = field(default_factory=dict)
    auto_plan_continue_attempts: dict[str, int] = field(default_factory=dict)
    auto_plan_continue_plan_attempts: dict[str, int] = field(default_factory=dict)
    auto_plan_continue_last_blocked: str = ""
    auto_control_continue_attempts: dict[str, int] = field(default_factory=dict)
    auto_control_continue_count: int = 0
    auto_control_continue_last_blocked: str = ""
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
    main_dashboard: dict[str, Any] = field(default_factory=dict)
    description_jobs: set[str] = field(default_factory=set)
    description_signatures: dict[str, str] = field(default_factory=dict)
    category_jobs: set[str] = field(default_factory=set)
    category_signatures: dict[str, str] = field(default_factory=dict)
    token_usage_registry_signature: tuple[float, int] = (0.0, -1)
