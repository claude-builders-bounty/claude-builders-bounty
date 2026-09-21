#!/bin/bash
# Claude Code PreToolUse hook: block destructive Bash commands.
# The command-structure classifier lives in command_parser.py so quoted prose
# and arguments are not mistaken for executable commands.
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PARSER="$SCRIPT_DIR/command_parser.py"
LOG_FILE="${HOME:?}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

is_destructive() {
  local status
  if python3 "$PARSER" "$1"; then
    return 0
  else
    status=$?
  fi
  # The parser uses 1 for a classified-safe command. Any other failure is an
  # analysis failure, not evidence of safety, so fail closed.
  if [ "$status" -eq 1 ]; then
    return 1
  fi
  printf 'Destructive-command classifier failed (status %s); blocking command.\n' "$status" >&2
  return 0
}

log_blocked() {
  local cmd="$1"
  local project_path="${2:-${CLAUDE_PROJECT_PATH:-$(pwd)}}"
  printf '[%s] BLOCKED: %s | project: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$cmd" "$project_path" >> "$LOG_FILE"
}

validate_command() {
  local cmd="$1"
  if [ -n "$cmd" ] && is_destructive "$cmd"; then
    printf '%s\n' 'DESTRUCTIVE COMMAND BLOCKED' "Command: $cmd"
    log_blocked "$cmd"
    return 1
  fi
}

# Claude Code PreToolUse protocol. Invalid and non-Bash events are neutral.
if [ "$#" -eq 0 ]; then
  PROTOCOL_INPUT=$(cat)
  parsed=$(printf '%s' "$PROTOCOL_INPUT" | python3 -c '
import base64, json, sys
try:
    data = json.load(sys.stdin)
    if data.get("tool_name") == "Bash":
        ti = data.get("tool_input") or {}
        command = ti.get("command", "")
        cwd = data.get("cwd") or ""
        print(base64.b64encode(command.encode()).decode() + "\t" + base64.b64encode(cwd.encode()).decode())
except (ValueError, TypeError, AttributeError):
    pass
')
  if [ -z "$parsed" ]; then exit 0; fi
  command_b64=${parsed%%$'\t'*}
  cwd_b64=${parsed#*$'\t'}
  command=$(printf '%s' "$command_b64" | base64 --decode 2>/dev/null || printf '%s' "$command_b64" | base64 -D)
  cwd=$(printf '%s' "$cwd_b64" | base64 --decode 2>/dev/null || printf '%s' "$cwd_b64" | base64 -D)
  if [ -n "$command" ] && is_destructive "$command"; then
    log_blocked "$command" "${cwd:-${CLAUDE_PROJECT_PATH:-$(pwd)}}"
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Destructive command blocked by safety hook."}}'
  fi
  exit 0
fi

validate_command "$1"
