#!/bin/bash

# Claude Code pre-tool-use hook: Dangerous Command Guard
# Intercepts destructive commands before execution

set -euo pipefail

# Log file for blocked commands
BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$BLOCKED_LOG")"

# Read JSON from stdin
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Default: allow
DECISION="allow"
REASON=""

# Only check Bash tool
if [[ "$TOOL_NAME" == "Bash" ]]; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

  # Dangerous patterns
  DANGEROUS_PATTERNS=(
    "rm -rf /"                      # Delete root
    "rm -rf /\*"                    # Delete root (wildcard)
    "rm -rf //\*"                   # Delete root (double slash)
    "DROP TABLE"                    # SQL: drop table
    "DROP DATABASE"                 # SQL: drop database
    "DROP SCHEMA"                   # SQL: drop schema
    "TRUNCATE"                      # SQL: truncate table
    "git push --force"              # Git force push
    "git push -f"                   # Git force push (short)
    "DELETE FROM.*;"                # SQL: delete all (no WHERE)
    "DELETE FROM\s+\w+\s*$"         # SQL: delete all (end of line)
  )

  # Check each pattern
  for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qE "$pattern"; then
      DECISION="block"
      REASON="Dangerous command detected: pattern '$pattern' matched"
      break
    fi
  done

  # Block if blocked
  if [[ "$DECISION" == "block" ]]; then
    TIMESTAMP=$(date -Iseconds)
    PROJECT_PATH="$(pwd)"
    echo "[${TIMESTAMP}] [${PROJECT_PATH}] ${COMMAND}" >> "$BLOCKED_LOG"
  fi
fi

# Output decision
if [[ "$DECISION" == "block" ]]; then
  jq -n \
    --arg decision "block" \
    --arg reason "$REASON" \
    '{decision: $decision, reason: $reason}'
else
  jq -n '{decision: "allow"}'
fi

exit 0
