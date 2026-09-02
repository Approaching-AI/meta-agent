#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash meta-agent/scripts/session-end.sh
  bash meta-agent/scripts/session-end.sh --append-daily --operator <name>

What it does:
  - Shows the target daily notes file and a ready-to-fill template
  - Optionally appends that template to today's daily notes

Notes:
  - This script only prepares a daily-notes template. The agent still decides
    what to record, whether a Roadmap plan is needed, and when to commit or push.
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

pick_daily_file() {
  shopt -s nullglob
  local matches=("$DAILY_NOTES_DIR/$TODAY"*.md)
  shopt -u nullglob

  if [[ -f "$DAILY_NOTES_DIR/$TODAY.md" ]]; then
    printf '%s\n' "$DAILY_NOTES_DIR/$TODAY.md"
    return 0
  fi

  if ((${#matches[@]} == 1)); then
    printf '%s\n' "${matches[0]}"
    return 0
  fi

  printf '%s\n' "$DAILY_NOTES_DIR/$TODAY.md"
}

print_daily_template() {
  local operator="$1"
  cat <<EOF
## Session $(date +%H:%M)

operator: $operator

**做了什么**：
- 

**结论**：
- 

**待处理 / 风险**：
- 

**下一步**：
- 
EOF
}

ensure_daily_header() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    mkdir -p "$(dirname "$file")"
    printf '# %s\n\n' "$TODAY" > "$file"
  fi
}

append_daily_template() {
  local operator="$1"
  local file="$2"

  ensure_daily_header "$file"
  printf '\n' >> "$file"
  print_daily_template "$operator" >> "$file"
  printf 'Appended session template to %s\n' "$(relpath "$file")"
}

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  printf 'Error: not inside a git repository.\n' >&2
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
TODAY=$(date +%F)
DAILY_NOTES_DIR="$REPO_ROOT/daily-notes"
DAILY_FILE=$(pick_daily_file)

DO_APPEND_DAILY=0
OPERATOR_NAME="<name>"

while (($# > 0)); do
  case "$1" in
    --append-daily)
      DO_APPEND_DAILY=1
      shift
      ;;
    --operator)
      if (($# < 2)); then
        printf 'Error: --operator requires a value.\n' >&2
        usage >&2
        exit 1
      fi
      OPERATOR_NAME="$2"
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

printf 'Repo: %s\n' "$REPO_ROOT"
printf 'Daily notes target: %s\n' "$(relpath "$DAILY_FILE")"
printf '\n'

printf '%s\n' '--- Daily Notes Template ---'
print_daily_template "$OPERATOR_NAME"

if ((DO_APPEND_DAILY == 1)); then
  append_daily_template "$OPERATOR_NAME" "$DAILY_FILE"
fi
