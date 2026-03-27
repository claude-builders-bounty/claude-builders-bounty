#!/usr/bin/env bash
# safety-hook.sh — Claude Code pre-tool-use hook
# Blocks destructive bash commands before they are executed.
#
# Install:
#   mkdir -p ~/.claude/hooks
#   cp safety-hook.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
#
# The hook reads JSON from stdin containing the tool call details.
# Exit code 0 = allow, exit code 1 = block.

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"

# Read the JSON input from stdin
INPUT="$(cat)"

# Extract the command from the tool input
COMMAND="$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)"
PROJECT_PATH="$(echo "$INPUT" | jq -r '.tool_input.workdir // .cwd // "."' 2>/dev/null)"

if [[ -z "$COMMAND" ]]; then
  # No command found — allow (not a bash tool call)
  exit 0
fi

BLOCKED=0
REASON=""

# --- Destructive pattern checks ---

# 1. rm -rf (recursive force delete)
if echo "$COMMAND" | grep -qiE '(^|[;&|`])\s*rm\s+.*-[^\s]*r[^\s]*f|(^|[;&|`])\s*rm\s+.*-[^\s]*f[^\s]*r'; then
  BLOCKED=1
  REASON="Dangerous 'rm -rf' detected — recursive force-delete can destroy data irreversibly"
fi

# 2. DROP TABLE
if echo "$COMMAND" | grep -qiE 'drop\s+table'; then
  BLOCKED=1
  REASON="SQL 'DROP TABLE' detected — this permanently deletes a database table and its data"
fi

# 3. git push --force (rewrites remote history)
if echo "$COMMAND" | grep -qiE 'git\s+push\s+.*--force|--force-push|git\s+push\s+-f\b'; then
  BLOCKED=1
  REASON="'git push --force' detected — this rewrites remote history and can erase others' work"
fi

# 4. TRUNCATE
if echo "$COMMAND" | grep -qiE 'truncate\s'; then
  BLOCKED=1
  REASON="SQL 'TRUNCATE' detected — this irreversibly deletes all rows from a table"
fi

# 5. DELETE FROM without WHERE clause
if echo "$COMMAND" | grep -qiE 'delete\s+from' && ! echo "$COMMAND" | grep -qiE 'delete\s+from\s+\S+\s+where'; then
  BLOCKED=1
  REASON="SQL 'DELETE FROM' without WHERE clause detected — this would delete ALL rows from the table"
fi

# --- Log and decide ---
TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

if [[ "$BLOCKED" -eq 1 ]]; then
  # Ensure log directory exists
  mkdir -p "$(dirname "$LOG_FILE")"

  # Log the blocked attempt
  echo "${TIMESTAMP} | BLOCKED | project=${PROJECT_PATH} | command=${COMMAND}" >> "$LOG_FILE"

  # Output block reason as JSON for Claude Code
  jq -n --arg reason "$REASON" '{
    "decision": "block",
    "reason": $reason
  }'
  exit 1
fi

# Command is safe — allow it
exit 0
