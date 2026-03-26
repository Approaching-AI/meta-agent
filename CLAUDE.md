# Meta Agent Guidelines

These are advisory guidelines — adapt them to the current project context.

Scope note:
- These rules describe how `meta-agent` maintains its own internal records.
- `meta-agent`'s internal session log is stored in `meta-log/`.
- External/project agents that only use `meta-agent` as guidance should write project records to the host project's own `daily-notes/` convention, not to `meta-agent/meta-log/`.

Key references:
- `runtime/AGENT-RUNTIME.md` — compact execution rules for external agents
- `daily-notes.md` — how `meta-agent` keeps its internal `meta-log/`
- `doc.md` — snapshot-style documentation
- `sop.md` — standard operating procedures
- `doc/methodology.md` — full methodology reference

## Session 开始流程

1. **检查 `handoff/*.pending.md`** — 如果有 pending 的 handoff 文件，读取内容作为本次 session 的任务指引。
2. **认领 handoff** — 立即将选中的文件从 `.pending.md` 重命名为 `.active.md`，然后 commit & push，防止其他 session 重复认领。
3. **如果没有 pending handoff** — 等待用户给出指令。

> **开放问题**：如果同时存在多个 pending 文件，agent 根据具体情况自行判断如何处理（全部执行、按优先级选择等），待后续积累经验后再标准化。
>
> **并发说明**：rename + push 之间仍有短暂竞争窗口，但对于当前使用频率足够。如果未来出现实际冲突，再引入更强的锁机制。

## Session 结束流程

当人类要求结束 session 时，执行以下标准流程：

1. **总结写入 meta-log** — 记录本次 session 做了什么、遇到什么问题、下一步是什么。Append 到当天的 `meta-log/` 文件。记录开头标注 `operator: <name>`（与 agent 协作的人）。如果不知道操作者是谁，主动询问，不能用 git config 或其他环境信息代替确认。
2. **Commit & push** — 对本仓库执行 git commit 和 push，确保所有变更（meta-log、doc、代码等）持久化到远端。
3. **判断是否需要后续 agent 接手** — 如果任务未完成且后续可由 agent 独立推进，将 handoff prompt 写入 `handoff/YYYY-MM-DD-<简短描述>.pending.md`。文件内容纯粹是 prompt，不加 frontmatter 或其他格式。Prompt 包含：任务背景（简要）、当前进度、下一步指令、需要注意的风险。后续 agent 运行在同一个仓库中，能访问 meta-log 和所有记录，所以 prompt 只需指明方向，不需重复已有上下文。如果任务已完成或需要人类介入，不生成 handoff 文件，在 meta-log 中说明即可。

不要把 session end 委托给一键 helper script。结束流程依赖上下文判断，必须由 agent 自己完成。

## Handoff 状态流转

文件后缀表示状态：`.pending.md` → `.active.md` → `.done.md`

- **pending → active**：session 认领时重命名，立即 commit & push。
- **active → done**：任务完成时重命名。不限于特定流程阶段——agent 在工作过程中任何时候判断任务已完成，就执行 rename。
- **其他 session 看到 `.active.md`**：说明已有 session 在处理，不要重复认领。
