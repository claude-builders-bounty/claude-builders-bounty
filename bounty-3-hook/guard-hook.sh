#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# guard-hook.sh — Claude Code PreToolUse hook
#
# Blocks destructive commands before Claude Code executes them.
# Designed to run as a PreToolUse hook — receives tool input on stdin as JSON.
#
# Blocks:
#   - rm -rf (recursive force delete)
#   - DROP TABLE / DROP DATABASE
#   - git push --force / git push -f
#   - TRUNCATE TABLE
#   - DELETE FROM without WHERE clause
#
# Logs blocked attempts to ~/.claude/hooks/blocked.log as JSON lines.
#
# Usage:
#   Configured via .claude/settings.json (see README.md)
#   Reads JSON from stdin, exits 2 to block, 0 to allow.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
PROJECT_DIR="${PWD}"

# ---------------------------------------------------------------------------
# Ensure log directory exists
# ---------------------------------------------------------------------------
mkdir -p "$LOG_DIR"

# ---------------------------------------------------------------------------
# Read stdin (tool input JSON from Claude Code)
# ---------------------------------------------------------------------------
INPUT="$(cat)"

# ---------------------------------------------------------------------------
# Extract the command string from the JSON input
# Parse tool_input.command (for Bash tool) or tool_input.sql (for SQL tools)
# ---------------------------------------------------------------------------
extract_command() {
    local input="$1"

    # Try jq first
    if command -v jq &>/dev/null; then
        local cmd
        cmd="$(echo "$input" | jq -r '.tool_input.command // .tool_input.sql // .tool_input.input // empty' 2>/dev/null || true)"
        if [[ -n "$cmd" ]]; then
            echo "$cmd"
            return
        fi
    fi

    # Fallback: grep for command field
    local cmd
    cmd="$(echo "$input" | grep -oP '"command"\s*:\s*"((?:[^"\\]|\\.)*)"' | head -1 | sed 's/.*: *"//;s/"$//' || true)"
    if [[ -n "$cmd" ]]; then
        echo "$cmd"
        return
    fi

    # Fallback: grep for sql field
    cmd="$(echo "$input" | grep -oP '"sql"\s*:\s*"((?:[^"\\]|\\.)*)"' | head -1 | sed 's/.*: *"//;s/"$//' || true)"
    if [[ -n "$cmd" ]]; then
        echo "$cmd"
        return
    fi

    # Fallback: grep for input field
    cmd="$(echo "$input" | grep -oP '"input"\s*:\s*"((?:[^"\\]|\\.)*)"' | head -1 | sed 's/.*: *"//;s/"$//' || true)"
    echo "$cmd"
}

COMMAND="$(extract_command "$INPUT")"

# If we couldn't extract a command, allow (don't block non-command tools)
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# Normalize: collapse whitespace, lowercase for matching
NORMALIZED="$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' ' ')"

# ---------------------------------------------------------------------------
# Log a blocked attempt
# ---------------------------------------------------------------------------
log_blocked() {
    local reason="$1"
    local timestamp
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    local project
    project="$(basename "$PROJECT_DIR")"

    # Truncate command for logging (max 200 chars)
    local log_cmd="${COMMAND:0:200}"

    # JSON line
    printf '{"timestamp":"%s","reason":"%s","command":"%s","project":"%s"}\n' \
        "$timestamp" \
        "$reason" \
        "$(echo "$log_cmd" | sed 's/"/\\"/g' | tr '\n' ' ')" \
        "$project" \
        >> "$LOG_FILE"
}

# ---------------------------------------------------------------------------
# Block with message
# ---------------------------------------------------------------------------
block() {
    local reason="$1"
    local explanation="$2"

    log_blocked "$reason"
    echo "BLOCKED: ${explanation}" >&2
    exit 2
}

# ---------------------------------------------------------------------------
# Pattern checks
# ---------------------------------------------------------------------------

# 1. rm -rf (recursive force delete)
# Match rm with flags containing both -r and -f (in any order, combined or separate)
if echo "$NORMALIZED" | grep -qP 'rm\s+(-\w*r\w*f\w*|-\w*f\w*r\w*)\b'; then
    block "rm-rf" "rm -rf is blocked. Use rm with explicit paths and no -rf flag, or remove files individually."
fi

# 2. DROP TABLE / DROP DATABASE
if echo "$NORMALIZED" | grep -qP 'drop\s+(table|database)\b'; then
    block "drop-table" "DROP TABLE/DATABASE is blocked. This permanently destroys data. Remove this protection only if you are certain."
fi

# 3. git push --force / git push -f (but allow --force-with-lease)
if echo "$NORMALIZED" | grep -qP 'git\s+push\s+.*--force-with-lease'; then
    : # --force-with-lease is safe, skip
elif echo "$NORMALIZED" | grep -qP 'git\s+push\s+.*(-f|--force)\b'; then
    block "git-push-force" "git push --force is blocked. Force-pushing rewrites remote history. Use --force-with-lease if you must, or remove this protection."
fi

# 4. TRUNCATE TABLE (SQL statement, not the English word in other contexts)
# Matches: TRUNCATE TABLE name, TRUNCATE name (SQL), but not "truncate the string"
if echo "$NORMALIZED" | grep -qP '^\s*truncate\s+(table\s+)?\w' || \
   echo "$NORMALIZED" | grep -qP ';\s*truncate\s+(table\s+)?\w'; then
    block "truncate" "TRUNCATE is blocked. This removes all rows permanently without logging. Use DELETE with a WHERE clause instead."
fi

# 5. DELETE FROM without WHERE
if echo "$NORMALIZED" | grep -qP 'delete\s+from\s+\w'; then
    # Check if there's a WHERE clause
    if ! echo "$NORMALIZED" | grep -qP 'delete\s+from\s+\w+.*\bwhere\b'; then
        block "delete-without-where" "DELETE FROM without WHERE clause is blocked. This deletes all rows in the table. Add a WHERE clause to target specific rows."
    fi
fi

# ---------------------------------------------------------------------------
# All checks passed — allow the command
# ---------------------------------------------------------------------------
exit 0
