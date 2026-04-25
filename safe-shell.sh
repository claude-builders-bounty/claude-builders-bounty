#!/usr/bin/env bash
# ============================================================================
# safe-shell.sh — Claude Code Pre-Tool-Use Hook
# Blocks dangerous bash commands before execution.
#
# Installation:
#   mkdir -p ~/.claude/hooks/ && cp safe-shell.sh ~/.claude/hooks/pre-tool-use
#   chmod +x ~/.claude/hooks/pre-tool-use
# ============================================================================
set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

# ---- Helper ----
log_and_block() {
    local reason="$1"
    local cmd="$2"
    local project_path
    project_path=$(pwd 2>/dev/null || echo "unknown")
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    {
        echo "[$timestamp] $reason"
        echo "  Project: $project_path"
        echo "  Command: $cmd"
        echo "  ---"
    } >> "$LOG_FILE"

    echo "{\"approved\": false, \"message\": \"$reason\"}"
    exit 0
}

# ---- Extract command from stdin ----
INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)

def find_cmd(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'command' and isinstance(v, str) and v.strip():
                return v.strip()
            if isinstance(v, (dict, list)):
                result = find_cmd(v)
                if result:
                    return result
    return None

if isinstance(data, dict):
    cmd = find_cmd(data)
    if cmd:
        print(cmd)
" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
    echo '{"approved": true}'
    exit 0
fi

# Normalize: collapse whitespace, then lowercase
NORMALIZED=$(echo "$COMMAND" | tr -s ' ')
LOWER=$(echo "$NORMALIZED" | tr '[:upper:]' '[:lower:]')

# ---- Block rules ----
# Match patterns anywhere in the command for maximum safety

# 1. rm -rf (recursive force delete)
if echo "$LOWER" | grep -qE '\brm\s+-rf\b'; then
    log_and_block "Blocked: 'rm -rf' — recursive force delete is destructive and irreversible." "$COMMAND"
fi

# 2. DROP TABLE (destructive SQL)
if echo "$LOWER" | grep -qE '\bdrop\s+table\b'; then
    log_and_block "Blocked: 'DROP TABLE' — this destroys an entire database table irreversibly." "$COMMAND"
fi

# 3. git push --force (destructive git)
if echo "$LOWER" | grep -qE '\bgit\s+push\b.*--force'; then
    log_and_block "Blocked: 'git push --force' — force-pushing overwrites remote history and can cause data loss for collaborators." "$COMMAND"
fi

# 4. TRUNCATE (destructive SQL)
if echo "$LOWER" | grep -qE '\btruncate\b'; then
    log_and_block "Blocked: 'TRUNCATE' — this empties an entire database table irreversibly." "$COMMAND"
fi

# 5. DELETE FROM without WHERE clause
if echo "$LOWER" | grep -qE '\bdelete\s+from\b'; then
    # Check if there's a WHERE clause anywhere in the statement
    if ! echo "$LOWER" | grep -qiE '\bwhere\b'; then
        log_and_block "Blocked: 'DELETE FROM' without a WHERE clause — this would delete ALL rows in the table." "$COMMAND"
    fi
fi

# If no rules matched, approve
echo '{"approved": true}'
exit 0
