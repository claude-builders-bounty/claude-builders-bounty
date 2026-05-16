#!/usr/bin/env bash
# =============================================================================
# Claude Code Pre-Tool-Use Hook: Block Destructive Commands
# =============================================================================
# Blocks dangerous bash/CLI commands before they execute:
#   - rm -rf (recursive force delete)
#   - DROP TABLE / DROP DATABASE
#   - git push --force / --force-with-lease (force push to main/master)
#   - TRUNCATE TABLE
#   - DELETE FROM without WHERE clause
# =============================================================================
# Claude Code hooks receive JSON on stdin with tool invocation details.
# Fields include: tool_name, tool_input (the command), cwd (project path).
# Exit 0 = allow the tool call. Exit non-zero = block it.
# =============================================================================

set -euo pipefail

# ── Read JSON from stdin ────────────────────────────────────────────────────
INPUT_JSON="$(cat)"

# Extract relevant fields using jq (Claude Code guarantees jq is available)
TOOL_NAME="$(echo "$INPUT_JSON" | jq -r '.tool_name // ""')"
TOOL_INPUT="$(echo "$INPUT_JSON" | jq -r '.tool_input.command // ""')"
CWD="$(echo "$INPUT_JSON" | jq -r '.cwd // "'"$PWD"'"')"

# ── Only inspect Bash/Shell tool calls ──────────────────────────────────────
# We only care about bash/shell commands. Let everything else pass through.
if [[ "$TOOL_NAME" != "Bash" && "$TOOL_NAME" != "bash" && "$TOOL_NAME" != "Shell" ]]; then
    exit 0
fi

# ── Normalize the command for pattern matching ──────────────────────────────
# Collapse whitespace, trim, and lowercase for case-insensitive matching
NORM_CMD="$(echo "$TOOL_INPUT" | tr -s '[:space:]' ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
LOWER_CMD="$(echo "$NORM_CMD" | tr '[:upper:]' '[:lower:]')"

# ── Log setup ───────────────────────────────────────────────────────────────
LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
mkdir -p "$LOG_DIR"

# ── Blocking logic ──────────────────────────────────────────────────────────
BLOCK_REASON=""

# Check: rm -rf (any variant including rm -r -f, rm -rf *, rm -fr, /bin/rm -rf, etc.)
if echo "$LOWER_CMD" | grep -qP '\brm\b.*\s+-[a-z]*r[a-z]*f|rm\b.*\s+-[a-z]*f[a-z]*r|rm\b.*\s+--recursive.*\s+--force|rm\b.*\s+--force.*\s+--recursive'; then
    BLOCK_REASON="rm -rf (recursive force delete)"
fi

# Check: DROP TABLE or DROP DATABASE (SQL)
if [ -z "$BLOCK_REASON" ]; then
    if echo "$LOWER_CMD" | grep -qP '\bdrop\s+(table|database)\b'; then
        BLOCK_REASON="DROP TABLE / DROP DATABASE"
    fi
fi

# Check: git push --force or git push --force-with-lease (especially to main/master)
if [ -z "$BLOCK_REASON" ]; then
    if echo "$LOWER_CMD" | grep -qP '\bgit\s+push\b.*\s--force'; then
        BLOCK_REASON="git push --force / --force-with-lease"
    fi
fi

# Check: TRUNCATE TABLE
if [ -z "$BLOCK_REASON" ]; then
    if echo "$LOWER_CMD" | grep -qP '\btruncate\s+(table\s+)?\w+'; then
        BLOCK_REASON="TRUNCATE TABLE"
    fi
fi

# Check: DELETE FROM without WHERE
if [ -z "$BLOCK_REASON" ]; then
    if echo "$LOWER_CMD" | grep -qP '\bdelete\s+from\s+\w+'; then
        # Only block if there's no WHERE clause
        if ! echo "$LOWER_CMD" | grep -qP '\bwhere\b'; then
            BLOCK_REASON="DELETE FROM without WHERE clause"
        fi
    fi
fi

# If no block reason, allow the command
if [ -z "$BLOCK_REASON" ]; then
    exit 0
fi

# ── Block the command ──────────────────────────────────────────────────────
TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# Log the blocked attempt
cat >> "$LOG_FILE" <<EOF
[$TIMESTAMP] BLOCKED: $BLOCK_REASON
  Command : $NORM_CMD
  Project : $CWD
---
EOF

# Display clear message to the user (stderr is shown to the user by Claude Code)
cat >&2 <<MSG

╔══════════════════════════════════════════════════════════════════╗
║  🛑  DESTRUCTIVE COMMAND BLOCKED                                ║
╠══════════════════════════════════════════════════════════════════╣
║  Reason : ${BLOCK_REASON}
║  Command: ${NORM_CMD}
║  Project: ${CWD}
╠══════════════════════════════════════════════════════════════════╣
║  This command could cause irreversible data loss.               ║
║  It has been blocked by the pre-tool-use safety hook.           ║
║                                                                ║
║  If you are ABSOLUTELY SURE you want to run this:              ║
║    1. Review the command carefully                             ║
║    2. Run it manually in your terminal                         ║
║    3. Or temporarily disable this hook                         ║
║                                                                ║
║  Logged to: ${LOG_FILE}
╚══════════════════════════════════════════════════════════════════╝

MSG

# Non-zero exit blocks the tool from executing
exit 1
