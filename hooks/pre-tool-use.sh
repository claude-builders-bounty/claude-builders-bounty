#!/bin/bash
HOOK_DIR="$HOME/.claude/hooks"
LOG_FILE="$HOOK_DIR/blocked.log"
PROJECT_PATH="$(pwd)"

mkdir -p "$HOOK_DIR"
read -r TOOL_INPUT

if echo "$TOOL_INPUT" | grep -q '"tool":"bash"'; then
    COMMAND=$(echo "$TOOL_INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('input',{}).get('command',''))" 2>/dev/null)
    
    DANGEROUS_PATTERNS=("rm -rf" "DROP TABLE" "git push --force" "TRUNCATE" "DELETE FROM")
    
    for pattern in "${DANGEROUS_PATTERNS[@]}"; do
        if echo "$COMMAND" | grep -qi "$pattern"; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED: $COMMAND | Project: $PROJECT_PATH" >> "$LOG_FILE"
            echo "{\"decision\":\"deny\",\"reason\":\"⚠️ Command blocked: '$pattern'\"}"
            exit 0
        fi
    done
fi

echo '{"decision":"allow"}'
