#!/usr/bin/env bash
# block-destructive-commands.sh — Claude Code PreToolUse hook
# Blocks destructive bash commands and logs attempts.
# Install: cp block-destructive-commands.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-commands.sh
set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
CWD=$(echo "$INPUT" | jq -r '.cwd // "unknown"')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_FILE="${HOME}/.claude/hooks/blocked.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

block_and_log() {
  local reason="$1"
  echo "[$TIMESTAMP] BLOCKED | cwd=$CWD | reason=$reason | command=$COMMAND" >> "$LOG_FILE"
  echo "BLOCKED: $reason" >&2
  echo "Attempted command: $COMMAND" >&2
  echo "Project path: $CWD" >&2
  echo "Logged to: $LOG_FILE" >&2
  exit 2
}

# 1. rm -rf (recursive force delete)
if echo "$COMMAND" | grep -qE '\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|-rf\s+|-fr\s+)'; then
  block_and_log "rm -rf detected: recursive forced deletion is destructive and irreversible"
fi

# 2. DROP TABLE (SQL)
if echo "$COMMAND" | grep -qiE '\bDROP\s+TABLE\b'; then
  block_and_log "DROP TABLE detected: destructive SQL operation that destroys table structure and data"
fi

# 3. git push --force / git push -f
if echo "$COMMAND" | grep -qE '\bgit\s+push\s+.*( --force | -f\b| --force-with-lease )'; then
  block_and_log "git push --force detected: force pushing rewrites remote history and can destroy others' work"
fi

# 4. TRUNCATE (SQL)
if echo "$COMMAND" | grep -qiE '\bTRUNCATE\s+(TABLE\s+)?\w+'; then
  block_and_log "TRUNCATE detected: destructive SQL operation that permanently removes all rows from a table"
fi

# 5. DELETE FROM without WHERE clause (SQL)
if echo "$COMMAND" | grep -qiE '\bDELETE\s+FROM\s+\w+(\s*;?\s*$)' && \
   ! echo "$COMMAND" | grep -qiE '\bWHERE\b'; then
  block_and_log "DELETE FROM without WHERE detected: would delete ALL rows from the table"
fi

exit 0
