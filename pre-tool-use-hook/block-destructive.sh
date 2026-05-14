#!/bin/bash
# block-destructive.sh — Claude Code PreToolUse hook
# Blocks dangerous shell commands: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
# Install: cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read JSON input from stdin (PreToolUse event)
INPUT=$(cat)

# Only process Bash tool calls
TOOL=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
if [ "$TOOL" != "Bash" ]; then
  exit 0
fi

# Extract the actual command
CMD=$(echo "$INPUT" | python3 -c "
import json,sys
d = json.load(sys.stdin)
ti = d.get('tool_input', {})
print(ti.get('command', ti.get('cmd', '')))
" 2>/dev/null)

# Get project info
PROJECT_DIR=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('project_dir',''))" 2>/dev/null)
[ -z "$PROJECT_DIR" ] && PROJECT_DIR="${CLAUDE_PROJECT_DIR:-unknown}"

# Normalize: collapse whitespace for matching
CMD_NORM=$(echo "$CMD" | tr -s ' ')

# ---- Danger Pattern Checks ----
REASON=""

# 1. rm -rf (recurisve forced delete)
if echo "$CMD_NORM" | grep -qE '\brm\s+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)\b'; then
  REASON="rm -rf is blocked: this permanently deletes files without recovery. Use 'rm' without -rf, or move to Trash instead."
fi

# 2. git push --force (destructive force-push)
if [ -z "$REASON" ] && echo "$CMD_NORM" | grep -qE '\bgit\s+push\s+.*(--force|-f)\b'; then
  REASON="git push --force is blocked: overwrites remote history and can break collaborators. Use 'git push --force-with-lease' for a safer force-push."
fi

# 3. DROP TABLE (destructive DDL)
if [ -z "$REASON" ] && echo "$CMD_NORM" | grep -qiE '\bDROP\s+TABLE'; then
  REASON="DROP TABLE is blocked: permanently deletes a database table and all its data. Use DELETE or rename instead."
fi

# 4. TRUNCATE
if [ -z "$REASON" ] && echo "$CMD_NORM" | grep -qiE '\bTRUNCATE\b'; then
  REASON="TRUNCATE is blocked: quickly removes all rows from a table without transaction safety. Use DELETE or a safer batch approach."
fi

# 5. DELETE FROM without WHERE (mass deletion with no filter)
if [ -z "$REASON" ] && echo "$CMD_NORM" | grep -qiE '\bDELETE\s+FROM\b'; then
  # Check if WHERE clause is present
  if ! echo "$CMD_NORM" | grep -qiE '\bWHERE\b'; then
    REASON="DELETE FROM without WHERE is blocked: would delete ALL rows in the table. Add a WHERE clause to target specific rows."
  fi
fi

# ---- Act on Result ----
if [ -n "$REASON" ]; then
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

  # Log the blocked attempt
  echo "[$TIMESTAMP] BLOCKED | dir=$PROJECT_DIR | cmd=$CMD" >> "$LOG_FILE"

  # Return denial to Claude Code
  echo "{\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"$REASON\"}"
  exit 0
fi

# Allow everything else
exit 0
