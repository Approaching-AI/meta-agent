# Meta Agent Runtime Guide

This file is the fast path for agents running in a project that integrates `meta-agent`.

Read this file first. Only open `meta-agent/doc/methodology.md` when you need rationale, examples, or help with an edge case.

If you were launched by an automation driver, also follow the driver prompt. In that mode, the handoff file remains the primary task context, and you must write the expected session result file before ending the session.

In the autonomous driver flow, handoff state is directory-based:

- `handoff/`: queued inputs for future sessions
- `handoff-run/`: a handoff currently being consumed by a running session
- `handoff-history/`: consumed handoff inputs kept for audit/history

The driver, not the agent, is responsible for moving files across those directories.

## Session Start

In autonomous mode, the underlying SOP is:

1. Check `handoff/` for queued handoff files.
2. If one exists, the driver moves it to `handoff-run/` before launching the session.
3. Read that handoff content and use it as the primary task prompt.
4. If there is no queued handoff, fall back to the configured goal file or wait for user instructions.

Notes:

- If multiple queued handoffs exist, choose pragmatically based on priority and fit.
- On restart after interruption, inspect `handoff-run/` first. A valid `session-result.json` means the consumed input can be archived; otherwise the handoff should be re-queued.

## Session End

Run this flow before writing the final `session-result.json`.

1. Append a summary to today's `meta-log/`.
2. Include `operator: <name>` at the start of the session entry. This must be the human collaborator for the current session. If the automation driver provided an operator value, use that exact value. Only ask explicitly when no operator was provided.
3. Record what was done, important conclusions, open problems, and the next step.
4. Commit and push the repository so notes, docs, code, and handoff state are persisted.
5. Decide whether another agent session can continue the remaining work.
6. If yes, create a new handoff file under `handoff/`.
7. The handoff file should contain only a prompt with: brief background, current progress, the next instruction, and key risks.
8. If the work is complete or requires human input next, do not create a new handoff file. Say so in `meta-log/`.

If the automation setup provides both `questions/` and `answers/` directories:

- ask humans by writing files under `questions/`
- consume human replies from `answers/`
- use the same basename for a question and its answer
- check for a matching answer before asking the same question again or declaring a hard block

The session-result file is the final driver-facing acknowledgement after this flow is complete. It is not a substitute for the flow.

## State Model

For autonomous driver runs, handoff directories encode state:

- `handoff/`: queued for future consumption
- `handoff-run/`: currently in-flight
- `handoff-history/`: consumed and archived

## When To Read More

Open `meta-agent/doc/methodology.md` only if you need one of these:

- the reasoning behind the workflow
- examples of prompts or handoffs
- clarification for an unusual case not covered here
