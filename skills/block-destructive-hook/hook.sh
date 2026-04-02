#!/usr/bin/env bash
# pre-tool-use hook: blocks destructive bash commands
# Claude Code hooks format: https://docs.anthropic.com/claude-code/hooks
#
# Usage:
#   Place this script in ~/.claude/hooks/pre-tool-use
#   Make it executable: chmod +x ~/.claude/hooks/pre-tool-use
#
# Exit codes:
#   0  = allow the command (blocked patterns NOT detected)
#   70 = block the command (dangerous pattern detected)

set -euo pipefail

HOOK_VERSION="1.0.0"
BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"
TOOL_NAME="${1:-}"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
PROJECT_PATH="${PWD:-unknown}"

# Ensure the blocked log directory exists
mkdir -p "$(dirname "$BLOCKED_LOG")"
touch "$BLOCKED_LOG" 2>/dev/null || true

log_blocked() {
    local tool="$1"
    local command="$2"
    local reason="$3"
    echo "[${TIMESTAMP}] TOOL=${tool} PROJECT=${PROJECT_PATH} REASON=${reason} COMMAND=${command}" >> "$BLOCKED_LOG"
}

notify_blocked() {
    local reason="$1"
    echo ""
    echo "⚠️   BLOCKED: $reason"
    echo ""
    echo "If you intentionally want to run this command, you can override with:"
    echo "  --confirm  (per-command approval)"
    echo ""
    echo "This attempt has been logged to: $BLOCKED_LOG"
    echo ""
}

block_command() {
    local reason="$1"
    local command="$2"
    log_blocked "$TOOL_NAME" "$command" "$reason"
    notify_blocked "$reason"
    exit 70
}

# Read the command from stdin (Claude Code passes tool input via stdin for bash)
COMMAND=""
if [[ -t 0 ]]; then
    # No stdin (interactive), try to get from $1 or environment
    COMMAND="${COMMAND_INPUT:-${1:-}}"
else
    COMMAND="$(cat /dev/stdin 2>/dev/null || echo '')"
fi

# Also check for arguments passed directly
if [[ -z "$COMMAND" && -n "${1:-}" ]]; then
    COMMAND="$1"
fi

# Check if there's a --confirm flag (user override)
if echo "$COMMAND" | grep -qE '^\s*(--confirm|-y|\+cg)\s' 2>/dev/null; then
    exit 0
fi

# Nothing to check
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# Normalize whitespace for easier pattern matching
NORMALIZED="$(echo "$COMMAND" | sed 's/\s\+/ /g')"

# Pattern 1: rm -rf / or rm -rf ~ or rm -rf /home etc.
if echo "$COMMAND" | grep -qE 'rm\s+(-[rfR]+\s+)*(/|~|/\*)' 2>/dev/null; then
    block_command "Recursive force delete detected (rm -rf /, rm -rf ~, or rm -rf /*)" "$COMMAND"
fi

# Pattern 2: DROP TABLE (SQL)
if echo "$NORMALIZED" | grep -qE 'DROP\s+TABLE' 2>/dev/null; then
    block_command "DROP TABLE detected — this permanently deletes a database table" "$COMMAND"
fi

# Pattern 3: TRUNCATE TABLE
if echo "$NORMALIZED" | grep -qE 'TRUNCATE\s+TABLE' 2>/dev/null; then
    block_command "TRUNCATE TABLE detected — this permanently deletes all rows from a table" "$COMMAND"
fi

# Pattern 4: git push --force (with common aliases)
if echo "$COMMAND" | grep -qE 'git\s+(push|force-push|pr\s+push)\s+.*--force' 2>/dev/null; then
    block_command "Force push detected — this can overwrite remote history and cause data loss for collaborators" "$COMMAND"
fi

# Pattern 5: DELETE FROM without WHERE
if echo "$NORMALIZED" | grep -qE 'DELETE\s+FROM\s+[a-zA-Z_][a-zA-Z0-9_]*\s*(;|$|\s+WHERE)' 2>/dev/null; then
    # Check if WHERE is actually present (not just matching the pattern above)
    if ! echo "$NORMALIZED" | grep -qE 'DELETE\s+FROM\s+[a-zA-Z_][a-zA-Z0-9_]*\s+WHERE' 2>/dev/null; then
        block_command "DELETE FROM without WHERE clause — this would delete ALL rows from the table" "$COMMAND"
    fi
fi

# Pattern 6: mkfs (create filesystem)
if echo "$COMMAND" | grep -qE '^\s*(sudo\s+)?mkfs' 2>/dev/null; then
    block_command "mkfs detected — this formats/erases an entire disk or partition" "$COMMAND"
fi

# Pattern 7: dd of=/dev/sdX or similar (disk wipe)
if echo "$COMMAND" | grep -qE 'dd\s+.*of=/dev/sd' 2>/dev/null; then
    block_command "dd to block device detected — this can wipe disks" "$COMMAND"
fi

# Pattern 8: shred -zuz (secure delete with overwrite)
if echo "$COMMAND" | grep -qE 'shred\s+.*-zuz' 2>/dev/null; then
    block_command "shred -zuz detected — this securely deletes files beyond recovery" "$COMMAND"
fi

# Pattern 9: git push -f (short form)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*-[fF]\b' 2>/dev/null; then
    block_command "Force push (-f) detected — this can overwrite remote history" "$COMMAND"
fi

# Pattern 10: DROP DATABASE
if echo "$NORMALIZED" | grep -qE 'DROP\s+DATABASE' 2>/dev/null; then
    block_command "DROP DATABASE detected — this permanently deletes an entire database" "$COMMAND"
fi

# Pattern 11: truncate (shell command, not SQL)
if echo "$COMMAND" | grep -qE '^\s*truncate\s+.*--size\s*=\s*0' 2>/dev/null; then
    block_command "truncate --size=0 detected — this empties files" "$COMMAND"
fi

# Pattern 12: > file (output redirection wiping target) - only block if it's overwriting important files
# Skip this one as it could be too aggressive for legitimate uses

exit 0
