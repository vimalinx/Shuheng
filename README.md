<div align="center">

<h1>枢衡 Shuheng</h1>

<p><strong>面向本地多 Agent 的中心执行、调度、记忆与审批层。</strong></p>

<p>
把会话管理、多 Agent 调度、任务看板、记忆治理和自动化执行入口收进一个更稳定、更清爽、更适合长期工作的 curses TUI。
</p>

<p>
  <a href="README.md"><strong>简体中文</strong></a>
  ·
  <a href="README.en.md">English</a>
</p>

<p>
  <a href="https://www.python.org/"><img alt="Python >= 3.10" src="https://img.shields.io/badge/Python-%3E%3D3.10-111827?style=for-the-badge&logo=python&logoColor=white"></a>
  <a href="#项目定位"><img alt="Curses TUI" src="https://img.shields.io/badge/Interface-curses-0f172a?style=for-the-badge"></a>
  <a href="#架构方向"><img alt="Agent Harness" src="https://img.shields.io/badge/Agent_Harness-governed-1f2937?style=for-the-badge"></a>
  <a href="https://linux.do/"><img alt="LINUX DO" src="https://img.shields.io/badge/Community-LINUX%20DO-111827?style=for-the-badge"></a>
</p>

<p>
  <a href="#快速开始">快速开始</a>
  ·
  <a href="#能力总览">能力总览</a>
  ·
  <a href="#命令入口">命令入口</a>
  ·
  <a href="#架构方向">架构方向</a>
  ·
  <a href="#community">Community</a>
</p>

</div>

---

## 项目定位

`枢衡 Shuheng` 是面向本地多 Agent 的终端控制面。它不重写底层 agent runtime，而是把用户每天真正接触的执行、调度、审批、记忆和会话工作台单独维护起来。

当前发布定位是 **experimental local alpha**：本地 curses TUI、会话、任务账本、artifact、审批、Secret Vault 和 OMP runtime 输出/控制是主要稳定面。外部 AI 通过本地 JSONL stdio 的 `shuheng-agent-gateway` 接入。A2A/MCP-shaped 数据是 Agent Mail 和资源注册表中的本地 record 形状。

你可以把它理解成：

```text
会话管理器 + 多 Agent 调度台 + 任务看板 + 记忆/审批治理层 + 自动化控制面板
```

它先把 OMP runtime 在终端中做得更可控、更耐用、更适合长任务，并为未来的 Codex、Claude Code 等 provider adapter 保留统一控制面；会话历史、harness 账本、子 agent、Secret Vault 和 OMP 隔离运行时默认都由 Shuheng 自己维护在 `~/.shuheng`。

> Runtimes execute. Shuheng governs the control surface.

## 为什么需要它

| 痛点 | 枢衡 Shuheng 的处理方式 |
| --- | --- |
| 主项目 TUI 改动容易和上游冲突 | TUI 外置维护，日常直接运行 `shuheng` |
| 长会话容易混乱 | 历史恢复、置顶、分类、过滤、归档和回收站 |
| 多 Agent 容易失控 | 主控 orchestrator 统一拆解、调度、汇总和验收 |
| 子 Agent 身份不稳定 | 支持临时/持久子 Agent、profile、role、模型和记忆候选 |
| 任务进展难追踪 | 任务账本、独立 progress ledger、步骤计划、agent mail、artifact、启发式 eval 和 trace |
| Secret 内容不应混入普通历史 | 本地加密 Secret Vault，锁定后清除明文状态 |

当前实现基于 Python `curses`，刻意选择低依赖、可控、稳定的终端方案，避免复杂 UI 框架在部分终端、Wayland 或鼠标模式组合下引入输入污染。

## 能力总览

### 一句话

`枢衡 Shuheng` 把自然语言指挥、会话整理、任务拆解、多 Agent 协作、记忆治理和自动化执行合成一个终端控制面。

### 核心能力矩阵

| 能力层 | 说明 | 你可以这样说 |
| --- | --- | --- |
| 会话管理 | 置顶、分类、过滤、折叠、归档、重命名、删除 | `把这个会话归类到“项目开发”` |
| 任务计划 | 创建多步骤计划，跟踪步骤完成状态 | `给这个项目建一个五步计划，然后按步骤推进` |
| 子 Agent 调度 | 创建、复用、停止、删除临时或持久子 Agent | `开一个临时研究员，帮我查这个库的最佳实践` |
| 主控编排 | 由主 agent 统一拆解任务、分派、等待和汇总 | `等子 Agent 返回后再汇总，不要现在结束` |
| 自动化入口 | 文件、代码、浏览器、日志、记忆、系统操作 | `让审查员检查刚才写的代码` |
| 治理视图 | 任务账本、审批、artifact、recovery、启发式 eval、trace | `看看后台那个任务有结果了吗` |

### 会话工作区

| 能力 | 用途 |
| --- | --- |
| 置顶 / 取消置顶 | 把重要会话固定在上方 |
| 分类 | 用“开发”“研究”“日常”“待处理”等标签管理会话 |
| 过滤 | 只显示某一类会话 |
| 折叠 / 展开 | 控制侧边栏密度 |
| 归档 / 取消归档 | 收起暂时不用但仍需保留的会话 |
| 重命名 | 给任务留下可读标题 |
| 删除到回收站 | 清理无用会话 |

### 任务看板

复杂任务可以先拆成步骤，再逐步推进；子 Agent 可以挂靠到具体步骤执行。

```text
任务：构建一个爬虫系统

1. 分析目标网站
2. 设计数据结构
3. 编写爬虫代码
4. 测试反爬策略
5. 输出文档与运行说明
```

可以做到：

- 创建多步骤计划。
- 标记步骤完成。
- 跟踪当前进行到哪一步。
- 让子 Agent 绑定到具体步骤。
- 让主控 Agent 保留整体调度权。

### 子 Agent 控制台

| 角色 | 适合承担的工作 |
| --- | --- |
| Researcher | 搜集资料、分析方案、输出调研结论 |
| Coder | 编写代码、修复 bug、实现功能 |
| Reviewer | 审核代码、发现问题、做质量检查 |
| Verifier | 复核结果、运行测试、确认事实 |
| Memory curator | 整理长期有效的信息候选 |
| Ops agent | 处理部署、环境、日志和命令执行类任务 |

### 临时与持久子 Agent

| 类型 | 适合场景 | 行为 |
| --- | --- | --- |
| 临时子 Agent | 一次性任务、短调研、实验分析 | 不长期保存身份，用完即可 |
| 持久子 Agent | 长期项目、固定角色、专属助手 | 有稳定身份，可保存 profile、职责、记忆候选和默认模型 |

示例：

```text
开一个临时研究员，帮我查这个库的最佳实践。
创建一个长期代码审查员，以后专门 review 我的 Python 项目。
叫之前那个研究员继续分析。
让审查员检查刚才写的代码。
```

### 自然语言控制

你可以不用记命令，直接说目标：

```text
把当前会话置顶。
把这个会话归类到“项目开发”。
隐藏归档会话。
把这个会话重命名为“FastAPI 后端重构”。
```

```text
给这个项目建一个五步计划，然后按步骤推进。
把第一步交给研究员，第二步交给程序员。
等子 Agent 返回后再汇总，不要现在结束。
```

```text
帮我管理这个会话。
帮我创建一个子 Agent。
帮我把任务拆成计划。
帮我让几个 Agent 分工完成。
帮我整理历史会话。
```

## 快速开始

### 1. 安装

完整新机器安装、平台支持和状态迁移说明见 [`docs/install.md`](docs/install.md)。

```bash
curl -fsSL https://raw.githubusercontent.com/vimalinx/Shuheng/main/scripts/install.sh | sh
```

安装器会在用户目录创建隔离 venv，安装 `shuheng`/`shuheng-check` 等入口，安装或验证固定版本的 OMP，默认安装共享的 `shuheng-agent-gateway` skill，并运行 `shuheng-check`。OMP 需要 Bun 1.3.14+；缺少主 runtime 时安装器会明确失败，不会输出假成功。支持 Linux、WSL2 和 best-effort macOS；native Windows 请使用 WSL2。

开发者源码安装：

```bash
python -m pip install -e .
```

也可以不安装，直接从源码运行：

```bash
PYTHONPATH=src python -m shuheng
```

`shuheng` 是保留的 Python 模块名；正式命令入口使用 `shuheng`。

先确认公开命令入口可用：

```bash
shuheng --help
shuheng --version
```

`shuheng --help`、启动 TUI、本地协议记录和 `shuheng-check` 都走 Shuheng 自己的本地控制面。默认 runtime core 是 OhMyPi / OMP。

### 2. 检查接入状态

```bash
shuheng-check
```

健康输出包含：

```text
Core runtime: OhMyPi / OMP
OMP runtime check: OK
Status: OK
Launch without legacy patches: shuheng
```

### 3. 启动

```bash
shuheng
```

推荐更新方式是重新运行已检查过的安装器：

```bash
sh /tmp/shuheng-install.sh --version v0.2.0-alpha.1
shuheng --version
shuheng-check
```

## 命令入口

进入 TUI 后输入 `/help` 可以查看完整命令。

### 会话

```text
/continue [n]        列出或恢复历史会话
/sessions            列出历史会话
/new                 新建空会话
/temp                新建不写入历史日志、会话记忆或记忆候选的临时会话
/clear               清空当前屏幕
/status              显示当前状态
/stop                中止当前任务
/resume              让 agent 总结最近会话
/fold                切换过程自动折叠
/md                  切换轻量 Markdown 渲染
/rename <name>       手动命名当前会话
/pin [n]             置顶当前或第 n 个会话
/unpin [n]           取消置顶当前或第 n 个会话
/category [n] <name> 设置当前或第 n 个会话分类
/filter [category]   按分类筛选会话
/archive [n]         归档当前或第 n 个会话
/delete [n]          删除当前或第 n 个会话到回收站
```

### 模型

```text
/model               管理模型配置、切换当前对话模型、提取模型、验活、设置默认
```

模型配置保存在 `~/.shuheng/config/mykey.py`，目录权限为 `0700`，配置和备份为 `0600`。OMP 默认采用 `standard + write`；只有明确设置 `SHUHENG_OMP_PERMISSION_PROFILE=full` 与 `SHUHENG_OMP_APPROVAL_MODE=yolo` 才会进入无提示的全权限模式。单独设置 `yolo` 会被程序降级为 `write`；`full + write/always-ask` 仍保留程序级高风险动作门。额外继承的环境变量必须逐名写入 `SHUHENG_OMP_INHERIT_ENV`。

### 子 Agent

```text
/agents                         列出持久子 agent
/agent list                     列出子 agent
/agent new [role:]<name>        新建子 agent
/agent ask <agent> <prompt>     让子 agent 执行任务
/agent role <agent> <role>      设置子 agent 角色
/agent model <agent> [model]    设置持久子 agent 默认模型
/agent settings <agent>         打开持久子 agent 设置
/agent memory <agent>           查看子 agent 记忆
/agent remember <agent> <text>  追加子 agent 记忆
/agent stop <agent>             停止子 agent
/agent delete <agent>           移除子 agent
```

### Agent Projects（Pi-native worker）

```text
/agent-projects                               打开内嵌单文件 Agent Project 工作台
/agent-project list                           列出本地项目
/agent-project create <id> [name]             创建项目
/agent-project fork <source-id> <new-id>      Fork 项目
/agent-project build <id>                     校验并生成内容寻址 Build
/agent-project run <id> <objective>           运行无自定义权限请求的 Build
/agent-project run <id> --grant-declared ...  显式授权该次冻结 Build 声明的 capabilities 与本地 Tools
```

OMP 始终是主 Agent 和默认 Provider；Pi-native 只运行受账本、审批和
single-writer 入口管理的任务型 worker。获准的项目 Tool 是可信本机
Node 代码，当前 MVP 尚无 OS syscall 沙箱，不能靠写锁阻止它直接产生
主机副作用，只应运行你信任的源码。Pi worker 不支持 Secret Vault
执行或无账本直接聊天；冻结 Build bytes 也不会持久归档，源文件变化后
只能按 digest 审计，不能从 Shuheng 状态单独重放旧 Build。所有
Project 任务都须经 `/agent-project run` 确认当前 Build；`/agent ask`、
scheduler 和 recovery retry 不会从可变源码静默启动。

Pi-native 是可选实验 Provider。首次使用需有 Node.js 22.19+ 和 npm，
通过已安装命令按 lockfile 安装固定 SDK；否则 `/runtimes` 会显示
`missing_package`，OMP 仍可正常使用：

```bash
shuheng runtime setup-pi
shuheng runtime check --require-pi
```

### 治理与可观测性

```text
/tasks               查看共享任务账本
/bus                 查看 agent mail
/approvals           查看待审批事项
/approve <id>        批准待审批事项
/reject <id>         拒绝待审批事项
/artifacts           打开 artifact store
/recover             查看或处理可恢复任务
/evals               查看启发式任务评估和 trace
/baseline            查看架构基线对比报告和证据等级
/memory              打开记忆系统可视化检查
/mem                 /memory 的别名
```

### Secret Vault

```text
/Secret                         进入本地加密 Secret Vault
/Secret status                  查看 Secret Vault 状态
/Secret sessions                查看 Secret 会话
/Secret open-session <n>        打开 Secret 会话
/lock                           锁定 Secret Vault 并清除明文状态
/toSecret [delete|archive] [n]  单向迁移普通会话到 Secret
```

## 项目结构

```text
.
├── README.md / README.en.md          中英文说明
├── THIRD_PARTY_NOTICES.md            外部 runtime 与依赖许可边界
├── pyproject.toml                    包元数据、依赖、命令入口与 ruff 配置
├── docs/
│   ├── agent-harness-architecture.md     长期 agent harness 架构基线（北极星）
│   ├── development/                      公开贡献者工程契约
│   ├── app-py-decomposition-plan.md      `app.py` 渐进拆分计划（Phase 0–7）
│   ├── runtime-provider-control-plane.md runtime provider 控制面设计
│   ├── public-alpha-readiness.md         发布姿态、已知缺口、fresh clone 预期
│   └── install.md                        跨平台安装与平台支持说明
├── scripts/
│   ├── check_policy_gates.py         harness policy gate 函数级 smoke（CI 门禁）
│   ├── check_release_hygiene.py      发布卫生检查（密钥 / 私有路径 / 口径）
│   ├── runtime_smoke.py              runtime provider 运行时 smoke
│   ├── dogfood_stdio_gateway.py      本地 stdio agent gateway 端到端 dogfood
│   ├── wheel_smoke.py                wheel/sdist 完整性与公开/私有边界检查
│   ├── release_scan_rules.py         发布内容扫描规则
│   └── install.sh                    `curl|sh` 跨平台安装器（Linux / WSL2 / macOS）
├── src/shuheng/
│   # ── 入口与装配 ──
│   ├── __main__.py                   `python -m shuheng`
│   ├── __init__.py                   包定义、`__version__`
│   ├── cli.py                        轻量公开 CLI（`--help` 不导入重型 runtime）
│   ├── app.py                        curses TUI 主装配 + 进程循环（仍在精简的 composition 模块）
│   # ── 纯叶子：类型 / 文本 / 路径 ──
│   ├── ui_types.py                   UI 状态与共享数据类
│   ├── text_utils.py                 终端 cell / 文本纯函数
│   ├── path_utils.py                 文件系统路径安全纯函数
│   ├── agent_projects.py             Agent Project/Blueprint/Build/Run Manifest 纯契约
│   ├── agent_editor.py               单文件编辑状态、原子保存与外部冲突检测
│   # ── 存储适配 ──
│   ├── ledger_store.py               JSONL 追加/读/缓存（fcntl + 线程锁）
│   ├── history_store.py              普通会话历史与 transcript 存取
│   ├── subagent_store.py             子 agent 身份 / profile / 记忆 / sidebar key
│   ├── secret_vault.py               Secret Vault 加解密（xchacha20poly1305）与加密存储
│   ├── compat_legacy.py              历史会话 / 记忆遗留解析（隔离区）
│   # ── 治理层 ──
│   ├── governance.py                 task / approval / artifact / trace / eval 记录语义与单写者锁
│   ├── control_protocol.py           agent task 控制协议（v2）解析
│   ├── local_protocol_registry.py    本地协议 record 形状（A2A/MCP-shaped 元数据）
│   ├── context_packs.py              上下文分层与记忆 hydration
│   ├── release_readiness.py          发布成熟度、baseline 证据等级、启发式 eval
│   # ── 运行时 ──
│   ├── runtime.py                    runtime provider 抽象与注册表
│   ├── runtime_dispatch.py           provider 中立的派发与流归一
│   ├── runtime_evidence.py           runtime / e2e 证据收集
│   ├── runtime_setup.py              OMP/Pi 安装、RPC 就绪、版本与健康检查
│   ├── ohmypi_provider.py            OhMyPi/OMP provider（subprocess + JSONL stdio RPC）
│   ├── pi_native_provider.py         Pi-native 冻结 Build worker provider
│   ├── subagent_task_dispatch.py     注入式受治理子 Agent 任务派发
│   ├── agent_project_workspace.py    Agent Project TUI/命令装配层
│   ├── integration.py                `shuheng-check` doctor 与本地集成工具
│   ├── frontend_history_compat.py    遗留 frontend 历史 / 命名 fallback
│   # ── 自动化与扩展 ──
│   ├── scheduler.py                  定时任务注册与触发（cron / interval / at）
│   ├── workflows.py                  声明式 workflow 定义
│   ├── plugins.py                    声明式 plugin 注册
│   ├── skill_installer.py            安装共享 skill（如 shuheng-agent-gateway）
│   # ── 协议桥接 ──
│   ├── agent_bridge.py               本地 agent bridge / stdio gateway API（发现 agent、投递任务、提交治理提案）
│   # ── UI 渲染与输入 ──
│   ├── rendering.py                  curses-free 渲染变换与消息块解析
│   ├── dashboard.py                  仪表盘 schema 与归一
│   ├── input_controller.py           终端输入 / 光标 / 鼠标 / 粘贴
│   ├── commands.py                   命令补全与命令处理
│   # ── 辅助 ──
│   ├── baseline.py                   架构 baseline 报告项
│   └── history_titles.py             会话标题 / 描述（process-summary 安全）
└── tests/                            pytest 套件，覆盖纯函数、加解密、解析器、各 store、rendering、governance、安装与发布等
```

依赖方向（自下而上，来自 [`docs/app-py-decomposition-plan.md`](docs/app-py-decomposition-plan.md)）：

```text
路径 / 类型常量 → 纯文本与 cell 工具 → 存储适配与 store → 治理域服务
  → 渲染器 / 命令处理 / 本地协议 record → app.py 装配门面与进程循环
```

> `src/shuheng/app.py` 仍是约 28k 行的 composition 模块，是当前最大的可维护性风险，正按上述计划分阶段精简；新抽取的模块不得反向 import `shuheng.app`。

> 个别承载已退役品牌的内部遗留胶水模块（仅本地兼容用途、非公开控制面）按退役策略不在公开结构图中具名，见仓库源码。

## 架构方向

`枢衡 Shuheng` 正在从聊天入口演进为可治理的本地 agent harness。

架构基线：

```text
docs/agent-harness-architecture.md
```

| 原则 | 方向 |
| --- | --- |
| 强主控 Orchestrator | 一个主控对最终结果负责 |
| 受限子 Agent | 子 Agent 按 role、permission、budget、stop condition 执行 |
| 单写者原则 | 读任务可并行，写操作保持受控 |
| 可审计 | task ledger、progress ledger、mail、artifact、approval、eval、trace 可追踪 |
| 人类审批门 | 长期记忆、Secret、删除、部署和外部副作用需要审批 |
| 协议记录 | A2A/MCP-shaped 对象作为 Agent Mail 和资源注册表中的本地 registry/record 形状存在 |
| 本地 gateway | `shuheng-agent-gateway serve --stdio` 提供持久的本地 JSONL stdin/stdout 通道 |

如果改动触及 TUI、子 Agent、审批、记忆、artifact、recovery、eval/trace、A2A/MCP 或 orchestration 行为，完成前都应对照架构基线检查。

### Release Readiness

Shuheng 的发布成熟度元数据由 `src/shuheng/release_readiness.py` 维护。当前默认结论：

- 稳定本地面：curses TUI、会话工作区、任务账本、artifact、审批、Secret Vault、OMP runtime 输出/控制。
- 实验面：Pi-native Agent Projects、baseline report、runtime/evidence smoke、heuristic eval、scheduler runtime dispatch、本地 protocol-shaped registry records、stdio agent gateway。
- 已知缺口：`app.py` 仍是大型 composition module；eval 不证明事实/引用正确；A2A/MCP-shaped records 不是可访问协议 endpoint；Pi-native 自定义 Tool 是可信本机代码而非 OS 沙箱。

### 本地 Agent Gateway

```bash
shuheng install-agent-gateway-skill
shuheng-agent-gateway register
shuheng-agent-gateway agent-directory
shuheng-agent-gateway serve --stdio
shuheng-agent-gateway message-send --target <agent-id> --message "要交给这个 agent 的任务"
shuheng-agent-gateway task-status --task-id <task-id>
```

`shuheng install-agent-gateway-skill` 会把 Shuheng 自带的 `shuheng-agent-gateway` skill 安装/更新到共享 skill 根目录，默认是 `~/.agents/skills`。这样其他本地 agent 可以通过 `$shuheng-agent-gateway` 学会使用本地 stdio gateway；该 skill 只说明 agent 发现、投递消息和查询任务状态，不暴露 Shuheng 内部上下文、账本、Secret 或权限矩阵。

`serve --stdio` 是给外部 AI/supervisor 持有的持久本地进程。它通过 stdin/stdout 传递 JSONL，公开动作固定为 `agent_directory`、`message_send`、`task_status` 和 `gateway_status`；内部 metadata、文件路径和其他 bridge 动作不会跨过该进程边界。`message-send` 会走 Shuheng Orchestrator 的子 agent task 路径和审批门。

公开客户端只应启动 `shuheng-agent-gateway`。`shuheng-agent-bridge` 和 `python -m shuheng.agent_bridge` 是供本地 Provider/插件使用的受信内部集成面，不是 public gateway 的别名，也不应交给不受信客户端持有。

本地端到端验证：

```bash
python scripts/dogfood_stdio_gateway.py
```

该脚本会在隔离的 `SHUHENG_HOME` 中启动真实 `serve --stdio` 子进程，验证 `agent_directory`、`message_send`、`task_status`、task ledger、approval ledger 和 trace ledger。

## 开发

源码运行：

```bash
PYTHONPATH=src python -m shuheng
```

集成检查：

```bash
shuheng-check
```

提交前建议：

```bash
python -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/dogfood_stdio_gateway.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_release_hygiene.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_policy_gates.py
PYTHONDONTWRITEBYTECODE=1 python scripts/dogfood_stdio_gateway.py
PYTHONDONTWRITEBYTECODE=1 python scripts/runtime_smoke.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
python -m compileall -q src scripts
npm ci --ignore-scripts --prefix integrations/pi-native-sidecar
node --check integrations/pi-native-sidecar/sidecar.mjs
python -m build --sdist --wheel --outdir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist
git diff --check
```

`scripts/wheel_smoke.py --dist-dir` 默认会分别安装最新 wheel 和 sdist，检查 wheel metadata/私有文件边界、wheel RECORD hash/size 完整性、sdist archive 的公开/私有文件边界、sdist metadata/entry points 和 SOURCES 清单一致性，并扫描两个 artifact 内容里的密钥形态和本地绝对路径，再运行公开入口点检查；`--no-deps` 和 `--wheel-only` 仅用于本地调试，不属于发布门禁。

发布前确认不要把本地绝对路径、密钥、模型配置、普通会话日志或 Secret Vault 内容写进仓库。`scripts/check_release_hygiene.py` 会检查治理文件、包元数据、私有路径、真实密钥形态和公开 alpha 口径。

### 开源发布边界

- License: MIT，见 `LICENSE`。
- 安全报告与边界：见 `SECURITY.md`。本地 agent gateway 使用 JSONL stdio；涉及外部发送、部署、删除、Secret、长期记忆的操作仍走本地审批门。
- 贡献流程：见 `CONTRIBUTING.md`；行为准则见 `CODE_OF_CONDUCT.md`。
- 发布记录：见 `CHANGELOG.md`。
- 第三方依赖边界：见 `THIRD_PARTY_NOTICES.md`。
- 贡献者工程契约：见 `docs/development/`。
- CI: `.github/workflows/ci.yml` 运行 release hygiene、policy gate、runtime smoke、pytest、compile、package build、wheel smoke 和 `git diff --check`。
- Public alpha readiness：见 `docs/public-alpha-readiness.md`，其中记录发布姿态、源码边界、已知缺口和 fresh clone 期望。

## Community

This project is promoted in the [LINUX DO](https://linux.do/) open-source community. Thanks to the community for discussion, feedback, and suggestions.
