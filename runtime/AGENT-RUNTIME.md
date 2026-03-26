# Meta Agent Runtime Guide

This file is the fast path for agents running in a project that integrates `meta-agent`.

Read this file first. Only open `meta-agent/doc/methodology.md` when you need rationale, examples, or help with an edge case.

## Session Start

Preferred helper:

```bash
bash meta-agent/scripts/session-start.sh
```

Useful variants:

```bash
bash meta-agent/scripts/session-start.sh --claim-first
bash meta-agent/scripts/session-start.sh --claim <pending-file-or-basename>
```

The underlying SOP is:

1. Check `handoff/*.pending.md`.
2. If one or more pending handoff files exist, choose the one you will handle now.
3. Immediately rename it from `.pending.md` to `.active.md`.
4. Commit and push the rename as soon as practical so other sessions see the claim.
5. Read the handoff content and use it as the task prompt.
6. If there is no pending handoff, wait for user instructions.

Notes:

- If multiple pending files exist, choose pragmatically based on priority and fit.
- `rename + push` still leaves a short race window. That is acceptable for now.

## Session End

Run this flow when the human explicitly asks to end the session.

1. Append a summary to today's daily notes.
2. Include `operator: <name>` at the start of the session entry. This must be the human collaborator for the current session. If unknown, ask explicitly instead of inferring from git config or other metadata.
3. Record what was done, important conclusions, open problems, and the next step.
4. Commit and push the repository so notes, docs, code, and handoff state are persisted.
5. Decide whether another agent session can continue the remaining work.
6. If yes, create `handoff/YYYY-MM-DD-<short-description>.pending.md`.
7. The handoff file should contain only a prompt with: brief background, current progress, the next instruction, and key risks.
8. If the current handoff task is complete, rename its file from `.active.md` to `.done.md`.
9. If the work is complete or requires human input next, do not create a new handoff file. Say so in daily notes.

Do not rely on a session-end helper script for this flow. Session end requires contextual judgment, a real summary, and explicit operator confirmation.

## State Model

Handoff filenames encode state:

- `.pending.md`: waiting to be claimed
- `.active.md`: claimed by an active session
- `.done.md`: finished

## When To Read More

Open `meta-agent/doc/methodology.md` only if you need one of these:

- the reasoning behind the workflow
- examples of prompts or handoffs
- clarification for an unusual case not covered here
