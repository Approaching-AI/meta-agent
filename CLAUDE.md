# Meta Agent Guidelines

These are advisory guidelines — adapt them to the current project context.

Scope note:
- These rules describe how `meta-agent` maintains its own internal records.
- `meta-agent`'s core persistent structure is just `meta-log/` + `doc/`.
- `meta-agent`'s internal session log is stored in `meta-log/`.
- External/project agents that only use `meta-agent` as guidance should write project records to the host project's own `daily-notes/` convention, not to `meta-agent/meta-log/`.

Key references:
- `runtime/AGENT-RUNTIME.md` — compact execution rules for external agents
- `daily-notes.md` — how `meta-agent` keeps its internal `meta-log/`
- `doc.md` — snapshot-style documentation
- `sop.md` — standard operating procedures
- `doc/methodology.md` — full methodology reference

## Session 开始流程

1. **检查最近上下文** — 先看最新的 `meta-log/`、相关 `doc/`、以及当前任务直接引用的文件，确认上一轮工作停在什么位置。
2. **读取显式任务入口** — 如果用户、driver 或当前仓库里已有目标文件给了明确任务入口，就以它为准继续推进。
3. **如果没有可执行入口** — 等待用户给出指令，不要为了“交接格式”而额外制造文件。

## Session 结束流程

当人类要求结束 session 时，执行以下标准流程：

1. **总结写入 meta-log** — 记录本次 session 做了什么、遇到什么问题、下一步是什么。Append 到当天的 `meta-log/` 文件。记录开头标注 `operator: <name>`（与 agent 协作的人）。如果不知道操作者是谁，主动询问，不能用 git config 或其他环境信息代替确认。
2. **Commit & push** — 对本仓库执行 git commit 和 push，确保所有变更（meta-log、doc、代码等）持久化到远端。
3. **为下一轮留下清晰入口** — 如果任务未完成但后续 agent 可以继续，就把“当前进度、下一步、关键风险”写清楚。默认直接写进 `meta-log/` 或相关目标文件；只有在确实需要时，才额外创建专门的交接文件。

不要把 session end 委托给一键 helper script。结束流程依赖上下文判断，必须由 agent 自己完成。
