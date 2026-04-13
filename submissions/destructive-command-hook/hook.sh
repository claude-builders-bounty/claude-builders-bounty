#!/usr/bin/env bash
# ============================================================================
# Claude Code Pre-Tool-Use Hook: Destructive Command Blocker
# ============================================================================
# Intercepts dangerous bash commands before Claude Code executes them.
#
# Hook format: receives JSON on stdin with {tool_name, tool_input}.
# Exit 0 = allow, Exit 2 = block (Claude Code convention).
# When blocking, outputs JSON: {"decision": "block", "reason": "..."}.
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"

# ---------------------------------------------------------------------------
# Read hook input from stdin
# ---------------------------------------------------------------------------
INPUT="$(cat)"

# ---------------------------------------------------------------------------
# Extract tool name — only inspect Bash tool invocations
# ---------------------------------------------------------------------------
TOOL_NAME="$(printf '%s' "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')"

if [ "$TOOL_NAME" != "Bash" ]; then
    exit 0
fi

# ---------------------------------------------------------------------------
# Extract the command string from tool_input.command
# ---------------------------------------------------------------------------
COMMAND="$(printf '%s' "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')"

if [ -z "$COMMAND" ]; then
    exit 0
fi

# ---------------------------------------------------------------------------
# Destructive pattern definitions (parallel arrays for clean separation)
# ---------------------------------------------------------------------------
PATTERNS=(
    'rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*f'
    'rm[[:space:]]+-[a-zA-Z]*f[a-zA-Z]*r'
    'DROP[[:space:]]+TABLE'
    'TRUNCATE[[:space:]]'
    'DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z_][a-zA-Z0-9_.]*[[:space:]]*;'
    'DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z_][a-zA-Z0-9_.]*[[:space:]]*$'
    'git[[:space:]]+push[[:space:]]+--force'
    'git[[:space:]]+push[[:space:]]+-f[[:space:]]'
    'git[[:space:]]+reset[[:space:]]+--hard'
    'mkfs\.'
    'dd[[:space:]]+if='
    ':\(\)\{.*:\|:.*&.*\};:'
)

REASONS=(
    'rm -rf: recursive force deletion can destroy entire directory trees'
    'rm -rf: recursive force deletion can destroy entire directory trees'
    'DROP TABLE: permanently removes database tables and all their data'
    'TRUNCATE: removes all rows from a table without logging individual deletions'
    'DELETE FROM without WHERE clause: removes all rows from a table'
    'DELETE FROM without WHERE clause: removes all rows from a table'
    'git push --force: rewrites remote history and can cause data loss for collaborators'
    'git push --force: rewrites remote history and can cause data loss for collaborators'
    'git reset --hard: discards all uncommitted changes permanently'
    'mkfs: formats a filesystem partition, destroying all existing data'
    'dd if=: raw disk copy that can overwrite partitions or devices'
    'Fork bomb: infinite process spawning that crashes the system'
)

# ---------------------------------------------------------------------------
# Check command against each pattern
# ---------------------------------------------------------------------------
for i in "${!PATTERNS[@]}"; do
    PATTERN="${PATTERNS[$i]}"
    REASON="${REASONS[$i]}"

    if printf '%s' "$COMMAND" | grep -qiE "$PATTERN" 2>/dev/null; then
        # ---------------------------------------------------------------
        # Ensure log directory exists
        # ---------------------------------------------------------------
        mkdir -p "$LOG_DIR"

        # ---------------------------------------------------------------
        # Extract working directory if present in the input
        # ---------------------------------------------------------------
        WORK_DIR="$(printf '%s' "$INPUT" | grep -o '"working_directory"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"working_directory"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' 2>/dev/null || echo "unknown")"
        if [ -z "$WORK_DIR" ]; then
            WORK_DIR="$(pwd)"
        fi

        # ---------------------------------------------------------------
        # Log the blocked attempt
        # ---------------------------------------------------------------
        TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        printf '[%s] BLOCKED | command: %s | reason: %s | cwd: %s\n' \
            "$TIMESTAMP" "$COMMAND" "$REASON" "$WORK_DIR" >> "$LOG_FILE"

        # ---------------------------------------------------------------
        # Output block decision as JSON for Claude Code
        # ---------------------------------------------------------------
        printf '{"decision": "block", "reason": "BLOCKED: %s. The command \\"%s\\" was prevented from executing."}\n' \
            "$REASON" "$COMMAND"

        exit 2
    fi
done

# ---------------------------------------------------------------------------
# No destructive pattern matched — allow execution
# ---------------------------------------------------------------------------
exit 0
