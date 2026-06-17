#!/usr/bin/env bash
# Pre-tool-use hook for Claude Code
# Blocks dangerous bash commands before execution.
#
# Installation:
#   mkdir -p ~/.claude/hooks
#   cp pre-tool-use-hook.sh ~/.claude/hooks/pre-tool-use-hook.sh
#   chmod +x ~/.claude/hooks/pre-tool-use-hook.sh
#
# Add to ~/.claude/settings.json:
# {
#   "hooks": {
#     "preToolUse": "~/.claude/hooks/pre-tool-use-hook.sh"
#   }
# }

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
PROJECT_PATH="$(pwd)"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Read the command from stdin (Claude Code passes JSON)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Normalize command for checking
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# Blocked patterns
BLOCKED=0
BLOCK_REASON=""

# Check for dangerous patterns
if echo "$CMD_LOWER" | grep -qE 'rm\s+-rf\s+/|rm\s+-rf\s+\*|rm\s+-rf\s+\.'; then
  BLOCKED=1
  BLOCK_REASON="Dangerous rm -rf detected"
elif echo "$CMD_LOWER" | grep -qE 'drop\s+table\s+'; then
  BLOCKED=1
  BLOCK_REASON="DROP TABLE detected"
elif echo "$CMD_LOWER" | grep -qE 'git\s+push\s+--force'; then
  BLOCKED=1
  BLOCK_REASON="git push --force detected"
elif echo "$CMD_LOWER" | grep -qE 'truncate\s+table\s+'; then
  BLOCKED=1
  BLOCK_REASON="TRUNCATE TABLE detected"
elif echo "$CMD_LOWER" | grep -qE 'delete\s+from\s+\w+\s*;'; then
  BLOCKED=1
  BLOCK_REASON="DELETE FROM without WHERE clause detected"
elif echo "$CMD_LOWER" | grep -qE 'delete\s+from\s+\w+\s*$'; then
  BLOCKED=1
  BLOCK_REASON="DELETE FROM without WHERE clause detected"
fi

if [ "$BLOCKED" -eq 1 ]; then
  # Log the blocked attempt
  mkdir -p "$(dirname "$LOG_FILE")"
  echo "[$TIMESTAMP] BLOCKED: $BLOCK_REASON | Command: $COMMAND | Project: $PROJECT_PATH" >> "$LOG_FILE"

  # Output error message to stderr (Claude will see this)
  echo "🚫 BLOCKED: $BLOCK_REASON" >&2
  echo "   Command: $COMMAND" >&2
  echo "   This attempt has been logged to $LOG_FILE" >&2
  echo "   If you need to run this command, please do it manually outside of Claude Code." >&2

  # Exit with error to block the tool use
  exit 1
fi

# Command is safe — allow it
exit 0
