# Meta Agent Runtime Guide

This file is the fast path for agents running in a project that integrates `meta-agent`.

Read this file first. Only open `meta-agent/doc/methodology.md` when you need rationale, examples, or help with an edge case. The host project’s future feature plans live in its own `doc/roadmap/` directory.

## Session Start

1. Check the latest `meta-log/`, the files directly referenced by the current task, and the user’s instructions.
2. If there is already a clear task entry point, continue from there.
3. If the current task has settled, the user asks for a future direction, or a new idea needs design, inspect the relevant parts of the host project’s `doc/roadmap/` as needed.
4. If there is no clear entry point, wait for user instructions.

Do not scan the entire Roadmap on every session. Roadmap is a pool of persisted future plans, not a queue or an automatic work scheduler.

## Roadmap 累积

When a new feature idea should not interrupt the current implementation:

1. Use Plan Mode or a similar planning process to explore and rehearse the idea.
2. Save the resulting plan under `doc/roadmap/<topic>/`, normally as `plan.md`.
3. Keep working on the current task after the plan is persisted.

The entry may contain any supporting material needed; there is no required template, depth, status, priority, or approval workflow. If the active Plan Mode cannot write files, save the agreed plan after returning to a write-enabled phase.

When the current task is complete, the agent decides whether a Roadmap item is relevant enough to start. Keep the original plan as design history and record implementation results in the host project’s `meta-log/` or stable documentation.

## Session End

Run this flow when the human explicitly asks to end the session:

```bash
bash meta-agent/scripts/session-end.sh
```

Useful variant:

```bash
bash meta-agent/scripts/session-end.sh --append-daily --operator <name>
```

The helper only prepares a daily-notes template. The agent still decides what to record and when to commit or push.

1. Append a summary to the host project’s daily notes.
2. Include `operator: <name>` at the start of the session entry. If unknown, ask.
3. Record what was done, important conclusions, open problems, and the next step.
4. Commit and push the repository so notes, docs, and code are persisted.
5. If an unrelated future direction was designed during the session, make sure its Roadmap plan is saved.

If the work is complete or the next step requires human input, say so in the daily notes. Do not create queue files or handoff files.

## When To Read More

Open `meta-agent/doc/methodology.md` only if you need one of these:

- the reasoning behind the workflow
- examples of prompts or continuity patterns
- clarification for an unusual case not covered here
