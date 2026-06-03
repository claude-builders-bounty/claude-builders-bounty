#!/bin/bash
# pre-tool-use hook: blocks destructive bash commands
# Place in ~/.claude/hooks/pre-tool-use/block-destructive.sh

set -euo pipefail

# Read stdin (JSON tool call from Claude Code)
INPUT=$(cat)

# Parse the bash command from the tool input
COMMAND=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    # Extract bash command - it could be in different places depending on the tool
    if isinstance(data, dict):
        # Direct tool call format
        cmd = data.get('command') or data.get('input') or data.get('bash') or ''
        # Also check nested params
        if not cmd and 'params' in data:
            params = data['params']
            cmd = params.get('command') or params.get('input') or params.get('bash') or ''
        print(cmd)
    else:
        print('')
except:
    print('')
" 2>/dev/null || echo "")

# If no command found, allow
if [ -z "$COMMAND" ]; then
  echo '{"is_approved": true}'
  exit 0
fi

BLOCKED=false
REASON=""

# Pattern 1: rm -rf (recursive force delete)
if echo "$COMMAND" | grep -qP '(^|\s)(rm\s+.*-[rRfF]+[rRfF-]*|rm\s+.*--recursive\s+.*--force|rm\s+.*--force\s+.*--recursive)'; then
  BLOCKED=true
  REASON="Dangerous recursive delete: '$COMMAND'"
fi

# Pattern 2: git push --force (force push)
if echo "$COMMAND" | grep -qP '(^|\s)git\s+push\s+.*(--force|-f)\b'; then
  BLOCKED=true
  REASON="Force push detected: '$COMMAND'"
fi

# Pattern 3: DROP TABLE (SQL destructive)
if echo "$COMMAND" | grep -qiP '(^|\s)(DROP\s+TABLE|DROP\s+DATABASE|DROP\s+INDEX)\b'; then
  BLOCKED=true
  REASON="Destructive SQL: '$COMMAND'"
fi

# Pattern 4: TRUNCATE (SQL destructive)
if echo "$COMMAND" | grep -qiP '(^|\s)TRUNCATE\b'; then
  BLOCKED=true
  REASON="Destructive SQL: '$COMMAND'"
fi

# Pattern 5: DELETE FROM without WHERE (dangerous delete without filter)
if echo "$COMMAND" | grep -qiP '(^|\s)DELETE\s+FROM\b'; then
  if ! echo "$COMMAND" | grep -qiP '\bWHERE\b'; then
    BLOCKED=true
    REASON="DELETE FROM without WHERE clause: '$COMMAND'"
  fi
fi

# Log blocked attempt
if [ "$BLOCKED" = true ]; then
  LOG_FILE="$HOME/.claude/hooks/blocked.log"
  LOG_DIR="$(dirname "$LOG_FILE")"
  mkdir -p "$LOG_DIR"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED | cwd: $(pwd) | cmd: $COMMAND | reason: $REASON" >> "$LOG_FILE"
  # Also print to stderr for immediate feedback
  echo "🔒 BLOCKED: $REASON" >&2
  echo "   Logged to: $LOG_FILE" >&2
  echo "   To allow, run: git config --global hooks.allow-danger 'command'" >&2
  
  echo "{\"is_approved\": false, \"msg\": \"$REASON\"}"
  exit 1
fi

# Allow the command
echo '{"is_approved": true}'
exit 0
