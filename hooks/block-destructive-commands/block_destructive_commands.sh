#!/usr/bin/env bash
# Claude Code PreToolUse Hook: Destructive Bash Command Blocker (Shell Version)
# Intercepts: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE

set -e

# Read stdin JSON payload
PAYLOAD=$(cat)

if [ -z "$PAYLOAD" ]; then
    exit 0
fi

# Extract command and project directory using python if available, or basic regex/sed
if command -v python3 >/dev/null 2>&1; then
    COMMAND=$(echo "$PAYLOAD" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tool_input', {}).get('command', ''))" 2>/dev/null || echo "")
    CWD_DIR=$(echo "$PAYLOAD" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('cwd', ''))" 2>/dev/null || pwd)
else
    COMMAND=$(echo "$PAYLOAD" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n 1 | cut -d'"' -f4)
    CWD_DIR=$(pwd)
fi

if [ -z "$COMMAND" ]; then
    exit 0
fi

BLOCKED_REASON=""

# 1. rm -rf variations
if echo "$COMMAND" | grep -Eiq '(^|[;&|][[:space:]]*)rm[[:space:]]+(-[a-zA-Z0-9_-]*[rR][a-zA-Z0-9_-]*[fF]|-[a-zA-Z0-9_-]*[fF][a-zA-Z0-9_-]*[rR]|--recursive[[:space:]]+--force|--force[[:space:]]+--recursive|-[rR][[:space:]]+-[fF]|-[fF][[:space:]]+-[rR])\b'; then
    BLOCKED_REASON="Recursive forced deletion ('rm -rf') can permanently wipe project files, directories, or system paths."
# 2. DROP TABLE / DATABASE
elif echo "$COMMAND" | grep -Eiq '\bDROP[[:space:]]+(TEMPORARY[[:space:]]+)?(TABLE|DATABASE|SCHEMA)\b'; then
    BLOCKED_REASON="Destructive DDL statement ('DROP TABLE / DATABASE') destroys database tables and schemas."
# 3. git push --force
elif echo "$COMMAND" | grep -Eiq '\bgit[[:space:]]+push\b[^\n;&|]*(--force\b|--force-with-lease\b|-f\b)'; then
    BLOCKED_REASON="Forced git push ('git push --force') can permanently overwrite upstream commits."
# 4. TRUNCATE
elif echo "$COMMAND" | grep -Eiq '\bTRUNCATE([[:space:]]+TABLE)?[[:space:]]+[a-zA-Z0-9_.]+'; then
    BLOCKED_REASON="Destructive SQL statement ('TRUNCATE TABLE') wipes all table rows."
# 5. DELETE FROM without WHERE
elif echo "$COMMAND" | grep -Eiq '\bDELETE[[:space:]]+FROM\b' && ! echo "$COMMAND" | grep -Eiq '\bWHERE\b'; then
    BLOCKED_REASON="Unbounded 'DELETE FROM' without a WHERE clause will delete all records in the table."
fi

if [ -n "$BLOCKED_REASON" ]; then
    LOG_DIR="$HOME/.claude/hooks"
    mkdir -p "$LOG_DIR"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%d %H:%M:%S")
    
    # Append log record
    printf '{"timestamp":"%s","command":"%s","project_path":"%s","reason":"%s"}\n' \
        "$TIMESTAMP" "$(echo "$COMMAND" | tr -d '"' | tr '\n' ' ')" "$CWD_DIR" "$BLOCKED_REASON" >> "$LOG_DIR/blocked.log"

    # Emit JSON denial
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "🚫 [BLOCKED BY SECURITY POLICY] Command was rejected:\nCommand: $COMMAND\nReason: $BLOCKED_REASON\n\nPlease revise your tool call to use a safer alternative."
  }
}
EOF
    exit 0
fi

exit 0
