# 会话：init-agents-md

- 日期：2026-09-29
- 分支：claude/gracious-faraday-75rp8h

## 目标
新仓库，构建 AGENTS.md；要求把记忆系统和会话内容都放进仓库，便于后续查看；搭建一个简单的 system。

## 对话记录
- 用户：这是新仓库，希望在 AGENTS.md 中说明需要把记忆系统放入仓库、把会话内容放入仓库，便于后续查看，并构建一个简单的系统。
- 决策：采用纯 Markdown 文件方案——`memory/`（索引 + 单条记忆）、`sessions/`（每次会话一个文件）、`scripts/new-session.sh`（创建会话记录）。

## 执行的操作
- 新建 `AGENTS.md`、`memory/MEMORY.md`、`memory/project-repo-purpose.md`、`sessions/_template.md`、`scripts/new-session.sh`。

## 总结
仓库已具备最小可用的记忆 + 会话记录系统。

## 待办
- 后续会话按 AGENTS.md 流程使用并按需调整。
