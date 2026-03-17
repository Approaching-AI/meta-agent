# Daily Notes

Agent should maintain a history log. To facilitate collaboration with humans, consider using a **daily notes** approach: create a `meta-log/` folder and organize records by date。文件名格式为 `YYYY-MM-DD.md` 或 `YYYY-MM-DD-<简要主题>.md`，可根据内容选择是否加主题后缀。

## Principles

- **Append-only by default.** Daily notes are records of what happened. Avoid modifying past entries.
- **Annotate, don't silently edit.** If a past entry turns out to be misleading or incorrect, mark the correction explicitly (e.g., add a note with the date of correction and the reason), rather than silently changing the original text.

## Session 标注

每次 session 的记录应标注操作者（即当时与 agent 协作的人）。在 session 对应的 section 开头加一行：

```
operator: <name>
```

这样在多人协作时可以追溯每段记录是谁主导的。如果 agent 不知道当前操作者是谁，应主动询问。

## What to Record

What goes into daily notes is decided by the agent and its human collaborator together. Typical triggers include:

- **New findings or conclusions** discovered during work.
- **Context overflow** — when the conversation context is about to fill up, persist the current working state so a future session can pick up where it left off.
