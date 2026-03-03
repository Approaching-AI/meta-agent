# Daily Notes

Agent should maintain a history log. To facilitate collaboration with humans, consider using a **daily notes** approach: create a `daily-notes/` folder and organize records by date.

## Principles

- **Append-only by default.** Daily notes are records of what happened. Avoid modifying past entries.
- **Annotate, don't silently edit.** If a past entry turns out to be misleading or incorrect, mark the correction explicitly (e.g., add a note with the date of correction and the reason), rather than silently changing the original text.

## What to Record

What goes into daily notes is decided by the agent and its human collaborator together. Typical triggers include:

- **New findings or conclusions** discovered during work.
- **Context overflow** — when the conversation context is about to fill up, persist the current working state so a future session can pick up where it left off.
