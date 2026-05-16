#!/usr/bin/env bash
# Claude Code pre-tool-use hook: Block destructive bash commands
# Install: cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh
# See README.md for hooks.json setup

set -euo pipefail

# Read the tool input from stdin (JSON), save to temp file for multiple reads
INPUT=$(cat)

# Extract the command using jq
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$COMMAND" ]; then
  echo '{"decision": "allow"}'
  exit 0
fi

# Normalize for matching
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

BLOCKED=0
REASON=""

# Pattern 1: rm -rf
if echo "$CMD_LOWER" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s)'; then
  BLOCKED=1
  REASON="rm -rf detected: This will recursively force-delete files and cannot be undone."
fi

# Pattern 1b: rm -rf / or rm -rf ~ or rm -rf /*
if [ "$BLOCKED" -eq 0 ]; then
  if echo "$CMD_LOWER" | grep -qE 'rm\s+-[rf]+\s+(/|~|/\*)'; then
    BLOCKED=1
    REASON="rm -rf with root/home path detected: This would destroy critical files."
  fi
fi

# Pattern 2: DROP TABLE / DROP DATABASE / DROP SCHEMA
if [ "$BLOCKED" -eq 0 ]; then
  if echo "$CMD_LOWER" | grep -qE 'drop\s+(table|database|schema)\s'; then
    BLOCKED=1
    REASON="DROP TABLE/DATABASE/SCHEMA detected: This will permanently delete database objects."
  fi
fi

# Pattern 3: git push --force / git push -f
if [ "$BLOCKED" -eq 0 ]; then
  if echo "$CMD_LOWER" | grep -qE 'git\s+push\s+.*(--force|-f\b)'; then
    BLOCKED=1
    REASON="git push --force detected: This can overwrite remote history and lose others' work."
  fi
fi

# Pattern 4: TRUNCATE
if [ "$BLOCKED" -eq 0 ]; then
  if echo "$CMD_LOWER" | grep -qE 'truncate(\s+table)?\s+\S'; then
    BLOCKED=1
    REASON="TRUNCATE detected: This will delete all rows from a table without individual row logging."
  fi
fi

# Pattern 5: DELETE FROM without WHERE
if [ "$BLOCKED" -eq 0 ]; then
  if echo "$CMD_LOWER" | grep -qE 'delete\s+from\s+\S+'; then
    if ! echo "$CMD_LOWER" | grep -qE 'delete\s+from\s+\S+\s.*where\s'; then
      BLOCKED=1
      REASON="DELETE FROM without WHERE detected: This will delete ALL rows in the table."
    fi
  fi
fi

# Handle result
if [ "$BLOCKED" -eq 1 ]; then
  # Log the blocked attempt
  LOG_DIR="$HOME/.claude/hooks"
  LOG_FILE="$LOG_DIR/blocked.log"
  mkdir -p "$LOG_DIR"
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  PROJECT_PATH=$(pwd)
  echo "[$TIMESTAMP] BLOCKED | cmd='$COMMAND' | project='$PROJECT_PATH' | reason='$REASON'" >> "$LOG_FILE"

  # Escape reason for JSON
  REASON_ESCAPED=$(echo "$REASON" | sed 's/"/\\"/g')
  echo "{\"decision\": \"block\", \"reason\": \"$REASON_ESCAPED\"}"
  exit 0
fi

# Allow the command
echo '{"decision": "allow"}'
