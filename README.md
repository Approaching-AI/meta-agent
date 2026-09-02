# Meta Agent

A collection of advisory guidelines for building AI agents.

All content in this repository is **advisory, not prescriptive**. Agents should adapt these suggestions to their specific context, adopting what fits and setting aside what doesn't.

At the highest level, `meta-agent` only needs two persistent parts:

- `meta-log/`: the running record of what happened, what was decided, and what should happen next
- `doc/`: the stable knowledge base for the project

Everything else is optional support around those two folders.

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

Useful helper in the host repo:

```bash
bash meta-agent/scripts/session-end.sh
```

This helper only prepares a daily-notes template. The agent remains responsible for context, prioritization, and persistence.

## Roadmap 累积

When a new feature idea should not interrupt the current implementation, use Plan Mode or a similar planning process to design and rehearse it, then save the result in the host project’s Roadmap:

```text
doc/roadmap/<topic>/plan.md
```

Each item has its own directory. `plan.md` is a recommended entry point, not a required schema; supporting research, sketches, experiments, and open questions can live beside it. There is no mandatory status, priority, depth, or approval workflow.

Roadmap is a persisted pool of future plans, not a queue. Agents should inspect it only when the current task has settled, the user asks to continue a direction, or a new idea needs design. The agent decides whether and when a plan is ready to implement. Keep the plan as design history and record actual execution in the host project’s `meta-log/` or stable docs.

The Roadmap directory belongs to the host repository. It must not be written into the `meta-agent` submodule’s own `doc/` directory.

## Updating an integrated project

After updating the submodule, refresh the host project’s runtime guide:

```bash
git submodule update --remote meta-agent
bash meta-agent/scripts/sync-runtime.sh
```

This release removes the old handoff queue and autonomous session driver. Existing host repositories should stop invoking `scripts/meta-agent`, `run-session`, `run-loop`, or handoff-specific helper options. The update does not delete any existing host-side handoff files; archive or remove those deliberately if they are no longer needed.
