#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash meta-agent/scripts/session-end.sh
  bash meta-agent/scripts/session-end.sh --append-daily --operator <name>
  bash meta-agent/scripts/session-end.sh --create-handoff <short-description>
  bash meta-agent/scripts/session-end.sh --complete-current
  bash meta-agent/scripts/session-end.sh --complete <active-file-or-basename>

What it does:
  - Shows the target daily notes file and a ready-to-fill template
  - Optionally appends that template to today's daily notes
  - Optionally creates a pending handoff template file
  - Optionally marks an active handoff as done

Notes:
  - This script does not commit or push. The agent should still decide when to do that.
  - The agent is still responsible for deciding whether a handoff is needed.
EOF
}

slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
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

resolve_active() {
  local query="$1"
  local matches=()
  local file

  for file in "${active_files[@]}"; do
    if [[ "$file" == "$query" || "$(relpath "$file")" == "$query" || "$(basename "$file")" == "$query" ]]; then
      matches+=("$file")
    fi
  done

  if ((${#matches[@]} == 1)); then
    printf '%s\n' "${matches[0]}"
    return 0
  fi

  if ((${#matches[@]} > 1)); then
    printf 'Error: multiple active handoff files match "%s".\n' "$query" >&2
    local match
    for match in "${matches[@]}"; do
      printf '  - %s\n' "$(relpath "$match")" >&2
    done
    exit 1
  fi

  printf 'Error: no active handoff file matches "%s".\n' "$query" >&2
  exit 1
}

complete_handoff() {
  local active_file="$1"
  local done_file="${active_file%.active.md}.done.md"
  mv "$active_file" "$done_file"
  printf 'Marked done: %s\n' "$(relpath "$done_file")"
}

create_handoff() {
  local description="$1"
  local slug
  slug=$(slugify "$description")

  if [[ -z "$slug" ]]; then
    printf 'Error: handoff description must contain letters or numbers.\n' >&2
    exit 1
  fi

  mkdir -p "$HANDOFF_DIR"
  local handoff_file="$HANDOFF_DIR/$TODAY-$slug.pending.md"

  if [[ -e "$handoff_file" ]]; then
    printf 'Error: handoff file already exists: %s\n' "$(relpath "$handoff_file")" >&2
    exit 1
  fi

  cat > "$handoff_file" <<EOF
任务背景：

当前进度：

下一步指令：

风险 / 注意事项：

EOF

  printf 'Created handoff template: %s\n' "$(relpath "$handoff_file")"
}

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  printf 'Error: not inside a git repository.\n' >&2
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
TODAY=$(date +%F)
DAILY_NOTES_DIR="$REPO_ROOT/daily-notes"
HANDOFF_DIR="$REPO_ROOT/handoff"
DAILY_FILE=$(pick_daily_file)

shopt -s nullglob
active_files=("$HANDOFF_DIR"/*.active.md)
shopt -u nullglob

DO_APPEND_DAILY=0
OPERATOR_NAME="<name>"
HANDOFF_DESCRIPTION=""
COMPLETE_MODE=""
COMPLETE_TARGET=""

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
    --create-handoff)
      if (($# < 2)); then
        printf 'Error: --create-handoff requires a description.\n' >&2
        usage >&2
        exit 1
      fi
      HANDOFF_DESCRIPTION="$2"
      shift 2
      ;;
    --complete-current)
      COMPLETE_MODE="current"
      shift
      ;;
    --complete)
      if (($# < 2)); then
        printf 'Error: --complete requires a file name.\n' >&2
        usage >&2
        exit 1
      fi
      COMPLETE_MODE="target"
      COMPLETE_TARGET="$2"
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
printf '\n'

printf 'Active handoffs: %s\n' "${#active_files[@]}"
if ((${#active_files[@]} > 0)); then
  local_file_index=1
  for file in "${active_files[@]}"; do
    printf '  [%d] %s\n' "$local_file_index" "$(relpath "$file")"
    local_file_index=$((local_file_index + 1))
  done
fi

printf '\n'
printf 'Suggested handoff file:\n'
printf '  handoff/%s-<short-description>.pending.md\n' "$TODAY"
printf '\n'

if ((DO_APPEND_DAILY == 1)); then
  append_daily_template "$OPERATOR_NAME" "$DAILY_FILE"
fi

if [[ -n "$HANDOFF_DESCRIPTION" ]]; then
  create_handoff "$HANDOFF_DESCRIPTION"
fi

case "$COMPLETE_MODE" in
  current)
    if ((${#active_files[@]} == 0)); then
      printf 'No active handoff found. Nothing to mark done.\n'
    elif ((${#active_files[@]} > 1)); then
      printf 'Error: multiple active handoffs exist. Use --complete <active-file-or-basename>.\n' >&2
      exit 1
    else
      complete_handoff "${active_files[0]}"
    fi
    ;;
  target)
    complete_handoff "$(resolve_active "$COMPLETE_TARGET")"
    ;;
esac
