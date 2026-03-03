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
2. Append a reference to your `CLAUDE.md` so agents know to read the guidelines

To update the guidelines later:

```bash
git submodule update --remote meta-agent
```
