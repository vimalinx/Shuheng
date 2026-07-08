---
name: shuheng-agent-gateway
description: Use when an external AI agent needs to discover local Shuheng agents, send a governed message or task to a Shuheng subagent, or check task status through the local JSONL stdio Shuheng gateway. Use for Shuheng inter-agent routing, agent directory lookup, and local stdio gateway messaging; not for Web, HTTP, mobile, remote access, or reading Shuheng private context.
---

# Shuheng Agent Gateway

Use Shuheng as a local governed agent directory and message target. Treat it as
a local stdio gateway owned by Shuheng's Orchestrator.

## Quick Commands

List agents:

```bash
shuheng-agent-gateway agent-directory
```

Send a governed task to a known agent:

```bash
shuheng-agent-gateway message-send --target <agent-id> --message "Task for this Shuheng agent"
```

Check a dispatched task:

```bash
shuheng-agent-gateway task-status --task-id <task-id>
```

Run a long-lived JSONL stdio gateway:

```bash
shuheng-agent-gateway serve --stdio
```

## JSONL Stdio Actions

After `serve --stdio`, send one JSON object per line:

```json
{"action":"agent_directory","args":{}}
{"action":"message_send","args":{"target":"<agent-id>","message":"Task for this Shuheng agent"}}
{"action":"task_status","args":{"task_id":"<task-id>"}}
```

Read each JSON line response before sending the next command.

## Boundaries

- Use only local CLI or JSONL stdio. Do not use Web, HTTP, mobile, remote, SSE, push, or socket assumptions.
- Use `agent_directory` to learn purpose and routing identifiers only.
- Do not read Shuheng internal context packs, task ledgers, memory files, approval stores, secret stores, permission matrices, or filesystem paths.
- Do not treat a skill as permission to bypass Shuheng approval gates.
- High-risk work is accepted only through Shuheng's governed task path and may require human approval.
- If a target is missing or ambiguous, ask the user which Shuheng agent to use instead of inventing a new target.
