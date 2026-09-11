#!/usr/bin/env bash
# Claude Code PreToolUse hook — block destructive bash before execution.
# Exit 0 allow; exit 2 block. Logs blocks to ~/.claude/hooks/blocked.log
set -euo pipefail

LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
PROJECT_PATH="${CLAUDE_PROJECT_DIR:-${PWD:-unknown}}"
mkdir -p "$LOG_DIR"

input=$(cat || true)
cmd="$input"
if command -v jq >/dev/null 2>&1; then
  parsed=$(printf '%s' "$input" | jq -r '.tool_input.command // .command // .input.command // empty' 2>/dev/null || true)
  if [[ -n "${parsed:-}" && "$parsed" != "null" ]]; then cmd="$parsed"; fi
fi
flat=$(printf '%s' "$cmd" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g')

reason=""
check() {
  local re="$1" why="$2"
  if printf '%s' "$flat" | grep -Eiq -- "$re"; then
    reason="$why"
    return 0
  fi
  return 1
}

if check 'rm[[:space:]]+-[a-zA-Z]*r' 'rm -r/-rf recursive delete'; then :; fi
if [[ -z "$reason" ]] && check 'mkfs\.' 'mkfs filesystem wipe'; then :; fi
if [[ -z "$reason" ]] && check 'dd[[:space:]]+.*of=/dev/' 'dd write to block device'; then :; fi
if [[ -z "$reason" ]] && check 'curl[[:space:]].*\|\s*(ba)?sh' 'curl pipe to shell'; then :; fi
if [[ -z "$reason" ]] && check 'wget[[:space:]].*\|\s*(ba)?sh' 'wget pipe to shell'; then :; fi
if [[ -z "$reason" ]] && check 'git[[:space:]]+push[[:space:]].*(--force|-f)' 'git push --force'; then :; fi
if [[ -z "$reason" ]] && check 'DROP[[:space:]]+(TABLE|DATABASE)' 'SQL DROP TABLE/DATABASE'; then :; fi
if [[ -z "$reason" ]] && check 'TRUNCATE[[:space:]]+(TABLE[[:space:]]+)?' 'SQL TRUNCATE'; then :; fi
# DELETE FROM t;  or DELETE FROM t  without WHERE
if [[ -z "$reason" ]] && printf '%s' "$flat" | grep -Eiq 'DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z0-9_."`]+[[:space:]]*;?[[:space:]]*$'; then
  if ! printf '%s' "$flat" | grep -Eiq 'WHERE'; then reason='DELETE FROM without WHERE'; fi
fi
if [[ -z "$reason" ]] && check ':()\{ :\|:& \};:' 'fork bomb'; then :; fi

if [[ -n "$reason" ]]; then
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  printf '%s\tproject=%s\treason=%s\tcmd=%s\n' "$ts" "$PROJECT_PATH" "$reason" "$flat" >> "$LOG_FILE"
  cat >&2 <<MSG
BLOCKED by pre-tool-use destructive-bash hook.
Reason: $reason
Command: $flat
Log: $LOG_FILE
Refusing to run this tool call. Use a safer command or ask the operator.
MSG
  exit 2
fi
exit 0
