# Meta Agent Runtime Guide

This file is the fast path for agents running in a project that integrates `meta-agent`.

Read this file first. Only open `meta-agent/doc/methodology.md` when you need rationale, examples, or help with an edge case.

If you were launched by an automation driver, also follow the driver prompt. In that mode, the handoff file remains the primary task context, and you must write the expected session result file before ending the session.

The repo supports two handoff operating modes:

- manual mode: the agent claims `.pending.md` files and advances them through `.active.md` to `.done.md`
- autonomous mode: the driver moves files across `handoff/`, `handoff-run/`, and `handoff-history/`

## Session Start

In manual mode, preferred helper:

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

In autonomous mode, the underlying SOP is:

1. Check `handoff/` for queued handoff files.
2. If one exists, the driver moves it to `handoff-run/` before launching the session.
3. Read that handoff content and use it as the primary task prompt.
4. If there is no queued handoff, fall back to the configured goal file or wait for user instructions.

Notes:

- If multiple queued handoffs exist, choose pragmatically based on priority and fit.
- On restart after interruption, inspect `handoff-run/` first. A valid `session-result.json` means the consumed input can be archived; otherwise the handoff should be re-queued.

## Session End

Run this flow when the human explicitly asks to end the session.

In manual mode, preferred helper:

```bash
bash meta-agent/scripts/session-end.sh
```

Useful variants:

```bash
bash meta-agent/scripts/session-end.sh --append-daily --operator <name>
bash meta-agent/scripts/session-end.sh --create-handoff <short-description>
bash meta-agent/scripts/session-end.sh --complete-current
```

These helpers only prepare files and deterministic renames. The agent still decides whether a handoff is needed, what summary to write, and when to commit or push.

1. Append a summary to today's daily notes.
2. Include `operator: <name>` at the start of the session entry. If unknown, ask.
3. Record what was done, important conclusions, open problems, and the next step.
4. Commit and push the repository so notes, docs, code, and handoff state are persisted.
5. Decide whether another agent session can continue the remaining work.
6. If yes, create `handoff/YYYY-MM-DD-<short-description>.pending.md`.
7. The handoff file should contain only a prompt with: brief background, current progress, the next instruction, and key risks.
8. If the current handoff task is complete, rename its file from `.active.md` to `.done.md`.
9. If the work is complete or requires human input next, do not create a new handoff file. Say so in daily notes.

In autonomous mode, run this same flow before writing the final `session-result.json`, with these differences:

1. Append the summary to today's `meta-log/`.
2. Use the operator value provided by the driver when present. Only ask explicitly when none was provided.
3. Create any follow-up handoff under `handoff/`; the driver is responsible for moving consumed inputs across directories.
4. Write `session-result.json` only after the normal session-end flow is complete.

If the automation setup provides both `questions/` and `answers/` directories:

- ask humans by writing files under `questions/`
- consume human replies from `answers/`
- use the same basename for a question and its answer
- check for a matching answer before asking the same question again or declaring a hard block

The session-result file is the final driver-facing acknowledgement after this flow is complete. It is not a substitute for the flow.

## State Model

Manual mode uses filename state:

- `.pending.md`: waiting to be claimed
- `.active.md`: claimed by an active session
- `.done.md`: finished

Autonomous driver mode uses directory state:

- `handoff/`: queued for future consumption
- `handoff-run/`: currently in-flight
- `handoff-history/`: consumed and archived

## When To Read More

Open `meta-agent/doc/methodology.md` only if you need one of these:

- the reasoning behind the workflow
- examples of prompts or handoffs
- clarification for an unusual case not covered here
