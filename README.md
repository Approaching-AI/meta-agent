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
bash meta-agent/scripts/session-end.sh
```
