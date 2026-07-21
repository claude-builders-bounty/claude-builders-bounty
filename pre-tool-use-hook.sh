#!/bin/bash
set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
RED='\033[31m'
NC='\033[0m'

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" 2>/dev/null)

if [ -z "$COMMAND" ]; then
    exit 0
fi

block() {
    local reason="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local project_path
    project_path=$(pwd)

    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$timestamp] BLOCKED: $reason | command: $COMMAND | project: $project_path" >> "$LOG_FILE"

    echo -e "${RED}[BLOCKED] $reason${NC}" >&2
    echo -e "${RED}Command: $COMMAND${NC}" >&2

    cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"$reason"}}
EOF
    exit 0
}

if echo "$COMMAND" | grep -qE 'rm[[:space:]]+-[a-zA-Z]*(r[a-zA-Z]*f|f[a-zA-Z]*r)[a-zA-Z]*'; then
    block "rm -rf (recursive force delete)"
fi

if echo "$COMMAND" | grep -qiE 'DROP\s+TABLE'; then
    block "DROP TABLE (SQL destructive operation)"
fi

if echo "$COMMAND" | grep -qE '\bgit\s+push\b(\s+.*)?\s(-f|--force|--force-with-lease)(\s|$)'; then
    block "git push --force (force push)"
fi

if echo "$COMMAND" | grep -qiE '\bTRUNCATE\b'; then
    block "TRUNCATE (SQL destructive operation)"
fi

if echo "$COMMAND" | grep -qiE 'DELETE\s+FROM'; then
    if ! echo "$COMMAND" | grep -qiE '\bWHERE\b'; then
        block "DELETE FROM without WHERE clause (dangerous SQL operation)"
    fi
fi

exit 0
