#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash meta-agent/scripts/session-start.sh
  bash meta-agent/scripts/session-start.sh --claim-first
  bash meta-agent/scripts/session-start.sh --claim <pending-file-or-basename>

What it does:
  - Lists pending and active handoff files
  - Optionally claims one pending handoff by renaming it to .active.md
  - Prints the claimed handoff content for immediate execution

Notes:
  - This script does not commit or push. The agent should still decide when to do that.
  - The agent is still responsible for prioritization and edge-case handling.
EOF
}

relpath() {
  local path="$1"
  if [[ "$path" == "$REPO_ROOT/"* ]]; then
    printf '%s\n' "${path#$REPO_ROOT/}"
  else
    printf '%s\n' "$path"
  fi
}

list_handoffs() {
  local label="$1"
  shift
  local files=("$@")

  printf '%s: %s\n' "$label" "${#files[@]}"
  if ((${#files[@]} == 0)); then
    return
  fi

  local index=1
  local file
  for file in "${files[@]}"; do
    printf '  [%d] %s\n' "$index" "$(relpath "$file")"
    index=$((index + 1))
  done
}

resolve_pending() {
  local query="$1"
  local matches=()
  local file

  for file in "${pending_files[@]}"; do
    if [[ "$file" == "$query" || "$(relpath "$file")" == "$query" || "$(basename "$file")" == "$query" ]]; then
      matches+=("$file")
    fi
  done

  if ((${#matches[@]} == 1)); then
    printf '%s\n' "${matches[0]}"
    return 0
  fi

  if ((${#matches[@]} > 1)); then
    printf 'Error: multiple pending handoff files match "%s".\n' "$query" >&2
    local match
    for match in "${matches[@]}"; do
      printf '  - %s\n' "$(relpath "$match")" >&2
    done
    exit 1
  fi

  printf 'Error: no pending handoff file matches "%s".\n' "$query" >&2
  exit 1
}

claim_file() {
  local pending_file="$1"
  local active_file="${pending_file%.pending.md}.active.md"

  mv "$pending_file" "$active_file"

  printf 'Claimed: %s\n' "$(relpath "$active_file")"
  printf 'Next: commit and push this rename so other sessions see the claim.\n'
  printf '\n'
  printf '%s\n' '--- Handoff Content ---'
  cat "$active_file"
}

ACTION="inspect"
CLAIM_TARGET=""

while (($# > 0)); do
  case "$1" in
    --claim-first)
      ACTION="claim-first"
      shift
      ;;
    --claim)
      if (($# < 2)); then
        printf 'Error: --claim requires a file name.\n' >&2
        usage >&2
        exit 1
      fi
      ACTION="claim"
      CLAIM_TARGET="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Error: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  printf 'Error: not inside a git repository.\n' >&2
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
HANDOFF_DIR="$REPO_ROOT/handoff"

shopt -s nullglob
pending_files=("$HANDOFF_DIR"/*.pending.md)
active_files=("$HANDOFF_DIR"/*.active.md)
shopt -u nullglob

printf 'Repo: %s\n' "$REPO_ROOT"
list_handoffs "Pending handoffs" "${pending_files[@]}"
list_handoffs "Active handoffs" "${active_files[@]}"
printf '\n'

case "$ACTION" in
  inspect)
    if ((${#pending_files[@]} == 0)); then
      printf 'No pending handoff found. Wait for user instructions.\n'
      exit 0
    fi

    if ((${#pending_files[@]} == 1)); then
      printf 'Single pending handoff detected:\n'
      printf '%s\n' '--- Handoff Content ---'
      cat "${pending_files[0]}"
      printf '\n'
      printf 'Claim it with:\n'
      printf '  bash meta-agent/scripts/session-start.sh --claim-first\n'
      exit 0
    fi

    printf 'Choose one file, then claim it with:\n'
    printf '  bash meta-agent/scripts/session-start.sh --claim <pending-file-or-basename>\n'
    exit 0
    ;;
  claim-first)
    if ((${#pending_files[@]} == 0)); then
      printf 'No pending handoff found. Nothing to claim.\n'
      exit 0
    fi
    claim_file "${pending_files[0]}"
    ;;
  claim)
    claim_file "$(resolve_pending "$CLAIM_TARGET")"
    ;;
esac
