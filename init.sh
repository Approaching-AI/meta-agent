#!/bin/bash
# Usage: curl -fsSL https://raw.githubusercontent.com/Approaching-AI/meta-agent/main/init.sh | bash
# Or:    bash <(curl -fsSL https://raw.githubusercontent.com/Approaching-AI/meta-agent/main/init.sh)

set -e

# Ensure we are in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not inside a git repository."
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)

# Add meta-agent as submodule if not already present
if [ ! -d "$REPO_ROOT/meta-agent" ]; then
  echo "Adding meta-agent as submodule..."
  git submodule add https://github.com/Approaching-AI/meta-agent.git meta-agent
else
  echo "meta-agent submodule already exists."
fi

# Append reference to CLAUDE.md if not already present
CLAUDE_MD="$REPO_ROOT/CLAUDE.md"
MARKER="meta-agent/"

if [ -f "$CLAUDE_MD" ] && grep -q "$MARKER" "$CLAUDE_MD"; then
  echo "CLAUDE.md already references meta-agent."
else
  echo "" >> "$CLAUDE_MD"
  cat >> "$CLAUDE_MD" << 'EOF'

## Meta Agent Guidelines

Read the advisory guidelines in `meta-agent/` before starting work. These are suggestions — adapt them to the current project context.

Key files:
- `meta-agent/daily-notes.md` — how to keep daily logs
- `meta-agent/doc.md` — snapshot-style documentation
- `meta-agent/sop.md` — standard operating procedures

Periodically (e.g., daily or weekly) check if meta-agent has updates:
```bash
git submodule update --remote meta-agent
```
If there are changes, commit the update.
EOF
  echo "Updated CLAUDE.md with meta-agent reference."
fi

echo "Done. meta-agent integrated."
