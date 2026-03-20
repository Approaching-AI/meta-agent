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
MARKER=".meta-agent/AGENT-RUNTIME.md"

# Sync the compact runtime guide into the host repo so agents can read a local file
bash "$REPO_ROOT/meta-agent/scripts/sync-runtime.sh"

if [ -f "$CLAUDE_MD" ] && grep -q "$MARKER" "$CLAUDE_MD"; then
  echo "CLAUDE.md already references meta-agent."
else
  echo "" >> "$CLAUDE_MD"
  cat >> "$CLAUDE_MD" << 'EOF'

## Meta Agent Guidelines

Read and follow the runtime guide in `.meta-agent/AGENT-RUNTIME.md`.

Only open `meta-agent/doc/methodology.md` when you need extra rationale, examples, or edge-case guidance.

Periodically (e.g., daily or weekly) check if meta-agent has updates:
```bash
git submodule update --remote meta-agent
bash meta-agent/scripts/sync-runtime.sh
```
If there are changes, commit the update.
EOF
  echo "Updated CLAUDE.md with meta-agent reference."
fi

echo "Done. meta-agent integrated."
