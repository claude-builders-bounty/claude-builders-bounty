#!/usr/bin/env bash
# Pre-tool-use hook for Claude Code
# Blocks destructive bash commands before they execute.
# Install: install -m 755 block-destructive.sh ~/.claude/hooks/pre-tool-use
set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

INPUT=$(cat)

# Extract the command from the PreToolUse event JSON
COMMAND=$(echo "$INPUT" | python3 -c "
import json,sys
try:
    data = json.load(sys.stdin)
    tool = data.get('tool', {}) or data.get('tool_use', {})
    inp = tool.get('input', {}) or {}
    cmd = inp.get('command', '') or inp.get('cmd', '') or inp.get('value', '')
    print(cmd.strip())
except:
    print('')
" 2>/dev/null || true)

if [ -z "$COMMAND" ]; then
    echo '{"permissionDecision": "allow"}'
    exit 0
fi

# Normalize command
CMD_NORM=$(echo "$COMMAND" | sed -E 's/^[[:space:]]+//' | tr -s ' ')

BLOCKED=0
REASON=""

# Pattern 1: rm -rf (destructive recursion)
if echo "$CMD_NORM" | grep -qiE '(^|[;&|`(])[[:space:]]*rm[[:space:]]+-[rR][fF]'; then
    BLOCKED=1; REASON="rm -rf (recursive force delete)"
fi

# Pattern 2: git push --force
if echo "$CMD_NORM" | grep -qiE '(^|[;&|`(])[[:space:]]*git[[:space:]]+push.*(--force|-f\b)'; then
    BLOCKED=1; REASON="git push --force (forced push)"
fi

# Pattern 3: DROP TABLE
if echo "$CMD_NORM" | grep -qiE '\bDROP\s+TABLE\b'; then
    BLOCKED=1; REASON="DROP TABLE (database table deletion)"
fi

# Pattern 4: TRUNCATE TABLE
if echo "$CMD_NORM" | grep -qiE '\bTRUNCATE\s+TABLE\b'; then
    BLOCKED=1; REASON="TRUNCATE TABLE (database truncation)"
fi

# Pattern 5: DELETE FROM without WHERE
if echo "$CMD_NORM" | grep -qiE '\bDELETE\s+FROM\b'; then
    if ! echo "$CMD_NORM" | grep -qiE '\bWHERE\b'; then
        BLOCKED=1; REASON="DELETE FROM without WHERE clause (mass deletion)"
    fi
fi

# Pattern 6: sudo rm -rf
if echo "$CMD_NORM" | grep -qiE '(^|[;&|`(])[[:space:]]*sudo[[:space:]]+rm[[:space:]]+-[rR][fF]'; then
    BLOCKED=1; REASON="sudo rm -rf (privileged destructive delete)"
fi

if [ "$BLOCKED" -eq 1 ]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    PROJECT_PATH="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    echo "[$TIMESTAMP] BLOCKED: $COMMAND | reason: $REASON | path: $PROJECT_PATH" >> "$LOG_FILE"
    # Output blocked decision with clear message
    cat <<EOJSON
{"permissionDecision": "block", "responseMessage": "⛔ BLOCKED: $REASON\n\nCommand: $COMMAND\nLogged to: $LOG_FILE"}
EOJSON
    exit 0
fi

echo '{"permissionDecision": "allow"}'
