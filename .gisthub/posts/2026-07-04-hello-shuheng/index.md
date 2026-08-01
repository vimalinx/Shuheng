---
title: "三分钟跑起你的本地 Agent 控制面"
date: 2026-07-04
type: note
cover: images/cover.png
tags: [安装, 快速开始, TUI, alpha]
author: "vimalinx"
---

枢衡 Shuheng 首个公开 alpha（0.1.0）上线 🎉

它是一个面向本地多 Agent 的终端控制面：不重写底层 agent runtime，只把会话、调度、审批、记忆这些事情收进一个 curses TUI。

## 安装只要一条命令

```bash
curl -fsSL https://raw.githubusercontent.com/vimalinx/Shuheng/main/scripts/install.sh | sh
```

安装器会在用户目录建隔离 venv，装好 `shuheng` / `shuheng-check` 入口和固定版本的 OMP runtime。OMP 需要 Bun 1.3.14+；缺主 runtime 时安装器会明确失败，不会假装成功。

支持 Linux、WSL2，macOS 是 best-effort；native Windows 请走 WSL2。

## 装完先自检

```bash
shuheng-check
```

健康输出长这样：

```text
Core runtime: OhMyPi / OMP
OMP runtime check: OK
Status: OK
```

## 启动

```bash
shuheng
```

进入 TUI 后输入 `/help` 看完整命令。开发者也可以不安装直接跑：

```bash
PYTHONPATH=src python -m shuheng
```

要求 Python >= 3.10，MIT 协议。当前定位是 experimental local alpha，欢迎来试 🙌
