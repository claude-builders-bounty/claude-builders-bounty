#!/usr/bin/env bash
# safety-hook.sh — Pre-tool-use hook for Claude Code
# Blocks destructive bash commands before they execute.
# Bounty: #3 — $100
#
# Usage: Installed to ~/.claude/hooks/ and invoked by Claude Code
# before each Bash tool call.

set -euo pipefail

# --- Configuration ---
BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"
LOG_DIR="$(dirname "$BLOCKED_LOG")"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# --- Read input from Claude Code ---
# Claude Code passes JSON via stdin with tool_name and tool_input
INPUT=$(cat)

# Extract tool name and command
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Only intercept Bash tool calls
if [[ "$TOOL_NAME" != "Bash" ]]; then
    exit 0
fi

# Skip empty commands
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# --- Dangerous pattern detection ---
BLOCKED=0
REASON=""

# Pattern 1: rm -rf (recursive force delete)
if echo "$COMMAND" | grep -qiE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b'; then
    BLOCKED=1
    REASON="Blocked: 'rm -rf' is a recursive force-delete that can destroy files irreversibly."
fi

# Pattern 2: rm -r on root or home
if echo "$COMMAND" | grep -qiE 'rm\s+.*(-r|--recursive)\s+(/|~|\$HOME)'; then
    BLOCKED=1
    REASON="Blocked: Recursive delete on system directory (/, ~, \$HOME)."
fi

# Pattern 3: DROP TABLE
if echo "$COMMAND" | grep -qiE '\bDROP\s+TABLE\b'; then
    BLOCKED=1
    REASON="Blocked: 'DROP TABLE' permanently deletes a database table and all its data."
fi

# Pattern 4: git push --force (without --force-with-lease)
if echo "$COMMAND" | grep -qiE 'git\s+push\s+.*--force\b' && ! echo "$COMMAND" | grep -qiE '--force-with-lease'; then
    BLOCKED=1
    REASON="Blocked: 'git push --force' can overwrite remote history. Use '--force-with-lease' if force-push is needed."
fi

# Pattern 5: TRUNCATE
if echo "$COMMAND" | grep -qiE '\bTRUNCATE\b'; then
    BLOCKED=1
    REASON="Blocked: 'TRUNCATE' removes all rows from a table without logging individual row deletions."
fi

# Pattern 6: DELETE FROM without WHERE clause
if echo "$COMMAND" | grep -qiE '\bDELETE\s+FROM\b' && ! echo "$COMMAND" | grep -qiE '\bWHERE\b'; then
    BLOCKED=1
    REASON="Blocked: 'DELETE FROM' without a WHERE clause deletes ALL rows from the table."
fi

# --- Handle blocked command ---
if [[ "$BLOCKED" -eq 1 ]]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    PROJECT_PATH=$(pwd)

    # Log the blocked attempt
    echo "[${TIMESTAMP}] BLOCKED | project: ${PROJECT_PATH} | command: ${COMMAND} | reason: ${REASON}" >> "$BLOCKED_LOG"

    # Output message for Claude
    echo "🚫 SAFETY HOOK: Command blocked."
    echo ""
    echo "  Command: ${COMMAND}"
    echo "  Reason:  ${REASON}"
    echo ""
    echo "  This command was intercepted by the safety hook to prevent"
    echo "  potential data loss or destructive operations."
    echo ""
    echo "  If this command is truly needed, run it manually in your terminal."
    echo "  Logged to: ${BLOCKED_LOG}"

    exit 2  # Non-zero exit blocks the tool call
fi

# --- Allow the command ---
exit 0
