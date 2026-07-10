# Agent Harness Architecture Baseline

以下内容由用户提供并作为持续维护的架构基准。后续完成 TUI / agent harness 相关工作后，都要自动和本文档比对，确认实现是否更接近该目标架构。

---

你这套系统最正确的方向不是“很多 Agent 自由聊天”，而是：

一个强主控 Orchestrator + 多个受限子 Agent + 共享任务账本 + artifact 引用 + 单写者原则 + 人类审批门 + 可审计通信协议 + 外部长期记忆。

这也是目前前沿实践里越来越清晰的方向。Anthropic 的多 Agent 研究系统采用的是 lead agent 规划、拆分任务、并行生成 subagent，再由主 Agent 综合结果的模式；他们报告说在内部研究评估中，多 Agent 系统相对单 Agent 有明显提升，但代价是 token 使用大幅增加，而且只在任务天然可并行、上下文超过单窗口、工具很多或搜索空间很大的时候最划算。

Cognition/Devin 的经验更“泼冷水”，也更适合工程落地：多 Agent 最容易死在上下文传递不完整、隐含决策丢失、写操作冲突上。它们认为真正有用的形态往往不是无结构 swarm，而是“读任务并行、写任务单线、审查任务清洁上下文、多 Agent 通过明确桥梁通信”。

所以你要做的不是“Agent 越多越智能”，而是把 Agent 设计成一种受协议约束的工程资源：该并行时并行，该隔离时隔离，该串行时串行，该人类审批时绝不自动越权。

三、信息源分级与当前前沿共识
1. 最高优先级信息源

我建议你把来源分成四档：

第一档：前沿实验室工程报告和官方文档。
包括 Anthropic multi-agent research system、Claude Code context engineering、OpenAI Agents SDK/Codex subagents、A2A、MCP、Cognition/Devin、Microsoft AutoGen/Magentic-One、LangGraph/LangChain。这些来源的价值在于它们不是单纯讲概念，而是在讲“实际跑长任务时怎么失败、怎么恢复、怎么控制上下文、怎么设审批”。

第二档：协议规范。
MCP 负责 Agent 到工具/资源的连接，A2A 负责 Agent 到 Agent 的互操作。A2A 官方把它定位成 Agent 间通信标准，核心对象包括 Agent Card、Task、Message、Part、Artifact、contextId，并支持 request/response、SSE 流式更新和 push notification。MCP 官方则把 MCP 定义为把 AI 应用连接到外部系统、数据、工具和工作流的开放标准。

第三档：论文与综述。
通信中心化的 LLM 多 Agent 综述把 LLM-MAS 看作“受通信协议约束的自动化系统”，并把架构分成 flat、hierarchical、team、society、hybrid 等类型；这对你设计“什么时候是子 Agent、什么时候是 Agent 团队、什么时候是远程 Agent 社会”很有用。

第四档：普通框架博客和 demo。
这些可以参考代码，但不能作为架构决策依据。你的目标是长期运行、可恢复、可审计、可自动化，而不是演示三四个 Agent 互相聊天。

四、总原则：你这套 Agent 系统要守住 12 条铁律
单主控原则：任何复杂任务必须有一个明确 Orchestrator 对最终结果负责。
读并行、写串行：调研、检索、代码阅读、审查可以并行；真正修改代码、发布内容、部署、写长期记忆尽量单线或审批后执行。Cognition 明确指出多 Agent 写作/写代码容易因为上下文和合并问题出错，较可行的是多 Agent 读、单 Agent 统一写。
Agent-as-tool 优先，handoff 次之，A2A 用于远程/异构 Agent：OpenAI Agents SDK 也把“manager 调 specialist as tool”和“handoff 转交控制权”区分开；前者适合主控综合，后者适合用户或任务控制权转移。
上下文比 Agent 数量更重要：Cognition 直接说长任务 Agent 工程的第一工作是 context engineering；Claude Code 的实践也是 JIT context、progressive disclosure、compaction、外部笔记和子 Agent 清洁上下文。
Artifact 引用优先于消息复制：子 Agent 不要把几万字原始材料塞回主窗口，而应返回结论、证据、artifact id、hash、路径、引用范围。Claude Code/Anthropic 也强调让子 Agent 在文件系统中产出 artifacts，再由主 Agent 按需读取，减少“电话游戏”。
计划账本 + 进度账本：Magentic-One 使用 task ledger 和 progress ledger 来维持计划、事实、待查项、进展和重规划；这比让 Agent 靠聊天记忆靠谱得多。
子 Agent 默认不能直接写长期记忆：只能提交 memory candidate，由 Memory Curator 和人类审批门处理。
每个委托都必须有 objective、output contract、tools、boundaries、budget、stop condition：Anthropic 报告中强调，给子 Agent 的委托要包含目标、输出格式、工具/来源指导和边界，否则会出现过度搜索、过量 spawn、方向漂移。
强模型管总，弱/便宜模型跑窄任务：Magentic-One 文档建议 Orchestrator 使用强推理模型；子 Agent 可以按任务换模型。
审批门硬编码，不交给模型自由判断：部署、外发、删文件、删记忆、花钱等必须是程序级 gate。OpenAI Agents SDK 也把 human review、guardrails、sandbox、state、tracing 作为 Agent 应用关键能力。
评估看最终状态，不只看过程是否漂亮：Anthropic 强调长任务 Agent 的 eval 要评估最终结果和 checkpoint，而不是只看对话中间看起来多聪明。
不要做无结构 swarm：Cognition 到 2026 的经验是，有用的是 map-reduce-and-manage、read-only subagents、review loop、single-writer，而不是一堆 Agent 自由讨论。

五、什么时候拆 Agent，什么时候不拆
1. 应该拆 Agent 的情况
拆分触发条件	说明	推荐形态
上下文边界不同	一个子任务只需要局部上下文，放进主窗口会污染主上下文	subagent / skill
工具边界不同	某个任务需要特定工具，例如浏览器、代码执行、数据库、MCP 工具	agent-as-tool
权限边界不同	某个任务有高风险权限，需要隔离或审批	restricted agent
专业能力不同	调研、代码、测试、审查、记忆整理需要不同提示词和模型	specialist agent
天然可并行	多来源调研、多方案比较、多模块代码阅读	map-reduce subagents
需要清洁视角	审查、找 bug、验证结论，需要不被主 Agent 思路污染	reviewer / verifier
任务超过单上下文窗口	需要分阶段、分文件、分模块处理	orchestrator-worker
需要远程/异构 Agent	不同机器、不同框架、不同组织的 Agent 协作	A2A

Anthropic 对多 Agent 的经验很明确：它适合“任务很复杂、搜索空间大、工具很多、上下文超过单窗口、工作可并行”的场景；不适合所有 Agent 都必须共享同一大段上下文、任务依赖很强、或并行收益低的场景。

2. 不应该拆 Agent 的情况
不拆条件	原因	更好做法
任务很短	拆 Agent 的通信成本比收益高	单 Agent + skill
输出必须高度统一	多 Agent 会导致风格、判断、口径不一致	单写者
所有步骤强依赖同一隐含决策链	子 Agent 拿不到完整隐含上下文，容易误解	单线程 + compaction
多个 Agent 会同时写同一文件/同一结论	合并冲突和责任不清	single-writer
只是提示词复杂，不是任务复杂	拆 Agent 不能解决提示词混乱	prompt refactor
没有评估标准	多 Agent 会放大不可控性	先建 eval
没有 artifact/trace/ledger	只靠聊天通信会丢信息	先建协议和日志

Cognition 的核心警告是：Agent 的动作本身包含大量隐含决策，只传“消息摘要”会丢失真正的上下文；这就是多 Agent 系统经常看起来热闹、实际结果更差的根源。

六、推荐的子 Agent 角色体系

你的系统可以分成三层：控制层、执行层、治理层。

1. 控制层
Agent	职责	是否写操作	是否写长期记忆
Meta Orchestrator	接收用户目标，决定任务优先级、拆分、审批、验收	可发起，但不直接越权	否，只提交候选
Planner	生成任务树、依赖关系、预算、stop condition	否	否
Router	判断用 skill、subagent、handoff、A2A、MCP	否	否
Context Engineer	组装 context pack、压缩、检索、去污染	否	可提交候选
Protocol Gateway	内部协议、A2A、MCP、Feishu/OpenClaw 等桥接	受限	否

2. 执行层
Agent	职责	推荐权限
Researcher	多来源调研、比较、证据收集	只读网络/文档
Code Reader	读代码、画结构、找入口、定位风险	只读 repo
Coder	实现变更	受限写入，必须 checkpoint
Tester	运行测试、生成复现、检查失败	可执行命令，受 sandbox
Reviewer	清洁上下文审查 bug、逻辑、边界	只读优先
Verifier / Citation Agent	验证事实、引用、来源质量	只读
Tool Executor	调 MCP 工具、API、数据库、命令行	最小权限
Ops Agent	部署、环境、CI、日志	高风险，必须审批

Anthropic 的多 Agent 系统里还专门使用 CitationAgent 来检查最终回答中的 claim 是否有来源归属；这对你做调研、客户报告、SEO/GEO、学习材料都很有价值。

3. 治理层
Agent	职责	关键限制
Memory Curator	从 trace 中提取记忆候选、去重、冲突检测	不直接写，需审批
Approval Agent	生成给人类看的审批摘要	不能自批
Risk Guard	检查外发、删除、部署、花钱、高风险批量操作	规则优先于模型
Eval Agent	对最终状态、引用、工具效率、完成度打分	清洁上下文
Recovery Agent	从 checkpoint 恢复、整理失败原因	只读/受限写

七、Agent 组群怎么编排
1. 默认模式：Orchestrator-worker

这是你的主架构。主 Agent 负责规划、分派、综合、验收；子 Agent 只负责局部任务。Anthropic 的研究系统也是 lead agent 先分析问题、制定策略、生成并行子 Agent，子 Agent 独立搜索/处理后把结果交回主 Agent 综合。

适合：调研、复杂问答、代码库理解、方案比较、客户报告。
风险：主 Agent 过度 spawn、子 Agent 搜索失控、返回格式不统一。
控制：预算、输出协议、stop condition、source policy、trace。

2. Agent-as-tool

主 Agent 把子 Agent 当成一个“高级工具”调用。OpenAI Agents SDK 文档也建议，当 manager 需要综合最终答案、外层流程稳定、任务边界清楚时，使用 agents-as-tools。

适合：

“请代码审查 Agent 检查这个 diff”
“请引用验证 Agent 验证这些 claim”
“请研究 Agent 查某个子问题”

不适合：

子 Agent 要持续和用户互动
子 Agent 要独立接管任务
子 Agent 需要和其他 Agent 直接协商

3. Handoff

handoff 是把控制权交给另一个 Agent。OpenAI 文档把 handoff 用于某个分支需要不同指令、工具或政策的情况；但也提醒不要过早拆 specialist，因为会增加提示词、trace 和审批面。

适合：

从“学习规划”交给“物理题讲解 Agent”
从“客户需求收集”交给“SEO 执行 Agent”
从“调研”交给“代码实现”

不适合：

主 Agent 仍必须强综合的任务
多个 Agent 同时对同一目标做最终判断

4. Read-only swarm

多个只读 Agent 并行读取不同材料、不同代码模块、不同网页、不同论文。Cognition 认为“读任务”比“写任务”更适合并行，因为它不会产生合并冲突；Claude Research 一类系统也常见多个 Agent 负责读，最后由主 Agent 写。

适合：

论文调研
竞品分析
多网站信息抽取
大代码库理解
多个技术方案比较

5. Single-writer code squad

代码任务建议这样组织：

Orchestrator
  ├─ Code Reader A：读架构
  ├─ Code Reader B：读相关模块
  ├─ Researcher：查官方文档
  ├─ Reviewer：审查计划
  └─ Coder：唯一写入者
        └─ Tester：跑测试
        └─ Reviewer：清洁上下文复审

原因很简单：多 Agent 同时写代码会产生冲突、重复实现和隐含决策不一致。Cognition 的可行经验是“多个 Agent 提供智能，但写入保持单线程”。

6. Agent team / A2A team

只有当 Agent 需要真正互相通信、跨框架、跨机器、跨组织协作时，才升级为 Agent team。Claude Code 文档也区分了 subagents 和 agent team：subagents 主要向主 Agent 汇报，而 agent team 是独立 Agent 之间直接协作；当 subagents 需要彼此沟通或上下文边界已经不够时，才转成 team。

A2A 适合这种 team，因为它定义了 Agent Card、Task、Message、Part、Artifact、contextId，并支持长任务、流式状态更新和 artifacts。

八、通信协议设计

你内部可以设计一个轻量协议，外部兼容 A2A，工具调用走 MCP。

1. 协议分层
用户 / Feishu / OpenClaw / CLI / Local JSONL stdio client
        ↓
Meta Orchestrator
        ↓
Internal Agent Mail / Event Bus
        ↓
Subagents / Teams
        ↓
MCP Tool Gateway / A2A Gateway / Codex / Claude Code / Local tools

MCP 和 A2A 不要混用角色：MCP 是 Agent 调工具、资源和工作流；A2A 是 Agent 发现、协商、共享任务和交换上下文。A2A 官方文档也明确把 MCP 定位为 agent-to-tool，把 A2A 定位为 agent-to-agent。

2. 内部消息 Envelope
{
  "schema_version": "agentmail.v1",
  "message_id": "msg_01J...",
  "thread_id": "thr_01J...",
  "context_id": "ctx_01J...",
  "task_id": "task_01J...",
  "parent_task_id": "task_parent_01J...",
  "timestamp": "2026-05-22T20:30:00+08:00",

  "from": {
    "agent_id": "orchestrator.main",
    "role": "orchestrator",
    "capability_version": "2026.05"
  },
  "to": {
    "type": "agent|group|capability|human",
    "target": "research.squad"
  },

  "intent": "delegate",
  "priority": "high",
  "project_pool": "study-mainline|client-borne|resomate|bio-api|content-system|ops-infra",

  "status": "created",
  "requires_human_approval": false,

  "budget": {
    "max_tokens": 80000,
    "max_tool_calls": 30,
    "max_wall_clock_seconds": 1800,
    "max_subagents": 4
  },

  "permissions": {
    "tools_allowed": ["web.search", "repo.read", "mcp.filesystem.read"],
    "tools_forbidden": ["email.send", "deploy", "filesystem.delete"],
    "write_policy": "none|draft_only|sandbox_only|approved_only",
    "network_policy": "allowlist|open|none",
    "secrets_policy": "no_secret_access"
  },

  "context_policy": {
    "history_mode": "none|summary|last_n|full",
    "history_window_messages": 12,
    "memory_scopes": ["user.profile", "project.client-borne", "team.research"],
    "include_trace_refs": true,
    "include_raw_logs": false,
    "artifact_reference_only": true,
    "retrieval_query": "Agent communication protocol design, A2A, MCP, subagent orchestration"
  },

  "task": {
    "objective": "调研 Agent 间通信协议，并给出可落地设计",
    "non_goals": [
      "不要写泛泛概念",
      "不要依赖低质量 SEO 文章"
    ],
    "success_criteria": [
      "至少覆盖 A2A、MCP、OpenAI Agents SDK、Anthropic、Cognition、AutoGen",
      "给出协议字段、状态机、失败模式"
    ],
    "output_contract": {
      "format": "json_markdown",
      "required_sections": [
        "findings",
        "evidence",
        "decisions",
        "risks",
        "artifact_refs",
        "memory_candidates",
        "confidence"
      ]
    }
  },

  "artifacts": [
    {
      "artifact_id": "art_01J...",
      "type": "file|diff|report|trace|dataset|screenshot",
      "uri": "artifact://research/a2a_notes.md",
      "hash": "sha256:...",
      "provenance": "generated_by:research.agent.01"
    }
  ],

  "assumptions": [],
  "open_questions": [],
  "risks": [],
  "approval": {
    "approval_required_for": [
      "external_send",
      "publish",
      "delete_file",
      "delete_memory",
      "write_long_term_memory",
      "deploy",
      "spend_money",
      "external_commitment",
      "high_risk_batch_change"
    ],
    "approval_status": "not_required|pending|approved|rejected"
  }
}

这个结构和 A2A 的 Task / Message / Artifact / contextId 思路兼容，也保留了你内部需要的权限、预算、上下文、记忆和审批字段。A2A 的 Task 本身就有 id、context_id、status、artifacts、history 等字段，并支持控制返回历史长度。

3. 状态机
created
  → accepted
  → working
  → blocked
  → input_required
  → completed
  → failed
  → cancelled

A2A 的 Task 也有生命周期状态，并且支持 interrupted/input-required 这类需要用户或调用方继续输入的状态；这对长期任务很重要。

4. 子 Agent 返回格式
{
  "task_id": "task_01J...",
  "agent_id": "research.agent.01",
  "status": "completed",
  "summary": "一句话结论",
  "findings": [
    {
      "claim": "多 Agent 适合可并行、搜索空间大的任务",
      "evidence": ["source_ref_1", "source_ref_2"],
      "confidence": 0.86
    }
  ],
  "decisions": [
    {
      "decision": "本任务建议使用 orchestrator-worker，而非自由 swarm",
      "reason": "需要主控综合，且避免写操作冲突"
    }
  ],
  "risks": [
    {
      "risk": "子 Agent 返回摘要丢失隐含决策",
      "mitigation": "保留 trace_ref 和 artifact_ref"
    }
  ],
  "open_questions": [],
  "artifact_refs": [
    "artifact://research/agent_protocol_notes.md"
  ],
  "memory_candidates": [
    {
      "scope": "project.agent-os",
      "statement": "用户偏好成功率、稳定性、可恢复性高于 token 成本",
      "evidence_ref": "conversation://...",
      "ttl": "long",
      "requires_human_approval": true
    }
  ],
  "next_recommended_actions": [
    "让 Reviewer 检查协议字段是否足够覆盖审批门"
  ]
}

九、上下文管理方案
1. 上下文分层

你不要把所有东西都塞进 prompt。建议分成九层：

L0 System Constitution
  永久规则：安全、审批门、单写者原则、不能越权

L1 User Profile
  你的偏好、长期目标、项目池、学习优先级、工具偏好

L2 Project Memory
  某个项目的目标、现状、架构、客户约束、历史决策

L3 Task Brief
  当前任务目标、边界、成功标准、输入输出

L4 Plan Ledger
  任务树、依赖、当前策略、已决定事项

L5 Progress Ledger
  已完成、卡住点、失败尝试、待查项、下一步

L6 Working Notes
  子 Agent 临时笔记、草稿、局部发现

L7 Artifacts
  文件、diff、报告、截图、日志、测试结果

L8 Raw Trace
  原始工具调用、完整对话、网页、命令输出

Claude Code 的 context engineering 实践强调 JIT context、progressive disclosure、CLAUDE.md/规则文件、按需 glob/grep、临近上下文极限时 compaction、以及把重要知识写到外部笔记/文件中。

2. 每个 Agent 启动时拿什么
Agent 类型	必须上下文	不该给
Orchestrator	L0-L5 + artifact index	全部 raw logs
Researcher	Task Brief + source policy + output contract	用户全部私人记忆
Code Reader	repo map + task brief + relevant files	无关项目记忆
Coder	具体 diff 目标 + constraints + tests	所有调研原文
Reviewer	目标 + diff/artifact + success criteria	Coder 的长篇自我解释
Memory Curator	trace summaries + memory candidates	无关 raw chatter
Approval Agent	操作摘要 + 风险 + rollback	多余技术细节

Claude Code 文档把 subagent 描述为有独立上下文、返回 1k-2k 左右摘要的隔离 worker；它适合并行探索，但不应该把主上下文完整复制过去。

3. 什么时候压缩，什么时候新开 Agent
情况	动作
主 Agent 接近上下文极限	compaction：保留决策、bug、约束、未完成项
一个子问题需要大量探索	新开 subagent
需要清洁审查视角	新开 reviewer
任务进入新阶段	写 phase summary 到 progress ledger
子 Agent 返回信息太多	只保留 summary + artifact refs
出现失败/偏航	checkpoint 回滚 + recovery summary

Anthropic/Claude Code 都强调长任务需要 checkpoint、durable execution、tracing、compaction 和外部状态，否则错误会在长链路中累积。

十、子 Agent 记忆机制
1. 记忆类型
记忆类型	内容	写入者	审批
Short-term working memory	当前任务临时事实、待办、局部假设	Agent 自己	不需要
Episodic memory	某次任务过程、失败、结果	Memory Curator	重要时审批
Semantic memory	稳定知识、项目架构、客户背景	Memory Curator	需要
Procedural memory	SOP、工具使用方法、调研流程	Memory Curator	需要
User preference memory	你的长期偏好、禁忌、优先级	Memory Curator	必须审批
Project memory	项目目标、接口、历史决策	Project Orchestrator	需要
Team memory	某组 Agent 的工作约定	Team lead	需要
Agent-private scratch	子 Agent 临时草稿	子 Agent	不持久化或短 TTL

你的系统里，子 Agent 默认不能直接写长期记忆。它只能发：

{
  "intent": "memory_write_request",
  "memory_candidate": {
    "scope": "project.agent-os",
    "type": "semantic|episodic|procedural|preference",
    "statement": "要写入的记忆",
    "evidence_refs": ["trace://...", "artifact://..."],
    "confidence": 0.82,
    "ttl": "short|medium|long",
    "conflicts_with": [],
    "requires_human_approval": true
  }
}

这样做是为了避免“Agent 把临时猜测写成永久事实”。MCP 安全分析也提醒，工具/协议本身不自动解决 task isolation、上下文塑形、权限和实现偏差问题；这些必须由应用层治理。

2. Memory Hydration 策略

每次启动 Agent 前，不是把全部记忆塞进去，而是生成一个 memory pack：

{
  "memory_pack_id": "mempack_01J...",
  "for_task_id": "task_01J...",
  "included": [
    {
      "scope": "user.profile",
      "reason": "影响项目优先级和审批门",
      "items": ["study-mainline always highest priority", "approval gates"]
    },
    {
      "scope": "project.agent-os",
      "reason": "影响架构设计",
      "items": ["single-writer principle", "Agent Mailer plan"]
    }
  ],
  "excluded": [
    {
      "scope": "client-borne",
      "reason": "当前任务无关，避免污染"
    }
  ]
}

这符合 Claude Code 的 progressive disclosure 思路：先给最小必需上下文，后续按需检索，而不是把整个历史都丢进去。

十一、提示词模板
1. Orchestrator Prompt
你是 Meta Orchestrator。你的责任不是亲自做完所有事，而是把任务拆成可控、可审计、可恢复的执行单元。

你必须遵守：
1. 学习主线 study-mainline 永远最高优先级。
2. 对外发送、发布、删除文件/记忆、写长期记忆、部署、花钱、对外承诺、高风险批量修改，必须人类审批。
3. 读任务可以并行，写任务默认单写者。
4. 不允许无结构 swarm。每个子 Agent 必须有 objective、boundaries、output_contract、budget、tools、stop_condition。
5. 子 Agent 返回 artifact refs，不要返回无节制长文。
6. 任何长期记忆只能提交 memory_candidate，不能直接写入。
7. 最终输出必须基于 evidence、artifacts、tests 或清楚标注的不确定性。

输入：
- user_request
- available_tools
- memory_pack
- project_state
- approval_policy

请输出：
{
  "task_understanding": "...",
  "should_split_agents": true/false,
  "split_reason": "...",
  "architecture_pattern": "single_agent|agent_as_tool|orchestrator_worker|handoff|a2a_team|single_writer_code_squad",
  "task_plan": [...],
  "subagent_delegations": [...],
  "approval_required": [...],
  "context_plan": {...},
  "memory_plan": {...},
  "evaluation_plan": {...},
  "stop_conditions": [...]
}

2. Delegation Prompt
你将作为受限子 Agent 执行一个明确子任务。你不对最终用户直接负责，只对委托任务负责。

目标：
{objective}

边界：
{boundaries}

禁止事项：
{non_goals}

可用工具：
{tools_allowed}

禁止工具：
{tools_forbidden}

上下文：
{context_pack}

成功标准：
{success_criteria}

输出必须严格包含：
1. summary
2. findings
3. evidence_refs
4. decisions
5. risks
6. open_questions
7. artifact_refs
8. memory_candidates
9. confidence
10. recommended_next_actions

不要写长期记忆。
不要做超出权限的外部操作。
发现需要审批的动作，只能生成 approval_request。

3. Reviewer Prompt
你是清洁上下文 Reviewer。你的目标不是赞同前一个 Agent，而是发现问题。

请检查：
1. 目标是否满足
2. 证据是否支持结论
3. 是否有未说明假设
4. 是否有上下文遗漏
5. 是否违反权限/审批门
6. 是否有写操作冲突
7. 是否有测试缺口
8. 是否存在更简单方案

输出：
{
  "verdict": "pass|needs_fix|fail",
  "critical_issues": [],
  "minor_issues": [],
  "missing_context": [],
  "approval_risks": [],
  "recommended_fixes": [],
  "confidence": 0.0
}

4. Memory Curator Prompt
你是 Memory Curator。你不能直接写入长期记忆，只能生成候选项并标注证据。

请从 trace 和 artifact 中提取：
1. 稳定用户偏好
2. 项目长期决策
3. 可复用流程
4. 明确失败经验
5. 需要删除或更新的旧记忆

不要记录：
1. 临时情绪
2. 未验证猜测
3. 一次性细节
4. 与长期行为无关的闲聊
5. 没有证据的总结

输出：
{
  "memory_candidates": [
    {
      "scope": "...",
      "type": "preference|project|procedural|episodic|semantic",
      "statement": "...",
      "evidence_refs": [],
      "confidence": 0.0,
      "ttl": "short|medium|long",
      "conflict_check": "...",
      "requires_human_approval": true
    }
  ],
  "rejected_items": [
    {
      "statement": "...",
      "reason": "too temporary|low confidence|no evidence|privacy risk"
    }
  ]
}

十二、安全、审批、评估
1. 审批门

你的系统里这些操作必须硬编码为 approval-required：

- 对外发送消息
- 发布内容
- 删除文件
- 删除记忆
- 写入长期记忆
- 部署
- 花钱
- 对外承诺
- 高风险批量修改
- 修改权限策略
- 访问敏感凭据
- 长时间后台任务升级权限

OpenAI Agents SDK 文档把 guardrails、human review、state、sandbox、MCP、tracing、evals 都列为真实 Agent 应用的关键能力；这说明“审批和可观测性”不是附加功能，而是 Agent 工程主干。

2. Trace 与 Eval

建议每个任务都记录：

{
  "task_id": "...",
  "plan_versions": [],
  "messages": [],
  "tool_calls": [],
  "artifacts": [],
  "checkpoints": [],
  "approvals": [],
  "memory_candidates": [],
  "final_state": {},
  "eval": {
    "completion": 0.0,
    "factual_accuracy": 0.0,
    "citation_accuracy": 0.0,
    "source_quality": 0.0,
    "tool_efficiency": 0.0,
    "policy_compliance": 0.0,
    "human_takeover_cost": 0.0
  }
}

Anthropic 对多 Agent 系统的评估强调 factual accuracy、citation accuracy、completeness、source quality、tool efficiency，并强调要看最终状态、checkpoint 和人类评估，而不是只看中间过程。

3. Sandbox 与权限

Magentic-One 文档也建议在运行多 Agent 时使用容器、虚拟环境、日志监控、人类介入、限制访问和数据保护。

你本地可以这样分权限：

read_only_agent:
  repo: read
  network: allowlist
  shell: none
  memory_write: no

code_agent:
  repo: write_sandbox
  shell: test_only
  network: none/allowlist
  memory_write: candidate_only

ops_agent:
  deploy: approval_required
  secrets: approval_required
  shell: restricted
  network: allowlist

external_comm_agent:
  draft: yes
  send: approval_required

十三、分阶段实现路线图
v0：先做单主控，不急着多 Agent

目标：先把 Harness 搭起来。

- Meta Orchestrator
- Task Ledger
- Progress Ledger
- Artifact Store
- MessageLog
- Approval Gates
- Memory Candidate Queue
- MCP Tool Gateway
- Basic eval

这一阶段不要追求“多 Agent 炫技”。先做到：任务能记录、能恢复、能审批、能追踪、能人工接管。

v1：加 read-only subagents

目标：并行调研、并行读代码、并行审查。

- Research Agent
- Code Reader Agent
- Reviewer Agent
- Citation Verifier
- Context Pack Builder
- 子 Agent 返回结构化 JSON + artifact refs

这阶段最安全、收益最大，因为读任务不容易造成破坏。

v2：加 single-writer code squad

目标：自动完成代码任务，但控制写操作。

- Planner 拆任务
- Code Readers 并行读
- Coder 唯一写入
- Tester 跑测试
- Reviewer 清洁上下文复查
- Human approval for risky changes
- checkpoint / rollback

OpenAI Codex 的 subagents 也强调它们适合高度并行任务，但会消耗更多 token，并且子 Agent 继承 sandbox policy 与 approval policy；这和你的“强审批、可回滚”设计是兼容的。

v3：接 A2A / Agent Mailer / 远程 Agent team

目标：让不同机器、不同框架、不同服务中的 Agent 能通信。

- Agent Card Registry
- Internal Agent Mail
- A2A Gateway
- MCP Gateway
- Feishu/OpenClaw UI
- Agent capability discovery
- Async task subscription
- Push notification
- Long-running jobs

A2A 的 Agent Card 机制可以描述 Agent 名称、provider、endpoint、capabilities、auth、skills、input/output modes 和 examples；这正好可以作为你系统里的 Agent 注册表基础。

十四、最推荐默认架构

你的默认架构可以定成：

Vimalinx Agent Harness
│
├─ Meta Orchestrator
│   ├─ Task Router
│   ├─ Planner
│   ├─ Context Engineer
│   ├─ Approval Controller
│   └─ Eval Controller
│
├─ Shared State
│   ├─ Task Ledger
│   ├─ Progress Ledger
│   ├─ MessageLog
│   ├─ Artifact Store
│   ├─ Memory Store
│   └─ Checkpoint Store
│
├─ Agent Runtime
│   ├─ Research Squad
│   ├─ Code Reading Squad
│   ├─ Single Writer Coder
│   ├─ Tester
│   ├─ Reviewer
│   ├─ Citation Verifier
│   ├─ Memory Curator
│   └─ Ops Agent
│
├─ Protocol Layer
│   ├─ Internal Agent Mail
│   ├─ A2A Gateway
│   ├─ MCP Gateway
│   └─ Codex / Claude Code / Deer Flow / OpenClaw bridge
│
└─ Human Interface
    ├─ Chat
    ├─ Feishu
    ├─ CLI
    ├─ Dashboard
    └─ Approval Inbox

一句话概括：

主 Agent 像总指挥，子 Agent 像受限专家，Task Ledger 像作战地图，Artifact Store 像证据库，Memory Curator 像档案员，Approval Gate 像保险丝，A2A/MCP 像外部协议接口。

真正能跑起来的关键，不是“让 Agent 说更多话”，而是让每次通信都带上：任务 ID、上下文 ID、目标、边界、权限、证据、artifact、状态、风险、审批要求和下一步。这样多 Agent 才不会变成一堆幻觉互相传话，而会变成一套可控的工程系统。
