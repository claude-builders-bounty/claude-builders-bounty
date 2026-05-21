#!/usr/bin/env bash
# pre-tool-use hook for Claude Code
# Blocks dangerous bash commands before execution
# Install: cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh

HOOK_NAME="block-destructive"
LOG_FILE="$HOME/.claude/hooks/blocked.log"
BLOCK_PATTERNS=(
    "rm\s+-rf\s+/"
    "rm\s+-rf\s+~"
    "rm\s+-rf\s+\*"
    "rm\s+--recursive\s+--force\s+/"
    "DROP\s+TABLE"
    "TRUNCATE\s+TABLE"
    "TRUNCATE\s+[a-zA-Z_]"
    "DELETE\s+FROM"
    "git\s+push\s+(-f|--force)"
    "git\s+push\s+--force-with-lease"
    "rm\s+-rf\s+[^/]"  
)

mkdir -p "$(dirname "$LOG_FILE")"

INPUT=$(cat)
TOOL=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)

if [ "$TOOL" != "Bash" ]; then
    echo "$INPUT"
    exit 0
fi

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

if [ -z "$COMMAND" ]; then
    echo "$INPUT"
    exit 0
fi

check_delete_from() {
    echo "$1" | grep -qiE "DELETE\s+FROM" && ! echo "$1" | grep -qiE "WHERE\s"
}

for pattern in "${BLOCK_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        PROJECT_PATH="$(pwd)"
        echo "[$TIMESTAMP] Blocked command: $COMMAND | Project: $PROJECT_PATH" >> "$LOG_FILE"
        python3 -c "
import sys, json
print(json.dumps({
    'decision': 'block',
    'reason': f'Blocked by $HOOK_NAME hook: destructive command detected. The command \"{sys.argv[1]}\" matches a blocked pattern. If you truly need to run this, use a different approach or ask the user to explicitly allow it.'
}))" "$COMMAND"
        exit 0
    fi
done

if check_delete_from "$COMMAND"; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    PROJECT_PATH="$(pwd)"
    echo "[$TIMESTAMP] Blocked command: $COMMAND | Project: $PROJECT_PATH" >> "$LOG_FILE"
    python3 -c "
import sys, json
print(json.dumps({
    'decision': 'block',
    'reason': f'Blocked by $HOOK_NAME hook: DELETE FROM without WHERE clause detected. The command \"{sys.argv[1]}\" could delete all rows. Add a WHERE clause to proceed.'
}))" "$COMMAND"
    exit 0
fi

echo "$INPUT"