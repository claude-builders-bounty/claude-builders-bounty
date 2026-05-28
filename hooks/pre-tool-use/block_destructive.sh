#!/bin/bash
# Pre-tool-use hook: block destructive bash commands
# Install: cp -r hooks/pre-tool-use ~/.claude/hooks/

COMMAND="$1"
BLOCKED_LOG="$HOME/.claude/hooks/blocked.log"
PROJECT_PATH="${2:-$(pwd)}"

# Patterns to block
PATTERNS=(
    "rm\s+-rf"
    "DROP\s+TABLE"
    "git\s+push\s+--force"
    "TRUNCATE"
    "DELETE\s+FROM\s+WHERE"
)

blocked=false
for pattern in "${PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -Ei "$pattern" > /dev/null 2>&1; then
        blocked=true
        break
    fi
done

if [ "$blocked" = true ]; then
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] BLOCKED: $COMMAND | Project: $PROJECT_PATH" >> "$BLOCKED_LOG"
    echo "Hook: Destructive command blocked."
    echo "This command was blocked by the pre-tool-use hook because it matches a dangerous pattern."
    echo "If you need to proceed, please review the command and run it manually with caution."
    exit 1
fi

exit 0
