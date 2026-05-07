#!/usr/bin/env bash
# pre-tool-use — Claude Code safety hook
# Blocks dangerous bash commands before they execute.
# Install: cp this file to ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
#
# Environment variables available in pre-tool-use hooks:
#   CLAUDE_TOOL_NAME   — the tool being called (e.g., "Bash", "FileWrite")
#   CLAUDE_TOOL_INPUT  — the full tool input as JSON
#   CLAUDE_PROJECT_DIR — the project root directory

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Only intercept Bash tool calls
if [ "${CLAUDE_TOOL_NAME:-}" != "Bash" ]; then
  exit 0
fi

# Extract the command from the JSON input using Python for reliability
COMMAND=$(python3 -c "
import sys, json
try:
    inp = json.loads('${CLAUDE_TOOL_INPUT//\'/\\\'}')
    print(inp.get('command', ''))
except:
    print('')
" 2>/dev/null)

# If Python extraction failed, fall back to raw input
if [ -z "$COMMAND" ]; then
  COMMAND="${CLAUDE_TOOL_INPUT:-}"
fi

# Normalize: trim whitespace and lowercase for matching
TRIMMED=$(echo "$COMMAND" | xargs)
LOWERED=$(echo "$TRIMMED" | tr '[:upper:]' '[:lower:]')

# ─── Dangerous patterns to block ────────────────────────────────────────────

blocked_reason=""

# 1. rm -rf (recursive force delete)
if echo "$LOWERED" | grep -Pq '(^|\s)rm\s+(-[rf]+|-[rf]\s+\S+|--recursive\s+--force)'; then
  blocked_reason="Recursive force delete (rm -rf) is blocked. Use a trash directory or 'rm -r' with confirmation."
fi

# 2. DROP TABLE
if echo "$LOWERED" | grep -Pq 'drop\s+table'; then
  blocked_reason="'DROP TABLE' is blocked. Use 'DROP TABLE IF EXISTS' only after confirming the table name in a migration file."
fi

# 3. git push --force / git push -f
if echo "$LOWERED" | grep -Pq 'git\s+push\s+.*(--force|-f)\b'; then
  blocked_reason="'git push --force' is blocked. Use 'git push --force-with-lease' instead."
fi

# 4. TRUNCATE
if echo "$LOWERED" | grep -Pq 'truncate\s+'; then
  blocked_reason="'TRUNCATE' is blocked. Use 'DELETE FROM' with a WHERE clause instead."
fi

# 5. DELETE FROM without WHERE
if echo "$LOWERED" | grep -Pq 'delete\s+from\s+\w+\s*$'; then
  blocked_reason="'DELETE FROM' without a WHERE clause is blocked. Add a WHERE clause to limit the scope."
fi

# ─── Take action ────────────────────────────────────────────────────────────

if [ -n "$blocked_reason" ]; then
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$TIMESTAMP] BLOCKED: $COMMAND" >> "$LOG_FILE"
  echo "[$TIMESTAMP] Reason: $blocked_reason" >> "$LOG_FILE"
  echo "" >> "$LOG_FILE"

  cat <<EOF

╔══════════════════════════════════════════════════════════════╗
║  🛑 COMMAND BLOCKED BY SAFETY HOOK                          ║
╠══════════════════════════════════════════════════════════════╣
║  $blocked_reason
║
║  Logged to: ~/.claude/hooks/blocked.log
╚══════════════════════════════════════════════════════════════╝

EOF
  exit 1
fi

exit 0
