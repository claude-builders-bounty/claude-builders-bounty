#!/usr/bin/env bash
# pre-tool-use.sh — Claude Code pre-tool-use hook
# Blocks dangerous bash commands before execution.
#
# Install:
#   mkdir -p ~/.claude/hooks/pre-tool-use && cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use/ && chmod +x ~/.claude/hooks/pre-tool-use/pre-tool-use.sh

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# ── Read JSON input from stdin ──────────────────────────────────────────────
INPUT=""
while IFS= read -r line; do
  INPUT+="$line"
done

# Extract tool name and command from the JSON
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)

# Only inspect Bash tool invocations
if [[ "$TOOL_NAME" != "Bash" ]]; then
  exit 0  # Not a bash command, allow
fi

# Get project path (current working directory)
PROJECT_PATH="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── Dangerous pattern checks ────────────────────────────────────────────────

# Normalize: collapse whitespace, lowercase for pattern matching
NORMALIZED=$(echo "$COMMAND" | tr -s ' ' | tr '[:upper:]' '[:lower:]')

check_pattern() {
  local pattern="$1"
  local reason="$2"
  if echo "$NORMALIZED" | grep -qE "$pattern"; then
    log_blocked "$reason"
    echo "🚫 BLOCKED: $reason" >&2
    echo "" >&2
    echo "The command: $COMMAND" >&2
    echo "Was blocked because: $reason" >&2
    echo "If this is intentional, use a safer alternative or run it manually." >&2
    exit 2  # Exit code 2 = block the tool call
  fi
}

log_blocked() {
  local reason="$1"
  echo "[$TIMESTAMP] BLOCKED | Command: $COMMAND | Reason: $reason | Path: $PROJECT_PATH" >> "$LOG_FILE"
}

# 1. rm -rf (recursive force delete)
check_pattern 'rm\s+.*-.*r.*f|rm\s+.*-.*f.*r|rm\s+--recursive\s+--force|rm\s+-rf' \
  "Recursive force delete (rm -rf) — risk of irreversible data loss"

# 2. DROP TABLE
check_pattern 'drop\s+table' \
  "DROP TABLE — will permanently delete a database table"

# 3. git push --force
check_pattern 'git\s+push\s+.*--force|git\s+push\s+.*-f\b|git\s+push\s+-f\b' \
  "Force push (git push --force) — will overwrite remote history"

# 4. TRUNCATE
check_pattern 'truncate\s+table|truncate\s' \
  "TRUNCATE — will delete all rows from a table"

# 5. DELETE FROM without WHERE clause
check_pattern 'delete\s+from\s+\S+\s*;?\s*$' \
  "DELETE FROM without WHERE — will delete ALL rows from the table"

# 6. Additional safety: DELETE FROM ... ; without WHERE (multiline trick)
if echo "$COMMAND" | grep -qiE 'delete\s+from' && ! echo "$COMMAND" | grep -qiE 'where'; then
  check_pattern 'delete\s+from' \
    "DELETE FROM without WHERE clause — will delete ALL rows"
fi

# All checks passed — allow the command
exit 0
