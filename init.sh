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
- `meta-agent/doc/methodology.md` — full methodology reference

## Session 结束流程

当人类要求结束 session 时，执行以下标准流程：

1. **总结写入 daily notes** — 记录本次 session 做了什么、遇到什么问题、下一步是什么。Append 到当天的 daily notes 文件。
2. **Commit & push** — 对本仓库执行 git commit 和 push，确保所有变更（daily notes、doc、代码等）持久化到远端。
3. **判断是否需要后续 agent 接手** — 如果任务未完成且后续可由 agent 独立推进，生成一段 handoff prompt，包含：任务背景（简要）、当前进度、下一步指令、需要注意的风险。后续 agent 运行在同一个仓库中，能访问 daily notes 和所有记录，所以 prompt 只需指明方向，不需重复已有上下文。如果任务已完成或需要人类介入，不生成 prompt，在 daily notes 中说明即可。

Periodically (e.g., daily or weekly) check if meta-agent has updates:
```bash
git submodule update --remote meta-agent
```
If there are changes, commit the update.
EOF
  echo "Updated CLAUDE.md with meta-agent reference."
fi

echo "Done. meta-agent integrated."
