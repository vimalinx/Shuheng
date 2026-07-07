"""Local agent bridge API for Shuheng-managed context and proposals.

This module is intentionally a thin boundary over existing app-owned services.
Agent clients such as OMP plugins should call this bridge instead of reading
Shuheng files directly or writing memory/scheduler ledgers themselves.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any


BRIDGE_SCHEMA_VERSION = "shuheng.agent_bridge.v1"
GATEWAY_SCHEMA_VERSION = "shuheng.agent_gateway.v1"
SUPPORTED_ACTIONS = (
    "metadata",
    "agent_directory",
    "agent_list",
    "agent_get",
    "agent_match",
    "message_send",
    "task_status",
    "gateway_status",
    "gateway_register",
    "query",
    "memory_context_get",
    "memory_candidate_submit",
    "proposal_submit",
    "delegate",
    "studio_state",
    "studio_update",
)


@dataclass(frozen=True)
class BridgeOptions:
    genericagent_root: str = ""
    harness_dir: str = ""
    secret_vault_dir: str = ""


class BridgeAgent:
    """Minimal State.agent substitute for offline bridge calls."""

    def __init__(self) -> None:
        self.log_path = ""
        self.llmclients: list[Any] = []
        self.history: list[Any] = []

    def get_llm_name(self, model: bool = False) -> str:
        del model
        return "agent-bridge"

    def abort(self) -> None:
        return None


def _install_env(options: BridgeOptions) -> None:
    if options.genericagent_root:
        os.environ["GENERICAGENT_ROOT"] = os.path.abspath(os.path.expanduser(options.genericagent_root))
    if options.harness_dir:
        os.environ["SHUHENG_HARNESS_DIR"] = os.path.abspath(os.path.expanduser(options.harness_dir))
    if options.secret_vault_dir:
        os.environ["SHUHENG_SECRET_VAULT_DIR"] = os.path.abspath(os.path.expanduser(options.secret_vault_dir))


def load_app(options: BridgeOptions | None = None) -> Any:
    """Load the app module after applying path env overrides."""

    _install_env(options or BridgeOptions())
    return importlib.import_module("shuheng.app")


def create_bridge_state(app: Any | None = None) -> Any:
    """Create a minimal state and hydrate durable subagent metadata."""

    app = app or load_app()
    state = app.State(agent=BridgeAgent())
    state.current_title = "agent-bridge"
    try:
        app.load_subagents(state)
    except Exception:
        # Read failures are surfaced by downstream target lookup/errors.
        pass
    return state


def bridge_metadata(app: Any | None = None) -> dict[str, Any]:
    app = app or load_app()
    return {
        "schema_version": BRIDGE_SCHEMA_VERSION,
        "status": "ok",
        "owner": "shuheng.control_plane",
        "supported_actions": list(SUPPORTED_ACTIONS),
        "contracts": {
            "agent_directory": "purpose_only_agent_discovery",
            "message_send": "orchestrator_owned_agent_task_dispatch",
            "task_status": "task_ledger_status_query",
            "memory_context_get": "read_only_context_pack",
            "memory_candidate_submit": "candidate_only_human_approval",
            "proposal_submit": "governed_schema_proposal",
            "gateway_transport": "jsonl_stdio_or_one_shot_cli",
        },
        "paths": {
            "app_root_dir": getattr(app, "APP_ROOT_DIR", ""),
            "external_runtime_checkout_configured": bool(getattr(app, "GENERICAGENT_ROOT", "")),
            "shuheng_home": getattr(app, "SHUHENG_HOME", ""),
            "shuheng_memory_dir": getattr(app, "SHUHENG_MEMORY_DIR", ""),
            "harness_dir": getattr(app, "AGENT_HARNESS_DIR", ""),
            "runtime_registry": getattr(app, "AGENT_RUNTIME_REGISTRY_PATH", ""),
            "memory_candidates": getattr(app, "AGENT_MEMORY_CANDIDATES_PATH", ""),
            "approvals": getattr(app, "AGENT_APPROVALS_PATH", ""),
            "subagents_dir": getattr(app, "SUBAGENTS_DIR", ""),
            "secret_vault_dir": getattr(app, "SECRET_VAULT_DIR", ""),
        },
        "policy": {
            "long_term_memory_write": "candidate_only",
            "approval_owner": "shuheng.policy",
            "provider_direct_writes": False,
            "network_surface": "none",
            "web_http_surface": False,
            "execution_owner": "shuheng.orchestrator",
        },
    }


def bridge_error(message: str, **extra: Any) -> dict[str, Any]:
    return {
        "schema_version": BRIDGE_SCHEMA_VERSION,
        "status": "error",
        "error": message,
        **extra,
    }


class AgentBridgeService:
    """Provider-neutral bridge facade consumed by local agent clients."""

    def __init__(self, app: Any | None = None, state: Any | None = None) -> None:
        self.app = app or load_app()
        self.state = state if state is not None else create_bridge_state(self.app)
        self.started_at = time.time()

    def query(self, endpoint: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.app.ohmypi_tui_query_endpoint(self.state, endpoint, args or {})

    def refresh(self) -> None:
        try:
            self.app.load_subagents(self.state)
        except Exception:
            pass

    def gateway_status(self) -> dict[str, Any]:
        metadata = bridge_metadata(self.app)
        return {
            "schema_version": GATEWAY_SCHEMA_VERSION,
            "status": "running",
            "transport": "jsonl_stdio_or_one_shot_cli",
            "pid": os.getpid(),
            "uptime_seconds": max(0, int(time.time() - self.started_at)),
            "owner": "shuheng.control_plane",
            "web_http_surface": False,
            "network_surface": "none",
            "supported_actions": list(SUPPORTED_ACTIONS),
            "metadata": metadata,
        }

    def gateway_registration(self) -> dict[str, Any]:
        register_fn = getattr(self.app, "register_persistent_agent_gateway", None)
        if not callable(register_fn):
            return bridge_error("Shuheng app does not expose gateway registration.")
        return register_fn()

    def agent_directory(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(args or {})
        self.refresh()
        if payload.get("public", True):
            registry = self.app.ensure_local_protocol_registry(self.state)
            return self.app.local_protocol_public_registry(registry)["agent_directory"]
        return self.query("agent_list", payload)

    def agent_list(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        self.refresh()
        return self.query("agent_list", args or {})

    def agent_get(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        self.refresh()
        return self.query("agent_get", args or {})

    def agent_match(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        self.refresh()
        return self.query("agent_match", args or {})

    def message_send(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(args or {})
        self.refresh()
        target = str(payload.get("target") or payload.get("agent_id") or payload.get("recipient") or "").strip()
        text = str(payload.get("message") or payload.get("text") or payload.get("content") or payload.get("objective") or "").strip()
        if not target:
            return bridge_error("message_send requires target.")
        if not text:
            return bridge_error("message_send requires message text.")
        mode = str(payload.get("mode") or "task").strip().lower()
        if mode not in {"task", "inbox"}:
            return bridge_error("message_send mode must be task or inbox.", mode=mode)
        if mode == "inbox":
            result, status_code = self.app.append_agent_mail_intake_message({
                **payload,
                "target": target,
                "message": text,
                "from_agent": str(payload.get("from_agent") or payload.get("from") or "external.agent"),
            })
            result["http_status_equivalent"] = status_code
            return result
        sub = self.app.resolve_subagent(self.state, target)
        if sub is None:
            return bridge_error("Target subagent was not found or was ambiguous.", target=target)
        dispatch = self.app.start_subagent_task_structured(
            self.state,
            sub,
            text,
            source=str(payload.get("source") or "agent_gateway"),
            parent_task_id=str(payload.get("parent_task_id") or payload.get("parentTaskId") or ""),
            task_title=str(payload.get("task_title") or payload.get("title") or ""),
        )
        return {
            "schema_version": "a2a.message_send_response.v1",
            "accepted": dispatch.status not in {"failed", "rejected"},
            "status": dispatch.status,
            "contextId": "shuheng",
            "delivery": {
                "mode": "orchestrator_agent_task",
                "auto_dispatch": True,
                "transport": "local_jsonl_stdio",
                "execution_owner": "shuheng.orchestrator",
                "web_http_surface": False,
            },
            "target": sub.agent_id,
            "agent": {"agent_id": sub.agent_id, "name": sub.name, "role": self.app.normalized_subagent_role(sub.role)},
            "task_id": dispatch.task_id,
            "approval_id": dispatch.approval_id,
            "provider_id": dispatch.provider_id,
            "message": dispatch.message,
            "error": dispatch.error,
        }

    def task_status(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(args or {})
        task_id = str(payload.get("task_id") or payload.get("taskId") or "").strip()
        if not task_id:
            return bridge_error("task_status requires task_id.")
        row = self.app.latest_task_records().get(task_id)
        if not isinstance(row, dict):
            return bridge_error("task was not found.", task_id=task_id)
        return self.app.tui_tool_task_get(self.state, {"task_id": task_id})

    def memory_context_get(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.query("memory_context_get", args or {})

    def memory_candidate_submit(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(args or {})
        payload.setdefault("proposal_type", "memory_candidate")
        payload.setdefault("source", "agent:omp_plugin")
        payload.setdefault("evidence_ref", "runtime://provider/ohmypi/plugin")
        return self.app.ohmypi_tui_propose_memory_candidate(self.state, payload)

    def proposal_submit(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(args or {})
        if payload.get("proposal_type") == "memory_candidate":
            payload.setdefault("source", "agent:omp_plugin")
            payload.setdefault("evidence_ref", "runtime://provider/ohmypi/plugin")
        return self.app.ohmypi_tui_propose_host_tool_handler(self.state, payload)

    def delegate(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        """Delegate work to a professional subagent via shuheng-control v2.

        Args:
            agent_role: Target agent role (e.g., "novelist")
            objective: Task objective
            workdir: Optional workspace root
            success_criteria: Optional list of success criteria
            stop_condition: Optional stop condition

        Returns:
            shuheng-control delegate.create result or error.
        """
        payload = dict(args or {})
        agent_role = str(payload.get("agent_role") or "").strip()
        objective = str(payload.get("objective") or "").strip()
        if not agent_role or not objective:
            return bridge_error("delegate requires agent_role and objective.")
        # Use the TUI's shuheng-control dispatch to create a delegation
        return self.query("delegate_create", payload)

    def studio_state(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        """Get a professional agent's Studio state (blocks for managed regions).

        Args:
            agent_role: Target agent role

        Returns:
            Studio blocks grouped by managed region.
        """
        payload = dict(args or {})
        agent_role = str(payload.get("agent_role") or "").strip()
        if not agent_role:
            return bridge_error("studio_state requires agent_role.")
        return self.query("studio_state", payload)

    def studio_update(self, args: dict[str, Any] | None = None) -> dict[str, Any]:
        """Write a human-initiated UI update into a professional agent's memory.

        Args:
            agent_role: Target agent role
            region: Managed region name
            block: Block data { type, data }

        Returns:
            Confirmation of the memory write.
        """
        payload = dict(args or {})
        agent_role = str(payload.get("agent_role") or "").strip()
        region = str(payload.get("region") or "").strip()
        if not agent_role or not region:
            return bridge_error("studio_update requires agent_role and region.")
        return self.query("studio_update", payload)


    def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return bridge_error("Bridge payload must be a JSON object.")
        action = str(payload.get("action") or "").strip()
        args = payload.get("args") if isinstance(payload.get("args"), dict) else {}
        if action == "metadata":
            return bridge_metadata(self.app)
        if action == "gateway_status":
            return self.gateway_status()
        if action == "gateway_register":
            return self.gateway_registration()
        if action == "agent_directory":
            return self.agent_directory(args)
        if action == "agent_list":
            return self.agent_list(args)
        if action == "agent_get":
            return self.agent_get(args)
        if action == "agent_match":
            return self.agent_match(args)
        if action == "message_send":
            return self.message_send(args)
        if action == "task_status":
            return self.task_status(args)
        if action == "query":
            endpoint = str(payload.get("endpoint") or args.get("endpoint") or "").strip()
            endpoint_args = args.get("args") if isinstance(args.get("args"), dict) else args
            if not endpoint:
                return bridge_error("query action requires endpoint.")
            return self.query(endpoint, endpoint_args)
        if action == "memory_context_get":
            return self.memory_context_get(args)
        if action == "memory_candidate_submit":
            return self.memory_candidate_submit(args)
        if action == "proposal_submit":
            return self.proposal_submit(args)
        if action == "delegate":
            return self.delegate(args)
        if action == "studio_state":
            return self.studio_state(args)
        if action == "studio_update":
            return self.studio_update(args)
        return bridge_error("Unsupported action.", action=action, supported_actions=list(SUPPORTED_ACTIONS))


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except Exception as exc:
        raise ValueError(f"invalid JSON: {type(exc).__name__}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object")
    return payload


def run_bridge_call(payload: dict[str, Any], options: BridgeOptions | None = None) -> dict[str, Any]:
    app = load_app(options)
    service = AgentBridgeService(app=app)
    return service.handle(payload)


def serve_jsonl(options: BridgeOptions | None = None, *, stdin: Any = None, stdout: Any = None) -> int:
    service = AgentBridgeService(app=load_app(options), state=None)
    in_fh = stdin or sys.stdin
    out_fh = stdout or sys.stdout
    out_fh.write(json.dumps(service.gateway_status(), ensure_ascii=False, sort_keys=True) + "\n")
    out_fh.flush()
    for raw_line in in_fh:
        line = str(raw_line or "").strip()
        if not line:
            continue
        try:
            payload = parse_json_object(line)
            response = service.handle(payload)
        except Exception as exc:
            response = bridge_error(f"{type(exc).__name__}: {exc}")
        out_fh.write(json.dumps(response, ensure_ascii=False, sort_keys=True) + "\n")
        out_fh.flush()
    return 0


def _common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default="", help="optional compatibility checkout path")
    parser.add_argument("--harness-dir", default="", help="Shuheng harness directory override")
    parser.add_argument("--secret-vault-dir", default="", help="Shuheng secret vault directory override")


def _options_from_args(args: argparse.Namespace) -> BridgeOptions:
    return BridgeOptions(
        genericagent_root=str(getattr(args, "root", "") or ""),
        harness_dir=str(getattr(args, "harness_dir", "") or ""),
        secret_vault_dir=str(getattr(args, "secret_vault_dir", "") or ""),
    )


def _print_json(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shuheng local agent bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    metadata = sub.add_parser("metadata", help="print bridge metadata")
    _common_options(metadata)

    status = sub.add_parser("status", help="print local gateway status")
    _common_options(status)

    register = sub.add_parser("register", help="register Shuheng as a local persistent stdio gateway")
    _common_options(register)

    serve = sub.add_parser("serve", help="serve bridge requests over JSONL stdio; no socket or HTTP server is opened")
    _common_options(serve)
    serve.add_argument("--stdio", action="store_true", help="serve JSONL over stdin/stdout")

    call = sub.add_parser("call", help="execute a bridge JSON payload")
    _common_options(call)
    call.add_argument("payload", nargs="?", default="", help="JSON payload; reads stdin when omitted")

    directory = sub.add_parser("agent-directory", help="print public agent directory")
    _common_options(directory)

    send = sub.add_parser("message-send", help="send a governed local message/task to a Shuheng agent")
    _common_options(send)
    send.add_argument("--target", required=True)
    send.add_argument("--message", required=True)
    send.add_argument("--mode", choices=["task", "inbox"], default="task")
    send.add_argument("--from-agent", default="external.agent")
    send.add_argument("--title", default="")

    task_status = sub.add_parser("task-status", help="read task status for a dispatched message")
    _common_options(task_status)
    task_status.add_argument("--task-id", required=True)

    query = sub.add_parser("query", help="execute a read-only query endpoint")
    _common_options(query)
    query.add_argument("endpoint")
    query.add_argument("--args-json", default="{}", help="endpoint args JSON object")

    context = sub.add_parser("context-get", help="generate a context pack")
    _common_options(context)
    context.add_argument("--target", default="")
    context.add_argument("--objective", default="Shuheng bridge context request")
    context.add_argument("--task-id", default="")
    context.add_argument("--parent-task-id", default="")

    memory = sub.add_parser("memory-candidate-submit", help="submit a governed memory candidate")
    _common_options(memory)
    memory.add_argument("--target", required=True)
    memory.add_argument("--statement", required=True)
    memory.add_argument("--evidence-ref", default="")
    memory.add_argument("--task-id", default="")

    args = parser.parse_args(argv)
    options = _options_from_args(args)

    try:
        if args.command == "metadata":
            _print_json(bridge_metadata(load_app(options)))
            return 0
        if args.command == "status":
            _print_json(AgentBridgeService(app=load_app(options)).gateway_status())
            return 0
        if args.command == "register":
            _print_json(AgentBridgeService(app=load_app(options)).gateway_registration())
            return 0
        if args.command == "serve":
            return serve_jsonl(options)
        if args.command == "call":
            raw_payload = args.payload or sys.stdin.read()
            _print_json(run_bridge_call(parse_json_object(raw_payload), options))
            return 0
        if args.command == "agent-directory":
            _print_json(run_bridge_call({"action": "agent_directory", "args": {}}, options))
            return 0
        if args.command == "message-send":
            payload = {
                "action": "message_send",
                "args": {
                    "target": args.target,
                    "message": args.message,
                    "mode": args.mode,
                    "from_agent": args.from_agent,
                    "task_title": args.title,
                },
            }
            _print_json(run_bridge_call(payload, options))
            return 0
        if args.command == "task-status":
            _print_json(run_bridge_call({"action": "task_status", "args": {"task_id": args.task_id}}, options))
            return 0
        if args.command == "query":
            payload = {
                "action": "query",
                "endpoint": args.endpoint,
                "args": parse_json_object(args.args_json),
            }
            _print_json(run_bridge_call(payload, options))
            return 0
        if args.command == "context-get":
            payload = {
                "action": "memory_context_get",
                "args": {
                    "target": args.target,
                    "objective": args.objective,
                    "task_id": args.task_id,
                    "parent_task_id": args.parent_task_id,
                },
            }
            _print_json(run_bridge_call(payload, options))
            return 0
        if args.command == "memory-candidate-submit":
            payload = {
                "action": "memory_candidate_submit",
                "args": {
                    "target": args.target,
                    "statement": args.statement,
                    "evidence_ref": args.evidence_ref,
                    "task_id": args.task_id,
                },
            }
            _print_json(run_bridge_call(payload, options))
            return 0
    except Exception as exc:
        _print_json(bridge_error(f"{type(exc).__name__}: {exc}"))
        return 1
    return 2


def gateway_main(argv: list[str] | None = None) -> int:
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
