#!/bin/bash
# Pre-tool-use hook: blocks destructive bash commands
set -e

COMMAND=$(jq -r '.tool_input.command // empty')
LOG_FILE="$HOME/.claude/hooks/blocked.log"

[ -z "$COMMAND" ] && exit 0
PROJECT_PATH=$(jq -r '.cwd // empty')
NORMALIZED=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

deny() {
  local reason="$1"
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] COMMAND: $COMMAND | PROJECT: $PROJECT_PATH | REASON: $reason" >> "$LOG_FILE"
  jq -n --arg reason "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: ($reason)
    }
  }'
  exit 0
}

# Check destructive patterns
if echo "$NORMALIZED" | grep -qE '\brm[[:space:]]+-rf\b'; then
  deny "rm -rf is not allowed — use a targeted path instead of recursive force-delete"
fi

if echo "$NORMALIZED" | grep -qE '\bdrop[[:space:]]+table\b'; then
  deny "DROP TABLE is not allowed — this would destroy database data permanently"
fi

if echo "$NORMALIZED" | grep -qE '\btruncate[[:space:]]+table\b'; then
  deny "TRUNCATE is not allowed — this would wipe a database table"
fi

if echo "$NORMALIZED" | grep -qE '\bgit[[:space:]]+push.*--force\b'; then
  deny "git push --force is not allowed — use --force-with-lease instead"
fi

if echo "$NORMALIZED" | grep -qE '\bdelete[[:space:]]+from\b'; then
  if ! echo "$NORMALIZED" | grep -qE '\bwhere\b'; then
    deny "DELETE FROM without WHERE is not allowed — this would delete all rows in a table"
  fi
fi

exit 0
