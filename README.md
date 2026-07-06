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

当前发布定位是 **experimental local alpha**：本地 curses TUI、会话、任务账本、artifact、审批、Secret Vault 和 OMP runtime 输出/控制是主要稳定面。Shuheng 不再内置 Web Console、HTTP gateway、mobile 或 remote endpoint；A2A/MCP-shaped 数据只作为本地 registry/record 形状保留，不代表可访问的协议服务或完整认证。

你可以把它理解成：

```text
会话管理器 + 多 Agent 调度台 + 任务看板 + 记忆/审批治理层 + 自动化控制面板
```

它负责让 OMP、Codex、Claude Code 等本地 agent runtime 在终端中更可控、更耐用、更适合长任务；会话历史、harness 账本、子 agent、Secret Vault 和 OMP 隔离运行时默认都由 Shuheng 自己维护在 `~/.shuheng`。

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
```

`shuheng --help`、启动 TUI、gateway 和 `shuheng-check` 都走 Shuheng 自己的本地控制面。默认 runtime core 是 OhMyPi / OMP。

### 2. 检查接入状态

```bash
shuheng-check
```

健康输出包含：

```text
Core runtime: OhMyPi / OMP
Status: OK
Launch without legacy patches: shuheng
```

### 3. 启动

```bash
shuheng
```

推荐更新方式：

```bash
cd /path/to/Shuheng
shuheng
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
├── README.md
├── README.en.md
├── pyproject.toml
├── docs/
│   └── agent-harness-architecture.md
├── scripts/
│   └── check_policy_gates.py
├── src/
│   └── shuheng/
│       ├── __main__.py
│       ├── __init__.py
│       ├── cli.py
│       ├── app.py
│       ├── integration.py
│       ├── runtime.py
│       ├── scheduler.py
│       ├── release_readiness.py
│       ├── control_protocol.py
│       ├── frontend_history_compat.py
│       ├── agent_bridge.py
│       ├── ohmypi_provider.py
│       └── compat_legacy.py
└── tests/
    ├── conftest.py
    ├── test_cell_utils.py
    ├── test_jsonl.py
    ├── test_path_safety.py
    ├── test_scheduler_parsing.py
    ├── test_secret_crypto.py
    └── test_time_path_helpers.py
```

| 文件 | 作用 |
| --- | --- |
| `src/shuheng/cli.py` | 轻量公开 CLI 入口；`--help` 不导入重型 TUI/runtime |
| `src/shuheng/app.py` | curses TUI 主实现、会话/记忆/审批/Secret Vault 核心逻辑 |
| `src/shuheng/integration.py` | Shuheng doctor 检查和本地集成工具 |
| `src/shuheng/runtime.py` | runtime provider 抽象层与注册表 |
| `src/shuheng/scheduler.py` | 定时任务注册表与触发判定(cron / interval / at) |
| `src/shuheng/release_readiness.py` | 发布成熟度、baseline 证据等级、gateway 安全姿态和启发式 eval 纯函数 |
| `src/shuheng/control_protocol.py` | agent task 控制协议(v2)解析 |
| `src/shuheng/frontend_history_compat.py` | Shuheng 本地历史/命名 fallback |
| `src/shuheng/agent_bridge.py` | 本地 agent bridge API,供 OMP 等客户端读写 Shuheng 状态 |
| `src/shuheng/ohmypi_provider.py` | OMP runtime adapter(进程、host tool、usage 同步) |
| `src/shuheng/compat_legacy.py` | 历史会话/记忆的兼容解析 |
| `tests/` | pytest 测试套件,覆盖纯函数与加解密、解析器 |
| `scripts/check_policy_gates.py` | harness policy gate 的函数级 smoke 检查 |
| `docs/agent-harness-architecture.md` | 长期 agent harness 架构基线 |
| `pyproject.toml` | Python 包配置、依赖与命令入口 |

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
| 协议记录 | A2A/MCP-shaped 对象只作为本地 registry/record 形状存在；没有内建 HTTP endpoint 或协议认证 |

如果改动触及 TUI、子 Agent、审批、记忆、artifact、recovery、eval/trace、A2A/MCP 或 orchestration 行为，完成前都应对照架构基线检查。

### Release Readiness

Shuheng 的发布成熟度元数据由 `src/shuheng/release_readiness.py` 维护。当前默认结论：

- 稳定本地面：curses TUI、会话工作区、任务账本、artifact、审批、Secret Vault、OMP runtime 输出/控制。
- 实验面：baseline report、runtime/evidence smoke、heuristic eval、scheduler runtime dispatch、本地 protocol-shaped registry records。
- 已知缺口：`app.py` 仍是大型 composition module；eval 不证明事实/引用正确；A2A/MCP-shaped records 不是可访问协议 endpoint；Web Console、HTTP gateway、mobile、remote endpoint 不是当前产品面。

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
python -m ruff check src tests scripts/check_policy_gates.py scripts/check_release_hygiene.py scripts/release_scan_rules.py scripts/runtime_smoke.py scripts/wheel_smoke.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_release_hygiene.py
PYTHONDONTWRITEBYTECODE=1 python scripts/check_policy_gates.py
PYTHONDONTWRITEBYTECODE=1 python scripts/runtime_smoke.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
python -m compileall -q src scripts
python -m build --sdist --wheel --outdir /tmp/shuheng-dist
PYTHONDONTWRITEBYTECODE=1 python scripts/wheel_smoke.py --dist-dir /tmp/shuheng-dist
git diff --check
```

`scripts/wheel_smoke.py --dist-dir` 默认会分别安装最新 wheel 和 sdist，检查 wheel metadata/私有文件边界、wheel RECORD hash/size 完整性、sdist archive 的公开/私有文件边界、sdist metadata/entry points 和 SOURCES 清单一致性，并扫描两个 artifact 内容里的密钥形态和本地绝对路径，再运行公开入口点检查；`--no-deps` 和 `--wheel-only` 仅用于本地调试，不属于发布门禁。

发布前确认不要把本地绝对路径、密钥、模型配置、普通会话日志或 Secret Vault 内容写进仓库。`scripts/check_release_hygiene.py` 会检查治理文件、包元数据、私有路径、真实密钥形态和公开 alpha 口径。

### 开源发布边界

- License: MIT，见 `LICENSE`。
- 安全报告与边界：见 `SECURITY.md`。Shuheng 不内置 Web Console、HTTP gateway、mobile 或 remote endpoint；涉及外部发送、部署、删除、Secret、长期记忆的操作仍走本地审批门。
- 贡献流程：见 `CONTRIBUTING.md`；行为准则见 `CODE_OF_CONDUCT.md`。
- 发布记录：见 `CHANGELOG.md`。
- CI: `.github/workflows/ci.yml` 运行 release hygiene、policy gate、runtime smoke、pytest、compile、package build、wheel smoke 和 `git diff --check`。
- Public alpha readiness：见 `docs/public-alpha-readiness.md`，其中记录发布姿态、Trellis ledger 公开语义、已知缺口和 fresh clone 期望。

## Community

This project is promoted in the [LINUX DO](https://linux.do/) open-source community. Thanks to the community for discussion, feedback, and suggestions.
