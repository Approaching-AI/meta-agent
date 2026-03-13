# Meta Agent Guidelines

These are advisory guidelines — adapt them to the current project context.

Key references:
- `daily-notes.md` — how to keep daily logs
- `doc.md` — snapshot-style documentation
- `sop.md` — standard operating procedures
- `doc/methodology.md` — full methodology reference

## Session 结束流程

当人类要求结束 session 时，执行以下标准流程：

1. **总结写入 daily notes** — 记录本次 session 做了什么、遇到什么问题、下一步是什么。Append 到当天的 daily notes 文件。
2. **Commit & push** — 对本仓库执行 git commit 和 push，确保所有变更（daily notes、doc、代码等）持久化到远端。
3. **判断是否需要后续 agent 接手** — 如果任务未完成且后续可由 agent 独立推进，生成一段 handoff prompt，包含：任务背景（简要）、当前进度、下一步指令、需要注意的风险。后续 agent 运行在同一个仓库中，能访问 daily notes 和所有记录，所以 prompt 只需指明方向，不需重复已有上下文。如果任务已完成或需要人类介入，不生成 prompt，在 daily notes 中说明即可。
