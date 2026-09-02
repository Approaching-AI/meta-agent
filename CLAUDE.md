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
- `doc/roadmap/README.md` — how to accumulate future feature plans
- `doc/methodology.md` — full methodology reference

## Session 开始流程

1. **检查最近上下文** — 先看最新的 `meta-log/`、相关 `doc/`、以及当前任务直接引用的文件，确认上一轮工作停在什么位置。
2. **读取显式任务入口** — 如果用户或当前仓库里已有目标文件给了明确任务入口，就以它为准继续推进。
3. **按需查看 Roadmap** — 当前任务收束、用户要求继续某个方向、或新想法需要设计时，再查看宿主项目的 `doc/roadmap/`。
4. **如果没有可执行入口** — 等待用户给出指令，不要为了队列或交接格式而额外制造文件。

## Session 结束流程

当人类要求结束 session 时，执行以下标准流程：

1. **总结写入 meta-log** — 记录本次 session 做了什么、遇到什么问题、下一步是什么。Append 到当天的 `meta-log/` 文件。记录开头标注 `operator: <name>`（与 agent 协作的人）。如果不知道操作者是谁，主动询问，不能用 git config 或其他环境信息代替确认。
2. **Commit & push** — 对本仓库执行 git commit 和 push，确保所有变更（meta-log、doc、代码等）持久化到远端。
3. **为下一轮留下清晰入口** — 如果任务未完成但后续 agent 可以继续，就把“当前进度、下一步、关键风险”写进 `meta-log/` 或相关目标文件；如果只是尚未排期的新方向，则保存到宿主项目的 `doc/roadmap/<topic>/`。

`session-end.sh` 只能用于准备 daily-notes 模板，不能替代 agent 对上下文和下一步的判断。
