# 2026-09-02

## Roadmap 累积方法与 handoff 清理

operator: xwy

**做了什么**：
- 新增 `doc/roadmap/README.md`，定义宿主项目使用 `doc/roadmap/<topic>/plan.md` 累积暂缓实现的功能计划；条目采用独立目录，内容深度和附属材料不设强制限制。
- 更新完整方法论、runtime guide、README、`doc.md` 和 `CLAUDE.md`，说明如何在当前功能进行中先用 Plan Mode 设计并保存 Roadmap，再由 agent 按需判断何时实现。
- 删除 autonomous driver、session-input 示例和 handoff 专用的 session-start helper；将 session-end helper 收缩为 daily-notes 模板工具。
- 更新 methodology PDF 快照，保持与 Markdown 方法论同步。

**结论**：
- Roadmap 是 `doc/` 内的未来计划沉淀，不是第三个核心持久层、任务队列或自动调度机制。
- handoff 已从实现和默认指导中彻底移除；历史 `meta-log/` 保持 append-only，不回改旧记录。

**待处理 / 风险**：
- 引用旧版本的宿主仓库需要停止调用 `scripts/meta-agent`、`run-session`、`run-loop` 和 handoff 专用参数；本次不会自动删除宿主仓库已有的 handoff 文件。
- 已有宿主仓库需更新 submodule 后运行 `scripts/sync-runtime.sh`，才能获得新的 Roadmap runtime 指引。

**验证**：
- `git diff --check` 和 shell 语法检查通过。
- 在临时 git 仓库中验证 `session-end.sh --append-daily --operator tester` 正常生成 daily-notes 模板。
- 在临时 git 仓库中验证 `sync-runtime.sh` 生成的 runtime guide 与源文件一致。
- 当前文档相对链接检查通过，已删除的 driver/handoff 入口不存在。
