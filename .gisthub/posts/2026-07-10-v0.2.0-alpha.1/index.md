---
title: "v0.2.0-alpha.1 发布：更紧的边界，更诚实的安装"
date: 2026-07-10
type: update
cover: images/cover.png
tags: [release, alpha, changelog]
author: "vimalinx"
---

Shuheng v0.2.0-alpha.1（PEP 440: `0.2.0a1`）发布 🚀 仍是 experimental local alpha，但这版把几个关键边界收紧了。

## 本次更新

- **Pi-native Agent Projects**：可编辑、不可变 Build 的 Agent Projects，跑在常驻 OMP 主 Agent 之下；显式 Tool 授权、task-policy 分离、Run Manifest 溯源、单写者参与。Pi worker 的 Tool 是可信本机 Node 代码，MVP 阶段没有 OS syscall 沙箱，只跑你信任的源码。
- **密钥边界收紧**：模型凭据移入 Shuheng 私有状态（`~/.shuheng/config/mykey.py`，目录 `0700`、文件 `0600`），subprocess 环境和 OMP 审批边界同步收紧。单独设 `yolo` 会被降级为 `write`，要全权限必须 `full + yolo` 同时显式设置。
- **更诚实的安装与自检**：干净机器上 OMP/Pi runtime setup 和 doctor 行为如实报告，缺 runtime 明确失败，不输出假成功。
- **Gateway 收窄**：持久 JSONL gateway 缩减为四个公开动作的正向 schema，帧里不再带内部 metadata 和机器路径。
- **可复现发布**：声明的 Python / build-tool 版本上可复现，CI 增加 clean-clone 覆盖。
- **版本身份切换**：从 `0.1.0` 切到 PEP 440 `0.2.0a1`，验证了 fresh install 和 alpha.1 升级路径。

## 升级

推荐重跑已检查过的安装器：

```bash
sh /tmp/shuheng-install.sh --version v0.2.0-alpha.1
shuheng --version
shuheng-check
```

## 已知缺口（照实说）

- `app.py` 仍是约 28k 行的 composition module，正按 `docs/app-py-decomposition-plan.md` 分阶段精简
- heuristic eval 不证明事实 / 引用正确
- A2A/MCP-shaped records 是本地 record 形状，不是可访问的协议 endpoint

完整边界见 `docs/public-alpha-readiness.md` 和 `CHANGELOG.md`。MIT 协议，欢迎试用和反馈 🙌
