#!/usr/bin/env bash
# Safe Claude: Pre-Tool-Use Hook for Claude Code
# Blocks destructive bash commands before they execute.
# Install: mkdir -p ~/.claude/hooks && cp block-destructive-commands.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-commands.sh

set -euo pipefail

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null)

[ -z "$COMMAND" ] && exit 0

BLOCKED=""
REASON=""

if echo "$COMMAND" | grep -qiE 'rm\\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\\b' || echo "$COMMAND" | grep -qiE 'rm\\s+--recursive\\s+--force'; then
    BLOCKED="rm -rf"
    REASON="Recursive force delete detected."
fi

if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiE 'DROP\\s+TABLE'; then
    BLOCKED="DROP TABLE"
    REASON="SQL DROP TABLE detected."
fi

if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiE 'git\\s+push\\s+.*(--force|-f\\b)'; then
    BLOCKED="git push --force"
    REASON="Force push detected."
fi

if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiE 'TRUNCATE\\s+TABLE'; then
    BLOCKED="TRUNCATE TABLE"
    REASON="SQL TRUNCATE detected."
fi

if [ -z "$BLOCKED" ] && echo "$COMMAND" | grep -qiE 'DELETE\\s+FROM'; then
    if ! echo "$COMMAND" | grep -qiE 'DELETE\\s+FROM.*WHERE'; then
        BLOCKED="DELETE FROM (no WHERE)"
        REASON="DELETE FROM without WHERE clause."
    fi
fi

PROJECT_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('cwd', d.get('cwd', 'unknown')))
except:
    print('unknown')
" 2>/dev/null)

if [ -n "$BLOCKED" ]; then
    LOG_DIR="$HOME/.claude/hooks"
    mkdir -p "$LOG_DIR"
    TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    echo "[$TIMESTAMP] BLOCKED: $BLOCKED | Command: $COMMAND | Project: $PROJECT_PATH" >> "$LOG_DIR/blocked.log"
    echo "{\"decision\":\"block\",\"reason\":\"BLOCKED by safe-claude: $BLOCKED. $REASON Logged to ~/.claude/hooks/blocked.log\"}"
    exit 0
fi

exit 0
