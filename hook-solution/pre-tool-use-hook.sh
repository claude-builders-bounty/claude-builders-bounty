#!/usr/bin/env bash
# pre-tool-use-hook.sh — Claude Code pre-tool-use hook
# Blocks dangerous bash commands before execution.
#
# Installation (2 commands):
#   mkdir -p ~/.claude/hooks && cp pre-tool-use-hook.sh ~/.claude/hooks/
#   chmod +x ~/.claude/hooks/pre-tool-use-hook.sh
#
# Then add to ~/.claude/settings.json:
#   { "hooks": { "preToolUse": ["bash ~/.claude/hooks/pre-tool-use-hook.sh"] } }

set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"
TOOL_NAME="${1:-}"
TOOL_INPUT="${2:-}"

# Only intercept Bash tool calls
if [[ "$TOOL_NAME" != "Bash" && "$TOOL_NAME" != "bash" ]]; then
    exit 0
fi

# Extract the command from tool input (JSON or plain string)
COMMAND="$TOOL_INPUT"

# If it looks like JSON, extract the "command" field
if [[ "$COMMAND" == *"{"* ]]; then
    COMMAND=$(echo "$COMMAND" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('command', data.get('cmd', '')))
except:
    print(sys.stdin.read())
" 2>/dev/null || echo "$COMMAND")
fi

# Skip empty commands
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# ─── Blocked Patterns ──────────────────────────────────────────────
BLOCKED=false
REASON=""

# rm -rf (recursive force delete)
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive)\s'; then
    BLOCKED=true
    REASON="Blocked: 'rm -rf' — recursive force delete is not allowed"
fi
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive)\s+/'; then
    BLOCKED=true
    REASON="Blocked: 'rm -rf /' — attempting to delete root filesystem"
fi
# Simple rm -rf without path (still dangerous)
if echo "$COMMAND" | grep -qE '^rm\s+-rf\s'; then
    BLOCKED=true
    REASON="Blocked: 'rm -rf' — recursive force delete is not allowed"
fi

# DROP TABLE
if echo "$COMMAND" | grep -qiE 'DROP\s+TABLE'; then
    BLOCKED=true
    REASON="Blocked: 'DROP TABLE' — destructive SQL operation"
fi

# DROP DATABASE
if echo "$COMMAND" | grep -qiE 'DROP\s+DATABASE'; then
    BLOCKED=true
    REASON="Blocked: 'DROP DATABASE' — destructive SQL operation"
fi

# git push --force (force push)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*(--force|-f)\b'; then
    BLOCKED=true
    REASON="Blocked: 'git push --force' — force push can overwrite remote history"
fi

# TRUNCATE
if echo "$COMMAND" | grep -qiE 'TRUNCATE\s+(TABLE\s+)?'; then
    BLOCKED=true
    REASON="Blocked: 'TRUNCATE' — deletes all rows from table"
fi

# DELETE FROM without WHERE clause
if echo "$COMMAND" | grep -qiE 'DELETE\s+FROM\s+\S+(\s*;|\s*$)' && ! echo "$COMMAND" | grep -qiE 'WHERE\s'; then
    BLOCKED=true
    REASON="Blocked: 'DELETE FROM' without WHERE — would delete all rows"
fi

# ─── Additional Safety Patterns ────────────────────────────────────

# chmod 777 (overly permissive)
if echo "$COMMAND" | grep -qE 'chmod\s+777'; then
    BLOCKED=true
    REASON="Blocked: 'chmod 777' — overly permissive file permissions"
fi

# curl | sh / curl | bash (pipe to shell)
if echo "$COMMAND" | grep -qE 'curl\s.*\|\s*(ba)?sh'; then
    BLOCKED=true
    REASON="Blocked: piping curl to shell — potential code injection"
fi

# wget | sh / wget | bash
if echo "$COMMAND" | grep -qE 'wget\s.*\|\s*(ba)?sh'; then
    BLOCKED=true
    REASON="Blocked: piping wget to shell — potential code injection"
fi

# mkfs (format disk)
if echo "$COMMAND" | grep -qE 'mkfs\.'; then
    BLOCKED=true
    REASON="Blocked: 'mkfs' — formatting disk/filesystem"
fi

# dd to device (write to disk)
if echo "$COMMAND" | grep -qE 'dd\s+.*of=/dev/'; then
    BLOCKED=true
    REASON="Blocked: 'dd of=/dev/' — writing directly to device"
fi

# ─── Handle Block ──────────────────────────────────────────────────
if $BLOCKED; then
    # Log the blocked attempt
    mkdir -p "$(dirname "$LOG_FILE")"
    {
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Timestamp: $(date -Iseconds)"
        echo "Project:   $(pwd)"
        echo "Command:   $COMMAND"
        echo "Reason:    $REASON"
        echo ""
    } >> "$LOG_FILE"

    # Output the reason (Claude Code will see this)
    echo "$REASON"
    echo "This command has been blocked by the pre-tool-use safety hook."
    echo "Log: $LOG_FILE"
    exit 2  # Non-zero = blocked
fi

# Command is safe — allow execution
exit 0
