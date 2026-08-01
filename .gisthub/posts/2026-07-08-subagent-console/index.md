---
title: "子 Agent 控制台与本地 stdio Gateway"
date: 2026-07-08
type: note
cover: images/cover.png
tags: [子Agent, gateway, stdio, 架构]
author: "vimalinx"
---

这周给 Shuheng 落了本地 stdio agent gateway，顺手整理下子 Agent 体系的玩法 📝

## 临时 vs 持久子 Agent

| 类型 | 适合场景 | 行为 |
| --- | --- | --- |
| 临时子 Agent | 一次性任务、短调研 | 不长期保存身份，用完即走 |
| 持久子 Agent | 长期项目、固定角色 | 稳定身份，可存 profile、职责、记忆候选和默认模型 |

内置角色：Researcher / Coder / Reviewer / Verifier / Memory curator / Ops agent。

```text
/agent new researcher        新建子 agent
/agent ask researcher 查这个库的最佳实践
/agent remember researcher 这条结论长期有效
/agent stop researcher       停止
```

也可以自然语言：「开一个临时研究员，帮我查这个库的最佳实践」。

## 外部 AI 怎么接进来

新增本地 JSONL stdio gateway，给外部 AI / supervisor 持有的持久本地进程：

```bash
shuheng install-agent-gateway-skill
shuheng-agent-gateway register
shuheng-agent-gateway agent-directory
shuheng-agent-gateway serve --stdio
shuheng-agent-gateway message-send --target <agent-id> --message "任务"
shuheng-agent-gateway task-status --task-id <task-id>
```

几个关键设计：

- `serve --stdio` 公开动作固定为四个：`agent_directory`、`message_send`、`task_status`、`gateway_status`
- 内部 metadata、文件路径和其他 bridge 动作不会跨过这个进程边界
- `message-send` 走 Shuheng Orchestrator 的子 agent task 路径和审批门，不是裸奔
- `shuheng-agent-bridge` 是受信内部集成面，不要交给不受信客户端

端到端验证有现成脚本：`python scripts/dogfood_stdio_gateway.py`，会在隔离的 `SHUHENG_HOME` 里起真实子进程，验证 agent 发现、消息投递、task / approval / trace 账本。

原则不变：子 Agent 按 role、permission、budget、stop condition 执行，写操作保持单写者受控，人类审批门兜底。
