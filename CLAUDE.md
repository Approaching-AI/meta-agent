# Meta Agent Guidelines

These are advisory guidelines — adapt them to the current project context.

Key references:
- `daily-notes.md` — how to keep daily logs
- `doc.md` — snapshot-style documentation
- `sop.md` — standard operating procedures
- `doc/methodology.md` — full methodology reference

## Session 开始流程

1. **检查 `handoff/*.pending.md`** — 如果有 pending 的 handoff 文件，读取内容作为本次 session 的任务指引。
2. **如果没有 pending handoff** — 等待用户给出指令。

> **开放问题**：如果同时存在多个 pending 文件，agent 根据具体情况自行判断如何处理（全部执行、按优先级选择等），待后续积累经验后再标准化。

## Session 结束流程

当人类要求结束 session 时，执行以下标准流程：

1. **总结写入 daily notes** — 记录本次 session 做了什么、遇到什么问题、下一步是什么。Append 到当天的 daily notes 文件。
2. **Commit & push** — 对本仓库执行 git commit 和 push，确保所有变更（daily notes、doc、代码等）持久化到远端。
3. **判断是否需要后续 agent 接手** — 如果任务未完成且后续可由 agent 独立推进，将 handoff prompt 写入 `handoff/YYYY-MM-DD-<简短描述>.pending.md`。文件内容纯粹是 prompt，不加 frontmatter 或其他格式。Prompt 包含：任务背景（简要）、当前进度、下一步指令、需要注意的风险。后续 agent 运行在同一个仓库中，能访问 daily notes 和所有记录，所以 prompt 只需指明方向，不需重复已有上下文。如果任务已完成或需要人类介入，不生成 handoff 文件，在 daily notes 中说明即可。

## Handoff 完成标记

当 agent 完成了某个 handoff 任务时，将对应文件从 `.pending.md` 重命名为 `.done.md`。这不限于特定流程阶段——agent 在工作过程中任何时候判断任务已完成，就执行 rename。
