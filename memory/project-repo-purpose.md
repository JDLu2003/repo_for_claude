---
name: 仓库用途与约定
type: project
updated: 2026-09-29
---
本仓库需要同时存放 Agent 的**记忆系统**和**会话内容**，方便用户后续在仓库里查看。

**Why:** 用户希望会话与记忆可持久化、可回溯，不依赖单次会话上下文。
**How to apply:** 每次会话开始读 `memory/MEMORY.md`，过程中写入 `sessions/`，结束时提炼记忆并提交。
