# Meta Agent

A collection of advisory guidelines for building AI agents.

All content in this repository is **advisory, not prescriptive**. Agents should adapt these suggestions to their specific context, adopting what fits and setting aside what doesn't.

## Quick Start

In any git project, run:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Approaching-AI/meta-agent/main/init.sh)
```

This will:
1. Add `meta-agent` as a git submodule
2. Copy a compact runtime guide to `.meta-agent/AGENT-RUNTIME.md`
3. Append a reference to your `CLAUDE.md` so agents read the local runtime guide first

To update the guidelines later:

```bash
git submodule update --remote meta-agent
bash meta-agent/scripts/sync-runtime.sh
```

`meta-agent/doc/methodology.md` remains the full reference. The copied `.meta-agent/AGENT-RUNTIME.md` is the fast execution path for external agents.

Useful helpers in the host repo:

```bash
bash meta-agent/scripts/session-start.sh
```

## Autonomous Session Driver

`meta-agent` now includes a thin agent-agnostic session driver. The standard call format is:

```bash
meta-agent/scripts/meta-agent run-session \
  --agent codex \
  --repo /path/to/repo \
  --input /path/to/repo/.meta-agent/runs/run-001/session-input.json \
  --run-dir /path/to/repo/.meta-agent/runs/run-001
```

`session-input.json` is the driver input contract. See `runtime/session-input.example.json` for a concrete example. The minimal useful shape is:

```json
{
  "goal_file": "goals/goal-session-driver.md",
  "handoff_file": "handoff/2026-03-26-example.pending.md",
  "runtime_guide_file": ".meta-agent/AGENT-RUNTIME.md",
  "open_questions_dir": "questions"
}
```

`goal_file` is the long-lived goal file for the automation loop. `GOAL.md` is only the default filename. In practice, a topic-specific name such as `goals/goal-session-driver.md` is often better for tracking work over time.

The driver turns that input into one autonomous agent session. It writes:

- `<run-dir>/prompt.md`
- `<run-dir>/events.jsonl`
- `<run-dir>/last-message.md`
- `<run-dir>/driver-metadata.json`
- `<run-dir>/session-result.json` by default, unless `session_result_file` is set in the input

The required session result shape is:

```json
{
  "outcome": "continue | completed | hard_blocked | failed",
  "summary": "short plain-language summary",
  "handoff_files": ["handoff/optional-file.pending.md"],
  "question_files": ["questions/optional-question.md"],
  "block_reason": "required when outcome is hard_blocked"
}
```

Current adapter support:

- `codex`: invokes `codex --dangerously-bypass-approvals-and-sandbox exec ...`

Use `--dry-run` to render the prompt and planned command without invoking the agent:

```bash
meta-agent/scripts/meta-agent run-session \
  --agent codex \
  --repo /path/to/repo \
  --input /path/to/repo/.meta-agent/runs/run-001/session-input.json \
  --run-dir /path/to/repo/.meta-agent/runs/run-001 \
  --dry-run
```

To keep running until there is no pending handoff left, use `run-loop`:

```bash
meta-agent/scripts/meta-agent run-loop \
  --agent codex \
  --repo /path/to/repo
```

`run-loop` behavior:

- picks the newest `handoff/*.pending.md` as the next session input
- falls back to the configured goal file only for the first session when no pending handoff exists
- keeps question files asynchronous; they do not stop the loop by themselves
- stops on `hard_blocked`, on session failure, when no pending handoff remains, or when `--max-sessions` is reached

The goal file is not meant to be a task checklist. It is better treated as the long-lived explanation of what the system is trying to achieve, how the agent should interpret progress, and what boundaries it should respect.
