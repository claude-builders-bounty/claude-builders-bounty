#!/usr/bin/env bash
# PreToolUse Hook: Destructive Command Interceptor for Claude Code (Bash version)
# Intercepts dangerous bash commands, logs to ~/.claude/hooks/blocked.log, and returns exit code 2.

set -euo pipefail

# Read stdin
INPUT=$(cat)

if [ -z "$INPUT" ]; then
    exit 0
fi

# Extract tool name and command using python3 or jq
if command -v python3 >/dev/null 2>&1; then
    TOOL_NAME=$(python3 -c "import sys, json; data=json.loads(sys.argv[1]); print(data.get('tool_name', ''))" "$INPUT" 2>/dev/null || echo "")
    CMD=$(python3 -c "import sys, json; data=json.loads(sys.argv[1]); ti=data.get('tool_input', {}); print(ti.get('command', '') if isinstance(ti, dict) else (ti if isinstance(ti, str) else ''))" "$INPUT" 2>/dev/null || echo "")
elif command -v jq >/dev/null 2>&1; then
    TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || echo "")
    CMD=$(echo "$INPUT" | jq -r '(.tool_input.command // .tool_input // empty)' 2>/dev/null || echo "")
else
    # Fallback grep extraction
    CMD="$INPUT"
    TOOL_NAME="Bash"
fi

# Only inspect Bash / shell executions
if [ -n "$TOOL_NAME" ] && [ "$TOOL_NAME" != "Bash" ] && [ "$TOOL_NAME" != "bash" ]; then
    exit 0
fi

if [ -z "$CMD" ]; then
    exit 0
fi

BLOCKED_REASON=""

# 1. rm -rf variations
if echo "$CMD" | grep -Eq '(^|[;&|`$\(\)]|\s)(sudo\s+)?rm\s+([^\n]*\s+)?(-[a-zA-Z0-9]*[rf][a-zA-Z0-9]*|--recursive|--force)'; then
    BLOCKED_REASON="rm with recursive/force flags (-r, -f, --recursive, --force)"
# 2. DROP TABLE / DATABASE / SCHEMA
elif echo "$CMD" | grep -Eiq '\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW)\b'; then
    BLOCKED_REASON="Destructive SQL DROP statement"
# 3. TRUNCATE
elif echo "$CMD" | grep -Eiq '\bTRUNCATE(\s+TABLE)?\b'; then
    BLOCKED_REASON="Destructive SQL TRUNCATE statement"
# 4. DELETE FROM without WHERE
elif echo "$CMD" | grep -Eiq '\bDELETE\s+FROM\b' && ! echo "$CMD" | grep -Eiq '\bWHERE\b'; then
    BLOCKED_REASON="SQL DELETE FROM statement without a WHERE clause"
# 5. git push --force variations
elif echo "$CMD" | grep -Eq '(^|[;&|`$\(\)]|\s)git\s+push\b' && echo "$CMD" | grep -Eq '(\s|^)(-f\b|--force\b|--force-with-lease\b)'; then
    BLOCKED_REASON="Git force push operation (-f, --force, --force-with-lease)"
# 6. mkfs / disk wipe
elif echo "$CMD" | grep -Eq '(^|[;&|`$\(\)]|\s)(sudo\s+)?mkfs(\.[a-zA-Z0-9]+)?\b'; then
    BLOCKED_REASON="Filesystem formatting utility (mkfs)"
fi

if [ -n "$BLOCKED_REASON" ]; then
    CLAUDE_HOOKS_DIR="${HOME}/.claude/hooks"
    mkdir -p "$CLAUDE_HOOKS_DIR"
    LOG_FILE="$CLAUDE_HOOKS_DIR/blocked.log"
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

    cat <<EOF >> "$LOG_FILE"
[$TIMESTAMP] BLOCKED: $BLOCKED_REASON
  Command: $CMD
  Project: $PROJECT_DIR
------------------------------------------------------------
EOF

    cat <<EOF >&2

[SECURITY GUARD] Command Execution Blocked!
Pattern Detected : $BLOCKED_REASON
Blocked Command  : $CMD
Audit Logging    : Recorded in ~/.claude/hooks/blocked.log
Reason           : Destructive operations (rm -rf, git push --force, DROP TABLE, TRUNCATE, unconstrained DELETE) are strictly prohibited.
Action Required  : Reformulate the command safely without destructive operations.

EOF
    # Exit code 2 notifies Claude Code to abort tool execution and pass stderr back to model
    exit 2
fi

exit 0
