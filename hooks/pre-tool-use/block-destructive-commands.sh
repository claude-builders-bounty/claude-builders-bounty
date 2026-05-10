#!/bin/bash
# ───────────────────────────────────────────────
#  Pre-Tool-Use Hook: Block Destructive Commands
#  ───────────────────────────────────────────────
#  Prevents Claude Code from executing dangerous
#  bash commands like rm -rf, DROP TABLE, etc.
#
#  Installation:
#    ln -sf "$PWD" ~/.claude/hooks/pre-tool-use
#
#  Logs: ~/.claude/hooks/blocked.log
# ───────────────────────────────────────────────

LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Read the command from stdin (Claude Code passes the command via JSON on stdin)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('command',''))" 2>/dev/null || echo "$INPUT")

# Normalize: lowercase for pattern matching
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# ── Pattern definitions ──
BLOCKED=0
REASON=""

# 1. rm -rf (any variant)
if echo "$CMD_LOWER" | grep -qE '\brm\s+(-[a-z]*r[a-z]*f[a-z]*|-f[a-z]*r[a-z]*|-[a-z]*rf[a-z]*)\b'; then
    if echo "$COMMAND" | grep -qvE '(node_modules|\.git|__pycache__|/tmp/|/var/tmp/)'; then
        BLOCKED=1
        REASON="BLOCKED: Destructive rm -rf command detected. Use targeted 'rm' with specific files instead."
    fi
fi

# 2. DROP TABLE and TRUNCATE TABLE
if echo "$CMD_LOWER" | grep -qE '^\s*drop\s+table|^\s*truncate\s+table'; then
    BLOCKED=1
    REASON="BLOCKED: Destructive SQL command detected. Use safe migrations or backups first."
fi

# 3. git push --force (allow --force-with-lease)
if echo "$CMD_LOWER" | grep -qE '\bgit\s+push\s+.*(\-\-force|\-f)\b' && ! echo "$CMD_LOWER" | grep -qE '\-\-force\-with\-lease'; then
    BLOCKED=1
    REASON="BLOCKED: 'git push --force' detected. Use 'git push --force-with-lease' instead (safer alternative)."
fi

# 4. DELETE FROM without WHERE clause
if echo "$CMD_LOWER" | grep -qE 'delete\s+from\s+\w+\s*(;|$|--|#)' && ! echo "$CMD_LOWER" | grep -qE '\bwhere\b'; then
    BLOCKED=1
    REASON="BLOCKED: DELETE FROM without WHERE clause detected. Add a WHERE clause to prevent data loss."
fi

# 5. chmod -R 777
if echo "$CMD_LOWER" | grep -qE '\bchmod\s+-r\s*777\b'; then
    BLOCKED=1
    REASON="BLOCKED: 'chmod -R 777' detected. Use more restrictive permissions (755 or 644)."
fi

# 6. Direct disk writes (writes to /dev/sdX etc.)
if echo "$CMD_LOWER" | grep -qE '(>|>>)\s+/dev/(sd|nvme|hd)'; then
    BLOCKED=1
    REASON="BLOCKED: Direct disk write detected. This would damage the filesystem."
fi

# ── Action ──
if [ "$BLOCKED" = "1" ]; then
    LOG_DIR=$(dirname "$LOG_FILE")
    mkdir -p "$LOG_DIR"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED | command='$COMMAND' | reason='$REASON' | pwd='$(pwd)'" >> "$LOG_FILE"

    echo "❌ $REASON" >&2
    echo "   Blocked command: $COMMAND" >&2
    echo "   Logged to: $LOG_FILE" >&2
    exit 1
fi

exit 0
