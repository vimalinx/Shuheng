#!/usr/bin/env python3
"""Dogfood the Shuheng local JSONL stdio agent gateway as an external client."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_no_forbidden_payload(payload: dict[str, Any], *, isolated_home: str) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    forbidden_fragments = [
        isolated_home,
        "context_pack",
        "harness_dir",
        "subagents_dir",
        "secret_vault_dir",
        "registration_path",
        "api_key",
    ]
    for fragment in forbidden_fragments:
        if fragment and fragment in text:
            fail(f"gateway discovery leaked forbidden fragment: {fragment}")


def configure_env(isolated_home: str) -> dict[str, str]:
    env = os.environ.copy()
    env["SHUHENG_HOME"] = isolated_home
    env["SHUHENG_DISABLE_LEGACY_IMPORT"] = "1"
    env.pop("SHUHENG_HARNESS_DIR", None)
    env.pop("SHUHENG_SECRET_VAULT_DIR", None)
    env["PYTHONPATH"] = str(SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def seed_target_agent(isolated_home: str) -> str:
    os.environ["SHUHENG_HOME"] = isolated_home
    os.environ["SHUHENG_DISABLE_LEGACY_IMPORT"] = "1"
    os.environ.pop("SHUHENG_HARNESS_DIR", None)
    os.environ.pop("SHUHENG_SECRET_VAULT_DIR", None)
    sys.path.insert(0, str(SRC))
    from shuheng import app  # noqa: PLC0415
    from shuheng.agent_bridge import BridgeAgent  # noqa: PLC0415

    state = app.State(agent=BridgeAgent())
    sub = app.create_subagent(
        state,
        "Gateway Dogfood Agent",
        "A deterministic fixture agent used only by the local stdio gateway dogfood smoke.",
        role="researcher",
        persistent=True,
    )
    return sub.agent_id


class GatewayClient:
    def __init__(self, env: dict[str, str]) -> None:
        self.process = subprocess.Popen(
            [sys.executable, "-u", "-m", "shuheng.agent_bridge", "serve", "--stdio"],
            cwd=str(ROOT),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def close(self) -> None:
        if self.process.stdin:
            try:
                self.process.stdin.close()
            except OSError:
                pass
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)

    def read_json_line(self) -> dict[str, Any]:
        if self.process.stdout is None:
            fail("gateway stdout is unavailable")
        line = self.process.stdout.readline()
        if not line:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            fail(f"gateway produced no response; returncode={self.process.poll()} stderr={stderr}")
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"gateway returned invalid JSON line: {line!r}: {exc}")
        if not isinstance(payload, dict):
            fail(f"gateway response must be an object: {payload!r}")
        return payload

    def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.process.stdin is None:
            fail("gateway stdin is unavailable")
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        self.process.stdin.flush()
        return self.read_json_line()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="shuheng-stdio-gateway-") as tmp:
        isolated_home = str(Path(tmp) / "home")
        target_agent_id = seed_target_agent(isolated_home)
        env = configure_env(isolated_home)
        client = GatewayClient(env)
        try:
            status = client.read_json_line()
            if status.get("schema_version") != "shuheng.agent_gateway.v1":
                fail(f"unexpected status schema: {status}")
            if status.get("status") != "running":
                fail(f"gateway not running: {status}")
            if status.get("web_http_surface") is not False:
                fail(f"gateway exposed web/http surface: {status}")
            if status.get("network_surface") != "none":
                fail(f"gateway exposed network surface: {status}")

            directory = client.request({"action": "agent_directory", "args": {}})
            if directory.get("schema_version") != "shuheng.agent_directory.v1":
                fail(f"unexpected directory schema: {directory}")
            if directory.get("discovery_policy", {}).get("context_exposed") is not False:
                fail(f"directory exposed context: {directory}")
            if directory.get("discovery_policy", {}).get("permission_matrix_exposed") is not False:
                fail(f"directory exposed permission matrix: {directory}")
            if not any(item.get("agent_id") == target_agent_id for item in directory.get("agents", [])):
                fail(f"seeded target agent missing from directory: {directory}")
            assert_no_forbidden_payload(directory, isolated_home=isolated_home)

            sent = client.request({
                "action": "message_send",
                "args": {
                    "target": target_agent_id,
                    "message": "Dogfood request: ask for password handling guidance without receiving any password value.",
                    "task_title": "Stdio gateway dogfood",
                    "source": "dogfood_stdio_gateway",
                },
            })
            if sent.get("schema_version") != "a2a.message_send_response.v1":
                fail(f"unexpected message_send schema: {sent}")
            if sent.get("accepted") is not True:
                fail(f"message_send was not accepted: {sent}")
            if sent.get("target") != target_agent_id:
                fail(f"message_send target drifted: {sent}")
            delivery = sent.get("delivery") if isinstance(sent.get("delivery"), dict) else {}
            if delivery.get("mode") != "orchestrator_agent_task":
                fail(f"message_send bypassed orchestrator task path: {sent}")
            if delivery.get("execution_owner") != "shuheng.orchestrator":
                fail(f"message_send execution owner drifted: {sent}")
            if delivery.get("web_http_surface") is not False:
                fail(f"message_send exposed web/http surface: {sent}")
            if sent.get("status") != "approval_required":
                fail(f"dogfood request should stop at approval gate, not launch runtime: {sent}")
            task_id = str(sent.get("task_id") or "")
            approval_id = str(sent.get("approval_id") or "")
            if not task_id or not approval_id:
                fail(f"message_send missing task/approval ids: {sent}")

            task_status = client.request({"action": "task_status", "args": {"task_id": task_id}})
            if task_status.get("schema_version") != "shuheng.query.v1":
                fail(f"unexpected task_status schema: {task_status}")
            if task_status.get("status") != "ok":
                fail(f"task_status failed: {task_status}")
            task = task_status.get("task") if isinstance(task_status.get("task"), dict) else {}
            if task.get("task_id") != task_id or task.get("status") != "approval_required":
                fail(f"task_status did not return approval task row: {task_status}")
            if task.get("assigned_agent") != target_agent_id:
                fail(f"task_status assigned agent mismatch: {task_status}")

            harness_dir = Path(isolated_home) / "memory" / "agent_harness"
            task_rows = read_jsonl(harness_dir / "tasks.jsonl")
            approval_rows = read_jsonl(harness_dir / "approvals.jsonl")
            trace_rows = read_jsonl(harness_dir / "traces.jsonl")
            if not any(row.get("task_id") == task_id and row.get("status") == "approval_required" for row in task_rows):
                fail(f"durable task ledger missing dispatched task: {task_rows}")
            if not any(row.get("approval_id") == approval_id for row in approval_rows):
                fail(f"approval ledger missing approval id {approval_id}: {approval_rows}")
            if not any(row.get("task_id") == task_id and row.get("event") == "policy_gate_waiting_approval" for row in trace_rows):
                fail(f"trace ledger missing policy gate event for {task_id}: {trace_rows}")

            result = {
                "schema_version": "shuheng.gateway_dogfood.v1",
                "ok": True,
                "target_agent_id": target_agent_id,
                "task_id": task_id,
                "approval_id": approval_id,
                "status": task.get("status"),
                "checked": [
                    "gateway_status",
                    "agent_directory",
                    "message_send",
                    "task_status",
                    "task_ledger",
                    "approval_ledger",
                    "trace_ledger",
                ],
            }
            sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
            return 0
        finally:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
