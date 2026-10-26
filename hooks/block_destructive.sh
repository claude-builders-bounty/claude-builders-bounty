#!/usr/bin/env bash
#
# block_destructive.sh — Pure Bash PreToolUse hook for Claude Code
#
# Intercepts and blocks destructive commands before execution:
#   * rm -rf / rm -r -f / rm --recursive --force
#   * DROP TABLE
#   * git push --force / -f / --force-with-lease
#   * TRUNCATE TABLE
#   * DELETE FROM without WHERE
#   * Low-level disk formatting (mkfs, dd if=... of=/dev/...)
#   * Fork bombs
#
# Zero runtime dependencies beyond standard coreutils.

set -euo pipefail

# Read hook event from stdin
INPUT=$(cat)

# Extract tool name and command using sed / grep (no jq dependency)
TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed -E 's/"tool_name"[[:space:]]*:[[:space:]]*"([^"]*)"/\1/' || echo "")

if [ "$TOOL_NAME" != "Bash" ] && [ "$TOOL_NAME" != "bash" ]; then
    # Not a Bash tool call, allow immediately
    exit 0
fi

# Extract command string
CMD=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | sed -E 's/"command"[[:space:]]*:[[:space:]]*"([^"]*)"/\1/' || echo "")

# If command is empty, allow
if [ -z "$CMD" ]; then
    exit 0
fi

# Function to block command
block() {
    local RULE="$1"
    local REASON="$2"
    local LOG_DIR="$HOME/.claude/hooks"
    local LOG_FILE="$LOG_DIR/blocked.log"
    
    mkdir -p "$LOG_DIR"
    local TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%d %H:%M:%S")
    echo "[$TS] BLOCKED ($RULE)" >> "$LOG_FILE"
    echo "Command: $CMD" >> "$LOG_FILE"
    echo "Reason: $REASON" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"
    
    echo "BLOCKED by PreToolUse Safety Guard:" >&2
    echo "Rule: $RULE" >&2
    echo "Reason: $REASON" >&2
    echo "Logged to: $LOG_FILE" >&2
    exit 1
}

# 1. rm -rf variations
if echo "$CMD" | grep -Ei '\brm\s+([^\n;|&]*\s+)?(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|--recursive\s+--force|--force\s+--recursive|-[a-zA-Z]*r[a-zA-Z]*\s+-[a-zA-Z]*f[a-zA-Z]*)\b' >/dev/null 2>&1; then
    block "Recursive Force Removal" "Destructive recursive deletion ('rm -rf') detected. This operation permanently removes directory trees without confirmation."
fi

# 2. git push --force variations
if echo "$CMD" | grep -Ei '\bgit\s+([^\n;|&]*\s+)?push\s+([^\n;|&]*\s+)?(--force|-f|--force-with-lease)\b' >/dev/null 2>&1; then
    block "Git Force Push" "Force push ('git push --force') detected. Overwriting remote history can destroy collaborator work and branches."
fi

# 3. DROP TABLE
if echo "$CMD" | grep -Ei '\bDROP\s+TABLE\b' >/dev/null 2>&1; then
    block "SQL Drop Table" "Destructive SQL operation ('DROP TABLE') detected. This destroys the database schema and all contained table records."
fi

# 4. TRUNCATE TABLE
if echo "$CMD" | grep -Ei '\bTRUNCATE(\s+TABLE)?\b' >/dev/null 2>&1; then
    block "SQL Truncate Table" "Destructive SQL operation ('TRUNCATE') detected. This permanently purges all rows from the specified table."
fi

# 5. DELETE FROM without WHERE
if echo "$CMD" | grep -Ei '\bDELETE\s+FROM\b' >/dev/null 2>&1; then
    if ! echo "$CMD" | grep -Ei '\bWHERE\b' >/dev/null 2>&1; then
        block "SQL Delete Without Where" "Destructive SQL operation ('DELETE FROM' without 'WHERE' clause) detected. This clears all table data."
    fi
fi

# 6. Disk Overwrite / mkfs
if echo "$CMD" | grep -Ei '\b(mkfs|dd\s+if=[^\n;|&]*\s+of=/dev/)\b' >/dev/null 2>&1; then
    block "Disk Overwrite or Formatting" "Low-level storage formatting or raw disk overwrite command detected."
fi

# 7. Fork Bomb
if echo "$CMD" | grep -E ':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:' >/dev/null 2>&1; then
    block "Fork Bomb" "Denial-of-service fork bomb pattern intercepted."
fi

# Safe command
exit 0
