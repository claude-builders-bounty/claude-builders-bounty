#!/usr/bin/env bash
# Wrapper that delegates to the Python hook.
# Falls back to a basic built-in check if Python is unavailable.

HOOK_DIR="${HOME}/.claude/hooks"
PYTHON_HOOK="${HOOK_DIR}/block-destructive-commands.py"

if command -v python3 &> /dev/null && [ -f "$PYTHON_HOOK" ]; then
    exec python3 "$PYTHON_HOOK"
elif command -v python &> /dev/null && [ -f "$PYTHON_HOOK" ]; then
    exec python "$PYTHON_HOOK"
else
    # Minimal bash fallback: block the most dangerous patterns
    INPUT=$(cat)
    COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "$INPUT" | python -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

    if echo "$COMMAND" | grep -qiE 'rm -rf /|DROP TABLE|TRUNCATE|DELETE FROM' 2>/dev/null; then
        echo '{"continue": false, "decision": "block", "reason": "destructive command detected"}'
        exit 2
    fi
    echo '{"continue": true}'
    exit 0
fi
