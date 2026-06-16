#!/usr/bin/env bash
# Claude Code pre-tool-use hook: blocks destructive bash commands
# Install: cp block-destructive.sh ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Read the tool input from stdin (Claude Code passes JSON)
INPUT=$(cat)

# Extract the command from the JSON input
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    cmd = data.get('tool_input', {}).get('command', '') or data.get('input', {}).get('command', '')
    print(cmd)
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
    exit 0
fi

BLOCKED=false
REASON=""

# Check destructive patterns
if echo "$COMMAND" | grep -qiE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|(-[a-zA-Z]*f[a-zA-Z]*r))'; then
    BLOCKED=true
    REASON="Blocked: 'rm -rf' is destructive and irreversible"
elif echo "$COMMAND" | grep -qiE 'DROP\s+TABLE'; then
    BLOCKED=true
    REASON="Blocked: 'DROP TABLE' permanently deletes database tables"
elif echo "$COMMAND" | grep -qiE 'git\s+push\s+.*--force'; then
    BLOCKED=true
    REASON="Blocked: 'git push --force' overwrites remote history"
elif echo "$COMMAND" | grep -qiE 'TRUNCATE\s+(TABLE\s+)?[a-zA-Z_]'; then
    BLOCKED=true
    REASON="Blocked: 'TRUNCATE' removes all rows from a table"
elif echo "$COMMAND" | grep -qiE 'DELETE\s+FROM\s+[a-zA-Z_]' && ! echo "$COMMAND" | grep -qiE 'WHERE\s+'; then
    BLOCKED=true
    REASON="Blocked: 'DELETE FROM' without WHERE clause deletes all rows"
fi

if [ "$BLOCKED" = true ]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    PROJECT_PATH=$(pwd)
    echo "${TIMESTAMP} | ${PROJECT_PATH} | ${COMMAND}" >> "$LOG_FILE"
    
    # Output block message to Claude (stderr goes to Claude as explanation)
    echo "⛔ COMMAND BLOCKED" >&2
    echo "$REASON" >&2
    echo "Logged to: $LOG_FILE" >&2
    
    # Exit with non-zero to block execution
    exit 1
fi

# Allow normal commands
exit 0
