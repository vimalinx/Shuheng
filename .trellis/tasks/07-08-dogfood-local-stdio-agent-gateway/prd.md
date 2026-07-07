# Dogfood Local Stdio Agent Gateway

## Goal

Prove Shuheng's local JSONL stdio gateway works as a real external-agent entrypoint, not only as internal service calls. An external AI/supervisor should be able to hold `shuheng-agent-gateway serve --stdio`, discover available agents by purpose, send a governed message/task to a target agent, and query task status through the same local gateway contract.

## What I Already Know

- Shuheng's active product surface is local TUI + OMP + local JSONL stdio gateway.
- Web Console, HTTP gateway, mobile, and remote endpoints are archived and out of scope.
- `src/shuheng/agent_bridge.py` already exposes `gateway_status`, `agent_directory`, `message_send`, `task_status`, `register`, and `serve --stdio`.
- Existing policy gates validate `AgentBridgeService` directly, but do not fully dogfood a persistent subprocess speaking JSONL over stdin/stdout.
- `message_send` dispatches through `start_subagent_task_structured(...)` so Shuheng keeps Orchestrator ownership, policy gates, task ledger, traces, and approval behavior.
- External discovery must remain purpose-only and must not expose context packs, permission matrices, local paths, Secret Vault plaintext, or broad workflow internals.

## Requirements

- Add a repeatable local dogfood smoke that starts `shuheng-agent-gateway serve --stdio` as a subprocess.
- The smoke must parse the initial gateway status line and prove the transport is JSONL stdio with no Web/HTTP surface.
- The smoke must send JSONL requests for `agent_directory`, `message_send`, and `task_status` over the same running process.
- The smoke must create/use an isolated `SHUHENG_HOME` or harness directory so it does not mutate the user's normal runtime state.
- The smoke must create a deterministic local target agent fixture through Shuheng APIs or a safe fixture setup, not depend on the user's current real agents.
- `agent_directory` output must expose role/agent purpose enough for another agent to choose a target, while excluding context, permissions, local paths, and Secret details.
- `message_send` must return an accepted response with task id, target agent id, delivery mode, execution owner, and no queued-only fake success.
- `task_status` must return the task ledger status for the dispatched task.
- Evidence must prove the task entered Shuheng governance records rather than bypassing ledger/approval paths.
- Keep the supported gateway path local JSONL stdio only; do not add sockets, HTTP, mobile, remote ops, or public network binding.

## Acceptance Criteria

- [ ] `python3 scripts/dogfood_stdio_gateway.py` starts `shuheng-agent-gateway serve --stdio` and completes successfully.
- [ ] The first JSONL line is `shuheng.agent_gateway.v1` with `status:"running"`, `web_http_surface:false`, and `network_surface:"none"`.
- [ ] Sending `{"action":"agent_directory"}` over the running process returns purpose-only agent discovery and does not expose local paths, context internals, permission matrices, or Secret details.
- [ ] Sending `{"action":"message_send","args":{"target":"...","message":"..."}}` over the same process returns `accepted:true`, an Orchestrator-owned delivery contract, and a non-empty task id.
- [ ] Sending `{"action":"task_status","args":{"task_id":"..."}}` over the same process returns a successful task status payload for that task.
- [ ] The dogfood smoke verifies durable task ledger and trace/artifact/approval-safe behavior where applicable under the isolated state root.
- [ ] Policy gates include the stdio dogfood boundary so future changes cannot regress to service-only validation.
- [ ] Docs/specs state that external agents should use the local JSONL stdio gateway and that the dogfood smoke is the executable proof.
- [ ] Targeted checks, full tests, release hygiene, runtime smoke, build, wheel smoke, and `shuheng-check` pass where feasible.

## Definition Of Done

- A checked-in dogfood script or test exercises the real stdio gateway subprocess.
- Unit/policy tests cover the subprocess JSONL contract and privacy boundary.
- The runtime/provider spec and release docs are updated if the verification surface changes.
- Architecture baseline comparison is reported before completion.
- Code is committed in a focused commit, excluding unrelated `_knowledge_base/`.

## Technical Approach

Use a small deterministic smoke script rather than relying only on shell pipelines. The script should:

- Create a temporary `SHUHENG_HOME`.
- Seed a persistent local subagent fixture through app APIs in that isolated home.
- Launch the current checkout's gateway module with `PYTHONPATH=src python3 -m shuheng.agent_bridge serve --stdio`.
- Exchange newline-delimited JSON objects over stdin/stdout.
- Assert response schemas, task id propagation, privacy boundaries, and ledger visibility.
- Terminate the subprocess cleanly even on failure.

## Decision (ADR-lite)

Context: Other agents need a stable way to discover Shuheng-managed agents and send work without being given broad context, filesystem paths, or network endpoints.

Decision: The executable proof will be a local stdio subprocess dogfood smoke. It keeps the product boundary aligned with the current local-first architecture and avoids reintroducing Web/HTTP/mobile/remote surfaces.

Consequences: This validates the actual external-client path and catches serialization/process-state regressions. It does not prove remote transport, phone clients, A2A/MCP certification, or real OMP model execution completion.

## Out Of Scope

- No Web, HTTP server, socket binding, mobile endpoint, or remote gateway.
- No exposure of full context packs, permission matrix, workflow internals, local paths, Secret Vault plaintext, or runtime logs in discovery.
- No always-on service installer.
- No new agent runtime provider.
- No real user-state mutation in tests.

## Technical Notes

- Likely files: `src/shuheng/agent_bridge.py`, `src/shuheng/app.py`, `scripts/check_policy_gates.py`, a new smoke script under `scripts/`, and targeted tests if needed.
- Existing docs/specs: `docs/runtime-provider-control-plane.md`, `docs/public-alpha-readiness.md`, `docs/agent-harness-architecture.md`, `.trellis/spec/backend/agent-control-protocol.md`.
- Existing direct service gate: `assert_agent_bridge_contract_and_omp_plugin()` in `scripts/check_policy_gates.py`.
- Current public commands: `shuheng-agent-gateway register`, `agent-directory`, `serve --stdio`, `message-send`, `task-status`.
