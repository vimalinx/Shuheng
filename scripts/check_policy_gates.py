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
import threading
import urllib.request
import curses
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ga_tui import app as a  # noqa: E402


def retarget_harness(root: str) -> None:
    a.MODEL_RESPONSES_DIR = os.path.join(root, "model_responses")
    a.TOKEN_USAGE_PATH = os.path.join(a.MODEL_RESPONSES_DIR, "session_token_usage.json")
    a.SESSION_META_PATH = os.path.join(a.MODEL_RESPONSES_DIR, "session_meta.json")
    a.SESSION_TRASH_DIR = os.path.join(a.MODEL_RESPONSES_DIR, ".trash")
    a.AGENT_HARNESS_DIR = os.path.join(root, "harness")
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
    a.AGENT_GATEWAY_PUSH_SUBSCRIPTIONS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_push_subscriptions.jsonl")
    a.AGENT_GATEWAY_PUSH_DELIVERIES_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_push_deliveries.jsonl")
    a.AGENT_GATEWAY_DAEMON_PID_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_daemon.pid")
    a.AGENT_GATEWAY_DAEMON_STATUS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_daemon.json")
    a.AGENT_GATEWAY_DAEMON_LOG_PATH = os.path.join(a.AGENT_HARNESS_DIR, "gateway_daemon.log")
    a.AGENT_BRIDGE_REGISTRY_PATH = os.path.join(a.AGENT_HARNESS_DIR, "bridge_registry.json")
    a.LLM_RECENT_MODELS_PATH = os.path.join(a.AGENT_HARNESS_DIR, "recent_models.json")
    a.SECRET_VAULT_DIR = os.path.join(root, "secret_vault")
    a.SECRET_VAULT_META_PATH = os.path.join(a.SECRET_VAULT_DIR, "vault.json")
    a.SECRET_VAULT_DATA_DIR = os.path.join(a.SECRET_VAULT_DIR, "data")
    a.SECRET_VAULT_SESSIONS_DIR = os.path.join(a.SECRET_VAULT_DATA_DIR, "sessions")
    a.SUBAGENTS_DIR = os.path.join(root, "subagents")
    a.TEMP_SUBAGENTS_DIR = os.path.join(root, "temp-subagents")
    os.makedirs(a.AGENT_HARNESS_DIR, exist_ok=True)
    os.makedirs(a.SUBAGENTS_DIR, exist_ok=True)
    os.makedirs(a.TEMP_SUBAGENTS_DIR, exist_ok=True)


class FakeAgent:
    def put_task(self, prompt: str, source: str = "") -> queue.Queue:
        del prompt, source
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

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        self.calls.append((y, x, text, attr))


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
    assert any(item["uri"] == "resource://agent-mail/gateway-daemon" for item in mcp["resources"]), mcp
    assert any(item["uri"] == "resource://agent-mail/bridges" for item in mcp["resources"]), mcp
    assert any(item["name"] == "repo.read" for item in mcp["tools"]), mcp
    capabilities = registry["capability_registry"]
    assert capabilities["schema_version"] == "agentcapabilities.v1", capabilities
    assert "researcher" in capabilities["roles"], capabilities
    assert capabilities["roles"]["researcher"]["permissions"]["write_policy"] == "none", capabilities
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
    assert pack["layers"]["L1_user_profile"]["included"] is False, pack["layers"]["L1_user_profile"]
    assert pack["layers"]["L3_task_brief"]["source_policy"]["allowed_sources"], pack["layers"]["L3_task_brief"]
    assert "memory_pack_ref" in pack["layers"]["L6_working_notes"], pack["layers"]["L6_working_notes"]
    assert isinstance(pack["layers"]["L7_artifacts"]["items"], list), pack["layers"]["L7_artifacts"]
    assert pack["source_policy"]["allowed_sources"], pack["source_policy"]
    prompt = a.format_context_pack_for_prompt(pack)
    assert "Source policy:" in prompt, prompt
    assert "Memory hydration pack:" in prompt, prompt
    assert "Recent artifact refs:" in prompt, prompt
    return pack


def assert_restored_process_group_main_speech_visible() -> None:
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
    assert "第一段主代理说明：先检查已有子代理。" in rendered, rendered
    assert "第二段主代理说明：现在派发任务并等待回复。" in rendered, rendered
    assert "最终主代理总结：两个步骤都已处理。" in rendered, rendered
    assert rendered.count("最终主代理总结：两个步骤都已处理。") == 1, rendered
    assert "· 过程 Turn 1" not in rendered, rendered
    assert "· 过程 Turn 2" not in rendered, rendered
    assert "hidden lookup" not in rendered, rendered
    assert "hidden.txt" not in rendered, rendered
    assert "hidden tool output" not in rendered, rendered


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
    assert reloaded.selected_session == "main", reloaded.selected_session
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


def assert_subagent_create_respects_force_new_and_topic_terms() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_subagent_create_")
    retarget_harness(root)
    state = a.State(agent=ContextFakeAgent())
    state.running = True
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
    assert len(falsesocial_agents) == 2, [(sub.agent_id, sub.name) for sub in state.subagents.values()]
    assert len({sub.agent_id for sub in falsesocial_agents}) == 2

    a.apply_tui_controls_from_text(
        state,
        ga_control(create_agent_action("FalseSocial 管理代理", persistent=True, force_new=True, profile="专门管理 falsesocial 的账号、内容和运维事项。")),
        source="agent",
    )
    falsesocial_agents = [sub for sub in state.subagents.values() if "falsesocial" in sub.agent_id]
    assert len(falsesocial_agents) == 3, [(sub.agent_id, sub.name) for sub in state.subagents.values()]
    a.apply_tui_controls_from_text(
        state,
        '<ga-tui>{"action":"subagent_create","name":"Legacy Should Not Run","persistent":true}</ga-tui>',
        source="agent",
    )
    assert a.resolve_subagent(state, "Legacy Should Not Run") is None

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
    assert "schema_version:\"ga-control.v2\"" in a.TUI_AGENT_CONTROL_HINT
    assert "delegate.create" in a.TUI_AGENT_CONTROL_HINT
    assert "能力说明" in a.TUI_AGENT_CONTROL_HINT
    assert "不要在示例、教程或解释中包含可执行 `<ga-control>` 标签" in a.TUI_AGENT_CONTROL_HINT
    assert "回复末尾隐藏块" in a.TUI_AGENT_CONTROL_HINT
    assert '<ga-tui>{"action":"subagent_ask"' not in a.TUI_AGENT_CONTROL_HINT
    assert "secret_subagents" in a.TUI_AGENT_CONTROL_HINT
    assert "memory/subagents/" in a.TUI_AGENT_CONTROL_HINT
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


def assert_legacy_subagent_result_backfills_to_restored_session() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_legacy_subagent_restore_")
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


def assert_self_intro_does_not_consume_mutual_chat_step() -> None:
    root = tempfile.mkdtemp(prefix="ga_tui_policy_check_")
    retarget_harness(root)
    install_fake_agent_runtime()
    main_agent = SequencedFakeAgent(["我没有发出新的控制块。"])
    state = a.State(agent=main_agent)
    state.running = True
    orchestration_text = ga_control(
        plan_action("缺少自我介绍步骤的双代理对话", ["创建正式子代理", "创建临时子代理", "两个代理互相聊天对话", "汇总所有内容到我这里"]),
        create_agent_action("正式丙", persistent=True, profile="你是正式永久子代理，名叫正式丙。稍后和临时子代理临时丁交流。"),
        create_agent_action("临时丁", temporary=True, profile="你是临时子代理，名叫临时丁。稍后和正式子代理正式丙交流。"),
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
    assert streaming_key_frame0 in state.message_block_cache, state.message_block_cache.keys()

    state.run_frame = 1
    a.message_lines_cached(state, 80)
    assert state.message_block_cache[stable_key] is stable_block
    assert streaming_key_frame0 not in state.message_block_cache
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
    assert streaming_key_frame1 in state.message_block_cache, state.message_block_cache.keys()


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


def run_checks() -> None:
    assert_top_bar_header_requested_fields()
    assert_long_secret_render_reuses_stable_message_blocks()
    assert_secret_native_restore_hydrates_backend_context_blocks()
    assert_restored_process_group_main_speech_visible()
    assert_process_detail_line_not_swallowed_by_code_fence()
    assert_single_search_turn_keeps_final_reply_visible()
    assert_ask_user_tool_use_input_payload_visible()
    assert_ask_user_multiline_tool_args_payload_visible()
    assert_aux_mouse_buttons_do_not_start_selection()
    assert_subagent_result_context_update_from_notice()
    assert_live_subagent_result_reaches_main_context()
    assert_selected_subagent_chat_is_direct_session()
    assert_running_main_input_is_queued_and_interruptible()
    assert_subagent_create_respects_force_new_and_topic_terms()
    assert_legacy_subagent_result_backfills_to_restored_session()
    assert_recent_sessions_use_last_message_activity()
    assert_self_intro_does_not_consume_mutual_chat_step()

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
        ok_recent, recent_msg = a.remember_recent_model_entry(llm_entries[1], llm_entries)
        assert ok_recent, recent_msg
        ok_recent, recent_msg = a.remember_recent_model_entry(llm_entries[0], llm_entries)
        assert ok_recent, recent_msg
        assert a.load_recent_model_names(llm_entries)[:2] == ["alpha", "beta"]
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
        assert sub.agent.llm_no == 0
    finally:
        a.mykey_path = old_mykey_path

    old_probe_models = a.probe_models_for_config
    try:
        a.probe_models_for_config = lambda _cfg_type, _cfg, timeout=12.0: (True, ["model-alpha", "model-gamma"], "ok")
        ok_probe, added_models, probe_msg = a.probe_and_merge_models(llm_entries[0], llm_entries)
        assert ok_probe, probe_msg
        assert [entry.cfg["model"] for entry in added_models] == ["model-gamma"], added_models
    finally:
        a.probe_models_for_config = old_probe_models
    help_state = a.State(agent=ContextFakeAgent())
    a.submit(help_state, "/LlM")
    assert "管理模型配置" in help_state.messages[-1].content
    a.submit(help_state, "/MODEL")
    assert "当前对话模型" in help_state.messages[-1].content
    assert "默认新对话模型" in help_state.messages[-1].content

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
                create_agent_action("续跑正式", persistent=True, profile="正式测试子代理"),
            ),
            ga_control(create_agent_action("续跑临时", temporary=True, profile="临时测试子代理")),
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
                create_agent_action("阻塞正式", persistent=True, profile="正式测试子代理"),
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
    assert_gateway_schema(registry)
    baseline_report = registry["baseline_comparison"]
    assert_baseline_report_schema(baseline_report)
    baseline_items = a.baseline_panel_items(state)
    assert baseline_items and baseline_items[0].key == "summary", baseline_items
    assert any(item.key == "a2a_mcp_gateway" for item in baseline_items), baseline_items
    formatted_baseline = a.format_baseline_report(baseline_report)
    assert "Architecture Baseline Comparison" in formatted_baseline, formatted_baseline
    assert a.AGENT_BASELINE_REPORT_PATH in formatted_baseline, formatted_baseline
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
    assert any(
        msg.role == "user"
        and "[GA TUI AgentTask Envelope v2]" in msg.content
        and '"tools_forbidden": [' in msg.content
        and '"deploy"' in msg.content
        for msg in contract_sub.messages
    ), contract_sub.messages
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
        create_agent_action("正式甲", persistent=True, profile="你是正式永久子代理，名叫正式甲。稍后和临时子代理临时乙交流。"),
        create_agent_action("临时乙", profile="你是临时子代理，名叫临时乙。稍后和正式子代理正式甲交流。"),
        delegate_action("正式甲", "请先向主控说一句话自我介绍，说完了告诉我。"),
        delegate_action("临时乙", "请先向主控说一句话自我介绍，说完了告诉我。"),
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
