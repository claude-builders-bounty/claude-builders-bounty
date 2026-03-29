#!/usr/bin/env bash
# Claude Code pre-tool-use hook: blocks destructive bash commands
# Bounty #3 — https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
PROJECT_PATH="${PWD}"

# Read the tool input from stdin (JSON from Claude Code hook system)
INPUT=$(cat)

# Extract the tool name and command
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only inspect Bash tool calls
if [[ "$TOOL_NAME" != "Bash" ]] || [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Normalize: lowercase for SQL checks, original for shell checks
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

BLOCKED=""
REASON=""

# 1. rm -rf
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\b'; then
  BLOCKED="$COMMAND"
  REASON="Recursive force delete (rm -rf) is blocked to prevent accidental data loss."
fi

# 2. git push --force (including -f shorthand)
if [[ -z "$BLOCKED" ]] && echo "$COMMAND" | grep -qE 'git\s+push\s+.*(-f|--force)\b'; then
  BLOCKED="$COMMAND"
  REASON="Force push (git push --force) is blocked to prevent overwriting remote history."
fi

# 3. DROP TABLE
if [[ -z "$BLOCKED" ]] && echo "$CMD_LOWER" | grep -qE '\bdrop\s+table\b'; then
  BLOCKED="$COMMAND"
  REASON="DROP TABLE is blocked to prevent accidental schema destruction."
fi

# 4. TRUNCATE
if [[ -z "$BLOCKED" ]] && echo "$CMD_LOWER" | grep -qE '\btruncate\b'; then
  BLOCKED="$COMMAND"
  REASON="TRUNCATE is blocked to prevent mass data deletion."
fi

# 5. DELETE FROM without WHERE
if [[ -z "$BLOCKED" ]]; then
  if echo "$CMD_LOWER" | grep -qE '\bdelete\s+from\b'; then
    if ! echo "$CMD_LOWER" | grep -qE '\bdelete\s+from\b.*\bwhere\b'; then
      BLOCKED="$COMMAND"
      REASON="DELETE FROM without a WHERE clause is blocked to prevent wiping entire tables."
    fi
  fi
fi

# If a destructive command was detected, block it
if [[ -n "$BLOCKED" ]]; then
  # Ensure log directory exists
  mkdir -p "$(dirname "$LOG_FILE")"

  # Log the blocked attempt
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "${TIMESTAMP} | BLOCKED | ${BLOCKED} | ${PROJECT_PATH}" >> "$LOG_FILE"

  # Output the block reason (Claude Code reads this)
  echo "BLOCKED: ${REASON}"
  echo "The attempted command has been logged to ${LOG_FILE}"
  exit 2
fi

exit 0
