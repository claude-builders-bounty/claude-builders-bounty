#!/usr/bin/env bash
#
# pre-tool-use.sh - Claude Code hook that blocks destructive bash commands
#
# Installation:
#   mkdir -p ~/.claude/hooks
#   cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use
#   chmod +x ~/.claude/hooks/pre-tool-use
#
# This hook intercepts dangerous bash commands before they execute.
# Blocked patterns: rm -rf, DROP TABLE, git push --force, TRUNCATE,
#                   DELETE FROM without WHERE

set -euo pipefail

# Configuration
BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"
PROJECT_PATH="$(pwd)"

# Create log file if it doesn't exist
touch "$BLOCKED_LOG"

# Read the proposed tool use from stdin
INPUT=$(cat)

# Extract the command from JSON input (simple parsing)
COMMAND=$(echo "$INPUT" | grep -oP '"command":\s*"\K[^"]+' || echo "")

if [[ -z "$COMMAND" ]]; then
  # No command found, allow
  echo "$INPUT"
  exit 0
fi

# Normalize for checking
CHECK_CMD=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# Check for blocked patterns
BLOCK_REASON=""

# Pattern 1: rm -rf (recursive force delete)
if echo "$CHECK_CMD" | grep -qE '\brm\s+-[a-z]*f[a-z]*\s+.*'; then
  if echo "$CHECK_CMD" | grep -qE '\brm\s+(-[a-z]*r[a-z]*f| -[a-z]*fr[a-z]*)\s+.*'; then
    BLOCK_REASON="Blocked 'rm -rf': Recursive force deletion is dangerous and can destroy the project or system files."
  fi
fi

# Pattern 2: DROP TABLE
if echo "$CHECK_CMD" | grep -qE '\bdrop\s+table\b'; then
  BLOCK_REASON="Blocked 'DROP TABLE': Dropping tables destroys data permanently. Use migrations or ALTER TABLE instead."
fi

# Pattern 3: git push --force
if echo "$CHECK_CMD" | grep -qE '\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b'; then
  BLOCK_REASON="Blocked 'git push --force': Force pushing can overwrite teammates' work. Use git push --force-with-lease instead."
fi

# Pattern 4: TRUNCATE
if echo "$CHECK_CMD" | grep -qE '\btruncate\s+(table\s+)?\w+'; then
  BLOCK_REASON="Blocked 'TRUNCATE': Truncating tables deletes all data without logging individual rows."
fi

# Pattern 5: DELETE FROM without WHERE
if echo "$CHECK_CMD" | grep -qE '\bdelete\s+from\s+\w+\s*;?\s*$'; then
  BLOCK_REASON="Blocked 'DELETE FROM' without WHERE: This deletes all rows in a table. Add a WHERE clause to limit the scope."
fi

# If blocked, log and reject
if [[ -n "$BLOCK_REASON" ]]; then
  TIMESTAMP=$(date -Iseconds)
  echo "[$TIMESTAMP] PROJECT: ${PROJECT_PATH}" >> "$BLOCKED_LOG"
  echo "[$TIMESTAMP] BLOCKED: ${COMMAND}" >> "$BLOCKED_LOG"
  echo "[$TIMESTAMP] REASON:  ${BLOCK_REASON}" >> "$BLOCKED_LOG"
  echo "" >> "$BLOCKED_LOG"

  # Return modified JSON with blocked command explanation
  cat <<EOF
{
  "blocked": true,
  "reason": "$BLOCK_REASON",
  "original_command": "$COMMAND",
  "suggestion": "This command was blocked for safety. Please review the operation and use a safer alternative if possible.",
  "log_file": "$BLOCKED_LOG"
}
EOF
  exit 0
fi

# Command is safe, pass through
 echo "$INPUT"
