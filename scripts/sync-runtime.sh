#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
META_AGENT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not inside a git repository."
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
SOURCE_FILE="$META_AGENT_DIR/runtime/AGENT-RUNTIME.md"
TARGET_DIR="$REPO_ROOT/.meta-agent"
TARGET_FILE="$TARGET_DIR/AGENT-RUNTIME.md"

mkdir -p "$TARGET_DIR"
cp "$SOURCE_FILE" "$TARGET_FILE"

echo "Synced $TARGET_FILE"
